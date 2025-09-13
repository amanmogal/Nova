from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.config import get_settings
from src.agent import run_agent  # existing helper that drives the LangGraph workflow
from src.tools.notion_connector import NotionConnector
from src.db.supabase_connector import SupabaseConnector
from src.tools.rag_engine import RAGEngine
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import traceback
from dataclasses import dataclass, asdict
from fastapi import Response
from src.monitoring.metrics_collector import get_metrics_collector
import json

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Nova Notion-Agent API", version="0.1.0")
settings = get_settings()

# ---------------------------------------------------------------------------
# Sync monitoring and health tracking
# ---------------------------------------------------------------------------

@dataclass
class SyncMetrics:
    """Track sync performance and health metrics."""
    last_sync_time: Optional[datetime] = None
    last_successful_sync: Optional[datetime] = None
    sync_duration: Optional[float] = None
    tasks_processed: int = 0
    chunks_created: int = 0
    errors_count: int = 0
    consecutive_failures: int = 0
    is_healthy: bool = True
    error_message: Optional[str] = None

class SyncMonitor:
    """Monitor and track sync operations."""
    
    def __init__(self):
        self.metrics = SyncMetrics()
        self.sync_history: list[Dict[str, Any]] = []
        self.max_history_size = 100
    
    def record_sync_start(self):
        """Record the start of a sync operation."""
        self.metrics.last_sync_time = datetime.utcnow()
        logger.info(" Starting RAG sync operation")
    
    def record_sync_success(self, duration: float, tasks_processed: int, chunks_created: int):
        """Record a successful sync operation."""
        self.metrics.last_successful_sync = datetime.utcnow()
        self.metrics.sync_duration = duration
        self.metrics.tasks_processed = tasks_processed
        self.metrics.chunks_created = chunks_created
        self.metrics.consecutive_failures = 0
        self.metrics.is_healthy = True
        self.metrics.error_message = None
        
        # Add to history
        sync_record = {
            "timestamp": self.metrics.last_successful_sync.isoformat(),
            "status": "success",
            "duration": duration,
            "tasks_processed": tasks_processed,
            "chunks_created": chunks_created,
            "error": None
        }
        self._add_to_history(sync_record)
        
        logger.info(f" RAG sync completed successfully in {duration:.2f}s - {tasks_processed} tasks, {chunks_created} chunks")
    
    def record_sync_failure(self, error: Exception, duration: float = 0):
        """Record a failed sync operation."""
        self.metrics.consecutive_failures += 1
        self.metrics.errors_count += 1
        self.metrics.sync_duration = duration
        self.metrics.is_healthy = self.metrics.consecutive_failures < 3
        self.metrics.error_message = str(error)
        
        # Add to history
        sync_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "failure",
            "duration": duration,
            "tasks_processed": 0,
            "chunks_created": 0,
            "error": str(error)
        }
        self._add_to_history(sync_record)
        
        logger.error(f" RAG sync failed after {duration:.2f}s: {error}")
        logger.error(f"Consecutive failures: {self.metrics.consecutive_failures}")
    
    def _add_to_history(self, record: Dict[str, Any]):
        """Add sync record to history, maintaining max size."""
        self.sync_history.append(record)
        if len(self.sync_history) > self.max_history_size:
            self.sync_history.pop(0)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            "is_healthy": self.metrics.is_healthy,
            "last_sync": self.metrics.last_sync_time.isoformat() if self.metrics.last_sync_time else None,
            "last_successful_sync": self.metrics.last_successful_sync.isoformat() if self.metrics.last_successful_sync else None,
            "consecutive_failures": self.metrics.consecutive_failures,
            "total_errors": self.metrics.errors_count,
            "sync_duration": self.metrics.sync_duration,
            "tasks_processed": self.metrics.tasks_processed,
            "chunks_created": self.metrics.chunks_created,
            "error_message": self.metrics.error_message
        }
    
    def get_sync_history(self, limit: int = 10) -> list[Dict[str, Any]]:
        """Get recent sync history."""
        return self.sync_history[-limit:] if self.sync_history else []

