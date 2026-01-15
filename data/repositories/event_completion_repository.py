"""
Repository for event completion operations.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Tuple
from sqlalchemy import func
from data.db import EventCompletion
from data.repositories.base_repository import BaseRepository


class EventCompletionRepository(BaseRepository[EventCompletion]):
    """Repository for event completion data access."""
    
    def __init__(self):
        super().__init__(EventCompletion)
    
    def get_by_event_id(self, event_id: str, completion_date: Optional[date] = None) -> Optional[EventCompletion]:
        """
        Get completion record by event ID and optionally by date.
        
        Args:
            event_id: Google Calendar event ID
            completion_date: Optional date to filter by (defaults to today)
            
        Returns:
            EventCompletion instance or None
        """
        try:
            if completion_date is None:
                completion_date = date.today()
            
            # Use DATE(completed_at) to match by date
            return self.db.query(EventCompletion).filter(
                EventCompletion.event_id == str(event_id),
                func.date(EventCompletion.completed_at) == completion_date,
                EventCompletion.is_done == True
            ).first()
        except Exception as e:
            print(f"Error getting completion by event_id: {e}")
            return None
    
    def get_by_event_id_and_date(self, event_id: str, completion_date: date) -> Optional[EventCompletion]:
        """
        Get completion record by event ID and completion date.
        
        Args:
            event_id: Google Calendar event ID
            completion_date: Date when task was completed
            
        Returns:
            EventCompletion instance or None
        """
        return self.get_by_event_id(event_id, completion_date)
    
    def mark_done(self, event_id: str, description: Optional[str] = None, completion_date: Optional[date] = None, completed_at_datetime: Optional[datetime] = None) -> Optional[EventCompletion]:
        """
        Mark an event as done for a specific date.
        
        Args:
            event_id: Google Calendar event ID
            description: Optional completion description
            completion_date: Date when task is being completed (defaults to today)
            completed_at_datetime: Optional specific datetime for completed_at (defaults to midnight of completion_date or now)
            
        Returns:
            Updated or created EventCompletion instance
        """
        if completion_date is None:
            completion_date = date.today()
        
        # If completed_at_datetime is provided, use it; otherwise use midnight of completion_date
        if completed_at_datetime is not None:
            completed_at = completed_at_datetime
        else:
            # Set to midnight of the completion_date
            completed_at = datetime.combine(completion_date, datetime.min.time())
        
        local_now = datetime.now()
        
        completion = self.get_by_event_id_and_date(event_id, completion_date)
        
        if completion:
            # Update existing completion
            completion.is_done = True
            completion.completed_at = completed_at
            completion.completion_description = description
            completion.updated_at = local_now
            return self.update(completion)
        else:
            # Create new completion - use the specified completed_at datetime
            # The date will be extracted from completed_at in queries using DATE(completed_at)
            return self.create(
                event_id=str(event_id),
                is_done=True,
                completed_at=completed_at,
                completion_description=description
            )
    
    def mark_undone(self, event_id: str, completion_date: Optional[date] = None) -> Optional[EventCompletion]:
        """
        Mark an event as undone for a specific date.
        
        Args:
            event_id: Google Calendar event ID
            completion_date: Date to mark as undone (defaults to today)
            
        Returns:
            Updated EventCompletion instance or None
        """
        local_now = datetime.now()
        if completion_date is None:
            completion_date = date.today()
        
        completion = self.get_by_event_id_and_date(event_id, completion_date)
        
        if completion:
            completion.is_done = False
            completion.completed_at = None
            completion.updated_at = local_now
            return self.update(completion)
        else:
            # Create undone record (though this is unusual)
            return self.create(
                event_id=str(event_id),
                completion_date=completion_date,
                is_done=False
            )
    
    def is_done(self, event_id: str, completion_date: Optional[date] = None) -> bool:
        """
        Check if event is marked as done for a specific date.
        
        Args:
            event_id: Google Calendar event ID
            completion_date: Date to check (defaults to today)
            
        Returns:
            True if done on that date, False otherwise
        """
        if completion_date is None:
            completion_date = date.today()
        
        completion = self.get_by_event_id_and_date(event_id, completion_date)
        return completion.is_done if completion else False
    
    def get_completion_timestamp(self, event_id: str, completion_date: Optional[date] = None) -> Optional[datetime]:
        """
        Get completion timestamp for a specific date.
        
        Args:
            event_id: Google Calendar event ID
            completion_date: Date to check (defaults to today)
            
        Returns:
            Completion timestamp or None
        """
        if completion_date is None:
            completion_date = date.today()
        
        completion = self.get_by_event_id_and_date(event_id, completion_date)
        if completion and completion.is_done and completion.completed_at:
            return completion.completed_at
        return None
    
    def get_completion_description(self, event_id: str, completion_date: Optional[date] = None) -> Optional[str]:
        """
        Get completion description for a specific date.
        
        Args:
            event_id: Google Calendar event ID
            completion_date: Date to check (defaults to today)
            
        Returns:
            Description or None
        """
        if completion_date is None:
            completion_date = date.today()
        
        completion = self.get_by_event_id_and_date(event_id, completion_date)
        if completion and completion.completion_description:
            return completion.completion_description
        return None
    
    def get_all_completed_events(self) -> List[str]:
        """
        Get list of all completed event IDs.
        
        Returns:
            List of event IDs
        """
        try:
            completions = self.db.query(EventCompletion).filter(
                EventCompletion.is_done == True
            ).all()
            return [c.event_id for c in completions]
        except Exception as e:
            print(f"Error getting completed events: {e}")
            return []
    
    def get_completion_status_batch(self, event_ids: List[str], completion_date: Optional[date] = None) -> Dict[str, Tuple[bool, Optional[datetime], Optional[str]]]:
        """
        Get completion status for multiple events on a specific date.
        
        Args:
            event_ids: List of event IDs
            completion_date: Date to check completions for (defaults to today)
            
        Returns:
            Dictionary mapping event_id to (is_done, completed_at, description) tuple
        """
        try:
            if completion_date is None:
                completion_date = date.today()
            
            event_ids_str = [str(eid) for eid in event_ids]
            completions = self.db.query(EventCompletion).filter(
                EventCompletion.event_id.in_(event_ids_str),
                func.date(EventCompletion.completed_at) == completion_date,
                EventCompletion.is_done == True
            ).all()
            
            result = {}
            for completion in completions:
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
        except Exception as e:
            print(f"Error getting batch completion status: {e}")
            return {event_id: (False, None, None) for event_id in event_ids}

