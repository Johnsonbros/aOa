# OpenClaw-First Fork Guide for aOa

This guide explains how to create a dedicated fork of `aOa` for exclusive OpenClaw agent usage, with an emphasis on reducing token waste and maximizing reusable context.

## Goal

Build a fork (for example `aoa-openclaw`) that keeps aOa's core ranking/prediction engine but changes runtime defaults so OpenClaw agents:

- always attempt prediction before expensive search/read loops,
- reuse session-aware context packets,
- enforce strict token budgets per channel/profile,
- continuously learn from prediction outcomes in the background.

## 1) Create and Bootstrap the Fork

1. Fork `CTGS-Innovations/aOa` into your org/user (for example `openclaw/aoa-openclaw`).
2. Clone your fork and set remotes:

```bash
git clone git@github.com:openclaw/aoa-openclaw.git
cd aoa-openclaw
git remote add upstream git@github.com:CTGS-Innovations/aOa.git
git fetch upstream
```

3. Create long-lived integration branch:

```bash
git checkout -b openclaw/main
```

## 2) Define the “OpenClaw-Only” Product Contract

Document this as non-negotiable behavior in your fork:

- **Predict-before-search**: agent orchestration must call `aoa.predict` + `aoa.symbol_search` first.
- **Budgeted context injection**: context bundles are clipped to target token budget before model invocation.
- **Partitioned memory**: all ranking/memory keys partitioned by `user + workspace + channel + agent-profile`.
- **Outcome feedback required**: every prediction batch must be finalized as hit/miss and fed back to tuner.

## 3) Add OpenClaw Runtime Adapter Layer

Introduce an adapter package (suggested path `integrations/openclaw/`) that exposes stable operations:

- `predict_context(request)`
- `record_access(event)`
- `finalize_prediction(window)`
- `token_savings_metrics(scope)`

Keep it thin: adapter should orchestrate existing aOa endpoints/components, not duplicate ranking logic.

## 4) Enforce Budget Profiles to Prevent Token Burn

Create a simple policy table used before each LLM call:

- **micro** (chat/DM): top 1–2 files/snippets, strict confidence floor.
- **standard** (web/CLI): top 3–5 files.
- **deep** (explicit analysis mode): larger pack with provenance metadata.

Required policy behavior:

1. Request predictions.
2. Drop low-confidence results.
3. Pack results to budget.
4. Attach “why selected” metadata.

## 5) Add Continuous Background Optimization

Run a worker (service or scheduled job) that:

- replays accesses into ranking,
- finalizes stale prediction windows,
- updates tuner feedback,
- snapshots best weights,
- emits daily/weekly token-savings reports.

This is what makes OpenClaw agents improve over time without repeatedly rediscovering context.

## 6) Prevent Cross-Project Context Pollution

Implement strict namespace keys, for example:

```text
aoa:{user}:{workspace}:{channel}:{agent_profile}:{signal}
```

Only allow global fallback priors for safe structural heuristics (never project-private content).

## 7) Operational Rollout Strategy

Use a staged deployment path:

1. **Shadow mode**: predict only; do not inject.
2. **Safe mode**: inject only high-confidence micro bundles.
3. **Adaptive mode**: enable tuner-driven budgets.
4. **Autonomous mode**: continuous optimization with guardrails.

Gate promotions by KPI thresholds (Hit@K, acceptance rate, savings/latency ratio).

## 8) KPIs That Prove You’re Saving Tokens

Track these per workspace/channel/profile:

- Hit@1/3/5
- context acceptance rate
- grep/read tool-call reduction ratio
- token savings per interaction and per day
- enrichment latency overhead
- confidence calibration error

If these are not trending in the right direction, reduce injection aggressiveness and tighten confidence floors.

## 9) Repo Governance for Long-Term Maintainability

For clean upstream syncs:

- Keep OpenClaw-specific code isolated under `integrations/openclaw/` and policy config files.
- Avoid invasive rewrites of ranking core unless necessary.
- Merge `upstream/main` regularly and resolve integration drift quickly.
- Add CI checks that fail if predict-before-search middleware is bypassed.

## 10) Suggested 1-Week Execution Plan

- **Day 1–2**: create adapter + policy config + namespace keying.
- **Day 3**: wire prediction attribution (log/check/finalize).
- **Day 4**: implement background optimizer worker.
- **Day 5**: ship shadow mode and baseline metrics.
- **Day 6–7**: enable safe injection for a small cohort and evaluate KPIs.

---

## Minimal Definition of Done

Your OpenClaw-tailored fork is successful when:

- agents consistently use predict-before-search,
- context injection stays within budget automatically,
- hit/miss attribution continuously updates ranking/tuner,
- daily reports show sustained tool-call and token reduction,
- no cross-project context leaks are observed.
