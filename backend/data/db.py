from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class EventCompletion(Base):
    """Model for tracking event completion status."""
    __tablename__ = 'event_completions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, nullable=False, index=True)
    is_done = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True, index=True)
    completion_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

class TaskSession(Base):
    """Model for tracking time spent on tasks."""
    __tablename__ = 'task_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    status = Column(String, nullable=False)  # 'running', 'Paused', 'done'
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

class UserXP(Base):
    """Model for tracking user XP points and levels."""
    __tablename__ = 'user_xp'
    id = Column(Integer, primary_key=True, autoincrement=True)
    total_xp = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

class XPTransaction(Base):
    """Model for logging each XP transaction (ledger)."""
    __tablename__ = 'xp_transactions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    points = Column(Integer, nullable=False)
    event_id = Column(String, nullable=True)
    description = Column(String, nullable=True)
    total_xp_after = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

class DailyXPDeduction(Base):
    """Model for tracking daily XP deduction runs."""
    __tablename__ = 'daily_xp_deduction'
    id = Column(Integer, primary_key=True, autoincrement=True)
    last_run_date = Column(DateTime, nullable=False, unique=True, index=True)
    pending_count = Column(Integer, default=0, nullable=False)
    deducted_count = Column(Integer, default=0, nullable=False)
    total_xp_deducted = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)


class CountdownTimer(Base):
    """Model for tracking multiple goal timers."""
    __tablename__ = 'countdown_timers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    total_seconds = Column(Integer, nullable=False)
    remaining_seconds = Column(Integer, nullable=False)
    is_running = Column(Boolean, default=False, nullable=False)
    last_updated_at = Column(DateTime, nullable=True) # last_updated_at can be Null before start
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

