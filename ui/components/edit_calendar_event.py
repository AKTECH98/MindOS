"""
Edit Calendar Event Component
Form to edit existing events in Google Calendar.
"""
import streamlit as st
from datetime import datetime, date, time
from typing import Optional, Dict

from integrations.gcalendar import CalendarService


def render_edit_event_form(calendar_service: CalendarService, event: Dict) -> Optional[Dict]:
    """
    Render a form to edit an existing calendar event.
    
    Args:
        calendar_service: CalendarService instance to update events
        event: Event dictionary with current event data
        
    Returns:
        Dictionary with updated event data if successful, None otherwise
    """
    st.subheader("✏️ Edit Event")
    
    # Extract current event data
    current_title = event.get('title', '')
    current_start = event.get('start_time')
    current_end = event.get('end_time')
    current_description = event.get('description', '')
    current_recurrence = event.get('recurrence')
    is_recurring = current_recurrence is not None and 'daily' in current_recurrence.lower()
    event_id = event.get('id')
    
    if not event_id:
        st.error("❌ Event ID not found. Cannot edit this event.")
        return None
    
    # Check if delete confirmation is needed
    if st.session_state.get(f'confirm_delete_{event_id}', False):
        st.warning("⚠️ **Are you sure you want to delete this event?**")
        st.info("This will delete the event from Google Calendar. For recurring events, only this instance will be deleted.")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Yes, Delete", key=f"confirm_delete_yes_{event_id}", use_container_width=True, type="primary"):
                try:
                    calendar_service.delete_event(event_id)
                    st.success(f"✅ Event deleted successfully!")
                    # Clear flags and cache
                    st.session_state[f'confirm_delete_{event_id}'] = False
                    if 'calendar_events' in st.session_state:
                        del st.session_state['calendar_events']
                    # Return a special marker to indicate deletion
                    return {'deleted': True, 'event_id': event_id}
                except Exception as e:
                    st.error(f"❌ Error deleting event: {str(e)}")
                    st.session_state[f'confirm_delete_{event_id}'] = False
                    return None
        with col2:
            if st.button("❌ Cancel", key=f"confirm_delete_no_{event_id}", use_container_width=True):
                st.session_state[f'confirm_delete_{event_id}'] = False
                st.rerun()
        
        return None
    
    with st.form("edit_calendar_event_form", clear_on_submit=False):
        # Title
        title = st.text_input("Event Title *", value=current_title, placeholder="Enter event title")
        
        # Date and Time
        if current_start:
            # Extract date and time from current start time
            event_date = current_start.date() if hasattr(current_start, 'date') else date.today()
            start_time_val = current_start.time() if hasattr(current_start, 'time') else time(9, 0)
            end_time_val = current_end.time() if current_end and hasattr(current_end, 'time') else time(10, 0)
        else:
            event_date = date.today()
            start_time_val = time(9, 0)
            end_time_val = time(10, 0)
        
        event_date = st.date_input("Date *", value=event_date)
        
        # Time columns
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input("Start Time *", value=start_time_val)
        with col2:
            end_time = st.time_input("End Time *", value=end_time_val)
        
        # Recurrence option
        repeat_daily = st.checkbox("Repeat daily", value=is_recurring)
        
        # Description
        description = st.text_area("Description (optional)", value=current_description, placeholder="Enter event description")
        
        # Submit buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            submitted = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
        with col2:
            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
        with col3:
            delete_clicked = st.form_submit_button("🗑️ Delete", use_container_width=True, type="secondary")
        
        if cancelled:
            return None
        
        if delete_clicked:
            # Set flag to show confirmation dialog
            st.session_state[f'confirm_delete_{event_id}'] = True
            st.rerun()
        
        if submitted:
            # Validate inputs
            if not title:
                st.error("❌ Please enter an event title")
                return None
            
            if end_time <= start_time:
                st.error("❌ End time must be after start time")
                return None
            
            try:
                # Combine date and time
                start_datetime = datetime.combine(event_date, start_time)
                end_datetime = datetime.combine(event_date, end_time)
                
                # Update event via calendar service
                updated_event = calendar_service.update_event(
                    event_id=event_id,
                    title=title,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    description=description if description else None,
                    repeat_daily=repeat_daily
                )
                
                if updated_event:
                    st.success(f"✅ Event '{title}' updated successfully!")
                    # Clear cache to refresh events list
                    if 'calendar_events' in st.session_state:
                        del st.session_state['calendar_events']
                    return updated_event
                else:
                    st.error("❌ Failed to update event. Please try again.")
                    return None
                    
            except Exception as e:
                st.error(f"❌ Error updating event: {str(e)}")
                return None
    
    return None

