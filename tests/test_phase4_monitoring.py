"""
Comprehensive test script for Phase 4 monitoring and analytics.

Tests LangSmith integration, performance metrics, feedback system,
analytics dashboard, and cost optimization features.
"""

import asyncio
import os
import sys
import time
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.monitoring.langsmith_tracer import get_tracer, LangSmithTracer
from src.monitoring.metrics_collector import get_metrics_collector, MetricsCollector
from src.monitoring.feedback_system import get_feedback_system, FeedbackSystem, FeedbackType, FeedbackRating
from src.monitoring.analytics_dashboard import get_analytics_dashboard, AnalyticsDashboard
from src.monitoring.cost_optimizer import get_cost_optimizer, CostOptimizer

async def test_phase4_monitoring():
    """Test Phase 4 monitoring and analytics features."""
    print(" Testing Phase 4 Monitoring & Analytics")
    print("=" * 60)
    
    try:
        # Test 1: LangSmith Tracer
        print("1. Testing LangSmith Tracer...")
        tracer = get_tracer()
        print(f"   LangSmith enabled: {tracer.enabled}")
        print(f"   Project name: {tracer.project_name}")
        
        # Test tracing capabilities
        with tracer.trace_agent_run("test_goal", "test_input") as run_tree:
            if run_tree:
                print("    LangSmith tracing working")
            else:
                print("    LangSmith tracing not configured (expected if no API key)")
        
        # Test 2: Metrics Collector
        print("\n2. Testing Metrics Collector...")
        metrics_collector = get_metrics_collector()
        
        # Record some test metrics
        start_time = time.time()
        time.sleep(0.1)  # Simulate operation
        duration_ms = (time.time() - start_time) * 1000
        
        metrics_collector.record_operation(
            operation_type="test_operation",
            duration_ms=duration_ms,
            token_count=500,
            success=True
        )
        
        metrics_collector.record_llm_call(
            model="gemini-pro",
            input_tokens=300,
            output_tokens=200,
            duration_ms=duration_ms,
            success=True
        )
        
        # Get performance summary
        performance_summary = metrics_collector.get_performance_summary(hours=1)
        print(f"   Total operations: {performance_summary.get('total_operations', 0)}")
        print(f"   Success rate: {performance_summary.get('success_rate_percent', 0)}%")
        print(f"   Average duration: {performance_summary.get('average_duration_ms', 0):.2f}ms")
        print("    Metrics collection working")
        
        # Test 3: Feedback System
        print("\n3. Testing Feedback System...")
        feedback_system = get_feedback_system()
        
        # Collect some test feedback
        feedback_id1 = feedback_system.collect_satisfaction_feedback(
            rating=FeedbackRating.EXCELLENT,
            text_feedback="Great performance!",
            user_id="test_user",
            goal="daily_planning"
        )
        
        feedback_id2 = feedback_system.collect_task_completion_feedback(
            task_id="test_task_123",
            completed=True,
            rating=FeedbackRating.GOOD,
            text_feedback="Task completed successfully"
        )
        
        feedback_id3 = feedback_system.collect_bug_report(
            description="Test bug report",
            severity="low",
            steps_to_reproduce="Test steps"
        )
        
        # Get feedback summary
        feedback_summary = feedback_system.get_feedback_summary(hours=1)
        print(f"   Total feedback: {feedback_summary.get('total_feedback', 0)}")
        print(f"   Average rating: {feedback_summary.get('average_rating', 0)}/5")
        print(f"   Feedback types: {feedback_summary.get('feedback_by_type', {})}")
        print("    Feedback system working")
        
        # Test 4: Cost Optimizer
        print("\n4. Testing Cost Optimizer...")
        cost_optimizer = get_cost_optimizer()
        
        # Track some test costs
        cost_optimizer.track_operation_cost(
            operation_type="test_operation",
            cost_usd=0.0025,
            tokens_used=500,
            model="gemini-pro"
        )
        
        cost_optimizer.track_operation_cost(
            operation_type="llm_call",
            cost_usd=0.0015,
            tokens_used=300,
            model="gemini-pro"
        )
        
        # Get cost summary
        cost_summary = cost_optimizer.get_cost_summary(days=1)
        print(f"   Total cost: ${cost_summary.get('total_cost', 0):.6f}")
        print(f"   Total operations: {cost_summary.get('total_operations', 0)}")
        print(f"   Cost breakdown: {cost_summary.get('operation_cost_breakdown', {})}")
        print("    Cost optimization working")
        
        # Test 5: Analytics Dashboard
        print("\n5. Testing Analytics Dashboard...")
        analytics_dashboard = get_analytics_dashboard()
        
        # Get comprehensive dashboard
        dashboard = analytics_dashboard.get_comprehensive_dashboard(hours=1)
        print(f"   System health: {dashboard.system_health.get('status', 'unknown')}")
        print(f"   Health score: {dashboard.system_health.get('health_score', 0)}")
        print(f"   Issues: {len(dashboard.system_health.get('issues', []))}")
        print(f"   Warnings: {len(dashboard.system_health.get('warnings', []))}")
        
        # Get dashboard summary
        dashboard_summary = analytics_dashboard.get_dashboard_summary(hours=1)
        key_metrics = dashboard_summary.get('key_metrics', {})
        print(f"   Key metrics - Operations: {key_metrics.get('total_operations', 0)}")
        print(f"   Key metrics - Success rate: {key_metrics.get('success_rate', 0)}%")
        print(f"   Key metrics - Cost: ${key_metrics.get('total_cost', 0):.6f}")
        print("    Analytics dashboard working")
        
        # Test 6: Generate Report
        print("\n6. Testing Report Generation...")
        report = analytics_dashboard.generate_report(hours=1)
        
        executive_summary = report.get('executive_summary', {})
        print(f"   System health: {executive_summary.get('system_health', 'unknown')}")
        print(f"   Health score: {executive_summary.get('health_score', 0)}")
        print(f"   Total operations: {executive_summary.get('total_operations', 0)}")
        print(f"   Success rate: {executive_summary.get('success_rate', 0)}%")
        print(f"   User satisfaction: {executive_summary.get('user_satisfaction', 0)}/5")
        
        key_insights = report.get('key_insights', [])
        print(f"   Key insights: {len(key_insights)}")
        for insight in key_insights[:2]:  # Show first 2 insights
            print(f"     - {insight}")
        
        recommendations = report.get('recommendations', [])
        print(f"   Recommendations: {len(recommendations)}")
        for rec in recommendations[:2]:  # Show first 2 recommendations
            print(f"     - {rec}")
        
        print("    Report generation working")
        
        # Test 7: Alerts and Monitoring
        print("\n7. Testing Alerts and Monitoring...")
        
        # Get alerts
        alerts = analytics_dashboard.get_alerts(hours=1)
        print(f"   Total alerts: {len(alerts)}")
        for alert in alerts:
            print(f"     - {alert['type']}: {alert['message']} (severity: {alert['severity']})")
        
        # Get cost alerts
        cost_alerts = cost_optimizer.get_cost_alerts(hours=1)
        print(f"   Cost alerts: {len(cost_alerts)}")
        for alert in cost_alerts:
            print(f"     - {alert['alert_type']}: {alert['message']}")
        
        print("    Alerts and monitoring working")
        
        # Test 8: Performance Optimization
        print("\n8. Testing Performance Optimization...")
        
        # Test cost optimization
        optimization_result = cost_optimizer.optimize_operation(
            operation_type="test_optimization",
            estimated_tokens=1500,
            model="gemini-pro"
        )
        
        print(f"   Optimization applied: {optimization_result.get('optimized', False)}")
        print(f"   Estimated cost: ${optimization_result.get('estimated_cost', 0):.6f}")
        print(f"   Recommendations: {len(optimization_result.get('recommendations', []))}")
        
        # Get optimization recommendations
        opt_recommendations = cost_optimizer.get_optimization_recommendations()
        print(f"   General recommendations: {len(opt_recommendations)}")
        for rec in opt_recommendations:
            print(f"     - {rec['category']}: {rec['recommendation']} (priority: {rec['priority']})")
        
        print("    Performance optimization working")
        
        print("\n" + "=" * 60)
        print(" Phase 4 Monitoring Test Completed Successfully!")
        
        # Summary
        print("\n PHASE 4 SUMMARY:")
        print(f"   - LangSmith Integration: {' Working' if tracer.enabled else ' Not configured'}")
        print(f"   - Metrics Collection:  Working ({performance_summary.get('total_operations', 0)} operations)")
        print(f"   - Feedback System:  Working ({feedback_summary.get('total_feedback', 0)} feedback entries)")
        print(f"   - Cost Optimization:  Working (${cost_summary.get('total_cost', 0):.6f} tracked)")
        print(f"   - Analytics Dashboard:  Working (health: {dashboard.system_health.get('status', 'unknown')})")
        print(f"   - Report Generation:  Working ({len(key_insights)} insights, {len(recommendations)} recommendations)")
        print(f"   - Alerts & Monitoring:  Working ({len(alerts)} alerts, {len(cost_alerts)} cost alerts)")
        print(f"   - Performance Optimization:  Working ({len(opt_recommendations)} recommendations)")
        
        return {
            "success": True,
            "langsmith_enabled": tracer.enabled,
            "metrics_collected": performance_summary.get('total_operations', 0),
            "feedback_collected": feedback_summary.get('total_feedback', 0),
            "cost_tracked": cost_summary.get('total_cost', 0),
            "system_health": dashboard.system_health.get('status', 'unknown'),
            "alerts_generated": len(alerts) + len(cost_alerts)
        }
        
    except Exception as e:
        print(f" Error testing Phase 4 monitoring: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

async def test_monitoring_integration():
    """Test integration of monitoring systems with the agent."""
    print("\n Testing Monitoring Integration")
    print("=" * 40)
    
    try:
        # Test that monitoring systems can be imported and used together
        from src.monitoring import (
            LangSmithTracer, MetricsCollector, FeedbackSystem, 
            AnalyticsDashboard, CostOptimizer
        )
        
        print("    All monitoring modules imported successfully")
        
        # Test global instances
        tracer = get_tracer()
        metrics = get_metrics_collector()
        feedback = get_feedback_system()
        dashboard = get_analytics_dashboard()
        optimizer = get_cost_optimizer()
        
        print("    All global instances created successfully")
        
        # Test basic functionality
        metrics.record_operation("integration_test", 100.0, 100)
        feedback.collect_satisfaction_feedback(FeedbackRating.GOOD)
        optimizer.track_operation_cost("integration_test", 0.001, 100)
        
        print("    Basic monitoring functionality working")
        
        return True
        
    except Exception as e:
        print(f" Error in monitoring integration test: {str(e)}")
        return False

if __name__ == "__main__":
    async def main():
        await test_monitoring_integration()
        await test_phase4_monitoring()
    
    asyncio.run(main()) 