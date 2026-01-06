"""
Repository for event completion operations.
"""
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from data.db import EventCompletion
from data.repositories.base_repository import BaseRepository


class EventCompletionRepository(BaseRepository[EventCompletion]):
    """Repository for event completion data access."""
    
    def __init__(self):
        super().__init__(EventCompletion)
    
    def get_by_event_id(self, event_id: str) -> Optional[EventCompletion]:
        """
        Get completion record by event ID.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            EventCompletion instance or None
        """
        try:
            return self.db.query(EventCompletion).filter(
                EventCompletion.event_id == str(event_id)
            ).first()
        except Exception as e:
            print(f"Error getting completion by event_id: {e}")
            return None
    
    def mark_done(self, event_id: str, description: Optional[str] = None) -> Optional[EventCompletion]:
        """
        Mark an event as done.
        
        Args:
            event_id: Google Calendar event ID
            description: Optional completion description
            
        Returns:
            Updated or created EventCompletion instance
        """
        local_now = datetime.now()
        completion = self.get_by_event_id(event_id)
        
        if completion:
            completion.is_done = True
            completion.completed_at = local_now
            completion.completion_description = description
            completion.updated_at = local_now
            return self.update(completion)
        else:
            return self.create(
                event_id=str(event_id),
                is_done=True,
                completed_at=local_now,
                completion_description=description
            )
    
    def mark_undone(self, event_id: str) -> Optional[EventCompletion]:
        """
        Mark an event as undone.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Updated or created EventCompletion instance
        """
        local_now = datetime.now()
        completion = self.get_by_event_id(event_id)
        
        if completion:
            completion.is_done = False
            completion.completed_at = None
            completion.updated_at = local_now
            return self.update(completion)
        else:
            return self.create(
                event_id=str(event_id),
                is_done=False
            )
    
    def is_done(self, event_id: str) -> bool:
        """
        Check if event is marked as done.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if done, False otherwise
        """
        completion = self.get_by_event_id(event_id)
        return completion.is_done if completion else False
    
    def get_completion_timestamp(self, event_id: str) -> Optional[datetime]:
        """
        Get completion timestamp.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Completion timestamp or None
        """
        completion = self.get_by_event_id(event_id)
        if completion and completion.is_done and completion.completed_at:
            return completion.completed_at
        return None
    
    def get_completion_description(self, event_id: str) -> Optional[str]:
        """
        Get completion description.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Description or None
        """
        completion = self.get_by_event_id(event_id)
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
    
    def get_completion_status_batch(self, event_ids: List[str]) -> Dict[str, Tuple[bool, Optional[datetime], Optional[str]]]:
        """
        Get completion status for multiple events.
        
        Args:
            event_ids: List of event IDs
            
        Returns:
            Dictionary mapping event_id to (is_done, completed_at, description) tuple
        """
        try:
            event_ids_str = [str(eid) for eid in event_ids]
            completions = self.db.query(EventCompletion).filter(
                EventCompletion.event_id.in_(event_ids_str)
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

