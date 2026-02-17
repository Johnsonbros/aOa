# Deep Dive: Re-optimizing aOa for the OpenClaw Ecosystem

This document proposes how to integrate aOa into OpenClaw so an always-on assistant can continuously optimize context and token usage while preserving aOa’s current methods (intent capture, predictive ranking, and semantic compression).

## 1) Current aOa Strengths to Preserve (Do Not Rewrite)

aOa already has the right core loop:

1. **Capture behavior** from tool usage via hooks (`PostToolUse`, `UserPromptSubmit`).
2. **Infer semantic intent tags** from files, commands, and patterns.
3. **Score files** using recency/frequency/tag affinity.
4. **Predict and inject context** before the model spends tokens searching.
5. **Track prediction hit/miss** and tune weights over time.

Keep these methods intact and make OpenClaw a new runtime surface around them.

## 2) Why OpenClaw Is a Good Host

OpenClaw is designed as an always-on gateway + assistant control plane with long-lived runtime, channels, and skills. That environment is ideal for aOa because:

- aOa benefits from continuous session memory and telemetry accumulation.
- OpenClaw already supports long-running assistant workflows and routing.
- The assistant can execute optimization cycles in the background (24/7) without user friction.

## 3) Mapping aOa Components to OpenClaw Architecture

### aOa components today

- **Gateway** (`services/gateway/gateway.py`) routes requests for index/status/ranking APIs.
- **Intent capture hook** (`services/hooks/intent-capture.py`) records file/tool interactions and tags.
- **Predictive context hook** (`services/hooks/predict-context.py`) injects likely files/snippets.
- **Scorer/tuner** (`services/ranking/scorer.py`) computes rank/confidence and supports Thompson-sampling style weight exploration.

### OpenClaw integration targets

- **Gateway extension:** expose aOa endpoints through OpenClaw tool interfaces.
- **Skill wrapper:** package aOa operations as an OpenClaw skill so agent calls become first-class actions.
- **Background optimizer worker:** run periodic ranking/tuning jobs independent of active chat.
- **Per-channel/session policy layer:** apply different context budgets by channel (e.g., WhatsApp vs WebChat).

## 4) Integration Blueprint (Recommended)

## 4.1 Build an `aoa-bridge` OpenClaw Skill

Create a skill that wraps aOa HTTP endpoints:

- `aoa.symbol_search(query, mode)` → `/symbol`, `/multi`, `/pattern`
- `aoa.record_access(file, tags, source)` → `/rank/record`
- `aoa.predict(keywords, limit, snippet_lines)` → `/predict`
- `aoa.context.get(session, budget)` → `/context` or `/memory`
- `aoa.metrics.tokens()` → `/metrics/tokens`

**Design rule:** OpenClaw agent never calls raw grep/read loops until `aoa.predict` and `aoa.symbol_search` are attempted first.

## 4.2 Introduce a 24/7 Optimization Daemon

Run a persistent worker (inside OpenClaw gateway runtime or sidecar) that:

- Consumes interaction logs/events continuously.
- Replays access events to `rank/record`.
- Finalizes prediction windows (`/predict/finalize`) on inactivity thresholds.
- Periodically runs tuner feedback cycles (`/tuner/feedback`) and snapshots best weights (`/tuner/best`).
- Writes daily token-savings reports for observability.

This keeps optimization alive even when no one is actively in a coding session.

## 4.3 Add Budget-Aware Context Injection

Define budget tiers before every model invocation:

- **Micro budget** (chat channels): only top 1–2 files or short snippets.
- **Standard budget** (CLI/web): top 3–5 files with confidence threshold.
- **Deep budget** (explicit “analyze deeply”): larger context with traceability.

Selection policy:

1. Query `aoa.predict`.
2. Filter by confidence floor.
3. Truncate by token budget.
4. Include provenance metadata (`why this file`, confidence, last-hit).

## 4.4 Close the Loop with Outcome Attribution

For each prediction batch:

