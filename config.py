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

