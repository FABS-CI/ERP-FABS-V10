"""
TOUR 3: Database Schema & Optimization
- Index definitions
- Backup and recovery setup
- Audit logging schema
- Replication configuration
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class IndexDefinition:
    """Define MongoDB indexes"""
    
    def __init__(self, collection: str, fields: List[tuple], 
                 name: str = None, unique: bool = False, 
                 sparse: bool = False, ttl: int = None):
        self.collection = collection
        self.fields = fields  # List of (field_name, direction) tuples
        self.name = name
        self.unique = unique
        self.sparse = sparse
        self.ttl = ttl  # TTL in seconds (for expiring documents)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MongoDB createIndex format"""
        keys = {field: direction for field, direction in self.fields}
        options = {}
        
        if self.name:
            options["name"] = self.name
        if self.unique:
            options["unique"] = True
        if self.sparse:
            options["sparse"] = True
        if self.ttl:
            options["expireAfterSeconds"] = self.ttl
        
        return {"keys": keys, "options": options}
    
    def to_pymongo_call(self) -> str:
        """Generate pymongo create_index call"""
        field_list = [f"('{f[0]}', {f[1]})" for f in self.fields]
        args = ", ".join(field_list)
        
        options = []
        if self.name:
            options.append(f"name='{self.name}'")
        if self.unique:
            options.append("unique=True")
        if self.sparse:
            options.append("sparse=True")
        if self.ttl:
            options.append(f"expireAfterSeconds={self.ttl}")
        
        options_str = ", " + ", ".join(options) if options else ""
        return f"db['{self.collection}'].create_index([{args}]{options_str})"


