import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment-specific .env file
env = os.getenv("ENVIRONMENT", "production")
if env == "development":
    # Try to load .env.development, fallback to .env if not found
    env_file = Path(".env.development")
    if env_file.exists():
        load_dotenv(".env.development")
    else:
        load_dotenv()
else:
    load_dotenv()

# Set app title based on environment
APP_TITLE = "🧠 MindOS (Phase 1)" if env == "production" else "🧠 MindOS [DEV]"

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


