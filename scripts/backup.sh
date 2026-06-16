#!/bin/bash
# ============================================================
# ERP FABS-CI V10 — Script de sauvegarde automatique
# Backup: MongoDB (avec auth) + fichiers de config
# Rétention: 30 jours
# Logging: /var/log/fabsci-backup.log
# ============================================================

BACKUP_BASE="/home/user/backups/fabsci_erp"
LOG_FILE="/var/log/fabsci-backup.log"
RETENTION_DAYS=30
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$BACKUP_BASE/$TIMESTAMP"
MONGO_USER="mongoAdmin"
MONGO_PASS="MongoAdmin_FABS2026!"
DB_NAME="fabsci_erp"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "DÉBUT BACKUP FABS-CI ERP — $TIMESTAMP"
log "=========================================="

# Créer le répertoire de backup
mkdir -p "$BACKUP_DIR"

# 1. Backup MongoDB avec auth
log "Sauvegarde MongoDB (DB: $DB_NAME)..."
if mongodump \
    --uri="mongodb://$MONGO_USER:$MONGO_PASS@localhost:27017/$DB_NAME?authSource=admin" \
    --out="$BACKUP_DIR/mongodb" \
    --quiet 2>> "$LOG_FILE"; then
    log "✅ MongoDB backup OK"
else
    log "❌ ERREUR: MongoDB backup échoué"
    exit 1
fi

# 2. Backup fichiers de configuration
log "Sauvegarde configurations..."
cp /etc/mongod.conf "$BACKUP_DIR/mongod.conf" 2>/dev/null
cp /home/user/ERP-FABS-V10/.env.production "$BACKUP_DIR/.env.production" 2>/dev/null
log "✅ Configurations sauvegardées"

# 3. Compression
log "Compression de l'archive..."
tar -czf "$BACKUP_BASE/backup_$TIMESTAMP.tar.gz" -C "$BACKUP_BASE" "$TIMESTAMP" 2>> "$LOG_FILE"
rm -rf "$BACKUP_DIR"
BACKUP_SIZE=$(du -sh "$BACKUP_BASE/backup_$TIMESTAMP.tar.gz" | cut -f1)
log "✅ Archive créée: backup_$TIMESTAMP.tar.gz ($BACKUP_SIZE)"

# 4. Vérification d'intégrité
log "Vérification intégrité..."
if tar -tzf "$BACKUP_BASE/backup_$TIMESTAMP.tar.gz" > /dev/null 2>&1; then
    log "✅ Intégrité vérifiée"
    INTEGRITY="OK"
else
    log "❌ ERREUR: Archive corrompue!"
    INTEGRITY="FAIL"
    exit 1
fi

# 5. Nettoyage des backups anciens (> 30 jours)
log "Nettoyage backups > $RETENTION_DAYS jours..."
DELETED=$(find "$BACKUP_BASE" -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
log "✅ $DELETED ancien(s) backup(s) supprimé(s)"

# 6. Rapport final
BACKUP_COUNT=$(ls "$BACKUP_BASE"/backup_*.tar.gz 2>/dev/null | wc -l)
log "BACKUP TERMINÉ — Archives: $BACKUP_COUNT | Intégrité: $INTEGRITY"
log "=========================================="
exit 0
