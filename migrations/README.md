# Database Migrations

This directory contains database migration scripts for MindOS.

## Migration Structure

Each migration file should follow this pattern:

```python
"""
Migration: Description of what this migration does
Date: YYYY-MM-DD
"""
from sqlalchemy import text
from data.db import get_db

def up():
    """Apply migration."""
    db = get_db()
    try:
        # Your migration SQL here
        db.execute(text("ALTER TABLE ..."))
        db.commit()
        print("✅ Migration applied: ...")
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

def down():
    """Rollback migration."""
    db = get_db()
    try:
        # Your rollback SQL here
        db.execute(text("ALTER TABLE ..."))
        db.commit()
        print("✅ Migration rolled back: ...")
    except Exception as e:
        db.rollback()
        print(f"❌ Rollback failed: {e}")
        raise
    finally:
        db.close()
```

## Running Migrations

### Manual execution:
```python
from migrations.migration_XXX import up, down

# Apply migration
up()

# Rollback migration
down()
```

## Best Practices

1. **Always test migrations in development first**
2. **Make migrations reversible** (include `down()` function)
3. **Use `IF NOT EXISTS` / `IF EXISTS`** for safety
4. **Document breaking changes** in migration comments
5. **Never run development migrations on production database**

## Migration Naming

Use descriptive names with version numbers:
- `migration_001_add_completion_description.py`
- `migration_002_add_new_table.py`
- etc.

