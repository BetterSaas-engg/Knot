# Knot

Knot is a multi-tenant SaaS collaboration platform for managing delegated tasks with scheduling negotiation. It provides a FastAPI backbone API designed to be consumed by a web UI, Slack bot, Gmail integration, and AI agents.

## Local Database

**Prerequisite:** Docker Desktop must be running.

```powershell
# Start the database
docker compose up -d

# Stop the database
docker compose down

# Wipe the database (destroys all data)
docker compose down -v

# View logs
docker compose logs -f db

# Connect with psql
docker exec -it knot-postgres psql -U knot -d knot
```

## Database Migrations

```powershell
# Generate a new migration from model changes
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head

# Rollback the last migration
alembic downgrade -1

# Show the current revision
alembic current

# Show migration history
alembic history
```

## Local Setup (Windows)

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install and Run

```powershell
# Create and activate a virtual environment
uv venv
.venv\Scripts\Activate.ps1

# Install dependencies
uv pip install -e ".[dev]"

# Copy environment config
Copy-Item .env.example .env

# Start the dev server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Run Tests

```powershell
pytest
```

## Project Structure

See `CLAUDE.md` for architecture details and `DECISIONS.md` for architectural decision records.
