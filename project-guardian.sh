#!/bin/bash

# Exit on error
set -e

echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

echo "Creating and activating virtual environment..."
uv venv .venv
source .venv/bin/activate

echo "Installing dependencies..."
# Install core dependencies
uv pip install -e .

# Install test dependencies
uv pip install pytest

# Install development dependencies including pre-commit
uv pip install -e ".[dev]"
uv pip install pre-commit

echo "Setting up pre-commit hooks..."
pre-commit install

echo "Running tests..."
pytest tests/ -v

echo "Setup complete! Virtual environment is activated."
echo "To deactivate the virtual environment, run: deactivate"

# Reactivate the virtual environment to ensure it's properly set up
echo "Reactivating virtual environment..."
deactivate
source .venv/bin/activate
echo "Virtual environment reactivated and ready to use!"
