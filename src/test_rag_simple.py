#!/usr/bin/env python3
"""
Simple RAG Pipeline Test Script
Tests the core RAG functionality without pytest dependencies.
"""
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.rag_engine import RAGEngine
from src.schema.notion_schemas import NotionTaskSchema


class FakeNotionConnector:
    """Stubbed NotionConnector returning predictable data for tests."""
    
    def __init__(self, tasks):
        self._tasks = tasks
    
    def get_tasks(self):
        return self._tasks
    
    def get_routines(self):
        return []


def make_task(task_id: str, edited_dt: datetime, long_notes_words: int = 0):
    """Helper to generate NotionTaskSchema with optional long notes."""
    notes = "word " * long_notes_words if long_notes_words else "Sample notes"
    return NotionTaskSchema(
        id=task_id,
        title=f"Task {task_id}",
        status="Not Started",  # Updated to match your schema
        priority="Medium",
        due_date=None,
        scheduled_time=None,
        estimated_duration=None,
        tags=[],
        notes=notes,
        last_edited_time=edited_dt.isoformat(),
        url="https://notion.so/example",
    )


def test_chunking_logic():
    """Verify that _chunk_text splits long text into overlapping chunks."""
    print("Testing chunking logic...")
    
    # Create temporary directory for ChromaDB
    tmp_dir = tempfile.mkdtemp()
    os.environ["CHROMA_DB_PATH"] = os.path.join(tmp_dir, "chroma")
    os.environ["RAG_SYNC_STATE_PATH"] = os.path.join(tmp_dir, "rag_sync_state.json")
    
    try:
        engine = RAGEngine()
        long_text = "word " * 1000  # 1000 words
        chunks = engine._chunk_text(long_text.strip())
        
        # Expected: first chunk 300 words, overlap 50 words ⇒ effective step 250
        expected_chunks = (1000 - 300) // 250 + 1  # integer division
        if (1000 - 300) % 250:
            expected_chunks += 1
        
        print(f"Generated {len(chunks)} chunks (expected: {expected_chunks})")
        print(f"Each chunk size: {[len(chunk.split()) for chunk in chunks]}")
        
        assert len(chunks) == expected_chunks, f"Expected {expected_chunks} chunks, got {len(chunks)}"
        # Each chunk upper bound size
        assert all(len(chunk.split()) <= 300 for chunk in chunks), "Chunk size exceeds 300 words"
        
        print("✅ Chunking logic test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Chunking logic test FAILED: {e}")
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_incremental_sync():
    """Ensure that only modified tasks are re-embedded on subsequent syncs."""
    print("\nTesting incremental sync...")
    
    # Create temporary directory for ChromaDB
    tmp_dir = tempfile.mkdtemp()
    os.environ["CHROMA_DB_PATH"] = os.path.join(tmp_dir, "chroma")
    os.environ["RAG_SYNC_STATE_PATH"] = os.path.join(tmp_dir, "rag_sync_state.json")
    
    try:
        base_time = datetime.utcnow()
        task1 = make_task("task1", base_time - timedelta(days=1), long_notes_words=600)
        tasks_round1 = [task1]
        
        engine = RAGEngine()
        # Monkeypatch the notion attribute directly
        engine.notion = FakeNotionConnector(tasks_round1)
        
        # First sync – should embed task1 chunks
        print("Performing first sync...")
        engine.sync_notion_data()
        res1 = engine.tasks_collection.get(where={"parent_id": "task1"})
        chunk_count_round1 = len(res1["ids"]) if res1["ids"] else 0
        print(f"First sync created {chunk_count_round1} chunks")
        
        assert chunk_count_round1 > 0, "Expected chunks for task1 after first sync"
        
        # Second sync with no edits – nothing should change
        print("Performing second sync (no changes)...")
        engine.sync_notion_data()
        res2 = engine.tasks_collection.get(where={"parent_id": "task1"})
        print(f"Second sync: {len(res2['ids'])} chunks")
        
        assert len(res2["ids"]) == chunk_count_round1, "Chunk count should not change"
        
        # Third sync – task1 edited, should delete & re-add chunks
        print("Performing third sync (with changes)...")
        task1_updated = make_task("task1", datetime.utcnow(), long_notes_words=600)
        engine.notion = FakeNotionConnector([task1_updated])
        engine.sync_notion_data()
        res3 = engine.tasks_collection.get(where={"parent_id": "task1"})
        print(f"Third sync: {len(res3['ids'])} chunks")
        
        assert len(res3["ids"]) == chunk_count_round1, "Should have same number of chunks"
        
        print("✅ Incremental sync test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Incremental sync test FAILED: {e}")
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_search_functionality():
    """Test the search functionality of the RAG engine."""
    print("\nTesting search functionality...")
    
    # Create temporary directory for ChromaDB
    tmp_dir = tempfile.mkdtemp()
    os.environ["CHROMA_DB_PATH"] = os.path.join(tmp_dir, "chroma")
    os.environ["RAG_SYNC_STATE_PATH"] = os.path.join(tmp_dir, "rag_sync_state.json")
    
    try:
        engine = RAGEngine()
        
        # Create test tasks with specific content
        task1 = make_task("task1", datetime.utcnow(), long_notes_words=0)
        task1.notes = "This task is about machine learning and AI development"
        task1.title = "ML Development Task"
        
        task2 = make_task("task2", datetime.utcnow(), long_notes_words=0)
        task2.notes = "This task is about database optimization and performance"
        task2.title = "Database Optimization"
        
        # Inject test data
        engine.notion = FakeNotionConnector([task1, task2])
        
        # Sync data
        print("Syncing test data...")
        engine.sync_notion_data()
        
        # Test search
        print("Testing search for 'machine learning'...")
        results = engine.search_tasks("machine learning", n_results=5)
        print(f"Found {len(results)} results")
        
        # Should find task1
        assert len(results) > 0, "Should find at least one result"
        
        print("✅ Search functionality test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Search functionality test FAILED: {e}")
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main():
    """Run all RAG pipeline tests."""
    print("🧪 RAG Pipeline Test Suite")
    print("=" * 50)
    
    tests = [
        test_chunking_logic,
        test_incremental_sync,
        test_search_functionality,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} FAILED with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"Passed: {sum(results)}/{len(results)}")
    print(f"Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All RAG pipeline tests PASSED!")
    else:
        print("⚠️  Some tests failed. Check the output above.")


if __name__ == "__main__":
    main() 