"""Task list panel: today's tasks with Start/Pause controls."""
import streamlit as st
from datetime import date, datetime

from ui.components.calendar_events import get_calendar_service
from core.task_status import TaskStatusCore, extract_base_event_id
from core.task_session import TaskSessionCore
from ui.theme import SLATE_GREY, SMART_BLUE, BTN_START_GREEN, BTN_START_BORDER, BTN_PAUSE_RED, BTN_PAUSE_BORDER


_TASK_PANEL_CSS = f"""
<style>
.task-panel-outer > [data-testid="stVerticalBlock"] {{ gap: 0; }}
.task-panel-outer [data-testid="stMarkdown"] {{ margin-top: 0; padding-top: 0; }}
.task-panel-outer [data-testid="stMarkdown"] p {{ margin: 0; }}
.task-panel-outer [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    align-items: flex-start !important;
    gap: 0.5rem;
}}
.task-panel-outer [data-testid="stHorizontalBlock"] > div {{
    display: flex !important;
    align-items: flex-start !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"] > div:last-child {{
    padding-top: 0.5rem !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"] > div:first-child [data-testid="stVerticalBlock"] {{
    padding-top: 0 !important;
    margin-top: 0 !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"] .stButton {{
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}}
.task-list-panel {{ background: transparent; border: none; padding: 0; margin: 0; }}
.task-list-title {{
    font-family: inherit;
    font-size: 20px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--smart-blue);
    margin: 0 0 8px 0;
    padding-top: 0;
}}
.task-list-item {{
    font-family: inherit;
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(100, 116, 139, 0.3);
    font-size: 15px;
}}
.task-list-item:last-child {{ border-bottom: none; }}
.task-list-item-done {{ opacity: 0.8; text-decoration: line-through; }}
.task-panel-outer .stButton > button {{
    width: auto !important;
    min-width: 2.25rem;
    min-height: 1.4rem !important;
    line-height: 1.2 !important;
    padding: 2px 6px !important;
    white-space: nowrap;
    border-radius: 15px !important;
}}
.task-panel-outer .stButton > button,
.task-panel-outer .stButton > button * {{
    font-size: 14px !important;    
}}
.task-panel-outer button.btn-start {{
    background-color: {BTN_START_GREEN} !important;
    color: white !important;
    border-color: {BTN_START_BORDER} !important;
}}
.task-panel-outer button.btn-pause {{
    background-color: {BTN_PAUSE_RED} !important;
    color: white !important;
    border-color: {BTN_PAUSE_BORDER} !important;
}}
</style>
"""

_PANEL_MARK_AND_BUTTONS_SCRIPT = """
<script>
(function() {
    function markPanelAndStyleButtons() {
        var panel = document.querySelector('.task-list-panel');
        if (panel) {
            var inner = panel.closest('[data-testid="stVerticalBlock"]');
            if (inner && inner.parentElement) {
                inner.parentElement.classList.add('task-panel-outer');
            }
        }
        document.querySelectorAll('.task-panel-outer').forEach(function(outer) {
            outer.querySelectorAll('button').forEach(function(btn) {
                var t = (btn.textContent || '').trim();
                if (t === 'Start') btn.classList.add('btn-start');
                else if (t === 'Pause') btn.classList.add('btn-pause');
            });
        });
    }
    function run() {
        markPanelAndStyleButtons();
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
    else run();
    if (typeof MutationObserver !== 'undefined') {
        var obs = new MutationObserver(run);
        obs.observe(document.body, { childList: true, subtree: true });
    }
})();
</script>
"""


def render_task_list_panel():
    """Render today's task list with status and Start/Pause buttons."""
    st.markdown(_TASK_PANEL_CSS, unsafe_allow_html=True)
    with st.container(border=False, key="task_panel"):
        is_authenticated = False
        try:
            calendar_service = get_calendar_service()
            if calendar_service.service is not None:
                is_authenticated = True
        except ValueError:
            is_authenticated = False

        if not is_authenticated:
            st.markdown(f'<div class="task-list-panel"><div class="task-list-title">Tasks</div><p style="color: {SLATE_GREY}; font-size: 12px;">Connect calendar to see tasks.</p></div>', unsafe_allow_html=True)
            return

        selected_date = date.today()
        try:
            cache_key = f'calendar_events_{selected_date.isoformat()}'
            if cache_key not in st.session_state:
                events = calendar_service.get_events_for_date(selected_date)
                st.session_state[cache_key] = {
                    'events': events,
                    'timestamp': datetime.now()
                }
            else:
                cache_age = (datetime.now() - st.session_state[cache_key]['timestamp']).total_seconds()
                if cache_age > 300:
                    events = calendar_service.get_events_for_date(selected_date)
                    st.session_state[cache_key] = {'events': events, 'timestamp': datetime.now()}
                else:
                    events = st.session_state[cache_key]['events']

            base_event_ids_set = set()
            event_id_map = {}
            for event in events:
                event_id = event.get('id')
                if event_id:
                    event_id_str = str(event_id)
                    base_id = extract_base_event_id(event_id_str)
                    base_event_ids_set.add(base_id)
                    event_id_map[event_id_str] = base_id

            base_event_ids = list(base_event_ids_set)
            task_core = TaskStatusCore()
            completion_status_raw = task_core.get_completion_status_batch(base_event_ids, selected_date) if base_event_ids else {}

            completion_status = {}
            for event_id_str, base_id in event_id_map.items():
                status_data = completion_status_raw.get(base_id, (False, None, None))
                completion_status[event_id_str] = (status_data[0], status_data[1], status_data[2] if len(status_data) > 2 else None)

            if not events:
                st.markdown(f'<p style="color: {SLATE_GREY}; font-size: 12px;">No tasks for this day.</p>', unsafe_allow_html=True)
                return

            session_core = TaskSessionCore()
            st.markdown('<div class="task-list-panel"><div class="task-list-title">Tasks</div>', unsafe_allow_html=True)
            for event in events:
                event_id = event.get('id')
                if not event_id:
                    continue
                event_id_str = str(event_id)
                base_event_id = extract_base_event_id(event_id_str)
                is_done, completed_at, _ = completion_status.get(event_id_str, (False, None, None))
                is_done_today = False
                if is_done and completed_at:
                    completed_date = completed_at.date() if isinstance(completed_at, datetime) else completed_at
                    if completed_date == selected_date:
                        is_done_today = True

                title = event.get('title', 'No Title')
                if is_done_today:
                    st.markdown(
                        f'<div class="task-list-item task-list-item-done">'
                        f'<strong>{title}</strong> <span style="color: {SMART_BLUE}; font-size: 11px;">(Done)</span></div>',
                        unsafe_allow_html=True
                    )
                else:
                    active_session = session_core.get_active_session(base_event_id)
                    is_running = active_session is not None
                    col_title, col_btn = st.columns([3, 1])
                    with col_title:
                        st.markdown(f'<div class="task-list-item"><strong>{title}</strong></div>', unsafe_allow_html=True)
                    with col_btn:
                        if is_running:
                            if st.button("Pause", key=f"task_pause_{base_event_id}"):
                                session_core.pause_session(base_event_id)
                                st.rerun()
                        else:
                            if st.button("Start", key=f"task_start_{base_event_id}"):
                                session_core.start_session(base_event_id)
                                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            if hasattr(st, 'html'):
                st.html(_PANEL_MARK_AND_BUTTONS_SCRIPT, unsafe_allow_javascript=True)
        except Exception as e:
            st.error(f"Error loading tasks: {e}")
