#!/usr/bin/env python3
"""
LangGraph Validation Script
Validates the current LangGraph implementation for common issues and best practices.
"""

import sys
import os
import importlib
import inspect
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def validate_imports():
    """Validate all required LangGraph imports."""
    print(" Validating LangGraph imports...")
    
    required_imports = [
        ("langgraph.graph", ["StateGraph", "END"]),
        ("langgraph.checkpoint.memory", ["MemorySaver"]),
        ("langgraph.graph.message", ["add_messages"]),
    ]
    
    all_valid = True
    for module, items in required_imports:
        try:
            mod = importlib.import_module(module)
            for item in items:
                if hasattr(mod, item):
                    print(f"   {module}.{item}")
                else:
                    print(f"   {module}.{item} - NOT FOUND")
                    all_valid = False
        except ImportError as e:
            print(f"   {module} - Import failed: {e}")
            all_valid = False
    
    return all_valid

def validate_state_schema():
    """Validate the AgentState schema."""
    print("\n Validating AgentState schema...")
    
    try:
        from src.agent import AgentState
        
        # Check if it's a TypedDict
        if not hasattr(AgentState, '__annotations__'):
            print("   AgentState is not a TypedDict")
            return False
        
        # Check required fields
        required_fields = {
            'goal': str,
            'context': dict,
            'messages': list,
            'next_action': Optional[dict],
            'tool_calls': list,
            'tool_results': list,
            'error': Optional[str]
        }
        
        annotations = AgentState.__annotations__
        all_valid = True
        
        for field, expected_type in required_fields.items():
            if field in annotations:
                print(f"   {field}: {annotations[field]}")
            else:
                print(f"   Missing field: {field}")
                all_valid = False
        
        return all_valid
        
    except ImportError as e:
        print(f"   Could not import AgentState: {e}")
        return False

def validate_node_functions():
    """Validate node function signatures and patterns."""
    print("\n Validating node functions...")
    
    try:
        from src.agent import perception_node, reasoning_node, action_node, save_state_node
        
        node_functions = [
            ("perception_node", perception_node),
            ("reasoning_node", reasoning_node),
            ("action_node", action_node),
            ("save_state_node", save_state_node),
        ]
        
        all_valid = True
        
        for name, func in node_functions:
            # Check signature
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            
            if len(params) == 1 and params[0] == 'state':
                print(f"   {name}: Correct signature")
            else:
                print(f"   {name}: Incorrect signature - expected 'state' parameter")
                all_valid = False
            
            # Check return type annotation
            if sig.return_annotation != inspect.Signature.empty:
                print(f"   {name}: Has return type annotation")
            else:
                print(f"    {name}: Missing return type annotation")
        
        return all_valid
        
    except ImportError as e:
        print(f"   Could not import node functions: {e}")
        return False

def validate_conditional_edges():
    """Validate conditional edge functions."""
    print("\n Validating conditional edge functions...")
    
    try:
        from src.agent import should_continue
        
        # Check signature
        sig = inspect.signature(should_continue)
        params = list(sig.parameters.keys())
        
        if len(params) == 1 and params[0] == 'state':
            print("   should_continue: Correct signature")
        else:
            print("   should_continue: Incorrect signature")
            return False
        
        # Check return type
        if sig.return_annotation == Literal["continue", "end"]:
            print("   should_continue: Correct return type")
        else:
            print("   should_continue: Incorrect return type - should be Literal['continue', 'end']")
            return False
        
        return True
        
    except ImportError as e:
        print(f"   Could not import should_continue: {e}")
        return False

def validate_graph_structure():
    """Validate the graph structure."""
    print("\n Validating graph structure...")
    
    try:
        from src.agent import graph
        
        # Check if graph is compiled
        if hasattr(graph, 'nodes'):
            print("   Graph is compiled")
        else:
            print("   Graph is not compiled")
            return False
        
        # Check required nodes
        required_nodes = ["perception", "reasoning", "action", "save_state"]
        all_valid = True
        
        for node in required_nodes:
            if node in graph.nodes:
                print(f"   Node '{node}' exists")
            else:
                print(f"   Missing node: '{node}'")
                all_valid = False
        
        return all_valid
        
    except ImportError as e:
        print(f"   Could not import graph: {e}")
        return False

def validate_tool_mappings():
    """Validate tool mappings."""
    print("\n Validating tool mappings...")
    
    try:
        from src.agent import TOOLS
        
        if not isinstance(TOOLS, dict):
            print("   TOOLS is not a dictionary")
            return False
        
        required_tools = ["search_tasks", "update_task", "create_task", "send_notification", "get_routines"]
        all_valid = True
        
        for tool in required_tools:
            if tool in TOOLS:
                print(f"   Tool '{tool}' mapped")
            else:
                print(f"   Missing tool mapping: '{tool}'")
                all_valid = False
        
        return all_valid
        
    except ImportError as e:
        print(f"   Could not import TOOLS: {e}")
        return False

def validate_configuration():
    """Validate configuration patterns."""
    print("\n Validating configuration patterns...")
    
    try:
        from src.agent import run_agent
        
        # Check if run_agent function exists and has proper config
        if callable(run_agent):
            print("   run_agent function exists")
            
            # Check if it uses proper config pattern
            source = inspect.getsource(run_agent)
            if "thread_id" in source and "configurable" in source:
                print("   Uses proper configuration pattern")
                return True
            else:
                print("   Missing proper configuration pattern")
                return False
        else:
            print("   run_agent is not callable")
            return False
            
    except ImportError as e:
        print(f"   Could not import run_agent: {e}")
        return False

def run_validation():
    """Run all validation checks."""
    print(" LangGraph Validation Report")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    validations = [
        ("Imports", validate_imports),
        ("State Schema", validate_state_schema),
        ("Node Functions", validate_node_functions),
        ("Conditional Edges", validate_conditional_edges),
        ("Graph Structure", validate_graph_structure),
        ("Tool Mappings", validate_tool_mappings),
        ("Configuration", validate_configuration),
    ]
    
    results = []
    for name, validator in validations:
        try:
            result = validator()
            results.append((name, result))
        except Exception as e:
            print(f"   {name}: Validation failed with error: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print(" Validation Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = " PASS" if result else " FAIL"
        print(f"{name:20} {status}")
    
    print(f"\nOverall: {passed}/{total} validations passed")
    
    if passed == total:
        print(" All validations passed! Your LangGraph implementation looks good.")
        return True
    else:
        print("  Some validations failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1) 