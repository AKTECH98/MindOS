"""
Core business logic for task session management.
"""
from typing import Optional
from datetime import date
from data.repositories.task_session_repository import TaskSessionRepository
from data.db import TaskSession


class TaskSessionCore:
    """Core business logic for task session management."""
    
    def __init__(self):
        self.session_repo = TaskSessionRepository()
    
    def start_session(self, event_id: str) -> Optional[TaskSession]:
        """
        Start a new time tracking session for an event.
        Business rule: Only one session can run at a time per event.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Created TaskSession or None
        """
        try:
            return self.session_repo.start_session(event_id)
        finally:
            self.session_repo.close()
    
    def pause_session(self, event_id: str) -> bool:
        """
        Pause the running session for an event.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.session_repo.pause_session(event_id)
        finally:
            self.session_repo.close()
    
    def get_active_session(self, event_id: str) -> Optional[TaskSession]:
        """
        Get the currently active session for an event.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Active TaskSession or None
        """
        try:
            return self.session_repo.get_running_session(event_id)
        finally:
            self.session_repo.close()
    
    def get_total_time_spent(self, event_id: str) -> int:
        """
        Get total time spent on an event.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Total time in seconds
        """
        try:
            return self.session_repo.get_total_time_spent(event_id)
        finally:
            self.session_repo.close()
    
    def get_time_spent_for_date(self, event_id: str, target_date: date) -> int:
        """
        Get time spent on an event for a specific date.
        
        Args:
            event_id: Google Calendar event ID
            target_date: Date to filter sessions by
            
        Returns:
            Time in seconds spent on the target date
        """
        try:
            return self.session_repo.get_time_spent_for_date(event_id, target_date)
        finally:
            self.session_repo.close()
    
    def get_current_duration(self, event_id: str) -> Optional[int]:
        """
        Get current duration of active session.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Current duration in seconds or None
        """
        try:
            return self.session_repo.get_current_duration(event_id)
        finally:
            self.session_repo.close()

