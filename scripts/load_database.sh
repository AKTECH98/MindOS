#!/bin/bash
# Database loading script for MindOS
# Usage: ./scripts/load_database.sh <backup_path> [database_user]
#
# This script:
# 1. Drops the mindos_development database
# 2. Creates a new mindos_development database
# 3. Loads the backup from the specified backup_path
#
# Arguments:
#   backup_path: Path to the backup file or directory (required)
#   database_user: PostgreSQL user (optional, defaults to current user or DB_USER env var)

set -e  # Exit on error

# Check if backup_path is provided
if [ -z "$1" ]; then
    echo "❌ Error: backup_path is required"
    echo "Usage: ./scripts/load_database.sh <backup_path> [database_user]"
    echo "Example: ./scripts/load_database.sh backups/update_production.sql"
    exit 1
fi

BACKUP_PATH="$1"
DB_USER="${2:-${DB_USER:-$(whoami)}}"
DB_NAME="mindos_development"

# Change to project root directory
cd "$(dirname "$0")/.." || exit

echo "🗑️  Dropping database: $DB_NAME"
dropdb -U "$DB_USER" "$DB_NAME" || echo "⚠️  Database $DB_NAME does not exist (this is okay)"

echo "📦 Creating database: $DB_NAME"
createdb -U "$DB_USER" "$DB_NAME"

echo "📥 Loading backup from: $BACKUP_PATH"

# Check if backup is a directory (directory format) or file
if [ -d "$BACKUP_PATH" ]; then
    echo "📋 Detected directory format backup, using pg_restore..."
    pg_restore -U "$DB_USER" -d "$DB_NAME" "$BACKUP_PATH"
elif [ -f "$BACKUP_PATH" ]; then
    # Check if it's a custom format file (pg_dump -Fc) or SQL file
    # Try pg_restore first (works for custom format files)
    if pg_restore -l "$BACKUP_PATH" > /dev/null 2>&1; then
        echo "📋 Detected custom format backup file, using pg_restore..."
        pg_restore -U "$DB_USER" -d "$DB_NAME" "$BACKUP_PATH"
    else
        echo "📋 Detected SQL format backup, using psql..."
        psql -U "$DB_USER" -d "$DB_NAME" -f "$BACKUP_PATH"
    fi
else
    echo "❌ Error: Backup file/directory not found at $BACKUP_PATH"
    exit 1
fi

echo "✅ Database loaded successfully!"
