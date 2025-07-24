"""
RAG (Retrieval Augmented Generation) engine for the Notion agent.
"""
import os
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

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
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        try:
            return self.chroma_client.get_collection(name=name, embedding_function=self.embedding_function)
        except ValueError:
            return self.chroma_client.create_collection(name=name, embedding_function=self.embedding_function)
    
    def sync_notion_data(self):
        """
        Sync Notion data to the vector database.
        This should be run periodically to keep the vector DB up to date.
        """
        # Sync tasks
        self._sync_tasks()
        
        # Sync routines
        self._sync_routines()
        
        return True
    
    def _sync_tasks(self):
        """Sync tasks from Notion to ChromaDB."""
        # Get all tasks from Notion
        tasks = self.notion.get_tasks()
        
        # Prepare data for ChromaDB
        ids = [task.id for task in tasks]
        documents = []
        metadatas = []
        
        for task in tasks:
            # Create the document text for embedding
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
            
            documents.append(doc_text)
            
            # Create metadata
            metadata = {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "priority": task.priority if task.priority else "",
                "due_date": task.due_date if task.due_date else "",
                "url": task.url,
                "type": "task"
            }
            metadatas.append(metadata)
        
        # Clear existing data and add new data
        if ids:
            self.tasks_collection.delete(where={"type": "task"})
            self.tasks_collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
    
    def _sync_routines(self):
        """Sync routines from Notion to ChromaDB."""
        # Get all routines from Notion
        routines = self.notion.get_routines()
        
        # Prepare data for ChromaDB
        ids = [routine.id for routine in routines]
        documents = []
        metadatas = []
        
        for routine in routines:
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
            
            documents.append(doc_text)
            
            # Create metadata
            metadata = {
                "id": routine.id,
                "name": routine.name,
                "recurring": str(routine.recurring),
                "recurrence_pattern": routine.recurrence_pattern if routine.recurrence_pattern else "",
                "url": routine.url,
                "type": "routine"
            }
            metadatas.append(metadata)
        
        # Clear existing data and add new data
        if ids:
            self.routines_collection.delete(where={"type": "routine"})
            self.routines_collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
    
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