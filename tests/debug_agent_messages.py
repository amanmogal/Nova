#!/usr/bin/env python3
"""
Debug script to test the exact message format that the agent uses.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import get_settings
import google.generativeai as genai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent_message_format():
    """Test the exact message format that the agent uses."""
    
    # Initialize settings and model
    settings = get_settings()
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel(settings.gemini_model)
    
    print(f"Testing with model: {settings.gemini_model}")
    
    # Test 1: First call (no message history)
    print("\n=== Test 1: First Call (No History) ===")
    try:
        system_prompt = """
You are an autonomous AI agent that helps manage and schedule tasks in Notion.
Your goal is to intelligently prioritize and schedule tasks based on their urgency,
importance, dependencies, and user preferences.

## IMPORTANT: You must respond with structured JSON
You must always respond with a JSON object in this exact format:

```json
{
  "reasoning": "Your reasoning about what needs to be done",
  "action": {
    "tool": "tool_name",
    "parameters": {
      "param1": "value1",
      "param2": "value2"
    }
  },
  "confidence": 0.95
}
```

## Available Tools:
- `search_tasks`: Search for tasks with query parameter
- `update_task`: Update task properties with task_id and properties parameters
- `create_task`: Create new task with title, status, priority, due_date parameters
- `send_notification`: Send notification with message and priority parameters
- `get_routines`: Get user routines (no parameters needed)
- `end`: End the current session (no parameters needed)

Now, analyze the current context and determine the best course of action.
"""
        
        context_str = f"""
Current time: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Available tasks: 3
Task details:
  1. Todo 24/6 - In Progress
     Content: High priority task that needs attention...
  2. implementation day 1 - In Progress
     Content: Development task for phase 1...
  3. 4/6 day todo zaps - In Progress
     Content: Automation task for daily workflows...

Available routines: 2
Routine details:
  1. Morning Planning Session - Planning
     Content: Daily morning routine for planning...
  2. Email Processing - Communication
     Content: Friday email processing routine...

Work hours: 10:00 to 02:00

Previous actions completed successfully.
"""
        
        user_message = f"{system_prompt}\n\n{context_str}"
        
        messages = [{
            "role": "user",
            "parts": [user_message]
        }]
        
        print(f"Message count: {len(messages)}")
        print(f"First message role: {messages[0]['role']}")
        print(f"First message parts count: {len(messages[0]['parts'])}")
        print(f"First message content length: {len(messages[0]['parts'][0])}")
        
        response = model.generate_content(messages)
        print(f"Response candidates: {len(response.candidates)}")
        if response.candidates:
            response_text = response.candidates[0].content.parts[0].text
            print(f"✅ First call successful: {response_text[:100]}...")
            
            # Store the response for next test
            first_response = response_text
        else:
            print(f"❌ First call failed. Prompt feedback: {response.prompt_feedback}")
            return
    except Exception as e:
        print(f"Error in Test 1: {e}")
        return
    
    # Test 2: Second call (with message history)
    print("\n=== Test 2: Second Call (With History) ===")
    try:
        # Add the previous assistant message to history
        messages.append({
            "role": "model",
            "parts": [first_response]
        })
        
        # Add a new user message
        new_context = f"""
Current time: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Available tasks: 2
Task details:
  1. Todo 24/6 - In Progress
     Content: High priority task that needs attention...
  2. implementation day 1 - In Progress
     Content: Development task for phase 1...

Available routines: 1
Routine details:
  1. Morning Planning Session - Planning
     Content: Daily morning routine for planning...

Work hours: 10:00 to 02:00

Previous actions completed successfully.
"""
        
        new_user_message = f"{system_prompt}\n\n{new_context}"
        messages.append({
            "role": "user",
            "parts": [new_user_message]
        })
        
        print(f"Message count: {len(messages)}")
        print(f"Message roles: {[msg['role'] for msg in messages]}")
        print(f"Last message content length: {len(messages[-1]['parts'][0])}")
        
        response = model.generate_content(messages)
        print(f"Response candidates: {len(response.candidates)}")
        if response.candidates:
            response_text = response.candidates[0].content.parts[0].text
            print(f"✅ Second call successful: {response_text[:100]}...")
        else:
            print(f"❌ Second call failed. Prompt feedback: {response.prompt_feedback}")
    except Exception as e:
        print(f"Error in Test 2: {e}")
    
    # Test 3: Check message format issues
    print("\n=== Test 3: Message Format Analysis ===")
    try:
        # Test with different message formats
        test_messages = [
            {
                "role": "user",
                "parts": ["Hello"]
            },
            {
                "role": "model", 
                "parts": ["Hi there!"]
            },
            {
                "role": "user",
                "parts": ["How are you?"]
            }
        ]
        
        response = model.generate_content(test_messages)
        print(f"Simple conversation - candidates: {len(response.candidates)}")
        if response.candidates:
            print(f"✅ Simple conversation works: {response.candidates[0].content.parts[0].text}")
        else:
            print(f"❌ Simple conversation failed. Prompt feedback: {response.prompt_feedback}")
    except Exception as e:
        print(f"Error in Test 3: {e}")
    
    # Test 4: Check for content filtering
    print("\n=== Test 4: Content Filtering Test ===")
    try:
        # Test with potentially problematic content
        problematic_messages = [{
            "role": "user",
            "parts": [f"""
You are an AI agent. The current time is {datetime.now().strftime('%Y-%m-%d %H:%M')}.

Available tasks: 3
Task details:
  1. Todo 24/6 - In Progress (High Priority)
  2. implementation day 1 - In Progress
  3. 4/6 day todo zaps - In Progress

Available routines: 2
Routine details:
  1. Morning Planning Session - Planning
  2. Email Processing - Communication

Work hours: 10:00 to 02:00

Previous actions completed successfully.

Respond with JSON: {{"reasoning": "test", "action": {{"tool": "search_tasks", "parameters": {{"query": "test"}}}}, "confidence": 0.9}}
"""]
        }]
        
        response = model.generate_content(problematic_messages)
        print(f"Problematic content - candidates: {len(response.candidates)}")
        if response.candidates:
            print(f"✅ Problematic content works: {response.candidates[0].content.parts[0].text[:100]}...")
        else:
            print(f"❌ Problematic content failed. Prompt feedback: {response.prompt_feedback}")
    except Exception as e:
        print(f"Error in Test 4: {e}")

if __name__ == "__main__":
    test_agent_message_format() 