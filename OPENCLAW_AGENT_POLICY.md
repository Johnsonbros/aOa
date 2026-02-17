# OpenClaw Agent Tailoring Policy for aOa

This policy defines the **minimum required behavior** for running aOa as the context-optimization layer for an OpenClaw agent.

## 1) Scope

This policy applies to all integrations where an OpenClaw agent uses aOa for:

- symbol search,
- context prediction/injection,
- ranking and learning feedback,
- token savings telemetry.

## 2) Non-Negotiable Rules

1. **Predict before search**
   - Every agent turn MUST call prediction (`/predict`) before any broad search/read loop.
   - If prediction confidence is acceptable, use predicted files first.

2. **Budgeted context only**
   - Context injection MUST be clipped to a strict token budget before model invocation.
   - Context packets MUST include provenance metadata (`reason`, `confidence`, `source`).

3. **Outcome attribution required**
   - Each prediction batch MUST be logged and finalized as hit/miss (`/predict/log`, `/predict/check`, `/predict/finalize`).
   - Final outcomes MUST be fed into tuner feedback (`/tuner/feedback`).

4. **Tenant isolation by key**
   - Ranking/memory keys MUST be partitioned by: `user + workspace + channel + agent_profile`.
   - Cross-project content reuse is forbidden except global structural priors.

## 3) Runtime Modes

Implement and expose the following operating modes:

- **passive**: observe and learn only; no automatic injection unless confidence is high.
- **assist**: inject only conservative, high-confidence bundles.
- **aggressive**: inject by default with guardrails and continuous tuning.

Mode promotion/demotion MUST be based on rolling hit-rate and token ROI.

## 4) Budget Profiles

All requests MUST declare one profile:

- **micro**: 1–2 files/snippets; strict confidence floor.
- **standard**: 3–5 files/snippets; moderate confidence floor.
- **deep**: extended bundle with strict provenance and traceability.

Selection algorithm:

1. Query `/predict`.
2. Filter by confidence floor.
3. Pack to token budget.
4. Attach provenance metadata.

## 5) Required Endpoint Contract

At minimum, the OpenClaw adapter MUST call these aOa routes:

- `/symbol`, `/multi`, `/pattern`
- `/rank/record`, `/rank/stats`
- `/predict`, `/predict/log`, `/predict/check`, `/predict/finalize`, `/predict/stats`
- `/tuner/feedback`, `/tuner/best`, `/tuner/weights`
- `/metrics/tokens`
- `/context` and/or `/memory`

## 6) Failure and Fallback Policy

If `/predict` fails, times out, or returns low-confidence results:

1. Record fallback reason in telemetry.
2. Use bounded fallback search (never unbounded loops).
3. Continue attribution for all fallback reads.
4. Trigger health alerts when error/timeout thresholds are exceeded.

Default integration timeout targets:

- prediction path p95 ≤ 250ms
- context assembly p95 ≤ 150ms

## 7) Security and Trust Boundaries

- OpenClaw↔aOa traffic MUST be authenticated.
- Adapter credentials MUST be rotated periodically.
- Data exchanged MUST be minimal and purpose-limited.
- Logs MUST avoid raw secret leakage.

## 8) Data Lifecycle

- Interaction telemetry MUST define retention/TTL policy.
- Tenant-scoped delete MUST support user/workspace erasure.
- Daily aggregates MAY be retained longer than raw events.

## 9) KPI Gates for Rollout

Progression gates:

1. **Shadow → Safe**
   - measurable token-savings opportunity with acceptable latency overhead.
2. **Safe → Adaptive**
   - stable Hit@K and acceptance-rate improvements.
3. **Adaptive → Autonomous**
   - sustained ROI and bounded false-positive context injection.

Track at minimum:

- Hit@1/3/5
- context acceptance rate
- token savings per interaction/day
- search-call reduction ratio
- confidence calibration error
- enrichment latency overhead

## 10) Compliance Checklist

A deployment is compliant only if all are true:

- [ ] predict-before-search is enforced by middleware/tests.
- [ ] budget profile is required on every agent turn.
- [ ] prediction windows are logged, checked, and finalized.
- [ ] tuner feedback loop is active.
- [ ] tenant isolation keys include user/workspace/channel/profile.
- [ ] fallback behavior is bounded and observable.
- [ ] KPI dashboard exposes required metrics.

## 11) Definition of Done

OpenClaw-tailored operation is considered complete when:

- agents reliably use predicted context before broad search,
- context stays within budget automatically,
- feedback continuously improves ranking confidence,
- KPI trends show sustained token and tool-call reduction,
- no cross-project context leaks are observed.
