# Architectural Decision Records

## ADR-001: FastAPI as the web framework

**Context:** We need an async Python web framework that generates OpenAPI docs automatically, since multiple consumers (web UI, Slack bot, Gmail, AI agents) will integrate against the same API.

**Decision:** Use FastAPI.

**Consequences:**
- Built-in OpenAPI/Swagger docs make it easy for all consumers to discover endpoints.
- Native async support aligns with our I/O-heavy workload (DB, external APIs).
- Large ecosystem and community; easy to hire for.
- We accept the coupling to Starlette's ASGI layer, but this is a thin abstraction.

---

## ADR-002: Self-hosted Postgres on Railway over Supabase

**Context:** We considered Supabase for managed Postgres + auth, but it would create vendor lock-in on auth, row-level security policies, and their client SDK patterns.

**Decision:** Self-host Postgres on Railway with standard SQLAlchemy + Alembic migrations.

**Consequences:**
- Full control over schema, migrations, and connection pooling.
- No dependency on Supabase-specific features (RLS policies, auth hooks).
- We must build our own auth layer, but this is intentional for flexibility.
- Portable to any Postgres host if we leave Railway later.

---

## ADR-003: Backbone-first API design

**Context:** Knot will eventually have a web UI, Slack bot, Gmail integration, and AI agents. Building UI-first would couple the data layer to one consumer's needs.

**Decision:** Build the API backbone first. All consumers are equal clients of the same REST API.

**Consequences:**
- Forces clean separation between business logic and presentation.
- Any new consumer can be added without touching core logic.
- Slower time-to-visual-demo, but more sustainable architecture.
- API design must be consumer-agnostic from the start.

---

## ADR-004: Soft-reject for task dependency cascade

**Context:** Tasks in Knot can have subtasks, and subtasks can depend on parent tasks being accepted. When a parent task gets rejected by its assignee, we must decide what happens to dependent subtasks. Three options exist: cascade-reject (auto-reject all dependents), block (freeze them pending a decision), or soft-reject (mark them stale but keep them alive).

**Decision:** Soft-reject. When a parent task is rejected, dependent subtasks are marked stale with a `staleness_reason` but remain in the database, queryable and reassignable.

**Consequences:**
- Most reversible option; aligns with our reversibility principle.
- Matches how real teams negotiate: rejection usually means "let's renegotiate," not "discard everything."
- Requires a "stale" task state and a `staleness_reason` field.
- The dependency graph itself is preserved, so reactivating a parent can reactivate dependents.
- Schema implication: tasks table needs `state` and `staleness_reason` columns; there will be a `task_dependencies` table separate from `parent_task_id`.

---

## ADR-005: Separate task_date_proposals table

**Context:** Task scheduling involves negotiation — a delegator proposes dates, the assignee can counter-propose or accept. Storing this in a single `due_date` column on the tasks table would lose negotiation history and make multi-round negotiation impossible.

**Decision:** Create a separate `task_date_proposals` table that tracks each proposal round with proposer, proposed date, status (pending/accepted/rejected), and timestamps.

**Consequences:**
- Supports N rounds of negotiation without schema changes.
- The "current" due date is derived from the latest accepted proposal.
- Slightly more complex queries for "what's the due date?" but worth the flexibility.
- Activity log events can reference specific proposals.

---

## ADR-006: Local Docker Postgres + Railway-hosted Postgres for development

**Context:** We need a development database. Options were Railway-only, local-only, or both. Railway-only is slow (network on every test), prevents offline work, and risks schema collisions between developers/agents. Local-only diverges from production. Both gives fast iteration locally and a production-mirror remotely.

**Decision:** Use Docker Compose to run Postgres locally for daily development and tests. Use a Railway-hosted Postgres as the deployed dev environment. Alembic migrations are the single source of truth for the schema across both.

**Consequences:**
- Adds Docker Desktop as a required local dependency.
- Tests run against local Postgres only (fast, isolated, throwaway).
- `DATABASE_URL` in `.env` points to local Postgres; Railway URL is set as a Railway environment variable.
- Schema drift between environments is impossible as long as migrations are applied to both.

---

## ADR-007: UUIDv7 as primary key strategy

**Context:** Multi-tenant SaaS leaks information through sequential integer IDs (customer counts, growth rates). Random UUIDv4 keys cause Postgres B-tree index fragmentation at scale. UUIDv7 is timestamp-ordered, giving UUID benefits without the index penalty. Python 3.14 includes `uuid.uuid7()` natively.

**Decision:** All primary keys are UUIDv7, generated application-side via Python's standard library `uuid.uuid7()`.

