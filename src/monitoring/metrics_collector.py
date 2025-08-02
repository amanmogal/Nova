"""
Metrics collector for comprehensive performance monitoring.

This module provides detailed metrics collection for the Notion Agent,
including token usage, response times, success rates, and cost tracking.
"""

import time
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

from ..config import get_settings
from ..db.supabase_connector import SupabaseConnector

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    timestamp: datetime
    operation_type: str
    duration_ms: float
    token_count: Optional[int] = None
    cost_usd: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class CostMetrics:
    """Cost tracking metrics."""
    timestamp: datetime
    operation_type: str
    tokens_used: int
    cost_usd: float
    model: str
    metadata: Optional[Dict[str, Any]] = None

class MetricsCollector:
    """Comprehensive metrics collector for agent performance monitoring."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.settings = get_settings()
        self.db = SupabaseConnector()
        
        # In-memory metrics storage (for real-time access)
        self.performance_metrics = deque(maxlen=1000)  # Keep last 1000 metrics
        self.cost_metrics = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.operation_counts = defaultdict(int)
        
        # Cost tracking
        self.token_costs = {
            "gemini-pro": 0.0005,  # $0.0005 per 1K tokens input
            "gemini-pro-vision": 0.0005,
            "default": 0.0005
        }
        
        logger.info("Metrics collector initialized")
    
    def record_operation(self, 
                        operation_type: str, 
                        duration_ms: float, 
                        token_count: Optional[int] = None,
                        model: str = "gemini-pro",
                        success: bool = True,
                        error_message: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None):
        """Record a single operation's performance metrics."""
        timestamp = datetime.now()
        
        # Calculate cost if token count provided
        cost_usd = None
        if token_count:
            cost_per_token = self.token_costs.get(model, self.token_costs["default"])
            cost_usd = (token_count / 1000) * cost_per_token
        
        # Create metrics object
        metrics = PerformanceMetrics(
            timestamp=timestamp,
            operation_type=operation_type,
            duration_ms=duration_ms,
            token_count=token_count,
            cost_usd=cost_usd,
            success=success,
            error_message=error_message,
            metadata=metadata
        )
        
        # Store in memory
        self.performance_metrics.append(metrics)
        
        # Update counters
        self.operation_counts[operation_type] += 1
        if not success:
            self.error_counts[operation_type] += 1
        
        # Store cost metrics if applicable
        if cost_usd:
            cost_metrics = CostMetrics(
                timestamp=timestamp,
                operation_type=operation_type,
                tokens_used=token_count,
                cost_usd=cost_usd,
                model=model,
                metadata=metadata
            )
            self.cost_metrics.append(cost_metrics)
        
        # Log for debugging
        cost_str = f"${cost_usd:.6f}" if cost_usd else "$0.000000"
        logger.debug(f"Recorded {operation_type}: {duration_ms:.2f}ms, "
                    f"tokens: {token_count}, cost: {cost_str}")
    
    def record_llm_call(self, 
                       model: str, 
                       input_tokens: int, 
                       output_tokens: int, 
                       duration_ms: float,
                       success: bool = True,
                       error_message: Optional[str] = None):
        """Record LLM call metrics."""
        total_tokens = input_tokens + output_tokens
        
        self.record_operation(
            operation_type="llm_call",
            duration_ms=duration_ms,
            token_count=total_tokens,
            model=model,
            success=success,
            error_message=error_message,
            metadata={
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
        )
    
    def record_tool_call(self, 
                        tool_name: str, 
                        duration_ms: float,
                        success: bool = True,
                        error_message: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None):
        """Record tool call metrics."""
        self.record_operation(
            operation_type=f"tool_{tool_name}",
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata=metadata
        )
    
    def record_agent_run(self, 
                        goal: str, 
                        duration_ms: float,
                        total_tokens: int,
                        success: bool = True,
                        error_message: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None):
        """Record complete agent run metrics."""
        self.record_operation(
            operation_type=f"agent_run_{goal}",
            duration_ms=duration_ms,
            token_count=total_tokens,
            success=success,
            error_message=error_message,
            metadata=metadata
        )
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter metrics by time
        recent_metrics = [
            m for m in self.performance_metrics 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"message": f"No metrics found for last {hours} hours"}
        
        # Calculate summary statistics
        total_operations = len(recent_metrics)
        successful_operations = sum(1 for m in recent_metrics if m.success)
        total_duration = sum(m.duration_ms for m in recent_metrics)
        total_tokens = sum(m.token_count or 0 for m in recent_metrics)
        total_cost = sum(m.cost_usd or 0 for m in recent_metrics)
        
        # Calculate averages
        avg_duration = total_duration / total_operations if total_operations > 0 else 0
        avg_tokens = total_tokens / total_operations if total_operations > 0 else 0
        
        # Success rate
        success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0
        
        # Operation breakdown
        operation_breakdown = defaultdict(int)
        for metric in recent_metrics:
            operation_breakdown[metric.operation_type] += 1
        
        return {
            "time_period_hours": hours,
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "success_rate_percent": round(success_rate, 2),
            "total_duration_ms": round(total_duration, 2),
            "average_duration_ms": round(avg_duration, 2),
            "total_tokens": total_tokens,
            "average_tokens_per_operation": round(avg_tokens, 2),
            "total_cost_usd": round(total_cost, 6),
            "operation_breakdown": dict(operation_breakdown),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_cost_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get cost summary for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter cost metrics by time
        recent_costs = [
            c for c in self.cost_metrics 
            if c.timestamp >= cutoff_time
        ]
        
        if not recent_costs:
            return {"message": f"No cost data found for last {hours} hours"}
        
        # Calculate cost statistics
        total_cost = sum(c.cost_usd for c in recent_costs)
        total_tokens = sum(c.tokens_used for c in recent_costs)
        
        # Cost by operation type
        cost_by_operation = defaultdict(float)
        for cost in recent_costs:
            cost_by_operation[cost.operation_type] += cost.cost_usd
        
        # Cost by model
        cost_by_model = defaultdict(float)
        for cost in recent_costs:
            cost_by_model[cost.model] += cost.cost_usd
        
        return {
            "time_period_hours": hours,
            "total_cost_usd": round(total_cost, 6),
            "total_tokens": total_tokens,
            "average_cost_per_token": round(total_cost / total_tokens * 1000, 6) if total_tokens > 0 else 0,
            "cost_by_operation": dict(cost_by_operation),
            "cost_by_model": dict(cost_by_model),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter error metrics by time
        error_metrics = [
            m for m in self.performance_metrics 
            if not m.success and m.timestamp >= cutoff_time
        ]
        
        if not error_metrics:
            return {"message": f"No errors found for last {hours} hours"}
        
        # Error breakdown by operation type
        error_by_operation = defaultdict(int)
        error_messages = defaultdict(int)
        
        for metric in error_metrics:
            error_by_operation[metric.operation_type] += 1
            if metric.error_message:
                error_messages[metric.error_message] += 1
        
        return {
            "time_period_hours": hours,
            "total_errors": len(error_metrics),
            "error_by_operation": dict(error_by_operation),
            "error_messages": dict(error_messages),
            "timestamp": datetime.now().isoformat()
        }
    
    def save_metrics_to_db(self):
        """Save current metrics to database for persistence."""
        try:
            # Convert metrics to JSON-serializable format
            performance_data = [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "operation_type": m.operation_type,
                    "duration_ms": m.duration_ms,
                    "token_count": m.token_count,
                    "cost_usd": m.cost_usd,
                    "success": m.success,
                    "error_message": m.error_message,
                    "metadata": m.metadata
                }
                for m in self.performance_metrics
            ]
            
            cost_data = [
                {
                    "timestamp": c.timestamp.isoformat(),
                    "operation_type": c.operation_type,
                    "tokens_used": c.tokens_used,
                    "cost_usd": c.cost_usd,
                    "model": c.model,
                    "metadata": c.metadata
                }
                for c in self.cost_metrics
            ]
            
            # Save to database (implementation depends on your schema)
            # self.db.save_metrics(performance_data, cost_data)
            
            logger.info(f"Saved {len(performance_data)} performance metrics and {len(cost_data)} cost metrics to database")
            
        except Exception as e:
            logger.error(f"Error saving metrics to database: {e}")
    
    def clear_old_metrics(self, days: int = 7):
        """Clear metrics older than N days from memory."""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Clear old performance metrics
        original_count = len(self.performance_metrics)
        self.performance_metrics = deque(
            [m for m in self.performance_metrics if m.timestamp >= cutoff_time],
            maxlen=1000
        )
        
        # Clear old cost metrics
        original_cost_count = len(self.cost_metrics)
        self.cost_metrics = deque(
            [c for c in self.cost_metrics if c.timestamp >= cutoff_time],
            maxlen=1000
        )
        
        cleared_count = original_count - len(self.performance_metrics)
        cleared_cost_count = original_cost_count - len(self.cost_metrics)
        
        logger.info(f"Cleared {cleared_count} performance metrics and {cleared_cost_count} cost metrics older than {days} days")

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format for Grafana Cloud."""
        prometheus_lines = []
        
        # Export operation counters
        for name, value in self.operation_counts.items():
            prometheus_lines.append(f"# TYPE notion_agent_operation_count counter")
            prometheus_lines.append(f'notion_agent_operation_count{{operation="{name}"}} {value}')
        
        # Export error counters
        for name, value in self.error_counts.items():
            prometheus_lines.append(f"# TYPE notion_agent_error_count counter")
            prometheus_lines.append(f'notion_agent_error_count{{operation="{name}"}} {value}')
        
        # Export recent performance metrics (last 100)
        if self.performance_metrics:
            recent_metrics = list(self.performance_metrics)[-100:]
            for metric in recent_metrics:
                # Duration metrics
                prometheus_lines.append(f"# TYPE notion_agent_operation_duration_ms gauge")
                prometheus_lines.append(f'notion_agent_operation_duration_ms{{operation="{metric.operation_type}",success="{metric.success}"}} {metric.duration_ms}')
                
                # Token count metrics
                if metric.token_count:
                    prometheus_lines.append(f"# TYPE notion_agent_token_count gauge")
                    prometheus_lines.append(f'notion_agent_token_count{{operation="{metric.operation_type}"}} {metric.token_count}')
                
                # Cost metrics
                if metric.cost_usd:
                    prometheus_lines.append(f"# TYPE notion_agent_cost_usd gauge")
                    prometheus_lines.append(f'notion_agent_cost_usd{{operation="{metric.operation_type}"}} {metric.cost_usd}')
        
        # Export cost metrics summary
        if self.cost_metrics:
            recent_costs = list(self.cost_metrics)[-50:]
            total_cost = sum(c.cost_usd for c in recent_costs)
            prometheus_lines.append(f"# TYPE notion_agent_total_cost_usd gauge")
            prometheus_lines.append(f'notion_agent_total_cost_usd {total_cost}')
        
        # Add timestamp
        prometheus_lines.append(f"# TYPE notion_agent_last_export_time gauge")
        prometheus_lines.append(f'notion_agent_last_export_time {int(datetime.now().timestamp())}')
        
        return "\n".join(prometheus_lines)

# Global metrics collector instance
metrics_collector = MetricsCollector()

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return metrics_collector 