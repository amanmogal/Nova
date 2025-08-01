#!/usr/bin/env python3
"""
Debug script that tests the exact reasoning_node function from the agent.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent import reasoning_node
from src.config import get_settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_reasoning_node():
    """Test the exact reasoning_node function from the agent."""
    
    print("Testing the exact reasoning_node function...")
    
    # Create a test state similar to what the agent uses
    state = {
        "goal": "daily_planning",
        "context": {
            "current_time": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "work_hours": "10:00 to 02:00",
            "available_tasks": 3,
            "available_routines": 2
        },
        "messages": [],
        "search_results": {
            "success": True,
            "tasks": [
                {
                    "id": "task1",
                    "metadata": {
                        "title": "Todo 24/6",
                        "status": "In Progress",
                        "parent_id": "page_id_1"
                    }
                },
                {
                    "id": "task2", 
                    "metadata": {
                        "title": "implementation day 1",
                        "status": "In Progress",
                        "parent_id": "page_id_2"
                    }
                }
            ]
        },
        "routine_results": {
            "success": True,
            "routines": [
                {
                    "id": "routine1",
                    "metadata": {
                        "title": "Morning Planning Session",
                        "category": "Planning"
                    }
                }
            ]
        }
    }
    
    # Test 1: First call to reasoning_node
    print("\n=== Test 1: First Call to reasoning_node ===")
    try:
        result = reasoning_node(state)
        print(f"✅ reasoning_node executed successfully")
        print(f"Next action: {result.get('next_action', 'None')}")
        print(f"Current query: {result.get('current_query', 'None')}")
        print(f"Error: {result.get('error', 'None')}")
        
        # Store the result for next test
        first_result = result
        
    except Exception as e:
        print(f"❌ Error in first call: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Second call to reasoning_node (with message history)
    print("\n=== Test 2: Second Call to reasoning_node (With History) ===")
    try:
        # Add the previous result to the state
        state.update(first_result)
        
        # Update the state to simulate what happens after an action
        state["search_results"]["tasks"] = state["search_results"]["tasks"][:1]  # Reduce tasks
        
        result = reasoning_node(state)
        print(f"✅ Second reasoning_node call executed successfully")
        print(f"Next action: {result.get('next_action', 'None')}")
        print(f"Current query: {result.get('current_query', 'None')}")
        print(f"Error: {result.get('error', 'None')}")
        
    except Exception as e:
        print(f"❌ Error in second call: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Test with error state
    print("\n=== Test 3: Test with Error State ===")
    try:
        error_state = state.copy()
        error_state["error"] = "Test error"
        
        result = reasoning_node(error_state)
        print(f"✅ Error state handled successfully")
        print(f"Next action: {result.get('next_action', 'None')}")
        print(f"Error: {result.get('error', 'None')}")
        
    except Exception as e:
        print(f"❌ Error in error state test: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Test with empty search results
    print("\n=== Test 4: Test with Empty Search Results ===")
    try:
        empty_state = state.copy()
        empty_state["search_results"] = {"success": True, "tasks": []}
        empty_state["routine_results"] = {"success": True, "routines": []}
        
        result = reasoning_node(empty_state)
        print(f"✅ Empty results handled successfully")
        print(f"Next action: {result.get('next_action', 'None')}")
        print(f"Current query: {result.get('current_query', 'None')}")
        
    except Exception as e:
        print(f"❌ Error in empty results test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reasoning_node() 