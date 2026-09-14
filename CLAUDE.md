# Exhibition sales CRM

Take-home assignment for an AI Engineer role. Solo, 48-hour window. Full brief:
[ASSIGNMENT.md](ASSIGNMENT.md) — read it before anything else; it overrides everything
below if they ever conflict.

## Context files

Always loaded:

- @context/ai-interaction.md — workflow, bug-fix loop, and which vendored skill applies
  where
- @context/coding-standards.md — stack conventions (Python/FastAPI/SQLAlchemy/React)

Read on demand, not included by default (keep this file's context budget small):

- [docs/adr/](docs/adr/) — the actual design decisions and why (backend/DB/frontend
  stack, handoff-assistant orchestration approach)
- [data/README.md](data/README.md) — the CSV export's field reference

## Commands

- `./dev.sh` — build and start everything via Docker Compose; app at
  `http://localhost:3000`
- `./reset.sh` — stop and wipe this project's data; next start re-imports the archive
- `./verify.sh` — check Compose config + HTTP reachability
- `docker compose down` — stop, keep data

## Protected — never edit

`ASSIGNMENT.md`, `verify.sh`, `data/`, `docs/environment.md`, `docs/image-policy.md` —
these get replaced with originals before review.
