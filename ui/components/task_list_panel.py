"""Task list panel: today's tasks with Start/Pause controls."""
import streamlit as st
from datetime import date, datetime

from ui.components.calendar_events import get_calendar_service
from core.task_status import TaskStatusCore, extract_base_event_id
from core.task_session import TaskSessionCore
from ui.theme import SLATE_GREY, BTN_START_GREEN, BTN_PAUSE_RED


def _format_time_spent(seconds: int) -> str:
    """Format seconds as e.g. '2Hrs 15Mins 30Sec', '45Mins 0Sec', or '0Sec'."""
    if seconds <= 0:
        return "0Sec"
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    parts = []
    if hours > 0:
        parts.append(f"{hours}Hrs")
    if mins > 0 or hours > 0:
        parts.append(f"{mins}Mins")
    parts.append(f"{secs}Sec")
    return " ".join(parts)


_TASK_PANEL_CSS = f"""
<style>
.task-panel-outer > [data-testid="stVerticalBlock"] {{ gap: 0; }}
.task-panel-outer [data-testid="stMarkdown"] {{ margin-top: 0; padding-top: 0; }}
.task-panel-outer [data-testid="stMarkdown"] p {{ margin: 0; }}
.task-panel-outer [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    align-items: center !important;
    gap: 0.1rem;
    flex-wrap: nowrap !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"] > div {{
    display: flex !important;
    align-items: center !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"] > div:last-child {{
    padding-top: 0 !important;
    margin-top: 0 !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"] > div:first-child [data-testid="stVerticalBlock"] {{
    padding-top: 0 !important;
    margin-top: 0 !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(3)) {{
    min-height: 2.25rem !important;
    gap: 0px !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(3)) > div:nth-child(1) {{
    margin-right: 0rem !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(3)) > div:nth-child(2) {{
    margin-right: 1.75rem !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(3)) > div {{
    padding: 0 !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    margin-left: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    min-height: 2.25rem !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(3)) > div:nth-child(3) {{
    margin-left: 0 !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(3)) > div:last-child {{
    justify-content: flex-end !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(3)) > div:last-child:has(.task-list-item-time) {{
    justify-content: center !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(3)) > div [data-testid="stVerticalBlock"] {{
    padding: 0 !important;
    margin: 0 !important;
    min-height: 2.25rem !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: inherit !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(3)) > div [data-testid="stVerticalBlock"] > div {{
    width: 100% !important;
    min-height: 2.25rem !important;
    display: flex !important;
    align-items: center !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(3)) [data-testid="stMarkdown"] {{
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
    min-height: 2.25rem !important;
    display: flex !important;
    align-items: center !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(3)) [data-testid="stMarkdown"] p {{
    margin: 0 !important;
    padding: 0 !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(3)) [data-testid="stMarkdown"] .task-list-item {{
    padding: 0 0 0.75rem 0 !important;
    margin: 0 !important;
    width: 100% !important;
    min-height: 2.25rem !important;
    display: flex !important;
    align-items: center !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"] .stButton {{
    margin: 0 !important;
}}
.task-panel-outer .stCheckbox {{
    padding: 0 0 0.4rem 0 !important;
}}
.task-list-panel {{ background: transparent; padding: 0; margin: 0; }}
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
    padding: 0 0 0.75rem 0;
    font-size: 15px;
}}
.task-list-item-done {{ opacity: 0.8; }}
.task-list-item-done .task-xp-gained {{ margin-left: 0.5rem; font-size: 15px; font-weight: 600; }}
.task-list-item-time {{ font-size: 15px; display: flex; align-items: center; justify-content: center; padding: 0; margin: 0; line-height: 1.4; text-align: center; }}
.task-panel-outer .stButton > button {{
    width: 3.25rem !important;
    min-width: 3rem !important;
    min-height: 1.4rem !important;
    line-height: 1.2 !important;
    padding: 2px 6px !important;
    white-space: nowrap;
    border-radius: 20px !important;
}}
.task-panel-outer .stButton > button,
.task-panel-outer .stButton > button * {{
    font-size: 14px !important;
}}
.task-panel-outer button.btn-start {{
    background-color: {BTN_START_GREEN} !important;
    color: white !important;
}}
.task-panel-outer button.btn-pause {{
    background-color: #eab308 !important;
    color: white !important;
}}
.task-panel-outer button.btn-stop {{
    background-color: {BTN_PAUSE_RED} !important;
    color: white !important;
}}

.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(3)) > div:nth-child(3):has([data-testid="stHorizontalBlock"] > div:nth-child(2)) [data-testid="stHorizontalBlock"] {{
    gap: 0.5rem !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(3)) > div:nth-child(3):has([data-testid="stHorizontalBlock"] > div:nth-child(2)) .stButton > button {{
    min-width: unset !important;
    width: auto !important;
    padding: 2px 4px !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(2)):not(:has(> div:nth-child(3))) {{
    align-items: flex-start !important;
    margin-top: 0.75rem !important;
    gap: 0.5rem !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(2)):not(:has(> div:nth-child(3))) > div {{
    flex: 1 !important;
    min-width: 0 !important;
    padding-top: 0 !important;
    margin-top: 0 !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(2)):not(:has(> div:nth-child(3))) .stButton {{
    width: 100% !important;
    margin-top: 0 !important;
}}
.task-panel-outer [data-testid="stHorizontalBlock"]:has(> div:nth-child(2)):not(:has(> div:nth-child(3))) .stButton > button {{
    width: 100% !important;
    min-width: 0 !important;
}}
.task-list-item-title-wrap {{
    position: relative;
    display: inline-block;
}}
.task-list-item-time-today {{
    display: block;
    font-size: 12px;
    font-weight: normal;
    color: {SLATE_GREY};
    margin-top: 2px;
    opacity: 0;
    max-height: 0;
    overflow: hidden;
    transition: opacity 0.2s ease, max-height 0.2s ease;
}}
.task-list-item-title-wrap:hover .task-list-item-time-today {{
    opacity: 1;
    max-height: 1.5em;
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
                if (t === '▶') btn.classList.add('btn-start');
                else if (t === '⏸') btn.classList.add('btn-pause');
                else if (t === '■') btn.classList.add('btn-stop');
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
    with st.container(border=True, key="task_panel"):
        is_authenticated = False
        try:
            calendar_service = get_calendar_service()
            if calendar_service.service is not None:
                is_authenticated = True
        except ValueError:
            is_authenticated = False

        if not is_authenticated:
            st.markdown(
                f'<div class="task-list-panel"><div class="task-list-title">Tasks</div><p style="color: {SLATE_GREY}; font-size: 12px;">Connect calendar to see tasks.</p></div>',
                unsafe_allow_html=True
            )
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
                st.markdown(f'<div class="task-list-panel"><div class="task-list-title">Tasks</div><p style="color: {SLATE_GREY}; font-size: 12px;">No tasks for this day.</p></div>', unsafe_allow_html=True)
                return

            event_rows = []
            for idx, event in enumerate(events):
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
                event_rows.append((event, is_done_today, idx))
            event_rows.sort(key=lambda x: (x[1], x[2]))

            description_mode_base_id = None
            for event, is_done_today, _ in event_rows:
                if is_done_today:
                    continue
                base_id = extract_base_event_id(str(event.get('id')))
                if st.session_state.get(f'show_description_input_task_{base_id}', False):
                    description_mode_base_id = base_id
                    break
            if description_mode_base_id is not None:
                event_rows = [(e, done, i) for e, done, i in event_rows if extract_base_event_id(str(e.get('id'))) == description_mode_base_id]
                if event_rows:
                    event_rows = [event_rows[0]]  # show single task row + description box

            session_core = TaskSessionCore()
            st.markdown('<div class="task-list-panel"><div class="task-list-title">Tasks</div>', unsafe_allow_html=True)
            description_shown_for_bases = set()
            for event, is_done_today, _ in event_rows:
                event_id = event.get('id')
                event_id_str = str(event_id)
                base_event_id = extract_base_event_id(event_id_str)
                title = event.get('title', 'No Title')
                showing_description = st.session_state.get(f'show_description_input_task_{base_event_id}', False) and not is_done_today

                checkbox_key = f"task_done_{event_id_str}_{selected_date.isoformat()}"
                if is_done_today:
                    col_check, col_title, col_btn = st.columns([1, 3, 1])
                    with col_check:
                        done_checked = st.checkbox(
                            "Mark as done",
                            value=True,
                            key=checkbox_key,
                            label_visibility="collapsed",
                            disabled=False
                        )
                        if not done_checked:
                            task_core = TaskStatusCore()
                            task_core.mark_event_undone(base_event_id, completion_date=selected_date)
                            if cache_key in st.session_state:
                                del st.session_state[cache_key]
                            if 'calendar_events' in st.session_state:
                                del st.session_state['calendar_events']
                            if 'xp_info' in st.session_state:
                                del st.session_state['xp_info']
                            st.rerun()
                    with col_title:
                        xp_gained = f"+{TaskStatusCore.XP_PER_TASK}"
                        time_sec = session_core.get_time_spent_for_date(base_event_id, selected_date)
                        time_str = _format_time_spent(time_sec)
                        st.markdown(
                            f'<div class="task-list-item task-list-item-done">'
                            f'<div class="task-list-item-title-wrap"><strong>{title}</strong>'
                            f'<span class="task-list-item-time-today">Time spent today: {time_str}</span></div>'
                            f'<span class="task-xp-gained" style="color: {BTN_START_GREEN};">{xp_gained}</span></div>',
                            unsafe_allow_html=True
                        )
                    with col_btn:
                        st.empty()
                else:
                    active_session = session_core.get_active_session(base_event_id)
                    is_running = active_session is not None
                    col_check, col_title, col_btn = st.columns([1, 3, 1])
                    with col_check:
                        if not showing_description:
                            new_done_state = st.checkbox(
                                "Mark as done",
                                value=False,
                                key=checkbox_key,
                                label_visibility="collapsed",
                                disabled=is_running
                            )
                            if new_done_state:
                                st.session_state[f'show_description_input_task_{base_event_id}'] = True
                                st.rerun()
                        else:
                            unchecked = st.checkbox(
                                "Mark as done",
                                value=True,
                                key=f"task_done_while_desc_{event_id_str}_{selected_date.isoformat()}",
                                label_visibility="collapsed",
                                disabled=False
                            )
                            if not unchecked:
                                st.session_state.pop(f'show_description_input_task_{base_event_id}', None)
                                st.session_state.pop(f"description_input_task_{base_event_id}", None)
                                st.rerun()
                    with col_title:
                        time_sec = session_core.get_time_spent_for_date(base_event_id, selected_date)
                        time_str = _format_time_spent(time_sec)
                        st.markdown(
                            f'<div class="task-list-item"><div class="task-list-item-title-wrap">'
                            f'<strong>{title}</strong>'
                            f'<span class="task-list-item-time-today">Time spent today: {time_str}</span></div></div>',
                            unsafe_allow_html=True
                        )
                    with col_btn:
                        if not showing_description:
                            if is_running:
                                sub_col_pause, sub_col_stop = st.columns(2)
                                with sub_col_pause:
                                    if st.button("⏸", key=f"task_pause_{event_id_str}"):
                                        session_core.pause_session(base_event_id)
                                        st.rerun()
                                with sub_col_stop:
                                    if st.button("■", key=f"task_stop_{event_id_str}"):
                                        session_core.pause_session(base_event_id)
                                        st.session_state[f'show_description_input_task_{base_event_id}'] = True
                                        st.rerun()
                            else:
                                if st.button("▶", key=f"task_start_{event_id_str}"):
                                    session_core.start_session(base_event_id)
                                    st.rerun()

                if showing_description and base_event_id not in description_shown_for_bases:
                    description_shown_for_bases.add(base_event_id)
                    description = st.text_area(
                        "Completion Description *",
                        key=f"description_input_task_{base_event_id}",
                        placeholder="Enter what you accomplished in this task...",
                        height=100,
                        label_visibility="collapsed"
                    )
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("Save", key=f"save_description_task_{base_event_id}", use_container_width=True, type="primary"):
                            description_text = (description or "").strip()
                            if not description_text:
                                st.error("Description is required. Please describe what you accomplished before saving.")
                            else:
                                try:
                                    task_core = TaskStatusCore()
                                    success = task_core.mark_event_done(base_event_id, description=description_text, completion_date=selected_date)
                                    if success:
                                        st.session_state.pop(f'show_description_input_task_{base_event_id}', None)
                                        st.session_state.pop(f"description_input_task_{base_event_id}", None)
                                        if cache_key in st.session_state:
                                            del st.session_state[cache_key]
                                        if 'calendar_events' in st.session_state:
                                            del st.session_state['calendar_events']
                                        if 'xp_info' in st.session_state:
                                            del st.session_state['xp_info']
                                        st.rerun()
                                    else:
                                        st.error("Failed to save completion. Please try again.")
                                except ValueError as e:
                                    st.error(str(e))
                    with btn_col2:
                        if st.button("Cancel", key=f"cancel_description_task_{base_event_id}", use_container_width=True):
                            st.session_state.pop(f'show_description_input_task_{base_event_id}', None)
                            st.session_state.pop(f"description_input_task_{base_event_id}", None)
                            st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
            if hasattr(st, 'html'):
                st.html(_PANEL_MARK_AND_BUTTONS_SCRIPT, unsafe_allow_javascript=True)
        except Exception as e:
            st.error(f"Error loading tasks: {e}")
