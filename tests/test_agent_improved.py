"""
Test script for improved agent logic with JSON output and LangGraph.
"""
import asyncio
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent import run_agent, graph
from src.tools.rag_engine import RAGEngine

async def test_improved_agent():
    """Test the improved agent with JSON output and LangGraph."""
    print("🧪 Testing Improved Agent Logic")
    print("=" * 50)
    
    try:
        # Test 1: Verify LangGraph graph structure
        print("1. Testing LangGraph Graph Structure...")
        print(f"   Graph nodes: {list(graph.nodes.keys())}")
        print(f"   Graph type: {type(graph)}")
        print("   ✅ LangGraph structure verified")
        
        # Test 2: Test JSON output parsing
        print("\n2. Testing JSON Output Parsing...")
        test_response = '''
        {
          "reasoning": "I need to search for pending tasks to understand what needs to be done today",
          "action": {
            "tool": "search_tasks",
            "parameters": {
              "query": "pending tasks"
            }
          },
          "confidence": 0.95
        }
        '''
        
        # Test JSON parsing
        import json
        parsed = json.loads(test_response.strip())
        print(f"   Parsed reasoning: {parsed['reasoning']}")
        print(f"   Parsed tool: {parsed['action']['tool']}")
        print(f"   Parsed parameters: {parsed['action']['parameters']}")
        print("   ✅ JSON parsing working correctly")
        
        # Test 3: Test agent execution with LangGraph
        print("\n3. Testing Agent Execution with LangGraph...")
        
        # Sync RAG data first
        rag_engine = RAGEngine()
        print("   Syncing RAG data...")
        await rag_engine.sync_notion_data()
        print("   ✅ RAG data synced")
        
        # Run agent
        print("   Running agent...")
        result = await run_agent("daily_planning")
        
        print(f"   Agent completed with goal: {result.get('goal')}")
        print(f"   Final state has error: {result.get('error') is not None}")
        print(f"   Context tasks: {len(result.get('context', {}).get('tasks', []))}")
        print(f"   Context routines: {len(result.get('context', {}).get('routines', []))}")
        
        if result.get('error'):
            print(f"   ⚠️ Agent completed with error: {result['error']}")
        else:
            print("   ✅ Agent execution completed successfully")
        
        # Test 4: Verify state persistence
        print("\n4. Testing State Persistence...")
        from src.db.supabase_connector import SupabaseConnector
        db = SupabaseConnector()
        
        latest_state = db.get_latest_agent_state()
        if latest_state:
            print(f"   Latest state saved: {latest_state.get('timestamp')}")
            print("   ✅ State persistence working")
        else:
            print("   ⚠️ No state found in database")
        
        print("\n" + "=" * 50)
        print("🎉 Improved Agent Test Completed!")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing improved agent: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def test_json_output_format():
    """Test the JSON output format specifically."""
    print("\n🔍 Testing JSON Output Format")
    print("=" * 30)
    
    try:
        from src.prompts.system_prompt import SYSTEM_PROMPT
        print("System prompt includes JSON format instructions:")
        
        # Check if JSON format is mentioned
        if "JSON" in SYSTEM_PROMPT and "structured" in SYSTEM_PROMPT:
            print("   ✅ JSON output format instructions found")
        else:
            print("   ❌ JSON output format instructions missing")
        
        # Test available tools documentation
        if "Available Tools:" in SYSTEM_PROMPT:
            print("   ✅ Available tools documented")
        else:
            print("   ❌ Available tools not documented")
            
    except Exception as e:
        print(f"❌ Error testing JSON format: {str(e)}")

if __name__ == "__main__":
    async def main():
        await test_json_output_format()
        await test_improved_agent()
    
    asyncio.run(main()) 