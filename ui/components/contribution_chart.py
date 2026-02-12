"""Daily Pulse: GitHub-like contribution chart for task completions."""
import streamlit as st
from datetime import date, timedelta
from typing import Dict

from data.repositories.event_completion_repository import EventCompletionRepository
from data.db import EventCompletion
from sqlalchemy import func
from ui.theme import CONTRIB_COLORS, SLATE_GREY


def get_completions_by_date(start_date: date, end_date: date) -> Dict[date, int]:
    """Return completion counts per date in the given range."""
    try:
        repo = EventCompletionRepository()
        completions = repo.db.query(
            func.date(EventCompletion.completed_at).label('completion_date'),
            func.count(EventCompletion.id).label('count')
        ).filter(
            EventCompletion.is_done == True,
            EventCompletion.completed_at.isnot(None),
            func.date(EventCompletion.completed_at) >= start_date,
            func.date(EventCompletion.completed_at) <= end_date
        ).group_by(
            func.date(EventCompletion.completed_at)
        ).all()
        
        result = {}
        for completion_date, count in completions:
            if completion_date:
                result[completion_date] = count
        
        repo.close()
        return result
    except Exception as e:
        st.error(f"Error loading completion data: {e}")
        return {}


def get_color_for_count(count: int, max_count: int) -> str:
    """Return heatmap color for a given count (0 = no contributions)."""
    if count == 0 or max_count == 0:
        return "#ebedf0"  # No contributions

    if max_count <= 1:
        intensity = count
    else:
        ratio = count / max_count
        if ratio <= 0.25:
            intensity = 1
        elif ratio <= 0.50:
            intensity = 2
        elif ratio <= 0.75:
            intensity = 3
        else:
            intensity = 4

    colors = CONTRIB_COLORS
    return colors[intensity] if intensity < len(colors) else colors[-1]


def render_contribution_chart():
    """Render Daily Pulse heatmap (last ~1 year of completions)."""
    try:
        today = date.today()
        start_date = today - timedelta(days=370)
        completions_by_date = get_completions_by_date(start_date, today)
        max_count = max(completions_by_date.values()) if completions_by_date else 0
        all_dates = []
        current_date = start_date
        while current_date <= today:
            all_dates.append(current_date)
            current_date += timedelta(days=1)
        weeks = []
        current_week = []
        first_date = all_dates[0]
        first_weekday = first_date.weekday()
        days_since_sunday = (first_weekday + 1) % 7
        if days_since_sunday > 0:
            for i in range(days_since_sunday):
                current_week.append(None)
        
        # Add all dates, grouping into weeks
        for d in all_dates:
            current_week.append(d)
            if len(current_week) == 7:
                weeks.append(current_week)
                current_week = []
        if current_week:
            while len(current_week) < 7:
                current_week.append(None)
            weeks.append(current_week)
        
        st.markdown("""
        <style>
        .heatmap-container {
            background: var(--slate-bg);
            border: 1px solid var(--slate-border);
            border-radius: 8px;
            padding: 16px;
            position: relative;
            min-width: 0;
            background-size: 40px 40px;
        }
        .daily-pulse-title {
            font-family: inherit;
            font-size: 18px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--smart-blue);
            margin: 0 0 16px 0;
            position: relative;
            z-index: 1;
        }
        .contrib-square {
            width: 100%;
            aspect-ratio: 1;
            border-radius: 2px;
            cursor: pointer;
            position: relative;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            border: 2px solid rgba(0,0,0,0.1);
            flex-shrink: 0;
        }
        .contrib-square:hover {
            transform: scale(1.4);
            box-shadow: 0 0 8px rgba(6,182,212,0.6), 0 0 0 2px rgba(6,182,212,0.3);
            z-index: 100;
        }
        .heatmap-week-column {
            display: flex;
            flex-direction: column;
            gap: 2px;
            flex: 1 0 0;
            min-width: 0;
        }
        .heatmap-row {
            display: flex;
            flex-direction: row;
            gap: 2px;
            width: 100%;
            margin: 8px 0;
        }
        .pulse-label { font-family: inherit; }
        </style>
        """, unsafe_allow_html=True)
        with st.container():
            week_columns_html = []
            for week in weeks:
                week_squares = []
                for day_date in week:
                    if day_date is None:
                        week_squares.append('<div class="contrib-square" style="background-color: transparent; cursor: default;"></div>')
                    else:
                        count = completions_by_date.get(day_date, 0)
                        color = get_color_for_count(count, max_count)
                        date_str = day_date.strftime('%b %d, %Y')
                        task_text = f"{count} task{'s' if count != 1 else ''} completed"
                        tooltip_text = f"{date_str}: {task_text}".replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        week_squares.append(f'<div class="contrib-square" style="background-color:{color};" title="{tooltip_text}"></div>')
                week_columns_html.append(f'<div class="heatmap-week-column">{"".join(week_squares)}</div>')
            week_columns_str = "".join(week_columns_html)

            title_section = '<div class="daily-pulse-title">Daily Pulse</div>'
            chart_section = f'<div class="heatmap-row">{week_columns_str}</div>'
            c0, c1, c2, c3, c4 = CONTRIB_COLORS
            legend_section = (
                f'<div class="pulse-label" style="display: flex; align-items: center; gap: 5px; margin-top: 10px;">'
                f'<span style="font-size: 11px; color: {SLATE_GREY}; font-weight: 500;">Less</span>'
                '<div style="display: flex; gap: 2px;">'
                f'<div style="width: 11px; height: 11px; background-color: {c0}; border-radius: 2px; border: 1px solid rgba(0,0,0,0.1);"></div>'
                f'<div style="width: 11px; height: 11px; background-color: {c1}; border-radius: 2px; border: 1px solid rgba(0,0,0,0.1);"></div>'
                f'<div style="width: 11px; height: 11px; background-color: {c2}; border-radius: 2px; border: 1px solid rgba(0,0,0,0.1);"></div>'
                f'<div style="width: 11px; height: 11px; background-color: {c3}; border-radius: 2px; border: 1px solid rgba(0,0,0,0.1);"></div>'
                f'<div style="width: 11px; height: 11px; background-color: {c4}; border-radius: 2px; border: 1px solid rgba(0,0,0,0.1);"></div>'
                '</div>'
                f'<span style="font-size: 11px; color: {SLATE_GREY}; font-weight: 500;">More</span>'
                '</div>'
            )
            full_html = (
                '<div class="heatmap-container">'
                f'{title_section}'
                f'{chart_section}'
                '<div style="display: flex; justify-content: flex-start; align-items: flex-start; margin-top: 8px;">'
                '<div>' + legend_section + '</div></div></div>'
            )
            st.markdown(full_html, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error rendering Daily Pulse: {e}")

