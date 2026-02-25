#!/bin/bash
# ==============================================
# PostgreSQL Backup Script for BurgerPOS
# ==============================================
# Usage: ./backup.sh
# Cron: 0 2 * * * /path/to/backup.sh >> /var/log/burger-backup.log 2>&1
#
# Keeps last 7 daily backups. Older backups are automatically deleted.
# ==============================================

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-burger_pos}"
DB_USER="${POSTGRES_USER:-postgres}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/burger_pos_${TIMESTAMP}.sql.gz"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting backup of ${DB_NAME}..."

# Run pg_dump and compress
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
  -h "${DB_HOST}" \
  -p "${DB_PORT}" \
  -U "${DB_USER}" \
  -d "${DB_NAME}" \
  --no-owner \
  --no-acl \
  --clean \
  --if-exists \
  | gzip > "${BACKUP_FILE}"

# Check backup was created successfully
if [ -s "${BACKUP_FILE}" ]; then
  SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
  echo "[$(date)] ✅ Backup successful: ${BACKUP_FILE} (${SIZE})"
else
  echo "[$(date)] ❌ Backup FAILED: file is empty"
  rm -f "${BACKUP_FILE}"
  exit 1
fi

# Delete old backups
echo "[$(date)] 🧹 Cleaning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "burger_pos_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

# List remaining backups
echo "[$(date)] 📂 Current backups:"
ls -lh "${BACKUP_DIR}"/burger_pos_*.sql.gz 2>/dev/null || echo "  (none)"

echo "[$(date)] Done."
