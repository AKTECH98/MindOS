"""90-day countdown timer: fixed top-right on Home page (Days, Hours, Seconds)."""
import streamlit as st
from datetime import datetime

from config import COUNTDOWN_END_DATE, COUNTDOWN_START_DATE
from ui.theme import SMART_BLUE, SLATE_GREY, FONT_INTER, SLATE_BG, SLATE_BORDER


def _countdown_html(
    end_iso: str,
    start_iso: str | None,
    smart_blue: str,
    slate_grey: str,
    font_inter: str,
    slate_bg: str,
    slate_border: str,
) -> str:
    """Build HTML + CSS + JS for the 90-day countdown (client-side tick)."""
    start_attr = f' data-start-iso="{start_iso}"' if start_iso else ""
    return f"""
<div id="countdown-90-container" class="countdown-90-timer" data-end-iso="{end_iso}"{start_attr}>
  <div class="countdown-90-label">90-day countdown</div>
  <div id="countdown-90-value" class="countdown-90-value">-- days · -- hours · -- mins · -- secs</div>
</div>
<style>
.countdown-90-timer {{
  position: fixed;
  top: 4.5rem;
  right: 1rem;
  z-index: 999;
  font-family: {font_inter};
  background: {slate_bg};
  border: 1px solid {slate_border};
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}}
.countdown-90-label {{
  font-size: 11px;
  font-weight: 600;
  color: black;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}}
.countdown-90-value {{
  font-size: 14px;
  font-weight: 600;
  color: {smart_blue};
}}
</style>
<script>
(function() {{
  var el = document.getElementById('countdown-90-container');
  if (!el) return;
  var valueEl = document.getElementById('countdown-90-value');
  var endStr = el.getAttribute('data-end-iso');
  var startStr = el.getAttribute('data-start-iso');
  var end = new Date(endStr);
  var start = startStr ? new Date(startStr) : null;
  function tick() {{
    var now = new Date();
    if (start && now < start) {{
      var ms = start - now;
      var secs = Math.floor(ms / 1000) % 60;
      var mins = Math.floor(ms / 60000) % 60;
      var hours = Math.floor(ms / 3600000) % 24;
      var days = Math.floor(ms / 86400000);
      valueEl.textContent = 'Countdown starts in ' + days + ' days · ' + hours + ' hours · ' + mins + ' mins · ' + secs + ' secs';
      return;
    }}
    if (now >= end) {{
      valueEl.textContent = '0 days · 0 hours · 0 mins · 0 secs';
      return;
    }}
    var ms = end - now;
    var secs = Math.floor(ms / 1000) % 60;
    var mins = Math.floor(ms / 60000) % 60;
    var hours = Math.floor(ms / 3600000) % 24;
    var days = Math.floor(ms / 86400000);
    valueEl.textContent = days + ' days · ' + hours + ' hours · ' + mins + ' mins · ' + secs + ' secs';
  }}
  tick();
  setInterval(tick, 1000);
}})();
</script>
"""


def _static_fallback(end_iso: str, start_iso: str | None = None) -> str:
    """Compute remaining time for static fallback (no JS)."""
    try:
        end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        now = datetime.now()
        if end.tzinfo:
            now = datetime.now(tz=end.tzinfo)
        if start_iso:
            start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
            now_cmp = datetime.now(tz=start.tzinfo) if start.tzinfo else datetime.now()
            if now_cmp < start:
                delta = start - now_cmp
                return f"Countdown starts in {delta.days} days"
        if now >= end:
            return "0 days left"
        delta = end - now
        return f"{delta.days} days left"
    except Exception:
        return "—"


def render_90day_countdown():
    """Render 90-day countdown in top-right (Home page only). Uses st.html + JS when available."""
    end_iso = COUNTDOWN_END_DATE.strip()
    if "T" not in end_iso:
        end_iso = end_iso + "T23:59:59"
    start_iso = None
    if COUNTDOWN_START_DATE:
        start_iso = COUNTDOWN_START_DATE.strip()
        if "T" not in start_iso:
            start_iso = start_iso + "T00:00:00"

    html = _countdown_html(
        end_iso,
        start_iso,
        smart_blue=SMART_BLUE,
        slate_grey=SLATE_GREY,
        font_inter=FONT_INTER,
        slate_bg=SLATE_BG,
        slate_border=SLATE_BORDER,
    )
    if hasattr(st, "html"):
        st.html(html, unsafe_allow_javascript=True)
    else:
        static_text = _static_fallback(end_iso, start_iso)
        st.markdown(
            f'<div style="position:fixed;top:4.5rem;right:1rem;z-index:999;font-family:{FONT_INTER};'
            f'background:{SLATE_BG};border:1px solid {SLATE_BORDER};border-radius:8px;padding:0.5rem 0.75rem;'
            f'color:{SMART_BLUE};font-weight:600;">90-day: {static_text}</div>',
            unsafe_allow_html=True,
        )
