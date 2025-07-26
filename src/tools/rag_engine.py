"""
RAG (Retrieval Augmented Generation) engine for the Notion agent.
"""
import os
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import pathlib
import json as _json
from dateutil import parser as date_parser

from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
import google.generativeai as genai
from src.tools.notion_connector import NotionConnector
from src.schema.notion_schemas import NotionTaskSchema, RoutineSchema

# Load environment variables
load_dotenv()

# Configure Google API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class RAGEngine:
    """
    RAG Engine for retrieving context from Notion data using vector search.
    Implements Own Your Context Window by ensuring relevant data is
    passed to the LLM.
    """
    
    def __init__(self):
        """Initialize the RAG engine."""
        self.notion = NotionConnector()
        self.chroma_client = chromadb.PersistentClient(path=os.getenv("CHROMA_DB_PATH", "./data/chroma"))
        
        # Use Google's embedding model
        self.embedding_function = embedding_functions.GoogleGenerativeAIEmbeddingFunction(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model_name="models/embedding-001"
        )
        
        # Create or get collections
        self.tasks_collection = self._get_or_create_collection("notion_tasks")
        self.routines_collection = self._get_or_create_collection("notion_routines")

        # Sync state path
        self.sync_state_path = pathlib.Path(os.getenv("RAG_SYNC_STATE_PATH", "./data/rag_sync_state.json"))
        self.sync_state = self._load_sync_state()
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        try:
            return self.chroma_client.get_collection(name=name, embedding_function=self.embedding_function)
        except ValueError:
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
    
    def sync_notion_data(self):
        """
        Sync Notion data to the vector database.
        This should be run periodically to keep the vector DB up to date.
        """
        last_sync = self.sync_state.get("last_sync")

        # Sync tasks and routines incrementally
        self._sync_tasks(last_sync)
        self._sync_routines(last_sync)

        # Update sync state
        self.sync_state["last_sync"] = datetime.utcnow().isoformat()
        self._save_sync_state()

        return True
    
    def _sync_tasks(self, last_sync: Optional[str] = None):
        """Sync tasks from Notion to ChromaDB."""
        # Get all tasks from Notion
        tasks = self.notion.get_tasks()

        # If last_sync is provided, filter tasks that were edited after that time
        if last_sync:
            try:
                last_sync_dt = date_parser.isoparse(last_sync)
                tasks = [t for t in tasks if t.last_edited_time and date_parser.isoparse(t.last_edited_time) > last_sync_dt]
            except Exception:
                pass  # If parsing fails, fall back to full sync

        if not tasks:
            return  # Nothing to update
        
        # Prepare data for ChromaDB (with chunking)
        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        parent_ids: List[str] = []
        
        for task in tasks:
            parent_ids.append(task.id)
            # Create the document text for embedding (aggregate details)
            doc_text = f"Task: {task.title}\n"
            
            if task.status:
                doc_text += f"Status: {task.status}\n"
                
            if task.priority:
                doc_text += f"Priority: {task.priority}\n"
                
            if task.due_date:
                doc_text += f"Due Date: {task.due_date}\n"
                
            if task.scheduled_time:
                doc_text += f"Scheduled Time: {task.scheduled_time}\n"
                
            if task.estimated_duration:
                doc_text += f"Estimated Duration: {task.estimated_duration} minutes\n"
                
            if task.tags:
                doc_text += f"Tags: {', '.join(task.tags)}\n"
                
            if task.notes:
                doc_text += f"Notes: {task.notes}\n"
            
            # Split into chunks for embedding
            chunks = self._chunk_text(doc_text)

            for idx, chunk in enumerate(chunks):
                chunk_id = f"{task.id}_chunk_{idx}"
                ids.append(chunk_id)
                documents.append(chunk)
                metadata = {
                    "id": chunk_id,
                    "parent_id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority if task.priority else "",
                    "due_date": task.due_date if task.due_date else "",
                    "url": task.url,
                    "type": "task",
                    "chunk_index": idx
                }
                metadatas.append(metadata)
        
        # Remove existing embeddings for the affected parent tasks first
        for pid in parent_ids:
            self.tasks_collection.delete(where={"parent_id": pid})

        if ids:
            self.tasks_collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
    
    def _sync_routines(self, last_sync: Optional[str] = None):
        """Sync routines from Notion to ChromaDB."""
        # Get all routines from Notion
        routines = self.notion.get_routines()

        # Currently Notion API for routines not tracking last_edited_time in schema; perform full refresh if last_sync is None
        
        # Prepare data for ChromaDB (with chunking)
        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        parent_ids: List[str] = []
        
        for routine in routines:
            parent_ids.append(routine.id)
            # Create the document text for embedding
            doc_text = f"Routine: {routine.name}\n"
            
            # Add time blocks
            if routine.time_blocks:
                doc_text += "Time Blocks:\n"
                for block in routine.time_blocks:
                    doc_text += f"- {block.name}: {block.start_time} to {block.end_time} on {', '.join(block.days)}\n"
            
            # Add recurrence info
            if routine.recurring:
                doc_text += f"Recurring: Yes\n"
                if routine.recurrence_pattern:
                    doc_text += f"Recurrence Pattern: {routine.recurrence_pattern}\n"
            
            chunks = self._chunk_text(doc_text)

            for idx, chunk in enumerate(chunks):
                chunk_id = f"{routine.id}_chunk_{idx}"
                ids.append(chunk_id)
                documents.append(chunk)
                metadata = {
                    "id": chunk_id,
                    "parent_id": routine.id,
                    "name": routine.name,
                    "recurring": str(routine.recurring),
                    "recurrence_pattern": routine.recurrence_pattern if routine.recurrence_pattern else "",
                    "url": routine.url,
                    "type": "routine",
                    "chunk_index": idx
                }
                metadatas.append(metadata)
        
        # Remove existing embeddings for affected routines
        for pid in parent_ids:
            self.routines_collection.delete(where={"parent_id": pid})

        if ids:
            self.routines_collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

    # ------------------------- Sync State Helpers -------------------------

    def _load_sync_state(self) -> Dict[str, Any]:
        if self.sync_state_path.exists():
            try:
                with self.sync_state_path.open("r", encoding="utf-8") as f:
                    return _json.load(f)
            except Exception:
                return {}
        return {}

    def _save_sync_state(self):
        try:
            self.sync_state_path.parent.mkdir(parents=True, exist_ok=True)
            with self.sync_state_path.open("w", encoding="utf-8") as f:
                _json.dump(self.sync_state, f)
        except Exception as e:
            print(f"Error saving RAG sync state: {e}")
    
    def search_tasks(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for tasks using vector similarity.
        
        Args:
            query: The search query
            n_results: Number of results to return
            
        Returns:
            List of task dictionaries matching the query
        """
        results = self.tasks_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results or not results['ids'] or not results['ids'][0]:
            return []
            
        tasks = []
        for i, task_id in enumerate(results['ids'][0]):
            metadata = results['metadatas'][0][i]
            document = results['documents'][0][i]
            
            tasks.append({
                "id": task_id,
                "metadata": metadata,
                "content": document
            })
        
        return tasks
    
    def search_routines(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for routines using vector similarity.
        
        Args:
            query: The search query
            n_results: Number of results to return
            
        Returns:
            List of routine dictionaries matching the query
        """
        results = self.routines_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results or not results['ids'] or not results['ids'][0]:
            return []
            
        routines = []
        for i, routine_id in enumerate(results['ids'][0]):
            metadata = results['metadatas'][0][i]
            document = results['documents'][0][i]
            
            routines.append({
                "id": routine_id,
                "metadata": metadata,
                "content": document
            })
        
        return routines
    
    def build_context(self, query: str) -> Dict[str, Any]:
        """
        Build a context dictionary for the LLM with relevant information.
        Following Factor 3: Own Your Context Window.
        
        Args:
            query: The agent's current goal or query
            
        Returns:
            Dictionary with relevant context information
        """
        context = {
            "tasks": [],
            "routines": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Get relevant tasks
        tasks = self.search_tasks(query, n_results=5)
        context["tasks"] = tasks
        
        # Get relevant routines
        routines = self.search_routines(query, n_results=3)
        context["routines"] = routines
        
        # Add calendar view preferences (from memory)
        context["calendar_view_start"] = os.getenv("CALENDAR_VIEW_START", "10:00")  # 10 AM
        context["calendar_view_end"] = os.getenv("CALENDAR_VIEW_END", "02:00")  # 2 AM next day
        
        return context 