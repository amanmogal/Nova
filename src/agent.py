"""
Main agent implementation for the autonomous Notion task management agent.

"""
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Literal, TypedDict, Union
from enum import Enum

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai
from dotenv import load_dotenv
from langsmith import Client as LangSmithClient
# LangGraph imports removed - using simple loop implementation instead
# from langgraph.graph import StateGraph, END
from src.tools.notion_connector import NotionConnector
from src.config import get_settings
from src.tools.rag_engine import RAGEngine
from src.tools.notification_tool import NotificationTool
from src.db.supabase_connector import SupabaseConnector
from src.prompts.system_prompt import SYSTEM_PROMPT, DAILY_PLANNING_PROMPT, TASK_REPRIORITIZATION_PROMPT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agent.log")
    ]
)
logger = logging.getLogger("notion_agent")

# Load environment variables
load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# LangSmith tracing (observation/monitoring)
# If the user sets LANGCHAIN_TRACING_V2=true and provides LANGCHAIN_API_KEY
# the agent will automatically send traces to LangSmith for every execution.
# This block validates the credentials once at start-up and logs status.

if os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true":
    try:
        _ls_client = LangSmithClient()
        logger.info(
            "LangSmith tracing ENABLED – project: %s", get_settings().LANGCHAIN_PROJECT
        )
    except Exception as exc:
        logger.warning("LangSmith tracing could not be initialised: %s", exc)


# Configure Google API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# State and type definitions
class AgentState(TypedDict):
    """Type definition for the agent's state."""
    goal: str
    context: Dict[str, Any]
    messages: List[Dict[str, Any]]
    next_action: Optional[str]
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    error: Optional[str]


# Initialize tools
notion = NotionConnector()
rag_engine = RAGEngine()
notification_tool = NotificationTool()
db = SupabaseConnector()


# Tool definitions for LangGraph
def search_tasks_tool(state: AgentState) -> AgentState:
    """
    Search for tasks in Notion.
    """
    try:
        # Get query from state
        query = state.get("current_query", "")
        limit = state.get("search_limit", 5)
        
        tasks = rag_engine.search_tasks(query, n_results=limit)
        
        # Log the action
        db.log_action(
            action_type="search_tasks",
            details={"query": query, "limit": limit, "results_count": len(tasks)}
        )
        
        # Update state with results
        state["search_results"] = {"success": True, "tasks": tasks}
        return state
    except Exception as e:
        error = f"Error searching tasks: {str(e)}"
        logger.error(error)
        
        # Log the error
        db.log_action(
            action_type="search_tasks",
            details={"query": query, "limit": limit, "error": str(e)},
            status="error"
        )
        
        state["search_results"] = {"success": False, "error": error}
        return state


async def update_task_tool(state: AgentState) -> AgentState:
    """
    Update a task in Notion.
    """
    try:
        # Get task data from state
        task_id = state.get("current_task_id", "")
        properties = state.get("current_task_properties", {})
        logger.info(f"Attempting to update task with ID: {task_id} and properties: {properties}")
        
        result = await notion.update_task(task_id, properties)
        
        # Log the action
        db.log_action(
            action_type="update_task",
            details={"task_id": task_id, "properties": properties}
        )
        
        # Update state with results
        state["update_result"] = {"success": result, "task_id": task_id}
        return state
    except Exception as e:
        error = f"Error updating task {task_id}: {str(e)}"
        logger.error(error)
        
        # Log the error
        db.log_action(
            action_type="update_task",
            details={"task_id": task_id, "properties": properties, "error": str(e)},
            status="error"
        )
        
        state["update_result"] = {"success": False, "error": error, "task_id": task_id}
        return state


async def create_task_tool(state: AgentState) -> AgentState:
    """
    Create a new task in Notion.
    """
    try:
        # Get task data from state
        task_data = state.get("new_task_data", {})
        
        task_id = await notion.create_task(task_data)
        
        if task_id:
            # Log the action
            db.log_action(
                action_type="create_task",
                details={"task_data": task_data, "task_id": task_id}
            )
            
            # Update state with results
            state["create_result"] = {"success": True, "task_id": task_id}
        else:
            state["create_result"] = {"success": False, "error": "Failed to create task"}
        
        return state
    except Exception as e:
        error = f"Error creating task: {str(e)}"
        logger.error(error)
        
        # Log the error
        db.log_action(
            action_type="create_task",
            details={"task_data": task_data, "error": str(e)},
            status="error"
        )
        
        state["create_result"] = {"success": False, "error": error}
        return state


