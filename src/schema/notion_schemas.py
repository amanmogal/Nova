from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status options for tasks in Notion database."""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    COMPLETE = "Complete"


class TaskPriority(str, Enum):
    """Priority options for tasks in Notion database."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class NotionTaskSchema(BaseModel):
    """Schema for tasks in Notion database."""
    id: str = Field(..., description="Notion page ID")
    title: str = Field(..., description="Task title")
    status: TaskStatus = Field(TaskStatus.NOT_STARTED, description="Current status of the task")
    priority: Optional[TaskPriority] = Field(None, description="Priority level of the task")
    due_date: Optional[str] = Field(None, description="Due date in ISO format")
    scheduled_time: Optional[str] = Field(None, description="Scheduled time in ISO format")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")
    tags: Optional[List[str]] = Field(None, description="Tags associated with the task")
    notes: Optional[str] = Field(None, description="Additional notes about the task")
    last_edited_time: Optional[str] = Field(None, description="Last edited timestamp in ISO format")
    url: str = Field(..., description="URL to the task in Notion")
    
    class Config:
        use_enum_values = True


class RoutineSchema(BaseModel):
    """Schema for routines in Notion database."""
    id: str = Field(..., description="Notion page ID")
    task: str = Field(..., description="Routine task name")
    duration: Optional[int] = Field(None, description="Duration in minutes")
    notes: Optional[str] = Field(None, description="Additional notes")
    category: Optional[str] = Field(None, description="Category (Meetings, Focus Work, etc.)")
    days: Optional[List[str]] = Field(None, description="Days this routine applies to")
    status: Optional[List[str]] = Field(None, description="Status (Not Started, In Progress, Completed)")
    energy_level: Optional[str] = Field(None, description="Energy level (High, Medium, Low)")
    time: Optional[str] = Field(None, description="Scheduled time")
    location: Optional[str] = Field(None, description="Location (Office, Home, etc.)")
    url: str = Field(..., description="URL to the routine in Notion")


class NotionDatabaseSchema:
    """Provides the schema definitions for Notion databases."""
    
    @staticmethod
    def tasks_database_schema() -> Dict[str, Any]:
        """
        Returns the schema for the tasks database in Notion.
        Use this when creating or verifying the Notion database structure.
        """
        return {
            "Name": {
                "title": {}
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": status.value, "color": color}
                        for status, color in zip(
                            TaskStatus, 
                            ["gray", "blue", "yellow", "green", "red"]
                        )
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": priority.value, "color": color}
                        for priority, color in zip(
                            TaskPriority,
                            ["blue", "yellow", "orange", "red"]
                        )
                    ]
                }
            },
            "Due Date": {
                "date": {}
            },
            "Scheduled Time": {
                "date": {
                    "time_zone": "user"
                }
            },
            "Estimated Duration (minutes)": {
                "number": {
                    "format": "number"
                }
            },
            "Tags": {
                "multi_select": {
                    "options": []  # Will be populated by users
                }
            },
            "Notes": {
                "rich_text": {}
            }
        }
    
    @staticmethod
    def routines_database_schema() -> Dict[str, Any]:
        """
        Returns the schema for the routines database in Notion.
        Updated to match the actual database structure.
        """
        return {
            "Task": {
                "title": {}
            },
            "Duration": {
                "number": {
                    "format": "number"
                }
            },
            "Notes": {
                "rich_text": {}
            },
            "Category": {
                "select": {
                    "options": [
                        {"name": "Meetings", "color": "blue"},
                        {"name": "Focus Work", "color": "green"},
                        {"name": "Admin", "color": "gray"},
                        {"name": "Breaks", "color": "orange"},
                        {"name": "Email", "color": "red"},
                        {"name": "Planning", "color": "purple"},
                        {"name": "Learning", "color": "yellow"},
                        {"name": "1:1s", "color": "pink"},
                    ]
                }
            },
            "Days": {
                "multi_select": {
                    "options": [
                        {"name": "Monday", "color": "blue"},
                        {"name": "Tuesday", "color": "green"},
                        {"name": "Wednesday", "color": "yellow"},
                        {"name": "Thursday", "color": "orange"},
                        {"name": "Friday", "color": "red"},
                        {"name": "Saturday", "color": "purple"},
                        {"name": "Sunday", "color": "pink"},
                        {"name": "Weekdays", "color": "gray"},
                        {"name": "Weekends", "color": "brown"},
                    ]
                }
            },
            "Status": {
                "multi_select": {
                    "options": [
                        {"name": "Not Started", "color": "red"},
                        {"name": "In Progress", "color": "yellow"},
                        {"name": "Completed", "color": "green"},
                    ]
                }
            },
            "Energy Level": {
                "select": {
                    "options": [
                        {"name": "High", "color": "red"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "blue"},
                    ]
                }
            },
            "Time": {
                "date": {}
            },
            "Location": {
                "select": {
                    "options": [
                        {"name": "Office", "color": "blue"},
                        {"name": "Home", "color": "green"},
                        {"name": "Meeting Room", "color": "purple"},
                        {"name": "Client Site", "color": "orange"},
                        {"name": "Coworking Space", "color": "yellow"},
                        {"name": "Commuting", "color": "gray"},
                        {"name": "Coffee Shop", "color": "brown"},
                        {"name": "Outdoors", "color": "default"},
                    ]
                }
            }
        } 