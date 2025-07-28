from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.config import get_settings
from src.agent import run_agent  # existing helper that drives the LangGraph workflow
from src.tools.notion_connector import NotionConnector
from src.db.supabase_connector import SupabaseConnector
from src.tools.rag_engine import RAGEngine
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os

app = FastAPI(title="Nova Notion-Agent API", version="0.1.0")
settings = get_settings()

# ---------------------------------------------------------------------------
# Scheduler setup for periodic RAG sync
# ---------------------------------------------------------------------------

rag_engine = RAGEngine()

# Read interval (minutes) from env var, default to 60
SYNC_INTERVAL_MIN = int(os.getenv("RAG_SYNC_INTERVAL_MIN", "60"))

scheduler = AsyncIOScheduler()


@scheduler.scheduled_job("interval", minutes=SYNC_INTERVAL_MIN)
def _scheduled_rag_sync() -> None:  # noqa: D401, ANN001
    """Background job: sync Notion data to the vector DB."""
    try:
        rag_engine.sync_notion_data()
    except Exception as exc:  # noqa: BLE001
        # Log but suppress exception to keep scheduler alive
        print(f"[RAG Sync] Error: {exc}")


# FastAPI lifespan events ----------------------------------------------------


@app.on_event("startup")
async def _on_startup() -> None:  # noqa: D401
    scheduler.start()
    print(f"Scheduler started: syncing every {SYNC_INTERVAL_MIN} minute(s)")


@app.on_event("shutdown")
async def _on_shutdown() -> None:  # noqa: D401
    scheduler.shutdown()
    print("Scheduler shutdown")


class TaskIn(BaseModel):
    title: str
    notes: str | None = None
    status: str = "To Do"
    priority: str = "Medium"


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run/{goal}")
async def run_goal(goal: str) -> dict[str, str]:
    """Kick off an agent run for a given goal (e.g., daily_planning)."""
    try:
        result = run_agent(goal)
        return {"status": "completed", "result": str(result)}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/tasks")
async def create_task(task: TaskIn) -> dict[str, str]:
    """Create a new Notion task through the agent's connector."""
    notion = NotionConnector()
    task_id = notion.create_task(task.dict())
    return {"task_id": task_id}


@app.get("/state/latest")
async def latest_state() -> dict:
    db = SupabaseConnector()
    state = db.get_latest_agent_state()
    if not state:
        raise HTTPException(status_code=404, detail="No state found")
    return state 