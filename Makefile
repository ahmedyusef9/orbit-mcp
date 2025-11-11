# Makefile for MCP Server

.PHONY: help install install-dev test test-cov lint format clean docs run

# Default target
help:
	@echo "MCP Server - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  install        Install MCP Server"
	@echo "  install-dev    Install with development dependencies"
	@echo "  test           Run tests"
	@echo "  test-cov       Run tests with coverage"
	@echo "  lint           Check code style"
	@echo "  format         Format code"
	@echo "  clean          Remove build artifacts"
	@echo ""
	@echo "Usage:"
	@echo "  run            Run MCP Server CLI"
	@echo "  config         Initialize configuration"

# Installation
install:
	pip install -r requirements.txt
	pip install -e .

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -e .

# Testing
test:
	pytest

test-cov:
	pytest --cov=mcp --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

# Code Quality
lint:
	@echo "Running flake8..."
	flake8 src/ tests/
	@echo "Running mypy..."
	mypy src/
	@echo "Running pylint..."
	pylint src/mcp/

format:
	@echo "Formatting with black..."
	black src/ tests/
	@echo "Sorting imports..."
	isort src/ tests/

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete"

# Documentation
docs:
	@echo "Building documentation..."
	cd docs && make html

# Usage
run:
	mcp --help

config:
	mcp config init
	@echo "Configuration initialized at ~/.mcp/config.yaml"

# Version
version:
	@python -c "import mcp; print(f'MCP Server v{mcp.__version__}')"
