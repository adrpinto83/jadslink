#!/bin/bash
set -e # Exit on any error

# 1. Pull latest changes
echo "Pulling latest changes from Git..."
git pull origin main

# 2. Stop running services
echo "Stopping running services..."
docker-compose down

# 3. Rebuild images
echo "Rebuilding Docker images..."
docker-compose build

# 4. Start services in detached mode
echo "Starting services..."
docker-compose up -d

# 5. Prune old images and volumes
echo "Pruning old Docker images and volumes..."
docker system prune -af

echo "Deployment finished!"
