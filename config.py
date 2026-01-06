import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
APP_TITLE = "🧠 MindOS (Phase 1)"
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not set.\n"
        'Example: export DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/personal_assistant"'
    )

# Google Calendar API Configuration
BASE_DIR = Path(__file__).parent
TOKEN_FILE = BASE_DIR / "secrets" / "token.json"
CALENDAR_SCOPE = ["https://www.googleapis.com/auth/calendar"]

# Gemini AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Discord Bot Configuration
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "")


