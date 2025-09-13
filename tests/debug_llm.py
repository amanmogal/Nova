#!/usr/bin/env python3
"""
Debug script to test LLM responses and identify inconsistency issues.
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

def test_llm_response():
    """Test LLM response generation with different contexts."""
    
    # Initialize settings and model
    settings = get_settings()
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel(settings.gemini_model)
    
    print(f"Testing with model: {settings.gemini_model}")
    
    # Test 1: Simple prompt
    print("\n=== Test 1: Simple Prompt ===")
    try:
        messages = [{
            "role": "user",
            "parts": ["Hello, can you respond with a simple JSON object containing a greeting?"]
        }]
        
        response = model.generate_content(messages)
        print(f"Response candidates: {len(response.candidates)}")
        if response.candidates:
            print(f"Response text: {response.candidates[0].content.parts[0].text}")
        else:
            print(f"No candidates. Prompt feedback: {response.prompt_feedback}")
    except Exception as e:
        print(f"Error in Test 1: {e}")
    
    # Test 2: System prompt + context (similar to agent)
    print("\n=== Test 2: System Prompt + Context ===")
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
        
        response = model.generate_content(messages)
        print(f"Response candidates: {len(response.candidates)}")
        if response.candidates:
            response_text = response.candidates[0].content.parts[0].text
            print(f"Response text: {response_text[:200]}...")
            
            # Try to parse JSON
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    parsed = json.loads(json_str)
                    print(f" JSON parsed successfully: {parsed.get('action', {}).get('tool', 'unknown')}")
                else:
                    print(" No JSON found in response")
            except json.JSONDecodeError as e:
                print(f" JSON parsing failed: {e}")
        else:
            print(f"No candidates. Prompt feedback: {response.prompt_feedback}")
    except Exception as e:
        print(f"Error in Test 2: {e}")
    
    # Test 3: Multiple consecutive calls (to test rate limiting)
    print("\n=== Test 3: Multiple Consecutive Calls ===")
    try:
        for i in range(3):
            print(f"\n--- Call {i+1} ---")
            messages = [{
                "role": "user",
                "parts": [f"Respond with a simple JSON: {{\"test\": {i+1}, \"message\": \"call {i+1}\"}}"]
            }]
            
            response = model.generate_content(messages)
            print(f"Response candidates: {len(response.candidates)}")
            if response.candidates:
                print(f"Response: {response.candidates[0].content.parts[0].text}")
            else:
                print(f"No candidates. Prompt feedback: {response.prompt_feedback}")
    except Exception as e:
        print(f"Error in Test 3: {e}")
    
    # Test 4: Check model configuration
    print("\n=== Test 4: Model Configuration ===")
    try:
        print(f"Model name: {model.model_name}")
        print(f"Generation config: {model.generation_config}")
        
        # Test with generation config
        model_with_config = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
            )
        )
        
        messages = [{
            "role": "user",
            "parts": ["Respond with JSON: {\"status\": \"test\"}"]
        }]
        
        response = model_with_config.generate_content(messages)
        print(f"With config - candidates: {len(response.candidates)}")
        if response.candidates:
            print(f"Response: {response.candidates[0].content.parts[0].text}")
        else:
            print(f"No candidates. Prompt feedback: {response.prompt_feedback}")
    except Exception as e:
        print(f"Error in Test 4: {e}")

if __name__ == "__main__":
    test_llm_response() 