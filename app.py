"""MindOS app entrypoint."""
import streamlit as st

from config import APP_TITLE
from ui.theme import GLOBAL_CSS, PAGE_HOME_CSS, SMART_BLUE, SLATE_GREY, FONT_INTER
from ui.components.calendar_events import render_calendar_events
from ui.components.xp_bar import render_xp_bar
from ui.components.contribution_chart import render_contribution_chart
from ui.components.stats_panel import render_stats_panel
from ui.components.left_sidebar import render_left_sidebar
from ui.components.task_list_panel import render_task_list_panel
from data.db import init_db
from core.task_status import TaskStatusCore


@st.cache_resource
def initialize_app():
    """Initialize database and app resources."""
    try:
        init_db()
    except Exception as e:
        print(f"Database initialization warning: {e}")


def check_and_run_daily_deduction():
    """Run daily XP deduction for pending tasks if not already run today."""
    try:
        task_core = TaskStatusCore()
        if not task_core.should_run_daily_deduction():
            return
        result = task_core.deduct_xp_for_pending_tasks_from_yesterday()
        if result.get("success") and result.get("deducted_count", 0) > 0:
            print(f"✅ Daily XP deduction completed: {result['message']}")
        elif result.get("success"):
            print(f"ℹ️ Daily XP deduction: {result.get('message', 'No pending tasks')}")
        else:
            print(f"⚠️ Daily XP deduction failed: {result.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"Error running daily XP deduction: {e}")


def _render_home_hero():
    """Render home hero: title, subtitle, and mind input."""
    st.markdown(
        f"""
    <div style="text-align: center;">
    <h1 style="font-family: {FONT_INTER}; color: {SMART_BLUE}; font-weight: 700; margin-bottom: 16px;">
        MindOS
    </h1>
    <p style="font-family: {FONT_INTER}; color: {SLATE_GREY}; font-size: 18px; font-weight: 500; margin-bottom: 24px;">
        What's on Your Mind Today
    </p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.text_input(
        "What's on your mind",
        key="home_mind_input",
        placeholder="Type here...",
        label_visibility="collapsed",
    )


def home_page():
    """Render Home page with hero and task list."""
    if PAGE_HOME_CSS:
        st.markdown('<div id="page-is-home" style="display:none;"></div>', unsafe_allow_html=True)
        st.markdown(PAGE_HOME_CSS, unsafe_allow_html=True)
    col_main, col_right = st.columns([3.8, 1])
    with col_main:
        _render_home_hero()
    with col_right:
        render_task_list_panel()


def dashboard_page():
    """Render Dashboard: sidebar, XP bar, contribution chart, stats, calendar."""
    with st.container(border=False):
        col_sidebar, col_main, col_right = st.columns([0.8, 3.2, 1])
        with col_sidebar:
            render_left_sidebar()
        with col_main:
            with st.container():
                render_xp_bar()
                render_contribution_chart()
        with col_right:
            render_stats_panel()

    st.divider()
    render_calendar_events()


def main():
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    initialize_app()
    check_and_run_daily_deduction()

    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    _logo_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 36" width="140" height="36">
        <circle cx="18" cy="18" r="14" fill="none" stroke="{SMART_BLUE}" stroke-width="2.5"/>
        <circle cx="18" cy="18" r="5" fill="{SMART_BLUE}"/>
        <text x="42" y="24" font-family="Inter, sans-serif" font-size="20" font-weight="700" fill="{SMART_BLUE}">MindOS</text>
    </svg>'''
    _icon_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" width="36" height="36">
        <circle cx="18" cy="18" r="14" fill="none" stroke="{SMART_BLUE}" stroke-width="2.5"/>
        <circle cx="18" cy="18" r="5" fill="{SMART_BLUE}"/>
    </svg>'''
    st.logo(image=_logo_svg, icon_image=_icon_svg, size="medium")

    home = st.Page(home_page, title="Home", icon="🏠", default=True)
    dashboard = st.Page(dashboard_page, title="Dashboard", icon="📊")

    pg = st.navigation([home, dashboard])
    pg.run()


if __name__ == "__main__":
    main()
