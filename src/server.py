from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.config import get_settings
from src.agent import run_agent  # existing helper that drives the LangGraph workflow
from src.tools.notion_connector import NotionConnector
from src.db.supabase_connector import SupabaseConnector

app = FastAPI(title="Nova Notion-Agent API", version="0.1.0")
settings = get_settings()


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