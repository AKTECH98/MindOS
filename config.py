import os
from datetime import date, timedelta
from dotenv import load_dotenv
from pathlib import Path

if not os.getenv("DATABASE_URL"):
    app_env = os.getenv("APP_ENV", "dev")
    if app_env == "dev":
        load_dotenv(".env.dev", override=False)
    else:
        load_dotenv(".env.prod", override=False)

APP_ENV = os.getenv("APP_ENV", "dev")
APP_TITLE = "🧠 MindOS [PROD]" if APP_ENV == "prod" else "🧠 MindOS [DEV]"

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not set.\n"
        'Example: export DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/personal_assistant"'
    )

def mask_database_url(url: str) -> str:
    """Mask password in database URL for display."""
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        if parsed.password:
            masked_netloc = parsed.netloc.replace(f":{parsed.password}@", ":***@")
            parsed = parsed._replace(netloc=masked_netloc)
            return urlunparse(parsed)
    except Exception:
        pass
    return url

BASE_DIR = Path(__file__).parent
TOKEN_FILE = BASE_DIR / "secrets" / "token.json"
CALENDAR_SCOPE = ["https://www.googleapis.com/auth/calendar"]
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "")

# 90-day countdown: optional start date (countdown shows "Countdown starts in ..." before this).
# If COUNTDOWN_START_DATE is set, end is derived as start + 90 days. If only COUNTDOWN_END_DATE
# is set, no pre-start phase. If neither set, default start is 2026-02-14 and end is start + 90.
_countdown_start_env = os.getenv("COUNTDOWN_START_DATE")
_countdown_end_env = os.getenv("COUNTDOWN_END_DATE")
if _countdown_start_env:
    _start_d = date.fromisoformat(_countdown_start_env.strip())
    COUNTDOWN_START_DATE = _countdown_start_env.strip()
    COUNTDOWN_END_DATE = (_start_d + timedelta(days=90)).isoformat()
elif _countdown_end_env:
    COUNTDOWN_START_DATE = None
    COUNTDOWN_END_DATE = _countdown_end_env.strip()
else:
    COUNTDOWN_START_DATE = "2026-02-14"
    _start_d = date.fromisoformat(COUNTDOWN_START_DATE)
    COUNTDOWN_END_DATE = (_start_d + timedelta(days=90)).isoformat()


