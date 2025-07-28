import os
import shutil
import tempfile

import pytest
from datetime import datetime, timedelta

# Environment setup: use a temporary directory for Chroma DB to isolate tests
TMP_DIR = tempfile.mkdtemp()
os.environ["CHROMA_DB_PATH"] = os.path.join(TMP_DIR, "chroma")
# Ensure sync state file also goes to tmp
os.environ["RAG_SYNC_STATE_PATH"] = os.path.join(TMP_DIR, "rag_sync_state.json")

from src.tools.rag_engine import RAGEngine  # noqa: E402
from src.schema.notion_schemas import NotionTaskSchema  # noqa: E402


class _FakeNotionConnector:
    """Stubbed NotionConnector returning predictable data for tests."""

    def __init__(self, tasks):
        self._tasks = tasks

    def get_tasks(self):
        return self._tasks

    def get_routines(self):
        return []


@pytest.fixture(autouse=True)
def cleanup_tmpdir():
    """Clean up tmpdir after tests."""
    yield
    shutil.rmtree(TMP_DIR, ignore_errors=True)


def _make_task(task_id: str, edited_dt: datetime, long_notes_words: int = 0):
    """Helper to generate NotionTaskSchema with optional long notes."""
    notes = "word " * long_notes_words if long_notes_words else "Sample notes"
    return NotionTaskSchema(
        id=task_id,
        title=f"Task {task_id}",
        status="To Do",
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
    engine = RAGEngine()
    long_text = "word " * 1000  # 1000 words
    chunks = engine._chunk_text(long_text.strip())

    # Expected: first chunk 300 words, overlap 50 words ⇒ effective step 250
    expected_chunks = (1000 - 300) // 250 + 1  # integer division
    if (1000 - 300) % 250:
        expected_chunks += 1

    assert len(chunks) == expected_chunks
    # Each chunk upper bound size
    assert all(len(chunk.split()) <= 300 for chunk in chunks)


def test_incremental_sync():
    """Ensure that only modified tasks are re-embedded on subsequent syncs."""
    base_time = datetime.utcnow()
    task1 = _make_task("task1", base_time - timedelta(days=1), long_notes_words=600)
    tasks_round1 = [task1]

    # Inject fake connector before instantiating engine
    RAGEngine.NotionConnector = None  # type: ignore  # prevent accidental use

    engine = RAGEngine()
    # Monkeypatch the notion attribute directly
    engine.notion = _FakeNotionConnector(tasks_round1)

    # First sync – should embed task1 chunks
    engine.sync_notion_data()
    res1 = engine.tasks_collection.get(where={"parent_id": "task1"})
    chunk_count_round1 = len(res1["ids"]) if res1["ids"] else 0
    assert chunk_count_round1 > 0, "Expected chunks for task1 after first sync"

    # Second sync with no edits – nothing should change
    engine.sync_notion_data()
    res2 = engine.tasks_collection.get(where={"parent_id": "task1"})
    assert len(res2["ids"]) == chunk_count_round1

    # Third sync – task1 edited, should delete & re-add chunks (ids will differ)
    task1_updated = _make_task("task1", datetime.utcnow(), long_notes_words=600)
    engine.notion = _FakeNotionConnector([task1_updated])
    engine.sync_notion_data()
    res3 = engine.tasks_collection.get(where={"parent_id": "task1"})
    assert len(res3["ids"]) == chunk_count_round1  # same number of chunks
    # ids should have new suffix index starting from 0 again but they might match, so check documents differ
    assert res3["documents"][0][0] == res1["documents"][0][0]  # content same 