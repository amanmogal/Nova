#!/usr/bin/env python3
"""
Debug script that mimics the exact agent execution flow.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import get_settings
from src.prompts.system_prompt import SYSTEM_PROMPT
import google.generativeai as genai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent_reasoning_node():
    """Test the exact reasoning node logic from the agent."""
    
    # Initialize settings and model
    settings = get_settings()
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel(settings.gemini_model)
    
    print(f"Testing with model: {settings.gemini_model}")
    
    # Simulate the exact state that the agent uses
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
    
    # Test 1: First reasoning call (no message history)
    print("\n=== Test 1: First Reasoning Call ===")
    try:
        # Build the exact message format used by the agent
        system_prompt = SYSTEM_PROMPT
        
        # Build context string exactly like the agent does
        context_parts = []
        context_parts.append(f"Current time: {state['context']['current_time']}")
        context_parts.append(f"Work hours: {state['context']['work_hours']}")
        
        # Add tasks context
        if state.get("search_results", {}).get("success"):
            tasks = state["search_results"]["tasks"]
            context_parts.append(f"Available tasks: {len(tasks)}")
            context_parts.append("Task details:")
            for i, task in enumerate(tasks[:3], 1):
                metadata = task.get("metadata", {})
                title = metadata.get("title", "Unknown")
                status = metadata.get("status", "Unknown")
                context_parts.append(f"   {i}. {title} - {status}")
        
        # Add routines context
        if state.get("routine_results", {}).get("success"):
            routines = state["routine_results"]["routines"]
            context_parts.append(f"Available routines: {len(routines)}")
            context_parts.append("Routine details:")
            for i, routine in enumerate(routines[:3], 1):
                metadata = routine.get("metadata", {})
                title = metadata.get("title", "Unknown")
                category = metadata.get("category", "Unknown")
                context_parts.append(f"   {i}. {title} - {category}")
        
        context_str = "\n".join(context_parts)
        
        # Build the exact user message
        user_message = f"{system_prompt}\n\n{context_str}"
        
        messages = [{
            "role": "user",
            "parts": [user_message]
        }]
        
        print(f"Message length: {len(user_message)}")
        print(f"Context parts: {len(context_parts)}")
        
        response = model.generate_content(messages)
        print(f"Response candidates: {len(response.candidates)}")
        
        if response.candidates:
            response_text = response.candidates[0].content.parts[0].text
            print(f" First reasoning call successful")
            print(f"Response preview: {response_text[:200]}...")
            
            # Try to parse JSON
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    parsed = json.loads(json_str)
                    print(f" JSON parsed successfully")
                    print(f"Action tool: {parsed.get('action', {}).get('tool', 'unknown')}")
                    
                    # Store for next test
                    first_response = response_text
                else:
                    print(" No JSON found in response")
                    return
            except json.JSONDecodeError as e:
                print(f" JSON parsing failed: {e}")
                return
        else:
            print(f" First reasoning call failed. Prompt feedback: {response.prompt_feedback}")
            return
            
    except Exception as e:
        print(f"Error in Test 1: {e}")
        return
    
    # Test 2: Second reasoning call (with message history)
    print("\n=== Test 2: Second Reasoning Call (With History) ===")
    try:
        # Add the previous assistant message to history (exactly like the agent does)
        messages.append({
            "role": "model",
            "parts": [first_response]
        })
        
        # Update state for second call
        state["search_results"]["tasks"] = state["search_results"]["tasks"][:1]  # Reduce tasks
        
        # Build updated context
        context_parts = []
        context_parts.append(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        context_parts.append(f"Work hours: {state['context']['work_hours']}")
        
        # Add updated tasks context
        if state.get("search_results", {}).get("success"):
            tasks = state["search_results"]["tasks"]
            context_parts.append(f"Available tasks: {len(tasks)}")
            context_parts.append("Task details:")
            for i, task in enumerate(tasks[:3], 1):
                metadata = task.get("metadata", {})
                title = metadata.get("title", "Unknown")
                status = metadata.get("status", "Unknown")
                context_parts.append(f"   {i}. {title} - {status}")
        
        context_str = "\n".join(context_parts)
        
        # Build the exact user message
        user_message = f"{system_prompt}\n\n{context_str}"
        
        messages.append({
            "role": "user",
            "parts": [user_message]
        })
        
        print(f"Message count: {len(messages)}")
        print(f"Message roles: {[msg['role'] for msg in messages]}")
        print(f"Last message length: {len(user_message)}")
        
        response = model.generate_content(messages)
        print(f"Response candidates: {len(response.candidates)}")
        
        if response.candidates:
            response_text = response.candidates[0].content.parts[0].text
            print(f" Second reasoning call successful")
            print(f"Response preview: {response_text[:200]}...")
            
            # Try to parse JSON
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    parsed = json.loads(json_str)
                    print(f" JSON parsed successfully")
                    print(f"Action tool: {parsed.get('action', {}).get('tool', 'unknown')}")
                else:
                    print(" No JSON found in response")
            except json.JSONDecodeError as e:
                print(f" JSON parsing failed: {e}")
        else:
            print(f" Second reasoning call failed. Prompt feedback: {response.prompt_feedback}")
            
    except Exception as e:
        print(f"Error in Test 2: {e}")
    
    # Test 3: Check for rate limiting or token limits
    print("\n=== Test 3: Rate Limiting Test ===")
    try:
        # Make multiple rapid calls to test rate limiting
        for i in range(5):
            print(f"\n--- Rapid Call {i+1} ---")
            simple_messages = [{
                "role": "user",
                "parts": [f"Respond with JSON: {{\"test\": {i+1}, \"status\": \"rapid_call\"}}"]
            }]
            
            response = model.generate_content(simple_messages)
            print(f"Response candidates: {len(response.candidates)}")
            if response.candidates:
                print(f" Rapid call {i+1} successful")
            else:
                print(f" Rapid call {i+1} failed. Prompt feedback: {response.prompt_feedback}")
                
    except Exception as e:
        print(f"Error in Test 3: {e}")

if __name__ == "__main__":
    test_agent_reasoning_node() 