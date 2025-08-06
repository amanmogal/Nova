"""
Multi-tenant database schema.
Implements user isolation, row-level security, and user-specific configurations.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class SubscriptionTier(str, Enum):
    """User subscription tiers."""
    TRIAL = "trial"  # 4-day free trial
    PRO = "pro"      # Individual plan
    PLUS = "plus"    # Enhanced individual and professional plan
    TEAMS = "teams"  # Team collaboration plan


class User(Base):
    """User table for multi-tenant support."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notion integration
    notion_access_token = Column(Text, nullable=True)
    notion_workspace_id = Column(String(255), nullable=True)
    notion_workspace_name = Column(String(255), nullable=True)
    
    # Subscription and billing
    subscription_tier = Column(String(50), default=SubscriptionTier.TRIAL, nullable=False)
    subscription_status = Column(String(50), default="active", nullable=False)
    trial_ends_at = Column(DateTime, nullable=True)  # When trial expires
    billing_customer_id = Column(String(255), nullable=True)
    
    # Usage tracking
    monthly_requests = Column(Integer, default=0, nullable=False)
    monthly_tokens_used = Column(Integer, default=0, nullable=False)
    last_activity = Column(DateTime, nullable=True)
    
    # Team information (for Teams plan)
    team_id = Column(UUID(as_uuid=True), nullable=True)  # Team they belong to
    team_role = Column(String(50), nullable=True)  # admin, member, etc.
    
    # Relationships
    config = relationship("UserConfig", back_populates="user", uselist=False)
    agent_states = relationship("AgentState", back_populates="user")
    usage_logs = relationship("UsageLog", back_populates="user")


class UserConfig(Base):
    """User-specific configuration settings."""
    __tablename__ = "user_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notion database IDs
    notion_tasks_db_id = Column(String(255), nullable=True)
    notion_routines_db_id = Column(String(255), nullable=True)
    
    # Agent preferences
    daily_planning_time = Column(String(10), default="08:00", nullable=False)
    notification_preferences = Column(JSON, default=dict, nullable=False)
    agent_personality = Column(JSON, default=dict, nullable=False)
    
    # RAG settings
    rag_sync_interval_min = Column(Integer, default=60, nullable=False)
    max_context_length = Column(Integer, default=4000, nullable=False)
    
    # Performance settings
    enable_cost_optimization = Column(Boolean, default=True, nullable=False)
    enable_performance_monitoring = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="config")


class AgentState(Base):
    """Agent state per user."""
    __tablename__ = "agent_states"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Agent state data
    conversation_history = Column(JSON, default=list, nullable=False)
    context = Column(JSON, default=dict, nullable=False)
    preferences = Column(JSON, default=dict, nullable=False)
    last_activity = Column(DateTime, nullable=True)
    
    # Session tracking
    session_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="agent_states")


class UsageLog(Base):
    """Usage tracking per user."""
    __tablename__ = "usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Operation details
    operation_type = Column(String(100), nullable=False)
    operation_details = Column(JSON, default=dict, nullable=False)
    
    # Cost tracking
    tokens_used = Column(Integer, default=0, nullable=False)
    cost_usd = Column(String(20), default="0.00", nullable=False)
    
    # Performance metrics
    response_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")


# Pydantic models for API responses
class UserCreate(BaseModel):
    """Model for creating a new user."""
    email: str = Field(..., description="User email address")
    notion_access_token: Optional[str] = Field(None, description="Notion OAuth access token")
    notion_workspace_id: Optional[str] = Field(None, description="Notion workspace ID")


class UserResponse(BaseModel):
    """Model for user API responses."""
    id: str
    email: str
    created_at: datetime
    subscription_tier: SubscriptionTier
    trial_ends_at: Optional[datetime] = None
    notion_workspace_name: Optional[str] = None
    last_activity: Optional[datetime] = None
    team_id: Optional[str] = None
    team_role: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserConfigCreate(BaseModel):
    """Model for creating user configuration."""
    notion_tasks_db_id: Optional[str] = None
    notion_routines_db_id: Optional[str] = None
    daily_planning_time: str = "08:00"
    notification_preferences: Dict[str, Any] = {}
    agent_personality: Dict[str, Any] = {}
    rag_sync_interval_min: int = 60
    max_context_length: int = 4000
    enable_cost_optimization: bool = True
    enable_performance_monitoring: bool = True


class UserConfigResponse(BaseModel):
    """Model for user configuration API responses."""
    id: str
    user_id: str
    notion_tasks_db_id: Optional[str] = None
    notion_routines_db_id: Optional[str] = None
    daily_planning_time: str
    notification_preferences: Dict[str, Any]
    agent_personality: Dict[str, Any]
    rag_sync_interval_min: int
    max_context_length: int
    enable_cost_optimization: bool
    enable_performance_monitoring: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UsageLogResponse(BaseModel):
    """Model for usage log API responses."""
    id: str
    user_id: str
    operation_type: str
    operation_details: Dict[str, Any]
    tokens_used: int
    cost_usd: str
    response_time_ms: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Row-level security policies (Supabase)
RLS_POLICIES = {
    "users": """
        -- Users can only see their own data
        CREATE POLICY "Users can view own data" ON users
        FOR ALL USING (auth.uid() = id);
    """,
    
    "user_configs": """
        -- Users can only access their own config
        CREATE POLICY "Users can manage own config" ON user_configs
        FOR ALL USING (auth.uid() = user_id);
    """,
    
    "agent_states": """
        -- Users can only access their own agent states
        CREATE POLICY "Users can manage own agent states" ON agent_states
        FOR ALL USING (auth.uid() = user_id);
    """,
    
    "usage_logs": """
        -- Users can only view their own usage logs
        CREATE POLICY "Users can view own usage logs" ON usage_logs
        FOR ALL USING (auth.uid() = user_id);
    """
}


def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)


def enable_rls(connection):
    """Enable row-level security on all tables."""
    for table_name, policy in RLS_POLICIES.items():
        connection.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")
        connection.execute(policy) 