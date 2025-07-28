"""
Supabase database connector for agent state management.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()


class SupabaseConnector:
    """
    Connector for Supabase database.
    Handles the agent's state, execution history, and learned preferences.
    """
    
    def __init__(self):
        """Initialize the Supabase client."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        
        self.client = create_client(url, key)
    
    def save_agent_state(self, state: Dict[str, Any]) -> bool:
        """
        Save the agent's current state to Supabase.
        
        Args:
            state: Dictionary containing the agent's current state
            
        Returns:
            True if save was successful
        """
        try:
            timestamp = datetime.now().isoformat()
            
            # Add timestamp to state
            state_to_save = {
                **state,
                "timestamp": timestamp,
                "created_at": timestamp  # Required by Supabase
            }
            
            # Insert state into agent_state table
            response = self.client.table("agent_state").insert(state_to_save).execute()
            
            if len(response.data) > 0:
                return True
            return False
        except Exception as e:
            print(f"Error saving agent state: {str(e)}")
            return False
    
    def get_latest_agent_state(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest agent state from Supabase.
        
        Returns:
            Dictionary containing the latest agent state, or None if no state exists
        """
        try:
            response = self.client.table("agent_state") \
                .select("*") \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            
            if len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting latest agent state: {str(e)}")
            return None
    
    def log_action(self, action_type: str, details: Dict[str, Any], status: str = "success") -> bool:
        """
        Log an action taken by the agent.
        
        Args:
            action_type: Type of action (e.g., "update_task", "create_task", "send_notification")
            details: Dictionary with details about the action
            status: Status of the action (success, error)
            
        Returns:
            True if log was successful
        """
        try:
            timestamp = datetime.now().isoformat()
            
            action_log = {
                "action_type": action_type,
                "details": json.dumps(details),
                "status": status,
                "timestamp": timestamp,
                "created_at": timestamp  # Required by Supabase
            }
            
            response = self.client.table("agent_actions").insert(action_log).execute()
            
            if len(response.data) > 0:
                return True
            return False
        except Exception as e:
            print(f"Error logging action: {str(e)}")
            return False
    
    def save_learned_preference(self, preference_type: str, preference_data: Dict[str, Any]) -> bool:
        """
        Save a learned user preference.
        
        Args:
            preference_type: Type of preference (e.g., "time_block", "task_priority")
            preference_data: Dictionary with preference details
            
        Returns:
            True if save was successful
        """
        try:
            timestamp = datetime.now().isoformat()
            
            preference = {
                "preference_type": preference_type,
                "preference_data": json.dumps(preference_data),
                "created_at": timestamp,  # Required by Supabase
                "updated_at": timestamp
            }
            
            print(f"Debug: Saving preference payload: {preference}")
            # Check if preference already exists
            response = self.client.table("learned_preferences") \
                .select("id") \
                .eq("preference_type", preference_type) \
                .execute()
            
            if len(response.data) > 0:
                # Update existing preference
                preference_id = response.data[0]["id"]
                preference["updated_at"] = timestamp
                update_response = self.client.table("learned_preferences") \
                    .update(preference) \
                    .eq("id", preference_id) \
                    .execute()
                
                if len(update_response.data) > 0:
                    return True
                return False
            else:
                # Insert new preference
                insert_response = self.client.table("learned_preferences") \
                    .insert(preference) \
                    .execute()
                
                if len(insert_response.data) > 0:
                    return True
                return False
        except Exception as e:
            print(f"Error saving learned preference: {str(e)}")
            return False
    
    def get_learned_preferences(self, preference_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get learned user preferences.
        
        Args:
            preference_type: Optional filter by preference type
            
        Returns:
            List of preference dictionaries
        """
        try:
            query = self.client.table("learned_preferences").select("*")
            
            if preference_type:
                query = query.eq("preference_type", preference_type)
                
            response = query.execute()
            
            if len(response.data) > 0:
                # Parse JSON strings
                for pref in response.data:
                    if "preference_data" in pref:
                        pref["preference_data"] = json.loads(pref["preference_data"])
                
                return response.data
            return []
        except Exception as e:
            print(f"Error getting learned preferences: {str(e)}")
            return []
    
    def create_required_tables(self):
        """
        Create the required tables in Supabase if they don't exist.
        This method should be called during initial setup.
        """
        # Note: This is a placeholder as table creation typically happens
        # through Supabase's web interface or migrations
        # In a production system, you would use database migrations
        pass 