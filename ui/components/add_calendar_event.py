"""Form to add new Google Calendar events."""
import streamlit as st
from datetime import datetime, date, time
from typing import Optional, Dict

from integrations.gcalendar import CalendarService
from ui.theme import SMART_BLUE, FONT_INTER


def render_add_event_form(calendar_service: CalendarService) -> Optional[Dict]:
    """Render form to add a new calendar event."""
    st.markdown(
        f"""
    <h3 style="font-family: {FONT_INTER}; color: {SMART_BLUE}; font-weight: 600; margin-bottom: 16px;">
        ➕ Add New Event
    </h3>
    """,
        unsafe_allow_html=True,
    )

    with st.form("add_calendar_event_form", clear_on_submit=True):
        title = st.text_input("Event Title *", placeholder="Enter event title")
        event_date = st.date_input("Date *", value=date.today())
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input("Start Time *", value=time(9, 0))
        with col2:
            end_time = st.time_input("End Time *", value=time(10, 0))
        repeat_daily = st.checkbox("Repeat daily", value=False)
        description = st.text_area("Description (optional)", placeholder="Enter event description")
        submitted = st.form_submit_button("Create Event", use_container_width=True)
        if submitted:
            if not title:
                st.error("❌ Please enter an event title")
                return None
            
            if end_time <= start_time:
                st.error("❌ End time must be after start time")
                return None
            
            try:
                start_datetime = datetime.combine(event_date, start_time)
                end_datetime = datetime.combine(event_date, end_time)
                created_event = calendar_service.create_event(
                    title=title,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    description=description if description else None,
                    repeat_daily=repeat_daily
                )
                
                if created_event:
                    st.success(f"✅ Event '{title}' created successfully!")
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

