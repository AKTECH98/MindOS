"""
Core business logic for task status and XP management.
"""
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict
from dateutil import tz

from data.repositories.event_completion_repository import EventCompletionRepository
from data.repositories.xp_repository import XPRepository
from data.repositories.daily_xp_deduction_repository import DailyXPDeductionRepository
from core.task_session import TaskSessionCore


def extract_base_event_id(event_id: str) -> str:
    """Extract base event_id by removing timestamp suffix if present."""
    if '_' in str(event_id) and str(event_id).count('_') >= 1:
        parts = str(event_id).rsplit('_', 1)
        if len(parts) == 2 and 'T' in parts[1] and parts[1].endswith('Z'):
            return parts[0]
    return str(event_id)


def _get_date_from_datetime(dt) -> Optional[date]:
    """Extract date from datetime object."""
    if isinstance(dt, datetime):
        return dt.date()
    elif hasattr(dt, 'date'):
        return dt.date()
    elif isinstance(dt, date):
        return dt
    return None


class TaskStatusCore:
    """Core business logic for task completion and XP management."""
    
    XP_PER_TASK = 5
    
    def __init__(self):
        self.completion_repo = EventCompletionRepository()
        self.xp_repo = XPRepository()
        self.deduction_repo = DailyXPDeductionRepository()
    
    def mark_event_done(self, event_id: str, description: str, completion_date: Optional[date] = None) -> bool:
        """Mark event as done and award XP. XP only awarded on first completion per date."""
        if not description or not description.strip():
            raise ValueError("Description is required when marking a task as done")
        
        if completion_date is None:
            completion_date = date.today()
        
        try:
            was_already_done = self.completion_repo.is_done(event_id, completion_date)
            completion = self.completion_repo.mark_done(event_id, description.strip(), completion_date)
            if not completion:
                return False
            
            if not was_already_done:
                try:
                    self.xp_repo.add_xp(
                        self.XP_PER_TASK,
                        event_id=str(event_id),
                        description=f"Task completed: {event_id}"
                    )
                except Exception as e:
                    print(f"Warning: Failed to award XP for task completion: {e}")
            
            return True
        except Exception as e:
            print(f"Error marking event as done: {e}")
            return False
        finally:
            self.completion_repo.close()
            self.xp_repo.close()
    
    def mark_event_undone(self, event_id: str, completion_date: Optional[date] = None) -> bool:
        """Mark event as undone and deduct XP."""
        if completion_date is None:
            completion_date = date.today()
        
        try:
            completion = self.completion_repo.mark_undone(event_id, completion_date)
            if not completion:
                return False
            
            try:
                self.xp_repo.deduct_xp(
                    self.XP_PER_TASK,
                    event_id=str(event_id),
                    description=f"Task undone: {event_id}"
                )
            except Exception as e:
                print(f"Warning: Failed to deduct XP for task undo: {e}")
            
            return True
        except Exception as e:
            print(f"Error marking event as undone: {e}")
            return False
        finally:
            self.completion_repo.close()
            self.xp_repo.close()
    
    def is_event_done(self, event_id: str, completion_date: Optional[date] = None) -> bool:
        """Check if event is marked as done on a specific date."""
        try:
            return self.completion_repo.is_done(event_id, completion_date)
        finally:
            self.completion_repo.close()
    
    def get_completion_timestamp(self, event_id: str, completion_date: Optional[date] = None) -> Optional[datetime]:
        """Get completion timestamp for a specific date."""
        try:
            return self.completion_repo.get_completion_timestamp(event_id, completion_date)
        finally:
            self.completion_repo.close()
    
    def get_completion_description(self, event_id: str, completion_date: Optional[date] = None) -> Optional[str]:
        """Get completion description for a specific date."""
        try:
            return self.completion_repo.get_completion_description(event_id, completion_date)
        finally:
            self.completion_repo.close()
    
    def get_all_completed_events(self) -> List[str]:
        """Get list of all completed event IDs."""
        try:
            return self.completion_repo.get_all_completed_events()
        finally:
            self.completion_repo.close()
    
    def get_completion_status_batch(self, event_ids: List[str], completion_date: Optional[date] = None) -> Dict:
        """Get completion status for multiple events on a specific date."""
        try:
            return self.completion_repo.get_completion_status_batch(event_ids, completion_date)
        finally:
            self.completion_repo.close()
    
    def deduct_xp_for_pending_tasks_from_yesterday(self) -> Dict:
        """Deduct XP for incomplete tasks and handle running sessions."""
        from integrations.gcalendar import CalendarService
        
        try:
            last_run_date = self.deduction_repo.get_last_run_date()
            today = date.today()
            
            if last_run_date:
                days_since = (today - last_run_date).days
                if days_since == 0:
                    return {
                        "success": True,
                        "pending_count": 0,
                        "deducted_count": 0,
                        "total_xp_deducted": 0,
                        "message": "Deduction already ran today"
                    }
                elif days_since < 0:
                    days_since = 1
            else:
                days_since = 1
            
            calendar_service = CalendarService(require_auth=False)
            if calendar_service.service is None:
                return {
                    "success": False,
                    "pending_count": 0,
                    "deducted_count": 0,
                    "total_xp_deducted": 0,
                    "message": "Calendar service not authenticated"
                }
            
            total_pending_count = 0
            total_deducted_count = 0
            total_xp_deducted = 0
            total_running_xp_awarded = 0
            days_processed = []
            
            for day_offset in range(1, days_since + 1):
                check_date = today - timedelta(days=day_offset)
                
                check_datetime = datetime.combine(check_date, datetime.min.time())
                check_datetime = check_datetime.replace(tzinfo=tz.tzlocal())
                start_of_day = check_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = check_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                try:
                    events_result = calendar_service.service.events().list(
                        calendarId='primary',
                        timeMin=start_of_day.isoformat(),
                        timeMax=end_of_day.isoformat(),
                        maxResults=100,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    
                    events = events_result.get('items', [])
                    if not events:
                        continue
                    
                    full_event_ids = [str(event.get('id', '')) for event in events if event.get('id')]
                    base_event_ids_raw = [extract_base_event_id(eid) for eid in full_event_ids]
                    
                    seen = set()
                    base_event_ids = []
                    for base_id in base_event_ids_raw:
                        if base_id not in seen:
                            seen.add(base_id)
                            base_event_ids.append(base_id)
                    
                    completion_status = self.get_completion_status_batch(base_event_ids, check_date)
                    pending_base_ids = []
                    running_tasks_to_complete = []
                    session_core = TaskSessionCore()
                    
                    for base_id in base_event_ids:
                        is_done, completed_at, _ = completion_status.get(base_id, (False, None, None))
                        
                        should_deduct = False
                        if not is_done:
                            should_deduct = True
                        elif completed_at:
                            completed_date = _get_date_from_datetime(completed_at)
                            if completed_date and completed_date != check_date:
                                should_deduct = True
                        elif is_done:
                            should_deduct = True
                        
                        if should_deduct:
                            active_session = session_core.get_active_session(base_id)
                            if active_session is not None:
                                session_status = getattr(active_session, 'status', None)
                                session_start_time = getattr(active_session, 'start_time', None)
                                if session_status == 'running' and session_start_time is not None:
                                    session_start_date = session_start_time.date()
                                    if session_start_date == check_date:
                                        running_tasks_to_complete.append(base_id)
                                    else:
                                        pending_base_ids.append(base_id)
                                else:
                                    pending_base_ids.append(base_id)
                            else:
                                pending_base_ids.append(base_id)
                    
                    running_completed_count = 0
                    running_xp_awarded = 0
                    for base_id in running_tasks_to_complete:
                        try:
                            completion_date = check_date
                            completed_at_datetime = datetime.combine(completion_date, datetime.max.time()).replace(microsecond=0) - timedelta(seconds=1)
                            
                            was_already_done = self.completion_repo.is_done(base_id, completion_date)
                            pause_success = session_core.pause_session(base_id)
                            
                            if pause_success:
                                completion = self.completion_repo.mark_done(
                                    base_id,
                                    description="Stopped by system (forgot to stop timer)",
                                    completion_date=completion_date,
                                    completed_at_datetime=completed_at_datetime
                                )
                                if completion:
                                    if not was_already_done:
                                        try:
                                            self.xp_repo.add_xp(
                                                self.XP_PER_TASK,
                                                event_id=str(base_id),
                                                description=f"Task completed: {base_id}"
                                            )
                                            running_xp_awarded += self.XP_PER_TASK
                                        except Exception as e:
                                            print(f"Warning: Failed to award XP for running task completion: {e}")
                                    running_completed_count += 1
                        except Exception as e:
                            print(f"Error handling running task {base_id} on {check_date}: {e}")
                            pending_base_ids.append(base_id)
                    
                    session_core.session_repo.close()
                    
                    day_deducted_count = 0
                    day_xp_deducted = 0
                    
                    for base_id in pending_base_ids:
                        try:
                            success = self.xp_repo.deduct_xp(
                                self.XP_PER_TASK,
                                event_id=base_id,
                                description=f"Task from {check_date} not completed: {base_id}"
                            )
                            if success:
                                day_deducted_count += 1
                                day_xp_deducted += self.XP_PER_TASK
                        except Exception as e:
                            print(f"Error deducting XP for event {base_id} on {check_date}: {e}")
                    
                    total_pending_count += len(pending_base_ids) + running_completed_count
                    total_deducted_count += day_deducted_count
                    total_xp_deducted += day_xp_deducted
                    total_running_xp_awarded += running_xp_awarded
                    
                    days_processed.append({
                        'date': check_date,
                        'pending': len(pending_base_ids),
                        'running_stopped': running_completed_count,
                        'running_xp_awarded': running_xp_awarded,
                        'deducted': day_deducted_count,
                        'xp': day_xp_deducted
                    })
                    
                except Exception as e:
                    print(f"Error processing day {check_date}: {e}")
                    continue
            
            self.deduction_repo.record_deduction_run(
                total_pending_count,
                total_deducted_count,
                total_xp_deducted
            )
            
            running_info = ""
            if total_running_xp_awarded > 0:
                running_info = f" Stopped {sum(d.get('running_stopped', 0) for d in days_processed)} running task(s) and awarded {total_running_xp_awarded} XP."
            
            if total_deducted_count == 0:
                message = f"No pending tasks from {'yesterday' if days_since == 1 else f'the last {days_since} days'}.{running_info}"
            else:
                message = f"Deducted {total_xp_deducted} XP for {total_deducted_count} pending task(s) from {'yesterday' if days_since == 1 else f'the last {days_since} days'}.{running_info}"
            
            return {
                "success": True,
                "pending_count": total_pending_count,
                "deducted_count": total_deducted_count,
                "total_xp_deducted": total_xp_deducted,
                "running_stopped_count": sum(d.get('running_stopped', 0) for d in days_processed),
                "running_xp_awarded": total_running_xp_awarded,
                "days_processed": days_since,
                "days_breakdown": days_processed,
                "message": message
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
        """Check if daily deduction should run (hasn't run today yet)."""
        try:
            return not self.deduction_repo.has_run_today()
        finally:
            self.deduction_repo.close()
