"""
Database models and initialization.
"""
from datetime import datetime, date
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Integer, Text, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional

from config import DATABASE_URL

Base = declarative_base()


class EventCompletion(Base):
    """Model for tracking event completion status.
    
    Allows multiple completions per event_id (for recurring tasks completed on different days).
    Each completion is unique per (event_id, DATE(completed_at)) combination.
    The unique constraint is enforced via a database index on (event_id, DATE(completed_at)).
    """
    __tablename__ = 'event_completions'
    # Note: Unique constraint is enforced via database index, not SQLAlchemy constraint
    # This allows us to use DATE(completed_at) in the uniqueness check
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, nullable=False, index=True)
    is_done = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True, index=True)  # Timestamp for when it was marked done (used for date-based uniqueness)
    completion_description = Column(Text, nullable=True)  # Description of what was accomplished
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class TaskSession(Base):
    """Model for tracking time spent on tasks."""
    __tablename__ = 'task_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # Duration in seconds
    status = Column(String, nullable=False)  # 'running', 'Paused', 'done'
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class UserXP(Base):
    """Model for tracking user XP points and levels."""
    __tablename__ = 'user_xp'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    total_xp = Column(Integer, default=0, nullable=False)  # Cumulative XP points
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class XPTransaction(Base):
    """Model for logging each XP transaction (ledger)."""
    __tablename__ = 'xp_transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    points = Column(Integer, nullable=False)  # Positive for earned, negative for deducted
    event_id = Column(String, nullable=True)  # Optional: link to event that triggered this
    description = Column(String, nullable=True)  # Optional: description of the transaction
    total_xp_after = Column(Integer, nullable=False)  # Total XP after this transaction
    created_at = Column(DateTime, default=datetime.now, nullable=False)


class DailyXPDeduction(Base):
    """Model for tracking daily XP deduction runs."""
    __tablename__ = 'daily_xp_deduction'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    last_run_date = Column(DateTime, nullable=False, unique=True, index=True)  # Date when deduction last ran
    pending_count = Column(Integer, default=0, nullable=False)
    deducted_count = Column(Integer, default=0, nullable=False)
    total_xp_deducted = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)


# Global engine and session factory
_engine = None
_SessionLocal = None


def init_db():
    """Initialize database connection and create tables."""
    global _engine, _SessionLocal
    
    if _engine is None:
        _engine = create_engine(DATABASE_URL, echo=False)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        
        # Create tables
        Base.metadata.create_all(bind=_engine)
        
        # Add missing columns if they don't exist (migration)
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(_engine)
            columns = [col['name'] for col in inspector.get_columns('event_completions')]
            
            # Add completion_description column if it doesn't exist
            if 'completion_description' not in columns:
                print("Adding completion_description column to event_completions table...")
                with _engine.connect() as conn:
                    conn.execute(text("ALTER TABLE event_completions ADD COLUMN completion_description TEXT"))
                    conn.commit()
                print("Migration completed: added completion_description column")
            
            # Migration: Remove completion_date column if it exists (we now use completed_at)
            if 'completion_date' in columns:
                print("Migrating event_completions table to remove completion_date column...")
                with _engine.connect() as conn:
                    # Drop the old unique constraint if it exists
                    try:
                        conn.execute(text("ALTER TABLE event_completions DROP CONSTRAINT IF EXISTS uq_event_completion_date"))
                        conn.commit()
                    except:
                        pass
                    
                    # Drop completion_date column
                    conn.execute(text("ALTER TABLE event_completions DROP COLUMN completion_date"))
                    conn.commit()
                    
                    # Create unique index on (event_id, DATE(completed_at)) if it doesn't exist
                    try:
                        conn.execute(text("""
                            CREATE UNIQUE INDEX IF NOT EXISTS uq_event_completion_date_idx 
                            ON event_completions (event_id, DATE(completed_at))
                            WHERE is_done = true AND completed_at IS NOT NULL
                        """))
                        conn.commit()
                    except:
                        pass
                    
                print("Migration completed: removed completion_date column, using completed_at instead")
            
            # Ensure unique index exists (for databases that never had completion_date)
            if 'completion_date' not in columns:
                try:
                    with _engine.connect() as conn:
                        # Check if index exists
                        result = conn.execute(text("""
                            SELECT indexname FROM pg_indexes 
                            WHERE tablename = 'event_completions' 
                            AND indexname = 'uq_event_completion_date_idx'
                        """))
                        if not result.fetchone():
                            # Create unique index if it doesn't exist
                            conn.execute(text("""
                                CREATE UNIQUE INDEX uq_event_completion_date_idx 
                                ON event_completions (event_id, DATE(completed_at))
                                WHERE is_done = true AND completed_at IS NOT NULL
                            """))
                            conn.commit()
                            print("Created unique index on (event_id, DATE(completed_at))")
                except Exception as e:
                    print(f"Note: Index creation check failed (may already exist): {e}")
            
            # Legacy migration code removed - we now use completed_at instead of completion_date
        except Exception as e:
            print(f"Migration check failed (this is OK if column already exists): {e}")
        
        # Initialize UserXP record if it doesn't exist (singleton pattern)
        try:
            from sqlalchemy.orm import Session
            session = Session(bind=_engine)
            xp_record = session.query(UserXP).first()
            if not xp_record:
                xp_record = UserXP(total_xp=0)
                session.add(xp_record)
                session.commit()
            session.close()
        except Exception:
            pass
        
        print("Database initialized successfully")


def get_db() -> Session:
    """Get database session."""
    if _SessionLocal is None:
        init_db()
    if _SessionLocal is None:
        raise RuntimeError("Database session factory not initialized")
    return _SessionLocal()


def close_db():
    """Close database connection."""
    global _engine
    if _engine:
        _engine.dispose()
        _engine = None

