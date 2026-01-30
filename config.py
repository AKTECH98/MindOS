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

print(f"🔧 APP_ENV: {APP_ENV}")
print(f"🗄️  Database: {mask_database_url(DATABASE_URL)}")

BASE_DIR = Path(__file__).parent
TOKEN_FILE = BASE_DIR / "secrets" / "token.json"
CALENDAR_SCOPE = ["https://www.googleapis.com/auth/calendar"]
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "")


