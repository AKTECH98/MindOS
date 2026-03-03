import os
from dotenv import load_dotenv
from pathlib import Path

if not os.getenv("DATABASE_URL"):
    app_env = os.getenv("APP_ENV", "dev")
    if app_env == "dev":
        load_dotenv(".env.dev", override=False)
    else:
        load_dotenv(".env.prod", override=False)

APP_ENV = os.getenv("APP_ENV", "dev")

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

BASE_DIR = Path(__file__).parent.parent  # project root (parent of backend/)
TOKEN_FILE = BASE_DIR / "secrets" / "token.json"
CALENDAR_SCOPE = ["https://www.googleapis.com/auth/calendar"]




# XP awarded per task completion
XP_PER_TASK = 5
