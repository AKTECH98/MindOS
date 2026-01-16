"""
Left Sidebar Component
Displays Level, Total XP, and Quote in separate components.
"""
import streamlit as st

from core.xp import XPCore


def render_left_sidebar():
    """
    Render the left sidebar with Level, Total XP, and Quote components.
    """
    try:
        # Get XP info
        xp_core = XPCore()
        xp_info = xp_core.get_xp_info()
        
        total_xp = xp_info['total_xp']
        level = xp_info['level']
        
        # Inject CSS
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        
        .boss-bar-container {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            padding: 0;
        }
        
        .boss-bar-header {
            font-family: 'JetBrains Mono', monospace;
            font-size: 32px;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            letter-spacing: 2px;
            margin-bottom: 8px;
        }
        
        .xp-number {
            font-family: 'JetBrains Mono', monospace;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Level and Quote aligned together
        quote = "Don't Chase Success Become Able Success Will Chase You"
        st.markdown(
            f"""
            <div class="boss-bar-container" style="min-height: 300px; display: flex; flex-direction: column;">
                <div class="boss-bar-header" style="color: #06b6d4;">LEVEL {level}</div>
                <p style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
                   font-size: 28px; color: #64748b; font-weight: 500; font-style: italic; 
                   margin: 0; padding: 0; text-align: left; line-height: 1.8; flex: 1; display: flex; align-items: center;">
                    "{quote}"
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    except Exception as e:
        st.error(f"Error loading sidebar information: {e}")

