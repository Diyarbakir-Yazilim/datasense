.PHONY: build up down restart logs clean

# Build all docker containers
build:
	docker-compose build

# Start all services in the background
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Restart all services
restart:
	docker-compose restart

# View logs for all services
logs:
	docker-compose logs -f

# View backend logs specifically
logs-backend:
	docker-compose logs -f backend

# View AI API logs specifically
logs-ai:
	docker-compose logs -f ai_api

# Stop services and remove volumes (clean database/queues)
clean:
	docker-compose down -v
