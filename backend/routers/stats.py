from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.schemas import ContributionDataResponse, StatsOverviewResponse
from backend.data.db import EventCompletion

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/contributions", response_model=ContributionDataResponse)
def get_contributions(
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """Daily completion counts for the heatmap (defaults to past ~1 year)."""
    end = end or date.today()
    start = start or end - timedelta(days=370)

    rows = (
        db.query(
            func.date(EventCompletion.completed_at).label("cdate"),
            func.count(EventCompletion.id).label("cnt"),
        )
        .filter(
            EventCompletion.is_done == True,
            EventCompletion.completed_at.isnot(None),
            func.date(EventCompletion.completed_at).between(start, end),
        )
        .group_by(func.date(EventCompletion.completed_at))
        .all()
    )

    contributions = {
        (r.cdate.isoformat() if hasattr(r.cdate, "isoformat") else str(r.cdate)): r.cnt
        for r in rows
        if r.cdate
    }
    return ContributionDataResponse(
        contributions=contributions,
        max_count=max(contributions.values(), default=0),
    )


@router.get("/overview", response_model=StatsOverviewResponse)
def get_stats_overview(db: Session = Depends(get_db)):
    """High-level stats: total, today, this week, streak."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    def count(extra_filter):
        return (
            db.query(func.count(EventCompletion.id))
            .filter(EventCompletion.is_done == True, *extra_filter)
            .scalar() or 0
        )

    total  = count([])
    today_ = count([func.date(EventCompletion.completed_at) == today])
    week   = count([func.date(EventCompletion.completed_at) >= week_start])

    # Streak: consecutive days going back from today
    streak, check = 0, today
    while streak < 366:
        if count([func.date(EventCompletion.completed_at) == check]) == 0:
            break
        streak += 1
        check -= timedelta(days=1)

    return StatsOverviewResponse(
        total_completed=total, completed_today=today_,
        completed_this_week=week, current_streak_days=streak,
    )
