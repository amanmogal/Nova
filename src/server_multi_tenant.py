"""
Multi-tenant FastAPI server for the Notion Agent SaaS platform.
Implements user isolation, authentication, and all agent functionality.
"""
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from src.db.multi_tenant_connector import multi_tenant_db, UserCreate, UserConfigCreate, SubscriptionTier
from src.tools.multi_tenant_rag_engine import create_user_rag_engine
from src.middleware.user_isolation import (
    UserIsolationMiddleware, get_current_user, get_current_user_optional,
    check_user_quota, rate_limit, require_subscription_tier, require_paid_subscription,
    check_trial_status, create_jwt_token
)
from src.config import get_settings

# Load settings
settings = get_settings()

# Security scheme
security = HTTPBearer()


# Pydantic models for API requests/responses
class UserRegistrationRequest(BaseModel):
    email: str
    notion_access_token: Optional[str] = None
    notion_workspace_id: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: str


class AgentRunRequest(BaseModel):
    goal: str = "daily_planning"
    query: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class TaskSearchRequest(BaseModel):
    query: str
    limit: int = 5


class TaskUpdateRequest(BaseModel):
    task_id: str
    properties: Dict[str, Any]


class TaskCreateRequest(BaseModel):
    task_data: Dict[str, Any]


class NotificationRequest(BaseModel):
    recipient: str
    subject: str
    message: str
    priority: str = "normal"


class UsageSummaryResponse(BaseModel):
    month: str
    total_tokens: int
    total_cost_usd: str
    operation_counts: Dict[str, int]
    subscription_tier: str
    monthly_requests: int
    trial_ends_at: Optional[str] = None


class SubscriptionUpgradeRequest(BaseModel):
    new_tier: SubscriptionTier


class TrialStatusResponse(BaseModel):
    is_trial: bool
    expired: Optional[bool] = None
    days_remaining: Optional[int] = None
    hours_remaining: Optional[int] = None
    trial_ends_at: Optional[str] = None
    message: str


# Background task for RAG sync
async def sync_user_rag_data(user_id: str):
    """Background task to sync RAG data for a user."""
    try:
        rag_engine = create_user_rag_engine(user_id)
        await rag_engine.sync_notion_data()
    except Exception as e:
        print(f"Error syncing RAG data for user {user_id}: {str(e)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting multi-tenant Notion Agent server...")
    
    # Create database tables if they don't exist
    try:
        # This would be handled by Supabase migrations in production
        print("Database tables ready")
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
    
    yield
    
    # Shutdown
    print("Shutting down multi-tenant Notion Agent server...")


