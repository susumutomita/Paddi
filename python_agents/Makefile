.PHONY: help install test coverage lint format before-commit clean

PYTHON := python3
PIP := pip3
BLACK := black
FLAKE8 := flake8
PYTEST := pytest
COVERAGE := coverage

# Default target
help:
	@echo "Available targets:"
	@echo "  install       - Install dependencies"
	@echo "  test          - Run unit tests"
	@echo "  coverage      - Run tests with coverage report"
	@echo "  lint          - Run flake8 linter"
	@echo "  format        - Format code with black"
	@echo "  before-commit - Run all quality checks (format, lint, test, coverage)"
	@echo "  clean         - Clean up generated files"

# Install dependencies
install:
	$(PIP) install -r requirements.txt

# Run tests
test:
	$(PYTEST) tests/ -v

# Run tests with coverage
coverage:
	$(COVERAGE) run -m pytest tests/ -v
	$(COVERAGE) report -m
	$(COVERAGE) html
	@echo "Coverage report generated in htmlcov/index.html"

# Check coverage threshold (80%)
coverage-check: coverage
	$(COVERAGE) report --fail-under=80

# Run linter
lint:
	$(FLAKE8) collector/ explainer/ reporter/ tests/ --max-line-length=100 --extend-ignore=E203,W503

# Format code
format:
	$(BLACK) collector/ explainer/ reporter/ tests/ --line-length=100

# Run all checks before committing
before-commit: format lint test coverage-check
	@echo "✅ All quality checks passed!"

# Clean up generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf data/collected.json