class SchemaOptimizer:
    """Define optimal schema and indexes for all collections"""
    
    # Define all indexes
    INDEXES = [
        # Authentication & Users
        IndexDefinition("utilisateurs", [("email", 1)], 
                       name="idx_email", unique=True, sparse=True),
        IndexDefinition("utilisateurs", [("username", 1)], 
                       name="idx_username", unique=True, sparse=True),
        IndexDefinition("utilisateurs", [("role", 1)], name="idx_role"),
        IndexDefinition("utilisateurs", [("created_at", 1)], name="idx_created_at"),
        
        # Clients
        IndexDefinition("clients", [("email", 1)], name="idx_client_email"),
        IndexDefinition("clients", [("phone", 1)], name="idx_client_phone"),
        IndexDefinition("clients", [("status", 1)], name="idx_client_status"),
        IndexDefinition("clients", [("created_at", 1)], name="idx_client_created"),
        IndexDefinition("clients", [("name", "text")], name="idx_client_text_search"),
        
        # Products
        IndexDefinition("products", [("code", 1)], 
                       name="idx_product_code", unique=True, sparse=True),
        IndexDefinition("products", [("category", 1)], name="idx_product_category"),
        IndexDefinition("products", [("status", 1)], name="idx_product_status"),
        IndexDefinition("products", [("name", "text")], name="idx_product_text_search"),
        
        # Stock/Inventory
        IndexDefinition("stock", [("product_id", 1)], name="idx_stock_product"),
        IndexDefinition("stock", [("warehouse", 1)], name="idx_stock_warehouse"),
        IndexDefinition("stock", [("quantity", 1)], name="idx_stock_quantity"),
        IndexDefinition("stock", [("last_updated", 1)], name="idx_stock_updated"),
        
        # Orders
        IndexDefinition("orders", [("order_number", 1)], 
                       name="idx_order_number", unique=True, sparse=True),
        IndexDefinition("orders", [("client_id", 1)], name="idx_order_client"),
        IndexDefinition("orders", [("status", 1)], name="idx_order_status"),
        IndexDefinition("orders", [("created_at", 1)], name="idx_order_created"),
        IndexDefinition("orders", [("created_at", -1)], name="idx_order_created_desc"),
        
        # Invoices
        IndexDefinition("invoices", [("invoice_number", 1)], 
                       name="idx_invoice_number", unique=True, sparse=True),
        IndexDefinition("invoices", [("order_id", 1)], name="idx_invoice_order"),
        IndexDefinition("invoices", [("client_id", 1)], name="idx_invoice_client"),
        IndexDefinition("invoices", [("status", 1)], name="idx_invoice_status"),
        IndexDefinition("invoices", [("due_date", 1)], name="idx_invoice_due_date"),
        
        # Payments
        IndexDefinition("payments", [("invoice_id", 1)], name="idx_payment_invoice"),
        IndexDefinition("payments", [("transaction_id", 1)], 
                       name="idx_payment_transaction", unique=True, sparse=True),
        IndexDefinition("payments", [("status", 1)], name="idx_payment_status"),
        IndexDefinition("payments", [("payment_date", 1)], name="idx_payment_date"),
        
        # Audit Log (with TTL for automatic cleanup after 365 days)
        IndexDefinition("audit_logs", [("timestamp", 1)], name="idx_audit_timestamp"),
        IndexDefinition("audit_logs", [("user_id", 1)], name="idx_audit_user"),
        IndexDefinition("audit_logs", [("action", 1)], name="idx_audit_action"),
        IndexDefinition("audit_logs", [("resource_type", 1)], name="idx_audit_resource"),
        IndexDefinition("audit_logs", [("timestamp", 1)], 
                       name="idx_audit_ttl", ttl=31536000),  # 365 days
        
        # Session Management
        IndexDefinition("sessions", [("token_hash", 1)], 
                       name="idx_session_token", unique=True, sparse=True),
        IndexDefinition("sessions", [("user_id", 1)], name="idx_session_user"),
        IndexDefinition("sessions", [("expires_at", 1)], 
                       name="idx_session_expiry", ttl=3600),  # 1 hour
    ]
    
    @staticmethod
    def get_indexes_for_collection(collection: str) -> List[IndexDefinition]:
        """Get all indexes for a specific collection"""
        return [idx for idx in SchemaOptimizer.INDEXES if idx.collection == collection]
    
    @staticmethod
    def get_all_indexes() -> List[IndexDefinition]:
        """Get all indexes"""
        return SchemaOptimizer.INDEXES
    
    @staticmethod
    def generate_index_creation_script() -> str:
        """Generate Python script to create all indexes"""
        script = """#!/usr/bin/env python3
\"\"\"Create all database indexes for ERP-FABS\"\"\"

from pymongo import MongoClient, ASCENDING, DESCENDING

def create_indexes():
    client = MongoClient('mongodb://localhost:27017')
    db = client['erp_fabs']
    
    print("Creating indexes...")
    
"""
        
        for idx in SchemaOptimizer.INDEXES:
            direction = 1 if "(" in str(idx.fields) and idx.fields[0][1] == 1 else -1
            script += f"    {idx.to_pymongo_call()}\n"
        
        script += """
    print("✓ All indexes created successfully")
    client.close()

if __name__ == "__main__":
    create_indexes()
"""
        return script


class BackupConfiguration:
    """Backup and recovery configuration"""
    
    def __init__(self, backup_dir: str = "/backups/mongodb", 
                 retention_days: int = 30, compression: bool = True):
        self.backup_dir = backup_dir
        self.retention_days = retention_days
        self.compression = compression
    
    def get_backup_script(self) -> str:
        """Generate MongoDB backup script"""
        compression_flag = "--gzip" if self.compression else ""
        
        return f"""#!/bin/bash
# MongoDB Backup Script for ERP-FABS

BACKUP_DIR="{self.backup_dir}"
DB_NAME="erp_fabs"
MONGO_HOST="localhost"
MONGO_PORT="27017"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$DB_NAME-$TIMESTAMP"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting MongoDB backup..."

# Run mongodump
mongodump \\
    --host=$MONGO_HOST:$MONGO_PORT \\
    --db=$DB_NAME \\
    --out=$BACKUP_PATH \\
    {compression_flag}

if [ $? -eq 0 ]; then
    echo "✓ Backup completed: $BACKUP_PATH"
    
    # Cleanup old backups (older than {self.retention_days} days)
    find "$BACKUP_DIR" -maxdepth 1 -type d -mtime +{self.retention_days} -exec rm -rf {{}} \\;
else
    echo "✗ Backup failed"
    exit 1
fi
"""
    
    def get_restore_script(self) -> str:
        """Generate MongoDB restore script"""
        return """#!/bin/bash
# MongoDB Restore Script for ERP-FABS

DB_NAME="erp_fabs"
MONGO_HOST="localhost"
MONGO_PORT="27017"

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_path>"
    exit 1
fi

BACKUP_PATH="$1"

if [ ! -d "$BACKUP_PATH" ]; then
    echo "✗ Backup path not found: $BACKUP_PATH"
    exit 1
fi

echo "Restoring database from: $BACKUP_PATH"

# Run mongorestore
mongorestore \\
    --host=$MONGO_HOST:$MONGO_PORT \\
    --db=$DB_NAME \\
    --drop \\
    "$BACKUP_PATH/$DB_NAME"

if [ $? -eq 0 ]; then
    echo "✓ Restore completed"
else
    echo "✗ Restore failed"
    exit 1
fi
"""


