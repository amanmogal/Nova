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
from langgraph.graph import StateGraph, END
from src.tools.notion_connector import NotionConnector
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
            "LangSmith tracing ENABLED – project: %s", _ls_client.project_name
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


def update_task_tool(state: AgentState) -> AgentState:
    """
    Update a task in Notion.
    """
    try:
        # Get task data from state
        task_id = state.get("current_task_id", "")
        properties = state.get("current_task_properties", {})
        
        result = notion.update_task(task_id, properties)
        
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


def create_task_tool(state: AgentState) -> AgentState:
    """
    Create a new task in Notion.
    """
    try:
        # Get task data from state
        task_data = state.get("new_task_data", {})
        
        task_id = notion.create_task(task_data)
        
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


def get_routines_tool(state: AgentState) -> AgentState:
    """
    Get the user's routines from Notion.
    """
    try:
        routines = notion.get_routines()
        
        # Convert to dictionary format
        routines_data = []
        for routine in routines:
            routines_data.append({
                "id": routine.id,
                "name": routine.name,
                "time_blocks": [block.dict() for block in routine.time_blocks],
                "recurring": routine.recurring,
                "recurrence_pattern": routine.recurrence_pattern,
                "url": routine.url
            })
        
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
    
    # System prompt
    messages.append({
        "role": "system",
        "parts": [SYSTEM_PROMPT]
    })
    
    # Add goal-specific prompt
    if state["goal"] == "daily_planning":
        messages.append({
            "role": "user",
            "parts": [DAILY_PLANNING_PROMPT]
        })
    elif state["goal"] == "task_reprioritization":
        messages.append({
            "role": "user",
            "parts": [TASK_REPRIORITIZATION_PROMPT]
        })
    
    # Add context
    context_str = f"Current time: {datetime.now().isoformat()}\n\n"
    
    # Add tasks
    context_str += f"Available Tasks ({len(state['context'].get('tasks', []))}):\n"
    for i, task in enumerate(state["context"].get("tasks", []), 1):
        context_str += f"{i}. {task['content']}\n"
        
    # Add routines
    context_str += f"\nRoutines ({len(state['context'].get('routines', []))}):\n"
    for i, routine in enumerate(state["context"].get("routines", []), 1):
        context_str += f"{i}. {routine['content']}\n"
    
    # Add calendar preferences
    context_str += "\nCalendar Preferences:\n"
    context_str += f"- Calendar View Start: {state['context'].get('calendar_view_start', '10:00')}\n"
    context_str += f"- Calendar View End: {state['context'].get('calendar_view_end', '02:00')}\n"
    
    messages.append({
        "role": "user",
        "parts": [context_str]
    })
    
    # Add previous messages if available
    messages.extend(state.get("messages", []))
    
    # Add previous tool results
    for result in state.get("tool_results", []):
        messages.append({
            "role": "tool",
            "parts": [json.dumps(result["result"])]
        })
    
    # Generate response from LLM
    model = genai.GenerativeModel(
        os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    )
    
    try:
        response = model.generate_content(messages)
        
        # Update messages
        if not state.get("messages"):
            state["messages"] = []
        
        state["messages"].append({
            "role": "assistant",
            "parts": [response.text]
        })
        
        # Determine next action based on response
        response_text = response.text.lower()
        
        # Simple action determination logic
        if "search" in response_text or "find" in response_text:
            state["next_action"] = "search_tasks"
            # Extract search query from response
            state["current_query"] = "pending tasks"  # Default query
        elif "update" in response_text or "schedule" in response_text:
            state["next_action"] = "update_task"
        elif "create" in response_text or "add" in response_text:
            state["next_action"] = "create_task"
        elif "notify" in response_text or "send" in response_text:
            state["next_action"] = "send_notification"
        elif "routine" in response_text:
            state["next_action"] = "get_routines"
        else:
            state["next_action"] = "end"
        
        return state
    except Exception as e:
        error = f"Error in reasoning: {str(e)}"
        logger.error(error)
        state["error"] = error
        return state


def action(state: AgentState) -> Union[AgentState, Literal["reasoning", "end"]]:
    """
    Action node: Execute the next action.
    """
    next_action = state.get("next_action")
    
    if not next_action or next_action == "end":
        logger.info("Action: No action to execute, ending")
        return "end"
    
    logger.info(f"Action: Executing {next_action}")
    
    # Initialize tool_results if not present
    if "tool_results" not in state:
        state["tool_results"] = []
    
    # Execute the action
    if next_action in TOOLS:
        try:
            logger.info(f"Executing tool: {next_action}")
            tool_fn = TOOLS[next_action]
            updated_state = tool_fn(state)
            
            # Add result to tool_results
            result_key = f"{next_action}_result"
            if result_key in updated_state:
                state["tool_results"].append({
                    "tool_name": next_action,
                    "result": updated_state[result_key]
                })
            
            # Update state with tool results
            state.update(updated_state)
            
        except Exception as e:
            error = f"Error executing tool {next_action}: {str(e)}"
            logger.error(error)
            
            state["tool_results"].append({
                "tool_name": next_action,
                "result": {"success": False, "error": error}
            })
    else:
        error = f"Unknown action: {next_action}"
        logger.error(error)
        
        state["tool_results"].append({
            "tool_name": next_action,
            "result": {"success": False, "error": error}
        })
    
    # Clear next_action
    state["next_action"] = None
    
    # Check if we need to do more reasoning
    if any(not result["result"].get("success", True) for result in state["tool_results"]):
        # If there were errors, go back to reasoning
        return "reasoning"
    
    # Continue with another round of reasoning
    return "reasoning"


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
            "context_summary": {
                "tasks_count": len(state["context"].get("tasks", [])),
                "routines_count": len(state["context"].get("routines", [])),
                "timestamp": state["context"].get("timestamp")
            },
            "messages_count": len(state.get("messages", [])),
            "tool_results_count": len(state.get("tool_results", []))
        })
        
        logger.info("State saved successfully")
    except Exception as e:
        error = f"Error saving state: {str(e)}"
        logger.error(error)
        state["error"] = error
    
    return state


def build_graph() -> StateGraph:
    """
    Build the LangGraph state graph.
    Following Factor 8: Own Your Control Flow.
    
    Returns:
        StateGraph instance
    """
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("perception", perception)
    graph.add_node("reasoning", reasoning)
    graph.add_node("action", action)
    graph.add_node("save_state", save_state)
    
    # Add conditional edges
    graph.add_conditional_edges(
        "perception",
        lambda x: "reasoning"
    )
    
    graph.add_conditional_edges(
        "reasoning",
        lambda x: "action" if x.get("next_action") else "save_state"
    )
    
    graph.add_conditional_edges(
        "action",
        lambda x: "reasoning" if x.get("next_action") else "save_state"
    )
    
    graph.add_conditional_edges(
        "save_state",
        lambda x: END
    )
    
    # Set entry point
    graph.set_entry_point("perception")
    
    return graph


def run_agent(goal: str = "daily_planning") -> Dict[str, Any]:
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
    
    # Build graph
    graph = build_graph()
    
    # Run the graph using the correct method
    try:
        # Try the newer API first
        result = graph.invoke(initial_state)
    except AttributeError:
        # Fall back to older API
        result = graph.run(initial_state)
    
    logger.info("Agent run completed")
    
    return result


def main():
    """Main function."""
    # Sync Notion data to vector database
    logger.info("Syncing Notion data to vector database")
    rag_engine.sync_notion_data()
    
    # Run the agent
    goal = os.getenv("AGENT_GOAL", "daily_planning")
    run_agent(goal)


if __name__ == "__main__":
    main() 