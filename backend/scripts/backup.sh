#!/bin/bash
# Database Backup Script for Railway PostgreSQL
# Usage: ./backup.sh

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/keyword_tracker_${DATE}.sql.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting database backup..."

# Get DATABASE_URL from environment
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set"
    exit 1
fi

# Perform backup
pg_dump "$DATABASE_URL" | gzip > "$BACKUP_FILE"

# Check if backup was successful
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "Backup successful: $BACKUP_FILE ($SIZE)"
    
    # Keep only last 7 backups
    cd "$BACKUP_DIR"
    ls -t keyword_tracker_*.sql.gz | tail -n +8 | xargs -r rm -f
    
    echo "Backup complete. Kept last 7 backups."
else
    echo "ERROR: Backup failed"
    exit 1
fi
