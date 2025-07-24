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
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolInvocation

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


# Tool definitions
def search_tasks_tool(query: str, limit: int = 5) -> Dict[str, Any]:
    """
    Search for tasks in Notion.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        Dictionary with search results
    """
    try:
        tasks = rag_engine.search_tasks(query, n_results=limit)
        
        # Log the action
        db.log_action(
            action_type="search_tasks",
            details={"query": query, "limit": limit, "results_count": len(tasks)}
        )
        
        return {"success": True, "tasks": tasks}
    except Exception as e:
        error = f"Error searching tasks: {str(e)}"
        logger.error(error)
        
        # Log the error
        db.log_action(
            action_type="search_tasks",
            details={"query": query, "limit": limit, "error": str(e)},
            status="error"
        )
        
        return {"success": False, "error": error}


def update_task_tool(task_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a task in Notion.
    
    Args:
        task_id: The Notion page ID of the task
        properties: Dictionary of properties to update
        
    Returns:
        Dictionary with update result
    """
    try:
        result = notion.update_task(task_id, properties)
        
        # Log the action
        db.log_action(
            action_type="update_task",
            details={"task_id": task_id, "properties": properties}
        )
        
        return {"success": result, "task_id": task_id}
    except Exception as e:
        error = f"Error updating task {task_id}: {str(e)}"
        logger.error(error)
        
        # Log the error
        db.log_action(
            action_type="update_task",
            details={"task_id": task_id, "properties": properties, "error": str(e)},
            status="error"
        )
        
        return {"success": False, "error": error, "task_id": task_id}


def create_task_tool(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new task in Notion.
    
    Args:
        task_data: Dictionary with task properties
        
    Returns:
        Dictionary with creation result
    """
    try:
        task_id = notion.create_task(task_data)
        
        if task_id:
            # Log the action
            db.log_action(
                action_type="create_task",
                details={"task_data": task_data, "task_id": task_id}
            )
            
            return {"success": True, "task_id": task_id}
        else:
            return {"success": False, "error": "Failed to create task"}
    except Exception as e:
        error = f"Error creating task: {str(e)}"
        logger.error(error)
        
        # Log the error
        db.log_action(
            action_type="create_task",
            details={"task_data": task_data, "error": str(e)},
            status="error"
        )
        
        return {"success": False, "error": error}


def send_notification_tool(recipient: str, subject: str, message: str, 
                          priority: str = "normal") -> Dict[str, Any]:
    """
    Send a notification to the user.
    
    Args:
        recipient: Email address of the recipient
        subject: Subject line of the notification
        message: Body of the notification
        priority: Priority level (low, normal, high)
        
    Returns:
        Dictionary with notification result
    """
    try:
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
        
        return {"success": result}
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
        
        return {"success": False, "error": error}


def get_routines_tool() -> Dict[str, Any]:
    """
    Get the user's routines from Notion.
    
    Returns:
        Dictionary with routines
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
        
        return {"success": True, "routines": routines_data}
    except Exception as e:
        error = f"Error getting routines: {str(e)}"
        logger.error(error)
        
        # Log the error
        db.log_action(
            action_type="get_routines",
            details={"error": str(e)},
            status="error"
        )
        
        return {"success": False, "error": error}


# Available tools mapping
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
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with next action
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
        os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        tools=[
            {
                "name": "search_tasks",
                "description": "Search for tasks in Notion based on a query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "update_task",
                "description": "Update a task in Notion",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The Notion page ID of the task"
                        },
                        "properties": {
                            "type": "object",
                            "description": "Dictionary of properties to update"
                        }
                    },
                    "required": ["task_id", "properties"]
                }
            },
            {
                "name": "create_task",
                "description": "Create a new task in Notion",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_data": {
                            "type": "object",
                            "description": "Dictionary with task properties"
                        }
                    },
                    "required": ["task_data"]
                }
            },
            {
                "name": "send_notification",
                "description": "Send a notification to the user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipient": {
                            "type": "string",
                            "description": "Email address of the recipient"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Subject line of the notification"
                        },
                        "message": {
                            "type": "string",
                            "description": "Body of the notification"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "normal", "high"],
                            "default": "normal",
                            "description": "Priority level of the notification"
                        }
                    },
                    "required": ["recipient", "subject", "message"]
                }
            },
            {
                "name": "get_routines",
                "description": "Get the user's routines from Notion",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    )
    
    try:
        response = model.generate_content(messages)
        
        # Check for tool calls
        state["tool_calls"] = []
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and candidate.content:
                content = candidate.content
                
                # Process tool calls
                if hasattr(content, "parts"):
                    for part in content.parts:
                        if hasattr(part, "function_call"):
                            function_call = part.function_call
                            state["tool_calls"].append({
                                "name": function_call.name,
                                "arguments": json.loads(function_call.args)
                            })
        
        # Update messages
        if not state.get("messages"):
            state["messages"] = []
        
        state["messages"].append({
            "role": "assistant",
            "parts": [response.text]
        })
        
        return state
    except Exception as e:
        error = f"Error in reasoning: {str(e)}"
        logger.error(error)
        state["error"] = error
        return state


def action(state: AgentState) -> Union[AgentState, Literal["reasoning", "end"]]:
    """
    Action node: Execute tool calls.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node to transition to
    """
    tool_calls = state.get("tool_calls", [])
    
    if not tool_calls:
        logger.info("Action: No tool calls to execute, ending")
        return "end"
    
    logger.info(f"Action: Executing {len(tool_calls)} tool call(s)")
    
    # Initialize tool_results if not present
    if "tool_results" not in state:
        state["tool_results"] = []
    
    # Execute each tool call
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        arguments = tool_call["arguments"]
        
        if tool_name in TOOLS:
            try:
                logger.info(f"Executing tool: {tool_name} with args: {arguments}")
                tool_fn = TOOLS[tool_name]
                result = tool_fn(**arguments)
                
                state["tool_results"].append({
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "result": result
                })
            except Exception as e:
                error = f"Error executing tool {tool_name}: {str(e)}"
                logger.error(error)
                
                state["tool_results"].append({
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "result": {"success": False, "error": error}
                })
        else:
            error = f"Unknown tool: {tool_name}"
            logger.error(error)
            
            state["tool_results"].append({
                "tool_name": tool_name,
                "arguments": arguments,
                "result": {"success": False, "error": error}
            })
    
    # Clear tool calls
    state["tool_calls"] = []
    
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
    
    # Add edges
    graph.add_edge("perception", "reasoning")
    graph.add_edge("reasoning", "action")
    graph.add_edge("action", "reasoning")
    graph.add_edge("action", "end")
    graph.add_edge("reasoning", "save_state")
    graph.add_edge("save_state", "end")
    
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
    
    # Run the graph
    result = graph.invoke(initial_state)
    
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