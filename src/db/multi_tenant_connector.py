"""
Multi-tenant database connector for the Notion Agent SaaS platform.
Handles user isolation, context management, and user-specific operations.
"""
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from contextvars import ContextVar
from functools import wraps

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from supabase import create_client, Client
from dotenv import load_dotenv

from .multi_tenant_schema import (
    Base, User, UserConfig, AgentState, UsageLog,
    UserCreate, UserResponse, UserConfigCreate, UserConfigResponse,
    UsageLogResponse, SubscriptionTier
)

# Load environment variables
load_dotenv()

# Context variable for current user ID
current_user_id: ContextVar[Optional[str]] = ContextVar('current_user_id', default=None)


def require_user_context(func):
    """Decorator to ensure user context is available."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user_id.get() is None:
            raise ValueError("User context is required but not set")
        return func(*args, **kwargs)
    return wrapper


class MultiTenantConnector:
    """
    Multi-tenant database connector with user isolation.
    Handles all database operations with proper user context.
    """
    
    def __init__(self):
        """Initialize the multi-tenant connector."""
        # Supabase client for auth and real-time features
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        
        self.supabase_client = create_client(supabase_url, supabase_key)
        
        # SQLAlchemy setup for complex queries
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            self.engine = create_engine(database_url)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        else:
            self.engine = None
            self.SessionLocal = None
    
    def set_user_context(self, user_id: str):
        """Set the current user context for all operations."""
        current_user_id.set(user_id)
    
    def get_user_context(self) -> Optional[str]:
        """Get the current user context."""
        return current_user_id.get()
    
    def clear_user_context(self):
        """Clear the current user context."""
        current_user_id.set(None)
    
    @require_user_context
    def create_user(self, user_data: UserCreate) -> Optional[UserResponse]:
        """Create a new user with 4-day trial."""
        try:
            user_id = str(uuid.uuid4())
            
            # Set trial end date (7 days from now)
            trial_ends_at = datetime.utcnow() + timedelta(days=7)
            
            # Create user record
            user_record = {
                "id": user_id,
                "email": user_data.email,
                "notion_access_token": user_data.notion_access_token,
                "notion_workspace_id": user_data.notion_workspace_id,
                "subscription_tier": SubscriptionTier.TRIAL.value,
                "subscription_status": "active",
                "trial_ends_at": trial_ends_at.isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase_client.table("users").insert(user_record).execute()
            
            if response.data:
                # Create default user config
                self._create_default_user_config(user_id)
                return UserResponse(**response.data[0])
            
            return None
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return None
    
    @require_user_context
    def get_user(self) -> Optional[UserResponse]:
        """Get current user information."""
        try:
            user_id = self.get_user_context()
            response = self.supabase_client.table("users").select("*").eq("id", user_id).execute()
            
            if response.data:
                return UserResponse(**response.data[0])
            return None
        except Exception as e:
            print(f"Error getting user: {str(e)}")
            return None
    
    @require_user_context
    def update_user_notion_token(self, access_token: str, workspace_id: str, workspace_name: str = None):
        """Update user's Notion integration details."""
        try:
            user_id = self.get_user_context()
            update_data = {
                "notion_access_token": access_token,
                "notion_workspace_id": workspace_id,
                "notion_workspace_name": workspace_name,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase_client.table("users").update(update_data).eq("id", user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error updating user Notion token: {str(e)}")
            return False
    
    def _create_default_user_config(self, user_id: str):
        """Create default configuration for a new user."""
        try:
            config_data = {
                "user_id": user_id,
                "daily_planning_time": "08:00",
                "notification_preferences": {},
                "agent_personality": {},
                "rag_sync_interval_min": 60,
                "max_context_length": 4000,
                "enable_cost_optimization": True,
                "enable_performance_monitoring": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.supabase_client.table("user_configs").insert(config_data).execute()
        except Exception as e:
            print(f"Error creating default user config: {str(e)}")
    
    @require_user_context
    def get_user_config(self) -> Optional[UserConfigResponse]:
        """Get current user's configuration."""
        try:
            user_id = self.get_user_context()
            response = self.supabase_client.table("user_configs").select("*").eq("user_id", user_id).execute()
            
            if response.data:
                return UserConfigResponse(**response.data[0])
            return None
        except Exception as e:
            print(f"Error getting user config: {str(e)}")
            return None
    
    @require_user_context
    def update_user_config(self, config_data: UserConfigCreate) -> bool:
        """Update current user's configuration."""
        try:
            user_id = self.get_user_context()
            update_data = {
                **config_data.dict(exclude_unset=True),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase_client.table("user_configs").update(update_data).eq("user_id", user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error updating user config: {str(e)}")
            return False
    
    @require_user_context
    def save_agent_state(self, state: Dict[str, Any], session_id: str = None) -> bool:
        """Save agent state for current user."""
        try:
            user_id = self.get_user_context()
            
            state_data = {
                "user_id": user_id,
                "conversation_history": state.get("messages", []),
                "context": state.get("context", {}),
                "preferences": state.get("preferences", {}),
                "session_id": session_id,
                "is_active": True,
                "last_activity": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase_client.table("agent_states").insert(state_data).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error saving agent state: {str(e)}")
            return False
    
    @require_user_context
    def get_latest_agent_state(self) -> Optional[Dict[str, Any]]:
        """Get the latest agent state for current user."""
        try:
            user_id = self.get_user_context()
            response = self.supabase_client.table("agent_states") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("is_active", True) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            
            if response.data:
                state = response.data[0]
                return {
                    "messages": state.get("conversation_history", []),
                    "context": state.get("context", {}),
                    "preferences": state.get("preferences", {}),
                    "session_id": state.get("session_id"),
                    "last_activity": state.get("last_activity")
                }
            return None
        except Exception as e:
            print(f"Error getting latest agent state: {str(e)}")
            return None
    
    @require_user_context
    def log_usage(self, operation_type: str, operation_details: Dict[str, Any], 
                  tokens_used: int = 0, cost_usd: str = "0.00", 
                  response_time_ms: int = None, success: bool = True, 
                  error_message: str = None) -> bool:
        """Log usage for current user."""
        try:
            user_id = self.get_user_context()
            
            usage_data = {
                "user_id": user_id,
                "operation_type": operation_type,
                "operation_details": operation_details,
                "tokens_used": tokens_used,
                "cost_usd": cost_usd,
                "response_time_ms": response_time_ms,
                "success": success,
                "error_message": error_message,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase_client.table("usage_logs").insert(usage_data).execute()
            
            # Update user's monthly usage
            if success:
                self._update_monthly_usage(user_id, tokens_used)
            
            return len(response.data) > 0
        except Exception as e:
            print(f"Error logging usage: {str(e)}")
            return False
    
    def _update_monthly_usage(self, user_id: str, tokens_used: int):
        """Update user's monthly usage statistics."""
        try:
            # Get current month's usage
            current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Update monthly tokens used
            self.supabase_client.table("users") \
                .update({
                    "monthly_tokens_used": text("monthly_tokens_used + :tokens"),
                    "last_activity": datetime.utcnow().isoformat()
                }) \
                .eq("id", user_id) \
                .execute(params={"tokens": tokens_used})
        except Exception as e:
            print(f"Error updating monthly usage: {str(e)}")
    
    @require_user_context
    def get_usage_logs(self, limit: int = 50, offset: int = 0) -> List[UsageLogResponse]:
        """Get usage logs for current user."""
        try:
            user_id = self.get_user_context()
            response = self.supabase_client.table("usage_logs") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .range(offset, offset + limit - 1) \
                .execute()
            
            return [UsageLogResponse(**log) for log in response.data]
        except Exception as e:
            print(f"Error getting usage logs: {str(e)}")
            return []
    
    @require_user_context
    def get_monthly_usage_summary(self) -> Dict[str, Any]:
        """Get monthly usage summary for current user."""
        try:
            user_id = self.get_user_context()
            user = self.get_user()
            
            if not user:
                return {}
            
            # Get current month's logs
            current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            response = self.supabase_client.table("usage_logs") \
                .select("tokens_used, cost_usd, operation_type") \
                .eq("user_id", user_id) \
                .gte("created_at", current_month.isoformat()) \
                .execute()
            
            total_tokens = sum(log.get("tokens_used", 0) for log in response.data)
            total_cost = sum(float(log.get("cost_usd", "0.00")) for log in response.data)
            operation_counts = {}
            
            for log in response.data:
                op_type = log.get("operation_type", "unknown")
                operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
            
            return {
                "month": current_month.strftime("%Y-%m"),
                "total_tokens": total_tokens,
                "total_cost_usd": f"{total_cost:.2f}",
                "operation_counts": operation_counts,
                "subscription_tier": user.subscription_tier,
                "monthly_requests": user.monthly_requests,
                "trial_ends_at": user.trial_ends_at
            }
        except Exception as e:
            print(f"Error getting monthly usage summary: {str(e)}")
            return {}
    
    def check_user_quota(self, operation_type: str = None) -> Dict[str, Any]:
        """Check if user has quota remaining for operations."""
        try:
            user = self.get_user()
            if not user:
                return {"allowed": False, "reason": "User not found"}
            
            # Check if trial has expired
            if user.subscription_tier == SubscriptionTier.TRIAL and user.trial_ends_at:
                trial_end = user.trial_ends_at
                if isinstance(trial_end, str):
                    trial_end = datetime.fromisoformat(trial_end.replace('Z', '+00:00'))
                
                if datetime.utcnow() > trial_end:
                    return {"allowed": False, "reason": "Trial period has expired. Please upgrade to continue."}
            
            summary = self.get_monthly_usage_summary()
            
            # Check subscription tier limits
            tier_limits = {
                SubscriptionTier.TRIAL: {"requests": 120, "tokens": 50000},  # 7-day trial limits
                SubscriptionTier.PRO: {"requests": 1000, "tokens": 1000000},
                SubscriptionTier.PLUS: {"requests": 2500, "tokens": 2500000},
                SubscriptionTier.TEAMS: {"requests": 5000, "tokens": 5000000}
            }
            
            limits = tier_limits.get(user.subscription_tier, tier_limits[SubscriptionTier.TRIAL])
            
            # Check if user has exceeded limits
            if summary.get("monthly_requests", 0) >= limits["requests"]:
                return {"allowed": False, "reason": "Monthly request limit exceeded"}
            
            if summary.get("total_tokens", 0) >= limits["tokens"]:
                return {"allowed": False, "reason": "Monthly token limit exceeded"}
            
            return {
                "allowed": True,
                "remaining_requests": limits["requests"] - summary.get("monthly_requests", 0),
                "remaining_tokens": limits["tokens"] - summary.get("total_tokens", 0),
                "trial_expires": user.trial_ends_at if user.subscription_tier == SubscriptionTier.TRIAL else None
            }
        except Exception as e:
            print(f"Error checking user quota: {str(e)}")
            return {"allowed": False, "reason": "Error checking quota"}
    
    @require_user_context
    def upgrade_subscription(self, new_tier: SubscriptionTier) -> bool:
        """Upgrade user's subscription tier."""
        try:
            user_id = self.get_user_context()
            
            update_data = {
                "subscription_tier": new_tier.value,
                "trial_ends_at": None,  # Clear trial end date
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase_client.table("users").update(update_data).eq("id", user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error upgrading subscription: {str(e)}")
            return False
    
    @require_user_context
    def get_trial_status(self) -> Dict[str, Any]:
        """Get user's trial status and remaining time."""
        try:
            user = self.get_user()
            if not user:
                return {"error": "User not found"}
            
            if user.subscription_tier != SubscriptionTier.TRIAL:
                return {"is_trial": False, "message": "User is not on trial"}
            
            if not user.trial_ends_at:
                return {"is_trial": True, "error": "Trial end date not set"}
            
            trial_end = user.trial_ends_at
            if isinstance(trial_end, str):
                trial_end = datetime.fromisoformat(trial_end.replace('Z', '+00:00'))
            
            now = datetime.utcnow()
            time_remaining = trial_end - now
            
            if time_remaining.total_seconds() <= 0:
                return {
                    "is_trial": True,
                    "expired": True,
                    "message": "Trial has expired"
                }
            
            days_remaining = time_remaining.days
            hours_remaining = time_remaining.seconds // 3600
            
            return {
                "is_trial": True,
                "expired": False,
                "days_remaining": days_remaining,
                "hours_remaining": hours_remaining,
                "trial_ends_at": user.trial_ends_at,
                "message": f"Trial expires in {days_remaining} days, {hours_remaining} hours"
            }
        except Exception as e:
            print(f"Error getting trial status: {str(e)}")
            return {"error": str(e)}


# Global instance
multi_tenant_db = MultiTenantConnector() 