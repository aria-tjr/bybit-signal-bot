.PHONY: help build run stop logs test lint deploy clean

# Default target
help:
	@echo "Crypto Signal Bot - Available Commands:"
	@echo "  make build    - Build Docker images"
	@echo "  make run      - Run the bot in development mode"
	@echo "  make stop     - Stop all containers"
	@echo "  make logs     - Show container logs"
	@echo "  make test     - Run test suite"
	@echo "  make lint     - Run linters"
	@echo "  make deploy   - Deploy to production"
	@echo "  make clean    - Clean up containers and volumes"

# Build Docker images
build:
	@echo "Building Docker images..."
	cd docker && docker-compose build

# Run in development mode
run: build
	@echo "Starting bot in development mode..."
	cd docker && docker-compose up -d
	@echo "Bot started! Check logs with 'make logs'"

# Stop all containers
stop:
	@echo "Stopping all containers..."
	cd docker && docker-compose down

# Show logs
logs:
	cd docker && docker-compose logs -f

# Run tests
test:
	@echo "Running test suite..."
	cd docker && docker-compose run --rm app pytest -v --cov=app --cov-report=term-missing

# Run linters
lint:
	@echo "Running linters..."
	cd docker && docker-compose run --rm app sh -c "ruff check app/ && black --check app/ && mypy --strict app/"

# Deploy to production
deploy:
	@echo "Deploying to production..."
	git pull origin main
	cd docker && docker-compose pull
	cd docker && docker-compose up -d --remove-orphans
	@echo "Deployment complete!"

# Clean up
clean:
	@echo "Cleaning up containers and volumes..."
	cd docker && docker-compose down -v
	docker system prune -f
	@echo "Cleanup complete!"

# Development setup
dev-setup:
	@echo "Setting up development environment..."
	python -m venv venv
	./venv/bin/pip install -r requirements.txt
	cp .env.example .env
	@echo "Development setup complete! Edit .env file with your credentials."

# Format code
format:
	@echo "Formatting code..."
	black app/
	ruff check --fix app/

# Generate documentation
docs:
	@echo "Generating documentation..."
	cd docs && make html
	@echo "Documentation generated in docs/_build/html/"

# Database migrations
migrate:
	@echo "Running database migrations..."
	cd docker && docker-compose run --rm app alembic upgrade head

# Backup database
backup:
	@echo "Backing up database..."
	mkdir -p backups
	cd docker && docker-compose exec timescaledb pg_dump -U postgres crypto_signals | gzip > ../backups/backup_$(shell date +%Y%m%d_%H%M%S).sql.gz
	@echo "Backup complete!"

# Monitor performance
monitor:
	@echo "Opening monitoring dashboards..."
	@echo "Grafana: http://localhost:3000 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"

# Quick deploy (one-liner)
quick-deploy: clean build deploy
	@echo "Quick deployment complete!" 