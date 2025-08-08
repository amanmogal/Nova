"""
Multi-tenant RAG (Retrieval Augmented Generation) engine for the Notion agent.
Creates separate ChromaDB instances per user for complete data isolation.
"""
import os
import json
import pathlib
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from dateutil import parser as date_parser

from dotenv import load_dotenv
import chromadb
from chromadb import PersistentClient
from chromadb.config import Settings
import google.generativeai as genai

from src.tools.notion_connector import NotionConnector
from src.schema.notion_schemas import NotionTaskSchema, RoutineSchema
from src.db.multi_tenant_connector import multi_tenant_db

# Load environment variables
load_dotenv()

# Configure Google API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class MultiTenantRAGEngine:
    """
    Multi-tenant RAG Engine for retrieving context from Notion data using vector search.
    Creates separate ChromaDB instances per user for complete data isolation.
    """
    
    def __init__(self, user_id: str):
        """Initialize the RAG engine for a specific user."""
        self.user_id = user_id
        # Load per-user Notion credentials
        multi_tenant_db.set_user_context(user_id)
        creds = multi_tenant_db.get_user_credentials() or {}
        api_key_override = creds.get("notion_access_token")
        self.notion = NotionConnector(api_key=api_key_override)

        class GoogleEmbeddingFunction(chromadb.EmbeddingFunction):
            def __call__(self, input: List[str]) -> List[List[float]]:
                model = genai.GenerativeModel("models/embedding-001")
                return [genai.embed_content(model="models/embedding-001", content=text)["embedding"] for text in input]

        self.embedding_function = GoogleEmbeddingFunction()
        
        # User-specific ChromaDB path
        base_chroma_path = os.getenv("CHROMA_DB_PATH", "./data/chroma")
        self.chroma_path = pathlib.Path(base_chroma_path) / f"user_{user_id}"
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client for this user
        self.chroma_client = PersistentClient(
            path=str(self.chroma_path),
            settings=Settings(persist_directory=str(self.chroma_path), is_persistent=True),
        )
        
        # Create or get collections for this user
        self.tasks_collection = self._get_or_create_collection(f"user_{user_id}_tasks")
        self.routines_collection = self._get_or_create_collection(f"user_{user_id}_routines")

        # User-specific sync state path
        self.sync_state_path = self.chroma_path / "rag_sync_state.json"
        self.sync_state = self._load_sync_state()
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        try:
            print(f"Debug: Attempting to get collection: {name}")
            return self.chroma_client.get_collection(name=name, embedding_function=self.embedding_function)
        except Exception as e:
            print(f"Debug: Failed to get collection {name}: {e}. Attempting to create.")
            return self.chroma_client.create_collection(name=name, embedding_function=self.embedding_function)

    # ------------------------------------------------------------------
    # Text chunking utility
    # ------------------------------------------------------------------
    def _chunk_text(self, text: str, max_words: int = 300, overlap: int = 50) -> List[str]:
        """Split long text into overlapping word chunks.

        Args:
            text: The raw text to split.
            max_words: Target maximum number of words per chunk.
            overlap: Number of words to overlap between consecutive chunks.

        Returns:
            List of text chunks.
        """
        words = text.split()
        if len(words) <= max_words:
            return [text]

        chunks: List[str] = []
        start = 0
        while start < len(words):
            end = start + max_words
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            # move start forward keeping an overlap
            start = end - overlap
            if start < 0:
                start = 0
        return chunks
    
    async def sync_notion_data(self):
        """
        Sync Notion data to the user's vector database.
        This should be run periodically to keep the vector DB up to date.
        """
        try:
            # Set user context for database operations
            multi_tenant_db.set_user_context(self.user_id)
            
            # Get user configuration
            user_config = multi_tenant_db.get_user_config()
            if not user_config:
                print(f"No user config found for user {self.user_id}")
                return
            
            # Update Notion connector with user's tokens
            if user_config.notion_tasks_db_id:
                self.notion.tasks_db_id = user_config.notion_tasks_db_id
            if user_config.notion_routines_db_id:
                self.notion.routines_db_id = user_config.notion_routines_db_id
            
            # Get last sync time
            last_sync = self.sync_state.get("last_sync")
            
            # Sync tasks and routines
            await self._sync_tasks(last_sync)
            await self._sync_routines(last_sync)
            
            # Update sync state
            self.sync_state["last_sync"] = datetime.now().isoformat()
            self._save_sync_state()
            
            # Log the sync operation
            multi_tenant_db.log_usage(
                operation_type="rag_sync",
                operation_details={
                    "user_id": self.user_id,
                    "tasks_synced": len(self.sync_state.get("tasks_synced", [])),
                    "routines_synced": len(self.sync_state.get("routines_synced", []))
                }
            )
            
        except Exception as e:
            print(f"Error syncing Notion data for user {self.user_id}: {str(e)}")
            multi_tenant_db.log_usage(
                operation_type="rag_sync",
                operation_details={"user_id": self.user_id, "error": str(e)},
                success=False,
                error_message=str(e)
            )
    
    async def _sync_tasks(self, last_sync: Optional[str] = None):
        """Sync tasks from Notion to the user's vector database."""
        try:
            # Get tasks from Notion
            tasks = await self.notion.get_tasks()
            
            if not tasks:
                print(f"No tasks found for user {self.user_id}")
                return
            
            # Track synced task IDs
            synced_task_ids = []
            
            for task in tasks:
                try:
                    # Check if task was modified since last sync
                    if last_sync and task.last_edited_time:
                        task_edit_time = date_parser.parse(task.last_edited_time)
                        last_sync_time = date_parser.parse(last_sync)
                        if task_edit_time <= last_sync_time:
                            continue
                    
                    # Create task content for embedding
                    task_content = f"Task: {task.title}\n"
                    if task.description:
                        task_content += f"Description: {task.description}\n"
                    if task.status:
                        task_content += f"Status: {task.status}\n"
                    if task.priority:
                        task_content += f"Priority: {task.priority}\n"
                    if task.due_date:
                        task_content += f"Due Date: {task.due_date}\n"
                    if task.tags:
                        task_content += f"Tags: {', '.join(task.tags)}\n"
                    if task.notes:
                        task_content += f"Notes: {task.notes}\n"
                    
                    # Chunk the task content
                    chunks = self._chunk_text(task_content)
                    
                    # Delete existing chunks for this task
                    self.tasks_collection.delete(where={"parent_id": task.id})
                    
                    # Add chunks to vector database
                    for i, chunk in enumerate(chunks):
                        self.tasks_collection.add(
                            documents=[chunk],
                            metadatas=[{
                                "parent_id": task.id,
                                "chunk_index": i,
                                "title": task.title,
                                "status": task.status,
                                "priority": task.priority,
                                "due_date": task.due_date.isoformat() if task.due_date else None,
                                "tags": task.tags,
                                "type": "task"
                            }],
                            ids=[f"{task.id}_chunk_{i}"]
                        )
                    
                    synced_task_ids.append(task.id)
                    
                except Exception as e:
                    print(f"Error syncing task {task.id}: {str(e)}")
                    continue
            
            # Update sync state
            self.sync_state["tasks_synced"] = synced_task_ids
            
        except Exception as e:
            print(f"Error in _sync_tasks for user {self.user_id}: {str(e)}")
            raise
    
    async def _sync_routines(self, last_sync: Optional[str] = None):
        """Sync routines from Notion to the user's vector database."""
        try:
            # Get routines from Notion
            routines = await self.notion.get_routines()
            
            if not routines:
                print(f"No routines found for user {self.user_id}")
                return
            
            # Track synced routine IDs
            synced_routine_ids = []
            
            for routine in routines:
                try:
                    # Check if routine was modified since last sync
                    if last_sync and routine.last_edited_time:
                        routine_edit_time = date_parser.parse(routine.last_edited_time)
                        last_sync_time = date_parser.parse(last_sync)
                        if routine_edit_time <= last_sync_time:
                            continue
                    
                    # Create routine content for embedding
                    routine_content = f"Routine: {routine.name}\n"
                    if routine.description:
                        routine_content += f"Description: {routine.description}\n"
                    if routine.time_blocks:
                        routine_content += f"Time Blocks: {routine.time_blocks}\n"
                    if routine.recurring:
                        routine_content += f"Recurring: {routine.recurring}\n"
                    if routine.recurrence_pattern:
                        routine_content += f"Recurrence Pattern: {routine.recurrence_pattern}\n"
                    
                    # Chunk the routine content
                    chunks = self._chunk_text(routine_content)
                    
                    # Delete existing chunks for this routine
                    self.routines_collection.delete(where={"parent_id": routine.id})
                    
                    # Add chunks to vector database
                    for i, chunk in enumerate(chunks):
                        self.routines_collection.add(
                            documents=[chunk],
                            metadatas=[{
                                "parent_id": routine.id,
                                "chunk_index": i,
                                "name": routine.name,
                                "recurring": routine.recurring,
                                "recurrence_pattern": routine.recurrence_pattern,
                                "type": "routine"
                            }],
                            ids=[f"{routine.id}_chunk_{i}"]
                        )
                    
                    synced_routine_ids.append(routine.id)
                    
                except Exception as e:
                    print(f"Error syncing routine {routine.id}: {str(e)}")
                    continue
            
            # Update sync state
            self.sync_state["routines_synced"] = synced_routine_ids
            
        except Exception as e:
            print(f"Error in _sync_routines for user {self.user_id}: {str(e)}")
            raise
    
    def _load_sync_state(self) -> Dict[str, Any]:
        """Load sync state from file."""
        try:
            if self.sync_state_path.exists():
                with open(self.sync_state_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading sync state for user {self.user_id}: {str(e)}")
        
        return {
            "last_sync": None,
            "tasks_synced": [],
            "routines_synced": []
        }
    
    def _save_sync_state(self):
        """Save sync state to file."""
        try:
            with open(self.sync_state_path, "w") as f:
                json.dump(self.sync_state, f, indent=2)
        except Exception as e:
            print(f"Error saving sync state for user {self.user_id}: {str(e)}")
    
    def search_tasks(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for tasks in the user's vector database."""
        try:
            # Set user context for database operations
            multi_tenant_db.set_user_context(self.user_id)
            
            # Check user quota
            quota_check = multi_tenant_db.check_user_quota("search_tasks")
            if not quota_check.get("allowed", False):
                print(f"User {self.user_id} quota exceeded: {quota_check.get('reason')}")
                return []
            
            # Perform search
            results = self.tasks_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    formatted_results.append({
                        "content": doc,
                        "metadata": metadata,
                        "distance": results["distances"][0][i] if results["distances"] else None
                    })
            
            # Log the search operation
            multi_tenant_db.log_usage(
                operation_type="search_tasks",
                operation_details={
                    "user_id": self.user_id,
                    "query": query,
                    "results_count": len(formatted_results),
                    "n_results_requested": n_results
                }
            )
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching tasks for user {self.user_id}: {str(e)}")
            multi_tenant_db.log_usage(
                operation_type="search_tasks",
                operation_details={"user_id": self.user_id, "query": query, "error": str(e)},
                success=False,
                error_message=str(e)
            )
            return []
    
    def search_routines(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Search for routines in the user's vector database."""
        try:
            # Set user context for database operations
            multi_tenant_db.set_user_context(self.user_id)
            
            # Check user quota
            quota_check = multi_tenant_db.check_user_quota("search_routines")
            if not quota_check.get("allowed", False):
                print(f"User {self.user_id} quota exceeded: {quota_check.get('reason')}")
                return []
            
            # Perform search
            results = self.routines_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    formatted_results.append({
                        "content": doc,
                        "metadata": metadata,
                        "distance": results["distances"][0][i] if results["distances"] else None
                    })
            
            # Log the search operation
            multi_tenant_db.log_usage(
                operation_type="search_routines",
                operation_details={
                    "user_id": self.user_id,
                    "query": query,
                    "results_count": len(formatted_results),
                    "n_results_requested": n_results
                }
            )
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching routines for user {self.user_id}: {str(e)}")
            multi_tenant_db.log_usage(
                operation_type="search_routines",
                operation_details={"user_id": self.user_id, "query": query, "error": str(e)},
                success=False,
                error_message=str(e)
            )
            return []
    
    def build_context(self, query: str) -> Dict[str, Any]:
        """Build context for the user based on the query."""
        try:
            # Set user context for database operations
            multi_tenant_db.set_user_context(self.user_id)
            
            # Get user configuration
            user_config = multi_tenant_db.get_user_config()
            max_context_length = user_config.max_context_length if user_config else 4000
            
            # Search for relevant tasks and routines
            tasks = self.search_tasks(query, n_results=3)
            routines = self.search_routines(query, n_results=2)
            
            # Build context string
            context_parts = []
            
            if tasks:
                context_parts.append("Relevant Tasks:")
                for task in tasks:
                    context_parts.append(f"- {task['metadata'].get('title', 'Unknown Task')}: {task['content'][:200]}...")
            
            if routines:
                context_parts.append("\nRelevant Routines:")
                for routine in routines:
                    context_parts.append(f"- {routine['metadata'].get('name', 'Unknown Routine')}: {routine['content'][:200]}...")
            
            context_str = "\n".join(context_parts)
            
            # Truncate if too long
            if len(context_str) > max_context_length:
                context_str = context_str[:max_context_length] + "..."
            
            return {
                "tasks": tasks,
                "routines": routines,
                "context_string": context_str,
                "query": query,
                "user_id": self.user_id
            }
            
        except Exception as e:
            print(f"Error building context for user {self.user_id}: {str(e)}")
            return {
                "tasks": [],
                "routines": [],
                "context_string": "",
                "query": query,
                "user_id": self.user_id,
                "error": str(e)
            }
    
    def cleanup_user_data(self):
        """Clean up user's ChromaDB data (for account deletion)."""
        try:
            # Delete collections
            self.chroma_client.delete_collection(name=self.tasks_collection.name)
            self.chroma_client.delete_collection(name=self.routines_collection.name)
            
            # Delete sync state file
            if self.sync_state_path.exists():
                self.sync_state_path.unlink()
            
            # Delete user directory
            if self.chroma_path.exists():
                import shutil
                shutil.rmtree(self.chroma_path)
            
            print(f"Cleaned up ChromaDB data for user {self.user_id}")
            
        except Exception as e:
            print(f"Error cleaning up user data for {self.user_id}: {str(e)}")


# Factory function to create RAG engine for a user
def create_user_rag_engine(user_id: str) -> MultiTenantRAGEngine:
    """Create a RAG engine instance for a specific user."""
    return MultiTenantRAGEngine(user_id) 