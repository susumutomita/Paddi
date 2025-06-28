# Paddi - Multi-agent Cloud Audit Automation Tool
# Makefile for development, testing, and CI/CD

# Default shell
SHELL := /bin/bash

# Python settings
PYTHON := python
PIP := pip
PYTEST := python -m pytest

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

##@ General

.PHONY: help
help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\n${BLUE}Usage:${NC}\n  make ${GREEN}<target>${NC}\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2 } /^##@/ { printf "\n${YELLOW}%s${NC}\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: all
all: format lint test ## Run format, lint, and test

##@ Setup & Dependencies

.PHONY: install
install: ## Install all dependencies (Python, pre-commit hooks, npm packages)
	@printf "${BLUE}Installing dependencies...${NC}\n"
	$(PIP) install -r requirements.txt
	pre-commit install
	npm install
	@printf "${GREEN}✓ Dependencies installed${NC}\n"

.PHONY: install-dev
install-dev: install ## Install development dependencies
	@printf "${BLUE}Installing development dependencies...${NC}\n"
	$(PIP) install -r requirements-dev.txt
	@printf "${GREEN}✓ Development dependencies installed${NC}\n"

##@ Testing

.PHONY: test
test: ## Run tests with verbose output
	@printf "${BLUE}Running tests...${NC}\n"
	$(PYTEST) -v

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@printf "${BLUE}Running tests with coverage...${NC}\n"
	$(PYTEST) -v --cov=app

.PHONY: test-coverage-check
test-coverage-check: ## Run tests with coverage check (fail if < 80%)
	@printf "${BLUE}Running tests with coverage check (80%% minimum)...${NC}\n"
	$(PYTEST) --cov=app --cov-report=term-missing --cov-fail-under=80

.PHONY: test-debug
test-debug: ## Run tests in debug mode with logging
	@printf "${BLUE}Running tests in debug mode...${NC}\n"
	$(PYTEST) -vv -o log_cli=true

.PHONY: test-watch
test-watch: ## Run tests in watch mode (requires pytest-watch)
	@printf "${BLUE}Running tests in watch mode...${NC}\n"
	ptw

##@ Code Quality

.PHONY: format
format: ## Format code with black, isort, and markdownlint
	@printf "${BLUE}Formatting code...${NC}\n"
	black .
	isort .
	npx markdownlint-cli -c .markdownlint.json --fix docs/**/*.md README.md CLAUDE.md presentation.md
	@printf "${GREEN}✓ Code formatted${NC}\n"

.PHONY: lint
lint: lint-python lint-security lint-yaml lint-markdown ## Run all linters

.PHONY: lint-python
lint-python: ## Run Python linters (black, isort, pylint, flake8)
	@printf "${BLUE}Running Python linters...${NC}\n"
	black . --check
	isort . --check
	cd app && pylint . --rcfile=../.pylintrc
	flake8 .
	@printf "${GREEN}✓ Python linting passed${NC}\n"

.PHONY: lint-security
lint-security: ## Run security checks with bandit and detect-secrets
	@printf "${BLUE}Running security checks...${NC}\n"
	bandit -c pyproject.toml -r app/
	@printf "${GREEN}✓ Security checks passed${NC}\n"

.PHONY: lint-yaml
lint-yaml: ## Run YAML linter
	@printf "${BLUE}Running YAML linter...${NC}\n"
	yamllint -c .yamllint .
	@printf "${GREEN}✓ YAML linting passed${NC}\n"

.PHONY: lint-markdown
lint-markdown: ## Run Markdown linters
	@printf "${BLUE}Running Markdown linters...${NC}\n"
	npx markdownlint-cli -c .markdownlint.json docs/**/*.md README.md CLAUDE.md presentation.md
	npx textlint ./README.md
	@printf "${GREEN}✓ Markdown linting passed${NC}\n"

.PHONY: update-claude-secrets
update-claude-secrets: ## Update Claude secrets
	./set_claude_code_secrets.sh

##@ Pre-commit Checks

.PHONY: check-files
check-files: ## Check for large files and other issues
	@printf "${BLUE}Checking for large files, case conflicts, merge conflicts...${NC}\n"
	@find . -type f -size +1000k -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.venv/*" -not -path "./cli/target/*" -not -name "*.pdf" | if read line; then printf "${RED}Large files found:${NC}\n"; echo "$$line"; exit 1; fi
	@printf "${GREEN}✓ No large files found${NC}\n"

.PHONY: before-commit
before-commit: check-files test-coverage-check format lint ## Run all checks before committing

.PHONY: before_commit
before_commit: before-commit ## Alias for before-commit

.PHONY: check-all
check-all: before-commit ## Run all checks and display success message
	@printf "${GREEN}✅ All checks passed!${NC}\n"

##@ Application

.PHONY: run-collector
run-collector: ## Run the GCP Configuration Collector agent
	@printf "${BLUE}Running GCP Configuration Collector...${NC}\n"
	$(PYTHON) app/collector/agent_collector.py

.PHONY: run-explainer
run-explainer: ## Run the Security Risk Explainer agent
	@printf "${BLUE}Running Security Risk Explainer...${NC}\n"
	$(PYTHON) app/explainer/agent_explainer.py

.PHONY: run-reporter
run-reporter: ## Run the Report Generator agent
	@printf "${BLUE}Running Report Generator...${NC}\n"
	$(PYTHON) app/reporter/agent_reporter.py

.PHONY: run-all
run-all: ## Run all agents in sequence
	@printf "${BLUE}Running all agents...${NC}\n"
	$(MAKE) run-collector
	$(MAKE) run-explainer
	$(MAKE) run-reporter
	@printf "${GREEN}✓ All agents completed${NC}\n"

##@ Presentation

.PHONY: presentation-pdf
presentation-pdf: ## Export presentation to PDF using Marp
	@printf "${BLUE}Exporting presentation to PDF...${NC}\n"
	npx marp presentation.md --pdf --allow-local-files --html
	@printf "${GREEN}✓ Presentation exported to presentation.pdf${NC}\n"

.PHONY: presentation-html
presentation-html: ## Export presentation to HTML using Marp
	@printf "${BLUE}Exporting presentation to HTML...${NC}\n"
	npx marp presentation.md --html --allow-local-files
	@printf "${GREEN}✓ Presentation exported to presentation.html${NC}\n"

.PHONY: presentation-watch
presentation-watch: ## Watch presentation changes and auto-reload
	@printf "${BLUE}Starting presentation in watch mode...${NC}\n"
	npx marp presentation.md --watch --server

##@ Cleanup

.PHONY: clean
clean: ## Clean up generated files and caches
	@printf "${BLUE}Cleaning up...${NC}\n"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".coverage" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	@printf "${GREEN}✓ Cleanup completed${NC}\n"

.PHONY: clean-all
clean-all: clean ## Clean everything including node_modules
	@printf "${BLUE}Cleaning all dependencies...${NC}\n"
	rm -rf node_modules/
	rm -rf .venv/
	@printf "${GREEN}✓ All cleaned${NC}\n"
