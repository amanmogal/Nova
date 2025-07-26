"""Central configuration for the Nova Notion-Agent.

Reads environment variables (or a `.env` file) once, validates them, and makes
them available through `get_settings()`.  Uses Pydantic so we get clear error
messages when a required key is missing.
"""
from functools import lru_cache
from pydantic import BaseSettings, Field, validator


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

    class Config:
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"

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