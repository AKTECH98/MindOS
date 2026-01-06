"""
Script to drop unused tables from the database.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, inspect
from config import DATABASE_URL


def drop_unused_tables():
    """Drop unused tables from the database."""
    # Unused tables to drop
    unused_tables = ['reminder_preferences', 'reminder_logs']
    
    # Create engine
    engine = create_engine(DATABASE_URL, echo=False)
    
    try:
        # Get list of existing tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print("Existing tables in database:")
        for table in existing_tables:
            print(f"  - {table}")
        
        print(f"\nDropping unused tables...")
        
        with engine.connect() as conn:
            for table_name in unused_tables:
                if table_name in existing_tables:
                    try:
                        print(f"  Dropping table '{table_name}'...")
                        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                        conn.commit()
                        print(f"  ✅ Successfully dropped table '{table_name}'")
                    except Exception as e:
                        print(f"  ❌ Error dropping table '{table_name}': {e}")
                        conn.rollback()
                else:
                    print(f"  ⚠️  Table '{table_name}' does not exist, skipping")
        
        # Show remaining tables
        inspector = inspect(engine)
        remaining_tables = inspector.get_table_names()
        
        print(f"\nRemaining tables in database:")
        for table in remaining_tables:
            print(f"  - {table}")
        
        print("\n✅ Done!")
        
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    drop_unused_tables()