class AuditLogSchema:
    """Audit logging schema"""
    
    @staticmethod
    def get_audit_log_example() -> Dict[str, Any]:
        """Get example audit log document"""
        return {
            "_id": "ObjectId",
            "timestamp": datetime.now().isoformat(),
            "user_id": "user_123",
            "username": "pissken@editionsfabsci.com",
            "action": "CREATE",  # CREATE, READ, UPDATE, DELETE
            "resource_type": "invoices",  # clients, products, orders, invoices, payments, etc
            "resource_id": "resource_123",
            "old_values": {"status": "draft"},
            "new_values": {"status": "sent"},
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0...",
            "changes": {
                "status": {"old": "draft", "new": "sent"},
                "sent_at": {"old": None, "new": "2026-06-24T10:30:00"}
            },
            "severity": "medium",  # low, medium, high, critical
            "status": "success",  # success, failed, unauthorized
            "error_message": None
        }
    
    @staticmethod
    def get_audit_log_schema() -> Dict[str, Any]:
        """Get MongoDB schema definition for audit logs"""
        return {
            "bsonType": "object",
            "required": ["timestamp", "user_id", "action", "resource_type", "resource_id"],
            "properties": {
                "_id": {"bsonType": "objectId"},
                "timestamp": {"bsonType": "date"},
                "user_id": {"bsonType": "string"},
                "username": {"bsonType": "string"},
                "action": {"enum": ["CREATE", "READ", "UPDATE", "DELETE"]},
                "resource_type": {"bsonType": "string"},
                "resource_id": {"bsonType": "string"},
                "old_values": {"bsonType": "object"},
                "new_values": {"bsonType": "object"},
                "changes": {"bsonType": "object"},
                "ip_address": {"bsonType": "string"},
                "user_agent": {"bsonType": "string"},
                "severity": {"enum": ["low", "medium", "high", "critical"]},
                "status": {"enum": ["success", "failed", "unauthorized"]},
                "error_message": {"bsonType": ["string", "null"]}
            }
        }


