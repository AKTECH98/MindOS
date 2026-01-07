"""
Repository for task session operations.
"""
from datetime import datetime, timedelta, date
from typing import Optional, List
from data.db import TaskSession
from data.repositories.base_repository import BaseRepository


class TaskSessionRepository(BaseRepository[TaskSession]):
    """Repository for task session data access."""
    
    def __init__(self):
        super().__init__(TaskSession)
    
    def get_by_event_id(self, event_id: str) -> List[TaskSession]:
        """
        Get all sessions for an event.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            List of TaskSession instances
        """
        try:
            return self.db.query(TaskSession).filter(
                TaskSession.event_id == event_id
            ).order_by(TaskSession.start_time.desc()).all()
        except Exception as e:
            print(f"Error getting sessions by event_id: {e}")
            return []
    
    def get_running_session(self, event_id: str) -> Optional[TaskSession]:
        """
        Get currently running session for an event.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Running TaskSession or None
        """
        try:
            return self.db.query(TaskSession).filter(
                TaskSession.event_id == event_id,
                TaskSession.status == 'running'
            ).order_by(TaskSession.start_time.desc()).first()
        except Exception as e:
            print(f"Error getting running session: {e}")
            return None
    
    def start_session(self, event_id: str) -> Optional[TaskSession]:
        """
        Start a new session, pausing any existing one.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Created TaskSession or None
        """
        try:
            # Stop existing running session
            existing = self.get_running_session(event_id)
            if existing:
                now = datetime.now()
                if existing.start_time:
                    duration = int((now - existing.start_time).total_seconds())
                    existing.duration_seconds = duration
                existing.end_time = now
                existing.status = 'Paused'
                self.update(existing)
            
            # Create new session
            return self.create(
                event_id=event_id,
                start_time=datetime.now(),
                status='running'
            )
        except Exception as e:
            print(f"Error starting session: {e}")
            return None
    
    def pause_session(self, event_id: str) -> bool:
        """
        Pause the running session for an event.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self.get_running_session(event_id)
            if session:
                now = datetime.now()
                if session.start_time:
                    duration = int((now - session.start_time).total_seconds())
                    if session.duration_seconds:
                        duration += session.duration_seconds
                    session.duration_seconds = duration
                session.end_time = now
                session.status = 'Paused'
                return self.update(session) is not None
            return False
        except Exception as e:
            print(f"Error pausing session: {e}")
            return False
    
    def get_total_time_spent(self, event_id: str) -> int:
        """
        Get total time spent on an event (in seconds) from all stopped sessions.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Total time in seconds
        """
        try:
            sessions = self.db.query(TaskSession).filter(
                TaskSession.event_id == event_id,
                TaskSession.status.in_(['done', 'Paused']),
                TaskSession.duration_seconds.isnot(None)
            ).all()
            
            total = sum(session.duration_seconds for session in sessions if session.duration_seconds)
            
            # Also check if there's a running session
            active_session = self.get_running_session(event_id)
            if active_session and active_session.start_time:
                now = datetime.now()
                current_duration = int((now - active_session.start_time).total_seconds())
                if active_session.duration_seconds:
                    current_duration += active_session.duration_seconds
                total += current_duration
            
            return total
        except Exception as e:
            print(f"Error getting total time: {e}")
            return 0
    
    def get_time_spent_for_date(self, event_id: str, target_date: date) -> int:
        """
        Get time spent on an event for a specific date (in seconds).
        Only includes sessions that started on the target date.
        
        Args:
            event_id: Google Calendar event ID
            target_date: Date to filter sessions by
            
        Returns:
            Time in seconds spent on the target date
        """
        try:
            # Calculate start and end of target date (local time)
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time()) + timedelta(days=1)
            
            # Get all sessions for this event that started on the target date
            sessions = self.db.query(TaskSession).filter(
                TaskSession.event_id == event_id,
                TaskSession.start_time >= start_of_day,
                TaskSession.start_time < end_of_day
            ).all()
            
            total = 0
            
            for session in sessions:
                if session.status in ['done', 'Paused'] and session.duration_seconds:
                    # For completed/paused sessions, use the stored duration
                    total += session.duration_seconds
                elif session.status == 'running' and session.start_time:
                    # For running sessions, calculate current duration
                    now = datetime.now()
                    current_duration = int((now - session.start_time).total_seconds())
                    if session.duration_seconds:
                        current_duration += session.duration_seconds
                    total += current_duration
            
            return total
        except Exception as e:
            print(f"Error getting time for date: {e}")
            return 0
    
    def get_current_duration(self, event_id: str) -> Optional[int]:
        """
        Get current duration of active session.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Current duration in seconds or None
        """
        session = self.get_running_session(event_id)
        if not session:
            return None
        
        if session.status == 'running' and session.start_time:
            now = datetime.now()
            duration = int((now - session.start_time).total_seconds())
            if session.duration_seconds:
                duration += session.duration_seconds
            return duration
        elif session.status == 'Paused' and session.duration_seconds:
            return session.duration_seconds
        
        return None