**Consequences:**
- IDs are larger than integers (16 bytes vs 8), but the multi-tenant safety and offline-generation flexibility outweigh the cost.
- IDs can be generated before insert, simplifying event publishing and client-side workflows.
- The shared Base model will define `id` as a UUID column with a default generator.

---

## ADR-008: Business units modeled as a self-referential nullable hierarchy

**Context:** Customer organizations have varying structures. Some are flat (one company, one team list). Others nest (region > division > department). Imposing one structure excludes the other. A separate `parent_unit_id` self-reference, nullable, lets each customer choose.

**Decision:** The `business_units` table has a nullable `parent_unit_id` column referencing `business_units.id`. Flat organizations leave it NULL. Nested organizations populate it.

**Consequences:**
- Single table handles both topologies.
- Recursive CTEs are required to query full hierarchies (standard Postgres).
- If deep hierarchies become slow, a materialized path column can be added later without schema breakage.
- The `teams` table sits beneath `business_units`, not beside it.

**Status: Superseded by ADR-011 (2026-05-12)** — Business units removed in favor of a flat Organization → Project model. See ADR-011.

---

## ADR-009: Async SQLAlchemy with connection pooling

**Context:** FastAPI is async and most route handlers will do at least one database query. Without connection pooling, every query pays a 5–15ms TCP handshake cost. With pooling, connections are reused. Managed Postgres providers (Railway, Neon, RDS) silently kill idle connections, so the pool must validate connections before handing them out.

**Decision:** Use SQLAlchemy 2.x async engine with these pool settings: `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`, `pool_recycle=1800`. The asyncpg driver is the connection layer.

**Consequences:**
- ~5–15 idle connections held open per app instance. Acceptable on any Postgres plan above the free tier.
- `pool_pre_ping` adds <1ms per request to validate connections; eliminates "dead connection" errors after idle periods.
- `pool_recycle=1800` (30 min) ensures connections are refreshed before any managed provider's idle-kill timeout.
- FastAPI dependency injection provides one session per request, properly closed after the response.

---

## ADR-010: Shared Base model with timestamps and soft-delete

**Context:** Every domain table benefits from creation/update timestamps for audit and sorting. Soft-delete (a `deleted_at` column instead of physical deletion) preserves history, supports undo, and is the SaaS default for recoverability.

**Decision:** All ORM models inherit from a shared declarative Base that provides:
- `id`: UUID primary key, generated by Python's `uuid.uuid7()`
- `created_at`: timestamp with timezone, default `now()`
- `updated_at`: timestamp with timezone, default `now()`, updated on change
- `deleted_at`: nullable timestamp with timezone, NULL = not deleted

Default queries must filter out `deleted_at IS NOT NULL` rows. A helper will be added to make this ergonomic.

**Consequences:**
- Every table inherits these four columns.
- All queries must consider `deleted_at`; we'll add a session-level filter or query-builder helper to avoid mistakes.
- Hard deletes are still possible when legally required (GDPR right-to-be-forgotten) — those will be explicit and rare.
- Timestamps are always UTC, stored as `timestamptz`.

---

## ADR-011: Flat Organization → Project model for collaboration scope

**Context:** Earlier scaffolding (ADR-008) modeled a hierarchical Organization → BusinessUnit → Team structure. On reflection, this imposed project-management structure that Knot does not need. Knot is a collaboration tool, not a project management tool — it helps people assign, negotiate, and complete work, but does not impose epics, sprints, or hierarchical departments. Customers organize themselves; we provide the surface, not the structure.

**Decision:** The domain is flat: an Organization (the customer/tenant) contains many Projects. Each Project has one or more Leads and many Members, recorded in a `project_memberships` join table. Tasks (Phase 3) will live inside Projects. Users belong to exactly one Organization. There are no business units, teams, or workspaces.

Tables (Phase 1):
- `organizations` (tenant root, billing boundary)
- `users` (one per person, scoped to an organization via `org_id`)
- `projects` (collaboration containers, scoped via `org_id`)
- `project_memberships` (user × project, with role: `'lead'` | `'member'`)

**Consequences:**
- Schema is dramatically simpler — four tables vs nine.
- Cross-functional collaboration happens by membership, not org structure: the same user appears on multiple projects with different roles.
- Multi-tenancy enforced by `org_id` on every domain table; queries filter by the requesting user's `org_id` at the application layer.
- If a customer later needs business units or workspaces, we add that layer when a real need forces it. The current model does not prevent it.
- Roles are stored as a VARCHAR with a CHECK constraint (not a Postgres enum) so adding roles later is a one-line migration.
