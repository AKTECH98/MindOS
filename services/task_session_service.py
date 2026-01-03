"""
Task Session Service
Manages time tracking sessions for tasks.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError

from data.db import get_db, TaskSession


class TaskSessionService:
    """Service for managing task time tracking sessions."""
    
    @staticmethod
    def start_session(event_id: str) -> Optional[TaskSession]:
        """
        Start a new time tracking session for an event.
        Stops any existing running session for this event first.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Created TaskSession or None if failed
        """
        db = None
        try:
            db = get_db()
            
            # Stop any existing running session for this event
            existing_session = db.query(TaskSession).filter(
                TaskSession.event_id == event_id,
                TaskSession.status == 'running'
            ).first()
            
            if existing_session:
                # Calculate duration and pause it
                now = datetime.now()
                if existing_session.start_time:
                    duration = int((now - existing_session.start_time).total_seconds())
                    existing_session.duration_seconds = duration
                existing_session.end_time = now
                existing_session.status = 'Paused'
            
            # Create new running session
            new_session = TaskSession(
                event_id=event_id,
                start_time=datetime.now(),
                status='running'
            )
            db.add(new_session)
            db.commit()
            return new_session
        except SQLAlchemyError as e:
            print(f"Error starting session: {e}")
            if db:
                db.rollback()
            return None
        except Exception as e:
            print(f"Unexpected error starting session: {e}")
            if db:
                db.rollback()
            return None
        finally:
            if db:
                db.close()
    
    @staticmethod
    def pause_session(event_id: str) -> bool:
        """
        Stop the currently running session for an event (task is paused, session is done).
        Does not mark the task as done.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if successful, False otherwise
        """
        db = None
        try:
            db = get_db()
            session = db.query(TaskSession).filter(
                TaskSession.event_id == event_id,
                TaskSession.status == 'running'
            ).first()
            
            if session:
                now = datetime.now()
                if session.start_time:
                    duration = int((now - session.start_time).total_seconds())
                    # Add any previous paused duration if exists
                    if session.duration_seconds:
                        duration += session.duration_seconds
                    session.duration_seconds = duration
                session.end_time = now
                session.status = 'Paused'  # Task is paused
                db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            print(f"Error pausing session: {e}")
            if db:
                db.rollback()
            return False
        except Exception as e:
            print(f"Unexpected error pausing session: {e}")
            if db:
                db.rollback()
            return False
        finally:
            if db:
                db.close()
    
    @staticmethod
    def get_active_session(event_id: str) -> Optional[TaskSession]:
        """
        Get the currently active (running) session for an event.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Active running TaskSession or None
        """
        db = None
        try:
            db = get_db()
            session = db.query(TaskSession).filter(
                TaskSession.event_id == event_id,
                TaskSession.status == 'running'
            ).order_by(TaskSession.start_time.desc()).first()
            return session
        except SQLAlchemyError as e:
            print(f"Error getting active session: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error getting active session: {e}")
            return None
        finally:
            if db:
                db.close()
    
    @staticmethod
    def get_total_time_spent(event_id: str) -> int:
        """
        Get total time spent on an event (in seconds) from all stopped sessions.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Total time in seconds
        """
        db = None
        try:
            db = get_db()
            sessions = db.query(TaskSession).filter(
                TaskSession.event_id == event_id,
                TaskSession.status.in_(['done', 'Paused']),
                TaskSession.duration_seconds.isnot(None)
            ).all()
            
            total = sum(session.duration_seconds for session in sessions if session.duration_seconds)
            
            # Also check if there's a running session
            active_session = TaskSessionService.get_active_session(event_id)
            if active_session and active_session.start_time:
                # Add current running time
                now = datetime.now()
                current_duration = int((now - active_session.start_time).total_seconds())
                if active_session.duration_seconds:
                    current_duration += active_session.duration_seconds
                total += current_duration
            
            return total
        except SQLAlchemyError as e:
            print(f"Error getting total time: {e}")
            return 0
        except Exception as e:
            print(f"Unexpected error getting total time: {e}")
            return 0
        finally:
            if db:
                db.close()
    
    @staticmethod
    def get_current_duration(event_id: str) -> Optional[int]:
        """
        Get current duration of active session (for display).
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Current duration in seconds or None if no active session
        """
        session = TaskSessionService.get_active_session(event_id)
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

