"""Stats panel: total tasks, active days, average per day."""
import streamlit as st
from datetime import date, timedelta

from ui.components.contribution_chart import get_completions_by_date
from ui.theme import SMART_BLUE


_STATS_CSS = """
<style>
.stats-panel {
    background: var(--slate-bg);
    border: 1px solid var(--slate-border);
    border-radius: 8px;
    padding: 21px;
    position: relative;
    background-image: 
        linear-gradient(rgba(100, 116, 139, 0.1) 1px, transparent 1px),
        linear-gradient(90deg, rgba(100, 116, 139, 0.1) 1px, transparent 1px);
    background-size: 40px 40px;
    margin-top: 0;
}

.stats-title {
    font-family: inherit;
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--smart-blue);
    margin-bottom: 20px;
    text-align: center;
    position: relative;
    z-index: 1;
}

.stat-item {
    margin-bottom: 20px;
    position: relative;
    z-index: 1;
}

.stat-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 24px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 4px;
}

.stat-label {
    font-family: inherit;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--smart-blue);
    text-align: center;
}
</style>
"""


def _render_stats_html(total_tasks: int, active_days: int, avg_per_day: float) -> str:
    """Generate HTML for the stats panel."""
    return f'''
    <div class="stats-panel" style="margin-top: 0; margin-bottom: 0;">
        <div class="stats-title">Stats</div>
        <div class="stat-item">
            <div class="stat-value" style="color: {SMART_BLUE};">{total_tasks}</div>
            <div class="stat-label">Tasks</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" style="color: {SMART_BLUE};">{active_days}</div>
            <div class="stat-label">Active Days</div>
        </div>
        <div class="stat-item" style="margin-bottom: 0;">
            <div class="stat-value" style="color: {SMART_BLUE};">{avg_per_day:.1f}</div>
            <div class="stat-label">Avg/Day</div>
        </div>
    </div>
    '''


def render_stats_panel():
    """
    Render a stats panel showing productivity statistics.
    Displays total tasks, active days, and average per day.
    """
    st.markdown(_STATS_CSS, unsafe_allow_html=True)

    try:
        today = date.today()
        start_date = today - timedelta(days=370)
        completions_by_date = get_completions_by_date(start_date, today)
        total_tasks = sum(completions_by_date.values())
        active_days = len(completions_by_date)
        total_days = (today - start_date).days + 1
        avg_per_day = total_tasks / total_days if total_days > 0 else 0
        stats_html = _render_stats_html(total_tasks, active_days, avg_per_day)
        st.markdown(stats_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading stats: {e}")
        default_html = _render_stats_html(0, 0, 0.0)
        st.markdown(default_html, unsafe_allow_html=True)
