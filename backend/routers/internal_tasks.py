"""CRUD endpoints for internal Tasks table."""
import sys
import uuid
from pathlib import Path
from typing import List, Optional, Dict

from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, Integer
import sqlalchemy

from backend.database import get_db
from backend.schemas import TaskCreate, TaskUpdate, TaskResponse
from backend.data.db import Task, TaskSession, UserXP, EventCompletion, XPTransaction

router = APIRouter(prefix="/internal-tasks", tags=["Internal Tasks"])


def get_duration_seconds(start, end):
    if not start or not end:
        return None
    delta = end - start
    return int(delta.total_seconds())


from sqlalchemy import func
from backend.data.db import Task, TaskSession

@router.get("", response_model=List[TaskResponse])
def list_tasks(
    parent_task_id: Optional[str] = Query(None, description="Filter by parent task id. Pass 'root' to get top-level tasks only."),
    db: Session = Depends(get_db),
):
    """List all tasks. Optionally filter by parent_task_id."""
    # Subquery for cumulative time (including currently running sessions)
    now = func.now()
    session_sum = (
        db.query(
            TaskSession.task_id, 
            func.cast(
                func.sum(
                    func.coalesce(TaskSession.duration_seconds, 0) + 
                    case(
                        (TaskSession.status == "running", func.extract('epoch', now - TaskSession.start_time)),
                        else_=0
                    )
                ),
                sqlalchemy.Integer
            ).label("total")
        )
        .group_by(TaskSession.task_id)
        .subquery()
    )

    q = db.query(
        Task, 
        func.coalesce(session_sum.c.total, 0).label("time_spent"),
        EventCompletion.completed_at
    ).outerjoin(
        session_sum, Task.task_id == session_sum.c.task_id
    ).outerjoin(
        EventCompletion, Task.task_id == EventCompletion.task_id
    )

    if parent_task_id == "root":
        q = q.filter(Task.parent_task_id.is_(None))
    elif parent_task_id is not None:
        q = q.filter(Task.parent_task_id == parent_task_id)

    results = q.order_by(Task.task_created_on.asc()).all()
    
    # Map results to TaskResponse
    resp = []
    for task, time_spent, completed_at in results:
        task_dict = {c.name: getattr(task, c.name) for c in task.__table__.columns}
        task_dict["time_spent"] = time_spent
        task_dict["completed_at"] = completed_at
        resp.append(task_dict)
    return resp


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """Fetch a single task by its UUID."""
    # Subquery for sum of session durations (including running)
    now = func.now()
    total_time = (
        db.query(
            func.cast(
                func.sum(
                    func.coalesce(TaskSession.duration_seconds, 0) + 
                    case(
                        (TaskSession.status == "running", func.extract('epoch', now - TaskSession.start_time)),
                        else_=0
                    )
                ),
                Integer
            )
        )
        .filter(TaskSession.task_id == task_id)
        .scalar()
    ) or 0

    # Join with completion
    res = (
        db.query(Task, EventCompletion.completed_at)
        .outerjoin(EventCompletion, Task.task_id == EventCompletion.task_id)
        .filter(Task.task_id == task_id)
        .first()
    )
    if not res:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task, completed_at = res
    task_dict = {c.name: getattr(task, c.name) for c in task.__table__.columns}
    task_dict["time_spent"] = total_time
    task_dict["completed_at"] = completed_at
    return task_dict


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(body: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    if body.parent_task_id:
        parent = db.query(Task).filter(Task.task_id == body.parent_task_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent task not found")

    if not 0 <= body.progress <= 100:
        raise HTTPException(status_code=422, detail="progress must be 0–100")

    task = Task(
        task_id=str(uuid.uuid4()),
        task_name=body.task_name,
        description=body.description,
        parent_task_id=body.parent_task_id,
        source_type=body.source_type,
        external_id=body.external_id,
        progress=body.progress,
        expected_time=body.expected_time,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
@router.get("/tasks/completion-status")
def get_batch_completion_status(
    task_ids: str = Query(..., description="Comma-separated task UUIDs"),
    date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Fetch completion status (done, completed_at) for multiple tasks at once."""
    ids = [tid.strip() for tid in task_ids.split(",") if tid.strip()]
    completions = db.query(EventCompletion).filter(EventCompletion.task_id.in_(ids)).all()
    
    # Map by task_id
    status_map = {c.task_id: {
        "event_id": c.task_id, # Keep field name same for frontend compatibility if needed, or better, return both
        "is_done": c.is_done,
        "completed_at": c.completed_at,
        "completion_description": c.completion_description
    } for c in completions}
    
    # Fill in missing ones as not done
    result = {}
    for tid in ids:
        result[tid] = status_map.get(tid, {
            "event_id": tid,
            "is_done": False,
            "completed_at": None,
            "completion_description": None
        })
    
    return {"statuses": result}

@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, body: TaskUpdate, db: Session = Depends(get_db)):
    """Partially update a task (any combination of fields)."""
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if body.parent_task_id is not None:
        if body.parent_task_id == task_id:
            raise HTTPException(status_code=422, detail="A task cannot be its own parent")
        parent = db.query(Task).filter(Task.task_id == body.parent_task_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent task not found")

    if body.progress is not None and not 0 <= body.progress <= 100:
        raise HTTPException(status_code=422, detail="progress must be 0–100")

    # XP awarding logic
    old_progress = task.progress
    new_progress = body.progress
    
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    # Award XP if progress reached 100
    if old_progress < 100 and new_progress == 100:
        now = datetime.now()
        # Find user XP
        xp = db.query(UserXP).first()
        if not xp:
            xp = UserXP(total_xp=0)
            db.add(xp)
            db.flush()
        
        # Add completion record
        completion = db.query(EventCompletion).filter(EventCompletion.task_id == task_id).first()
        if not completion:
            completion = EventCompletion(task_id=task_id, event_id=task.external_id, is_done=True, completed_at=now)
            db.add(completion)
        else:
            completion.is_done = True
            completion.completed_at = now
            completion.updated_at = now

        # Increment XP
        from backend.config import XP_PER_TASK
        xp.total_xp += XP_PER_TASK
        db.add(XPTransaction(
            points=XP_PER_TASK, 
            task_id=task_id,
            event_id=task.external_id,
            description=f"Completed Task: {task.task_name}", 
            total_xp_after=xp.total_xp, 
            created_at=now
        ))

    # Handle un-completion if progress was lowered from 100 (without XP deduction)
    elif old_progress == 100 and new_progress is not None and new_progress < 100:
        now = datetime.now()
        # Update completion record
        completion = db.query(EventCompletion).filter(EventCompletion.task_id == task_id).first()
        if completion:
            completion.is_done = False
            completion.completed_at = None
            completion.updated_at = now

    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/done")
def mark_task_done(task_id: str, db: Session = Depends(get_db)):
    """Mark a task as done (100% progress) and award XP."""
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Award XP if not already 100
    xp_awarded = 0
    now = datetime.now()
    if task.progress < 100:
        task.progress = 100
        from backend.config import XP_PER_TASK
        xp_awarded = XP_PER_TASK
        
        # User XP record
        xp = db.query(UserXP).first()
        if not xp:
            xp = UserXP(total_xp=0)
            db.add(xp)
            db.flush()
        xp.total_xp += xp_awarded
        
        # Completion record
        completion = db.query(EventCompletion).filter(EventCompletion.task_id == task_id).first()
        if not completion:
            completion = EventCompletion(task_id=task_id, event_id=task.external_id, is_done=True, completed_at=now)
            db.add(completion)
        else:
            completion.is_done = True
            completion.completed_at = now
            completion.updated_at = now
            
        # XP Transaction
        db.add(XPTransaction(
            points=xp_awarded, 
            task_id=task_id,
            event_id=task.external_id,
            description=f"Completed Task: {task.task_name}", 
            total_xp_after=xp.total_xp, 
            created_at=now
        ))

    db.commit()
    return {"success": True, "xp_awarded": xp_awarded, "completed_at": now.isoformat()}


@router.delete("/{task_id}/done")
def mark_task_undone(task_id: str, db: Session = Depends(get_db)):
    """Reset task progress to 0 and mark as not done."""
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.progress = 0
    now = datetime.now()
    completion = db.query(EventCompletion).filter(EventCompletion.task_id == task_id).first()
    if completion:
        completion.is_done = False
        completion.completed_at = None
        completion.updated_at = now
    
    db.commit()
    return {"success": True}


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    """Delete a task (and all its subtasks recursively)."""
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Recursively delete children first
    _delete_recursive(db, task_id)
    db.commit()


def _delete_recursive(db: Session, task_id: str):
    """Delete all subtasks of a task, then the task itself."""
    children = db.query(Task).filter(Task.parent_task_id == task_id).all()
    for child in children:
        _delete_recursive(db, child.task_id)
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if task:
        db.delete(task)
