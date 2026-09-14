# ADR 0003: Frontend framework and UI drafting workflow — React + shadcn/ui, Pencil/Stitch for drafting

Status: Accepted
Date: 2026-09-14

## Context

Frontend is the candidate's strongest area, and the JD lists "React or similar" as basic must-have web development. The backend was already fixed to Python/FastAPI + SQLAlchemy (ADR 0001, ADR 0002), which rules out a single-process full-stack JS framework sharing an ORM with the backend. Separately, the candidate wants to draft shadcn-style pages/components using the Pencil MCP (Pen.dev — a multi-agent UI designer available as an MCP server in this environment) to reach a UI draft quickly, with Google Stitch AI plus a manual consistency pass as a fallback if Pencil's token usage becomes a constraint.

## Decision

React frontend using shadcn/ui components, built as a separate service from the FastAPI backend and calling it over REST. UI drafting is done at build time via the Pencil MCP (or Stitch AI as fallback), used only as a development-time tool — the shipped containers make no calls to either service at runtime.

## Alternatives considered

- **Merge frontend into a Next.js app talking directly to the DB** (e.g. via Prisma) — moot once the backend was fixed to Python/SQLAlchemy in ADR 0001/0002; a JS-based ORM colocated with a separate Python API doesn't apply.
- **Hand-build every screen from scratch** — rejected in favor of drafting via Pencil/Stitch to reach a working UI faster, then adjusting for visual consistency and wiring to live data, given the same-day MVP target.

## Consequences

Backend, data model, and handoff-policy logic are built first, with UI generation happening second against already-known data shapes (see the project's build-sequencing decision) — this makes UI rework the cheaper failure mode if any data-shape assumption turns out wrong, rather than the reverse. Pencil/Stitch usage must stay confined to development time; nothing in `compose.yml` may depend on either service, consistent with `docs/environment.md`'s requirement that the running app needs no external services once started.
