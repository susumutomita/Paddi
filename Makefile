.PHONY: install
install:
	pip install -r requirements.txt && pre-commit install && npm install

.PHONY: test
test:
	python -m pytest -v

.PHONY: test_coverage
test_coverage:
	python -m pytest  -v --cov=app

.PHONY: test_debug
test_debug:
	python -m pytest -vv -o log_cli=true

.PHONY: test_watch
test_watch:
	ptw

.PHONY: lint
lint:
	black . --check
	isort . --check
	cd app && pylint . --rcfile=../.pylintrc
	yamllint -c .yamllint .
	flake8 .
	npx textlint ./README.md

.PHONY: format
format:
	black .
	isort .

.PHONY: before_commit
before_commit: test format lint

# -------------------------------
# Presentation
# -------------------------------
.PHONY: presentation_pdf
presentation_pdf:        # Export presentation to PDF using Marp
	npx marp presentation.md --pdf --allow-local-files --html

.PHONY: presentation_html
presentation_html:       # Export presentation to HTML using Marp
	npx marp presentation.md --html --allow-local-files

.PHONY: presentation_watch
presentation_watch:      # Watch presentation changes and auto-reload
	npx marp presentation.md --watch --server

.PHONY: run
run:
	ground-monitoring