# Create FastAPI app
app = FastAPI(
    title="Notion Agent - Multi-Tenant API",
    description="Multi-tenant API for autonomous Notion task management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add user isolation middleware
app.add_middleware(UserIsolationMiddleware)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# Authentication endpoints
@app.post("/auth/register")
async def register_user(request: UserRegistrationRequest):
    """Register a new user with 4-day trial."""
    try:
        # Create user
        user_data = UserCreate(
            email=request.email,
            notion_access_token=request.notion_access_token,
            notion_workspace_id=request.notion_workspace_id
        )
        
        user = multi_tenant_db.create_user(user_data)
        if not user:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        # Create JWT token
        token = create_jwt_token(user.id, user.email)
        
        return {
            "user": user,
            "token": token,
            "message": "User registered successfully with 4-day trial"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/auth/login")
async def login_user(request: UserLoginRequest):
    """Login user (simplified - in production, implement proper auth)."""
    try:
        # In a real implementation, you'd verify credentials
        # For now, we'll just return a token if the user exists
        
        # This is a simplified login - in production, implement proper authentication
        raise HTTPException(status_code=501, detail="Login not implemented yet")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# User management endpoints
@app.get("/user/profile")
@check_user_quota("get_profile")
async def get_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user profile."""
    try:
        multi_tenant_db.set_user_context(current_user["id"])
        user = multi_tenant_db.get_user()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")


@app.put("/user/notion-integration")
@check_user_quota("update_integration")
async def update_notion_integration(
    access_token: str,
    workspace_id: str,
    workspace_name: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user's Notion integration."""
    try:
        multi_tenant_db.set_user_context(current_user["id"])
        success = multi_tenant_db.update_user_notion_token(access_token, workspace_id, workspace_name)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update Notion integration")
        
        return {"message": "Notion integration updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update integration: {str(e)}")


@app.get("/user/config")
@check_user_quota("get_config")
async def get_user_config(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user configuration."""
    try:
        multi_tenant_db.set_user_context(current_user["id"])
        config = multi_tenant_db.get_user_config()
        
        if not config:
            raise HTTPException(status_code=404, detail="User configuration not found")
        
        return config
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user config: {str(e)}")


@app.put("/user/config")
@check_user_quota("update_config")
async def update_user_config(
    config_data: UserConfigCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user configuration."""
    try:
        multi_tenant_db.set_user_context(current_user["id"])
        success = multi_tenant_db.update_user_config(config_data)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update user configuration")
        
        return {"message": "User configuration updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


# Subscription management endpoints
@app.get("/user/trial-status")
async def get_trial_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user's trial status and remaining time."""
    try:
        multi_tenant_db.set_user_context(current_user["id"])
        trial_status = multi_tenant_db.get_trial_status()
        
        return TrialStatusResponse(**trial_status)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trial status: {str(e)}")


@app.post("/user/upgrade-subscription")
@require_paid_subscription()
async def upgrade_subscription(
    request: SubscriptionUpgradeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Upgrade user's subscription tier."""
    try:
        multi_tenant_db.set_user_context(current_user["id"])
        success = multi_tenant_db.upgrade_subscription(request.new_tier)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to upgrade subscription")
        
        return {
            "message": f"Successfully upgraded to {request.new_tier.value} plan",
            "new_tier": request.new_tier.value
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upgrade subscription: {str(e)}")


@app.get("/subscription/plans")
async def get_subscription_plans():
    """Get available subscription plans."""
    return {
        "plans": [
                         {
                 "tier": "trial",
                 "name": "Free Trial",
                 "duration": "7 days",
                 "requests_per_month": 120,
                 "tokens_per_month": 50000,
                 "price": "Free",
                 "features": [
                     "Basic agent functionality",
                     "Notion integration",
                     "Task management",
                     "7-day trial period"
                 ]
             },
            {
                "tier": "pro",
                "name": "Pro",
                "duration": "Monthly",
                "requests_per_month": 1000,
                "tokens_per_month": 1000000,
                "price": "$10/month",
                "features": [
                    "Full agent functionality",
                    "Advanced task management",
                    "Priority support",
                    "Usage analytics"
                ]
            },
            {
                "tier": "plus",
                "name": "Plus",
                "duration": "Monthly",
                "requests_per_month": 2500,
                "tokens_per_month": 2500000,
                "price": "$19/month",
                "features": [
                    "Everything in Pro",
                    "Advanced analytics",
                    "Custom integrations",
                    "API access"
                ]
            },
            {
                "tier": "teams",
                "name": "Teams",
                "duration": "Monthly",
                "requests_per_month": 5000,
                "tokens_per_month": 5000000,
                "price": "$49/month + $12/user",
                "features": [
                    "Everything in Plus",
                    "Team collaboration",
                    "Admin dashboard",
                    "Custom onboarding"
                ]
            }
        ]
    }


# Agent endpoints
@app.post("/agent/run")
@check_user_quota("agent_run")
@rate_limit("agent_run", 10, 60)  # 10 runs per minute
@check_trial_status()
async def run_agent(
    request: AgentRunRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Run the agent for the current user."""
    try:
        multi_tenant_db.set_user_context(current_user["id"])
        
        # Create user-specific RAG engine
        rag_engine = create_user_rag_engine(current_user["id"])
        
        # Build context using RAG
        context = rag_engine.build_context(request.query or request.goal)
        
        # In a full implementation, you'd run the agent here
        # For now, return a mock response
        result = {
            "goal": request.goal,
            "context": context,
            "actions_taken": [],
            "next_steps": [],
            "user_id": current_user["id"]
        }
        
        # Schedule background RAG sync
        background_tasks.add_task(sync_user_rag_data, current_user["id"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent run failed: {str(e)}")


@app.post("/agent/sync")
@check_user_quota("rag_sync")
@rate_limit("rag_sync", 5, 300)  # 5 syncs per 5 minutes
async def sync_rag_data(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Manually trigger RAG data sync for the user."""
    try:
        # Schedule background sync
        background_tasks.add_task(sync_user_rag_data, current_user["id"])
        
        return {"message": "RAG sync scheduled successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# Task management endpoints
@app.post("/tasks/search")
@check_user_quota("search_tasks")
@rate_limit("search_tasks", 20, 60)  # 20 searches per minute
async def search_tasks(
    request: TaskSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search for tasks using RAG."""
    try:
        multi_tenant_db.set_user_context(current_user["id"])
        
        # Create user-specific RAG engine
        rag_engine = create_user_rag_engine(current_user["id"])
        
        # Search tasks
        results = rag_engine.search_tasks(request.query, request.limit)
        
        return {
            "query": request.query,
            "results": results,
            "total_count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task search failed: {str(e)}")


@app.put("/tasks/{task_id}")
@check_user_quota("update_task")
@rate_limit("update_task", 30, 60)  # 30 updates per minute
async def update_task(
    task_id: str,
    request: TaskUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update a task in Notion."""
    try:
        multi_tenant_db.set_user_context(current_user["id"])
        
        # In a full implementation, you'd update the task in Notion
        # For now, return a mock response
        result = {
            "task_id": task_id,
            "updated_properties": request.properties,
            "success": True
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task update failed: {str(e)}")


@app.post("/tasks")
@check_user_quota("create_task")
@rate_limit("create_task", 20, 60)  # 20 creates per minute
async def create_task(
    request: TaskCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new task in Notion."""
    try:
        multi_tenant_db.set_user_context(current_user["id"])
        
        # In a full implementation, you'd create the task in Notion
        # For now, return a mock response
        result = {
            "task_id": "mock_task_id",
            "task_data": request.task_data,
            "success": True
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")


# Notification endpoints
@app.post("/notifications/send")
@check_user_quota("send_notification")
@rate_limit("send_notification", 10, 60)  # 10 notifications per minute
async def send_notification(
    request: NotificationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Send a notification."""
    try:
        multi_tenant_db.set_user_context(current_user["id"])
        
        # In a full implementation, you'd send the notification
        # For now, return a mock response
        result = {
            "recipient": request.recipient,
            "subject": request.subject,
            "message": request.message,
            "priority": request.priority,
            "sent": True
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification failed: {str(e)}")


# Usage and analytics endpoints
@app.get("/usage/summary")
@check_user_quota("get_usage")
async def get_usage_summary(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user's usage summary."""
    try:
        multi_tenant_db.set_user_context(current_user["id"])
        summary = multi_tenant_db.get_monthly_usage_summary()
        
        return UsageSummaryResponse(**summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage summary: {str(e)}")


@app.get("/usage/logs")
@check_user_quota("get_usage_logs")
async def get_usage_logs(
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user's usage logs."""
    try:
        multi_tenant_db.set_user_context(current_user["id"])
        logs = multi_tenant_db.get_usage_logs(limit, offset)
        
        return {
            "logs": logs,
            "total_count": len(logs),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage logs: {str(e)}")


@app.get("/usage/quota")
async def get_user_quota(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user's current quota status."""
    try:
        multi_tenant_db.set_user_context(current_user["id"])
        quota = multi_tenant_db.check_user_quota()
        
        return quota
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quota: {str(e)}")


# Admin endpoints (require Teams subscription)
@app.get("/admin/users")
@require_subscription_tier("teams")
async def get_all_users(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get all users (admin only - Teams plan)."""
    try:
        # In a full implementation, you'd implement admin functionality
        raise HTTPException(status_code=501, detail="Admin functionality not implemented yet")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Admin operation failed: {str(e)}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return {
        "error": "Internal server error",
        "status_code": 500,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.server_multi_tenant:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 