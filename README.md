# Exhibition sales CRM

A CRM for a company that designs and builds exhibition stands: find an exhibitor or contact and see their opportunities and fair editions, update an opportunity and record a conversation, and schedule or find a follow-up. It also includes a handoff assistant that prepares and checks a brief for the technical team before an opportunity is passed over. See [the assignment](ASSIGNMENT.md) for the full brief.

Run `./dev.sh` to build and start everything via Docker Compose; the app is then at `http://localhost:3000`. `docker compose down` stops it, keeping data. `./reset.sh` stops and wipes the project's data — the next start re-imports the archive in `data/` (its [README](data/README.md) describes the files and field formats). `./verify.sh` checks the Compose config and that the app responds on port 3000. Run `./test.sh` to run the backend test suite against a throwaway, containerized database — no host Python or database required.

## Submission notes

### Stack and versions

| Layer | Choice | Version |
|---|---|---|
| Backend | Python / FastAPI | 3.13.7 / 0.121.2 |
| ORM / migrations | SQLAlchemy / Alembic | 2.0.44 / 1.17.1 |
| DB driver | psycopg | 3.2.12 |
| Backend package manager | uv | 0.12.13 |
| Database | PostgreSQL (`postgres:17.6-alpine3.22`) | 17.6 |
| Frontend | React / TypeScript | 19.3.0 / 7.0.2 |
| Build tool | Vite | 8.3.0 |
| UI | shadcn/ui (Radix primitives) + Tailwind CSS | Tailwind 4.3.3 |
| Frontend runtime image | `nginx:1.29.3-alpine3.22` | 1.29.3 |

Lint/type-check: `ruff` 0.14.4 + `mypy` 1.19.0 (strict) on the backend, `tsc` on the frontend. Backend tests: `pytest` 8.4.2 (34 tests, run with `./test.sh`). All images pinned to exact tags; dependencies locked (`uv.lock`, `package-lock.json`) — see `docs/image-policy.md`. Rationale for each stack choice is in `docs/adr/0001`–`0004`.

### Time spent

`~7 hours 30 minutes` — roughly 6–7 hours building, plus about an hour of planning and tooling setup before the first commit.

### Import decisions (see `backend/app/importer.py`, `data/README.md`, ADR-0002)

- Empty CSV fields import as `NULL`/`None`, never a zero, `false`, or placeholder string — an unknown budget/area/height must never read as a real zero-value answer.
- Monetary/area/height values use a decimal comma in the source (`12500,00`); parsed by substituting a decimal point, not rounded or re-scaled.
- Dates (`DD/MM/YYYY`) and date-times (`DD/MM/YYYY HH:mm`) are parsed, with date-times interpreted as `Europe/Rome` and stored timezone-aware, so "today" and follow-up due dates don't depend on the server's local timezone.
- `legacy_status` is trimmed and lowercased on import, so `Open` / ` open ` / `OPEN` collapse to one canonical value instead of splitting status filters across near-duplicate strings.
- `legacy_print_layout` (obsolete presentation metadata from the old system) is dropped — no commercial value, not part of the schema.
- A `requested_height_m` that exceeds its fair edition's `max_stand_height_m` is imported unchanged, never clamped or rejected — the conflict must stay visible to the sales/technical teams and to the handoff assistant, not be silently discarded.
- The importer upserts by each entity's legacy code (`company_code`, `contact_code`, `opportunity_code`, `entry_id`, `fair_edition_code`) via `ON CONFLICT DO NOTHING`, so re-running against the same or a replaced `data/` folder never duplicates rows — and, importantly, never overwrites values the app itself has since written (an edited opportunity, a completed follow-up, a new handoff run) on a plain restart. A full `reset.sh` only ever re-seeds an empty database, where every row is a fresh insert regardless.
- Startup skips the ~75k-row walk entirely when `data/manifest.json`'s sha256 fingerprint matches the one recorded from the last import (`import_state` table), so a plain `docker compose down` + `./dev.sh` restart serves requests in seconds instead of minutes. This is an optimisation, not the correctness guarantee — `import_archive` itself stays idempotent regardless — so a missing/replaced manifest just means the next start re-imports, never that data could be duplicated or lost.
- Company/contact **name** search is backed by `pg_trgm` GIN indexes, confirmed index-backed via `EXPLAIN ANALYZE` (see known gaps below for the code-search caveat).

### How the team's competing requests were handled

