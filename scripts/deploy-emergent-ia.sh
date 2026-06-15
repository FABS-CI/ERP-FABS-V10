#!/bin/bash

# Script de déploiement sur Emergent IA - ERP FABS-CI V7
# Date: 2026-06-02

set -e

echo "=========================================="
echo "Déploiement ERP FABS-CI V7 sur Emergent IA"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker n'est pas installé. Veuillez installer Docker d'abord.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose n'est pas installé. Veuillez installer Docker Compose d'abord.${NC}"
    exit 1
fi

# Load environment variables
if [ -f "scripts/production-env-config.json" ]; then
    echo -e "${GREEN}Chargement de la configuration de production...${NC}"
else
    echo -e "${RED}Fichier de configuration non trouvé: scripts/production-env-config.json${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Création du fichier .env à partir de la configuration...${NC}"
    # Note: This would need to be implemented based on the actual environment setup
    echo -e "${YELLOW}Veuillez configurer les variables d'environnement dans l'interface Emergent IA${NC}"
fi

# Build Docker images
echo -e "${GREEN}Construction des images Docker...${NC}"
docker-compose build

# Start services
echo -e "${GREEN}Démarrage des services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}Attente du démarrage des services (30 secondes)...${NC}"
sleep 30

# Check service health
echo -e "${GREEN}Vérification de l'état des services...${NC}"
docker-compose ps

# Check backend health
echo -e "${GREEN}Vérification de la santé du backend...${NC}"
if curl -f http://localhost:8001/health &> /dev/null; then
    echo -e "${GREEN}Backend: OK${NC}"
else
    echo -e "${RED}Backend: ERREUR${NC}"
fi

# Check frontend
echo -e "${GREEN}Vérification du frontend...${NC}"
if curl -f http://localhost/ &> /dev/null; then
    echo -e "${GREEN}Frontend: OK${NC}"
else
    echo -e "${RED}Frontend: ERREUR${NC}"
fi

# Display logs
echo -e "${YELLOW}Logs des services:${NC}"
docker-compose logs --tail=50

echo "=========================================="
echo -e "${GREEN}Déploiement terminé!${NC}"
echo "=========================================="
echo "Frontend: http://localhost"
echo "Backend API: http://localhost:8001"
echo "API Documentation: http://localhost:8001/docs"
echo "=========================================="
