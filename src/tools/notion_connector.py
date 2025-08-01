
# Notion API connector for the autonomous task management agent.
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from dotenv import load_dotenv
from notion_client import AsyncClient
from pydantic import BaseModel, Field

from src.schema.notion_schemas import NotionTaskSchema, TaskStatus, RoutineSchema

# Load environment variables
load_dotenv()


class NotionConnector:
    """
    Connector for the Notion API.
    Provides methods for interacting with Notion databases and pages.
    """
    
    def __init__(self):
        """Initialize the Notion API client."""
        self.api_key = os.getenv("NOTION_API_KEY")
        if not self.api_key:
            raise ValueError("NOTION_API_KEY environment variable not set")
        
        self.client = AsyncClient(auth=self.api_key)
        self.tasks_db_id = os.getenv("NOTION_TASKS_DATABASE_ID")
        self.routines_db_id = os.getenv("NOTION_ROUTINES_DATABASE_ID")
        
        if not self.tasks_db_id or not self.routines_db_id:
            raise ValueError("Notion database IDs not set in environment variables")
    
    def _property_value_to_python(self, property_type: str, property_value: Any) -> Any:
        """Convert Notion property values to Python objects."""
        if property_value is None:
            return None
        
        if property_type == "title":
            return property_value[0]["plain_text"] if property_value else ""
        elif property_type == "rich_text":
            return property_value[0]["plain_text"] if property_value else ""
        elif property_type == "select":
            return property_value["name"] if property_value else None
        elif property_type == "status":
            return property_value["name"] if property_value else None
        elif property_type == "multi_select":
            return [item["name"] for item in property_value] if property_value else []
        elif property_type == "date":
            if not property_value or not property_value.get("start"):
                return None
            return property_value["start"]
        elif property_type == "number":
            return property_value
        elif property_type == "checkbox":
            return property_value
        else:
            return property_value
    
    async def get_tasks(self, filter_criteria: Optional[Dict[str, Any]] = None) -> List[NotionTaskSchema]:
        """
        Fetch tasks from the Notion database with optional filtering.
        
        Args:
            filter_criteria: Optional dictionary with Notion filter criteria
            
        Returns:
            List of NotionTaskSchema objects representing tasks
        """
        query_params = {"database_id": self.tasks_db_id}
        if filter_criteria:
            query_params["filter"] = filter_criteria
            
        response = await self.client.databases.query(**query_params)
        tasks = []
        
        for result in response.get("results", []):
            props = result.get("properties", {})
            
            # Extract properties with proper conversions
            task_data = {
                "id": result["id"],
                "url": result["url"],
                "last_edited_time": result.get("last_edited_time"),
                "title": self._property_value_to_python("title", props.get("Task", {}).get("title")) or "Untitled Task",
                "status": self._property_value_to_python("status", props.get("Status", {}).get("status")) or "Not Started",
                "priority": self._property_value_to_python("select", props.get("Priority", {}).get("select")),
                "due_date": self._property_value_to_python("date", props.get("Due Date", {}).get("date")),
                "scheduled_time": None,  # Not in your schema
                "estimated_duration": None,  # Not in your schema
                "tags": [],  # Not in your schema
                "notes": self._property_value_to_python("rich_text", props.get("Notes", {}).get("rich_text"))
            }
            print(f"Debug: Raw Notion properties for task {result['id']}: {props}")
            print(f"Debug: Processed task_data for task {result['id']}: {task_data}")
            
            tasks.append(NotionTaskSchema(**task_data))
            
        return tasks
    
    async def update_task(self, task_id: str, properties: Dict[str, Any]) -> bool:
        """
        Update a task's properties in Notion.
        
        Args:
            task_id: The Notion page ID of the task
            properties: Dictionary of properties to update
            
        Returns:
            True if update was successful
        """
        try:
            # Convert select format to status format for Status field
            if "Status" in properties and "select" in properties["Status"]:
                properties["Status"] = {
                    "status": {
                        "name": properties["Status"]["select"]["name"]
                    }
                }
            
            await self.client.pages.update(page_id=task_id, properties=properties)
            return True
        except Exception as e:
            print(f"Error updating task {task_id}: {str(e)}")
            return False
    
    async def create_task(self, task_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new task in the Notion database.
        
        Args:
            task_data: Dictionary with task properties
            
        Returns:
            ID of the created task, or None if creation failed
        """
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": task_data.get("title", "New Task")
                        }
                    }
                ]
            }
        }
        
        # Add other properties if provided
        if task_data.get("status"):
            properties["Status"] = {"select": {"name": task_data["status"]}}
        
        if task_data.get("priority"):
            properties["Priority"] = {"select": {"name": task_data["priority"]}}
        
        if task_data.get("due_date"):
            properties["Due Date"] = {"date": {"start": task_data["due_date"]}}
        
        if task_data.get("scheduled_time"):
            properties["Scheduled Time"] = {"date": {"start": task_data["scheduled_time"]}}
        
        if task_data.get("estimated_duration") is not None:
            properties["Estimated Duration (minutes)"] = {"number": task_data["estimated_duration"]}
        
        if task_data.get("tags"):
            properties["Tags"] = {"multi_select": [{"name": tag} for tag in task_data["tags"]]}
        
        if task_data.get("notes"):
            properties["Notes"] = {"rich_text": [{"text": {"content": task_data["notes"]}}]}
        
        try:
            response = await self.client.pages.create(
                parent={"database_id": self.tasks_db_id},
                properties=properties
            )
            return response["id"]
        except Exception as e:
            print(f"Error creating task: {str(e)}")
            return None

    async def get_routines(self) -> List[RoutineSchema]:
        """
        Fetch routines from the Notion database.
        
        Returns:
            List of RoutineSchema objects representing routines
        """
        response = await self.client.databases.query(database_id=self.routines_db_id)
        routines = []
        
        for result in response.get("results", []):
            props = result.get("properties", {})
            
            # Extract task name (was "Name", now "Task")
            task = self._property_value_to_python("title", props.get("Task", {}).get("title"))
            
            # Extract other properties
            duration = self._property_value_to_python("number", props.get("Duration", {}).get("number"))
            notes = self._property_value_to_python("rich_text", props.get("Notes", {}).get("rich_text"))
            category = self._property_value_to_python("select", props.get("Category", {}).get("select"))
            days = self._property_value_to_python("multi_select", props.get("Days", {}).get("multi_select"))
            status = self._property_value_to_python("multi_select", props.get("Status", {}).get("multi_select"))
            energy_level = self._property_value_to_python("select", props.get("Energy Level", {}).get("select"))
            time = self._property_value_to_python("date", props.get("Time", {}).get("date"))
            location = self._property_value_to_python("select", props.get("Location", {}).get("select"))
            
            # Skip routines with missing required fields
            if not task:
                print(f"Warning: Skipping routine {result['id']} - missing task name")
                continue
                
            routine_data = {
                "id": result["id"],
                "url": result["url"],
                "task": task,
                "duration": duration,
                "notes": notes,
                "category": category,
                "days": days,
                "status": status,
                "energy_level": energy_level,
                "time": time,
                "location": location
            }
            
            try:
                routines.append(RoutineSchema(**routine_data))
            except Exception as e:
                print(f"Warning: Skipping routine {result['id']} - validation error: {e}")
                continue
            
        return routines 