"""
Repository for daily XP deduction tracking.
"""
from datetime import date, datetime
from typing import Optional
from data.repositories.base_repository import BaseRepository
from data.db import DailyXPDeduction


class DailyXPDeductionRepository(BaseRepository[DailyXPDeduction]):
    """Repository for daily XP deduction tracking."""
    
    def __init__(self):
        super().__init__(DailyXPDeduction)
    
    def get_last_run_date(self) -> Optional[date]:
        """Get the date when deduction last ran."""
        try:
            record = self.db.query(self.model_class).order_by(
                self.model_class.last_run_date.desc()
            ).first()
            if record:
                return record.last_run_date.date()
            return None
        except Exception as e:
            print(f"Error getting last run date: {e}")
            return None
    
    def has_run_today(self) -> bool:
        """Check if deduction has already run today."""
        try:
            today = date.today()
            record = self.db.query(self.model_class).filter(
                self.model_class.last_run_date >= datetime.combine(today, datetime.min.time())
            ).first()
            return record is not None
        except Exception as e:
            print(f"Error checking if run today: {e}")
            return False
    
    def record_deduction_run(self, pending_count: int, deducted_count: int, total_xp_deducted: int) -> bool:
        """Record that deduction has run for today."""
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            record = DailyXPDeduction(
                last_run_date=today,
                pending_count=pending_count,
                deducted_count=deducted_count,
                total_xp_deducted=total_xp_deducted
            )
            self.db.add(record)
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error recording deduction run: {e}")
            self.db.rollback()
            return False

