# ADR 0001: Backend language and framework — Python + FastAPI

Status: Accepted
Date: 2026-09-14

## Context

The assignment lets us choose the whole stack, as long as it's Dockerized, cross-arch (`amd64`+`arm64`), pinned-version, and runs with no host dependency beyond Docker. The target role (AI Engineer, LLM/Agentic AI, at a company starting in the trade-fair/exhibitions vertical) lists **"Solid Python"** as a MUST-HAVE skill and "basic web development: React or similar, REST APIs" as the other must-have. TypeScript is mentioned only as something written "day to day," not as a must-have. The candidate's strongest prior backend experience is C#/.NET (clean architecture), with frontend as the strongest overall area; direct Python project experience is comfortable-to-read but less battle-tested to write. The build window is compressed to a same-day MVP target.

## Decision

Backend: Python 3.x with FastAPI, as a separate service from the React frontend, communicating over a REST API.

## Alternatives considered

- **Full TypeScript stack (Next.js, one process/language)** — would be the fastest to wire up solo given the candidate's frontend strength, and avoids a two-language context switch. Rejected because it would not demonstrate the JD's explicit must-have ("Solid Python"), which is the actual purpose of this assignment as a hiring signal.
- **.NET backend + React frontend** — plays to the candidate's deepest backend experience. Rejected because .NET does not appear anywhere in the JD and would signal a stack mismatch with the role.

## Consequences

Introduces a two-service architecture (Python API + React SPA) instead of one unified app, adding an API-contract layer and two separate Docker build stages in `compose.yml`. Accepted as the direct cost of demonstrating the must-have skill the assignment is meant to test for.
