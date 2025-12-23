# aOa Context Intelligence - Work Board

> **Updated**: 2025-12-23 | **Phase**: 1 - Redis Scoring Engine
> **Goal**: Transform aOa from search tool to predictive prefetch (90% accuracy)

---

## Confidence Legend

| Indicator | Meaning | Action |
|-----------|---------|--------|
| 🟢 | Confident - clear path, similar to existing code | Proceed freely |
| 🟡 | Uncertain - some unknowns, may need quick research | Try first, then research |
| 🔴 | Lost - significant unknowns, needs research first | Research before starting |

| Research | Agent | When to Use |
|----------|-------|-------------|
| 131 | 1-3-1 Pattern | Problem decomposition, understanding behavior |
| GH | Growth Hacker | Architecture decisions, best practices |
| - | None | Straightforward implementation |

---

## Active

| # | Task | Expected Output | Solution Pattern | Status | C | R |
|---|------|-----------------|------------------|--------|---|---|
| P2-001 | Implement confidence calculation | Score 0.0-1.0 per file | Normalize composite score | Ready | 🟡 | GH |

---

## Phase 1 - Redis Scoring Engine ✅ COMPLETE

**Success Criteria**: Files ranked by recency + frequency + tag affinity. `/rank` endpoint returns top 10.
**Result**: 6/6 rubrics pass, average latency 21ms

| # | Task | Expected Output | Solution Pattern | Status |
|---|------|-----------------|------------------|--------|
| P1-001 | Create ranking package | `/src/ranking/__init__.py`, `redis_client.py` | New directory, class wrapping redis-py | ✅ |
| P1-002 | Implement score operations | `zadd()`, `zincrby()`, `zrange()` wrappers | RedisClient class with sorted set methods | ✅ |
| P1-003 | Add recency scoring | Files scored by last-access time | Normalized exponential decay (1hr half-life) | ✅ |
| P1-004 | Add frequency scoring | Files scored by access count | `ZINCRBY frequency:files 1 <file>` | ✅ |
| P1-005 | Add tag affinity scoring | Files scored per tag | `ZADD tag:<tag> <score> <file>` | ✅ |
| P1-006 | Modify intent-capture.py | Write scores on every intent capture | POST to /rank/record on each file | ✅ |
| P1-007 | Implement composite scoring | Combined score from all signals | Weighted sum with normalization | ✅ |
| P1-008 | Add decay mechanism | Old scores fade over time | Exponential decay in scorer.py | ✅ |
| P1-009 | Add /rank endpoint | `GET /rank?tag=<tag>&limit=10` returns ranked files | New route in indexer.py | ✅ |
| P1-010 | Integration test | End-to-end: intent -> score -> rank | Benchmark rubrics (6/6 pass) | ✅ |

---

## Phase 2 - Predictive Prefetch (Week 2)

**Success Criteria**: PreHook outputs predicted files with confidence. `UserPromptSubmit` triggers predictions.

| # | Task | Expected Output | Solution Pattern | Deps | Status | C | R |
|---|------|-----------------|------------------|------|--------|---|---|
| P2-001 | Implement confidence calculation | Score 0.0-1.0 per file | Normalize composite score | P1-007 | Active | 🟡 | GH |
| P2-002 | Create /predict endpoint | `GET /predict?tags=X,Y` returns predictions | New route using scorer | P2-001 | Queued | 🟢 | - |
| P2-003 | Update intent-prefetch.py | Output predictions to Claude | Call /predict, format output | P2-002 | Queued | 🔴 | 131 |
| P2-004 | Implement context peek | First N lines of predicted files | Read + truncate in prefetch | P2-003 | Queued | 🟢 | - |
| P2-005 | Add UserPromptSubmit hook | Predict on prompt submission | New hook event handler | P2-003 | Queued | 🔴 | 131 |
| P2-006 | Confidence threshold tuning | Only show predictions above X% | Configurable threshold | P2-004 | Queued | 🟡 | - |

---

## Phase 3 - Multi-Query Fusion (Week 3)

**Success Criteria**: `/context` endpoint returns ranked files + snippets for natural language intent.

