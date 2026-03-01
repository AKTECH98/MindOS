"""Task completion endpoints."""
from datetime import date, datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.config import XP_PER_TASK
from backend.database import get_db
from backend.schemas import (
    TaskCompletionRequest,
    BatchCompletionStatusResponse,
    TaskCompletionStatusItem,
)
from backend.utils.helpers import base_event_id
from backend.data.db import EventCompletion, UserXP, XPTransaction

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/completion-status", response_model=BatchCompletionStatusResponse)
def get_completion_status(
    event_ids: str = Query(..., description="Comma-separated event IDs"),
    target_date: Optional[date] = Query(None, alias="date"),
    db: Session = Depends(get_db),
):
    """Batch-fetch completion status for multiple events on a date."""
    target_date = target_date or date.today()
    ids = [base_event_id(e.strip()) for e in event_ids.split(",") if e.strip()]
    raw_ids = [e.strip() for e in event_ids.split(",") if e.strip()]

    completions = (
        db.query(EventCompletion)
        .filter(
            EventCompletion.event_id.in_(ids),
            func.date(EventCompletion.completed_at) == target_date,
            EventCompletion.is_done == True,
        )
        .all()
    )

    result = {
        c.event_id: TaskCompletionStatusItem(
            event_id=c.event_id,
            is_done=True,
            completed_at=c.completed_at,
            completion_description=c.completion_description,
        )
        for c in completions
    }
    # Fill in missing (not-done) events — keyed by the raw (suffixed) ID so the frontend matches
    raw_to_base = {base_event_id(r): r for r in raw_ids}
    for base_id in ids:
        if base_id not in result:
            result[base_id] = TaskCompletionStatusItem(
                event_id=base_id, is_done=False, completed_at=None, completion_description=None,
            )
    # Re-key by raw event IDs so frontend lookups work (frontend uses the full suffixed ID)
    return BatchCompletionStatusResponse(statuses={
        raw_to_base.get(base_id, base_id): item
        for base_id, item in result.items()
    })


@router.post("/{event_id}/done")
def mark_event_done(
    event_id: str,
    body: TaskCompletionRequest,
    db: Session = Depends(get_db),
):
    """Mark a task as done (requires description) and award XP."""
    base_id = base_event_id(event_id)
    if not body.description or not body.description.strip():
        raise HTTPException(status_code=422, detail="Description is required.")

    completion_date = body.date or date.today()
    if completion_date != date.today():
        raise HTTPException(status_code=400, detail="Can only mark today's tasks as done.")

    now = datetime.now()
    existing = (
        db.query(EventCompletion)
        .filter(
            EventCompletion.event_id == base_id,
            func.date(EventCompletion.completed_at) == completion_date,
            EventCompletion.is_done == True,
        )
        .first()
    )

    if existing:
        existing.completed_at = now
        existing.completion_description = body.description.strip()
        existing.updated_at = now
        db.commit()
        return {"success": True, "event_id": base_id, "xp_awarded": 0, "completed_at": now.isoformat()}

    db.add(EventCompletion(
        event_id=base_id,
        is_done=True,
        completed_at=now,
        completion_description=body.description.strip(),
    ))
    db.flush()

    xp = db.query(UserXP).first()
    if not xp:
        xp = UserXP(total_xp=0)
        db.add(xp)
        db.flush()
    xp.total_xp += XP_PER_TASK
    db.add(XPTransaction(
        points=XP_PER_TASK, event_id=base_id,
        description=f"Completed: {base_id}", total_xp_after=xp.total_xp, created_at=now,
    ))
    db.commit()
    return {"success": True, "event_id": base_id, "xp_awarded": XP_PER_TASK, "completed_at": now.isoformat()}


@router.delete("/{event_id}/done")
def mark_event_undone(
    event_id: str,
    target_date: Optional[date] = Query(None, alias="date"),
    db: Session = Depends(get_db),
):
    """Mark a task as undone and deduct XP."""
    base_id = base_event_id(event_id)
    completion_date = target_date or date.today()
    if completion_date != date.today():
        raise HTTPException(status_code=400, detail="Can only undo today's tasks.")

    record = (
        db.query(EventCompletion)
        .filter(
            EventCompletion.event_id == base_id,
            func.date(EventCompletion.completed_at) == completion_date,
            EventCompletion.is_done == True,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No completion found for this event today.")

    record.is_done = False
    record.completed_at = None
    record.updated_at = datetime.now()
    db.flush()

    xp = db.query(UserXP).first()
    if xp:
        xp.total_xp -= XP_PER_TASK
        db.add(XPTransaction(
            points=-XP_PER_TASK, event_id=base_id,
            description=f"Undone: {base_id}", total_xp_after=xp.total_xp,
        ))
    db.commit()
    return {"success": True, "event_id": base_id, "xp_deducted": XP_PER_TASK}
