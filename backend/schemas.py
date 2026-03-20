"""
Pydantic schemas for MindOS API request/response types.
"""
import datetime as dt
from typing import Optional, List, Dict

from pydantic import BaseModel


# ─── XP ────────────────────────────────────────────────────────────────────────

class XPInfoResponse(BaseModel):
    total_xp: int
    level: int
    current_level_xp: int
    xp_for_next_level: int


class XPTransactionResponse(BaseModel):
    id: int
    points: int
    event_id: Optional[str] = None
    description: Optional[str] = None
    total_xp_after: int
    created_at: dt.datetime

    class Config:
        from_attributes = True


# ─── Tasks (Internal) ──────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    task_name: str
    description: Optional[str] = None
    parent_task_id: Optional[str] = None
    source_type: str = "internal"
    external_id: Optional[str] = None
    task_date: Optional[dt.date] = None
    progress: int = 0
    expected_time: Optional[int] = None


class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    description: Optional[str] = None
    parent_task_id: Optional[str] = None
    source_type: Optional[str] = None
    external_id: Optional[str] = None
    task_date: Optional[dt.date] = None
    progress: Optional[int] = None
    expected_time: Optional[int] = None


class TaskResponse(BaseModel):
    task_id: str
    parent_task_id: Optional[str] = None
    source_type: str
    external_id: Optional[str] = None
    task_date: Optional[dt.date] = None
    task_name: str
    description: Optional[str] = None
    progress: int
    expected_time: Optional[int] = None
    time_spent: int = 0  # Total seconds from sessions
    task_created_on: dt.datetime
    task_updated_on: dt.datetime
    completed_at: Optional[dt.datetime] = None

    class Config:
        from_attributes = True


# ─── Task Completions (legacy Google Cal path) ─────────────────────────────────

class TaskCompletionRequest(BaseModel):
    description: str
    date: Optional[dt.date] = None


class TaskCompletionStatusItem(BaseModel):
    event_id: str
    is_done: bool
    completed_at: Optional[dt.datetime] = None
    completion_description: Optional[str] = None


class BatchCompletionStatusResponse(BaseModel):
    statuses: Dict[str, TaskCompletionStatusItem]


# ─── Sessions ──────────────────────────────────────────────────────────────────

class SessionActionResponse(BaseModel):
    success: bool
    event_id: str
    message: str


class TimeSpentResponse(BaseModel):
    event_id: str
    total_seconds: int
    formatted: str


class CurrentDurationResponse(BaseModel):
    event_id: str
    is_running: bool
    duration_seconds: Optional[int] = None


# ─── Calendar ──────────────────────────────────────────────────────────────────

class CalendarEventResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    start_time: Optional[dt.datetime] = None
    end_time: Optional[dt.datetime] = None
    is_all_day: bool
    recurrence: Optional[str] = None


class CalendarStatusResponse(BaseModel):
    authenticated: bool


class CreateEventRequest(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: dt.datetime
    end_time: dt.datetime
    is_all_day: bool = False


class UpdateEventRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[dt.datetime] = None
    end_time: Optional[dt.datetime] = None


# ─── Stats ─────────────────────────────────────────────────────────────────────

class ContributionDataResponse(BaseModel):
    contributions: Dict[str, int]
    max_count: int


class StatsOverviewResponse(BaseModel):
    total_completed: int
    completed_today: int
    completed_this_week: int
    current_streak_days: int


# ─── Countdown ─────────────────────────────────────────────────────────────────

class CreateCountdownRequest(BaseModel):
    name: str
    total_seconds: int


class CountdownResponse(BaseModel):
    id: int
    name: str
    total_seconds: int
    remaining_seconds: int
    is_running: bool
    last_updated_at: Optional[dt.datetime] = None
