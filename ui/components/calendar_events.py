"""Calendar events: list and manage Google Calendar events."""
import streamlit as st
from datetime import datetime, date
from typing import List, Dict, Optional

from integrations.gcalendar import CalendarService
from core.task_status import TaskStatusCore, extract_base_event_id
from core.task_session import TaskSessionCore
from ui.components.add_calendar_event import render_add_event_form
from ui.components.edit_calendar_event import render_edit_event_form
from ui.components.authenticate import render_authentication_prompt
from ui.theme import SMART_BLUE, FONT_INTER


@st.cache_resource
def get_calendar_service():
    """Get cached calendar service instance."""
    return CalendarService()


def format_time(event: Dict) -> str:
    """Format event start/end time for display."""
    start_time = event.get('start_time')
    end_time = event.get('end_time')
    is_all_day = event.get('is_all_day', False)
    
    if not start_time:
        return "Time TBD"
    
    if is_all_day:
        return "All Day"
    start_str = start_time.strftime("%I:%M %p").lstrip('0')
    if end_time:
        end_str = end_time.strftime("%I:%M %p").lstrip('0')
        return f"{start_str} - {end_str}"
    else:
        return start_str


def render_event_card(event: Dict, is_done: bool = False, completed_at: Optional[datetime] = None, completion_description: Optional[str] = None, debug_mode: bool = False, selected_date: Optional[date] = None):
    """Render one event card with checkbox, edit, and time-tracking controls."""
    event_id = event.get('id')
    if not event_id:
        return
    
    start_time = event.get('start_time')
    unique_key_suffix = ""
    if start_time:
        unique_key_suffix = f"_{start_time.isoformat()}"
    unique_event_key = f"{event_id}{unique_key_suffix}"

    with st.container():
        opacity = "opacity: 0.7;" if is_done else ""
        st.markdown(
            f"""
            <style>
            .event-card {{
                border-left: 4px solid var(--smart-blue);
                padding: 1rem;
                margin: 0.5rem 0;
                background-color: var(--slate-bg);
                border: 1px solid var(--slate-border);
                border-radius: 8px;
                {opacity}
                background-image: 
                    linear-gradient(rgba(100, 116, 139, 0.1) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(100, 116, 139, 0.1) 1px, transparent 1px);
                background-size: 40px 40px;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

        base_event_id = extract_base_event_id(event_id)
        session_core = TaskSessionCore()
        active_session = session_core.get_active_session(base_event_id)
        is_session_running = active_session is not None
        current_duration = session_core.get_current_duration(base_event_id)

        def format_duration(seconds: Optional[int]) -> str:
            if seconds is None or seconds == 0:
                return "0:00"
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            if hours > 0:
                return f"{hours}:{minutes:02d}:{secs:02d}"
            return f"{minutes}:{secs:02d}"
        showing_description = st.session_state.get(f'show_description_input_{unique_event_key}', False)
        if is_done:
            col_check, col_title = st.columns([1, 11])
            col_edit = None
        else:
            col_check, col_title, col_edit = st.columns([1, 8, 1])
        
        with col_check:
            checkbox_key = f"done_{unique_event_key}"
            if not showing_description:
                new_done_state = st.checkbox(
                    "Mark as done",
                    value=is_done,
                    key=checkbox_key,
                    label_visibility="collapsed",
                    disabled=is_session_running
                )
                if new_done_state != is_done:
                    base_event_id = extract_base_event_id(event_id)
                    if new_done_state:
                        # Show description input when marking as done
                        st.session_state[f'show_description_input_{unique_event_key}'] = True
                        st.rerun()
                    else:
                        task_core = TaskStatusCore()
                        task_core.mark_event_undone(base_event_id)
                        if 'calendar_events' in st.session_state:
                            del st.session_state['calendar_events']
                        if hasattr(st.session_state, 'xp_info'):
                            del st.session_state['xp_info']
                        st.rerun()
            else:
                st.checkbox(
                    "Mark as done",
                    value=True,
                    key=f"disabled_{checkbox_key}",
                    label_visibility="collapsed",
                    disabled=True
                )
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
                    if not description_text or len(description_text) == 0:
                        st.error("❌ Description is required. Please describe what you accomplished before saving.")
                    else:
                        try:
                            task_core = TaskStatusCore()
                            success = task_core.mark_event_done(base_event_id, description=description_text)
                            if success:
                                st.session_state[f'show_description_input_{unique_event_key}'] = False
                                if f"description_input_{unique_event_key}" in st.session_state:
                                    del st.session_state[f"description_input_{unique_event_key}"]
                                if 'calendar_events' in st.session_state:
                                    del st.session_state['calendar_events']
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
            if not is_done and is_session_running:
                st.markdown(f"⏱️ **Running:** {format_duration(current_duration)}")
        if not is_done and not showing_description and col_edit is not None:
            with col_edit:
                edit_key = f"edit_{unique_event_key}"
                if st.button("✏️", key=edit_key, help="Edit event"):
                    st.session_state[f'edit_event_{unique_event_key}'] = True
                    st.rerun()
        if not is_done and not showing_description:
            col_start, col_pause = st.columns([1, 1])
            
            with col_start:
                start_key = f"start_{unique_event_key}"
                start_disabled = is_session_running
                if st.button("▶️ Start", key=start_key, use_container_width=True, disabled=start_disabled):
                    base_event_id = extract_base_event_id(event_id)
                    session_core = TaskSessionCore()
                    session_core.start_session(base_event_id)
                    st.rerun()
            
            with col_pause:
                pause_key = f"pause_{unique_event_key}"
                pause_disabled = not is_session_running
                if st.button("⏸️ Pause", key=pause_key, use_container_width=True, disabled=pause_disabled):
                    base_event_id = extract_base_event_id(event_id)
                    session_core = TaskSessionCore()
                    session_core.pause_session(base_event_id)
                    st.rerun()
            base_event_id = extract_base_event_id(event_id)
            session_core = TaskSessionCore()
            if selected_date:
                time_spent = session_core.get_time_spent_for_date(base_event_id, selected_date)
                if time_spent > 0:
                    if selected_date == date.today():
                        st.markdown(f"**Time spent today:** {format_duration(time_spent)}")
                    else:
                        date_str = selected_date.strftime("%B %d, %Y")
                        st.markdown(f"**Time spent on {date_str}:** {format_duration(time_spent)}")
            else:
                total_time = session_core.get_total_time_spent(base_event_id)
                if total_time > 0:
                    st.markdown(f"**Total time spent:** {format_duration(total_time)}")
        if is_done:
            if completed_at:
                completed_str = completed_at.strftime("%Y-%m-%d %I:%M %p")
                st.markdown(f"**Completed on:** {completed_str}")
            if completion_description:
                st.markdown(f"**📝 What I accomplished:**")
                st.info(completion_description)
        else:
            time_str = format_time(event)
            st.markdown(f"**🕐 {time_str}**")
            
            # Recurrence
            recurrence = event.get('recurrence')
            if recurrence:
                st.markdown(f"**🔄 {recurrence}**")
            elif event.get('raw_event', {}).get('recurringEventId'):
                st.markdown("**🔄 Recurring event** (pattern not available)")
            
            description = event.get('description', '')
            if description:
                if len(description) > 200:
                    description = description[:200] + "..."
                st.markdown(f"**Description:** {description}")
        if debug_mode:
            with st.expander(f"🐛 Debug: {event.get('title', 'Event')}"):
                st.write("**Parsed Recurrence:**", event.get('recurrence') or "None")
                st.write("**Raw event recurrence:**", event.get('raw_event', {}).get('recurrence') or "None")
                st.write("**Recurring Event ID:**", event.get('raw_event', {}).get('recurringEventId') or "None")
                st.json(event.get('raw_event', {}))
        
        st.divider()
        if not is_done and st.session_state.get(f'edit_event_{unique_event_key}', False):
            calendar_service = get_calendar_service()
            result = render_edit_event_form(calendar_service, event)
            if result:
                if isinstance(result, dict) and result.get('deleted'):
                    st.session_state[f'edit_event_{unique_event_key}'] = False
                    if 'calendar_events' in st.session_state:
                        del st.session_state['calendar_events']
                    st.rerun()
                else:
                    st.session_state[f'edit_event_{unique_event_key}'] = False
                    if 'calendar_events' in st.session_state:
                        del st.session_state['calendar_events']
                    st.rerun()
            elif st.button("❌ Cancel Edit", key=f"cancel_edit_{unique_event_key}"):
                st.session_state[f'edit_event_{unique_event_key}'] = False
                st.rerun()


def render_calendar_events():
    """Render calendar events with task management (pending/done, time tracking)."""
    is_authenticated = False
    try:
        calendar_service = get_calendar_service()
        if calendar_service.service is not None:
            is_authenticated = True
    except ValueError:
        is_authenticated = False
    if not is_authenticated:
        today = date.today()
        today_str = today.strftime("%B %d, %Y")
        st.markdown(f"""
        <h2 style="font-family: {FONT_INTER}; color: {SMART_BLUE}; font-weight: 700; margin: 0;">
            {today_str} - Tasks
        </h2>
        """, unsafe_allow_html=True)
        render_authentication_prompt()
        return
    today = date.today()
    col_date, col_header = st.columns([1, 4])
    with col_date:
        selected_date = st.date_input(
            "Select Date",
            value=today,
            key="selected_date",
            help="Choose a date to view tasks"
        )
    selected_date_str = selected_date.strftime("%B %d, %Y")
    with col_header:
        st.markdown(f"""
        <h2 style="font-family: {FONT_INTER}; color: {SMART_BLUE}; font-weight: 700; margin: 0;">
            {selected_date_str} - Tasks
        </h2>
        """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            cache_key = f'calendar_events_{selected_date.isoformat()}'
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            get_calendar_service.clear()
            st.rerun()
    with col2:
        if st.button("➕ Add Event", use_container_width=True):
            st.session_state.show_add_event_form = True
    with col3:
        debug_mode = st.checkbox("🐛 Debug", help="Show raw event data for debugging")
    
    st.divider()
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
        calendar_service = get_calendar_service()
        if calendar_service.service is None:
            st.error("Calendar service not initialized")
            return
        cache_key = f'calendar_events_{selected_date.isoformat()}'
        if cache_key not in st.session_state:
            events = calendar_service.get_events_for_date(selected_date)
            st.session_state[cache_key] = {
                'events': events,
                'timestamp': datetime.now()
            }
        else:
            cache_age = (datetime.now() - st.session_state[cache_key]['timestamp']).total_seconds()
            if cache_age > 300:  # 5 minutes
                events = calendar_service.get_events_for_date(selected_date)
                st.session_state[cache_key] = {
                    'events': events,
                    'timestamp': datetime.now()
                }
            else:
                events = st.session_state[cache_key]['events']
        base_event_ids_set = set()
        event_id_map = {}
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
        completion_status_raw = task_core.get_completion_status_batch(base_event_ids, selected_date) if base_event_ids else {}
        if debug_mode:
            st.write("**Raw Completion Status (by base_id):**")
            st.json(completion_status_raw)
            st.write("**Event ID Mapping:**")
            st.json(event_id_map)
            st.write("**Base Event IDs queried:**")
            st.json(base_event_ids)
        
        # Map completion status back to original event_ids (batch returns by base_id)
        completion_status = {}
        for event_id_str, base_id in event_id_map.items():
            raw = completion_status_raw.get(base_id, (False, None, None))
            completion_status[event_id_str] = (raw[0], raw[1], raw[2] if len(raw) > 2 else None)
        if debug_mode:
            st.write("**Completion Status Debug:**")
            st.json(completion_status)
        pending_events = []
        done_events = []
        
        for event in events:
            event_id = event.get('id')
            if event_id:
                # Use base event_id (without timestamp) for lookup
                # The database stores completion status by base event_id
                event_id_str = str(event_id)
                is_done, completed_at, completion_description = completion_status.get(event_id_str, (False, None, None))
                
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
            col_pending, col_spacer, col_done = st.columns([1, 0.1, 1])
            
            with col_pending:
                st.markdown(f"""
                <h3 style="font-family: {FONT_INTER}; color: {SMART_BLUE}; font-weight: 600; margin-bottom: 16px;">
                    ⏳ Pending Tasks ({len(pending_events)})
                </h3>
                """, unsafe_allow_html=True)
                if pending_events:
                    for event_data in pending_events:
                        render_event_card(
                            event_data['event'],
                            is_done=False,
                            completed_at=None,
                            completion_description=None,
                            debug_mode=debug_mode,
                            selected_date=selected_date
                        )
                else:
                    st.info("🎉 No pending events! All tasks are completed.")
            with col_spacer:
                st.write("")
            
            with col_done:
                st.markdown(f"""
                <h3 style="font-family: {FONT_INTER}; color: {SMART_BLUE}; font-weight: 600; margin-bottom: 16px;">
                    ✅ Done Tasks ({len(done_events)})
                </h3>
                """, unsafe_allow_html=True)
                if done_events:
                    for event_data in done_events:
                        render_event_card(
                            event_data['event'],
                            is_done=True,
                            completed_at=event_data['completed_at'],
                            completion_description=event_data.get('completion_description'),
                            debug_mode=debug_mode,
                            selected_date=selected_date
                        )
                else:
                    st.info("📝 No completed events yet.")
    except ValueError as e:
        if "authentication" in str(e).lower() or "credential" in str(e).lower():
            st.info("👆 Click the sync button (🔄) above to authenticate and load your calendar events.")
        else:
            st.error(f"❌ Error: {str(e)}")
    except Exception as e:
        st.error(f"❌ Error loading calendar events: {str(e)}")
        st.info("Please check your internet connection and try again.")

