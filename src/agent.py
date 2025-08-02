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
# LangGraph imports for proper control flow
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
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
        
        # Ensure query is not empty
        if not query or not query.strip():
            query = "pending tasks"
            logger.info(f"Empty query provided, using default: {query}")
        
        tasks = rag_engine.search_tasks(query, n_results=limit)
        
        # Log the action
        db.log_action(
            action_type="search_tasks",
            details={"query": query, "limit": limit, "results_count": len(tasks)}
        )
        
        # Update state with results
        state["search_results"] = {"success": True, "tasks": tasks}
        
        # Check if tasks have proper IDs
        tasks_with_ids = []
        tasks_without_ids = []
        
        for task in tasks:
            task_id = task.get("id", "")
            if task_id and task_id.startswith(("21", "22", "23", "24", "25", "26", "27", "28", "29", "30")):
                tasks_with_ids.append(task)
            else:
                tasks_without_ids.append(task)
        
        # Log the findings
        logger.info(f"Found {len(tasks)} tasks: {len(tasks_with_ids)} with IDs, {len(tasks_without_ids)} without IDs")
        
        # If we have a pending update, try to find the matching task
        if state.get("pending_update"):
            pending_update = state["pending_update"]
            original_task_id = pending_update["original_task_id"]
            
            # Look for a task with matching title
            for task in tasks:
                task_title = task.get("metadata", {}).get("title", "")
                if original_task_id.lower() in task_title.lower():
                    # Found the task, set up the update
                    state["current_task_id"] = task.get("id", "")
                    state["current_task_properties"] = pending_update["properties"]
                    state["next_action"] = "update_task"
                    # Clear the pending update
                    state.pop("pending_update", None)
                    logger.info(f"Found task '{original_task_id}' with ID {task.get('id', '')}, proceeding with update")
                    break
            else:
                # Task not found, clear pending update and end
                state.pop("pending_update", None)
                state["next_action"] = "end"
                logger.warning(f"Task '{original_task_id}' not found in search results")
        
        # If we found tasks but they don't have proper IDs, this might indicate a configuration issue
        if tasks_without_ids and not tasks_with_ids:
            logger.warning("Found tasks but none have proper Notion page IDs. This may indicate a database configuration issue.")
            state["search_warning"] = "Tasks found but missing proper IDs - check Notion database configuration"
        
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
def perception_node(state: AgentState) -> AgentState:
    """Perception node: Gather context from environment."""
    return perception(state)

def reasoning_node(state: AgentState) -> AgentState:
    """Reasoning node: Generate the next action based on context."""
    return reasoning(state)

def action_node(state: AgentState) -> AgentState:
    """Action node: Execute the determined action."""
    import asyncio
    
    # Run the async execute_action in an event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an event loop, we need to create a new one
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, execute_action(state))
                return future.result()
        else:
            return loop.run_until_complete(execute_action(state))
    except RuntimeError:
        # If no event loop is running, create a new one
        return asyncio.run(execute_action(state))

def save_state_node(state: AgentState) -> AgentState:
    """Save state node: Persist the current state."""
    return save_state(state)

def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """Determine if the agent should continue or end."""
    next_action = state.get("next_action")
    error = state.get("error")
    
    # Add loop counter to prevent infinite loops
    loop_count = state.get("loop_count", 0)
    state["loop_count"] = loop_count + 1
    
    # Prevent infinite loops (max 3 iterations to be safe - reduced from 5)
    if loop_count >= 3:
        logger.warning("Agent ending due to maximum loop count reached")
        return "end"
    
    # Detect if we're stuck in a search loop (reduced threshold)
    if loop_count >= 2:
        # Check if we've been doing the same action repeatedly
        recent_actions = state.get("recent_actions", [])
        if len(recent_actions) >= 2:
            # Check if the last 2 actions are all search_tasks
            if all(action == "search_tasks" for action in recent_actions[-2:]):
                logger.warning("Agent ending due to search loop detection")
                return "end"
    
    # Check if we've been searching too much
    recent_actions = state.get("recent_actions", [])
    search_count = sum(1 for action in recent_actions if action == "search_tasks")
    if search_count >= 3:
        logger.warning("Agent ending due to excessive search operations")
        return "end"
    
    if error:
        logger.error(f"Agent ending due to error: {error}")
        return "end"
    
    if not next_action or next_action == "end":
        logger.info("Agent ending - no more actions")
        return "end"
    
    return "continue"

