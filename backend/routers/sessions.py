from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import SessionActionResponse, TimeSpentResponse, CurrentDurationResponse
from backend.utils.helpers import base_event_id
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


@router.post("/{event_id}/start", response_model=SessionActionResponse)
def start_session(event_id: str, db: Session = Depends(get_db)):
    """Start a session. Pauses any currently-running session first."""
    base_id = base_event_id(event_id)
    running = (
        db.query(TaskSession)
        .filter(TaskSession.event_id == base_id, TaskSession.status == "running")
        .first()
    )
    if running:
        now = datetime.now()
        running.duration_seconds = (running.duration_seconds or 0) + int((now - running.start_time).total_seconds())
        running.end_time = now
        running.status = "Paused"
        db.flush()

    db.add(TaskSession(event_id=base_id, start_time=datetime.now(), status="running"))
    db.commit()
    return SessionActionResponse(success=True, event_id=base_id, message="Session started.")


@router.post("/{event_id}/pause", response_model=SessionActionResponse)
def pause_session(event_id: str, db: Session = Depends(get_db)):
    """Pause the running session."""
    base_id = base_event_id(event_id)
    session = (
        db.query(TaskSession)
        .filter(TaskSession.event_id == base_id, TaskSession.status == "running")
        .first()
    )
    if not session:
        return SessionActionResponse(success=False, event_id=base_id, message="No running session.")

    now = datetime.now()
    session.duration_seconds = (session.duration_seconds or 0) + int((now - session.start_time).total_seconds())
    session.end_time = now
    session.status = "Paused"
    db.commit()
    return SessionActionResponse(success=True, event_id=base_id, message="Session paused.")


@router.get("/{event_id}/time-spent", response_model=TimeSpentResponse)
def get_time_spent(
    event_id: str,
    target_date: Optional[date] = Query(None, alias="date"),
    db: Session = Depends(get_db),
):
    """Total time spent on an event (optionally filtered by date)."""
    base_id = base_event_id(event_id)
    q = db.query(TaskSession).filter(TaskSession.event_id == base_id)
    if target_date:
        start = datetime.combine(target_date, datetime.min.time())
        q = q.filter(TaskSession.start_time >= start, TaskSession.start_time < start + timedelta(days=1))

    total = sum(
        (s.duration_seconds or 0) + (
            int((datetime.now() - s.start_time).total_seconds()) if s.status == "running" else 0
        )
        for s in q.all()
    )
    return TimeSpentResponse(event_id=base_id, total_seconds=total, formatted=_fmt(total))


@router.get("/{event_id}/current-duration", response_model=CurrentDurationResponse)
def get_current_duration(event_id: str, db: Session = Depends(get_db)):
    """Live duration of an active session."""
    base_id = base_event_id(event_id)
    session = (
        db.query(TaskSession)
        .filter(TaskSession.event_id == base_id, TaskSession.status == "running")
        .first()
    )
    if not session:
        return CurrentDurationResponse(event_id=base_id, is_running=False, duration_seconds=None)

    duration = (session.duration_seconds or 0) + int((datetime.now() - session.start_time).total_seconds())
    return CurrentDurationResponse(event_id=base_id, is_running=True, duration_seconds=duration)
