"""
Notification tool for the Notion agent.
"""
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class NotificationTool:
    """
    Tool for sending notifications to users.
    Implements Factor 7: Contact Humans with Tool Calls.
    """
    
    def __init__(self):
        """Initialize the notification tool."""
        self.email_sender = os.getenv("EMAIL_SENDER")
        self.email_api_key = os.getenv("EMAIL_API_KEY")
        
        if not self.email_sender or not self.email_api_key:
            print("WARNING: Email sender or API key not set. Notifications will be logged but not sent.")
    
    def send_notification(self, recipient: str, subject: str, message: str, 
                         priority: str = "normal", notification_type: str = "task_update") -> bool:
        """
        Send a notification to a user.
        
        Args:
            recipient: Email address of the recipient
            subject: Subject line of the notification
            message: Body of the notification
            priority: Priority level (low, normal, high)
            notification_type: Type of notification (task_update, schedule_conflict, etc.)
            
        Returns:
            True if notification was sent successfully
        """
        # For development/testing, just log the notification
        if not self.email_sender or not self.email_api_key or os.getenv("LOG_LEVEL") == "DEBUG":
            print("\n--- NOTIFICATION ---")
            print(f"To: {recipient}")
            print(f"Subject: {subject}")
            print(f"Priority: {priority}")
            print(f"Type: {notification_type}")
            print(f"Message: {message}")
            print("-------------------\n")
            return True
            
        # For production, actually send the email
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.email_sender
            msg["To"] = recipient
            msg["Subject"] = subject
            
            # Add priority header if needed
            if priority == "high":
                msg["X-Priority"] = "1"
                msg["X-MSMail-Priority"] = "High"
            elif priority == "low":
                msg["X-Priority"] = "5"
                msg["X-MSMail-Priority"] = "Low"
                
            # Add message body
            msg.attach(MIMEText(message, "plain"))
            
            # Send the message
            with smtplib.SMTP("smtp.example.com", 587) as server:  # Replace with actual SMTP server
                server.starttls()
                server.login(self.email_sender, self.email_api_key)
                server.send_message(msg)
                
            return True
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            return False
    
    def notify_task_scheduled(self, task: Dict[str, Any], recipient: str) -> bool:
        """
        Send a notification that a task has been scheduled.
        
        Args:
            task: Dictionary with task details
            recipient: Email address of the recipient
            
        Returns:
            True if notification was sent successfully
        """
        subject = f"Task Scheduled: {task.get('title', 'Untitled Task')}"
        
        message = f"Your task has been scheduled:\n\n"
        message += f"Task: {task.get('title', 'Untitled Task')}\n"
        
        if task.get("scheduled_time"):
            message += f"Scheduled Time: {task['scheduled_time']}\n"
            
        if task.get("estimated_duration"):
            message += f"Estimated Duration: {task['estimated_duration']} minutes\n"
            
        if task.get("priority"):
            message += f"Priority: {task['priority']}\n"
            
        if task.get("url"):
            message += f"\nView in Notion: {task['url']}\n"
            
        return self.send_notification(recipient, subject, message, notification_type="task_scheduled")
    
    def notify_scheduling_conflict(self, tasks: List[Dict[str, Any]], recipient: str) -> bool:
        """
        Send a notification about a scheduling conflict.
        
        Args:
            tasks: List of conflicting tasks
            recipient: Email address of the recipient
            
        Returns:
            True if notification was sent successfully
        """
        subject = "Scheduling Conflict Detected"
        
        message = "A scheduling conflict has been detected between the following tasks:\n\n"
        
        for i, task in enumerate(tasks, 1):
            message += f"{i}. {task.get('title', 'Untitled Task')}\n"
            
            if task.get("scheduled_time"):
                message += f"   Scheduled Time: {task['scheduled_time']}\n"
                
            if task.get("priority"):
                message += f"   Priority: {task['priority']}\n"
                
            if task.get("url"):
                message += f"   View in Notion: {task['url']}\n"
                
            message += "\n"
            
        message += "Please review and adjust the schedule as needed."
        
        return self.send_notification(
            recipient, subject, message, 
            priority="high", notification_type="scheduling_conflict"
        )
    
    def notify_upcoming_task(self, task: Dict[str, Any], minutes_until: int, recipient: str) -> bool:
        """
        Send a reminder about an upcoming task.
        
        Args:
            task: Dictionary with task details
            minutes_until: Minutes until the task is scheduled
            recipient: Email address of the recipient
            
        Returns:
            True if notification was sent successfully
        """
        subject = f"Upcoming Task: {task.get('title', 'Untitled Task')}"
        
        message = f"You have a task coming up in {minutes_until} minutes:\n\n"
        message += f"Task: {task.get('title', 'Untitled Task')}\n"
        
        if task.get("scheduled_time"):
            message += f"Scheduled Time: {task['scheduled_time']}\n"
            
        if task.get("estimated_duration"):
            message += f"Estimated Duration: {task['estimated_duration']} minutes\n"
            
        if task.get("priority"):
            message += f"Priority: {task['priority']}\n"
            
        if task.get("notes"):
            message += f"Notes: {task['notes']}\n"
            
        if task.get("url"):
            message += f"\nView in Notion: {task['url']}\n"
            
        return self.send_notification(recipient, subject, message, notification_type="upcoming_task") 