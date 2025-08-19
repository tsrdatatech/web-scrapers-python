.PHONY: install dev test lint format clean run help

help: ## Show this help message
	@echo "Universal Web Scraper (Python) - Available Commands"
	@echo "=================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with Poetry
	poetry install
	poetry run playwright install

dev: ## Install with development dependencies
	poetry install --with dev
	poetry run playwright install

test: ## Run tests
	poetry run pytest

lint: ## Run linting
	poetry run flake8 src/
	poetry run mypy src/

format: ## Format code
	poetry run black src/
	poetry run isort src/

format-check: ## Check code formatting
	poetry run black --check src/
	poetry run isort --check-only src/

clean: ## Clean up cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf storage/
	rm -f scraper.log

run: ## Run the scraper with example URL
	poetry run python -m src.main --url https://example.com --parser generic-news

run-seeds: ## Run the scraper with seeds file
	poetry run python -m src.main --file seeds.txt

shell: ## Activate Poetry shell
	poetry shell

setup: ## Run setup script
	./setup.sh
