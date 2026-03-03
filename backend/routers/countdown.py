from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.data.db import CountdownTimer
from backend.schemas import CountdownResponse, CreateCountdownRequest

router = APIRouter(prefix="/countdown", tags=["Countdown"])

def calculate_remaining(timer: CountdownTimer) -> int:
    remaining = timer.remaining_seconds
    if timer.is_running and timer.last_updated_at:
        elapsed = int((datetime.now() - timer.last_updated_at).total_seconds())
        remaining = max(0, timer.remaining_seconds - elapsed)
    return remaining

@router.get("", response_model=List[CountdownResponse])
def list_countdowns(db: Session = Depends(get_db)):
    timers = db.query(CountdownTimer).all()
    res = []
    for t in timers:
        res.append(CountdownResponse(
            id=t.id,
            name=t.name,
            total_seconds=t.total_seconds,
            remaining_seconds=calculate_remaining(t),
            is_running=t.is_running,
            last_updated_at=t.last_updated_at
        ))
    return res

@router.post("", response_model=CountdownResponse)
def create_countdown(req: CreateCountdownRequest, db: Session = Depends(get_db)):
    if db.query(CountdownTimer).filter(CountdownTimer.name == req.name).first():
        raise HTTPException(status_code=400, detail="Timer name already exists")
    
    t = CountdownTimer(
        name=req.name,
        total_seconds=req.total_seconds,
        remaining_seconds=req.total_seconds,
        is_running=False
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return CountdownResponse(
        id=t.id,
        name=t.name,
        total_seconds=t.total_seconds,
        remaining_seconds=t.remaining_seconds,
        is_running=t.is_running,
        last_updated_at=t.last_updated_at
    )

@router.get("/{timer_id}", response_model=CountdownResponse)
def get_countdown(timer_id: int, db: Session = Depends(get_db)):
    t = db.query(CountdownTimer).filter(CountdownTimer.id == timer_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Timer not found")
    return CountdownResponse(
        id=t.id,
        name=t.name,
        total_seconds=t.total_seconds,
        remaining_seconds=calculate_remaining(t),
        is_running=t.is_running,
        last_updated_at=t.last_updated_at
    )

@router.post("/{timer_id}/start", response_model=CountdownResponse)
def start_countdown(timer_id: int, db: Session = Depends(get_db)):
    t = db.query(CountdownTimer).filter(CountdownTimer.id == timer_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Timer not found")
    
    if not t.is_running:
        t.is_running = True
        t.last_updated_at = datetime.now()
        db.commit()
    
    return get_countdown(timer_id, db)

@router.post("/{timer_id}/pause", response_model=CountdownResponse)
def pause_countdown(timer_id: int, db: Session = Depends(get_db)):
    t = db.query(CountdownTimer).filter(CountdownTimer.id == timer_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Timer not found")
    
    if t.is_running:
        t.remaining_seconds = calculate_remaining(t)
        t.is_running = False
        t.last_updated_at = datetime.now()
        db.commit()
    
    return get_countdown(timer_id, db)

@router.delete("/{timer_id}")
def delete_countdown(timer_id: int, db: Session = Depends(get_db)):
    t = db.query(CountdownTimer).filter(CountdownTimer.id == timer_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Timer not found")
    db.delete(t)
    db.commit()
    return {"success": True}

@router.post("/{timer_id}/reset", response_model=CountdownResponse)
def reset_countdown(timer_id: int, db: Session = Depends(get_db)):
    t = db.query(CountdownTimer).filter(CountdownTimer.id == timer_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Timer not found")
    
    t.remaining_seconds = t.total_seconds
    t.is_running = False
    t.last_updated_at = None
    db.commit()
    return get_countdown(timer_id, db)
