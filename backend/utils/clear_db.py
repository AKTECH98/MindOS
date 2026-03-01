"""
Script to clear all data from the database.
"""
from data.db import (
    init_db, get_db, 
    EventCompletion, TaskSession, UserXP, XPTransaction
)


def clear_database():
    """Clear all records from all tables."""
    # Initialize database
    init_db()
    
    # Get database session
    db = get_db()
    
    try:
        # Delete all records from all tables
        deleted_completions = db.query(EventCompletion).delete()
        deleted_sessions = db.query(TaskSession).delete()
        deleted_xp_transactions = db.query(XPTransaction).delete()
        deleted_user_xp = db.query(UserXP).delete()
        
        # Commit the changes
        db.commit()
        
        print(f"Database cleared successfully!")
        print(f"  - Deleted {deleted_completions} event completion records")
        print(f"  - Deleted {deleted_sessions} task session records")
        print(f"  - Deleted {deleted_xp_transactions} XP transaction records")
        print(f"  - Deleted {deleted_user_xp} user XP records")
        
        # Re-initialize UserXP record (singleton pattern)
        xp_record = UserXP(total_xp=0)
        db.add(xp_record)
        db.commit()
        print(f"  - Re-initialized UserXP record")
        
    except Exception as e:
        db.rollback()
        print(f"Error clearing database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clear_database()

