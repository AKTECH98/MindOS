"""
XP Service
Manages user XP points and level calculations.
"""
from typing import Dict, Optional
from sqlalchemy.exc import SQLAlchemyError

from data.db import get_db, UserXP, XPTransaction


class XPService:
    """Service for managing user XP points and levels."""
    
    XP_PER_TASK = 5
    XP_PER_LEVEL = 100
    
    @staticmethod
    def _get_or_create_xp_record():
        """
        Get or create the singleton UserXP record.
        
        Returns:
            UserXP record or None if error
        """
        db = None
        try:
            db = get_db()
            xp_record = db.query(UserXP).first()
            if not xp_record:
                xp_record = UserXP(total_xp=0)
                db.add(xp_record)
                db.commit()
            return xp_record
        except SQLAlchemyError as e:
            print(f"Error getting/creating XP record: {e}")
            if db:
                db.rollback()
            return None
        except Exception as e:
            print(f"Unexpected error getting/creating XP record: {e}")
            if db:
                db.rollback()
            return None
        finally:
            if db:
                db.close()
    
    @staticmethod
    def add_xp(points: int, event_id: Optional[str] = None, description: Optional[str] = None) -> bool:
        """
        Add XP points to the user's total and log transaction.
        
        Args:
            points: Number of XP points to add
            event_id: Optional event ID that triggered this XP
            description: Optional description of the transaction
            
        Returns:
            True if successful, False otherwise
        """
        db = None
        try:
            db = get_db()
            xp_record = db.query(UserXP).first()
            
            if not xp_record:
                # Create if doesn't exist
                xp_record = UserXP(total_xp=points)
                db.add(xp_record)
                total_after = points
            else:
                xp_record.total_xp += points
                total_after = xp_record.total_xp
            
            # Log transaction in ledger
            transaction = XPTransaction(
                points=points,
                event_id=event_id,
                description=description or f"Task completed (+{points} XP)",
                total_xp_after=total_after
            )
            db.add(transaction)
            
            db.commit()
            return True
        except SQLAlchemyError as e:
            print(f"Error adding XP: {e}")
            if db:
                db.rollback()
            return False
        except Exception as e:
            print(f"Unexpected error adding XP: {e}")
            if db:
                db.rollback()
            return False
        finally:
            if db:
                db.close()
    
    @staticmethod
    def deduct_xp(points: int, event_id: Optional[str] = None, description: Optional[str] = None) -> bool:
        """
        Deduct XP points from the user's total and log transaction.
        Can result in negative XP.
        
        Args:
            points: Number of XP points to deduct
            event_id: Optional event ID that triggered this XP deduction
            description: Optional description of the transaction
            
        Returns:
            True if successful, False otherwise
        """
        db = None
        try:
            db = get_db()
            xp_record = db.query(UserXP).first()
            
            if not xp_record:
                # Create if doesn't exist (with negative XP)
                xp_record = UserXP(total_xp=-points)
                db.add(xp_record)
                total_after = -points
            else:
                xp_record.total_xp -= points
                total_after = xp_record.total_xp
            
            # Log transaction in ledger (points will be negative)
            transaction = XPTransaction(
                points=-points,
                event_id=event_id,
                description=description or f"Task undone (-{points} XP)",
                total_xp_after=total_after
            )
            db.add(transaction)
            
            db.commit()
            return True
        except SQLAlchemyError as e:
            print(f"Error deducting XP: {e}")
            if db:
                db.rollback()
            return False
        except Exception as e:
            print(f"Unexpected error deducting XP: {e}")
            if db:
                db.rollback()
            return False
        finally:
            if db:
                db.close()
    
    @staticmethod
    def get_xp_info() -> Dict:
        """
        Get current XP information including level and progress.
        
        Returns:
            Dictionary with:
            - total_xp: Total cumulative XP points
            - level: Current level (1-based)
            - current_level_xp: XP within current level (0-99)
            - xp_for_next_level: XP needed to reach next level
        """
        db = None
        try:
            db = get_db()
            xp_record = db.query(UserXP).first()
            
            if not xp_record:
                # Initialize if doesn't exist
                xp_record = UserXP(total_xp=0)
                db.add(xp_record)
                db.commit()
                total_xp = 0
            else:
                total_xp = xp_record.total_xp
            
            # Calculate level (Level 1 = 0-99 XP, Level 2 = 100-199 XP, etc.)
            # For negative XP, show how negative we are
            if total_xp < 0:
                level = 1
                # For negative XP, show absolute value as current_level_xp (how far below 0)
                current_level_xp = abs(total_xp) % XPService.XP_PER_LEVEL
                xp_for_next_level = XPService.XP_PER_LEVEL - current_level_xp
            else:
                level = (total_xp // XPService.XP_PER_LEVEL) + 1
                current_level_xp = total_xp % XPService.XP_PER_LEVEL
                xp_for_next_level = XPService.XP_PER_LEVEL - current_level_xp
            
            return {
                'total_xp': total_xp,
                'level': level,
                'current_level_xp': current_level_xp,
                'xp_for_next_level': xp_for_next_level
            }
        except SQLAlchemyError as e:
            print(f"Error getting XP info: {e}")
            return {
                'total_xp': 0,
                'level': 1,
                'current_level_xp': 0,
                'xp_for_next_level': 100
            }
        except Exception as e:
            print(f"Unexpected error getting XP info: {e}")
            return {
                'total_xp': 0,
                'level': 1,
                'current_level_xp': 0,
                'xp_for_next_level': 100
            }
        finally:
            if db:
                db.close()

