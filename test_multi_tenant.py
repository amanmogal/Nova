"""
Test script for multi-tenant backend implementation.
Tests user isolation, RAG engine, and API endpoints with new subscription model.
"""
import os
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

# Add src to path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Mock environment variables for testing
os.environ.setdefault("SUPABASE_URL", "https://mock-project.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "mock-supabase-key")
os.environ.setdefault("JWT_SECRET_KEY", "mock-jwt-secret-key")
os.environ.setdefault("DATABASE_URL", "postgresql://mock:mock@localhost:5432/mock")

from src.db.multi_tenant_connector import multi_tenant_db, UserCreate, UserConfigCreate, SubscriptionTier
from src.tools.multi_tenant_rag_engine import create_user_rag_engine
from src.middleware.user_isolation import create_jwt_token, get_user_from_token


class MultiTenantTester:
    """Test class for multi-tenant functionality."""
    
    def __init__(self):
        self.test_users = []
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results."""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
    
    def test_user_creation_with_trial(self):
        """Test user creation with 4-day trial period."""
        print("\n🧪 Testing User Creation with Trial Period...")
        
        try:
            # Create test user 1
            user1_data = UserCreate(
                email=f"test1_{uuid.uuid4()}@example.com",
                notion_access_token="test_token_1",
                notion_workspace_id="workspace_1"
            )
            
            # Set user context and create user
            multi_tenant_db.set_user_context(str(uuid.uuid4()))
            user1 = multi_tenant_db.create_user(user1_data)
            
            if user1:
                self.test_users.append(user1)
                self.log_test("User Creation with Trial", True, f"Created user: {user1.email} with trial tier")
                
                # Verify trial period is set
                if user1.trial_ends_at:
                    self.log_test("Trial Period Set", True, f"Trial ends at: {user1.trial_ends_at}")
                else:
                    self.log_test("Trial Period Set", False, "Trial end date not set")
                    return False
            else:
                self.log_test("User Creation with Trial", False, "Failed to create user")
                return False
            
            # Create test user 2
            user2_data = UserCreate(
                email=f"test2_{uuid.uuid4()}@example.com",
                notion_access_token="test_token_2",
                notion_workspace_id="workspace_2"
            )
            
            multi_tenant_db.set_user_context(str(uuid.uuid4()))
            user2 = multi_tenant_db.create_user(user2_data)
            
            if user2:
                self.test_users.append(user2)
                self.log_test("Second User Creation with Trial", True, f"Created user: {user2.email} with trial tier")
            else:
                self.log_test("Second User Creation with Trial", False, "Failed to create second user")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("User Creation with Trial", False, f"Exception: {str(e)}")
            return False
    
    def test_trial_status_checking(self):
        """Test trial status checking functionality."""
        print("\n🧪 Testing Trial Status Checking...")
        
        try:
            if not self.test_users:
                self.log_test("Trial Status Check", False, "No test users available")
                return False
            
            user = self.test_users[0]
            multi_tenant_db.set_user_context(user.id)
            
            # Get trial status
            trial_status = multi_tenant_db.get_trial_status()
            
            if trial_status.get("is_trial", False):
                self.log_test("Trial Status Check", True, f"Trial status: {trial_status.get('message')}")
                
                # Check if trial is not expired (should be valid for new users)
                if not trial_status.get("expired", True):
                    self.log_test("Trial Not Expired", True, f"Days remaining: {trial_status.get('days_remaining')}")
                else:
                    self.log_test("Trial Not Expired", False, "Trial should not be expired for new users")
                    return False
            else:
                self.log_test("Trial Status Check", False, "User should be on trial")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Trial Status Check", False, f"Exception: {str(e)}")
            return False
    
    def test_subscription_upgrade(self):
        """Test subscription upgrade functionality."""
        print("\n🧪 Testing Subscription Upgrade...")
        
        try:
            if not self.test_users:
                self.log_test("Subscription Upgrade", False, "No test users available")
                return False
            
            user = self.test_users[0]
            multi_tenant_db.set_user_context(user.id)
            
            # Upgrade to Pro plan
            success = multi_tenant_db.upgrade_subscription(SubscriptionTier.PRO)
            
            if success:
                # Verify upgrade
                updated_user = multi_tenant_db.get_user()
                if updated_user and updated_user.subscription_tier == SubscriptionTier.PRO:
                    self.log_test("Subscription Upgrade", True, f"Successfully upgraded to {updated_user.subscription_tier}")
                else:
                    self.log_test("Subscription Upgrade", False, "User tier not updated correctly")
                    return False
            else:
                self.log_test("Subscription Upgrade", False, "Failed to upgrade subscription")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Subscription Upgrade", False, f"Exception: {str(e)}")
            return False
    
    def test_user_config_isolation(self):
        """Test user configuration isolation."""
        print("\n🧪 Testing User Configuration Isolation...")
        
        try:
            if len(self.test_users) < 2:
                self.log_test("User Config Isolation", False, "Need at least 2 test users")
                return False
            
            user1 = self.test_users[0]
            user2 = self.test_users[1]
            
            # Set user 1 context and create config
            multi_tenant_db.set_user_context(user1.id)
            config1_data = UserConfigCreate(
                notion_tasks_db_id="tasks_db_1",
                notion_routines_db_id="routines_db_1",
                daily_planning_time="09:00",
                rag_sync_interval_min=30
            )
            
            success1 = multi_tenant_db.update_user_config(config1_data)
            if not success1:
                self.log_test("User Config Isolation", False, "Failed to update user 1 config")
                return False
            
            # Set user 2 context and create different config
            multi_tenant_db.set_user_context(user2.id)
            config2_data = UserConfigCreate(
                notion_tasks_db_id="tasks_db_2",
                notion_routines_db_id="routines_db_2",
                daily_planning_time="08:00",
                rag_sync_interval_min=60
            )
            
            success2 = multi_tenant_db.update_user_config(config2_data)
            if not success2:
                self.log_test("User Config Isolation", False, "Failed to update user 2 config")
                return False
            
            # Verify isolation - get configs back
            multi_tenant_db.set_user_context(user1.id)
            config1 = multi_tenant_db.get_user_config()
            
            multi_tenant_db.set_user_context(user2.id)
            config2 = multi_tenant_db.get_user_config()
            
            if (config1 and config2 and 
                config1.notion_tasks_db_id == "tasks_db_1" and 
                config2.notion_tasks_db_id == "tasks_db_2"):
                self.log_test("User Config Isolation", True, "Configs are properly isolated")
                return True
            else:
                self.log_test("User Config Isolation", False, "Configs are not properly isolated")
                return False
                
        except Exception as e:
            self.log_test("User Config Isolation", False, f"Exception: {str(e)}")
            return False
    
    def test_rag_engine_isolation(self):
        """Test RAG engine isolation between users."""
        print("\n🧪 Testing RAG Engine Isolation...")
        
        try:
            if len(self.test_users) < 2:
                self.log_test("RAG Engine Isolation", False, "Need at least 2 test users")
                return False
            
            user1 = self.test_users[0]
            user2 = self.test_users[1]
            
            # Create RAG engines for both users
            rag_engine1 = create_user_rag_engine(user1.id)
            rag_engine2 = create_user_rag_engine(user2.id)
            
            # Verify different paths
            if (rag_engine1.chroma_path != rag_engine2.chroma_path and
                f"user_{user1.id}" in str(rag_engine1.chroma_path) and
                f"user_{user2.id}" in str(rag_engine2.chroma_path)):
                self.log_test("RAG Engine Isolation", True, "RAG engines have separate paths")
                return True
            else:
                self.log_test("RAG Engine Isolation", False, "RAG engines share paths")
                return False
                
        except Exception as e:
            self.log_test("RAG Engine Isolation", False, f"Exception: {str(e)}")
            return False
    
    def test_usage_tracking(self):
        """Test usage tracking and quota management."""
        print("\n🧪 Testing Usage Tracking...")
        
        try:
            if not self.test_users:
                self.log_test("Usage Tracking", False, "No test users available")
                return False
            
            user = self.test_users[0]
            multi_tenant_db.set_user_context(user.id)
            
            # Log some usage
            success1 = multi_tenant_db.log_usage(
                operation_type="test_operation",
                operation_details={"test": "data"},
                tokens_used=100,
                cost_usd="0.01"
            )
            
            success2 = multi_tenant_db.log_usage(
                operation_type="another_operation",
                operation_details={"another": "test"},
                tokens_used=50,
                cost_usd="0.005"
            )
            
            if success1 and success2:
                # Get usage summary
                summary = multi_tenant_db.get_monthly_usage_summary()
                
                if summary and summary.get("total_tokens", 0) >= 150:
                    self.log_test("Usage Tracking", True, f"Tracked {summary.get('total_tokens')} tokens")
                    return True
                else:
                    self.log_test("Usage Tracking", False, "Usage not properly tracked")
                    return False
            else:
                self.log_test("Usage Tracking", False, "Failed to log usage")
                return False
                
        except Exception as e:
            self.log_test("Usage Tracking", False, f"Exception: {str(e)}")
            return False
    
    def test_quota_management(self):
        """Test quota checking and management."""
        print("\n🧪 Testing Quota Management...")
        
        try:
            if not self.test_users:
                self.log_test("Quota Management", False, "No test users available")
                return False
            
            user = self.test_users[0]
            multi_tenant_db.set_user_context(user.id)
            
            # Check quota
            quota = multi_tenant_db.check_user_quota()
            
            if quota and "allowed" in quota:
                self.log_test("Quota Management", True, f"Quota check successful: {quota.get('allowed')}")
                
                # Check if trial info is included
                if "trial_expires" in quota:
                    self.log_test("Trial Info in Quota", True, "Trial expiration info included")
                else:
                    self.log_test("Trial Info in Quota", False, "Trial expiration info missing")
                
                return True
            else:
                self.log_test("Quota Management", False, "Quota check failed")
                return False
                
        except Exception as e:
            self.log_test("Quota Management", False, f"Exception: {str(e)}")
            return False
    
    def test_jwt_token_management(self):
        """Test JWT token creation and validation."""
        print("\n🧪 Testing JWT Token Management...")
        
        try:
            if not self.test_users:
                self.log_test("JWT Token Management", False, "No test users available")
                return False
            
            user = self.test_users[0]
            
            # Create token
            token = create_jwt_token(user.id, user.email)
            
            if not token:
                self.log_test("JWT Token Management", False, "Failed to create token")
                return False
            
            # Validate token
            user_from_token = get_user_from_token(token)
            
            if user_from_token and user_from_token["id"] == user.id:
                self.log_test("JWT Token Management", True, "Token creation and validation successful")
                return True
            else:
                self.log_test("JWT Token Management", False, "Token validation failed")
                return False
                
        except Exception as e:
            self.log_test("JWT Token Management", False, f"Exception: {str(e)}")
            return False
    
    def test_agent_state_isolation(self):
        """Test agent state isolation between users."""
        print("\n🧪 Testing Agent State Isolation...")
        
        try:
            if len(self.test_users) < 2:
                self.log_test("Agent State Isolation", False, "Need at least 2 test users")
                return False
            
            user1 = self.test_users[0]
            user2 = self.test_users[1]
            
            # Save state for user 1
            multi_tenant_db.set_user_context(user1.id)
            state1 = {
                "messages": [{"role": "user", "content": "Hello from user 1"}],
                "context": {"user": "user1"},
                "preferences": {"theme": "dark"}
            }
            success1 = multi_tenant_db.save_agent_state(state1)
            
            # Save state for user 2
            multi_tenant_db.set_user_context(user2.id)
            state2 = {
                "messages": [{"role": "user", "content": "Hello from user 2"}],
                "context": {"user": "user2"},
                "preferences": {"theme": "light"}
            }
            success2 = multi_tenant_db.save_agent_state(state2)
            
            if not success1 or not success2:
                self.log_test("Agent State Isolation", False, "Failed to save agent states")
                return False
            
            # Retrieve states and verify isolation
            multi_tenant_db.set_user_context(user1.id)
            retrieved_state1 = multi_tenant_db.get_latest_agent_state()
            
            multi_tenant_db.set_user_context(user2.id)
            retrieved_state2 = multi_tenant_db.get_latest_agent_state()
            
            if (retrieved_state1 and retrieved_state2 and
                retrieved_state1["messages"][0]["content"] == "Hello from user 1" and
                retrieved_state2["messages"][0]["content"] == "Hello from user 2"):
                self.log_test("Agent State Isolation", True, "Agent states are properly isolated")
                return True
            else:
                self.log_test("Agent State Isolation", False, "Agent states are not properly isolated")
                return False
                
        except Exception as e:
            self.log_test("Agent State Isolation", False, f"Exception: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data."""
        print("\n🧹 Cleaning up test data...")
        
        try:
            for user in self.test_users:
                # Clean up RAG engine data
                rag_engine = create_user_rag_engine(user.id)
                rag_engine.cleanup_user_data()
                
                # Note: In a real implementation, you'd also delete user records
                # For testing, we'll just clean up the ChromaDB data
            
            self.log_test("Cleanup", True, f"Cleaned up data for {len(self.test_users)} users")
            
        except Exception as e:
            self.log_test("Cleanup", False, f"Exception during cleanup: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting Multi-Tenant Backend Tests (Updated Subscription Model)...")
        print("=" * 70)
        
        tests = [
            self.test_user_creation_with_trial,
            self.test_trial_status_checking,
            self.test_subscription_upgrade,
            self.test_user_config_isolation,
            self.test_rag_engine_isolation,
            self.test_usage_tracking,
            self.test_quota_management,
            self.test_jwt_token_management,
            self.test_agent_state_isolation
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                self.log_test(test.__name__, False, f"Test crashed: {str(e)}")
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Multi-tenant backend with new subscription model is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total


async def main():
    """Main test function."""
    tester = MultiTenantTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Multi-tenant backend with updated subscription model is ready!")
        print("\n📋 New Subscription Model:")
        print("   • 4-day Free Trial (50 requests, 50k tokens)")
        print("   • Pro Plan ($19/month - 1k requests, 1M tokens)")
        print("   • Plus Plan ($39/month - 2.5k requests, 2.5M tokens)")
        print("   • Teams Plan ($99/month - 5k requests, 5M tokens)")
        print("\nNext steps:")
        print("1. Set up Supabase database tables")
        print("2. Configure environment variables")
        print("3. Test the FastAPI server")
        print("4. Move to Week 3: User Dashboard")
    else:
        print("\n❌ Some issues need to be resolved before proceeding.")


if __name__ == "__main__":
    asyncio.run(main()) 