"""
Database models and initialization.
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Integer
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
        print("Database initialized successfully")


def get_db() -> Session:
    """Get database session."""
    if _SessionLocal is None:
        init_db()
    return _SessionLocal()


def close_db():
    """Close database connection."""
    global _engine
    if _engine:
        _engine.dispose()
        _engine = None

