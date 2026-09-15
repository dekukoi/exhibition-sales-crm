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
- **A contact is entered once, not once per fair.** Contacts belong to the company, and an opportunity references an existing one — so a returning exhibitor's people are already there for the next edition, and nothing is re-keyed per fair.
- **When to hand off to technical.** Implemented as a hybrid staged policy (ADR-0004), not a single all-or-nothing gate: an early **heads-up** is available the moment the fair edition and the *client-stated* budget (`client_budget_eur` — not the sales team's own `amount_eur` estimate) are known, matching the sales director's "as soon as a fair and a budget are named." A **continue** verdict is withheld until stand area *and* requested height are both known and the height has been checked against the fair edition's `max_stand_height_m`, matching the technical coordinator's "don't start work we can't deliver." Every "stop" names the specific missing field or the height-vs-limit conflict, never just "incomplete."

### Trying the handoff assistant

A deterministic, rule-based stand-in for a model response — no API keys, no external calls — labeled `simulated` wherever it surfaces (a badge per role and per run in the UI, a `simulated` column on the persisted run). Three roles run in sequence in one process: the **preparer** gathers the CRM and fair-edition snapshot and proposes a next step; the **checker** validates that proposal against the policy; the **coordinator** decides continue/stop and states why. Each run persists the snapshot it was judged on, both role outputs and the reason, and the run history shows all three — so an old run still reads against the brief as it stood then.

To try it live: `./dev.sh`, open http://localhost:3000, search a company, select an opportunity, then click **Run handoff assistant**.

| | Opportunity | Why | Outcome |
|---|---|---|---|
| **Complete enquiry** | `OP000001` (Aster Cosmetics, Beauty Trade Forum) | area, height and client budget all known; height within the edition's limit | `continue` |
| **Incomplete enquiry** | `OP000043` (Moruma Cosmetics) | client budget known, requested height missing | `stop`, heads-up `true`, reason names "requested height" |

Editing the brief and re-running appends a new run rather than overwriting — the history stays, most recent first, each entry showing the inputs it was judged on.

Those codes come from the archive as supplied. If the replacement `data/` differs, take any opportunity and use the update form to clear or fill stand area / requested height / client budget to reproduce either case. `backend/evals/handoff_examples.md` is a data-independent alternative: a committed log of all four policy branches (complete → continue; missing height → stop; height over the limit → stop; budget known but area/height missing → stop with heads-up), generated by running the pipeline itself (`backend/evals/generate_handoff_examples.py`) so it can't drift from the code.

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

- **No automated tests for the CRUD/search/follow-up screens.** Test-first work was deliberately reserved for the importer and the assistant's role logic — the two places correctness is load-bearing — which is where the 34 backend tests sit. The screens were verified by hand against the running app.
- **Opportunity `status` isn't a hard enum at the API boundary.** It's a normalized string from the legacy vocabulary (trimmed/lowercased, as on import), and the UI only offers values actually present in the data, but a direct API call could write something else. Deliberate: the archive's own status vocabulary is what's authoritative, and the brief scopes this to one trusted user.
- **Code search isn't index-backed.** `company_code`/`contact_code` use case-insensitive `ILIKE`, which Postgres won't serve from their btree indexes. Each match condition is its own `UNION ALL` branch precisely so this doesn't spread: combined under one `OR`, the whole query degrades to a sequential scan even for the name-only case. Split, company-name and contact-name search stay on their `pg_trgm` GIN indexes (confirmed by `EXPLAIN ANALYZE`) while the two code branches scan at ~3–7 ms on this archive. The real fix is a functional index on `lower(company_code)`; left out as exact-code lookup is the rarer path and the current cost is small.
- **Out of scope per the brief:** no auth/permissions/multi-user, no floor plans, 3D models, quotations or bills of materials, no automatic emails.
