#!/bin/bash

# Health check script for Emergent IA - ERP FABS-CI V7

# Check if backend is responding
curl -f http://localhost:8001/health || exit 1

# Check MongoDB connection
mongosh --eval "db.adminCommand('ping')" --quiet || exit 1

# Check Redis connection
redis-cli ping || exit 1

echo "All services are healthy"
exit 0