def send_notification_tool(state: AgentState) -> AgentState:
    """
    Send a notification to the user.
    """
    try:
        # Get notification data from state
        recipient = state.get("notification_recipient", "")
        subject = state.get("notification_subject", "")
        message = state.get("notification_message", "")
        priority = state.get("notification_priority", "normal")
        
        result = notification_tool.send_notification(
            recipient=recipient,
            subject=subject,
            message=message,
            priority=priority
        )
        
        # Log the action
        db.log_action(
            action_type="send_notification",
            details={
                "recipient": recipient, 
                "subject": subject,
                "priority": priority
            }
        )
        
        # Update state with results
        state["notification_result"] = {"success": result}
        return state
    except Exception as e:
        error = f"Error sending notification: {str(e)}"
        logger.error(error)
        
        # Log the error
        db.log_action(
            action_type="send_notification",
            details={
                "recipient": recipient,
                "subject": subject,
                "priority": priority,
                "error": str(e)
            },
            status="error"
        )
        
        state["notification_result"] = {"success": False, "error": error}
        return state


async def get_routines_tool(state: AgentState) -> AgentState:
    """
    Get the user's routines from Notion.
    """
    try:
        # Get routines from Notion
        routines_data = await notion.get_routines()
        
        # Log the action
        db.log_action(
            action_type="get_routines",
            details={"count": len(routines_data)}
        )
        
        # Update state with results
        state["routines_result"] = {"success": True, "routines": routines_data}
        return state
    except Exception as e:
        error = f"Error getting routines: {str(e)}"
        logger.error(error)
        
        # Log the error
        db.log_action(
            action_type="get_routines",
            details={"error": str(e)},
            status="error"
        )
        
        state["routines_result"] = {"success": False, "error": error}
        return state


# Available tools mapping for LangGraph
TOOLS = {
    "search_tasks": search_tasks_tool,
    "update_task": update_task_tool,
    "create_task": create_task_tool,
    "send_notification": send_notification_tool,
    "get_routines": get_routines_tool
}


# LangGraph nodes
def perception(state: AgentState) -> AgentState:
    """
    Perception node: Gather context from the environment.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with context
    """
    logger.info("Perception: Gathering context")
    
    # Build context with RAG
    context = rag_engine.build_context(state["goal"])
    
    # Update state with context
    state["context"] = context
    
    return state


def reasoning(state: AgentState) -> AgentState:
    """
    Reasoning node: Generate the next action based on context.
    """
    logger.info("Reasoning: Determining next action")
    
    # Prepare the prompt
    messages = []
    
    # Combine system prompt with goal-specific prompt
    system_prompt = SYSTEM_PROMPT
    
    if state["goal"] == "daily_planning":
        system_prompt += "\n\n" + DAILY_PLANNING_PROMPT
    elif state["goal"] == "task_reprioritization":
        system_prompt += "\n\n" + TASK_REPRIORITIZATION_PROMPT
    
    # Add context (simplified to avoid content filtering)
    context_str = f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    # Add task count
    task_count = len(state['context'].get('tasks', []))
    context_str += f"Available tasks: {task_count}\n"
    
    # Add routine count
    routine_count = len(state['context'].get('routines', []))
    context_str += f"Available routines: {routine_count}\n"
    
    # Add calendar preferences
    context_str += f"Work hours: {state['context'].get('calendar_view_start', '10:00')} to {state['context'].get('calendar_view_end', '02:00')}\n"
    
    # Create the user message with system prompt and context
    user_message = f"{system_prompt}\n\n{context_str}"
    
    # Add previous tool results to context (simplified to avoid content filtering)
    if state.get("tool_results"):
        user_message += "\n\nPrevious actions completed successfully."
    
    messages.append({
        "role": "user",
        "parts": [user_message]
    })
    
    # Add previous messages if available (but keep them simple)
    for msg in state.get("messages", []):
        if msg.get("role") == "assistant":
            messages.append({
                "role": "model",
                "parts": [msg.get("parts", [""])[0]]
            })
    
    # Generate response from LLM
    settings = get_settings()
    model = genai.GenerativeModel(settings.gemini_model)
    
    try:
        response = model.generate_content(messages)
        
        # Check if response has candidates before accessing .text
        if not response.candidates:
            logger.error(f"LLM response has no candidates. Prompt feedback: {response.prompt_feedback}")
            state["error"] = "LLM response has no candidates."
            return state

        # Update messages
        if not state.get("messages"):
            state["messages"] = []
        
        # Handle response text properly - get text from the first candidate's content
        candidate = response.candidates[0]
        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts') and candidate.content.parts:
            response_text = candidate.content.parts[0].text
        else:
            response_text = str(candidate)
        
        state["messages"].append({
            "role": "assistant",
            "parts": [response_text]
        })
        
        # Determine next action based on response
        response_text_lower = response_text.lower()
        
        # Simple action determination logic
        if "search" in response_text_lower or "find" in response_text_lower:
            state["next_action"] = "search_tasks"
            # Extract search query from response
            state["current_query"] = "pending tasks"  # Default query
        elif "update" in response_text_lower or "schedule" in response_text_lower:
        
            if state.get("context", {}).get("tasks"):
                state["next_action"] = "update_task"
                # For now, set a default task_id 
                # In a real implementation, the agent should identify which specific task to update
                if state["context"]["tasks"]:
                    # Use the parent_id from metadata, which is the actual Notion page ID
                    task_metadata = state["context"]["tasks"][0]["metadata"]
                    state["current_task_id"] = task_metadata.get("parent_id", "")
                else:
                    state["current_task_id"] = ""
                state["current_task_properties"] = {"Status": {"select": {"name": "In Progress"}}}
            else:
                state["next_action"] = "end"
        elif "create" in response_text_lower or "add" in response_text_lower:
            state["next_action"] = "create_task"
        elif "notify" in response_text_lower or "send" in response_text_lower:
            state["next_action"] = "send_notification"
        elif "routine" in response_text_lower:
            state["next_action"] = "get_routines"
        else:
            state["next_action"] = "end"
        
        return state
    except Exception as e:
        error = f"Error in reasoning: {str(e)}"
        logger.error(error)
        state["error"] = error
        return state


