#!/bin/bash
# ERP FABS-CI - MongoDB Restore Script
# Restore from local backup or S3

set -e

# Configuration
BACKUP_DIR="/var/backups/fabsci-erp"
MONGO_URI="${MONGO_URI:-mongodb://localhost:27017}"
DB_NAME="${DB_NAME:-fabsci_erp}"
S3_BUCKET="${S3_BUCKET:-fabsci-erp-backups}"
S3_ENABLED="${S3_ENABLED:-false}"

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file.gz> [--from-s3]"
    echo "Example: $0 fabsci_erp_20240601_120000.gz"
    echo "Example: $0 fabsci_erp_20240601_120000.gz --from-s3"
    exit 1
fi

BACKUP_FILE=$1
FROM_S3=${2:-false}

# Download from S3 if requested
if [ "${FROM_S3}" = "--from-s3" ]; then
    if [ "${S3_ENABLED}" != "true" ]; then
        echo "Error: S3 is not enabled. Set S3_ENABLED=true."
        exit 1
    fi
    
    echo "Downloading backup from S3..."
    aws s3 cp "s3://${S3_BUCKET}/${BACKUP_FILE}" "${BACKUP_DIR}/${BACKUP_FILE}"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"
else
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"
fi

# Check if backup file exists
if [ ! -f "${BACKUP_PATH}" ]; then
    echo "Error: Backup file not found: ${BACKUP_PATH}"
    exit 1
fi

# Confirm restore
echo "WARNING: This will restore the database from backup."
echo "Backup file: ${BACKUP_PATH}"
echo "Target database: ${DB_NAME}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm
if [ "${confirm}" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Create a backup of current database before restore
echo "Creating backup of current database..."
CURRENT_BACKUP="${BACKUP_DIR}/${DB_NAME}_before_restore_$(date +%Y%m%d_%H%M%S).gz"
mongodump --uri="${MONGO_URI}" \
          --db="${DB_NAME}" \
          --archive="${CURRENT_BACKUP}" \
          --gzip
echo "Current database backed up to: ${CURRENT_BACKUP}"

# Restore from backup
echo "Restoring database from backup..."
mongorestore --uri="${MONGO_URI}" \
             --db="${DB_NAME}" \
             --archive="${BACKUP_PATH}" \
             --gzip

echo "Restore completed successfully."
echo "Previous database backed up to: ${CURRENT_BACKUP}"

# Send notification (optional)
if [ -n "${SLACK_WEBHOOK_URL}" ]; then
    curl -X POST -H 'Content-type: application/json' \
         --data "{\"text\":\"MongoDB restore completed: ${BACKUP_FILE} to ${DB_NAME}\"}" \
         "${SLACK_WEBHOOK_URL}"
fi
