"""
Daily Pulse Component
Displays a GitHub-like contribution chart showing task completion activity.
"""
import streamlit as st
from datetime import datetime, date, timedelta
from typing import Dict

from data.repositories.event_completion_repository import EventCompletionRepository
from data.db import EventCompletion
from sqlalchemy import func


def get_completions_by_date(start_date: date, end_date: date) -> Dict[date, int]:
    """
    Get task completion counts grouped by date.
    
    Args:
        start_date: Start date for the range
        end_date: End date for the range
        
    Returns:
        Dictionary mapping date to count of completed tasks
    """
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
    """
    Get color for a contribution square based on task count.
    Uses GitHub-like color scheme with relative intensity.
    
    Args:
        count: Number of tasks completed on this day
        max_count: Maximum count in the dataset (for normalization)
        
    Returns:
        Hex color code
    """
    if count == 0:
        return "#ebedf0"  # Light gray (no contributions)
    
    if max_count == 0:
        return "#ebedf0"
    
    # Calculate intensity based on relative contribution
    # Use quartiles: 0-25%, 25-50%, 50-75%, 75-100%
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
    
    # Smart Blue color scheme (lighter to darker)
    colors = [
        "#64748b",  # 0 - No contributions (Slate Grey)
        "#67e8f9",  # 1 - Light Smart Blue
        "#22d3ee",  # 2 - Medium Smart Blue
        "#06b6d4",  # 3 - Smart Blue
        "#0891b2"   # 4 - Dark Smart Blue
    ]
    
    return colors[intensity] if intensity < len(colors) else colors[-1]


def render_contribution_chart():
    """
    Render Daily Pulse - a GitHub-like contribution chart showing task completion activity.
    Displays the last 371 days (approximately 1 year) in a grid format.
    """
    try:
        # Calculate date range (last 371 days to show ~1 year)
        today = date.today()
        start_date = today - timedelta(days=370)  # 371 days total (0-370 inclusive)
        
        # Get completion data
        completions_by_date = get_completions_by_date(start_date, today)
        
        # Find max count for color normalization
        max_count = max(completions_by_date.values()) if completions_by_date else 0
        
        # Create a list of all dates in range
        all_dates = []
        current_date = start_date
        while current_date <= today:
            all_dates.append(current_date)
            current_date += timedelta(days=1)
        
        # Group dates by week (starting from Sunday, like GitHub)
        weeks = []
        current_week = []
        
        # Find the day of week for the first date (0=Monday, 6=Sunday)
        first_date = all_dates[0]
        first_weekday = first_date.weekday()  # Monday=0, Sunday=6
        
        # Calculate days since Sunday (Sunday should be column 0)
        # If first_date is Sunday (weekday=6), days_since_sunday = 0
        # If first_date is Monday (weekday=0), days_since_sunday = 1
        # etc.
        days_since_sunday = (first_weekday + 1) % 7
        
        # Add padding days at the start if needed (to align with Sunday)
        if days_since_sunday > 0:
            for i in range(days_since_sunday):
                current_week.append(None)
        
        # Add all dates, grouping into weeks
        for d in all_dates:
            current_week.append(d)
            if len(current_week) == 7:
                weeks.append(current_week)
                current_week = []
        
        # Add remaining days to last week (pad to 7 days)
        if current_week:
            while len(current_week) < 7:
                current_week.append(None)
            weeks.append(current_week)
        
        # Add CSS with refined design
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        
        .heatmap-container {
            background: #475569;
            border: 1px solid #64748b;
            border-radius: 8px;
            padding: 16px;
            position: relative;
            background-image: 
                linear-gradient(rgba(100, 116, 139, 0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(100, 116, 139, 0.1) 1px, transparent 1px);
            background-size: 40px 40px;
        }
        
        .daily-pulse-title {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 18px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #06b6d4;
            margin: 0 0 16px 0;
            position: relative;
            z-index: 1;
        }
        
        .contrib-square {
            width: 11px;
            height: 11px;
            border-radius: 2px;
            cursor: pointer;
            position: relative;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            border: 1px solid rgba(0,0,0,0.1);
        }
        .contrib-square:hover {
            transform: scale(1.4);
            box-shadow: 0 0 8px rgba(6,182,212,0.6), 0 0 0 2px rgba(6,182,212,0.3);
            z-index: 100;
        }
        
        .pulse-label {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        </style>
        """, unsafe_allow_html=True)
        
        # Full width chart (no spacer needed, left sidebar is separate)
        with st.container():
            # Create week columns (horizontal layout - weeks go left to right)
            week_columns_html = []
            for week in weeks:
                week_squares = []
                for day_date in week:
                    if day_date is None:
                        # Empty square for padding
                        week_squares.append('<div style="width: 11px; height: 11px; background-color: transparent;"></div>')
                    else:
                        count = completions_by_date.get(day_date, 0)
                        color = get_color_for_count(count, max_count)
                        date_str = day_date.strftime('%b %d, %Y')
                        task_text = f"{count} task{'s' if count != 1 else ''} completed"
                        tooltip_text = f"{date_str}: {task_text}"
                        
                        # Escape HTML entities
                        tooltip_text = tooltip_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        
                        # Use title attribute for native browser tooltip
                        week_squares.append(f'<div class="contrib-square" style="background-color: {color};" title="{tooltip_text}"></div>')
                
                # Each week is a column with days stacked vertically
                week_columns_html.append(f'<div style="display: flex; flex-direction: column; gap: 3px;">{"".join(week_squares)}</div>')
            
            # Build complete HTML with container in one block
            week_columns_str = "".join(week_columns_html)
            
            # Build HTML components
            title_section = '<div class="daily-pulse-title">Daily Pulse</div>'
            chart_section = f'<div style="display: flex; flex-direction: row; gap: 3px; margin: 8px 0;">{week_columns_str}</div>'
            
            legend_section = (
                '<div class="pulse-label" style="display: flex; align-items: center; gap: 5px; margin-top: 10px;">'
                '<span style="font-size: 11px; color: #64748b; font-weight: 500;">Less</span>'
                '<div style="display: flex; gap: 2px;">'
                '<div style="width: 11px; height: 11px; background-color: #64748b; border-radius: 2px; '
                'border: 1px solid rgba(0,0,0,0.1);"></div>'
                '<div style="width: 11px; height: 11px; background-color: #67e8f9; border-radius: 2px; '
                'border: 1px solid rgba(0,0,0,0.1);"></div>'
                '<div style="width: 11px; height: 11px; background-color: #22d3ee; border-radius: 2px; '
                'border: 1px solid rgba(0,0,0,0.1);"></div>'
                '<div style="width: 11px; height: 11px; background-color: #06b6d4; border-radius: 2px; '
                'border: 1px solid rgba(0,0,0,0.1);"></div>'
                '<div style="width: 11px; height: 11px; background-color: #0891b2; border-radius: 2px; '
                'border: 1px solid rgba(0,0,0,0.1);"></div>'
                '</div>'
                '<span style="font-size: 11px; color: #64748b; font-weight: 500;">More</span>'
                '</div>'
            )
            
            # Combine everything in container (stats are in separate panel)
            full_html = (
                '<div class="heatmap-container">'
                f'{title_section}'
                f'{chart_section}'
                '<div style="display: flex; justify-content: flex-start; align-items: flex-start; margin-top: 8px;">'
                '<div>'
                f'{legend_section}'
                '</div>'
                '</div>'
                '</div>'
            )
            
            st.markdown(full_html, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error rendering Daily Pulse: {e}")

