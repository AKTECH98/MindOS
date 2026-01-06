"""
Calendar Events UI Component
Displays Google Calendar events in card format.
"""
import streamlit as st
from datetime import datetime, date
from typing import List, Dict, Optional

from integrations.gcalendar import CalendarService
from core.task_status import TaskStatusCore, extract_base_event_id
from core.task_session import TaskSessionCore
from ui.components.add_calendar_event import render_add_event_form
from ui.components.edit_calendar_event import render_edit_event_form
from ui.components.authenticate import render_authentication_prompt
from data.db import init_db


@st.cache_resource
def get_calendar_service():
    """Get cached calendar service instance."""
    return CalendarService()


def format_time(event: Dict) -> str:
    """
    Format event time for display.
    
    Args:
        event: Event dictionary with start_time and end_time
        
    Returns:
        Formatted time string
    """
    start_time = event.get('start_time')
    end_time = event.get('end_time')
    is_all_day = event.get('is_all_day', False)
    
    if not start_time:
        return "Time TBD"
    
    if is_all_day:
        return "All Day"
    
    # Format time
    start_str = start_time.strftime("%I:%M %p").lstrip('0')
    if end_time:
        end_str = end_time.strftime("%I:%M %p").lstrip('0')
        return f"{start_str} - {end_str}"
    else:
        return start_str


