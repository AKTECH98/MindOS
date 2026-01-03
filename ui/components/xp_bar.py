"""
XP Bar Component
Displays user XP progress and level information.
"""
import streamlit as st

from services.xp_service import XPService


def render_xp_bar():
    """
    Render the XP progress bar showing current level and progress.
    Displays level, progress bar, and XP count for current level.
    Handles negative XP with red color and backward direction.
    """
    try:
        # Always get fresh XP info (no caching)
        xp_info = XPService.get_xp_info()
        
        total_xp = xp_info['total_xp']
        level = xp_info['level']
        current_level_xp = xp_info['current_level_xp']
        xp_for_next_level = xp_info['xp_for_next_level']
        
        # Create columns for level and progress bar
        col_level, col_progress = st.columns([1, 4])
        
        with col_level:
            # Show level and total XP with color based on sign
            if total_xp < 0:
                st.markdown(f"### 🎮 Level {level}")
                st.caption(f"**Total: <span style='color: red;'>{total_xp} XP</span>**", unsafe_allow_html=True)
            else:
                st.markdown(f"### 🎮 Level {level}")
                st.caption(f"**Total: <span style='color: green;'>{total_xp} XP</span>**", unsafe_allow_html=True)
        
        with col_progress:
            if total_xp < 0:
                # Negative XP: show in red, backward direction
                st.markdown(f"**<span style='color: red;'>{current_level_xp} / 100 XP (Below Zero)</span>** ({xp_for_next_level} XP to reach 0)", unsafe_allow_html=True)
                
                # For negative XP, show progress bar in red (backward from right)
                # Progress bar shows how far below 0 we are
                progress = current_level_xp / 100.0
                st.markdown(
                    f"""
                    <div style="background-color: #f0f0f0; border-radius: 4px; padding: 2px; position: relative;">
                        <div style="background-color: #ff4444; width: {progress * 100}%; height: 20px; border-radius: 4px; margin: 0; margin-left: auto;"></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Positive XP: show in green, forward direction
                st.markdown(f"**<span style='color: green;'>{current_level_xp} / 100 XP</span>** ({xp_for_next_level} XP to next level)", unsafe_allow_html=True)
                
                # Calculate progress percentage (0-100)
                progress = current_level_xp / 100.0
                
                # Display progress bar in green
                st.markdown(
                    f"""
                    <div style="background-color: #f0f0f0; border-radius: 4px; padding: 2px;">
                        <div style="background-color: #44ff44; width: {progress * 100}%; height: 20px; border-radius: 4px; margin: 0;"></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
    except Exception as e:
        st.error(f"Error loading XP information: {e}")
        # Show default values on error
        st.markdown("### 🎮 Level 1")
        st.progress(0.0)