async def execute_action(state: AgentState) -> AgentState:
    """
    Execute the next action in the state.
    """
    next_action = state.get("next_action")
    
    if not next_action or next_action == "end":
        logger.info("Action: No action to execute, ending")
        return state
    
    logger.info(f"Action: Executing {next_action}")
    
    # Execute the action
    if next_action in TOOLS:
        try:
            logger.info(f"Executing tool: {next_action}")
            tool_fn = TOOLS[next_action]
            
            # Check if tool is async
            import asyncio
            import inspect
            if inspect.iscoroutinefunction(tool_fn):
                updated_state = await tool_fn(state)
            else:
                updated_state = tool_fn(state)
            
            # Update state with tool results
            state.update(updated_state)
            
        except Exception as e:
            error = f"Error executing tool {next_action}: {str(e)}"
            logger.error(error)
            
            if "tool_results" not in state:
                state["tool_results"] = []
            
            state["tool_results"].append({
                "tool_name": next_action,
                "result": {"success": False, "error": error}
            })
    else:
        error = f"Unknown action: {next_action}"
        logger.error(error)
        
        if "tool_results" not in state:
            state["tool_results"] = []
        
        state["tool_results"].append({
            "tool_name": next_action,
            "result": {"success": False, "error": error}
        })
    
    return state


def save_state(state: AgentState) -> AgentState:
    """
    Save the agent's state to the database.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state
    """
    logger.info("Saving agent state to database")
    
    try:
        # Save state to Supabase
        db.save_agent_state({
            "goal": state["goal"],
            "context": {
                "tasks_count": len(state["context"].get("tasks", [])),
                "routines_count": len(state["context"].get("routines", [])),
                "timestamp": state["context"].get("timestamp")
            }
        })
        
        logger.info("State saved successfully")
    except Exception as e:
        error = f"Error saving state: {str(e)}"
        logger.error(error)
        state["error"] = error
    
    return state


# build_graph function removed - using simple loop implementation instead


async def run_agent(goal: str = "daily_planning") -> Dict[str, Any]:
    """
    Run the agent with the specified goal.
    
    Args:
        goal: The goal for the agent to achieve
        
    Returns:
        Final agent state
    """
    logger.info(f"Running agent with goal: {goal}")
    
    # Initialize state
    initial_state = AgentState(
        goal=goal,
        context={},
        messages=[],
        next_action=None,
        tool_calls=[],
        tool_results=[],
        error=None
    )
    
    # Run the agent using a simple loop instead of LangGraph
    # This avoids the LangGraph API compatibility issues
    state = initial_state.copy()
    
    try:
        # Step 1: Perception - Gather context
        logger.info("Step 1: Perception - Gathering context")
        state = perception(state)
        
        # Step 2: Reasoning - Determine next action
        logger.info("Step 2: Reasoning - Determining next action")
        state = reasoning(state)
        
        # Step 3: Action - Execute actions in a loop
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        
        while state.get("next_action") and state.get("next_action") != "end" and iteration < max_iterations:
            logger.info(f"Step 3.{iteration + 1}: Action - Executing {state.get('next_action')}")
            
            # Execute the action
            state = await execute_action(state)
            
            # Clear next_action to prevent infinite loop
            state["next_action"] = None
            
            # Continue with reasoning for next action
            state = reasoning(state)
            iteration += 1
        
        # Step 4: Save state
        logger.info("Step 4: Saving state")
        state = save_state(state)
        
        logger.info("Agent run completed successfully")
        
    except Exception as e:
        error = f"Error in agent execution: {str(e)}"
        logger.error(error)
        state["error"] = error
    
    return state


async def main():
    """Main function."""
    # Sync Notion data to vector database
    logger.info("Syncing Notion data to vector database")
    rag_engine.sync_notion_data()
    
    # Run the agent
    goal = os.getenv("AGENT_GOAL", "daily_planning")
    await run_agent(goal)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 