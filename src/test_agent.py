"""
Simple test script for the agent functionality.
"""
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import run_agent
from src.tools.rag_engine import RAGEngine

def test_agent_basic():
    """Test basic agent functionality."""
    print(" Testing Agent Basic Functionality")
    print("=" * 50)
    
    # First, sync the RAG engine
    print("Syncing RAG engine...")
    rag_engine = RAGEngine()
    # Note: sync_notion_data is async, but we'll skip it for now
    # rag_engine.sync_notion_data()
    print("RAG sync skipped (async method)")
    
    # Test daily planning
    print("\n Testing Daily Planning Agent...")
    try:
        result = run_agent("daily_planning")
        print("Agent run completed successfully")
        print(f" Final state keys: {list(result.keys())}")
        
        if "error" in result and result["error"]:
            print(f" Error in agent run: {result['error']}")
        else:
            print("No errors detected")
            
        if "tool_results" in result:
            print(f" Tool executions: {len(result['tool_results'])}")
            for i, tool_result in enumerate(result['tool_results'], 1):
                print(f"  {i}. {tool_result['tool_name']}: {'ok' if tool_result['result'].get('success') else 'no'}")
        
    except Exception as e:
        print(f" Error running agent: {str(e)}")
        import traceback
        traceback.print_exc()

def test_agent_tools():
    """Test individual agent tools."""
    print("\n🔧 Testing Agent Tools")
    print("=" * 50)
    
    from src.agent import search_tasks_tool, get_routines_tool
    
    # Test search tool
    print("🔍 Testing search_tasks_tool...")
    try:
        state = {
            "current_query": "pending tasks",
            "search_limit": 3
        }
        result = search_tasks_tool(state)
        if "search_results" in result and result["search_results"].get("success"):
            tasks = result["search_results"]["tasks"]
            print(f" Found {len(tasks)} tasks")
        else:
            print(" Search failed")
    except Exception as e:
        print(f"Error testing search tool: {str(e)}")
    
    # Test routines tool
    print(" Testing get_routines_tool...")
    try:
        state = {}
        result = get_routines_tool(state)
        if "routines_result" in result and result["routines_result"].get("success"):
            routines = result["routines_result"]["routines"]
            print(f" Found {len(routines)} routines")
        else:
            print("ℹNo routines found (expected if no routines database)")
    except Exception as e:
        print(f" Error testing routines tool: {str(e)}")

if __name__ == "__main__":
    print(f"Starting Agent Tests at {datetime.now()}")
    print("=" * 60)
    
    test_agent_tools()
    test_agent_basic()
    
    print("\n" + "=" * 60)
    print("🏁 Agent Tests Completed") 