"""
LangSmith integration for comprehensive agent monitoring and tracing.

enabling detailed observation of agent behavior, performance m
This module provides LangSmith tracing capabilities for the Notion Agent,onitoring,
and debugging capabilities.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import contextmanager

try:
    from langsmith import Client, RunTree, traceable
    from langsmith.run_helpers import trace
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    logging.warning("LangSmith not available. Install with: pip install langsmith")

from ..config import get_settings

logger = logging.getLogger(__name__)

class LangSmithTracer:
    """LangSmith tracer for comprehensive agent monitoring."""
    
    def __init__(self):
        """Initialize LangSmith tracer with configuration."""
        self.settings = get_settings()
        self.client = None
        self.project_name = self.settings.LANGSMITH_PROJECT or "notion-agent"
        self.enabled = False
        
        if LANGSMITH_AVAILABLE and self.settings.LANGSMITH_API_KEY:
            try:
                self.client = Client(api_key=self.settings.LANGSMITH_API_KEY)
                self.enabled = True
                logger.info(f"LangSmith tracing enabled for project: {self.project_name}")
            except Exception as e:
                logger.error(f"Failed to initialize LangSmith client: {e}")
                self.enabled = False
        else:
            logger.warning("LangSmith not configured. Set LANGSMITH_API_KEY to enable tracing.")
    
    @contextmanager
    def trace_agent_run(self, goal: str, user_input: str = None):
        """Trace a complete agent run with LangSmith."""
        if not self.enabled:
            yield None
            return
            
        run_tree = None
        try:
            run_tree = RunTree(
                name=f"agent_run_{goal}",
                run_type="chain",
                inputs={
                    "goal": goal,
                    "user_input": user_input,
                    "timestamp": datetime.now().isoformat()
                },
                project_name=self.project_name
            )
            
            logger.info(f"Starting LangSmith trace for goal: {goal}")
            yield run_tree
            
        except Exception as e:
            logger.error(f"Error in LangSmith tracing: {e}")
            if run_tree:
                run_tree.end(error=str(e))
            yield None
        finally:
            if run_tree:
                run_tree.end()
                logger.info(f"Completed LangSmith trace for goal: {goal}")
    
    @contextmanager
    def trace_tool_call(self, tool_name: str, parameters: Dict[str, Any], parent_run: RunTree = None):
        """Trace individual tool calls."""
        if not self.enabled:
            yield None
            return
            
        tool_run = None
        start_time = time.time()
        
        try:
            tool_run = RunTree(
                name=f"tool_{tool_name}",
                run_type="tool",
                inputs=parameters,
                parent_run=parent_run,
                project_name=self.project_name
            )
            
            logger.debug(f"Tracing tool call: {tool_name}")
            yield tool_run
            
        except Exception as e:
            logger.error(f"Error in tool tracing: {e}")
            if tool_run:
                tool_run.end(error=str(e))
            yield None
        finally:
            if tool_run:
                duration = time.time() - start_time
                tool_run.end(outputs={"duration": duration})
                logger.debug(f"Completed tool trace: {tool_name} ({duration:.2f}s)")
    
    @contextmanager
    def trace_llm_call(self, model: str, prompt: str, parent_run: RunTree = None):
        """Trace LLM calls for performance monitoring."""
        if not self.enabled:
            yield None
            return
            
        llm_run = None
        start_time = time.time()
        
        try:
            llm_run = RunTree(
                name=f"llm_{model}",
                run_type="llm",
                inputs={"prompt": prompt},
                parent_run=parent_run,
                project_name=self.project_name
            )
            
            logger.debug(f"Tracing LLM call: {model}")
            yield llm_run
            
        except Exception as e:
            logger.error(f"Error in LLM tracing: {e}")
            if llm_run:
                llm_run.end(error=str(e))
            yield None
        finally:
            if llm_run:
                duration = time.time() - start_time
                llm_run.end(outputs={"duration": duration})
                logger.debug(f"Completed LLM trace: {model} ({duration:.2f}s)")
    
    def trace_decision(self, reasoning: str, action: str, confidence: float, parent_run: RunTree = None):
        """Trace agent decision-making process."""
        if not self.enabled:
            return
            
        try:
            decision_run = RunTree(
                name="agent_decision",
                run_type="chain",
                inputs={
                    "reasoning": reasoning,
                    "action": action,
                    "confidence": confidence
                },
                parent_run=parent_run,
                project_name=self.project_name
            )
            
            decision_run.end(outputs={"decision": action})
            logger.debug(f"Traced decision: {action} (confidence: {confidence})")
            
        except Exception as e:
            logger.error(f"Error tracing decision: {e}")
    
    def trace_error(self, error: Exception, context: Dict[str, Any], parent_run: RunTree = None):
        """Trace errors for debugging and monitoring."""
        if not self.enabled:
            return
            
        try:
            error_run = RunTree(
                name="agent_error",
                run_type="chain",
                inputs=context,
                parent_run=parent_run,
                project_name=self.project_name
            )
            
            error_run.end(error=str(error))
            logger.debug(f"Traced error: {type(error).__name__}")
            
        except Exception as e:
            logger.error(f"Error tracing error: {e}")
    
    def get_run_url(self, run_id: str) -> Optional[str]:
        """Get the URL for viewing a specific run in LangSmith."""
        if not self.enabled or not self.client:
            return None
            
        try:
            base_url = "https://smith.langchain.com"
            return f"{base_url}/runs/{run_id}"
        except Exception as e:
            logger.error(f"Error generating run URL: {e}")
            return None
    
    def get_project_stats(self) -> Dict[str, Any]:
        """Get statistics for the current project."""
        if not self.enabled or not self.client:
            return {}
            
        try:
            # This would require additional LangSmith API calls
            # For now, return basic project info
            return {
                "project_name": self.project_name,
                "tracing_enabled": self.enabled,
                "client_configured": self.client is not None
            }
        except Exception as e:
            logger.error(f"Error getting project stats: {e}")
            return {}

# Global tracer instance
tracer = LangSmithTracer()

def get_tracer() -> LangSmithTracer:
    """Get the global LangSmith tracer instance."""
    return tracer 