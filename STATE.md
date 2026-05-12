## Current State

- Phase completed: Phase 1 (DB schema + first migration applied)
- Last commit: "Phase 0 + Phase 1: project skeleton, db plumbing, core schema"
- Database state: 4 domain tables exist (organizations, users, projects, project_memberships) plus alembic_version. One migration applied: 9e54acd635d8 "create core tables".

## What works today

- FastAPI server runs locally via `uvicorn app.main:app --reload`
- Health endpoints: GET /health and GET /health/db
- Local Postgres in Docker on port 5433 (container: knot-postgres)
- pytest passes one health-endpoint test
- Alembic migrations run via async env.py

## Resuming the project

1. Make sure Docker Desktop is running
2. `cd C:\Users\Akhik\knot`
3. `docker compose up -d` (if Postgres container is stopped)
4. `.venv\Scripts\Activate.ps1`
5. Verify: `pytest` (should pass)
6. Verify: `uvicorn app.main:app --reload` then visit /health/db

## Next phase: Phase 2 — Multi-tenancy + auth

Goals:
- Add a FastAPI dependency that injects the current user's org_id into every authenticated route
- Decide on auth strategy: bearer JWT (rolled by us), Clerk, or Authentik/Authelia (open source)
- Add a `password_hash` column to users OR keep auth fully external (passwordless via magic link, or OAuth)
- Write the org/user CRUD endpoints needed to seed test data

Open questions to decide at start of Phase 2:
- Auth provider choice
- Whether to support passwordless from day one
- Whether to add an "organization owner" concept or rely on first-user logic

## Reference files

- CLAUDE.md: project principles + 12-phase roadmap
- DECISIONS.md: 11 ADRs explaining every architectural choice
- README.md: local setup commands
