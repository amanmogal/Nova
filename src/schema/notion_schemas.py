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


class TimeBlockPreference(BaseModel):
    """Schema for time block preferences in the routines database."""
    name: str = Field(..., description="Name of the time block")
    start_time: str = Field(..., description="Start time in 24-hour format (HH:MM)")
    end_time: str = Field(..., description="End time in 24-hour format (HH:MM)")
    days: List[str] = Field(..., description="Days of week this applies to")
    priority: int = Field(1, description="Priority level (1-5, with 5 being highest)")
    task_types: Optional[List[str]] = Field(None, description="Types of tasks suitable for this block")


class RoutineSchema(BaseModel):
    """Schema for routines in Notion database."""
    id: str = Field(..., description="Notion page ID")
    name: str = Field(..., description="Routine name")
    time_blocks: List[TimeBlockPreference] = Field(..., description="Preferred time blocks")
    recurring: bool = Field(False, description="Whether this is a recurring routine")
    recurrence_pattern: Optional[str] = Field(None, description="Pattern for recurrence (e.g., 'Daily', 'Weekdays')")
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
        Returns the schema for the routines & preferences database in Notion.
        """
        return {
            "Name": {
                "title": {}
            },
            "Time Blocks": {
                "rich_text": {}  # Stored as JSON string
            },
            "Recurring": {
                "checkbox": {}
            },
            "Recurrence Pattern": {
                "select": {
                    "options": [
                        {"name": "Daily", "color": "blue"},
                        {"name": "Weekdays", "color": "green"},
                        {"name": "Weekends", "color": "yellow"},
                        {"name": "Weekly", "color": "orange"},
                        {"name": "Monthly", "color": "red"},
                    ]
                }
            },
            "Description": {
                "rich_text": {}
            }
        } 