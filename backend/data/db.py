import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()

class Task(Base):
    """First-class task record owned by MindOS."""
    __tablename__ = 'tasks'
    task_id               = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_task_id        = Column(String(36), ForeignKey('tasks.task_id'), nullable=True, index=True)
    source_type           = Column(String(20), nullable=False, default='internal')  # 'internal' | 'google_cal'
    external_id           = Column(String, nullable=True, index=True)   # Google Cal event ID
    task_date             = Column(Date, nullable=True, index=True)      # The calendar date this task belongs to
    task_name             = Column(String, nullable=False)
    description           = Column(Text, nullable=True)                  # completion description / notes
    progress              = Column(Integer, default=0, nullable=False)   # 0-100
    expected_time         = Column(Integer, nullable=True)               # Store allotted time in seconds
    task_created_on       = Column(DateTime, default=datetime.now, nullable=False)
    task_updated_on       = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Each Google Cal event on a specific date is a unique task
    __table_args__ = (
        UniqueConstraint('external_id', 'task_date', name='uq_task_external_date'),
    )

    subtasks = relationship(
        'Task', 
        backref=backref('parent', remote_side=[task_id]), 
        lazy='dynamic',
        foreign_keys=[parent_task_id]
    )


class EventCompletion(Base):
    """Model for tracking task completion status."""
    __tablename__ = 'event_completions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Internal task UUID — the new primary reference
    task_id  = Column(String(36), ForeignKey('tasks.task_id'), nullable=True, index=True)
    is_done = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True, index=True)
    completion_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

class TaskSession(Base):
    """Model for tracking time spent on tasks."""
    __tablename__ = 'task_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id  = Column(String(36), ForeignKey('tasks.task_id'), nullable=True, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    status = Column(String, nullable=False)  # 'running', 'paused', 'done'
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
    task_id  = Column(String(36), ForeignKey('tasks.task_id'), nullable=True, index=True)
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
