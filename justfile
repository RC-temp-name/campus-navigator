# Show this menu
default:
    just --list

# Install dependencies (run once after cloning)
install:
    uv sync

# Start the app at http://localhost:5000
run:
    uv run run.py

# Run in production mode (Gunicorn, 4 workers)
prod:
    uv run gunicorn --workers 4 --bind 0.0.0.0:5000 run:app

# Build and run in Docker (port 5000) - Ctrl+C to stop
docker:
    docker compose up --build

# Check code style
lint:
    uvx ruff check .

# Auto-format all code (Python, JS, CSS, HTML)
format:
    uvx ruff format .
    npx --yes prettier@3 --write .
    uvx djlint app/templates --reformat

# Verify formatting without changing files
format-check:
    uvx ruff format --check .
    npx --yes prettier@3 --check .
    uvx djlint app/templates --check

# Auto-fix everything possible, then format
fix:
    uvx ruff check --fix .
    just format

# Release checks: `just lint`, `just format-check`, `uv run pytest`,
# compileall, `uv run tools/validate_data.py`, and `docker compose config`.
# THE command before pushing
check: lint format-check test test-frontend compile validate-data docker-config
    @echo 'All good - ready to push'

# Remove caches and build artifacts
clean:
    rm -rf .pytest_cache .ruff_cache htmlcov
    rm -f .coverage
    find . -type d -name __pycache__ -not -path './.venv/*' -prune -exec rm -rf {} +
    rm -f *.pyc *.pyo
    rm -rf dist build

# Run the Python test suite
test:
    uv run pytest

# Run browser-script tests with Node's built-in test runner
test-frontend:
    node --test tests/frontend/*.test.mjs

# Compile Python sources
compile:
    uv run python -m compileall -q app run.py tools

# Validate canonical graph data
validate-data:
    uv run tools/validate_data.py

# Verify the development compose file without starting containers
docker-config:
    docker compose config

# Run tests with coverage report
coverage:
    uv run pytest --cov=app --cov-report=term-missing --cov-report=html
