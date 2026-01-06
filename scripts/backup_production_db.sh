#!/bin/bash
# Backup production database
# Usage: ./scripts/backup_production_db.sh

cd "$(dirname "$0")/.." || exit

# Set production environment
export ENVIRONMENT=production

# Load production environment variables
if [ -f .env ]; then
    # Properly load .env file handling values with special characters
    set -a
    source .env
    set +a
else
    echo "❌ Error: .env file not found!"
    exit 1
fi

# Verify it's production database
if [[ "$DATABASE_URL" == *"mindos_development"* ]]; then
    echo "❌ ERROR: DATABASE_URL points to development database!"
    echo "   This script is for backing up PRODUCTION database only."
    exit 1
fi

# Parse DATABASE_URL
# Format: postgresql+psycopg://user:pass@host:port/dbname
DB_URL=$(echo "$DATABASE_URL" | sed 's/postgresql+psycopg:\/\///')
DB_USER=$(echo "$DB_URL" | cut -d':' -f1)
DB_PASS=$(echo "$DB_URL" | cut -d':' -f2 | cut -d'@' -f1)
DB_HOST_PORT=$(echo "$DB_URL" | cut -d'@' -f2 | cut -d'/' -f1)
DB_HOST=$(echo "$DB_HOST_PORT" | cut -d':' -f1)
DB_PORT=$(echo "$DB_HOST_PORT" | cut -d':' -f2)
DB_NAME=$(echo "$DB_URL" | cut -d'/' -f2)

# Set default port if not specified
if [ -z "$DB_PORT" ]; then
    DB_PORT=5432
fi

# Create backups directory
BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/production_backup_${TIMESTAMP}.sql"

echo "📦 Backing up production database..."
echo "   Database: $DB_NAME"
echo "   Host: $DB_HOST:$DB_PORT"
echo "   Backup file: $BACKUP_FILE"

# Set PGPASSWORD for pg_dump
export PGPASSWORD="$DB_PASS"

# First, verify database connection and get table info
echo "   Verifying database connection..."
TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT COUNT(*) FROM information_schema.tables 
    WHERE table_schema = 'public';
" 2>/dev/null | tr -d ' ')

if [ -z "$TABLE_COUNT" ] || [ "$TABLE_COUNT" = "0" ]; then
    echo "⚠️  Warning: Could not verify tables or database appears empty"
else
    echo "   Found $TABLE_COUNT tables in database"
    
    # Show record counts for main tables
    echo "   Current record counts:"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT '  event_completions: ' || COUNT(*) FROM event_completions
        UNION ALL
        SELECT '  task_sessions: ' || COUNT(*) FROM task_sessions
        UNION ALL
        SELECT '  xp_transactions: ' || COUNT(*) FROM xp_transactions
        UNION ALL
        SELECT '  user_xp: ' || COUNT(*) FROM user_xp
        UNION ALL
        SELECT '  daily_xp_deduction: ' || COUNT(*) FROM daily_xp_deduction;
    " 2>/dev/null | sed 's/^/     /'
fi

echo ""
echo "   Creating backup..."

# Create backup using pg_dump with verbose output
BACKUP_ERROR=0
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --clean --if-exists --no-owner --no-acl \
    --verbose \
    -f "$BACKUP_FILE" 2>&1 | grep -E "(dumping|finished)" | head -10
BACKUP_ERROR=${PIPESTATUS[0]}

if [ $BACKUP_ERROR -eq 0 ]; then
    # Check if backup file has content
    if [ ! -s "$BACKUP_FILE" ]; then
        echo "❌ ERROR: Backup file is empty!"
        rm -f "$BACKUP_FILE"
        unset PGPASSWORD
        exit 1
    fi
    
    # Compress the backup
    echo "   Compressing backup..."
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    
    echo ""
    echo "✅ Backup created successfully!"
    echo "   File: $BACKUP_FILE"
    echo "   Size: $(du -h "$BACKUP_FILE" | cut -f1)"
    
    # Create symlink to latest backup
    ln -sf "$(basename "$BACKUP_FILE")" "$BACKUP_DIR/production_backup_latest.sql.gz"
    echo "   Latest backup: $BACKUP_DIR/production_backup_latest.sql.gz"
    
    # Verify backup contains expected content
    echo ""
    echo "   Verifying backup content..."
    BACKUP_TABLES=$(gunzip -c "$BACKUP_FILE" 2>/dev/null | grep -c "CREATE TABLE" || echo "0")
    if [ "$BACKUP_TABLES" -gt 0 ]; then
        echo "   ✅ Backup contains $BACKUP_TABLES tables"
    else
        echo "   ⚠️  Warning: Could not verify tables in backup"
    fi
else
    echo "❌ Backup failed with exit code: $BACKUP_ERROR"
    rm -f "$BACKUP_FILE"
    unset PGPASSWORD
    exit 1
fi

# Unset password
unset PGPASSWORD

