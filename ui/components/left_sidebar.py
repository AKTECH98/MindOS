"""Left sidebar: level and quote."""
import streamlit as st

from core.xp import XPCore
from ui.theme import SMART_BLUE, SLATE_GREY, FONT_INTER


_LEFT_SIDEBAR_CSS = """
<style>
.boss-bar-container { padding: 0; }
.boss-bar-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 32px;
    font-weight: 700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    letter-spacing: 2px;
    margin-bottom: 8px;
}
.xp-number { font-family: 'JetBrains Mono', monospace; }
</style>
"""


def render_left_sidebar():
    """Render sidebar with level and quote."""
    try:
        xp_core = XPCore()
        xp_info = xp_core.get_xp_info()
        level = xp_info['level']
        quote = "Don't Chase Success Become Able Success Will Chase You"

        st.markdown(_LEFT_SIDEBAR_CSS, unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="boss-bar-container" style="min-height: 300px; display: flex; flex-direction: column;">
                <div class="boss-bar-header" style="color: {SMART_BLUE};">LEVEL {level}</div>
                <p style="font-family: {FONT_INTER}; font-size: 28px; color: {SLATE_GREY}; font-weight: 500; font-style: italic;
                   margin: 0; padding: 0; text-align: left; line-height: 1.8; flex: 1; display: flex; align-items: center;">
                    "{quote}"
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Error loading sidebar information: {e}")
