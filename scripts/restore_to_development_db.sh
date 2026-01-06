#!/bin/bash
# Restore production backup to development database
# Usage: ./scripts/restore_to_development_db.sh [backup_file]

cd "$(dirname "$0")/.." || exit

# Set development environment
export ENVIRONMENT=development

# Load development environment variables
if [ -f .env.development ]; then
    # Properly load .env file handling values with special characters
    set -a
    source .env.development
    set +a
    echo "📝 Loaded .env.development"
elif [ -f .env ]; then
    set -a
    source .env
    set +a
    echo "⚠️  Loaded .env (create .env.development for dev-specific settings)"
else
    echo "❌ Error: No .env or .env.development file found!"
    exit 1
fi

# Verify it's development database
if [[ "$DATABASE_URL" != *"mindos_development"* ]]; then
    echo "❌ ERROR: DATABASE_URL doesn't point to development database!"
    echo "   This script restores to DEVELOPMENT database only."
    exit 1
fi

# Parse DATABASE_URL
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

# Determine backup file
BACKUP_DIR="backups"
if [ -n "$1" ]; then
    BACKUP_FILE="$1"
    # If relative path, assume it's in backups directory
    if [[ "$BACKUP_FILE" != /* ]]; then
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
    fi
else
    # Use latest backup
    BACKUP_FILE="$BACKUP_DIR/production_backup_latest.sql.gz"
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    echo ""
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/production_backup_*.sql.gz 2>/dev/null || echo "   (none)"
    exit 1
fi

# Confirm restoration
echo "⚠️  WARNING: This will REPLACE all data in the development database!"
echo "   Development database: $DB_NAME"
echo "   Backup file: $BACKUP_FILE"
read -p "Are you sure? Type 'y' to confirm: " -r
echo
if [ "$REPLY" != "y" ]; then
    echo "❌ Aborted."
    exit 1
fi

echo "🔄 Restoring backup to development database..."

# Set PGPASSWORD
export PGPASSWORD="$DB_PASS"

# Check if database exists, create if not
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || true

# Drop existing connections (needed for clean restore)
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();
" 2>/dev/null || true

# Restore backup
if [[ "$BACKUP_FILE" == *.gz ]]; then
    # Decompress and restore
    gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" 2>&1
else
    # Restore directly
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE" 2>&1
fi

if [ $? -eq 0 ]; then
    echo "✅ Database restored successfully!"
    echo "   Development database now contains production backup data"
else
    echo "❌ Restore failed!"
    unset PGPASSWORD
    exit 1
fi

# Unset password
unset PGPASSWORD

echo ""
echo "✅ Done! Your development database has been restored from production backup."
echo "   You may need to restart your development app."

