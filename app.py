import streamlit as st

from config import APP_TITLE
from ui.components.calendar_events import render_calendar_events
from ui.components.xp_bar import render_xp_bar
from data.db import init_db

@st.cache_resource
def initialize_app():
    """Initialize app resources (database, etc.)"""
    try:
        init_db()
    except Exception as e:
        # Don't fail the app if DB init fails, but log it
        print(f"Database initialization warning: {e}")

def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    
    # Initialize app resources
    initialize_app()

    st.title("🧠 MindOS")

    # XP Bar Section
    render_xp_bar()
    st.divider()

    # Calendar Events Section
    render_calendar_events()
    
    st.divider()


if __name__ == "__main__":
    main()