- **"Last year's agreement isn't this year's."** An opportunity's conversation/activity view defaults to that opportunity (and so that fair edition) only; a company's full cross-edition history is one click away (the "Full company history" tab on a company page), for the account-manager need to see everything about an exhibitor in one place.
- **When to hand off to technical.** Implemented as a hybrid staged policy (ADR-0004), not a single all-or-nothing gate: an early **heads-up** is available the moment the fair edition and the *client-stated* budget (`client_budget_eur` — not the sales team's own `amount_eur` estimate) are known, matching the sales director's "as soon as a fair and a budget are named." A **continue** verdict is withheld until stand area *and* requested height are both known and the height has been checked against the fair edition's `max_stand_height_m`, matching the technical coordinator's "don't start work we can't deliver." Every "stop" names the specific missing field or the height-vs-limit conflict, never just "incomplete."

### Trying the handoff assistant

The assistant is a deterministic, rule-based stand-in for a model response — no API keys, no external calls — labeled `simulated: true` everywhere it surfaces (a "simulated" badge per role and per run in the UI, and a `simulated` column on the persisted `HandoffRun`). Three roles run in sequence in one process: the **preparer** gathers the CRM and fair-edition snapshot and proposes a next step; the **checker** validates that proposal against the handoff policy and records which proposal it checked; the **coordinator** decides continue/stop and states the reason. Every run persists the snapshot it was evaluated against, both role outputs and the coordinator's reason, and the run history on screen shows all three — so an old run still reads against the brief as it stood at the time, not as it stands now.

`backend/evals/handoff_examples.md` is a committed log of the four policy branches (complete brief → continue; missing height → stop; height over the edition's limit → stop; heads-up-only, i.e. budget known but area/height still missing → stop with heads-up) — generated by actually running the pipeline (`backend/evals/generate_handoff_examples.py`), so it can't drift from the code.

To try it live:

1. `./dev.sh`, then open http://localhost:3000 and search for a company (e.g. "Aster Cosmetics").
2. Open an opportunity and click **Run handoff assistant** in the "Handoff assistant" panel.
   - **Complete enquiry** — e.g. opportunity `OP000001` (Aster Cosmetics, Beauty Trade Forum): stand area, requested height, and client budget are all known and the height is within the edition's limit → verdict `continue`.
   - **Incomplete enquiry** — e.g. opportunity `OP000043` (Moruma Cosmetics): client budget is known but requested height is missing → verdict `stop`, heads-up `true`, reason names "requested height."
3. Edit the opportunity's brief (the "Update opportunity" form above the assistant) and re-run — a new run is appended, not overwritten; the full run history stays visible, most recent first, each entry showing the inputs it was judged on.

(The codes above are from the archive as supplied; if the replacement `data/` folder differs, search for any opportunity, use the "Update opportunity" form to clear or fill in stand area / requested height / client budget, and re-run to reproduce either case — or read the committed evals log for a data-independent demonstration of all four branches.)

### Verified

Checked against the exact command sequence in the assignment, on the archive as supplied:

| Step | Result |
|---|---|
| `./reset.sh` then `./dev.sh` (cold, empty database) | API serving in 46s; record counts 10,000 / 20,000 / 15,000 / 40,000 exactly match `data/manifest.json` |
| `./verify.sh` | Compose config valid, app reachable on port 3000 |
| `docker compose down` then `./dev.sh` | API serving in 4s (import skipped, logged as such); counts unchanged, no duplicates; an edited opportunity and a saved handoff run both survived |
| `./test.sh` | 34 passed |
| `ruff check` / `ruff format --check` / `mypy --strict` / `tsc --noEmit` | clean |

### Unfinished / known gaps

- No automated tests for the CRUD/search/follow-up screens. Test-first work was deliberately reserved for the importer and the handoff assistant's role logic — the two places where correctness is load-bearing — and that is where the 34 backend tests sit. The screens were verified by hand against the running app instead.
- Opportunity `status` is a normalized string sourced from the legacy data (trimmed/lowercased, like the importer), not a hard-enforced enum at the API boundary — the UI constrains the field to whatever vocabulary is actually present in the data, but a direct API call could in principle write an arbitrary value. Left this way deliberately: the CRM is single-user/trusted per the assignment's scope, and "no invented fields outside the legacy vocabulary" reads as "don't force new required fields," not "validate free text against a fixed enum."
- No auth/permissions/multi-user support, no floor plans/3D models/quotations/BOM, no automatic emails — all explicitly out of scope per `ASSIGNMENT.md`.
- `company_code`/`contact_code` search uses `ILIKE` (case-insensitive) against a plain btree index, which Postgres can't use for that operator — confirmed via `EXPLAIN ANALYZE` (`enable_seqscan = off` still falls back to a seq scan). Each match condition (company name, company code, contact code, contact name) now runs as its own `UNION ALL` branch specifically so this doesn't drag the *indexed* branches down with it — combining code and name in one `WHERE ... OR ...` was confirmed (via `EXPLAIN ANALYZE`) to force a full sequential scan even for the name-only case, since Postgres won't use an index for one side of an `OR` when the other side isn't indexable. With the branches split, company-name and contact-name search are confirmed index-backed (`Bitmap Index Scan` on the `pg_trgm` indexes) independent of the two code branches, which still sequentially scan (~3–7ms each at today's 10k/20k rows). Not fixed further here: the real fix for the code branches is a case-insensitive-friendly index (e.g. a functional index on `lower(company_code)`) via a new migration — out of scope for this pass since exact-code lookups are the less common search path and the current cost is small at this archive size.