- Log predicted files (`/predict/log`).
- Track whether agent actually read/used them (`/predict/check`).
- Finalize hit-rate window (`/predict/finalize`).
- Feed outcome into tuner (`/tuner/feedback`).

This preserves aOa’s existing adaptive-learning behavior, now upgraded to OpenClaw’s continuous runtime.

## 5) Data Model and Isolation Strategy

To fit OpenClaw’s multi-channel architecture while avoiding cross-pollution:

- Partition by **user + workspace/project + channel + agent profile**.
- Maintain separate ranking keys per partition with optional global fallbacks.
- Keep a global “cold-start prior” model only for structural heuristics, not raw private content.

Recommended key shape (conceptual):

`aoa:{user}:{workspace}:{channel}:{signal}:{...}`

## 6) 24/7 Runtime Modes

Implement three operating modes:

1. **Passive mode**
   - Observe and learn only.
   - No context injection unless confidence is high.

2. **Assist mode**
   - Inject low-risk high-confidence context.
   - Conservative budget.

3. **Aggressive optimization mode**
   - Inject ranked context by default.
   - Run periodic weight exploration and automated fallback checks.

Allow automatic promotion/demotion by rolling hit-rate and token ROI.

## 7) Token-Savings Strategy (Same Methods, Better Scheduling)

aOa methods stay the same; optimization improves by *when* they run:

- **Precompute candidate contexts** during idle windows.
- **Warm cache** top symbols/files per active workspace.
- **Debounce repeated user intent** so near-identical prompts reuse prior context packets.
- **Session continuity map**: carry forward last successful context bundle into next interaction.

Expected impact: lower first-token latency and fewer exploratory tool calls.

## 8) Observability You’ll Need in OpenClaw

Expose aOa-native KPIs in OpenClaw dashboards:

- Hit@K (K=1,3,5)
- Context acceptance rate (how often injected context was used)
- Token savings per interaction/session/day
- Search-call reduction ratio (baseline grep/read vs aOa-guided)
- Confidence calibration error (predicted confidence vs realized hit)
- Latency overhead from enrichment

## 9) Rollout Plan (Low Risk)

### Phase 0: Shadow mode
- OpenClaw calls aOa predict/rank, but does not inject context.
- Measure “would-have-saved” tokens.

### Phase 1: Safe injection
- Inject only when confidence exceeds strict threshold.
- Limit to tiny snippets and 1–2 files.

### Phase 2: Full adaptive mode
- Enable tuner feedback and dynamic budgets.
- Add per-channel policies.

### Phase 3: Autonomous optimizer
- Turn on scheduled background optimization and periodic reports.
- Auto-adjust mode based on ROI + false-positive rate.

## 10) Implementation Checklist

- [ ] Add OpenClaw skill package for aOa endpoints.
- [ ] Add middleware policy: `predict-before-search`.
- [ ] Add context budget manager (token-aware truncation).
- [ ] Add prediction attribution hooks in OpenClaw message/tool pipeline.
- [ ] Add partition-aware keying strategy.
- [ ] Add dashboard panels for aOa KPIs.
- [ ] Add background optimizer scheduler and health checks.

## 11) Key Risks and Mitigations

- **Risk:** Over-injection causes irrelevant context bloat.  
  **Mitigation:** confidence thresholds + strict per-channel budgets + hit-rate gating.

- **Risk:** Cross-project contamination.  
  **Mitigation:** hard namespace partitioning + explicit fallback rules.

- **Risk:** Optimization loop drifts after product changes.  
  **Mitigation:** rolling baseline tests + periodic weight reset endpoint (`/tuner/reset`).

## 12) Recommended First Sprint (Practical)

If you want immediate progress with low disruption:

1. Implement `aoa-bridge` skill with `symbol_search`, `predict`, and `record_access` only.
2. Add `predict-before-search` orchestration rule in OpenClaw agent flow.
3. Enable shadow metrics in production-like usage for 7 days.
4. Review savings/hit metrics and then enable safe injection.

This gives a fast path to value while preserving aOa’s proven optimization mechanics.
