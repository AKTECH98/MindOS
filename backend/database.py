"""
Database setup for MindOS FastAPI backend.
sys.path is set by main.py before this module is imported.

Task backfilling is handled by the separate script:
    python -m backend.utils.backfill_tasks
"""
import os
import sys
from datetime import datetime
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
    """
    Initialize the database: create all tables (if not exist) and run lightweight
    column migrations. Task backfilling is handled by the separate script:
        python -m backend.utils.backfill_tasks
    """
    from .data.db import Base, UserXP  # noqa: F401

    # Create all tables (idempotent — no-op if they already exist)
    Base.metadata.create_all(bind=engine)

    # ── Lightweight column migrations ─────────────────────────────────────────
    with engine.connect() as conn:
        inspector = inspect(engine)

        # event_completions: ensure task_id and completion_description exist
        if 'event_completions' in inspector.get_table_names():
            ec_cols = [c['name'] for c in inspector.get_columns('event_completions')]
            if 'completion_description' not in ec_cols:
                conn.execute(text("ALTER TABLE event_completions ADD COLUMN completion_description TEXT"))
                conn.commit()
            if 'task_id' not in ec_cols:
                conn.execute(text("ALTER TABLE event_completions ADD COLUMN task_id VARCHAR(36)"))
                conn.commit()
            if 'event_id' not in ec_cols:
                conn.execute(text("ALTER TABLE event_completions ADD COLUMN event_id VARCHAR"))
                conn.commit()
            else:
                try:
                    conn.execute(text("ALTER TABLE event_completions ALTER COLUMN event_id DROP NOT NULL"))
                    conn.commit()
                except Exception:
                    pass  # already nullable

        # task_sessions: ensure task_id exists
        if 'task_sessions' in inspector.get_table_names():
            ts_cols = [c['name'] for c in inspector.get_columns('task_sessions')]
            if 'task_id' not in ts_cols:
                conn.execute(text("ALTER TABLE task_sessions ADD COLUMN task_id VARCHAR(36)"))
                conn.commit()
        # xp_transactions: ensure task_id exists
        if 'xp_transactions' in inspector.get_table_names():
            xp_cols = [c['name'] for c in inspector.get_columns('xp_transactions')]
            if 'task_id' not in xp_cols:
                conn.execute(text("ALTER TABLE xp_transactions ADD COLUMN task_id VARCHAR(36)"))
                conn.commit()
            if 'event_id' not in xp_cols:
                conn.execute(text("ALTER TABLE xp_transactions ADD COLUMN event_id VARCHAR"))
                conn.commit()

        # tasks: Migration to rename expected_completion_at -> expected_time
        if 'tasks' in inspector.get_table_names():
            task_cols = [c['name'] for c in inspector.get_columns('tasks')]
            # Renames and type migrations
            if 'expected_completion_at' in task_cols:
                try:
                    # Rename
                    conn.execute(text("ALTER TABLE tasks RENAME COLUMN expected_completion_at TO expected_time"))
                    conn.commit()
                    print("✅ Migrated tasks.expected_completion_at to expected_time")
                    # Postgres specific: also fix the type from timestamp -> integer
                    if engine.dialect.name == 'postgresql':
                         conn.execute(text("ALTER TABLE tasks ALTER COLUMN expected_time TYPE INTEGER USING (NULL)"))
                         conn.commit()
                         print("✅ Corrected expected_time type to INTEGER for PostgreSQL")
                except Exception as e:
                    print(f"⚠️  Could not rename/retype column via ALTER: {e}")
            elif 'expected_time' in task_cols and engine.dialect.name == 'postgresql':
                 # Check if it is a timestamp (legacy from old schema)
                 col = [c for c in inspector.get_columns('tasks') if c['name'] == 'expected_time'][0]
                 if 'TIMESTAMP' in str(col['type']).upper():
                     try:
                        conn.execute(text("ALTER TABLE tasks ALTER COLUMN expected_time TYPE INTEGER USING (NULL)"))
                        conn.commit()
                        print("✅ Corrected existing expected_time type to INTEGER for PostgreSQL")
                     except Exception as e:
                        print(f"⚠️  Could not retype existing column for PostgreSQL: {e}")
            elif 'expected_time' not in task_cols:
                # Add it if missing
                conn.execute(text("ALTER TABLE tasks ADD COLUMN expected_time INTEGER"))
                conn.commit()

    # ── Seed singleton records ────────────────────────────────────────────────
    db = SessionLocal()
    try:
        if not db.query(UserXP).first():
            db.add(UserXP(total_xp=0))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
