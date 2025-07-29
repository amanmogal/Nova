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

    # LangSmith (optional but recommended for tracing)
    LANGCHAIN_API_KEY: str | None = Field(None, env="LANGCHAIN_API_KEY")
    LANGCHAIN_TRACING_V2: bool = Field(False, env="LANGCHAIN_TRACING_V2")
    LANGCHAIN_PROJECT: str = Field("Nova-Agent", env="LANGCHAIN_PROJECT")

    # ── Local options / misc ─────────────────────────────────────────────────
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    # Notion Specific
    notion_tasks_database_id: str = Field(..., env="NOTION_TASKS_DATABASE_ID")
    notion_routines_database_id: str = Field(..., env="NOTION_ROUTINES_DATABASE_ID")

    # Gemini Model
    gemini_model: str = Field("gemini-pro", env="GEMINI_MODEL")

    # ChromaDB
    chroma_db_path: str = Field("./data/chroma", env="CHROMA_DB_PATH")

    # Email
    email_sender: str = Field(..., env="EMAIL_SENDER")
    email_api_key: str = Field(..., env="EMAIL_API_KEY")

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
    @validator("LANGCHAIN_TRACING_V2", pre=True)
    def _cast_bool(cls, v):  # noqa: N805
        if isinstance(v, bool):
            return v
        return str(v).lower() in {"1", "true", "yes"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a singleton Settings instance (cached)."""
    return Settings() 