# Initialize sync monitor
sync_monitor = SyncMonitor()

# ---------------------------------------------------------------------------
# Scheduler setup for periodic RAG sync with enhanced error handling
# ---------------------------------------------------------------------------

rag_engine = RAGEngine()

# Read interval (minutes) from env var, default to 60
SYNC_INTERVAL_MIN = int(os.getenv("RAG_SYNC_INTERVAL_MIN", "60"))

scheduler = AsyncIOScheduler()

def _scheduled_rag_sync() -> None:
    """Background job: sync Notion data to the vector DB with comprehensive error handling."""
    start_time = time.time()
    sync_monitor.record_sync_start()
    
    try:
        # Perform the sync operation
        sync_stats = rag_engine.sync_notion_data()
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Extract statistics from the sync operation
        tasks_processed = sync_stats.get("tasks_processed", 0)
        chunks_created = sync_stats.get("total_chunks_created", 0)
        
        sync_monitor.record_sync_success(duration, tasks_processed, chunks_created)
        
    except Exception as exc:
        duration = time.time() - start_time
        sync_monitor.record_sync_failure(exc, duration)
        
        # Log detailed error information
        logger.error(f"RAG sync failed with exception: {type(exc).__name__}: {exc}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Don't re-raise to keep scheduler alive, but log for monitoring
        # In production, you might want to send alerts here

@scheduler.scheduled_job("interval", minutes=SYNC_INTERVAL_MIN)
def scheduled_rag_sync_wrapper():
    """Wrapper for the scheduled sync job."""
    _scheduled_rag_sync()

# FastAPI lifespan events ----------------------------------------------------

@app.on_event("startup")
async def _on_startup() -> None:
    """Start the scheduler and log startup information."""
    try:
        scheduler.start()
        logger.info(f" Scheduler started: syncing every {SYNC_INTERVAL_MIN} minute(s)")
        logger.info(f" Sync monitoring initialized")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise

@app.on_event("shutdown")
async def _on_shutdown() -> None:
    """Shutdown the scheduler gracefully."""
    try:
        scheduler.shutdown()
        logger.info(" Scheduler shutdown")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# ---------------------------------------------------------------------------
# API Models
# ---------------------------------------------------------------------------

class TaskIn(BaseModel):
    title: str
    notes: str | None = None
    status: str = "To Do"
    priority: str = "Medium"

class SyncStatusResponse(BaseModel):
    is_healthy: bool
    last_sync: Optional[str]
    last_successful_sync: Optional[str]
    consecutive_failures: int
    total_errors: int
    sync_duration: Optional[float]
    tasks_processed: int
    chunks_created: int
    error_message: Optional[str]

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/sync", response_model=SyncStatusResponse)
async def sync_health_check() -> SyncStatusResponse:
    """Detailed sync health check endpoint."""
    health_data = sync_monitor.get_health_status()
    return SyncStatusResponse(**health_data)

@app.get("/monitoring/sync-history")
async def get_sync_history(limit: int = 10) -> Dict[str, Any]:
    """Get recent sync history for monitoring."""
    if limit > 50:
        limit = 50  # Prevent excessive data retrieval
    
    history = sync_monitor.get_sync_history(limit)
    return {
        "sync_history": history,
        "total_records": len(history),
        "requested_limit": limit
    }

@app.post("/sync/manual")
async def trigger_manual_sync() -> Dict[str, Any]:
    """Manually trigger a sync operation."""
    try:
        logger.info(" Manual sync triggered via API")
        _scheduled_rag_sync()
        
        # Get the latest health status
        health_data = sync_monitor.get_health_status()
        
        return {
            "status": "sync_triggered",
            "message": "Manual sync completed",
            "health": health_data
        }
    except Exception as e:
        logger.error(f"Manual sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Manual sync failed: {str(e)}")

@app.get("/monitoring/metrics")
async def get_sync_metrics() -> Dict[str, Any]:
    """Get comprehensive sync metrics for monitoring dashboard."""
    health_data = sync_monitor.get_health_status()
    history = sync_monitor.get_sync_history(20)
    
    # Calculate additional metrics
    successful_syncs = sum(1 for record in history if record["status"] == "success")
    failed_syncs = sum(1 for record in history if record["status"] == "failure")
    total_syncs = len(history)
    
    avg_duration = 0
    if successful_syncs > 0:
        durations = [record["duration"] for record in history if record["status"] == "success" and record["duration"]]
        avg_duration = sum(durations) / len(durations) if durations else 0
    
    return {
        "current_health": health_data,
        "recent_history": history,
        "statistics": {
            "total_syncs": total_syncs,
            "successful_syncs": successful_syncs,
            "failed_syncs": failed_syncs,
            "success_rate": (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0,
            "average_duration": round(avg_duration, 2),
            "last_24h_syncs": len([h for h in history if datetime.fromisoformat(h["timestamp"]) > datetime.utcnow() - timedelta(hours=24)])
        },
        "scheduler_info": {
            "interval_minutes": SYNC_INTERVAL_MIN,
            "next_sync": "Calculated from scheduler",
            "is_running": scheduler.running
        }
    }

@app.post("/run/{goal}")
async def run_goal(goal: str) -> dict[str, str]:
    """Kick off an agent run for a given goal (e.g., daily_planning)."""
    try:
        logger.info(f" Agent run triggered for goal: {goal}")
        result = run_agent(goal)
        logger.info(f" Agent run completed for goal: {goal}")
        return {"status": "completed", "result": str(result)}
    except Exception as exc:
        logger.error(f" Agent run failed for goal {goal}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.post("/tasks")
async def create_task(task: TaskIn) -> dict[str, str]:
    """Create a new Notion task through the agent's connector."""
    try:
        logger.info(f" Creating new task: {task.title}")
        notion = NotionConnector()
        task_id = notion.create_task(task.dict())
        logger.info(f" Task created successfully: {task_id}")
        return {"task_id": task_id}
    except Exception as e:
        logger.error(f" Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@app.get("/state/latest")
async def latest_state() -> dict:
    """Get the latest agent state from the database."""
    try:
        db = SupabaseConnector()
        state = db.get_latest_agent_state()
        if not state:
            raise HTTPException(status_code=404, detail="No state found")
        return state
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Failed to retrieve latest state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve state: {str(e)}")

# ---------------------------------------------------------------------------
# Dashboard endpoints for monitoring interface
# ---------------------------------------------------------------------------

@app.get("/dashboard/overview")
async def dashboard_overview() -> Dict[str, Any]:
    """Get overview data for the monitoring dashboard."""
    health_data = sync_monitor.get_health_status()
    recent_history = sync_monitor.get_sync_history(5)
    
    # Calculate system uptime (simplified)
    uptime_hours = 24  # This should be calculated from actual startup time
    
    return {
        "system_status": {
            "overall_health": health_data["is_healthy"],
            "uptime_hours": uptime_hours,
            "scheduler_status": "running" if scheduler.running else "stopped"
        },
        "sync_status": health_data,
        "recent_activity": recent_history,
        "quick_stats": {
            "total_tasks_processed": health_data["tasks_processed"],
            "total_chunks_created": health_data["chunks_created"],
            "error_rate": (health_data["total_errors"] / max(1, len(recent_history))) * 100
        }
    } 

@app.get("/metrics")
async def get_prometheus_metrics():
    """Export metrics in Prometheus format."""
    metrics_collector = get_metrics_collector()
    prometheus_data = metrics_collector.export_prometheus()
    
    return Response(
        content=prometheus_data,
        media_type="text/plain"
    )