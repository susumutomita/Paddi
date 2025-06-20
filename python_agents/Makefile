.PHONY: install test test-coverage lint format before-commit clean

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-coverage:
	pytest tests/ --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=80

# Run linting
lint:
	flake8 . --max-line-length=88 --extend-ignore=E203,W503
	pylint collector/ explainer/ reporter/ tests/ || true
	mypy . --ignore-missing-imports || true

# Format code
format:
	black .
	isort .

# Run all quality checks before commit
before-commit: format lint test-coverage
	@echo "All quality checks passed!"

# Clean up generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov .pytest_cache .mypy_cache
	rm -rf data/ output/

# Run collector with mock data
run-collector:
	python collector/agent_collector.py --use_mock=True

# Run collector with real GCP data (requires authentication)
run-collector-real:
	python collector/agent_collector.py --use_mock=False

# Help
help:
	@echo "Available targets:"
	@echo "  install         Install project dependencies"
	@echo "  test            Run unit tests"
	@echo "  test-coverage   Run tests with coverage report"
	@echo "  lint            Run linting tools"
	@echo "  format          Format code with black and isort"
	@echo "  before-commit   Run all quality checks"
	@echo "  clean           Clean up generated files"
	@echo "  run-collector   Run collector with mock data"
	@echo "  run-collector-real  Run collector with real GCP data"