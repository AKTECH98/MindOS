"""
Add Calendar Event Component
Form to create new events in Google Calendar.
"""
import streamlit as st
from datetime import datetime, date, time
from typing import Optional, Dict

from integrations.gcalendar import CalendarService


def render_add_event_form(calendar_service: CalendarService) -> Optional[Dict]:
    """
    Render a form to add a new calendar event.
    
    Args:
        calendar_service: CalendarService instance to create events
        
    Returns:
        Dictionary with event data if created successfully, None otherwise
    """
    st.subheader("➕ Add New Event")
    
    with st.form("add_calendar_event_form", clear_on_submit=True):
        # Title
        title = st.text_input("Event Title *", placeholder="Enter event title")
        
        # Date
        event_date = st.date_input("Date *", value=date.today())
        
        # Time columns
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input("Start Time *", value=time(9, 0))
        with col2:
            end_time = st.time_input("End Time *", value=time(10, 0))
        
        # Recurrence option
        repeat_daily = st.checkbox("Repeat daily", value=False)
        
        # Description (optional)
        description = st.text_area("Description (optional)", placeholder="Enter event description")
        
        # Submit button
        submitted = st.form_submit_button("Create Event", use_container_width=True)
        
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
                
                # Create event via calendar service
                created_event = calendar_service.create_event(
                    title=title,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    description=description if description else None,
                    repeat_daily=repeat_daily
                )
                
                if created_event:
                    st.success(f"✅ Event '{title}' created successfully!")
                    # Clear cache to refresh events list
                    if 'calendar_events' in st.session_state:
                        del st.session_state['calendar_events']
                    return created_event
                else:
                    st.error("❌ Failed to create event. Please try again.")
                    return None
                    
            except Exception as e:
                st.error(f"❌ Error creating event: {str(e)}")
                return None
    
    return None