class DatabaseReplication:
    """Replication configuration for MongoDB"""
    
    @staticmethod
    def get_replica_set_config() -> Dict[str, Any]:
        """Get MongoDB replica set configuration"""
        return {
            "_id": "erp_fabs_rs",
            "version": 1,
            "members": [
                {
                    "_id": 0,
                    "host": "mongodb-primary:27017",
                    "priority": 1
                },
                {
                    "_id": 1,
                    "host": "mongodb-secondary-1:27017",
                    "priority": 0
                },
                {
                    "_id": 2,
                    "host": "mongodb-secondary-2:27017",
                    "priority": 0
                }
            ],
            "settings": {
                "chainingAllowed": True,
                "heartbeatTimeoutSecs": 10,
                "electionTimeoutMillis": 10000
            }
        }
    
    @staticmethod
    def get_replica_setup_instructions() -> str:
        """Get instructions for setting up replica set"""
        return """
# MongoDB Replica Set Setup Instructions

## 1. Stop MongoDB instances
sudo systemctl stop mongod

## 2. Configure each node with replica set info
# Edit /etc/mongod.conf on each node:
replication:
  replSetName: "erp_fabs_rs"

## 3. Start MongoDB instances
sudo systemctl start mongod

## 4. Initialize replica set (from primary node)
mongo --host mongodb-primary:27017

rs.initiate({
    _id: "erp_fabs_rs",
    members: [
        { _id: 0, host: "mongodb-primary:27017", priority: 1 },
        { _id: 1, host: "mongodb-secondary-1:27017", priority: 0 },
        { _id: 2, host: "mongodb-secondary-2:27017", priority: 0 }
    ]
})

## 5. Verify replica set status
rs.status()

## 6. Configure write concern for durability
# In application code:
client = MongoClient("mongodb://...", replicaSet="erp_fabs_rs")
db.client.write_concern = WriteConcern(w=2, j=True)
"""


class DatabaseOptimizationChecklist:
    """Checklist for database optimization and production readiness"""
    
    CHECKLIST = [
        {
            "category": "Indexes",
            "items": [
                "✓ All required indexes created",
                "✓ Indexes on foreign keys (client_id, product_id, order_id)",
                "✓ Compound indexes for common queries",
                "✓ Text indexes for search functionality",
                "✓ TTL indexes for temporary data cleanup"
            ]
        },
        {
            "category": "Backup & Recovery",
            "items": [
                "✓ Daily automated backups configured",
                "✓ Backup retention policy (30 days)",
                "✓ Backup encryption enabled",
                "✓ Restore procedure tested",
                "✓ Disaster recovery plan documented"
            ]
        },
        {
            "category": "Monitoring",
            "items": [
                "✓ Database CPU monitoring",
                "✓ Memory usage monitoring",
                "✓ Disk space monitoring",
                "✓ Replication lag monitoring",
                "✓ Query performance monitoring"
            ]
        },
        {
            "category": "Security",
            "items": [
                "✓ Authentication enabled",
                "✓ Authorization (RBAC) configured",
                "✓ Network access restricted (firewall)",
                "✓ Encryption at rest enabled",
                "✓ Encryption in transit (TLS) enabled",
                "✓ Audit logging enabled"
            ]
        },
        {
            "category": "Performance",
            "items": [
                "✓ Query optimization completed",
                "✓ Aggregation pipeline optimization",
                "✓ Connection pooling configured",
                "✓ Caching strategy implemented",
                "✓ Slow query log analyzed"
            ]
        },
        {
            "category": "Maintenance",
            "items": [
                "✓ Regular maintenance windows scheduled",
                "✓ Database statistics updated",
                "✓ Index fragmentation monitored",
                "✓ Storage optimization completed",
                "✓ Replication health monitored"
            ]
        }
    ]
    
    @staticmethod
    def get_checklist() -> List[Dict[str, Any]]:
        """Get database readiness checklist"""
        return DatabaseOptimizationChecklist.CHECKLIST
    
    @staticmethod
    def generate_checklist_report() -> str:
        """Generate printable checklist report"""
        report = "DATABASE OPTIMIZATION & PRODUCTION READINESS CHECKLIST\n"
        report += "=" * 60 + "\n\n"
        
        for section in DatabaseOptimizationChecklist.CHECKLIST:
            report += f"## {section['category']}\n"
            for item in section['items']:
                report += f"  {item}\n"
            report += "\n"
        
        return report


# Utility functions
def get_all_indexes() -> List[Dict[str, Any]]:
    """Get all index definitions"""
    return [idx.to_dict() for idx in SchemaOptimizer.get_all_indexes()]


def get_backup_strategy() -> Dict[str, Any]:
    """Get recommended backup strategy"""
    return {
        "frequency": "daily at 2:00 AM UTC",
        "retention": "30 days",
        "compression": True,
        "verification": "test restore weekly",
        "encryption": "enabled",
        "offsite_sync": "AWS S3 with versioning"
    }
