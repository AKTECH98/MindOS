from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import XPInfoResponse, XPTransactionResponse
from backend.data.db import UserXP, XPTransaction

router = APIRouter(prefix="/xp", tags=["XP"])

XP_PER_LEVEL = 100


def compute_xp_info(total_xp: int) -> dict:
    if total_xp < 0:
        return {"total_xp": total_xp, "level": 0,
                "current_level_xp": abs(total_xp), "xp_for_next_level": abs(total_xp)}
    level = (total_xp // XP_PER_LEVEL) + 1
    current = total_xp % XP_PER_LEVEL
    return {"total_xp": total_xp, "level": level,
            "current_level_xp": current, "xp_for_next_level": XP_PER_LEVEL - current}


@router.get("", response_model=XPInfoResponse)
def get_xp_info(db: Session = Depends(get_db)):
    """Get current XP: total, level, and progress to next level."""
    record = db.query(UserXP).first()
    return compute_xp_info(record.total_xp if record else 0)


@router.get("/transactions", response_model=List[XPTransactionResponse])
def get_xp_transactions(limit: int = 50, db: Session = Depends(get_db)):
    """Recent XP transaction log."""
    return (
        db.query(XPTransaction)
        .order_by(XPTransaction.created_at.desc())
        .limit(limit)
        .all()
    )
