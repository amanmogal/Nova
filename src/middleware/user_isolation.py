"""
User isolation middleware for FastAPI.
Handles user context, authentication, and request isolation.
"""
import os
import jwt
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextvars import ContextVar

from src.db.multi_tenant_connector import multi_tenant_db, current_user_id

# Security scheme for JWT tokens
security = HTTPBearer()

# Context variable for current request user
current_request_user: ContextVar[Optional[Dict[str, Any]]] = ContextVar('current_request_user', default=None)


class UserIsolationMiddleware:
    """Middleware for user isolation and context management."""
    
    def __init__(self, app):
        self.app = app
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key")
        self.algorithm = "HS256"
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract user from request
            request = Request(scope, receive)
            user = await self._get_user_from_request(request)
            
            if user:
                # Set user context for this request
                current_request_user.set(user)
                multi_tenant_db.set_user_context(user["id"])
            
            # Add user to scope for downstream use
            scope["user"] = user
        
        await self.app(scope, receive, send)
    
    async def _get_user_from_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract user information from request headers."""
        try:
            # Check for Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return None
            
            # Extract token
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
            else:
                return None
            
            # Decode JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            
            if not user_id:
                return None
            
            # Get user from database
            multi_tenant_db.set_user_context(user_id)
            user = multi_tenant_db.get_user()
            
            if user:
                return {
                    "id": user.id,
                    "email": user.email,
                    "subscription_tier": user.subscription_tier,
                    "notion_workspace_id": user.notion_workspace_id,
                    "trial_ends_at": user.trial_ends_at,
                    "team_id": user.team_id,
                    "team_role": user.team_role
                }
            
            return None
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            print(f"Error extracting user from request: {str(e)}")
            return None


def get_current_user() -> Dict[str, Any]:
    """Dependency to get current user from request context."""
    user = current_request_user.get()
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def get_current_user_optional() -> Optional[Dict[str, Any]]:
    """Dependency to get current user (optional)."""
    return current_request_user.get()


def require_user_context():
    """Decorator to ensure user context is available."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                raise HTTPException(status_code=401, detail="User context required")
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def check_user_quota(operation_type: str = None):
    """Decorator to check user quota before operation."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                raise HTTPException(status_code=401, detail="User context required")
            
            # Check quota
            quota_check = multi_tenant_db.check_user_quota(operation_type)
            if not quota_check.get("allowed", False):
                raise HTTPException(
                    status_code=429, 
                    detail=f"Quota exceeded: {quota_check.get('reason')}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class UserContextManager:
    """Context manager for user operations."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.previous_user = None
    
    def __enter__(self):
        self.previous_user = current_user_id.get()
        multi_tenant_db.set_user_context(self.user_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_user:
            multi_tenant_db.set_user_context(self.previous_user)
        else:
            multi_tenant_db.clear_user_context()


def create_user_context(user_id: str) -> UserContextManager:
    """Create a user context manager."""
    return UserContextManager(user_id)


# Rate limiting utilities
class RateLimiter:
    """Simple rate limiter for user operations."""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, user_id: str, operation: str, limit: int, window_seconds: int = 60) -> bool:
        """Check if user is allowed to perform operation."""
        import time
        current_time = time.time()
        key = f"{user_id}:{operation}"
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [req_time for req_time in self.requests[key] 
                            if current_time - req_time < window_seconds]
        
        # Check if under limit
        if len(self.requests[key]) < limit:
            self.requests[key].append(current_time)
            return True
        
        return False


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(operation: str, limit: int, window_seconds: int = 60):
    """Decorator for rate limiting."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                raise HTTPException(status_code=401, detail="User context required")
            
            if not rate_limiter.is_allowed(user["id"], operation, limit, window_seconds):
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded for {operation}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Subscription tier checks
def require_subscription_tier(min_tier: str):
    """Decorator to require minimum subscription tier."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                raise HTTPException(status_code=401, detail="User context required")
            
            # Define tier hierarchy
            tier_hierarchy = {
                "trial": 0,
                "pro": 1,
                "plus": 2,
                "teams": 3
            }
            
            user_tier = user.get("subscription_tier", "trial")
            user_tier_level = tier_hierarchy.get(user_tier.lower(), 0)
            required_tier_level = tier_hierarchy.get(min_tier.lower(), 0)
            
            if user_tier_level < required_tier_level:
                raise HTTPException(
                    status_code=403,
                    detail=f"Subscription tier '{min_tier}' required. Current tier: '{user_tier}'"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_paid_subscription():
    """Decorator to require a paid subscription (not trial)."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                raise HTTPException(status_code=401, detail="User context required")
            
            user_tier = user.get("subscription_tier", "trial")
            if user_tier.lower() == "trial":
                raise HTTPException(
                    status_code=403,
                    detail="Paid subscription required. Please upgrade from trial to continue."
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def check_trial_status():
    """Decorator to check trial status and warn if expiring soon."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                raise HTTPException(status_code=401, detail="User context required")
            
            user_tier = user.get("subscription_tier", "trial")
            if user_tier.lower() == "trial":
                # Check trial status
                trial_status = multi_tenant_db.get_trial_status()
                if trial_status.get("expired", False):
                    raise HTTPException(
                        status_code=403,
                        detail="Trial has expired. Please upgrade to continue using the service."
                    )
                elif trial_status.get("days_remaining", 0) <= 1:
                    # Add warning header for expiring trial
                    # This would be handled in the response headers
                    pass
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Utility functions for user management
def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """Extract user from JWT token."""
    try:
        secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        if user_id:
            multi_tenant_db.set_user_context(user_id)
            user = multi_tenant_db.get_user()
            if user:
                return {
                    "id": user.id,
                    "email": user.email,
                    "subscription_tier": user.subscription_tier,
                    "notion_workspace_id": user.notion_workspace_id,
                    "trial_ends_at": user.trial_ends_at,
                    "team_id": user.team_id,
                    "team_role": user.team_role
                }
        
        return None
    except Exception:
        return None


def create_jwt_token(user_id: str, email: str) -> str:
    """Create JWT token for user."""
    import time
    secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(time.time()),
        "exp": int(time.time()) + (24 * 60 * 60)  # 24 hours
    }
    
    return jwt.encode(payload, secret_key, algorithm="HS256")


# Error handling for user operations
class UserOperationError(Exception):
    """Base exception for user operation errors."""
    pass


class UserQuotaExceededError(UserOperationError):
    """Exception raised when user quota is exceeded."""
    pass


class UserContextError(UserOperationError):
    """Exception raised when user context is missing or invalid."""
    pass


class TrialExpiredError(UserOperationError):
    """Exception raised when user's trial has expired."""
    pass


def handle_user_operation_error(func):
    """Decorator to handle user operation errors."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except UserQuotaExceededError as e:
            raise HTTPException(status_code=429, detail=str(e))
        except UserContextError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except TrialExpiredError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper 