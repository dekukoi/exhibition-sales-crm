# ADR 0002: Database access layer — SQLAlchemy + Alembic

Status: Accepted
Date: 2026-09-14

## Context

The assignment requires the archive to "grow to 100,000 contacts, with the associated companies, opportunities and activities; everyday searches should remain practical at that size" — schema and index design are therefore directly gradable, not incidental. The candidate initially assessed their own Python fluency as reading-comfortable but not confident writing an unfamiliar ORM's query API, and leaned toward raw SQL for transparency. After a short personal research pass, the candidate found SQLAlchemy's learning curve acceptable and preferred its productivity and Alembic's migration tooling, particularly for evolving the schema alongside the importer.

## Decision

Use SQLAlchemy as the ORM, with Alembic for schema migrations, on top of the Postgres 17 instance already defined in `compose.yml`.

## Alternatives considered

- **Raw SQL via `psycopg` (v3)**, hand-written `schema.sql`/migration files, small parameterized-query functions — maximal transparency and the smallest new-API surface, and forces deliberate index design for the 100k-row requirement. Not chosen once SQLAlchemy itself proved approachable enough, in favor of the ORM's structure and Alembic's migration workflow.
- **SQLModel** — a gentler, Pydantic-flavored layer over SQLAlchemy with tighter FastAPI integration. Not chosen once SQLAlchemy directly proved workable, to avoid an extra layer of indirection.
- **Prisma (Python client)** — rejected as community-maintained and less mature for Python than SQLAlchemy/Alembic.
- **Tortoise ORM / Piccolo** — rejected as a third ecosystem to learn from scratch under a same-day deadline, with less community documentation to fall back on when stuck.

## Consequences

Indexes (on `company_code`, `contact_code`, `fair_edition_code`, opportunity status/dates, `activity_log.follow_up_on`, etc.) must be designed deliberately rather than relying on ORM defaults, to satisfy the practical-search-at-100k requirement — SQLAlchemy makes this easy to get wrong silently (e.g. N+1 queries), so query plans should be spot-checked, not assumed. Alembic migrations track schema evolution alongside the importer, which must remain idempotent against a replaced `data/` folder plus `reset.sh` + `dev.sh`.
