import streamlit as st
from datetime import datetime

from config import APP_TITLE
from ui.components.calendar_events import render_calendar_events
from ui.components.xp_bar import render_xp_bar
from data.db import init_db
from core.task_status import TaskStatusCore

@st.cache_resource
def initialize_app():
    """Initialize app resources (database, etc.)"""
    try:
        init_db()
    except Exception as e:
        # Don't fail the app if DB init fails, but log it
        print(f"Database initialization warning: {e}")

def check_and_run_daily_deduction():
    """Check if daily XP deduction should run and execute it."""
    try:
        task_core = TaskStatusCore()
        
        # Check if it's past midnight and hasn't run today
        now = datetime.now()
        if now.hour >= 0:  # It's a new day (past midnight)
            if task_core.should_run_daily_deduction():
                result = task_core.deduct_xp_for_pending_tasks_from_yesterday()
                if result.get('success') and result.get('deducted_count', 0) > 0:
                    print(f"✅ Daily XP deduction completed: {result['message']}")
                elif result.get('success'):
                    print(f"ℹ️ Daily XP deduction: {result.get('message', 'No pending tasks')}")
                else:
                    print(f"⚠️ Daily XP deduction failed: {result.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"Error running daily XP deduction: {e}")

def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    
    # Initialize app resources
    initialize_app()
    
    # Check and run daily XP deduction if needed (runs once per day at startup)
    check_and_run_daily_deduction()

    st.title("MindOS")

    # XP Bar Section
    render_xp_bar()
    st.divider()

    # Calendar Events Section
    render_calendar_events()


if __name__ == "__main__":
    main()
