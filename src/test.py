"""
Test script for the autonomous Notion task management agent.
This script tests the basic functionality of the agent components.
"""
import os
import sys
from datetime import datetime
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.tools.notion_connector import NotionConnector
from src.tools.rag_engine import RAGEngine
from src.tools.notification_tool import NotificationTool
from src.db.supabase_connector import SupabaseConnector

# Load environment variables
load_dotenv()


def test_notion_connector(non_interactive: bool):
    """Test the Notion connector."""
    print("\n===== Testing Notion Connector =====")
    try:
        # Initialize connector
        notion = NotionConnector()
        
        # Test get_tasks
        print("Testing get_tasks...")
        tasks = notion.get_tasks()
        print(f"Retrieved {len(tasks)} tasks")
        
        if tasks:
            # Display first task
            print(f"First task: {tasks[0].title} (Status: {tasks[0].status})")
            
            # Test update_task
            if not non_interactive:
                if input("Do you want to test updating a task? (y/n): ").lower() == "y":
                    task_id = tasks[0].id
                    print(f"Updating task {task_id} ({tasks[0].title})...")
                
                # Define properties to update
                properties = {
                    "Status": {
                        "select": {
                            "name": "In Progress"
                        }
                    }
                }
                
                # Update the task
                result = notion.update_task(task_id, properties)
                print(f"Update result: {result}")
        else:
            # Test create_task
            if not non_interactive:
                if input("No tasks found. Do you want to create a test task? (y/n): ").lower() == "y":
                    print("Creating a test task...")
                    task_data = {
                        "title": f"Test Task {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        "status": "To Do",
                        "priority": "Medium",
                        "notes": "This is a test task created by the test script"
                    }
                    task_id = notion.create_task(task_data)
                    print(f"Created task with ID: {task_id}")
        
        # Test get_routines
        print("\nTesting get_routines...")
        routines = notion.get_routines()
        print(f"Retrieved {len(routines)} routines")
        
        if routines:
            # Display first routine
            print(f"First routine: {routines[0].name}")
            print(f"Time blocks: {len(routines[0].time_blocks)}")
            
        print("Notion connector tests completed successfully")
        return True
    except Exception as e:
        print(f"Error testing Notion connector: {str(e)}")
        return False


def test_rag_engine():
    """Test the RAG engine."""
    print("\n===== Testing RAG Engine =====")
    try:
        # Initialize RAG engine
        rag = RAGEngine()
        
        # Test sync_notion_data
        print("Testing sync_notion_data...")
        rag.sync_notion_data()
        
        # Test search_tasks
        print("\nTesting search_tasks...")
        query = "high priority"
        tasks = rag.search_tasks(query)
        
        print(f"Found {len(tasks)} tasks for query: '{query}'")
        for i, task in enumerate(tasks[:3], 1):  # Show up to 3 results
            print(f"{i}. {task['metadata']['title']}")
            
        # Test search_routines
        print("\nTesting search_routines...")
        query = "morning routine"
        routines = rag.search_routines(query)
        
        print(f"Found {len(routines)} routines for query: '{query}'")
        for i, routine in enumerate(routines[:3], 1):  # Show up to 3 results
            print(f"{i}. {routine['metadata']['name']}")
            
        # Test build_context
        print("\nTesting build_context...")
        context = rag.build_context("daily planning")
        
        print(f"Context built with {len(context.get('tasks', []))} tasks and {len(context.get('routines', []))} routines")
        print(f"Calendar view start: {context.get('calendar_view_start')}")
        print(f"Calendar view end: {context.get('calendar_view_end')}")
        
        print("RAG engine tests completed successfully")
        return True
    except Exception as e:
        print(f"Error testing RAG engine: {str(e)}")
        return False


def test_notification_tool():
    """Test the notification tool."""
    print("\n===== Testing Notification Tool =====")
    try:
        # Initialize notification tool
        notification = NotificationTool()
        
        # Test send_notification
        print("Testing send_notification...")
        # Using a dummy email for non-interactive testing
        recipient = "test@example.com"
        
        result = notification.send_notification(
            recipient=recipient,
            subject="Test Notification from Notion Agent",
            message="This is a test notification from your autonomous Notion agent.",
            priority="normal"
        )
        
        print(f"Notification sent: {result}")
        
        # Test notify_task_scheduled
        print("\nTesting notify_task_scheduled...")
        
        task = {
            "title": "Test Task",
            "scheduled_time": datetime.now().isoformat(),
            "estimated_duration": 30,
            "priority": "High",
            "url": "https://notion.so/test-task"
        }
        
        result = notification.notify_task_scheduled(task, recipient)
        print(f"Task scheduled notification sent: {result}")
            
        print("Notification tool tests completed successfully")
        return True
    except Exception as e:
        print(f"Error testing notification tool: {str(e)}")
        return False


def test_supabase_connector():
    """Test the Supabase connector."""
    print("\n===== Testing Supabase Connector =====")
    try:
        # Initialize Supabase connector
        db = SupabaseConnector()
        
        # Test save_agent_state
        print("Testing save_agent_state...")
        state = {
            "goal": "test",
            "timestamp": datetime.now().isoformat(),
            "context": {"test": True}
        }
        
        result = db.save_agent_state(state)
        print(f"State saved: {result}")
        
        # Test get_latest_agent_state
        print("\nTesting get_latest_agent_state...")
        latest_state = db.get_latest_agent_state()
        
        if latest_state:
            print(f"Retrieved latest state from: {latest_state.get('timestamp')}")
        else:
            print("No state found")
            
        # Test log_action
        print("\nTesting log_action...")
        action_result = db.log_action(
            action_type="test",
            details={"test": True, "timestamp": datetime.now().isoformat()},
            status="success"
        )
        
        print(f"Action logged: {action_result}")
        
        # Test save_learned_preference
        print("\nTesting save_learned_preference...")
        preference_result = db.save_learned_preference(
            preference_type="test_preference",
            preference_data={
                "test": True,
                "value": "test value",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        print(f"Preference saved: {preference_result}")
        
        # Test get_learned_preferences
        print("\nTesting get_learned_preferences...")
        preferences = db.get_learned_preferences()
        
        print(f"Retrieved {len(preferences)} preferences")
        
        print("Supabase connector tests completed successfully")
        return True
    except Exception as e:
        print(f"Error testing Supabase connector: {str(e)}")
        return False


def main():
    """Main test function."""
    print("===== Notion Task Management Agent Tests =====\n")

    # Mapping of test names to functions
    non_interactive = os.getenv("NON_INTERACTIVE", "false").lower() == "true"

    tests = {
        "Notion Connector": lambda: test_notion_connector(non_interactive),
        "RAG Engine": test_rag_engine,
        "Notification Tool": test_notification_tool,
        "Supabase Connector": test_supabase_connector,
    }

    results: dict[str, bool | str] = {}

    # Execute selected tests
    for test_name, test_function in tests.items():
        results[test_name] = test_function()

    # Print summary table
    print("\n===== Test Summary =====")
    for test_name, result in results.items():
        status = "PASS" if result is True else "FAIL" if result is False else "SKIPPED"
        print(f"{test_name}: {status}")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main() 