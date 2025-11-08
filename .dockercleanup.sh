#!/bin/bash
# =============================================================================
# Docker Cleanup Script for AutoCodit Agent
# =============================================================================
# This script cleans up Docker resources to prevent network connection errors
# and removes orphaned containers.
#
# Usage: ./dockercleanup.sh
# =============================================================================

set -e

echo "🧹 Starting Docker cleanup for AutoCodit Agent..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Stop all running containers for this project
echo "${YELLOW}📦 Stopping all AutoCodit Agent containers...${NC}"
docker-compose down --remove-orphans 2>/dev/null || true

# Remove any dangling autocodit containers
echo "${YELLOW}🗑️  Removing orphaned containers...${NC}"
docker ps -a | grep autocodit | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true

# Remove the old network if it exists
echo "${YELLOW}🌐 Cleaning up Docker networks...${NC}"
docker network ls | grep autocodit | awk '{print $1}' | xargs -r docker network rm 2>/dev/null || true

# Prune unused networks
echo "${YELLOW}✂️  Pruning unused networks...${NC}"
docker network prune -f

# Remove dangling images
echo "${YELLOW}🖼️  Removing dangling images...${NC}"
docker image prune -f

# Remove dangling volumes (optional - be careful with data)
echo "${YELLOW}💾 Checking for unused volumes...${NC}"
UNUSED_VOLUMES=$(docker volume ls -qf dangling=true | grep -v postgres_data | grep -v redis_data | grep -v runner-workspace || true)
if [ -n "$UNUSED_VOLUMES" ]; then
    echo "${YELLOW}Removing unused volumes...${NC}"
    echo "$UNUSED_VOLUMES" | xargs -r docker volume rm 2>/dev/null || true
else
    echo "${GREEN}No unused volumes to remove${NC}"
fi

echo ""
echo "${GREEN}✅ Cleanup completed successfully!${NC}"
echo ""
echo "${YELLOW}🚀 You can now start the project with:${NC}"
echo "   docker-compose up --build"
echo ""
echo "${YELLOW}📊 Current Docker status:${NC}"
echo "${YELLOW}Containers:${NC}"
docker ps -a --filter "name=autocodit" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "${YELLOW}Networks:${NC}"
docker network ls | grep -E 'NETWORK ID|autocodit' || echo "No autocodit networks found"
echo ""
echo "${YELLOW}Volumes:${NC}"
docker volume ls | grep -E 'DRIVER|autocodit|postgres_data|redis_data|runner-workspace' || echo "No autocodit volumes found"