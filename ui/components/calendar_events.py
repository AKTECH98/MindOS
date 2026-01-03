"""
Calendar Events UI Component
Displays Google Calendar events in card format.
"""
import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional

from services.calendar_service import CalendarService
from services.task_status_service import TaskStatusService
from services.task_session_service import TaskSessionService
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


def render_event_card(event: Dict, is_done: bool = False, completed_at: Optional[datetime] = None, debug_mode: bool = False):
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
        active_session = TaskSessionService.get_active_session(base_event_id)
        is_session_running = active_session is not None
        current_duration = TaskSessionService.get_current_duration(base_event_id)
        
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
        
        # Checkbox and Title row
        col_check, col_title, col_edit = st.columns([1, 8, 1])
        
        with col_check:
            # Checkbox for marking as done
            checkbox_key = f"done_{unique_event_key}"
            new_done_state = st.checkbox(
                "",
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
                    TaskStatusService.mark_event_done(base_event_id)
                    st.rerun()
                else:
                    TaskStatusService.mark_event_undone(base_event_id)
                    st.rerun()
        
        with col_title:
            title = event.get('title', 'No Title')
            if is_done:
                st.markdown(f"### ~~{title}~~ ✅")
            else:
                st.markdown(f"### {title}")
            
            # Show session status and timer
            if is_session_running:
                st.markdown(f"⏱️ **Running:** {format_duration(current_duration)}")
        
        with col_edit:
            # Edit button
            edit_key = f"edit_{unique_event_key}"
            if st.button("✏️", key=edit_key, help="Edit event"):
                st.session_state[f'edit_event_{unique_event_key}'] = True
                st.rerun()
        
        # Time tracking controls
        if not is_done:
            col_start, col_pause = st.columns([1, 1])
            
            with col_start:
                start_key = f"start_{unique_event_key}"
                start_disabled = is_session_running
                if st.button("▶️ Start", key=start_key, use_container_width=True, 
                            disabled=start_disabled):
                    # Extract base event_id for session tracking
                    base_event_id = extract_base_event_id(event_id)
                    TaskSessionService.start_session(base_event_id)
                    st.rerun()
            
            with col_pause:
                pause_key = f"pause_{unique_event_key}"
                pause_disabled = not is_session_running
                if st.button("⏸️ Pause", key=pause_key, use_container_width=True,
                            disabled=pause_disabled):
                    # Extract base event_id for session tracking
                    base_event_id = extract_base_event_id(event_id)
                    TaskSessionService.pause_session(base_event_id)
                    st.rerun()
            
            # Show total time spent
            total_time = TaskSessionService.get_total_time_spent(base_event_id)
            if total_time > 0:
                st.markdown(f"**Total time spent:** {format_duration(total_time)}")
        
        # Time
        time_str = format_time(event)
        st.markdown(f"**🕐 {time_str}**")
        
        # Completion timestamp if done
        if is_done and completed_at:
            completed_str = completed_at.strftime("%Y-%m-%d %I:%M %p")
            st.markdown(f"**✅ Completed on:** {completed_str}")
        
        # Recurrence
        recurrence = event.get('recurrence')
        if recurrence:
            st.markdown(f"**🔄 {recurrence}**")
        elif event.get('raw_event', {}).get('recurringEventId'):
            st.markdown("**🔄 Recurring event** (pattern not available)")
        
        # Debug info
        if debug_mode:
            with st.expander(f"🐛 Debug: {event.get('title', 'Event')}"):
                st.write("**Parsed Recurrence:**", event.get('recurrence') or "None")
                st.write("**Raw event recurrence:**", event.get('raw_event', {}).get('recurrence') or "None")
                st.write("**Recurring Event ID:**", event.get('raw_event', {}).get('recurringEventId') or "None")
                st.json(event.get('raw_event', {}))
        
        # Description
        description = event.get('description', '')
        if description:
            # Limit description length for better UI
            if len(description) > 200:
                description = description[:200] + "..."
            st.markdown(f"**Description:** {description}")
        
        st.divider()
        
        # Show edit form if edit button was clicked
        if st.session_state.get(f'edit_event_{unique_event_key}', False):
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
        st.header("📅 Today's Calendar Events")
        render_authentication_prompt()
        return
    
    # Authenticated UI - show full interface
    st.header("📅 Today's Calendar Events")
    
    # Action buttons and debug toggle
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            # Clear cache to force refresh
            if hasattr(st.session_state, 'calendar_events'):
                del st.session_state.calendar_events
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
        
        # Fetch events (cached for 5 minutes)
        cache_key = 'calendar_events'
        if cache_key not in st.session_state:
            events = calendar_service.get_today_events()
            st.session_state[cache_key] = {
                'events': events,
                'timestamp': datetime.now()
            }
        else:
            # Check if cache is older than 5 minutes
            cache_age = (datetime.now() - st.session_state[cache_key]['timestamp']).total_seconds()
            if cache_age > 300:  # 5 minutes
                events = calendar_service.get_today_events()
                st.session_state[cache_key] = {
                    'events': events,
                    'timestamp': datetime.now()
                }
            else:
                events = st.session_state[cache_key]['events']
        
        # Get completion status for all events (batch query for performance)
        # Extract base event_id (remove timestamp suffix if present) for database lookup
        base_event_ids = []
        event_id_map = {}  # Map base_id -> original_id for lookup
        for event in events:
            event_id = event.get('id')
            if event_id:
                event_id_str = str(event_id)
                # Extract base event_id (remove timestamp suffix if present)
                base_id = extract_base_event_id(event_id_str)
                
                base_event_ids.append(base_id)
                event_id_map[event_id_str] = base_id
        
        completion_status_raw = TaskStatusService.get_completion_status_batch(base_event_ids) if base_event_ids else {}
        
        # Map completion status back to original event_ids (with timestamps)
        completion_status = {}
        for event_id_str, base_id in event_id_map.items():
            completion_status[event_id_str] = completion_status_raw.get(base_id, (False, None))
        
        # Debug: Print completion status
        if debug_mode:
            st.write("**Completion Status Debug:**")
            st.json(completion_status)
        
        # Separate events into pending and done
        pending_events = []
        done_events = []
        
        for event in events:
            event_id = event.get('id')
            if event_id:
                # Use base event_id (without timestamp) for lookup
                # The database stores completion status by base event_id
                event_id_str = str(event_id)
                is_done, completed_at = completion_status.get(event_id_str, (False, None))
                
                # Debug output
                if debug_mode:
                    st.write(f"Event {event_id_str}: is_done={is_done}")
                
                event_data = {
                    'event': event,
                    'is_done': is_done,
                    'completed_at': completed_at
                }
                if is_done:
                    done_events.append(event_data)
                else:
                    pending_events.append(event_data)
        
        # Display events in tabs
        if not events:
            st.info("📭 No events scheduled for today.")
        else:
            # Create tabs for Pending and Done
            tab1, tab2 = st.tabs([f"⏳ Pending ({len(pending_events)})", f"✅ Done ({len(done_events)})"])
            
            with tab1:
                if pending_events:
                    st.markdown(f"**{len(pending_events)} pending event(s):**")
                    st.markdown("")  # Add spacing
                    
                    for event_data in pending_events:
                        render_event_card(
                            event_data['event'],
                            is_done=False,
                            completed_at=None,
                            debug_mode=debug_mode
                        )
                else:
                    st.info("🎉 No pending events! All tasks are completed.")
            
            with tab2:
                if done_events:
                    st.markdown(f"**{len(done_events)} completed event(s):**")
                    st.markdown("")  # Add spacing
                    
                    for event_data in done_events:
                        render_event_card(
                            event_data['event'],
                            is_done=True,
                            completed_at=event_data['completed_at'],
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