def render_event_card(event: Dict, is_done: bool = False, completed_at: Optional[datetime] = None, completion_description: Optional[str] = None, debug_mode: bool = False):
    """
    Render a single event as a card with checkbox and edit button.
    
    Args:
        event: Event dictionary with parsed details
        is_done: Whether the event is marked as done
        completed_at: Timestamp when event was completed (if done)
        debug_mode: Whether to show debug information
    """
    event_id = event.get('id')
    if not event_id:
        return
    
    # Create unique key for this event instance (use start_time to differentiate recurring instances)
    start_time = event.get('start_time')
    unique_key_suffix = ""
    if start_time:
        # Use ISO format timestamp for uniqueness
        unique_key_suffix = f"_{start_time.isoformat()}"
    unique_event_key = f"{event_id}{unique_key_suffix}"
    
    # Use Streamlit's native container with better styling
    with st.container():
        # Card styling - different style if done
        card_style = "border-left: 4px solid #28a745;" if is_done else "border-left: 4px solid #1f77b4;"
        opacity = "opacity: 0.7;" if is_done else ""
        
        st.markdown(
            f"""
            <style>
            .event-card {{
                {card_style}
                padding: 1rem;
                margin: 0.5rem 0;
                background-color: var(--background-color);
                border-radius: 4px;
                {opacity}
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Extract base event_id for session tracking (remove timestamp suffix if present)
        base_event_id = extract_base_event_id(event_id)
        
        # Get active session status (only running sessions are active)
        session_core = TaskSessionCore()
        active_session = session_core.get_active_session(base_event_id)
        is_session_running = active_session is not None
        current_duration = session_core.get_current_duration(base_event_id)
        
        # Format duration for display
        def format_duration(seconds: Optional[int]) -> str:
            if seconds is None or seconds == 0:
                return "0:00"
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            if hours > 0:
                return f"{hours}:{minutes:02d}:{secs:02d}"
            return f"{minutes}:{secs:02d}"
        
        # Check if we're in the middle of showing description input
        showing_description = st.session_state.get(f'show_description_input_{unique_event_key}', False)
        
        # Checkbox and Title row
        if is_done:
            # For done tasks: checkbox only (no edit button)
            col_check, col_title = st.columns([1, 11])
            col_edit = None  # Not used for done tasks
        else:
            # For pending tasks: checkbox, title, and edit button
            col_check, col_title, col_edit = st.columns([1, 8, 1])
        
        with col_check:
            # Checkbox for marking as done
            checkbox_key = f"done_{unique_event_key}"
            
            # Only show checkbox if not showing description input
            if not showing_description:
                new_done_state = st.checkbox(
                    "Mark as done",
                    value=is_done,
                    key=checkbox_key,
                    label_visibility="collapsed",
                    disabled=is_session_running
                )
                
                # Handle checkbox state change
                if new_done_state != is_done:
                    # Extract base event_id for completion tracking
                    base_event_id = extract_base_event_id(event_id)
                    
                    if new_done_state:
                        # Show description input when marking as done
                        st.session_state[f'show_description_input_{unique_event_key}'] = True
                        st.rerun()
                    else:
                        # Unchecking - mark as undone immediately
                        task_core = TaskStatusCore()
                        task_core.mark_event_undone(base_event_id)
                        if 'calendar_events' in st.session_state:
                            del st.session_state['calendar_events']
                        # Clear XP bar cache if it exists
                        if hasattr(st.session_state, 'xp_info'):
                            del st.session_state['xp_info']
                        st.rerun()
            else:
                # Show a disabled checkbox to maintain layout
                st.checkbox(
                    "Mark as done",
                    value=True,
                    key=f"disabled_{checkbox_key}",
                    label_visibility="collapsed",
                    disabled=True
                )
        
        # Show description input form when marking as done
        if st.session_state.get(f'show_description_input_{unique_event_key}', False) and not is_done:
            st.info("📝 **Required:** Please describe what you accomplished:")
            description = st.text_area(
                "Completion Description *",
                key=f"description_input_{unique_event_key}",
                placeholder="Enter what you accomplished in this task... (This field is required)",
                height=100,
                label_visibility="collapsed"
            )
            
            col_save, col_cancel = st.columns([1, 1])
            with col_save:
                if st.button("✅ Save", key=f"save_description_{unique_event_key}", use_container_width=True, type="primary"):
                    base_event_id = extract_base_event_id(event_id)
                    description_text = description.strip() if description else None
                    
                    # Validate that description is provided
                    if not description_text or len(description_text) == 0:
                        st.error("❌ Description is required. Please describe what you accomplished before saving.")
                    else:
                        try:
                            task_core = TaskStatusCore()
                            success = task_core.mark_event_done(base_event_id, description=description_text)
                            if success:
                                # Clear all related state
                                st.session_state[f'show_description_input_{unique_event_key}'] = False
                                # Clear the description input value
                                if f"description_input_{unique_event_key}" in st.session_state:
                                    del st.session_state[f"description_input_{unique_event_key}"]
                                # Clear cache to force refresh
                                if 'calendar_events' in st.session_state:
                                    del st.session_state['calendar_events']
                                # Clear XP bar cache if it exists
                                if hasattr(st.session_state, 'xp_info'):
                                    del st.session_state['xp_info']
                                st.rerun()
                            else:
                                st.error("Failed to save completion. Please try again.")
                        except ValueError as e:
                            st.error(f"❌ {str(e)}")
                        except Exception as e:
                            st.error(f"Failed to save completion: {str(e)}")
            with col_cancel:
                if st.button("❌ Cancel", key=f"cancel_description_{unique_event_key}", use_container_width=True):
                    # Just clear the description input flag - checkbox will revert naturally
                    st.session_state[f'show_description_input_{unique_event_key}'] = False
                    if 'calendar_events' in st.session_state:
                        del st.session_state['calendar_events']
                    st.rerun()
        
        with col_title:
            title = event.get('title', 'No Title')
            if is_done:
                st.markdown(f"### ~~{title}~~")
            else:
                st.markdown(f"### {title}")
            
            # Show session status and timer (only for pending tasks)
            if not is_done and is_session_running:
                st.markdown(f"⏱️ **Running:** {format_duration(current_duration)}")
        
        # Edit button (only for pending tasks and when description input is not showing)
        if not is_done and not showing_description and col_edit is not None:
            with col_edit:
                edit_key = f"edit_{unique_event_key}"
                if st.button("✏️", key=edit_key, help="Edit event"):
                    st.session_state[f'edit_event_{unique_event_key}'] = True
                    st.rerun()
        
        # Time tracking controls (only for pending tasks and when description input is not showing)
        if not is_done and not showing_description:
            col_start, col_pause = st.columns([1, 1])
            
            with col_start:
                start_key = f"start_{unique_event_key}"
                start_disabled = is_session_running
                if st.button("▶️ Start", key=start_key, use_container_width=True, 
                            disabled=start_disabled):
                    # Extract base event_id for session tracking
                    base_event_id = extract_base_event_id(event_id)
                    session_core = TaskSessionCore()
                    session_core.start_session(base_event_id)
                    st.rerun()
            
            with col_pause:
                pause_key = f"pause_{unique_event_key}"
                pause_disabled = not is_session_running
                if st.button("⏸️ Pause", key=pause_key, use_container_width=True,
                            disabled=pause_disabled):
                    # Extract base event_id for session tracking
                    base_event_id = extract_base_event_id(event_id)
                    session_core = TaskSessionCore()
                    session_core.pause_session(base_event_id)
                    st.rerun()
            
            # Show total time spent
            base_event_id = extract_base_event_id(event_id)
            session_core = TaskSessionCore()
            total_time = session_core.get_total_time_spent(base_event_id)
            if total_time > 0:
                st.markdown(f"**Total time spent:** {format_duration(total_time)}")
        
        # For done tasks, only show completion info; for pending tasks, show all details
        if is_done:
            # Completion timestamp if done (show prominently for completed tasks)
            if completed_at:
                completed_str = completed_at.strftime("%Y-%m-%d %I:%M %p")
                st.markdown(f"**Completed on:** {completed_str}")
            
            # Completion description if done
            if completion_description:
                st.markdown(f"**📝 What I accomplished:**")
                st.info(completion_description)
        else:
            # For pending tasks, show all details
            # Time
            time_str = format_time(event)
            st.markdown(f"**🕐 {time_str}**")
            
            # Recurrence
            recurrence = event.get('recurrence')
            if recurrence:
                st.markdown(f"**🔄 {recurrence}**")
            elif event.get('raw_event', {}).get('recurringEventId'):
                st.markdown("**🔄 Recurring event** (pattern not available)")
            
            # Description
            description = event.get('description', '')
            if description:
                # Limit description length for better UI
                if len(description) > 200:
                    description = description[:200] + "..."
                st.markdown(f"**Description:** {description}")
        
        # Debug info (show for both pending and done)
        if debug_mode:
            with st.expander(f"🐛 Debug: {event.get('title', 'Event')}"):
                st.write("**Parsed Recurrence:**", event.get('recurrence') or "None")
                st.write("**Raw event recurrence:**", event.get('raw_event', {}).get('recurrence') or "None")
                st.write("**Recurring Event ID:**", event.get('raw_event', {}).get('recurringEventId') or "None")
                st.json(event.get('raw_event', {}))
        
        st.divider()
        
        # Show edit form if edit button was clicked (only for pending tasks)
        if not is_done and st.session_state.get(f'edit_event_{unique_event_key}', False):
            calendar_service = get_calendar_service()
            result = render_edit_event_form(calendar_service, event)
            if result:
                # Check if event was deleted
                if isinstance(result, dict) and result.get('deleted'):
                    # Event deleted successfully, hide form and refresh
                    st.session_state[f'edit_event_{unique_event_key}'] = False
                    if 'calendar_events' in st.session_state:
                        del st.session_state['calendar_events']
                    st.rerun()
                else:
                    # Event updated successfully, hide form and refresh
                    st.session_state[f'edit_event_{unique_event_key}'] = False
                    if 'calendar_events' in st.session_state:
                        del st.session_state['calendar_events']
                    st.rerun()
            elif st.button("❌ Cancel Edit", key=f"cancel_edit_{unique_event_key}"):
                st.session_state[f'edit_event_{unique_event_key}'] = False
                st.rerun()


def render_calendar_events():
    """
    Main function to render calendar events in card format.
    Fetches today's events and displays them with task management features.
    """
    # Initialize database
    try:
        init_db()
    except Exception as e:
        st.warning(f"⚠️ Database initialization warning: {e}")
    
    # Check authentication status first - automatically start auth if needed
    is_authenticated = False
    try:
        calendar_service = get_calendar_service()
        if calendar_service.service is not None:
            is_authenticated = True
    except ValueError:
        is_authenticated = False
    
    # If not authenticated, automatically show authentication prompt
    if not is_authenticated:
        today = date.today()
        today_str = today.strftime("%B %d, %Y")
        st.header(f"{today_str} - Tasks")
        render_authentication_prompt()
        return
    
    # Authenticated UI - show full interface
    # Date picker for selecting which date to view
    today = date.today()
    
    # Put date picker in a compact column to prevent stretching
    col_date, col_header = st.columns([1, 4])
    with col_date:
        selected_date = st.date_input(
            "Select Date",
            value=today,
            key="selected_date",
            help="Choose a date to view tasks"
        )
    
    # Format selected date for header
    selected_date_str = selected_date.strftime("%B %d, %Y")
    with col_header:
        st.header(f"{selected_date_str} - Tasks")
    
    # Action buttons and debug toggle
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            # Clear cache for selected date to force refresh
            cache_key = f'calendar_events_{selected_date.isoformat()}'
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            # Clear the cached calendar service to pick up code changes
            get_calendar_service.clear()
            st.rerun()
    with col2:
        if st.button("➕ Add Event", use_container_width=True):
            st.session_state.show_add_event_form = True
    with col3:
        debug_mode = st.checkbox("🐛 Debug", help="Show raw event data for debugging")
    
    st.divider()
    
    # Show add event form if requested
    if st.session_state.get('show_add_event_form', False):
        calendar_service = get_calendar_service()
        created_event = render_add_event_form(calendar_service)
        if created_event:
            # Event created successfully, hide form and refresh
            st.session_state.show_add_event_form = False
            st.rerun()
        elif st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_add_event_form = False
            st.rerun()
        st.divider()
    
    try:
        # Initialize calendar service (cached) - we already checked auth above
        calendar_service = get_calendar_service()
        if calendar_service.service is None:
            st.error("Calendar service not initialized")
            return
        
        # Fetch events for selected date (cached per date for 5 minutes)
        cache_key = f'calendar_events_{selected_date.isoformat()}'
        if cache_key not in st.session_state:
            events = calendar_service.get_events_for_date(selected_date)
            st.session_state[cache_key] = {
                'events': events,
                'timestamp': datetime.now()
            }
        else:
            # Check if cache is older than 5 minutes
            cache_age = (datetime.now() - st.session_state[cache_key]['timestamp']).total_seconds()
            if cache_age > 300:  # 5 minutes
                events = calendar_service.get_events_for_date(selected_date)
                st.session_state[cache_key] = {
                    'events': events,
                    'timestamp': datetime.now()
                }
            else:
                events = st.session_state[cache_key]['events']
        
        # Get completion status for all events (batch query for performance)
        # Extract base event_id (remove timestamp suffix if present) for database lookup
        base_event_ids_set = set()  # Use set to ensure uniqueness
        event_id_map = {}  # Map event_id_str -> base_id for lookup
        for event in events:
            event_id = event.get('id')
            if event_id:
                event_id_str = str(event_id)
                # Extract base event_id (remove timestamp suffix if present)
                base_id = extract_base_event_id(event_id_str)
                
                base_event_ids_set.add(base_id)
                event_id_map[event_id_str] = base_id
        
        base_event_ids = list(base_event_ids_set)
        
        task_core = TaskStatusCore()
        completion_status_raw = task_core.get_completion_status_batch(base_event_ids) if base_event_ids else {}
        
        # Debug: Print raw completion status
        if debug_mode:
            st.write("**Raw Completion Status (by base_id):**")
            st.json(completion_status_raw)
            st.write("**Event ID Mapping:**")
            st.json(event_id_map)
            st.write("**Base Event IDs queried:**")
            st.json(base_event_ids)
        
        # Map completion status back to original event_ids (with timestamps)
        # All events with the same base_id will share the same completion status
        completion_status = {}
        for event_id_str, base_id in event_id_map.items():
            # Try to get status by base_id
            status_data = completion_status_raw.get(base_id, (False, None, None))
            
            # Also try direct lookup in case there's a mismatch
            if status_data == (False, None, None) and event_id_str in completion_status_raw:
                status_data = completion_status_raw[event_id_str]
            
            # Handle both old format (2-tuple) and new format (3-tuple)
            if len(status_data) == 2:
                is_done, completed_at = status_data
                completion_status[event_id_str] = (is_done, completed_at, None)
            else:
                completion_status[event_id_str] = status_data
        
        # Debug: Print completion status
        if debug_mode:
            st.write("**Completion Status Debug:**")
            st.json(completion_status)
        
        # Separate events into pending and done
        # A task is only considered "done" if it was completed on the selected date
        pending_events = []
        done_events = []
        
        for event in events:
            event_id = event.get('id')
            if event_id:
                # Use base event_id (without timestamp) for lookup
                # The database stores completion status by base event_id
                event_id_str = str(event_id)
                status_data = completion_status.get(event_id_str, (False, None, None))
                # Handle both old format (2-tuple) and new format (3-tuple)
                if len(status_data) == 2:
                    is_done, completed_at = status_data
                    completion_description = None
                else:
                    is_done, completed_at, completion_description = status_data
                
                # Check if task was completed on the selected date
                # Only show as "done" if completed on the selected date
                is_done_today = False
                if is_done and completed_at:
                    # Compare dates (ignore time)
                    if isinstance(completed_at, datetime):
                        completed_date = completed_at.date()
                    elif hasattr(completed_at, 'date'):
                        completed_date = completed_at.date()
                    else:
                        completed_date = completed_at
                    if completed_date == selected_date:
                        is_done_today = True
                
                # Debug output
                if debug_mode:
                    st.write(f"Event {event_id_str}: is_done={is_done}, completed_at={completed_at}, is_done_today={is_done_today}")
                
                event_data = {
                    'event': event,
                    'is_done': is_done_today,  # Only true if completed on selected date
                    'completed_at': completed_at if is_done_today else None,
                    'completion_description': completion_description if is_done_today else None
                }
                if is_done_today:
                    done_events.append(event_data)
                else:
                    pending_events.append(event_data)
        
        # Display events in split screen (half for pending, half for done)
        if not events:
            if selected_date == today:
                st.info("📭 No events scheduled for today.")
            else:
                st.info(f"📭 No events scheduled for {selected_date_str}.")
        else:
            # Create two columns to split the screen in half with margin between them
            col_pending, col_spacer, col_done = st.columns([1, 0.1, 1])
            
            with col_pending:
                st.subheader(f"⏳ Pending Tasks ({len(pending_events)})")
                if pending_events:
                    for event_data in pending_events:
                        render_event_card(
                            event_data['event'],
                            is_done=False,
                            completed_at=None,
                            completion_description=None,
                            debug_mode=debug_mode
                        )
                else:
                    st.info("🎉 No pending events! All tasks are completed.")
            
            with col_spacer:
                # Empty spacer column for margin
                st.write("")
            
            with col_done:
                st.subheader(f"✅ Done Tasks ({len(done_events)})")
                if done_events:
                    for event_data in done_events:
                        render_event_card(
                            event_data['event'],
                            is_done=True,
                            completed_at=event_data['completed_at'],
                            completion_description=event_data.get('completion_description'),
                            debug_mode=debug_mode
                        )
                else:
                    st.info("📝 No completed events yet.")
        
    except ValueError as e:
        # This should not happen now since we handle auth above, but keep as fallback
        if "authentication" in str(e).lower() or "credential" in str(e).lower():
            st.info("👆 Click the sync button (🔄) above to authenticate and load your calendar events.")
        else:
            st.error(f"❌ Error: {str(e)}")
    except Exception as e:
        st.error(f"❌ Error loading calendar events: {str(e)}")
        st.info("Please check your internet connection and try again.")

