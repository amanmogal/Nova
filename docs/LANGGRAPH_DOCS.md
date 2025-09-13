# LangGraph Documentation & Best Practices

## Overview
LangGraph is a library for building stateful, multi-actor applications with LLMs. It provides a framework for creating complex workflows with proper state management and checkpointing.

## Current Project Setup
- **LangGraph Version**: Latest (from requirements.txt)
- **LangChain Version**: Latest compatible version
- **Checkpointer**: MemorySaver (for development/testing)

## Core Concepts

### 1. StateGraph
The main building block for creating workflows.

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Define state schema
class AgentState(TypedDict):
    goal: str
    context: Dict[str, Any]
    messages: List[Dict]
    next_action: Optional[Dict]
    tool_calls: List[Dict]
    tool_results: List[Dict]
    error: Optional[str]

# Create graph
workflow = StateGraph(AgentState)
```

### 2. Node Functions
Each node function should:
- Take state as input
- Return partial state updates
- Be pure functions (no side effects)

```python
def perception_node(state: AgentState) -> AgentState:
    """Perception node: Gather context from environment."""
    # Process state and return updates
    return {"context": updated_context}

def reasoning_node(state: AgentState) -> AgentState:
    """Reasoning node: Generate next action."""
    # Analyze state and determine next action
    return {"next_action": action_plan}
```

### 3. Graph Construction
```python
def build_graph() -> StateGraph:
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
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "save_state",
        should_continue,
        {
            "continue": "reasoning",
            "end": END
        }
    )
    
    return workflow.compile(checkpointer=MemorySaver())
```

### 4. Conditional Edges
Use conditional edges for dynamic flow control:

```python
def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """Determine if the workflow should continue."""
    if state.get("error"):
        return "end"
    if state.get("goal_achieved", False):
        return "end"
    return "continue"
```

## Best Practices

### 1. State Management
- **Immutable Updates**: Always return new state objects, don't modify existing ones
- **Partial Updates**: Only return the keys that changed
- **Type Safety**: Use TypedDict for state schema definition

### 2. Error Handling
```python
def safe_node(state: AgentState) -> AgentState:
    try:
        # Node logic here
        return {"result": processed_data}
    except Exception as e:
        logger.error(f"Error in node: {e}")
        return {"error": str(e)}
```

### 3. Checkpointing
- **Development**: Use MemorySaver for testing
- **Production**: Use PostgresSaver for persistence
- **Thread IDs**: Always provide unique thread_id in config

```python
config = {
    "configurable": {
        "thread_id": f"agent_thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "checkpoint_ns": "agent_checkpoints"
    }
}
```

### 4. Graph Execution
```python
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

# Run graph
final_state = graph.invoke(initial_state, config=config)
```

## Common Patterns

### 1. Tool Integration
```python
async def action_node(state: AgentState) -> AgentState:
    """Execute tools based on next_action."""
    if not state.get("next_action"):
        result=await execute_action(state)
        return state
    
    tool_name = state["next_action"]["tool"]
    parameters = state["next_action"]["parameters"]
    
    if tool_name in TOOLS:
        try:
            result = TOOLS[tool_name](state)
            return {
                "tool_calls": state["tool_calls"] + [state["next_action"]],
                "tool_results": state["tool_results"] + [result]
            }
        except Exception as e:
            return {"error": f"Tool execution failed: {e}"}
    
    return {"error": f"Unknown tool: {tool_name}"}
```

### 2. Message Handling
```python
from langgraph.graph.message import add_messages

def add_message_to_state(state: AgentState, message: Dict) -> AgentState:
    """Add a message to the state."""
    return add_messages(state, [message])
```

### 3. State Validation
```python
def validate_state(state: AgentState) -> bool:
    """Validate state before processing."""
    required_keys = ["goal", "context", "messages"]
    return all(key in state for key in required_keys)
```

## Error Prevention Checklist

### Before Running Graph:
1.  Verify all imports are correct
2.  Check state schema matches TypedDict
3.  Ensure all nodes return proper state updates
4.  Validate conditional edge functions return correct literals
5.  Test node functions individually
6.  Verify tool mappings are complete

### During Development:
1.  Use logging for debugging
2.  Handle exceptions in each node
3.  Validate state at each step
4.  Test with minimal state first
5.  Check checkpoint configuration

### Common Issues & Solutions:

1. **Import Errors**
   ```python
   # Correct imports
   from langgraph.graph import StateGraph, END
   from langgraph.checkpoint.memory import MemorySaver
   from langgraph.graph.message import add_messages
   ```

2. **State Schema Mismatch**
   ```python
   # Ensure state updates match schema
   class AgentState(TypedDict):
       goal: str
       context: Dict[str, Any]
       # ... other fields
   
   # Return only changed fields
   return {"context": new_context}  # 
   # return {"invalid_field": value}  # 
   ```

3. **Conditional Edge Issues**
   ```python
   # Must return literal values
   def should_continue(state: AgentState) -> Literal["continue", "end"]:
       return "continue"  # 
       # return "invalid"  # 
   ```

4. **Checkpointing Issues**
   ```python
   # Always provide thread_id
   config = {
       "configurable": {
           "thread_id": "unique_thread_id",  # 
           # Missing thread_id  # 
       }
   }
   ```

## Testing Patterns

### 1. Graph Structure Testing
```python
def test_graph_structure():
    graph = build_graph()
    assert "perception" in graph.nodes
    assert "reasoning" in graph.nodes
    assert "action" in graph.nodes
    assert "save_state" in graph.nodes
```

### 2. Node Function Testing
```python
def test_perception_node():
    test_state = AgentState(
        goal="test_goal",
        context={},
        messages=[],
        next_action=None,
        tool_calls=[],
        tool_results=[],
        error=None
    )
    result = perception_node(test_state)
    assert isinstance(result, dict)
    assert "context" in result
```

### 3. End-to-End Testing
```python
async def test_full_workflow():
    initial_state = AgentState(
        goal="daily_planning",
        context={},
        messages=[],
        next_action=None,
        tool_calls=[],
        tool_results=[],
        error=None
    )
    
    config = {
        "configurable": {
            "thread_id": f"test_thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "checkpoint_ns": "test_checkpoints"
        }
    }
    
    final_state = graph.invoke(initial_state, config=config)
    assert final_state is not None
    assert "error" not in final_state or final_state["error"] is None
```

## Performance Considerations

1. **Memory Usage**: Use MemorySaver only for development
2. **State Size**: Keep state objects small and focused
3. **Node Efficiency**: Make nodes as lightweight as possible
4. **Checkpointing**: Use appropriate checkpoint intervals

## Migration Notes

When updating LangGraph versions:
1. Check for breaking changes in imports
2. Verify state schema compatibility
3. Test all conditional edges
4. Update checkpointing configuration if needed

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph)
- [LangChain Integration](https://python.langchain.com/docs/langgraph) 