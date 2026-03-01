"""90-day countdown timer: fixed top-right on Home page (DD, HH, MM, SS + progress bar)."""
import streamlit as st
from datetime import datetime

from config import COUNTDOWN_END_DATE, COUNTDOWN_START_DATE
from ui.theme import SMART_BLUE, FONT_INTER, SLATE_BG, SLATE_BORDER, TEXT_LIGHT

MAX_DAYS = 90
TRACK_COLOR = "rgba(241,245,249,0.55)"


def _normalize_iso(date_iso: str, default_time: str) -> str:
    """Ensure ISO string has a time part."""
    s = date_iso.strip()
    return s if "T" in s else f"{s}{default_time}"


def _compute_remaining(end_iso: str, start_iso: str | None) -> tuple[int, int, int, int] | None:
    """Return (days, hours, mins, secs) remaining; None on error."""
    try:
        end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        now = datetime.now(tz=end.tzinfo) if end.tzinfo else datetime.now()
        if start_iso:
            start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
            now_cmp = datetime.now(tz=start.tzinfo) if start.tzinfo else now
            if now_cmp < start:
                delta = start - now_cmp
                return (
                    delta.days,
                    delta.seconds // 3600,
                    (delta.seconds % 3600) // 60,
                    delta.seconds % 60,
                )
        if now >= end:
            return (0, 0, 0, 0)
        delta = end - now
        return (
            delta.days,
            delta.seconds // 3600,
            (delta.seconds % 3600) // 60,
            delta.seconds % 60,
        )
    except Exception:
        return None


def _compute_bar_pct(end_iso: str, start_iso: str | None) -> float:
    """Return remaining fraction 0..1 for the progress bar."""
    try:
        end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        start = datetime.fromisoformat(start_iso.replace("Z", "+00:00")) if start_iso else None
        now = datetime.now(tz=end.tzinfo) if end.tzinfo else datetime.now()
        total_sec = (end - start).total_seconds() if start else MAX_DAYS * 86400
        if start and now < start:
            return 1.0
        if now >= end:
            return 0.0
        remaining_sec = (end - now).total_seconds()
        return min(1.0, remaining_sec / total_sec)
    except Exception:
        return 0.0


