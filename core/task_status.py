"""
Core business logic for task status and XP management.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dateutil import tz

from data.repositories.event_completion_repository import EventCompletionRepository
from data.repositories.xp_repository import XPRepository
from data.repositories.daily_xp_deduction_repository import DailyXPDeductionRepository


def extract_base_event_id(event_id: str) -> str:
    """
    Extract base event_id by removing timestamp suffix if present.
    
    Args:
        event_id: Event ID that may have a timestamp suffix
        
    Returns:
        Base event ID without timestamp suffix
    """
    if '_' in str(event_id) and str(event_id).count('_') >= 1:
        parts = str(event_id).rsplit('_', 1)
        if len(parts) == 2 and 'T' in parts[1] and parts[1].endswith('Z'):
            return parts[0]
    return str(event_id)


class TaskStatusCore:
    """Core business logic for task completion and XP management."""
    
    XP_PER_TASK = 5
    
    def __init__(self):
        self.completion_repo = EventCompletionRepository()
        self.xp_repo = XPRepository()
        self.deduction_repo = DailyXPDeductionRepository()
    
    def mark_event_done(self, event_id: str, description: str) -> bool:
        """
        Mark event as done and award XP.
        Business rule: Completing a task awards XP points.
        Business rule: Description is required when marking a task as done.
        
        Args:
            event_id: Google Calendar event ID
            description: Required completion description (cannot be empty)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If description is empty or None
        """
        # Validate that description is provided
        if not description or not description.strip():
            raise ValueError("Description is required when marking a task as done")
        
        try:
            # 1. Update completion status (data operation)
            completion = self.completion_repo.mark_done(event_id, description.strip())
            if not completion:
                return False
            
            # 2. Award XP (business rule: completing tasks gives XP)
            try:
                self.xp_repo.add_xp(
                    self.XP_PER_TASK,
                    event_id=str(event_id),
                    description=f"Task completed: {event_id}"
                )
            except Exception as e:
                # Business rule: Don't fail task completion if XP fails
                print(f"Warning: Failed to award XP for task completion: {e}")
            
            return True
        except Exception as e:
            print(f"Error marking event as done: {e}")
            return False
        finally:
            self.completion_repo.close()
            self.xp_repo.close()
    
    def mark_event_undone(self, event_id: str) -> bool:
        """
        Mark event as undone and deduct XP.
        Business rule: Undoing a task deducts XP points.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # 1. Update completion status
            completion = self.completion_repo.mark_undone(event_id)
            if not completion:
                return False
            
            # 2. Deduct XP (business rule: undoing tasks deducts XP)
            try:
                self.xp_repo.deduct_xp(
                    self.XP_PER_TASK,
                    event_id=str(event_id),
                    description=f"Task undone: {event_id}"
                )
            except Exception as e:
                # Business rule: Don't fail task undo if XP fails
                print(f"Warning: Failed to deduct XP for task undo: {e}")
            
            return True
        except Exception as e:
            print(f"Error marking event as undone: {e}")
            return False
        finally:
            self.completion_repo.close()
            self.xp_repo.close()
    
    def is_event_done(self, event_id: str) -> bool:
        """
        Check if event is marked as done.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if done, False otherwise
        """
        try:
            return self.completion_repo.is_done(event_id)
        finally:
            self.completion_repo.close()
    
    def get_completion_timestamp(self, event_id: str) -> Optional[datetime]:
        """
        Get completion timestamp.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Completion timestamp or None
        """
        try:
            return self.completion_repo.get_completion_timestamp(event_id)
        finally:
            self.completion_repo.close()
    
    def get_completion_description(self, event_id: str) -> Optional[str]:
        """
        Get completion description.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Description or None
        """
        try:
            return self.completion_repo.get_completion_description(event_id)
        finally:
            self.completion_repo.close()
    
    def get_all_completed_events(self) -> List[str]:
        """
        Get list of all completed event IDs.
        
        Returns:
            List of event IDs
        """
        try:
            return self.completion_repo.get_all_completed_events()
        finally:
            self.completion_repo.close()
    
    def get_completion_status_batch(self, event_ids: List[str]) -> Dict:
        """
        Get completion status for multiple events.
        
        Args:
            event_ids: List of event IDs
            
        Returns:
            Dictionary mapping event_id to (is_done, completed_at, description) tuple
        """
        try:
            return self.completion_repo.get_completion_status_batch(event_ids)
        finally:
            self.completion_repo.close()
    
    def deduct_xp_for_pending_tasks_from_yesterday(self) -> Dict:
        """
        Business rule: Tasks not completed yesterday lose XP.
        Complex orchestration of calendar + completion + XP.
        
        Returns:
            Dictionary with success status and details
        """
        from integrations.gcalendar import CalendarService
        
        try:
            # Get yesterday's date range
            now = datetime.now(tz.tzlocal())
            yesterday = now - timedelta(days=1)
            start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_yesterday = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Fetch yesterday's events from calendar
            calendar_service = CalendarService(require_auth=False)
            if calendar_service.service is None:
                return {
                    "success": False,
                    "pending_count": 0,
                    "deducted_count": 0,
                    "total_xp_deducted": 0,
                    "message": "Calendar service not authenticated"
                }
            
            # Get events from yesterday
            time_min = start_of_yesterday.isoformat()
            time_max = end_of_yesterday.isoformat()
            
            events_result = calendar_service.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                return {
                    "success": True,
                    "pending_count": 0,
                    "deducted_count": 0,
                    "total_xp_deducted": 0,
                    "message": "No events found for yesterday"
                }
            
            # Get completion status for all yesterday's events
            # Extract base event IDs to ensure consistency (completions are stored by base ID)
            full_event_ids = [str(event.get('id', '')) for event in events if event.get('id')]
            base_event_ids_raw = [extract_base_event_id(eid) for eid in full_event_ids]
            
            # Deduplicate base IDs (multiple instances of recurring events share the same base ID)
            # Use a set to preserve order while removing duplicates
            seen = set()
            base_event_ids = []
            for base_id in base_event_ids_raw:
                if base_id not in seen:
                    seen.add(base_id)
                    base_event_ids.append(base_id)
            
            # Get completion status using base IDs (completions are stored by base ID)
            completion_status = self.get_completion_status_batch(base_event_ids)
            
            # Find pending tasks (not completed yesterday)
            # Only deduct XP for tasks that were NOT completed yesterday
            pending_base_ids = []
            yesterday_date = yesterday.date()
            
            for base_id in base_event_ids:
                is_done, completed_at, _ = completion_status.get(base_id, (False, None, None))
                
                # Task is pending (should deduct XP) if:
                # 1. Not marked as done, OR
                # 2. Marked as done but completed on a different date (not yesterday)
                should_deduct = False
                if not is_done:
                    # Not done, so should deduct
                    should_deduct = True
                elif completed_at:
                    # Check if completed yesterday
                    if isinstance(completed_at, datetime):
                        completed_date = completed_at.date()
                    elif hasattr(completed_at, 'date'):
                        completed_date = completed_at.date()
                    else:
                        completed_date = completed_at
                    
                    # Only deduct if NOT completed yesterday
                    if completed_date != yesterday_date:
                        should_deduct = True
                # If is_done but no completed_at, treat as not completed yesterday
                elif is_done:
                    # Done but no timestamp - shouldn't happen, but treat as pending to be safe
                    should_deduct = True
                
                if should_deduct:
                    pending_base_ids.append(base_id)
            
            if not pending_base_ids:
                return {
                    "success": True,
                    "pending_count": 0,
                    "deducted_count": 0,
                    "total_xp_deducted": 0,
                    "message": f"All {len(events)} tasks from yesterday were completed!"
                }
            
            # Deduct XP for each pending task (business rule)
            # Use base event IDs consistently to match how completions are stored
            deducted_count = 0
            total_xp_deducted = 0
            
            for base_id in pending_base_ids:
                try:
                    success = self.xp_repo.deduct_xp(
                        self.XP_PER_TASK,
                        event_id=base_id,  # Use base ID consistently
                        description=f"Task from yesterday not completed: {base_id}"
                    )
                    if success:
                        deducted_count += 1
                        total_xp_deducted += self.XP_PER_TASK
                except Exception as e:
                    print(f"Error deducting XP for event {base_id}: {e}")
                    # Continue with other tasks
            
            # Record that deduction has run for today
            self.deduction_repo.record_deduction_run(
                len(pending_base_ids),
                deducted_count,
                total_xp_deducted
            )
            
            return {
                "success": True,
                "pending_count": len(pending_base_ids),
                "deducted_count": deducted_count,
                "total_xp_deducted": total_xp_deducted,
                "message": f"Deducted {total_xp_deducted} XP for {deducted_count} pending task(s) from yesterday"
            }
            
        except Exception as e:
            print(f"Error deducting XP for pending tasks: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "pending_count": 0,
                "deducted_count": 0,
                "total_xp_deducted": 0,
                "message": f"Error: {str(e)}"
            }
        finally:
            self.completion_repo.close()
            self.xp_repo.close()
            self.deduction_repo.close()
    
    def should_run_daily_deduction(self) -> bool:
        """
        Check if daily deduction should run (hasn't run today yet).
        
        Returns:
            True if deduction should run, False if it already ran today
        """
        try:
            return not self.deduction_repo.has_run_today()
        finally:
            self.deduction_repo.close()

