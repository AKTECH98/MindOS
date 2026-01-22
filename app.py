import streamlit as st
from datetime import datetime

from config import APP_TITLE
from ui.components.calendar_events import render_calendar_events
from ui.components.xp_bar import render_xp_bar
from ui.components.contribution_chart import render_contribution_chart
from ui.components.stats_panel import render_stats_panel
from ui.components.left_sidebar import render_left_sidebar
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

    # Apply global theme CSS
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global theme variables */
    :root {
        --smart-blue: #06b6d4;
        --slate-grey: #64748b;
        --slate-bg: #475569;
        --slate-border: #64748b;
    }
    
    /* Apply theme to Streamlit elements */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--smart-blue);
    }
    
    /* Buttons */
    .stButton > button {
        background-color: var(--slate-bg);
        color: var(--smart-blue);
        border: 1px solid var(--slate-border);
        border-radius: 8px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: var(--smart-blue);
        color: white;
        border-color: var(--smart-blue);
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background-color: var(--slate-bg);
        border: 1px solid var(--slate-border);
        border-radius: 8px;
        color: var(--smart-blue);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Date input */
    .stDateInput > div > div > input {
        background-color: var(--slate-bg);
        border: 1px solid var(--slate-border);
        border-radius: 8px;
        color: var(--smart-blue);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Checkboxes */
    .stCheckbox > label {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--slate-grey);
    }
    
    /* Info/Error messages */
    .stInfo, .stSuccess, .stWarning, .stError {
        border-left: 4px solid var(--smart-blue);
        border-radius: 4px;
    }
    
    /* Numbers should use monospace */
    .number, [class*="number"] {
        font-family: 'JetBrains Mono', monospace;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h1 style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
       color: #06b6d4; font-weight: 700; margin-bottom: 24px;">
        MindOS
    </h1>
    """, unsafe_allow_html=True)

    # Left sidebar, main content, and stats panel side by side
    col_sidebar, col_main, col_stats = st.columns([0.8, 3, 1])
    
    with col_sidebar:
        # Left Sidebar with Level, Total XP, and Quote
        render_left_sidebar()
    
    with col_main:
        # Container to minimize spacing between components
        with st.container():
            # XP Bar Section (progress bar only)
            render_xp_bar()
            
            # Contribution Chart Section (no extra spacing)
            render_contribution_chart()
    
    with col_stats:
        # Stats Panel (appears once on the right)
        render_stats_panel()
    
    # Divider between sections
    st.divider()

    # Calendar Events Section
    render_calendar_events()


if __name__ == "__main__":
    main()