def build_graph() -> StateGraph:
    """Build the LangGraph workflow."""
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("perception", perception_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("action", action_node)
    workflow.add_node("save_state", save_state_node)
    
    # Set entry point
    workflow.set_entry_point("perception")
    
    # Add edges
    workflow.add_edge("perception", "reasoning")
    workflow.add_edge("reasoning", "action")
    workflow.add_edge("action", "save_state")
    
    # Add conditional edge from save_state
    workflow.add_conditional_edges(
        "save_state",
        should_continue,
        {
            "continue": "reasoning",
            "end": END
        }
    )
    
    return workflow.compile(checkpointer=MemorySaver())

# Create the compiled graph
graph = build_graph()

def create_agent():
    """Create the agent graph for LangGraph Studio."""
    return graph

# Core agent functions
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
    
    # Build comprehensive context
    context_str = f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    # Add task details
    tasks = state['context'].get('tasks', [])
    task_count = len(tasks)
    context_str += f"Available tasks: {task_count}\n"
    
    if tasks:
        context_str += "Task details:\n"
        for i, task in enumerate(tasks[:3]):  # Show first 3 tasks
            metadata = task.get('metadata', {})
            content = task.get('content', '')[:100]  # First 100 chars
            context_str += f"  {i+1}. {metadata.get('title', 'Unknown')} - {metadata.get('status', 'No status')}\n"
            context_str += f"     Content: {content}...\n"
    
    # Add routine details
    routines = state['context'].get('routines', [])
    routine_count = len(routines)
    context_str += f"\nAvailable routines: {routine_count}\n"
    
    if routines:
        context_str += "Routine details:\n"
        for i, routine in enumerate(routines[:3]):  # Show first 3 routines
            metadata = routine.get('metadata', {})
            content = routine.get('content', '')[:100]  # First 100 chars
            context_str += f"  {i+1}. {metadata.get('task', 'Unknown')} - {metadata.get('category', 'No category')}\n"
            context_str += f"     Content: {content}...\n"
    
    # Add calendar preferences
    context_str += f"\nWork hours: {state['context'].get('calendar_view_start', '10:00')} to {state['context'].get('calendar_view_end', '02:00')}\n"
    
    # Add previous tool results
    if state.get("tool_results"):
        context_str += "\nPrevious actions completed successfully.\n"
    
    # Create the user message with system prompt and context
    user_message = f"{system_prompt}\n\n{context_str}"
    
    messages.append({
        "role": "user",
        "parts": [user_message]
    })
    
    # For now, don't add previous messages to prevent context issues
    # This will be fixed in a future iteration with proper conversation management
    # previous_messages = state.get("messages", [])
    # if len(previous_messages) > 4:  # Keep only last 2 pairs (4 messages total)
    #     previous_messages = previous_messages[-4:]
    # 
    # # Add previous messages in proper conversation format
    # for msg in previous_messages:
    #     if msg.get("role") == "assistant":
    #         messages.append({
    #             "role": "model",
    #             "parts": [msg.get("parts", [""])[0]]
    #         })
    #     elif msg.get("role") == "user":
    #         messages.append({
    #             "role": "user",
    #             "parts": [msg.get("parts", [""])[0]]
    #         })
    
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
        
        # For now, don't maintain message history to prevent context issues
        # This will be fixed in a future iteration with proper conversation management
        # state["messages"] = []  # Clear message history
        
        # Parse JSON response for structured tool calls
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                logger.info(f"Attempting to parse JSON: {json_str}")
                parsed_response = json.loads(json_str)
                
                # Extract action details
                action = parsed_response.get('action', {})
                tool_name = action.get('tool')
                parameters = action.get('parameters', {})
                reasoning = parsed_response.get('reasoning', '')
                confidence = parsed_response.get('confidence', 0.5)
                
                logger.info(f"Parsed action: {tool_name} with parameters: {parameters}")
                logger.info(f"Reasoning: {reasoning}")
                logger.info(f"Confidence: {confidence}")
                
                # Set next action based on parsed JSON
                if tool_name and tool_name in TOOLS:
                    state["next_action"] = tool_name
                    state["action_parameters"] = parameters
                    state["action_reasoning"] = reasoning
                    state["action_confidence"] = confidence
                    
                    # Set specific parameters for tools
                    if tool_name == "search_tasks":
                        state["current_query"] = parameters.get("query", "pending tasks")
                    elif tool_name == "update_task":
                        task_id = parameters.get("task_id", "")
                        properties = parameters.get("properties", {})
                        
                        # If task_id is a title (not a UUID), we need to search for it first
                        if task_id and not task_id.startswith(("21", "22", "23", "24", "25", "26", "27", "28", "29", "30")):
                            # This is likely a task title, not an ID - search for it
                            state["next_action"] = "search_tasks"
                            state["current_query"] = task_id
                            state["pending_update"] = {
                                "properties": properties,
                                "original_task_id": task_id
                            }
                            logger.info(f"Task ID '{task_id}' appears to be a title, searching for it first")
                        elif tasks:
                            # Try to find a task with a proper ID
                            task_with_id = None
                            for task in tasks:
                                task_metadata = task.get("metadata", {})
                                task_parent_id = task_metadata.get("parent_id", "")
                                if task_parent_id and task_parent_id.startswith(("21", "22", "23", "24", "25", "26", "27", "28", "29", "30")):
                                    task_with_id = task
                                    break
                            
                            if task_with_id:
                                task_metadata = task_with_id["metadata"]
                                state["current_task_id"] = task_id or task_metadata.get("parent_id", "")
                                state["current_task_properties"] = properties
                                logger.info(f"Using task ID: {state['current_task_id']}")
                            else:
                                # No task with proper ID found, send notification and end
                                state["next_action"] = "send_notification"
                                state["notification_message"] = "Daily planning completed: Found tasks but unable to update due to missing task IDs. Please check your Notion database configuration."
                                state["notification_priority"] = "warning"
                                logger.warning("No task with proper ID found, sending notification and ending")
                        else:
                            state["next_action"] = "end"
                    elif tool_name == "create_task":
                        state["new_task_title"] = parameters.get("title", "")
                        state["new_task_status"] = parameters.get("status", "Not Started")
                        state["new_task_priority"] = parameters.get("priority", "Medium")
                        state["new_task_due_date"] = parameters.get("due_date", "")
                    elif tool_name == "send_notification":
                        state["notification_message"] = parameters.get("message", "")
                        state["notification_priority"] = parameters.get("priority", "normal")
                else:
                    logger.warning(f"Unknown tool: {tool_name}")
                    state["next_action"] = "end"
            else:
                logger.warning("No JSON found in response, falling back to text parsing")
                # Fallback to simple text parsing for backward compatibility
                response_text_lower = response_text.lower()
                
                            # Default to search_tasks for daily planning, but check if we've already searched
                if state["goal"] == "daily_planning":
                    # Check if we've already searched recently to prevent loops
                    recent_actions = state.get("recent_actions", [])
                    search_count = sum(1 for action in recent_actions if action == "search_tasks")
                    
                    if search_count >= 2:
                        # We've searched enough, check if we have tasks with proper IDs
                        tasks = state.get('context', {}).get('tasks', [])
                        tasks_with_ids = []
                        
                        for task in tasks:
                            task_id = task.get("id", "")
                            if task_id and task_id.startswith(("21", "22", "23", "24", "25", "26", "27", "28", "29", "30")):
                                tasks_with_ids.append(task)
                        
                        if tasks_with_ids:
                            # We have tasks with IDs, proceed with update
                            state["next_action"] = "update_task"
                            task_metadata = tasks_with_ids[0].get("metadata", {})
                            state["current_task_id"] = task_metadata.get("parent_id", "")
                            state["current_task_properties"] = {"scheduled_time": "2025-08-03 10:00"}
                            logger.info("Found tasks with IDs, proceeding with update")
                        else:
                            # No tasks with proper IDs, send notification and end
                            state["next_action"] = "send_notification"
                            state["notification_message"] = "Daily planning completed: Found tasks but unable to schedule due to missing task IDs. Please check your Notion database configuration."
                            state["notification_priority"] = "warning"
                            logger.info("Search limit reached, no tasks with proper IDs, sending notification and ending")
                    elif recent_actions and recent_actions[-1] == "search_tasks":
                        # We just searched, so end the session to prevent loops
                        state["next_action"] = "end"
                        logger.info("Already searched recently, ending session to prevent loops")
                    else:
                        state["next_action"] = "search_tasks"
                        state["current_query"] = "pending tasks"
                        logger.info("Defaulting to search_tasks for daily planning")
                elif "search" in response_text_lower or "find" in response_text_lower:
                    state["next_action"] = "search_tasks"
                    state["current_query"] = "pending tasks"
                elif "update" in response_text_lower or "schedule" in response_text_lower:
                    if tasks:
                        state["next_action"] = "update_task"
                        task_metadata = tasks[0]["metadata"]
                        state["current_task_id"] = task_metadata.get("parent_id", "")
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
                    
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            # Don't set error, just fall back to text parsing
            logger.info("Falling back to text parsing due to JSON decode error")
            
            # Fallback to simple text parsing
            response_text_lower = response_text.lower()
            
            # Default to search_tasks for daily planning
            if state["goal"] == "daily_planning":
                state["next_action"] = "search_tasks"
                state["current_query"] = "pending tasks"
                logger.info("Defaulting to search_tasks for daily planning after JSON error")
            elif "search" in response_text_lower or "find" in response_text_lower:
                state["next_action"] = "search_tasks"
                state["current_query"] = "pending tasks"
            elif "update" in response_text_lower or "schedule" in response_text_lower:
                if tasks:
                    state["next_action"] = "update_task"
                    task_metadata = tasks[0]["metadata"]
                    state["current_task_id"] = task_metadata.get("parent_id", "")
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
    
    # Track recent actions for loop detection
    if "recent_actions" not in state:
        state["recent_actions"] = []
    state["recent_actions"].append(next_action)
    
    # Keep only the last 5 actions to prevent memory bloat
    if len(state["recent_actions"]) > 5:
        state["recent_actions"] = state["recent_actions"][-5:]
    
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


async def run_agent(goal: str = "daily_planning") -> Dict[str, Any]:
    """
    Run the agent with the specified goal using LangGraph.
    
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
    
    # Run the agent using LangGraph
    try:
        logger.info("Starting LangGraph execution")
        
        # Run the graph with the initial state
        # Use invoke() method for LangGraph with proper config and reduced recursion limit
        config = {
            "configurable": {
                "thread_id": f"agent_thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "checkpoint_ns": "agent_checkpoints",
                "checkpoint_id": f"agent_thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            },
            "recursion_limit": 50  # Increased to allow more steps for complex tasks or to hit custom termination conditions
        }
        final_state = graph.invoke(initial_state, config=config)
        
        logger.info("LangGraph execution completed successfully")
        return final_state
        
    except Exception as e:
        error = f"Error in LangGraph execution: {str(e)}"
        logger.error(error)
        initial_state["error"] = error
        return initial_state


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