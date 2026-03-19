from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import SessionActionResponse, TimeSpentResponse, CurrentDurationResponse
from backend.data.db import TaskSession

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _fmt(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    parts = []
    if h: parts.append(f"{h}h")
    if m or h: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts) if seconds > 0 else "0s"


import uuid

@router.post("/{task_id}/start", response_model=SessionActionResponse)
def start_session(task_id: str, db: Session = Depends(get_db)):
    """Start a session. Pauses any currently-running session first."""
    # Pause any other running session globally
    running_any = (
        db.query(TaskSession)
        .filter(TaskSession.status == "running")
        .all()
    )
    for r in running_any:
        now = datetime.now()
        r.duration_seconds = (r.duration_seconds or 0) + int((now - r.start_time).total_seconds())
        r.end_time = now
        r.status = "Paused"
    
    db.flush()
    db.add(TaskSession(task_id=task_id, start_time=datetime.now(), status="running"))
    
    db.commit()
    return SessionActionResponse(success=True, event_id=task_id, message="Session started.")


@router.post("/{task_id}/pause", response_model=SessionActionResponse)
def pause_session(task_id: str, db: Session = Depends(get_db)):
    """Pause the running session."""
    session = db.query(TaskSession).filter(
        TaskSession.status == "running",
        TaskSession.task_id == task_id
    ).first()
    
    if not session:
        return SessionActionResponse(success=False, event_id=task_id, message="No running session.")

    now = datetime.now()
    session.duration_seconds = (session.duration_seconds or 0) + int((now - session.start_time).total_seconds())
    session.end_time = now
    session.status = "Paused"
    db.commit()
    return SessionActionResponse(success=True, event_id=task_id, message="Session paused.")


@router.get("/{task_id}/time-spent", response_model=TimeSpentResponse)
def get_time_spent(
    task_id: str,
    target_date: Optional[date] = Query(None, alias="date"),
    db: Session = Depends(get_db),
):
    """Total time spent on a task (optionally filtered by date)."""
    q = db.query(TaskSession).filter(TaskSession.task_id == task_id)

    if target_date:
        start = datetime.combine(target_date, datetime.min.time())
        q = q.filter(TaskSession.start_time >= start, TaskSession.start_time < start + timedelta(days=1))

    total = sum(
        (s.duration_seconds or 0) + (
            int((datetime.now() - s.start_time).total_seconds()) if s.status == "running" else 0
        )
        for s in q.all()
    )
    return TimeSpentResponse(event_id=task_id, total_seconds=total, formatted=_fmt(total))


@router.get("/{task_id}/current-duration", response_model=CurrentDurationResponse)
def get_current_duration(task_id: str, db: Session = Depends(get_db)):
    """Live duration of an active session."""
    session = db.query(TaskSession).filter(
        TaskSession.status == "running",
        TaskSession.task_id == task_id
    ).first()
    
    if not session:
        return CurrentDurationResponse(event_id=task_id, is_running=False, duration_seconds=None)

    duration = (session.duration_seconds or 0) + int((datetime.now() - session.start_time).total_seconds())
    return CurrentDurationResponse(event_id=task_id, is_running=True, duration_seconds=duration)
