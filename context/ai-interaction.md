# AI Interaction Guidelines

Ported from a working project's proven workflow, trimmed for a solo 48-hour submission
(no team, no branch protection, no shared integration branch).

## Communication

- Be concise and direct
- Explain non-obvious decisions briefly
- Ask before large refactors or architectural changes
- Don't add features not in `ASSIGNMENT.md`
- Never delete files without clarification

## Workflow

Common workflow for every feature/fix:

1. **Document** — if it's a real architectural decision, write an ADR in `docs/adr/`.
   For anything smaller, skip straight to implementing.
2. **Branch** — new branch per feature/fix.
3. **Implement** — build the feature/fix. See the skill map below for which parts get
   `/tdd`.
4. **Test** — verify it works (manually where there's no test yet). Run type-check/lint
   and fix errors.
5. **Iterate** — adjust as needed.
6. **Commit** — only after it works. Small, frequent commits with real messages — this
   repo's development history is part of what gets reviewed.
7. **Merge** — merge to `main`. Solo repo, no PR/approval gate.
8. **Delete branch** after merge.
9. **Review** — `/code-review` before submission (see skill map).

Do NOT commit without confirming it actually works. If something's broken, fix it first.

## Bug Fixes

**Diagnose → plan → ask → fix.** This is what `/diagnosing-bugs` does — invoke it
directly for anything beyond a one-line fix.

- **Diagnose** — confirm the root cause in the actual code before proposing anything.
  Cite the exact file/line; don't guess.
- **Plan** — write up the root cause and the proposed fix (what changes, why, what's
  explicitly out of scope).
- **Ask** — get explicit go-ahead before writing code.
- **Fix** — implement, then verify per the Test step above.

## Branching

New branch per feature/fix: `feature/[name]` or `fix/[name]`. Solo repo — no PR
approval gate, just merge to `main` when it's verified working.

## Commits

- Ask before committing (don't auto-commit)
- Conventional commit messages (`feat:`, `fix:`, `chore:`)
- One feature/fix per commit — keep the history real, not one end-of-process dump
- Concise subject line; a short body is fine when it explains a non-obvious "why"

## When Stuck

- If something isn't working after 2-3 attempts, stop and explain the issue —
  `/diagnosing-bugs` if it's a genuine bug, not just re-guessing
- Ask for clarification if `ASSIGNMENT.md` is ambiguous rather than assuming

## Code Changes

- Make minimal changes to accomplish the task
- Don't refactor unrelated code unless asked
- Don't add "nice to have" features — this assignment is explicitly graded on reasoning
  and working core flows, not scope
- Preserve existing patterns in the codebase

## Code Review

`/code-review` before submission, especially for:

- Security (the assignment assumes one user, but don't leave obvious holes)
- Performance (the archive must stay practical at 100,000 contacts — check for anything
  that won't scale, like an unindexed search)
- Logic errors (edge cases in the messy CSV data, the handoff policy's branches)
- Patterns (matches the rest of the codebase?)

## Skill map — which vendored skill, which moment

Only the skills that actually recur while building this. Everything else vendored in
`.claude/skills/` was either already used during planning (`grilling`, `domain-modeling`)
or doesn't apply to a solo repo (`resolving-merge-conflicts`, the issue-tracker/triage
setup) — don't reach for those here.

| Step / moment | Skill | Why this one, here |
|---|---|---|
| Implement — the CSV importer, and the handoff-assistant's preparer/checker/coordinator roles | `/tdd` | The two places correctness is actually graded: the importer must survive a full data reset, and the coordinator's continue/stop branching needs to be provably right, not just look right once. |
| Implement — CRUD screens, plumbing, everything else | *(none)* | Don't force test-first on low-stakes glue code. |
| Any bug beyond a one-line fix | `/diagnosing-bugs` | Is the diagnose→plan→ask→fix loop above, formalized. |
| Before finalizing the CRM ↔ handoff-assistant module boundary | `/codebase-design` | The seam between "ordinary CRM" and "the assistant" is a real design decision worth getting right once. |
| Before submission | `/code-review` | Last pass, against the checklist above. |
