
#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/var/backups/stoic-citadel"
PG_HOST="localhost"
PG_PORT="5432"
PG_USER="user"
PG_DB="stoic_citadel"
REDIS_HOST="localhost"
REDIS_PORT="6379"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
MAX_BACKUPS=7

# Cloud storage configuration (replace with your actual configuration)
S3_BUCKET="s3://stoic-citadel-backups"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# 1. PostgreSQL Backup
echo "Backing up PostgreSQL database..."
PG_BACKUP_FILE="$BACKUP_DIR/pg_backup_$TIMESTAMP.sql"
pg_dump "postgresql://$PG_USER@$PG_HOST:$PG_PORT/$PG_DB" > "$PG_BACKUP_FILE"

# 2. Redis Backup
echo "Backing up Redis database..."
REDIS_BACKUP_FILE="$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb"
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --rdb "$REDIS_BACKUP_FILE"

# 3. Compress Backups
echo "Compressing backups..."
gzip "$PG_BACKUP_FILE"
gzip "$REDIS_BACKUP_FILE"

# 4. Upload to Cloud Storage (e.g., AWS S3)
echo "Uploading backups to cloud storage..."
# aws s3 cp "$PG_BACKUP_FILE.gz" "$S3_BUCKET/"
# aws s3 cp "$REDIS_BACKUP_FILE.gz" "$S3_BUCKET/"
echo "Cloud upload placeholder. Implement your cloud provider's CLI commands."

# 5. Rotate Backups
echo "Rotating backups..."
find "$BACKUP_DIR" -name "pg_backup_*.sql.gz" -mtime +$MAX_BACKUPS -delete
find "$BACKUP_DIR" -name "redis_backup_*.rdb.gz" -mtime +$MAX_BACKUPS -delete

echo "Backup process completed successfully."
