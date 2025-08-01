import os
from src.tools.rag_engine import RAGEngine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def inspect_chroma_collections():
    print("Initializing RAGEngine to connect to ChromaDB...")
    rag_engine = RAGEngine()
    print("RAGEngine initialized.")

    print("\n--- Inspecting notion_tasks collection ---")
    try:
        tasks_count = rag_engine.tasks_collection.count()
        print(f"Total tasks in collection: {tasks_count}")

        if tasks_count > 0:
            print("\nPeeking at first 5 tasks:")
            # Peek returns a dictionary with 'ids', 'embeddings', 'metadatas', 'documents'
            peek_results = rag_engine.tasks_collection.peek(limit=5)
            for i in range(len(peek_results['ids'])):
                print(f"  ID: {peek_results['ids'][i]}")
                print(f"  Document: {peek_results['documents'][i][:100]}...") # Show first 100 chars
                print(f"  Metadata: {peek_results['metadatas'][i]}")
                print("-" * 20)
        else:
            print("No tasks found in the collection.")

    except Exception as e:
        print(f"Error inspecting tasks collection: {e}")

    print("\n--- Inspecting notion_routines collection ---")
    try:
        routines_count = rag_engine.routines_collection.count()
        print(f"Total routines in collection: {routines_count}")

        if routines_count > 0:
            print("\nPeeking at first 5 routines:")
            peek_results = rag_engine.routines_collection.peek(limit=5)
            for i in range(len(peek_results['ids'])):
                print(f"  ID: {peek_results['ids'][i]}")
                print(f"  Document: {peek_results['documents'][i][:100]}...") # Show first 100 chars
                print(f"  Metadata: {peek_results['metadatas'][i]}")
                print("-" * 20)
        else:
            print("No routines found in the collection.")

    except Exception as e:
        print(f"Error inspecting routines collection: {e}")

if __name__ == "__main__":
    inspect_chroma_collections()
