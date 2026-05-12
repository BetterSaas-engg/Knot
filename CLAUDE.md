# Knot

Knot is a multi-tenant SaaS collaboration platform for managing delegated tasks with scheduling negotiation. It exposes a FastAPI backbone API that will be consumed by a web UI, Slack bot, Gmail integration, and AI agents.

## Architecture Principles

- **Backbone-first**: FastAPI is the center of gravity. All consumers (web UI, Slack, Gmail, AI agents) interact through this API.
- **Multi-tenant from day one**: Every domain table carries an `org_id`. All queries are scoped to the tenant.
- **Event-driven**: State changes publish events. The `app/events/` module is reserved for this.
- **Reversibility**: No lock-in. Standard FastAPI + Postgres + Alembic. No framework-specific magic.
- **Python 3.14**, deployed to Railway.

## Folder Structure

```
app/
├── main.py          # FastAPI app creation and router mounting
├── config.py        # pydantic-settings, reads .env
├── api/routes/      # Route handlers, organized by domain
├── core/            # Shared utilities: auth, dependencies, middleware
├── db/              # SQLAlchemy engine, session, base model
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic request/response schemas
├── services/        # Business logic layer
└── events/          # Event bus and event definitions
```

## Coding Standards

- Type hints are required on all function signatures.
- Use `ruff` for linting and formatting.
- Prefer composition over inheritance.
- No global mutable state.
- Async by default for I/O-bound operations.

## Build Phases

| Phase | Milestone |
|-------|-----------|
| **0** | **Project skeleton (current)** |
| 1 | DB schema + Alembic migrations |
| 2 | Multi-tenancy + auth |
| 3 | Core task API: create, accept, reject, counter-propose |
| 4 | Event bus (Postgres LISTEN/NOTIFY or Redis Streams) |
| 5 | Notifications worker (in-app first) |
| 6 | Minimal web UI (Next.js, demo-grade) |
| 7 | Notes with rich text (Tiptap) |
| 8 | Calendar view |
| 9 | Slack integration with interactive buttons |
| 10 | Gmail integration (outbound first) |
| 11 | Task dependencies + soft-reject cascade |
| 12 | Agent API surface (scoped tokens, agent-friendly endpoints) |

## Important

Before making changes, read `DECISIONS.md` to understand past architectural choices.
