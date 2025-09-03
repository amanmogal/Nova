"""Central configuration for the Nova Notion-Agent.

Reads environment variables (or a `.env` file) once, validates them, and makes
them available through `get_settings()`.  Uses Pydantic so we get clear error
messages when a required key is missing.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    # ── Core Keys ─────────────────────────────────────────────────────────────
    GOOGLE_API_KEY: str = Field(..., env="GOOGLE_API_KEY")
    NOTION_API_KEY: str = Field(..., env="NOTION_API_KEY")

    # Supabase
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_KEY: str = Field(..., env="SUPABASE_KEY")
    
    # Monitoring & Analytics
    LANGSMITH_API_KEY: str | None = Field(None, env="LANGSMITH_API_KEY")
    LANGSMITH_PROJECT: str = Field("notion-agent", env="LANGSMITH_PROJECT")
    LANGSMITH_TRACING_V2: bool = Field(True, env="LANGSMITH_TRACING_V2")
    # Optional in local/dev
    GRAFANA_USERNAME: str | None = Field(None, env="GRAFANA_USERNAME")
    GRAFANA_API_KEY: str | None = Field(None, env="GRAFANA_API_KEY")
    GRAFANA_PROMETHEUS_URL: str | None = Field(None, env="GRAFANA_PROMETHEUS_URL")  
    
    # Cost Management
    DAILY_COST_LIMIT: float = Field(1.00, env="DAILY_COST_LIMIT")
    MONTHLY_COST_LIMIT: float = Field(25.00, env="MONTHLY_COST_LIMIT")
    OPERATION_COST_THRESHOLD: float = Field(0.01, env="OPERATION_COST_THRESHOLD")
    
    # Performance Monitoring
    ENABLE_PERFORMANCE_MONITORING: bool = Field(True, env="ENABLE_PERFORMANCE_MONITORING")
    ENABLE_COST_OPTIMIZATION: bool = Field(True, env="ENABLE_COST_OPTIMIZATION")
    ENABLE_FEEDBACK_COLLECTION: bool = Field(True, env="ENABLE_FEEDBACK_COLLECTION")

    # ── Local options / misc ─────────────────────────────────────────────────
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    # Notion Specific
    notion_tasks_database_id: str | None = Field(None, env="NOTION_TASKS_DATABASE_ID")
    notion_routines_database_id: str | None = Field(None, env="NOTION_ROUTINES_DATABASE_ID")

    # Gemini Model
    gemini_model: str = Field("gemini-2.5-flash", env="GEMINI_MODEL")

    # ChromaDB
    chroma_db_path: str = Field("./data/chroma", env="CHROMA_DB_PATH")

    # Email
    email_sender: str | None = Field(None, env="EMAIL_SENDER")
    email_api_key: str | None = Field(None, env="EMAIL_API_KEY")

    # Scheduling
    daily_planning_time: str = Field("08:00", env="DAILY_PLANNING_TIME")
    calendar_view_start: str = Field("10:00", env="CALENDAR_VIEW_START")
    calendar_view_end: str = Field("02:00", env="CALENDAR_VIEW_END")

    # RAG Sync
    rag_sync_interval_min: int = Field(60, env="RAG_SYNC_INTERVAL_MIN")

    class Config:
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields instead of raising errors

    # Cast truthy strings → booleans
    @validator("LANGSMITH_TRACING_V2", pre=True)
    def _cast_bool(cls, v):  # noqa: N805
        if isinstance(v, bool):
            return v
        return str(v).lower() in {"1", "true", "yes"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a singleton Settings instance (cached)."""
    return Settings() 