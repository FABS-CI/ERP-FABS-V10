#!/bin/bash
# ERP FABS-CI - MongoDB Backup Script
# Automated daily backup with S3 upload

set -e

# Configuration
BACKUP_DIR="/var/backups/fabsci-erp"
MONGO_URI="${MONGO_URI:-mongodb://localhost:27017}"
DB_NAME="${DB_NAME:-fabsci_erp}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-fabsci-erp-backups}"
S3_ENABLED="${S3_ENABLED:-false}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${DB_NAME}_${TIMESTAMP}"
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.gz"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo "Starting MongoDB backup: ${BACKUP_NAME}"

# Create backup
mongodump --uri="${MONGO_URI}" \
          --db="${DB_NAME}" \
          --archive="${BACKUP_FILE}" \
          --gzip

echo "Backup created: ${BACKUP_FILE}"

# Upload to S3 if enabled
if [ "${S3_ENABLED}" = "true" ]; then
    echo "Uploading backup to S3..."
    aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET}/${BACKUP_NAME}.gz"
    echo "Backup uploaded to S3: s3://${S3_BUCKET}/${BACKUP_NAME}.gz"
fi

# Clean up old backups
echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "${DB_NAME}_*.gz" -mtime +${RETENTION_DAYS} -delete

# Clean up old S3 backups if enabled
if [ "${S3_ENABLED}" = "true" ]; then
    echo "Cleaning up S3 backups older than ${RETENTION_DAYS} days..."
    aws s3 ls "s3://${S3_BUCKET}/" | while read -r line; do
        createDate=$(echo $line | awk '{print $1" "$2}')
        createDate=$(date -d"$createDate" +%s)
        olderThan=$(date -d"-${RETENTION_DAYS} days" +%s)
        if [[ $createDate -lt $olderThan ]]; then
            fileName=$(echo $line | awk '{print $4}')
            if [ $fileName != "" ]; then
                aws s3 rm "s3://${S3_BUCKET}/${fileName}"
            fi
        fi
    done
fi

# Log backup completion
echo "Backup completed successfully: ${BACKUP_NAME}"
echo "Backup size: $(du -h ${BACKUP_FILE} | cut -f1)"

# Send notification (optional)
if [ -n "${SLACK_WEBHOOK_URL}" ]; then
    curl -X POST -H 'Content-type: application/json' \
         --data "{\"text\":\"MongoDB backup completed: ${BACKUP_NAME} (${BACKUP_FILE})\"}" \
         "${SLACK_WEBHOOK_URL}"
fi
