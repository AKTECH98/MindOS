"""
XP Bar Component
Displays user XP progress and level information.
Video game aesthetic with defrosting effects and boss-bar styling.
"""
import streamlit as st

from core.xp import XPCore


def render_xp_bar():
    """
    Render the XP progress bar showing current level and progress.
    Displays level, progress bar, and XP count for current level.
    Handles negative XP with defrosting effect (red/ice to green/gold).
    """
    try:
        # Always get fresh XP info (no caching)
        xp_core = XPCore()
        xp_info = xp_core.get_xp_info()
        
        total_xp = xp_info['total_xp']
        level = xp_info['level']
        current_level_xp = xp_info['current_level_xp']
        xp_for_next_level = xp_info['xp_for_next_level']
        
        # Inject custom CSS with refined design
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        
        .boss-bar-container {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .boss-bar-header {
            font-family: 'JetBrains Mono', monospace;
            font-size: 32px;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            letter-spacing: 2px;
            margin-bottom: 8px;
        }
        
        .status-text {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 14px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }
        
        .progress-bar-outer {
            background: #475569;
            border: 1px solid #64748b;
            border-radius: 12px;
            padding: 2px;
            position: relative;
            height: 24px;
            overflow: hidden;
            background-image: 
                linear-gradient(rgba(100, 116, 139, 0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(100, 116, 139, 0.1) 1px, transparent 1px);
            background-size: 40px 40px;
        }
        
        .progress-bar-inner {
            height: 100%;
            position: relative;
            overflow: hidden;
            border-radius: 10px;
            background: 
                repeating-linear-gradient(90deg, 
                    transparent, 
                    transparent 19px, 
                    rgba(255,255,255,0.03) 19px, 
                    rgba(255,255,255,0.03) 20px);
        }
        
        .progress-bar-segments {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            display: flex;
            gap: 0;
        }
        
        .progress-segment {
            width: 5%;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            height: 100%;
        }
        
        .progress-bar-fill {
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
            border-radius: 10px;
            transition: width 0.5s ease;
            box-shadow: 
                0 0 8px currentColor,
                inset 0 0 10px rgba(255,255,255,0.1);
        }
        
        .progress-bar-fill.negative {
            margin-left: auto;
            right: 0;
        }
        
        .progress-bar-fill.positive {
            background: #06b6d4;
            color: #06b6d4;
        }
        
        .progress-bar-fill.negative-fill {
            background: #06b6d4;
            color: #06b6d4;
        }
        
        .progress-spark {
            position: absolute;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: #ffffff;
            box-shadow: 
                0 0 6px currentColor,
                0 0 12px currentColor,
                0 0 18px currentColor;
            animation: pulse-spark 1.5s ease-in-out infinite;
            z-index: 10;
        }
        
        @keyframes pulse-spark {
            0%, 100% { 
                opacity: 1;
                transform: translate(-50%, -50%) scale(1);
            }
            50% { 
                opacity: 0.6;
                transform: translate(-50%, -50%) scale(1.5);
            }
        }
        
        .progress-text {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            font-family: 'JetBrains Mono', monospace;
            font-size: 9px;
            font-weight: 600;
            color: rgba(255,255,255,0.9);
            text-shadow: 0 0 4px rgba(0,0,0,0.8);
            pointer-events: none;
            z-index: 5;
            padding: 0 4px;
        }
        
        .progress-text.leading-edge {
            right: 0;
            margin-right: 8px;
        }
        
        .progress-text.inside {
            left: 8px;
        }
        
        .xp-label {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .xp-number {
            font-family: 'JetBrains Mono', monospace;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Progress bar only (left sidebar is separate component)
        if total_xp < 0:
            # Negative XP: defrosting effect
            # Calculate progress (how close to 0, where 0 = fully defrosted)
            max_display = 500
            progress = min(current_level_xp / max_display, 1.0)
            
            # Calculate defrost percentage (inverse: closer to 0 = more defrosted)
            # When at -500, progress = 1.0 (fully frozen)
            # When at 0, progress = 0.0 (fully defrosted)
            defrost_percentage = (1.0 - progress) * 100
            
            progress_percent = progress * 100
            
            # Create segments (20 segments for 5% each)
            segments_html = ''.join(['<div class="progress-segment"></div>' for _ in range(20)])
            
            st.markdown(
                f"""
                <div class="xp-label" style="margin-bottom: 8px;">
                    <div class="xp-number" style="font-size: 16px; font-weight: 600; color: #06b6d4; margin-bottom: 4px;">
                        {total_xp} XP
                    </div>
                    <div style="font-size: 12px; color: #64748b; font-weight: 500;">
                        {xp_for_next_level} XP to reach Level 1
                    </div>
                </div>
                <div class="progress-bar-outer">
                    <div class="progress-bar-inner">
                        <div class="progress-bar-segments">{segments_html}</div>
                        <div class="progress-bar-fill negative negative-fill" style="width: {progress_percent}%;">
                            <div class="progress-spark" style="left: 100%; color: #06b6d4;"></div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
                # Positive XP: show in smart blue, forward direction
                st.markdown(
                    f"""
                    <div class="xp-label" style="margin-bottom: 8px;">
                        <div class="xp-number" style="font-size: 16px; font-weight: 600; color: #06b6d4; margin-bottom: 4px;">
                            {current_level_xp} / 100 XP
                        </div>
                        <div style="font-size: 12px; color: #64748b; font-weight: 500;">
                            {xp_for_next_level} XP to next level
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Calculate progress percentage (0-100)
                progress = current_level_xp / 100.0
                progress_percent = progress * 100
                
                # Create segments (20 segments for 5% each)
                segments_html = ''.join(['<div class="progress-segment"></div>' for _ in range(20)])
                
                st.markdown(
                    f"""
                    <div class="progress-bar-outer">
                        <div class="progress-bar-inner">
                            <div class="progress-bar-segments">{segments_html}</div>
                            <div class="progress-bar-fill positive" style="width: {progress_percent}%;">
                                <div class="progress-spark" style="left: 100%; color: #06b6d4;"></div>
                                <div class="progress-text leading-edge">{progress_percent:.0f}%</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
    except Exception as e:
        st.error(f"Error loading XP information: {e}")
        # Show default values on error
        st.markdown("### 🎮 Level 1")
        st.progress(0.0)