def _countdown_html(
    end_iso: str,
    start_iso: str | None,
    initial: tuple[int, int, int, int] | None,
    bar_pct: float,
) -> str:
    """Build HTML + CSS + JS for the 90-day countdown."""
    start_attr = f' data-start-iso="{start_iso}"' if start_iso else ""
    if initial is not None:
        d, h, m, s = initial
        dd, hh, mm, ss = f"{d:02d}", f"{h:02d}", f"{m:02d}", f"{s:02d}"
    else:
        dd = hh = mm = ss = "--"

    units_html = "".join(
        f"""
    <div class="countdown-90-unit">
      <span class="countdown-90-unit-label">{label}</span>
      <div class="countdown-90-circle-wrap">
        <span id="countdown-90-{id_suffix}" class="countdown-90-value">{val}</span>
      </div>
    </div>"""
        for label, id_suffix, val in [("DD", "days", dd), ("HH", "hours", hh), ("MM", "mins", mm), ("SS", "secs", ss)]
    )

    return f"""
<div id="countdown-90-container" class="countdown-90-timer" data-end-iso="{end_iso}" data-progress-color="{SMART_BLUE}"{start_attr}>
  <div class="countdown-90-label">90-day countdown</div>
  <div class="countdown-90-bar-track">
    <div id="countdown-90-bar-fill" class="countdown-90-bar-fill" style="width: {bar_pct * 100:.1f}%;"></div>
  </div>
  <div class="countdown-90-units">{units_html}
  </div>
</div>
<style>
.countdown-90-timer {{ font-family: {FONT_INTER}; background: {SLATE_BG}; border: 1px solid {SLATE_BORDER}; border-radius: 8px; padding: 0.5rem 0.75rem; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }}
.countdown-90-label {{ font-size: 11px; font-weight: 600; color: {TEXT_LIGHT}; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.35rem; }}
.countdown-90-bar-track {{ height: 6px; background: {SLATE_BORDER}; border-radius: 3px; overflow: hidden; margin-bottom: 0.5rem; }}
.countdown-90-bar-fill {{ height: 100%; background: {SMART_BLUE}; border-radius: 3px; transition: width 0.3s ease-out; }}
.countdown-90-units {{ display: flex; gap: 0.5rem; align-items: flex-start; }}
.countdown-90-unit {{ display: flex; flex-direction: column; align-items: center; min-width: 36px; }}
.countdown-90-unit-label {{ font-size: 10px; font-weight: 600; color: {TEXT_LIGHT}; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; opacity: 0.9; }}
.countdown-90-circle-wrap {{ width: 42px; height: 42px; border-radius: 50%; border: 2px solid {TRACK_COLOR}; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
.countdown-90-value {{ font-size: 11px; font-weight: 700; color: {SMART_BLUE}; }}
</style>
<script>
(function() {{
  var doc = document;
  var el = doc.getElementById("countdown-90-container");
  if (!el) {{
    var iframes = document.getElementsByTagName("iframe");
    for (var i = 0; i < iframes.length; i++) {{
      try {{
        var d = iframes[i].contentDocument;
        if (d && d.getElementById("countdown-90-container")) {{ doc = d; el = doc.getElementById("countdown-90-container"); break; }}
      }} catch (e) {{}}
    }}
  }}
  if (!el) return;
  var daysEl = doc.getElementById("countdown-90-days"), hoursEl = doc.getElementById("countdown-90-hours");
  var minsEl = doc.getElementById("countdown-90-mins"), secsEl = doc.getElementById("countdown-90-secs");
  var barFill = doc.getElementById("countdown-90-bar-fill");
  if (!daysEl) return;
  function pad(n) {{ return (n < 10 ? "0" : "") + n; }}
  function setBar(p) {{ if (barFill) barFill.style.width = (Math.max(0, Math.min(1, p)) * 100) + "%"; }}
  function tick() {{
    var end = new Date(el.getAttribute("data-end-iso"));
    var startStr = el.getAttribute("data-start-iso");
    var start = startStr ? new Date(startStr) : null;
    var now = new Date();
    var totalMs = start ? (end - start) : ({MAX_DAYS} * 86400 * 1000);
    var vals = [daysEl, hoursEl, minsEl, secsEl];
    if (start && now < start) {{
      var ms = start - now;
      vals[0].textContent = pad(Math.floor(ms / 86400000));
      vals[1].textContent = pad(Math.floor(ms / 3600000) % 24);
      vals[2].textContent = pad(Math.floor(ms / 60000) % 60);
      vals[3].textContent = pad(Math.floor(ms / 1000) % 60);
      setBar(1);
      return;
    }}
    if (now >= end) {{
      vals[0].textContent = vals[1].textContent = vals[2].textContent = vals[3].textContent = "00";
      setBar(0);
      return;
    }}
    var ms = end - now;
    vals[0].textContent = pad(Math.floor(ms / 86400000));
    vals[1].textContent = pad(Math.floor(ms / 3600000) % 24);
    vals[2].textContent = pad(Math.floor(ms / 60000) % 60);
    vals[3].textContent = pad(Math.floor(ms / 1000) % 60);
    setBar(ms / totalMs);
  }}
  tick();
  setInterval(tick, 1000);
}})();
</script>
"""


def _static_fallback(end_iso: str, start_iso: str | None) -> str:
    """Text for static fallback when JS unavailable."""
    try:
        remaining = _compute_remaining(end_iso, start_iso)
        if remaining is None:
            return "—"
        d = remaining[0]
        if start_iso:
            start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
            now = datetime.now(tz=start.tzinfo) if start.tzinfo else datetime.now()
            if now < start:
                return f"Countdown starts in {d} days"
        if remaining == (0, 0, 0, 0):
            return "0 days left"
        return f"{d} days left"
    except Exception:
        return "—"


def render_90day_countdown():
    """Render 90-day countdown in top-right (Home page). Uses st.html + JS when available."""
    end_iso = _normalize_iso(COUNTDOWN_END_DATE, "T23:59:59")
    start_iso = None
    if COUNTDOWN_START_DATE:
        start_iso = _normalize_iso(COUNTDOWN_START_DATE, "T00:00:00")

    initial = _compute_remaining(end_iso, start_iso)
    bar_pct = _compute_bar_pct(end_iso, start_iso)

    html = _countdown_html(end_iso, start_iso, initial, bar_pct)
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
