"""
Core business logic for XP management.
"""
from typing import Dict
from data.repositories.xp_repository import XPRepository


class XPCore:
    """Core business logic for XP management."""
    
    def __init__(self):
        self.xp_repo = XPRepository()
    
    def get_xp_info(self) -> Dict:
        """
        Get current XP information including level and progress.
        
        Returns:
            Dictionary with XP info
        """
        try:
            return self.xp_repo.get_xp_info()
        finally:
            self.xp_repo.close()

