"""
Database setup for MindOS FastAPI backend.
sys.path is set by main.py before this module is imported.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from dotenv import load_dotenv

# Load .env if DATABASE_URL not already set
if not os.getenv("DATABASE_URL"):
    project_root = Path(__file__).parent.parent
    app_env = os.getenv("APP_ENV", "dev")
    load_dotenv(project_root / f".env.{app_env}", override=False)

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set.")

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database connection, create tables, and run migrations."""
    from .data.db import Base, UserXP
    
    # Core table creation
    Base.metadata.create_all(bind=engine)
    
    # Migrations & Seeding
    with engine.connect() as conn:
        inspector = inspect(engine)
        
        # 1. Ensure completion_description exists
        cols = [c['name'] for c in inspector.get_columns('event_completions')]
        if 'completion_description' not in cols:
            conn.execute(text("ALTER TABLE event_completions ADD COLUMN completion_description TEXT"))
            conn.commit()
            
        # 2. Ensure unique index on (event_id, date(completed_at))
        # PostgreSQL specific syntax for creating a unique index on a date cast
        try:
            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_event_completion_date_idx 
                ON event_completions (event_id, (completed_at::date))
                WHERE is_done = true AND completed_at IS NOT NULL
            """))
            conn.commit()
        except Exception as e:
            print(f"Index migration note: {e}")

    # Seed singleton records
    db = SessionLocal()
    try:
        if not db.query(UserXP).first():
            db.add(UserXP(total_xp=0))
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
