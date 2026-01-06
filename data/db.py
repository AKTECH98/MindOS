"""
Database models and initialization.
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional

from config import DATABASE_URL

Base = declarative_base()


class EventCompletion(Base):
    """Model for tracking event completion status."""
    __tablename__ = 'event_completions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, unique=True, nullable=False, index=True)
    is_done = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    completion_description = Column(Text, nullable=True)  # Description of what was accomplished
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TaskSession(Base):
    """Model for tracking time spent on tasks."""
    __tablename__ = 'task_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # Duration in seconds
    status = Column(String, nullable=False)  # 'running', 'Paused', 'done'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UserXP(Base):
    """Model for tracking user XP points and levels."""
    __tablename__ = 'user_xp'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    total_xp = Column(Integer, default=0, nullable=False)  # Cumulative XP points
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class XPTransaction(Base):
    """Model for logging each XP transaction (ledger)."""
    __tablename__ = 'xp_transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    points = Column(Integer, nullable=False)  # Positive for earned, negative for deducted
    event_id = Column(String, nullable=True)  # Optional: link to event that triggered this
    description = Column(String, nullable=True)  # Optional: description of the transaction
    total_xp_after = Column(Integer, nullable=False)  # Total XP after this transaction
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DailyXPDeduction(Base):
    """Model for tracking daily XP deduction runs."""
    __tablename__ = 'daily_xp_deduction'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    last_run_date = Column(DateTime, nullable=False, unique=True, index=True)  # Date when deduction last ran
    pending_count = Column(Integer, default=0, nullable=False)
    deducted_count = Column(Integer, default=0, nullable=False)
    total_xp_deducted = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


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

