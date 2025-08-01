"""
Test script for RAG engine functionality.
"""
import asyncio
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.tools.rag_engine import RAGEngine
from src.tools.notion_connector import NotionConnector

async def test_rag_engine():
    """Test RAG engine functionality."""
    print("🧪 Testing RAG Engine")
    print("=" * 50)
    
    # Set environment variable for routines database
    os.environ["NOTION_ROUTINES_DATABASE_ID"] = "229e68c703808028bf47c49b7bad1735"
    
    try:
        # Initialize RAG engine
        print("1. Initializing RAG Engine...")
        rag_engine = RAGEngine()
        print("   ✅ RAG Engine initialized successfully")
        
        # Test Notion connector directly
        print("\n2. Testing Notion Connector...")
        notion = NotionConnector()
        
        # Test getting tasks
        print("   Testing task retrieval...")
        tasks = await notion.get_tasks()
        print(f"   ✅ Found {len(tasks)} tasks")
        if tasks:
            print(f"   Sample task: {tasks[0].title} (Status: {tasks[0].status})")
        
        # Test getting routines
        print("   Testing routine retrieval...")
        routines = await notion.get_routines()
        print(f"   ✅ Found {len(routines)} routines")
        if routines:
            print(f"   Sample routine: {routines[0].task} (Category: {routines[0].category})")
        
        # Test RAG sync
        print("\n3. Testing RAG Sync...")
        print("   Syncing tasks...")
        await rag_engine._sync_tasks()
        print("   ✅ Tasks synced successfully")
        
        print("   Syncing routines...")
        await rag_engine._sync_routines()
        print("   ✅ Routines synced successfully")
        
        # Test search functionality
        print("\n4. Testing Search Functionality...")
        
        # Test task search
        print("   Testing task search...")
        task_results = rag_engine.search_tasks("implementation", n_results=3)
        print(f"   ✅ Found {len(task_results)} task results")
        for i, result in enumerate(task_results[:2], 1):
            print(f"     {i}. {result.get('content', 'No content')[:100]}...")
        
        # Test routine search
        print("   Testing routine search...")
        routine_results = rag_engine.search_routines("meeting", n_results=3)
        print(f"   ✅ Found {len(routine_results)} routine results")
        for i, result in enumerate(routine_results[:2], 1):
            print(f"     {i}. {result.get('content', 'No content')[:100]}...")
        
        # Test context building
        print("\n5. Testing Context Building...")
        context = rag_engine.build_context("daily planning tasks")
        print(f"   ✅ Context built successfully")
        print(f"   Tasks in context: {len(context.get('tasks', []))}")
        print(f"   Routines in context: {len(context.get('routines', []))}")
        
        print("\n" + "=" * 50)
        print("🎉 RAG Engine Test Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Error testing RAG engine: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_engine()) 