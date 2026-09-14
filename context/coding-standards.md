# Coding Standards

Stack per `docs/adr/0001-0004.md`: Python 3.x + FastAPI backend, SQLAlchemy + Alembic on
Postgres 17, React + shadcn/ui frontend, two separate Docker services talking over REST.

## Backend (Python)

- Type hints everywhere; this is the JD's stated must-have, so code that demonstrates it
  cleanly is part of the point, not just a nice-to-have.
- `ruff` for lint + format, `mypy` for type checking — pin both in `requirements*.txt`/
  `pyproject.toml`, run them as part of the Test step in `ai-interaction.md`.
- Pydantic models for request/response schemas at the API boundary; SQLAlchemy models
  stay internal to the data layer, don't leak ORM objects out through FastAPI responses.
- One module per concern: importer, data models, CRM read/write logic, handoff-assistant
  roles (preparer/checker/coordinator) — don't collapse the assistant's three roles into
  one function; the separation is the thing being evaluated (ADR 0004).

## Database (SQLAlchemy + Alembic)

- Every migration goes through Alembic — no hand-edited schema, no `create_all()` in
  application code.
- Indexes are a deliberate decision, not an ORM default: `company_code`, `contact_code`,
  `fair_edition_code`, opportunity status/dates, `activity_log.follow_up_on` per ADR
  0002. Add an index when you add a query that filters/sorts on a new column, not
  speculatively.
- Watch for N+1s on any list/search endpoint — spot-check the generated SQL (`echo=True`
  or a query log) on the CRM search flows specifically, since 100k-row practicality is a
  graded requirement, not an aspiration.
- The importer must be idempotent against a full `reset.sh` + `dev.sh` replay against a
  replaced `data/` folder — no hardcoded assumptions from this session's specific CSVs.

## The handoff assistant

- The deterministic stand-in for model responses must be **visibly labeled as
  simulated** wherever its output surfaces (UI and persisted run record) — the
  assignment requires this explicitly, and it's an easy thing to forget once the code
  is working and looks real.
- Every run persists: the inputs used, each role's output, and the coordinator's reason
  string — not just the final continue/stop verdict.
- No agent framework, no real model calls, no API keys — plain functions/classes only
  (ADR 0004). Don't reach for LangChain even if it would be faster; it directly
  contradicts the brief.

## Frontend (React + shadcn/ui)

- TypeScript, function components, hooks — no class components.
- Talks to the backend only over the REST API; no direct DB access from the frontend
  service.
- Pencil/Stitch-drafted components get adjusted for consistency and wired to live data
  before being considered done — a draft that still shows placeholder data isn't
  finished (ADR 0003).
- Three required flows only (find exhibitor/contacts + opportunities/editions; update an
  opportunity + record a conversation; schedule/find a follow-up) — don't build screens
  the brief doesn't ask for.

## Docker / general

- Every image pinned to a specific tag (`postgres:17.6-alpine3.22` is already the
  pattern in `compose.yml` — match that precision elsewhere).
- No `latest`, no unpinned base images, per `docs/image-policy.md`.
- Nothing in `compose.yml` may depend on an external service, credential, or paid
  account once the app is started (`docs/environment.md`) — this rules out real
  Sentry, real LLM API calls, or anything else that needs a network credential at
  runtime.
