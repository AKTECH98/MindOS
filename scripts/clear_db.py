"""
Script to clear all data from the database.
"""
from data.db import init_db, get_db, EventCompletion, TaskSession


def clear_database():
    """Clear all records from all tables."""
    # Initialize database
    init_db()
    
    # Get database session
    db = get_db()
    
    try:
        # Delete all records from both tables
        deleted_completions = db.query(EventCompletion).delete()
        deleted_sessions = db.query(TaskSession).delete()
        
        # Commit the changes
        db.commit()
        
        print(f"Database cleared successfully!")
        print(f"  - Deleted {deleted_completions} event completion records")
        print(f"  - Deleted {deleted_sessions} task session records")
        
    except Exception as e:
        db.rollback()
        print(f"Error clearing database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clear_database()

