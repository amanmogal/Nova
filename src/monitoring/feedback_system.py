"""
Feedback system for collecting and analyzing user feedback.

This module provides comprehensive feedback collection and analysis
capabilities for continuous improvement of the Notion Agent.
"""

import logging
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

from ..config import get_settings
from ..db.supabase_connector import SupabaseConnector

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Types of feedback that can be collected."""
    SATISFACTION = "satisfaction"
    TASK_COMPLETION = "task_completion"
    DECISION_QUALITY = "decision_quality"
    RESPONSE_RELEVANCE = "response_relevance"
    OVERALL_EXPERIENCE = "overall_experience"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"

class FeedbackRating(Enum):
    """Rating scale for feedback."""
    VERY_POOR = 1
    POOR = 2
    NEUTRAL = 3
    GOOD = 4
    EXCELLENT = 5

@dataclass
class UserFeedback:
    """User feedback data structure."""
    timestamp: datetime
    feedback_type: FeedbackType
    rating: Optional[FeedbackRating] = None
    text_feedback: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    goal: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class FeedbackAnalysis:
    """Feedback analysis results."""
    total_feedback: int
    average_rating: float
    rating_distribution: Dict[int, int]
    feedback_by_type: Dict[str, int]
    recent_trends: Dict[str, float]
    improvement_suggestions: List[str]
    timestamp: datetime

class FeedbackSystem:
    """Comprehensive feedback collection and analysis system."""
    
    def __init__(self):
        """Initialize feedback system."""
        self.settings = get_settings()
        self.db = SupabaseConnector()
        
        # In-memory feedback storage
        self.feedback_store = []
        self.feedback_analysis_cache = {}
        self.cache_duration = timedelta(hours=1)
        
        logger.info("Feedback system initialized")
    
    def collect_feedback(self, 
                        feedback_type: FeedbackType,
                        rating: Optional[FeedbackRating] = None,
                        text_feedback: Optional[str] = None,
                        context: Optional[Dict[str, Any]] = None,
                        user_id: Optional[str] = None,
                        session_id: Optional[str] = None,
                        goal: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Collect user feedback and store it."""
        feedback = UserFeedback(
            timestamp=datetime.now(),
            feedback_type=feedback_type,
            rating=rating,
            text_feedback=text_feedback,
            context=context,
            user_id=user_id,
            session_id=session_id,
            goal=goal,
            metadata=metadata
        )
        
        # Store in memory
        self.feedback_store.append(feedback)
        
        # Clear analysis cache since we have new data
        self.feedback_analysis_cache.clear()
        
        # Log feedback collection
        logger.info(f"Collected {feedback_type.value} feedback: "
                   f"rating={rating.value if rating else 'None'}, "
                   f"user={user_id}, goal={goal}")
        
        # Generate feedback ID for reference
        feedback_id = f"feedback_{len(self.feedback_store)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return feedback_id
    
    def collect_satisfaction_feedback(self, 
                                    rating: FeedbackRating,
                                    text_feedback: Optional[str] = None,
                                    context: Optional[Dict[str, Any]] = None,
                                    **kwargs) -> str:
        """Collect user satisfaction feedback."""
        return self.collect_feedback(
            feedback_type=FeedbackType.SATISFACTION,
            rating=rating,
            text_feedback=text_feedback,
            context=context,
            **kwargs
        )
    
    def collect_task_completion_feedback(self, 
                                       task_id: str,
                                       completed: bool,
                                       rating: Optional[FeedbackRating] = None,
                                       text_feedback: Optional[str] = None,
                                       **kwargs) -> str:
        """Collect task completion feedback."""
        context = {
            "task_id": task_id,
            "completed": completed
        }
        
        return self.collect_feedback(
            feedback_type=FeedbackType.TASK_COMPLETION,
            rating=rating,
            text_feedback=text_feedback,
            context=context,
            **kwargs
        )
    
    def collect_decision_quality_feedback(self, 
                                        decision: str,
                                        rating: FeedbackRating,
                                        text_feedback: Optional[str] = None,
                                        **kwargs) -> str:
        """Collect feedback on agent decision quality."""
        context = {
            "decision": decision
        }
        
        return self.collect_feedback(
            feedback_type=FeedbackType.DECISION_QUALITY,
            rating=rating,
            text_feedback=text_feedback,
            context=context,
            **kwargs
        )
    
    def collect_bug_report(self, 
                          description: str,
                          severity: str = "medium",
                          steps_to_reproduce: Optional[str] = None,
                          **kwargs) -> str:
        """Collect bug report feedback."""
        context = {
            "severity": severity,
            "steps_to_reproduce": steps_to_reproduce
        }
        
        return self.collect_feedback(
            feedback_type=FeedbackType.BUG_REPORT,
            text_feedback=description,
            context=context,
            **kwargs
        )
    
    def collect_feature_request(self, 
                               description: str,
                               priority: str = "medium",
                               **kwargs) -> str:
        """Collect feature request feedback."""
        context = {
            "priority": priority
        }
        
        return self.collect_feedback(
            feedback_type=FeedbackType.FEATURE_REQUEST,
            text_feedback=description,
            context=context,
            **kwargs
        )
    
    def analyze_feedback(self, hours: int = 24) -> FeedbackAnalysis:
        """Analyze feedback for the last N hours."""
        # Check cache first
        cache_key = f"analysis_{hours}"
        if cache_key in self.feedback_analysis_cache:
            cached_analysis, cache_time = self.feedback_analysis_cache[cache_key]
            if datetime.now() - cache_time < self.cache_duration:
                return cached_analysis
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter feedback by time
        recent_feedback = [
            f for f in self.feedback_store 
            if f.timestamp >= cutoff_time
        ]
        
        if not recent_feedback:
            return FeedbackAnalysis(
                total_feedback=0,
                average_rating=0.0,
                rating_distribution={},
                feedback_by_type={},
                recent_trends={},
                improvement_suggestions=[],
                timestamp=datetime.now()
            )
        
        # Calculate basic statistics
        total_feedback = len(recent_feedback)
        
        # Rating analysis
        ratings = [f.rating.value for f in recent_feedback if f.rating]
        average_rating = sum(ratings) / len(ratings) if ratings else 0.0
        
        # Rating distribution
        rating_distribution = defaultdict(int)
        for rating in ratings:
            rating_distribution[rating] += 1
        
        # Feedback by type
        feedback_by_type = defaultdict(int)
        for feedback in recent_feedback:
            feedback_by_type[feedback.feedback_type.value] += 1
        
        # Recent trends (compare with previous period)
        previous_cutoff = cutoff_time - timedelta(hours=hours)
        previous_feedback = [
            f for f in self.feedback_store 
            if previous_cutoff <= f.timestamp < cutoff_time
        ]
        
        recent_trends = {}
        if previous_feedback:
            previous_ratings = [f.rating.value for f in previous_feedback if f.rating]
            previous_avg = sum(previous_ratings) / len(previous_ratings) if previous_ratings else 0.0
            recent_trends["rating_change"] = average_rating - previous_avg
            recent_trends["feedback_volume_change"] = total_feedback - len(previous_feedback)
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(recent_feedback)
        
        # Create analysis result
        analysis = FeedbackAnalysis(
            total_feedback=total_feedback,
            average_rating=round(average_rating, 2),
            rating_distribution=dict(rating_distribution),
            feedback_by_type=dict(feedback_by_type),
            recent_trends=recent_trends,
            improvement_suggestions=improvement_suggestions,
            timestamp=datetime.now()
        )
        
        # Cache the result
        self.feedback_analysis_cache[cache_key] = (analysis, datetime.now())
        
        return analysis
    
    def _generate_improvement_suggestions(self, feedback: List[UserFeedback]) -> List[str]:
        """Generate improvement suggestions based on feedback."""
        suggestions = []
        
        # Analyze low ratings
        low_ratings = [f for f in feedback if f.rating and f.rating.value <= 2]
        if low_ratings:
            suggestions.append(f"Address {len(low_ratings)} low-rated interactions")
        
        # Analyze feedback types
        feedback_counts = defaultdict(int)
        for f in feedback:
            feedback_counts[f.feedback_type.value] += 1
        
        # Check for specific issues
        bug_reports = [f for f in feedback if f.feedback_type == FeedbackType.BUG_REPORT]
        if bug_reports:
            suggestions.append(f"Review {len(bug_reports)} bug reports")
        
        feature_requests = [f for f in feedback if f.feedback_type == FeedbackType.FEATURE_REQUEST]
        if feature_requests:
            suggestions.append(f"Consider {len(feature_requests)} feature requests")
        
        # Check for task completion issues
        task_feedback = [f for f in feedback if f.feedback_type == FeedbackType.TASK_COMPLETION]
        failed_tasks = [f for f in task_feedback if f.context and not f.context.get("completed", True)]
        if failed_tasks:
            suggestions.append(f"Investigate {len(failed_tasks)} failed task completions")
        
        return suggestions
    
    def get_feedback_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get a summary of feedback data."""
        analysis = self.analyze_feedback(hours)
        
        return {
            "time_period_hours": hours,
            "total_feedback": analysis.total_feedback,
            "average_rating": analysis.average_rating,
            "rating_distribution": analysis.rating_distribution,
            "feedback_by_type": analysis.feedback_by_type,
            "recent_trends": analysis.recent_trends,
            "improvement_suggestions": analysis.improvement_suggestions,
            "timestamp": analysis.timestamp.isoformat()
        }
    
    def get_recent_feedback(self, hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent feedback entries."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_feedback = [
            f for f in self.feedback_store 
            if f.timestamp >= cutoff_time
        ]
        
        # Sort by timestamp (newest first) and limit
        recent_feedback.sort(key=lambda x: x.timestamp, reverse=True)
        recent_feedback = recent_feedback[:limit]
        
        # Convert to dictionary format
        return [
            {
                "timestamp": f.timestamp.isoformat(),
                "feedback_type": f.feedback_type.value,
                "rating": f.rating.value if f.rating else None,
                "text_feedback": f.text_feedback,
                "context": f.context,
                "user_id": f.user_id,
                "session_id": f.session_id,
                "goal": f.goal,
                "metadata": f.metadata
            }
            for f in recent_feedback
        ]
    
    def save_feedback_to_db(self):
        """Save feedback to database for persistence."""
        try:
            # Convert feedback to JSON-serializable format
            feedback_data = [
                {
                    "timestamp": f.timestamp.isoformat(),
                    "feedback_type": f.feedback_type.value,
                    "rating": f.rating.value if f.rating else None,
                    "text_feedback": f.text_feedback,
                    "context": f.context,
                    "user_id": f.user_id,
                    "session_id": f.session_id,
                    "goal": f.goal,
                    "metadata": f.metadata
                }
                for f in self.feedback_store
            ]
            
            # Save to database (implementation depends on your schema)
            # self.db.save_feedback(feedback_data)
            
            logger.info(f"Saved {len(feedback_data)} feedback entries to database")
            
        except Exception as e:
            logger.error(f"Error saving feedback to database: {e}")
    
    def clear_old_feedback(self, days: int = 30):
        """Clear feedback older than N days from memory."""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        original_count = len(self.feedback_store)
        self.feedback_store = [
            f for f in self.feedback_store 
            if f.timestamp >= cutoff_time
        ]
        
        cleared_count = original_count - len(self.feedback_store)
        logger.info(f"Cleared {cleared_count} feedback entries older than {days} days")
        
        # Clear analysis cache
        self.feedback_analysis_cache.clear()

# Global feedback system instance
feedback_system = FeedbackSystem()

def get_feedback_system() -> FeedbackSystem:
    """Get the global feedback system instance."""
    return feedback_system 