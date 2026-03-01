"""MindOS UI theme: colors, fonts, global and page-specific CSS."""
SMART_BLUE = "#06b6d4"
SLATE_GREY = "#64748b"
SLATE_BG = "#475569"
SLATE_BORDER = "#64748b"
TEXT_LIGHT = "#f1f5f9"
CONTRIB_COLORS = ["#64748b", "#67e8f9", "#22d3ee", "#06b6d4", "#0891b2"]
BTN_START_GREEN = "#22c55e"
BTN_PAUSE_RED = "#ef4444"
FONT_INTER = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --smart-blue: #06b6d4;
    --slate-grey: #64748b;
    --slate-bg: #475569;
    --slate-border: #64748b;
    --input-bg: #334155;
    --placeholder-color: #b8c5d6;
}
body, .stApp, [data-testid="stAppViewContainer"],
main, main .block-container, main section,
main > div, main section > div {
    border: none !important;
    box-shadow: none !important;
}
main [data-testid="stVerticalBlock"]:not(.task-panel-outer) {
    border: none !important;
}

main [data-testid="stHorizontalBlock"] > div,
[data-testid="stHorizontalBlock"] > div {
    border: none !important;
}
.task-panel-outer {
    border: 1px solid var(--slate-border) !important;
    border-radius: 8px;
    padding: 0.25rem 1rem 1rem 1rem;
    position: sticky;
    top: 1rem;
    max-height: 70vh;
    overflow-y: auto;
}
.task-panel-outer [data-testid="stVerticalBlock"],
.task-panel-outer [data-testid="stHorizontalBlock"],
.task-panel-outer [data-testid="stHorizontalBlock"] > div {
    border: none !important;
    box-shadow: none !important;
}

.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Reduce gap between main content and sidebar (space between them only) */
.stApp [data-testid="stAppViewContainer"] {
    margin-right: 0 !important;
}
.stApp [data-testid="stSidebar"] {
    margin-left: 0 !important;
}
/* If layout uses flex gap between main and sidebar */
.stApp > div:first-child {
    gap: 0.25rem !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--smart-blue);
}

.stButton > button {
    background-color: var(--slate-bg);
    color: var(--smart-blue);
    border: 1px solid var(--slate-border);
    border-radius: 8px;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-weight: 500;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background-color: var(--smart-blue);
    color: white;
    border-color: var(--smart-blue);
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select {
    background-color: var(--input-bg) !important;
    border: 1px solid var(--slate-border);
    border-radius: 8px;
    color: #f1f5f9;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: var(--placeholder-color) !important;
    opacity: 1;
}

.stDateInput > div > div > input {
    background-color: var(--slate-bg);
    border: 1px solid var(--slate-border);
    border-radius: 8px;
    color: var(--smart-blue);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stCheckbox > label {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--slate-grey);
}

.stInfo, .stSuccess, .stWarning, .stError {
    border-left: 4px solid var(--smart-blue);
    border-radius: 4px;
}

.number, [class*="number"] {
    font-family: 'JetBrains Mono', monospace;
}
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

PAGE_HOME_CSS = """
<style>
body:has(#page-is-home) main,
body:has(#page-is-home) main > div,
body:has(#page-is-home) main .block-container,
body:has(#page-is-home) main section,
body:has(#page-is-home) main section > div {
    border: none !important;
    box-shadow: none !important;
}
body:has(#page-is-home) main [data-testid="stVerticalBlock"]:not(.task-panel-outer),
body:has(#page-is-home) main [data-testid="stHorizontalBlock"],
body:has(#page-is-home) main [data-testid="stHorizontalBlock"] > div {
    border: none !important;
}
body:has(#page-is-home) [data-testid="stHorizontalBlock"] > div:first-child .stTextInput {
    max-width: 50% !important;
    width: 50% !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
body:has(#page-is-home) [data-testid="stHorizontalBlock"] > div:first-child .stTextInput input {
    border-radius: 16px !important;
}
/* Tighten gap between Level and XP bar in right column */
body:has(#page-is-home) [data-testid="stHorizontalBlock"] > div:last-child > [data-testid="stVerticalBlock"] {
    gap: 0.5rem !important;
}
</style>
"""
