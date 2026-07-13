#!/bin/bash

# Exit on any error
set -e

echo "Starting deployment of DataSense..."

# Navigate to project directory (assuming it's cloned here)
# cd /path/to/datasense

echo "Pulling latest code from GitHub..."
git pull origin main

echo "Building and starting Docker containers in production mode..."
# Use the production docker-compose file and build images
docker-compose -f docker-compose.prod.yml up --build -d

echo "Cleaning up old docker images to save space..."
docker image prune -f

echo "Deployment complete! DataSense is now running in production."
docker-compose -f docker-compose.prod.yml ps