| # | Task | Expected Output | Solution Pattern | Deps | Status | C | R |
|---|------|-----------------|------------------|------|--------|---|---|
| P3-001 | Create /context endpoint | `POST /context` with intent description | Combine /predict + snippet extraction | P2-004 | Queued | 🟡 | GH |
| P3-002 | Add `aoa context` CLI | `aoa context "fix auth bug"` | CLI wrapper for /context | P3-001 | Queued | 🟢 | - |
| P3-003 | Implement semantic matching | Map intent words to tags | Keyword extraction + tag lookup | P3-001 | Queued | 🔴 | 131 |
| P3-004 | Bundle results with confidence | JSON with files, snippets, scores | Structured response format | P3-003 | Queued | 🟢 | - |
| P3-005 | Caching layer | Cache common intents | Redis cache with TTL | P3-004 | Queued | 🟡 | - |

---

## Phase 4 - Accuracy Tuning (Week 4)

**Success Criteria**: 90% of predicted files are actually used. Weights auto-tune based on feedback.

| # | Task | Expected Output | Solution Pattern | Deps | Status | C | R |
|---|------|-----------------|------------------|------|--------|---|---|
| P4-001 | Implement prediction logging | Log predictions vs actual usage | Store predictions, compare to intents | P2-003 | Queued | 🟢 | - |
| P4-002 | Calculate hit rate metrics | % of predictions that were used | Compare predicted files to Read events | P4-001 | Queued | 🟡 | - |
| P4-003 | Implement weight tuning | Adjust recency/frequency/tag weights | Gradient descent on hit rate | P4-002 | Queued | 🔴 | GH |
| P4-004 | Add `aoa feedback` command | Manual feedback on predictions | `aoa feedback good/bad <file>` | P4-001 | Queued | 🟢 | - |
| P4-005 | Dashboard metrics | View accuracy over time | `/metrics` endpoint or CLI | P4-002 | Queued | 🟡 | - |
| P4-006 | Achieve 90% accuracy | Hit rate >= 90% | Iterate tuning until target met | P4-003 | Queued | 🔴 | GH |

---

## Phases Overview

| Phase | Focus | Status | Blocked By | Success Metric |
|-------|-------|--------|------------|----------------|
| 1 | Redis Scoring Engine | ✅ Complete | - | /rank returns ranked files (6/6 rubrics) |
| 2 | Predictive Prefetch | Ready | - | PreHook outputs predictions |
| 3 | Multi-Query Fusion | Queued | Phase 2 | /context endpoint works |
| 4 | Accuracy Tuning | Queued | Phase 3 | 90% hit rate |

---

## Completed

| # | Task | Output | Completed |
|---|------|--------|-----------|
| P1 | Phase 1 - Redis Scoring Engine | 6/6 rubrics pass, 21ms avg latency | 2025-12-23 |
| - | GH Analysis | 4-phase implementation plan | 2025-12-23 |
| - | Current state assessment | Services running, 75 intents captured | 2025-12-23 |

---

## Architecture Notes

```
Current:
  intent-capture.py -> POST /intent -> indexer.py -> SQLite

Phase 1 adds:
  intent-capture.py -> POST /intent -> indexer.py -> SQLite
                                                  -> Redis (scores)

Phase 2 adds:
  intent-prefetch.py -> GET /predict -> scorer.py -> Redis
                     <- ranked files with confidence

Phase 3 adds:
  aoa context "..." -> POST /context -> semantic matcher
                    <- files + snippets + confidence
```

## Key Dependencies

- Redis: Already running in docker-compose
- redis-py: Need to verify installed
- Lua scripting: For atomic decay operations

---

## Confidence Assessment Rationale

### 🟢 (Confident) - 15 tasks
- Standard CRUD operations, package creation, endpoint patterns
- Direct parallels in existing codebase (indexer.py endpoints)
- Well-documented Redis operations

### 🟡 (Uncertain) - 8 tasks
- Integration points between components
- Score normalization (math needs validation)
- Threshold tuning (iterative)

### 🔴 (Lost) - 5 tasks
- **P1-008 (Decay)**: Lua scripting in Redis, scheduling approach unclear
- **P2-003 (PreHook output)**: How does Claude Code parse hook stdout?
- **P2-005 (UserPromptSubmit)**: Hook event behavior undocumented
- **P3-003 (Semantic matching)**: NLP approach vs simple keyword extraction?
- **P4-003/P4-006 (Weight tuning)**: Gradient descent or simpler heuristic?
