# LRBF Development Makefile
# Institutional-grade commands for production trading platform

.PHONY: help install dev test clean lint format migrate db-migrate db-backup start stop logs

help:  ## Show this help message
	@echo 'LRBF Development Commands'
	@echo '========================='
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt

dev:  ## Run development server
	python app.py

test:  ## Run all tests
	python -m pytest tests/

clean:  ## Clean temporary files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*~' -delete

lint:  ## Run linter
	flake8 backend/ app.py

format:  ## Format code with black
	black backend/ app.py

db-migrate:  ## Run database migration
	python scripts/migrate_db.py

db-backup:  ## Backup database
	@mkdir -p data/backups
	@cp data/*.db data/backups/backup_$$(date +%Y%m%d_%H%M%S).db
	@echo "Database backed up to data/backups/"

start:  ## Start application (production mode)
	./start.sh

stop:  ## Stop application
	@pkill -f "python app.py" || echo "No running instances found"

logs:  ## View application logs
	tail -f logs/*.log
