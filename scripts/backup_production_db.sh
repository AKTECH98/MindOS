#!/bin/bash
# Backup production database
# Usage: ./scripts/backup_production_db.sh

cd "$(dirname "$0")/.." || exit

# Set production environment
export ENVIRONMENT=production

# Load production environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
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

# Create backup using pg_dump
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --clean --if-exists --no-owner --no-acl \
    -f "$BACKUP_FILE" 2>&1

if [ $? -eq 0 ]; then
    # Compress the backup
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    
    echo "✅ Backup created successfully!"
    echo "   File: $BACKUP_FILE"
    echo "   Size: $(du -h "$BACKUP_FILE" | cut -f1)"
    
    # Create symlink to latest backup
    ln -sf "$(basename "$BACKUP_FILE")" "$BACKUP_DIR/production_backup_latest.sql.gz"
    echo "   Latest backup: $BACKUP_DIR/production_backup_latest.sql.gz"
else
    echo "❌ Backup failed!"
    unset PGPASSWORD
    exit 1
fi

# Unset password
unset PGPASSWORD

