"""
Repository for XP operations.
"""
from datetime import datetime
from typing import Dict, Optional, List
from data.db import UserXP, XPTransaction
from data.repositories.base_repository import BaseRepository


class XPRepository(BaseRepository[UserXP]):
    """Repository for XP data access."""
    
    XP_PER_LEVEL = 100
    
    def __init__(self):
        super().__init__(UserXP)
    
    def get_or_create_xp_record(self) -> Optional[UserXP]:
        """
        Get or create the singleton XP record.
        
        Returns:
            UserXP instance or None if error
        """
        try:
            xp_record = self.db.query(UserXP).first()
            if not xp_record:
                xp_record = self.create(total_xp=0)
            return xp_record
        except Exception as e:
            print(f"Error getting/creating XP record: {e}")
            return None
    
    def add_xp(self, points: int, event_id: Optional[str] = None,
               description: Optional[str] = None,
               transaction_created_at: Optional[datetime] = None) -> bool:
        """
        Add XP points and log transaction.

        Args:
            points: Number of XP points to add
            event_id: Optional event ID
            description: Optional description
            transaction_created_at: Optional datetime for the transaction record (e.g. completion time for same-date matching)

        Returns:
            True if successful, False otherwise
        """
        try:
            xp_record = self.get_or_create_xp_record()
            if not xp_record:
                return False

            xp_record.total_xp += points
            total_after = xp_record.total_xp

            # Log transaction (use completion time when provided so completion and XP share the same date)
            transaction = XPTransaction(
                points=points,
                event_id=event_id,
                description=description or f"Task completed (+{points} XP)",
                total_xp_after=total_after,
                created_at=transaction_created_at if transaction_created_at is not None else datetime.now()
            )
            self.db.add(transaction)
            
            return self.update(xp_record) is not None
        except Exception as e:
            print(f"Error adding XP: {e}")
            self.db.rollback()
            return False
    
    def deduct_xp(self, points: int, event_id: Optional[str] = None,
                  description: Optional[str] = None) -> bool:
        """
        Deduct XP points and log transaction.
        
        Args:
            points: Number of XP points to deduct
            event_id: Optional event ID
            description: Optional description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            xp_record = self.get_or_create_xp_record()
            if not xp_record:
                return False
            
            xp_record.total_xp -= points
            total_after = xp_record.total_xp
            
            # Log transaction
            transaction = XPTransaction(
                points=-points,
                event_id=event_id,
                description=description or f"Task undone (-{points} XP)",
                total_xp_after=total_after
            )
            self.db.add(transaction)
            
            return self.update(xp_record) is not None
        except Exception as e:
            print(f"Error deducting XP: {e}")
            self.db.rollback()
            return False
    
    def get_xp_info(self) -> Dict:
        """
        Get current XP information including level and progress.
        
        Returns:
            Dictionary with XP info
        """
        try:
            xp_record = self.get_or_create_xp_record()
            if not xp_record:
                total_xp = 0
            else:
                total_xp = xp_record.total_xp
            
            # Calculate level
            if total_xp < 0:
                # Below zero: always Level 0, no 100-point levels
                level = 0
                current_level_xp = abs(total_xp)  # Full amount below zero
                xp_for_next_level = abs(total_xp)  # XP needed to reach 0
            else:
                level = (total_xp // self.XP_PER_LEVEL) + 1
                current_level_xp = total_xp % self.XP_PER_LEVEL
                xp_for_next_level = self.XP_PER_LEVEL - current_level_xp
            
            return {
                'total_xp': total_xp,
                'level': level,
                'current_level_xp': current_level_xp,
                'xp_for_next_level': xp_for_next_level
            }
        except Exception as e:
            print(f"Error getting XP info: {e}")
            return {
                'total_xp': 0,
                'level': 1,
                'current_level_xp': 0,
                'xp_for_next_level': 100
            }
    
    def get_transactions(self, limit: Optional[int] = None) -> List[XPTransaction]:
        """
        Get XP transaction history.
        
        Args:
            limit: Optional limit on number of transactions
            
        Returns:
            List of XPTransaction instances
        """
        try:
            query = self.db.query(XPTransaction).order_by(XPTransaction.created_at.desc())
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            print(f"Error getting transactions: {e}")
            return []

