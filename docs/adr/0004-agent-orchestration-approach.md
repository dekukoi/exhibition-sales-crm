# ADR 0004: Handoff-assistant orchestration — plain functions, deterministic stand-in, no agent framework

Status: Accepted
Date: 2026-09-14

## Context

The assignment requires a small orchestration on an opportunity: one role prepares a handoff brief, another checks it, and a coordinator decides whether to continue or stop — "ordinary functions in one process are fine," using "a deterministic local stand-in for model responses" and explicitly **"No API keys, external model calls or model downloads."** It further states "a chat interface, agent framework and automatic emails aren't needed." Separately, the target JD lists agent frameworks (LangChain, LlamaIndex, Google ADK) and MCP as nice-to-have, not must-have, and separately emphasizes "evaluate agent behaviour, find where it breaks, fix it" as core day-to-day work.

## Decision

Implement the preparer, checker, and coordinator as plain Python functions/classes in one process, backed by a deterministic, clearly-labeled stand-in for model responses. The coordinator's continue/stop decision (and its stated reason) is driven by the project's hybrid staged handoff policy: an early "heads-up" is available as soon as fair + budget are known, but the coordinator only returns "continue" once stand area and requested height are both present and the requested height has been checked against the fair edition's maximum; otherwise it returns "stop" with the specific missing field or the height-conflict as the reason.

## Alternatives considered

- **LangChain or another agent framework** — would demonstrate familiarity with a JD nice-to-have, but directly contradicts the assignment's explicit instruction that no agent framework is needed, and adds dependency weight against a same-day MVP deadline for a capability nothing in the brief requires.
- **A single "do everything" function** instead of three roles — simpler, but fails to demonstrate the role separation and an actual coordinator decision, which is the substantive thing being evaluated.

## Consequences

Because there is no real model in the loop, "evaluating agent behaviour" is demonstrated via a small committed evals log of example runs (complete brief → continue; missing height → stop with reason; requested height over the edition's limit → stop with reason) rather than live model-observability tooling — no Sentry-style tracing is needed for this piece specifically.
