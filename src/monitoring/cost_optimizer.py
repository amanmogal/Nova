"""
Cost optimizer for managing and optimizing API costs.

This module provides cost optimization strategies and monitoring
for the Notion Agent to minimize API expenses while maintaining performance.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

from .metrics_collector import get_metrics_collector, MetricsCollector

logger = logging.getLogger(__name__)

@dataclass
class CostOptimizationStrategy:
    """Cost optimization strategy configuration."""
    name: str
    description: str
    enabled: bool
    threshold: float
    action: str
    parameters: Dict[str, Any]

@dataclass
class CostAlert:
    """Cost alert data structure."""
    timestamp: datetime
    alert_type: str
    severity: str
    message: str
    cost_threshold: float
    current_cost: float
    recommendations: List[str]

class CostOptimizer:
    """Cost optimization system for the Notion Agent."""
    
    def __init__(self):
        """Initialize cost optimizer."""
        self.metrics_collector = get_metrics_collector()
        
        # Cost thresholds and limits
        self.daily_cost_limit = 1.00  # $1.00 per day
        self.monthly_cost_limit = 25.00  # $25.00 per month
        self.operation_cost_threshold = 0.01  # $0.01 per operation
        
        # Cost tracking
        self.daily_costs = defaultdict(float)
        self.monthly_costs = defaultdict(float)
        self.operation_costs = deque(maxlen=1000)
        
        # Optimization strategies
        self.optimization_strategies = self._initialize_strategies()
        
        # Alerts
        self.cost_alerts = deque(maxlen=100)
        
        logger.info("Cost optimizer initialized")
    
    def _initialize_strategies(self) -> Dict[str, CostOptimizationStrategy]:
        """Initialize cost optimization strategies."""
        return {
            "token_limit": CostOptimizationStrategy(
                name="token_limit",
                description="Limit token usage per operation",
                enabled=True,
                threshold=1000,
                action="limit_tokens",
                parameters={"max_tokens": 1000}
            ),
            "operation_frequency": CostOptimizationStrategy(
                name="operation_frequency",
                description="Limit operation frequency",
                enabled=True,
                threshold=100,
                action="rate_limit",
                parameters={"max_operations_per_hour": 100}
            ),
            "model_selection": CostOptimizationStrategy(
                name="model_selection",
                description="Use cost-effective models",
                enabled=True,
                threshold=0.0005,
                action="switch_model",
                parameters={"preferred_model": "gemini-pro"}
            ),
            "caching": CostOptimizationStrategy(
                name="caching",
                description="Enable response caching",
                enabled=True,
                threshold=0.001,
                action="enable_caching",
                parameters={"cache_duration": 3600}
            )
        }
    
    def track_operation_cost(self, 
                           operation_type: str,
                           cost_usd: float,
                           tokens_used: int,
                           model: str = "gemini-pro",
                           metadata: Optional[Dict[str, Any]] = None):
        """Track the cost of a single operation."""
        timestamp = datetime.now()
        
        # Store operation cost
        operation_cost = {
            "timestamp": timestamp,
            "operation_type": operation_type,
            "cost_usd": cost_usd,
            "tokens_used": tokens_used,
            "model": model,
            "metadata": metadata
        }
        self.operation_costs.append(operation_cost)
        
        # Update daily and monthly costs
        date_key = timestamp.strftime("%Y-%m-%d")
        month_key = timestamp.strftime("%Y-%m")
        
        self.daily_costs[date_key] += cost_usd
        self.monthly_costs[month_key] += cost_usd
        
        # Check for cost alerts
        self._check_cost_alerts(date_key, month_key, cost_usd)
        
        logger.debug(f"Tracked operation cost: {operation_type} = ${cost_usd:.6f}")
    
    def _check_cost_alerts(self, date_key: str, month_key: str, operation_cost: float):
        """Check for cost threshold violations and generate alerts."""
        daily_cost = self.daily_costs[date_key]
        monthly_cost = self.monthly_costs[month_key]
        
        # Daily cost alert
        if daily_cost > self.daily_cost_limit:
            alert = CostAlert(
                timestamp=datetime.now(),
                alert_type="daily_limit_exceeded",
                severity="high",
                message=f"Daily cost limit exceeded: ${daily_cost:.4f}",
                cost_threshold=self.daily_cost_limit,
                current_cost=daily_cost,
                recommendations=self._generate_cost_recommendations(daily_cost, "daily")
            )
            self.cost_alerts.append(alert)
            logger.warning(f"Daily cost limit exceeded: ${daily_cost:.4f}")
        
        # Monthly cost alert
        if monthly_cost > self.monthly_cost_limit:
            alert = CostAlert(
                timestamp=datetime.now(),
                alert_type="monthly_limit_exceeded",
                severity="high",
                message=f"Monthly cost limit exceeded: ${monthly_cost:.4f}",
                cost_threshold=self.monthly_cost_limit,
                current_cost=monthly_cost,
                recommendations=self._generate_cost_recommendations(monthly_cost, "monthly")
            )
            self.cost_alerts.append(alert)
            logger.warning(f"Monthly cost limit exceeded: ${monthly_cost:.4f}")
        
        # Operation cost alert
        if operation_cost > self.operation_cost_threshold:
            alert = CostAlert(
                timestamp=datetime.now(),
                alert_type="operation_cost_high",
                severity="medium",
                message=f"High operation cost: ${operation_cost:.4f}",
                cost_threshold=self.operation_cost_threshold,
                current_cost=operation_cost,
                recommendations=self._generate_cost_recommendations(operation_cost, "operation")
            )
            self.cost_alerts.append(alert)
            logger.warning(f"High operation cost: ${operation_cost:.4f}")
    
    def _generate_cost_recommendations(self, cost: float, cost_type: str) -> List[str]:
        """Generate cost optimization recommendations."""
        recommendations = []
        
        if cost_type == "daily":
            if cost > self.daily_cost_limit * 1.5:
                recommendations.append("Implement aggressive token limiting")
                recommendations.append("Enable response caching for repeated queries")
                recommendations.append("Review and optimize prompt engineering")
            else:
                recommendations.append("Monitor usage patterns")
                recommendations.append("Consider implementing rate limiting")
        
        elif cost_type == "monthly":
            if cost > self.monthly_cost_limit * 1.2:
                recommendations.append("Review monthly usage patterns")
                recommendations.append("Implement cost allocation by user/feature")
                recommendations.append("Consider upgrading to enterprise pricing")
            else:
                recommendations.append("Set up monthly cost monitoring")
                recommendations.append("Implement cost alerts")
        
        elif cost_type == "operation":
            recommendations.append("Optimize prompt length and complexity")
            recommendations.append("Use more efficient models where possible")
            recommendations.append("Implement operation result caching")
        
        return recommendations
    
    def get_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive cost summary for the last N days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Filter costs by date range
        daily_costs_in_range = {
            date: cost for date, cost in self.daily_costs.items()
            if start_date <= datetime.strptime(date, "%Y-%m-%d") <= end_date
        }
        
        monthly_costs_in_range = {
            month: cost for month, cost in self.monthly_costs.items()
            if start_date <= datetime.strptime(month + "-01", "%Y-%m-%d") <= end_date
        }
        
        # Calculate statistics
        total_cost = sum(daily_costs_in_range.values())
        avg_daily_cost = total_cost / len(daily_costs_in_range) if daily_costs_in_range else 0
        max_daily_cost = max(daily_costs_in_range.values()) if daily_costs_in_range else 0
        
        # Operation cost analysis
        recent_operations = [
            op for op in self.operation_costs
            if start_date <= op["timestamp"] <= end_date
        ]
        
        operation_cost_breakdown = defaultdict(float)
        model_cost_breakdown = defaultdict(float)
        
        for op in recent_operations:
            operation_cost_breakdown[op["operation_type"]] += op["cost_usd"]
            model_cost_breakdown[op["model"]] += op["cost_usd"]
        
        return {
            "time_period_days": days,
            "total_cost": round(total_cost, 6),
            "average_daily_cost": round(avg_daily_cost, 6),
            "max_daily_cost": round(max_daily_cost, 6),
            "daily_cost_limit": self.daily_cost_limit,
            "monthly_cost_limit": self.monthly_cost_limit,
            "operation_cost_threshold": self.operation_cost_threshold,
            "daily_costs": dict(daily_costs_in_range),
            "monthly_costs": dict(monthly_costs_in_range),
            "operation_cost_breakdown": dict(operation_cost_breakdown),
            "model_cost_breakdown": dict(model_cost_breakdown),
            "total_operations": len(recent_operations),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_cost_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get cost alerts for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_alerts = [
            alert for alert in self.cost_alerts
            if alert.timestamp >= cutoff_time
        ]
        
        return [
            {
                "timestamp": alert.timestamp.isoformat(),
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "cost_threshold": alert.cost_threshold,
                "current_cost": alert.current_cost,
                "recommendations": alert.recommendations
            }
            for alert in recent_alerts
        ]
    
    def optimize_operation(self, 
                          operation_type: str,
                          estimated_tokens: int,
                          model: str = "gemini-pro") -> Dict[str, Any]:
        """Optimize an operation before execution."""
        optimization_result = {
            "optimized": False,
            "recommendations": [],
            "estimated_cost": 0.0,
            "optimization_applied": None
        }
        
        # Calculate estimated cost
        cost_per_token = 0.0005  # $0.0005 per 1K tokens
        estimated_cost = (estimated_tokens / 1000) * cost_per_token
        optimization_result["estimated_cost"] = estimated_cost
        
        # Apply optimization strategies
        for strategy_name, strategy in self.optimization_strategies.items():
            if not strategy.enabled:
                continue
            
            if strategy.name == "token_limit" and estimated_tokens > strategy.threshold:
                optimization_result["optimized"] = True
                optimization_result["optimization_applied"] = strategy_name
                optimization_result["recommendations"].append(
                    f"Reduce token usage from {estimated_tokens} to {strategy.threshold}"
                )
                # Recalculate cost with reduced tokens
                estimated_cost = (strategy.threshold / 1000) * cost_per_token
                optimization_result["estimated_cost"] = estimated_cost
            
            elif strategy.name == "model_selection" and estimated_cost > strategy.threshold:
                optimization_result["optimized"] = True
                optimization_result["optimization_applied"] = strategy_name
                optimization_result["recommendations"].append(
                    f"Consider using {strategy.parameters['preferred_model']} for cost efficiency"
                )
        
        # Check if operation should be rate limited
        recent_operations = [
            op for op in self.operation_costs
            if op["timestamp"] >= datetime.now() - timedelta(hours=1)
        ]
        
        if len(recent_operations) > 100:  # Rate limit threshold
            optimization_result["recommendations"].append(
                "Rate limit exceeded - consider delaying operation"
            )
        
        return optimization_result
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get general cost optimization recommendations."""
        recommendations = []
        
        # Analyze recent costs
        recent_costs = list(self.operation_costs)[-100:]  # Last 100 operations
        if not recent_costs:
            return recommendations
        
        avg_cost = sum(op["cost_usd"] for op in recent_costs) / len(recent_costs)
        total_tokens = sum(op["tokens_used"] for op in recent_costs)
        
        # Token usage recommendations
        if total_tokens > 50000:  # 50K tokens threshold
            recommendations.append({
                "category": "token_optimization",
                "priority": "high",
                "recommendation": "Implement token usage monitoring and limiting",
                "potential_savings": "20-30%"
            })
        
        # Model selection recommendations
        model_costs = defaultdict(float)
        for op in recent_costs:
            model_costs[op["model"]] += op["cost_usd"]
        
        if model_costs:
            most_expensive_model = max(model_costs, key=model_costs.get)
            if most_expensive_model != "gemini-pro":
                recommendations.append({
                    "category": "model_selection",
                    "priority": "medium",
                    "recommendation": f"Consider switching from {most_expensive_model} to gemini-pro",
                    "potential_savings": "10-20%"
                })
        
        # Caching recommendations
        operation_types = [op["operation_type"] for op in recent_costs]
        if len(set(operation_types)) < len(operation_types) * 0.8:  # 80% are repeated
            recommendations.append({
                "category": "caching",
                "priority": "high",
                "recommendation": "Implement response caching for repeated operations",
                "potential_savings": "30-50%"
            })
        
        return recommendations
    
    def set_cost_limits(self, daily_limit: float, monthly_limit: float):
        """Update cost limits."""
        self.daily_cost_limit = daily_limit
        self.monthly_cost_limit = monthly_limit
        logger.info(f"Updated cost limits: daily=${daily_limit}, monthly=${monthly_limit}")
    
    def enable_strategy(self, strategy_name: str, enabled: bool):
        """Enable or disable an optimization strategy."""
        if strategy_name in self.optimization_strategies:
            self.optimization_strategies[strategy_name].enabled = enabled
            logger.info(f"{'Enabled' if enabled else 'Disabled'} strategy: {strategy_name}")
        else:
            logger.warning(f"Unknown strategy: {strategy_name}")
    
    def clear_old_data(self, days: int = 90):
        """Clear cost data older than N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clear old daily costs
        old_daily_costs = [
            date for date in self.daily_costs.keys()
            if datetime.strptime(date, "%Y-%m-%d") < cutoff_date
        ]
        for date in old_daily_costs:
            del self.daily_costs[date]
        
        # Clear old monthly costs
        old_monthly_costs = [
            month for month in self.monthly_costs.keys()
            if datetime.strptime(month + "-01", "%Y-%m-%d") < cutoff_date
        ]
        for month in old_monthly_costs:
            del self.monthly_costs[month]
        
        # Clear old operation costs
        original_count = len(self.operation_costs)
        self.operation_costs = deque(
            [op for op in self.operation_costs if op["timestamp"] >= cutoff_date],
            maxlen=1000
        )
        
        cleared_count = original_count - len(self.operation_costs)
        logger.info(f"Cleared {len(old_daily_costs)} daily costs, {len(old_monthly_costs)} monthly costs, and {cleared_count} operation costs older than {days} days")

# Global cost optimizer instance
cost_optimizer = CostOptimizer()

def get_cost_optimizer() -> CostOptimizer:
    """Get the global cost optimizer instance."""
    return cost_optimizer 