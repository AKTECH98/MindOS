#!/bin/bash
# Database backup script for MindOS
# Usage: ./scripts/backup_database.sh [backup_path] [database_user]
#
# This script creates a backup of the mindos_development database in directory format.
#
# Arguments:
#   backup_path: Path where to save the backup (optional, defaults to backups/mindos_backup_YYYYMMDD_HHMMSS)
#   database_user: PostgreSQL user (optional, defaults to current user or DB_USER env var)

set -e  # Exit on error

# Get database user from argument or environment variable, default to current user
DB_USER="${2:-${DB_USER:-$(whoami)}}"
DB_NAME="mindos_development"

# Change to project root directory
cd "$(dirname "$0")/.." || exit

# Generate default backup path if not provided
if [ -z "$1" ]; then
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_PATH="backups/mindos_backup_${TIMESTAMP}"
else
    BACKUP_PATH="$1"
fi

# Ensure backups directory exists
mkdir -p backups

# If backup path is a directory or doesn't exist, ensure it's created as a directory
if [ ! -f "$BACKUP_PATH" ]; then
    mkdir -p "$BACKUP_PATH"
fi

echo "💾 Creating backup of database: $DB_NAME"
echo "📁 Backup location: $BACKUP_PATH"

# Create backup in directory format (matches existing backup structure)
pg_dump -U "$DB_USER" -d "$DB_NAME" -Fd -f "$BACKUP_PATH"

echo "✅ Database backup created successfully at: $BACKUP_PATH"
echo "📋 To restore this backup, run:"
echo "   ./scripts/load_database.sh $BACKUP_PATH"
