"""
Task Status Service
Manages event completion status in the database.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError

from data.db import get_db, EventCompletion
from services.xp_service import XPService


class TaskStatusService:
    """Service for managing event completion status."""
    
    @staticmethod
    def mark_event_done(event_id: str, description: Optional[str] = None) -> bool:
        """
        Mark an event as done and record the completion timestamp and description.
        
        Args:
            event_id: Google Calendar event ID
            description: Optional description of what was accomplished
            
        Returns:
            True if successful, False otherwise
        """
        db = None
        try:
            db = get_db()
            # Ensure event_id is string for comparison
            event_id_str = str(event_id)
            completion = db.query(EventCompletion).filter(EventCompletion.event_id == event_id_str).first()
            
            # Store local time directly (naive datetime in local timezone)
            local_now = datetime.now()
            
            if completion:
                # Update existing record
                completion.is_done = True
                completion.completed_at = local_now
                completion.completion_description = description
                completion.updated_at = local_now
            else:
                # Create new record
                completion = EventCompletion(
                    event_id=event_id_str,
                    is_done=True,
                    completed_at=local_now,
                    completion_description=description
                )
                db.add(completion)
            
            db.commit()
            
            # Award XP points for task completion
            try:
                XPService.add_xp(XPService.XP_PER_TASK, event_id=event_id_str, description=f"Task completed: {event_id_str}")
            except Exception:
                # Don't fail the task completion if XP fails
                pass
            
            return True
        except SQLAlchemyError as e:
            print(f"Error marking event as done: {e}")
            if db:
                db.rollback()
            return False
        except Exception as e:
            print(f"Unexpected error marking event as done: {e}")
            if db:
                db.rollback()
            return False
        finally:
            if db:
                db.close()
    
    @staticmethod
    def mark_event_undone(event_id: str) -> bool:
        """
        Mark an event as not done.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if successful, False otherwise
        """
        db = None
        try:
            db = get_db()
            completion = db.query(EventCompletion).filter(EventCompletion.event_id == event_id).first()
            
            # Store local time directly
            local_now = datetime.now()
            
            if completion:
                completion.is_done = False
                completion.completed_at = None
                completion.updated_at = local_now
                db.commit()
            else:
                # Create record with is_done=False
                completion = EventCompletion(
                    event_id=event_id,
                    is_done=False,
                    completed_at=None
                )
                db.add(completion)
                db.commit()
            
            # Deduct XP points for marking task as undone
            try:
                XPService.deduct_xp(XPService.XP_PER_TASK, event_id=event_id, description=f"Task undone: {event_id}")
            except Exception:
                # Don't fail the task undo if XP fails
                pass
            
            return True
        except SQLAlchemyError as e:
            print(f"Error marking event as undone: {e}")
            if db:
                db.rollback()
            return False
        except Exception as e:
            print(f"Unexpected error marking event as undone: {e}")
            if db:
                db.rollback()
            return False
        finally:
            if db:
                db.close()
    
    @staticmethod
    def is_event_done(event_id: str) -> bool:
        """
        Check if an event is marked as done.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if event is done, False otherwise
        """
        db = None
        try:
            db = get_db()
            completion = db.query(EventCompletion).filter(EventCompletion.event_id == event_id).first()
            
            if completion:
                return completion.is_done
            return False
        except SQLAlchemyError as e:
            print(f"Error checking event status: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error checking event status: {e}")
            return False
        finally:
            if db:
                db.close()
    
    @staticmethod
    def get_completion_timestamp(event_id: str) -> Optional[datetime]:
        """
        Get the timestamp when an event was marked as done.
        Returns timestamp in local timezone.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Completion timestamp in local timezone or None if not done
        """
        db = None
        try:
            db = get_db()
            completion = db.query(EventCompletion).filter(EventCompletion.event_id == event_id).first()
            
            if completion and completion.is_done and completion.completed_at:
                # Return stored local time (already in local timezone)
                return completion.completed_at
            return None
        except SQLAlchemyError as e:
            print(f"Error getting completion timestamp: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error getting completion timestamp: {e}")
            return None
        finally:
            if db:
                db.close()
    
    @staticmethod
    def get_all_completed_events() -> List[str]:
        """
        Get list of all completed event IDs.
        
        Returns:
            List of event IDs that are marked as done
        """
        db = None
        try:
            db = get_db()
            completions = db.query(EventCompletion).filter(EventCompletion.is_done == True).all()
            return [c.event_id for c in completions]
        except SQLAlchemyError as e:
            print(f"Error getting completed events: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error getting completed events: {e}")
            return []
        finally:
            if db:
                db.close()
    
    @staticmethod
    def get_completion_description(event_id: str) -> Optional[str]:
        """
        Get the completion description for an event.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Completion description or None if not found
        """
        db = None
        try:
            db = get_db()
            completion = db.query(EventCompletion).filter(EventCompletion.event_id == event_id).first()
            
            if completion and completion.completion_description:
                return completion.completion_description
            return None
        except SQLAlchemyError as e:
            print(f"Error getting completion description: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error getting completion description: {e}")
            return None
        finally:
            if db:
                db.close()
    
    @staticmethod
    def get_completion_status_batch(event_ids: List[str]) -> dict:
        """
        Get completion status for multiple events in one query (for performance).
        
        Args:
            event_ids: List of Google Calendar event IDs
            
        Returns:
            Dictionary mapping event_id to (is_done, completed_at, description) tuple
        """
        db = None
        try:
            db = get_db()
            # Ensure all event_ids are strings for comparison
            event_ids_str = [str(eid) for eid in event_ids]
            
            completions = db.query(EventCompletion).filter(EventCompletion.event_id.in_(event_ids_str)).all()
            
            result = {}
            for completion in completions:
                # Return stored local time (already in local timezone)
                # Ensure event_id is string for consistent lookup
                event_id_key = str(completion.event_id)
                result[event_id_key] = (
                    bool(completion.is_done), 
                    completion.completed_at,
                    completion.completion_description
                )
            
            # Add False for events not in database
            for event_id in event_ids_str:
                if event_id not in result:
                    result[event_id] = (False, None, None)
            
            return result
        except SQLAlchemyError as e:
            print(f"Error getting batch completion status: {e}")
            return {event_id: (False, None, None) for event_id in event_ids}
        except Exception as e:
            print(f"Unexpected error getting batch completion status: {e}")
            return {event_id: (False, None, None) for event_id in event_ids}
        finally:
            if db:
                db.close()

