# aOa Context Intelligence - Work Board

> **Updated**: 2025-12-27 (Session 12) | **Phase**: 5 - Go Live
> **Goal**: Position aOa on outcomes, not features
> **Strategic Review**: See `.context/details/strategic-board-refresh.md`

---

## Phase 5 - Go Live (Outcome Positioning)

**Success Criteria**: README, landing page, and visuals all lead with outcomes. Zero feature-first messaging.
**Strategy**: Outcome/Intent selling > Feature selling. Show what users achieve, not what the tool does.

### Positioning Framework

**The Name IS the Value Prop:**

| Component | Meaning | User Benefit |
|-----------|---------|--------------|
| **O** | Big O notation - O(1) constant time | Speed: Same cost for 100 files or 100,000 |
| **Angle** | Approach angle, precision | Accuracy: Right answer, not just fast |
| **Attack** | 5 groups, 15+ methods | Confidence: Multiple signals, one result |

**The Problem We Solve:**
```
Traditional search: Cost COMPOUNDS as codebase grows
  100 files   → $X
  10K files   → $10X
  100K files  → $100X   ← This is O(n) or worse

aOa: Cost stays FLAT regardless of size
  100 files   → $X
  10K files   → $X
  100K files  → $X      ← This is O(1)
```

### Simplified Messaging (for non-CS audience)

| Concept | Simple Explanation |
|---------|-------------------|
| **Big O** | "Pay the same no matter how big your project gets" |
| **Angle** | "We find the RIGHT file, not just any file" |
| **Attack** | "5 groups, 15+ methods, 1 confident answer" |

### The Attack Methods (Full Depth)

**GROUP 1: Search Methods**
| Method | What It Does |
|--------|--------------|
| Symbol search | O(1) inverted index lookup |
| Multi-term | Ranked by density across terms |
| Pattern search | Agent-driven regex |
| File glob | Pattern matching |
| Changes | Recently modified files |

**GROUP 2: Intent Methods**
| Method | What It Does |
|--------|--------------|
| Intent tracking | Learns from every tool call |
| Tag affinity | Groups files by intent (#auth, #python) |
| Recent intents | What's hot right now |

**GROUP 3: Knowledge Methods**
| Method | What It Does |
|--------|--------------|
| Repo search | Search external codebases |
| Repo multi | Multi-term in knowledge repos |

**GROUP 4: Ranking Signals**
| Signal | What It Does |
|--------|--------------|
| Recency | Time decay (recently touched = higher) |
| Frequency | Access count (often touched = higher) |
| Filename boost | Name matching (exact > prefix > contains) |
| Transitions | P(B\|A) from session history |

**GROUP 5: Prediction**
| Method | What It Does |
|--------|--------------|
| Predictive prefetch | Files ready before you ask |
| Confidence scoring | Only surface high-confidence results |

**Summary**: 5 attack groups × 15+ methods → 1 confident answer

### Headline Translations

| ❌ Feature | ✅ Outcome |
|-----------|-----------|
| "O(1) inverted index" | "Same speed for 100 or 100,000 files" |
| "Predictive prefetch" | "Your next file, before you ask" |
| "68% token savings" | "Pay the same fee, no matter how big" |
| "7 ranking signals" | "7 ways to find it, 1 confident answer" |
| "100% accuracy" | "Right answer, first try" |

| # | Task | Expected Output | Solution Pattern | Deps | Status | C | R |
|---|------|-----------------|------------------|------|--------|---|---|
| GL-001 | Outcome-focused README | Headlines sell results, not specs | Rewrite existing README with outcome table | - | Done | 🟢 | - |
| GL-002 | Demo GIFs | 4 GIFs: search, prediction, why, cost | asciinema or screen capture, convert to GIF | GL-001 | Queued | 🟢 | - |
| GL-003 | Token savings calculator | Input sessions/month → Output $/saved | Simple HTML/JS calculator, embed in README | - | Queued | 🟢 | - |
| GL-004 | O/Angle/Attack imagery | 6 Gemini images: hero, bigo, angle, attack, scaling, status | generate-imagery.py with GEMINI_API_KEY | - | Done | 🟢 | - |
| GL-005 | Landing page copy | One-pager with outcome headlines | Markdown or HTML, links to README | GL-001 | Queued | 🟢 | - |

### Visual Strategy

**6 Images (Gemini-generated):**

| Image | Concept | Visual |
|-------|---------|--------|
| hero | O(1) vs O(n) | Flat cyan line vs rising red curve |
| bigo | Big O explained | Multiple paths, one stays flat |
| angle | Accuracy | Bullseye targeting, precision hit |
| attack | 7 methods | Seven vectors converging on target |
| scaling | Cost comparison | Compounding vs flat cost |
| status | Dashboard | HUD with 7 green indicators |

**Generator**: `./assets/generate-imagery.py` (requires GEMINI_API_KEY)

### GL-002: Demo GIF Storyboards

**Theme**: "Angle of Attack" - Sharp, fast, precise. No wasted motion.

#### GIF 1: The Search (3-5 seconds)
```
Frame 1: Terminal prompt, cursor blinking
Frame 2: Type: aoa search handleAuth
Frame 3: INSTANT result (emphasize <5ms)
         ⚡ 7 hits │ 3.2ms
           src/auth/handler.py:45
           src/middleware/session.py:12
           ...
Frame 4: Brief pause to let it land
```
**Message**: "Find anything. Instantly."

#### GIF 2: The Prediction (4-6 seconds)
```
Frame 1: User types prompt: "Fix the auth bug"
Frame 2: Status line updates BEFORE Claude responds:
         ⚡ aOa 🟢 100% │ 45 intents │ auth.py session.py middleware.py
Frame 3: Claude's response starts: "I see the auth files..."
Frame 4: Highlight: files were ready BEFORE the ask
```
**Message**: "Your next file, before you ask."

#### GIF 3: The Why (3-4 seconds)
```
Frame 1: aoa why src/auth/handler.py
Frame 2: Output appears:
         Tags: #python #auth #security
         Recent Activity (1h):
           Edit │ #auth #python
           Read │ #auth
         Prediction signals: 3 tags, 2 recent intents
Frame 3: Brief pause
```
**Message**: "Every prediction, explainable."

#### GIF 4: The Cost (5-7 seconds)
```
Frame 1: Split screen or before/after
         LEFT: "Without aOa"
           grep auth... (200 tokens)
           grep login... (200 tokens)
           read 8 files... (6,000 tokens)
           Total: 6,600 tokens

         RIGHT: "With aOa"
           [predicted: auth.py, session.py]
           Total: 150 tokens

Frame 2: Big number appears: "97% SAVINGS"
Frame 3: Dollar amount: "~$X/month saved"
```
**Message**: "Cut your Claude costs by 2/3."

#### Recording Notes
- Use asciinema for terminal capture
- Convert to GIF with gifski or similar
- Keep under 1MB each for fast loading
- Dark terminal theme (consistent brand)
- Monospace font, high contrast

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

## Quick Wins (P0) - COMPLETE

All quick wins implemented. Concept validated with 96.8% hit rate on session replay.

| # | Win | Result | Status |
|---|-----|--------|--------|
| QW-1 | Extract session_id from hooks | session_id + tool_use_id extracted | Done |
| QW-2 | Log predictions to Redis | POST /predict/log with 60s TTL | Done |
| QW-3 | Compare predictions to actual reads | POST /predict/check records hit/miss | Done |
| QW-4 | Show hit rate in `aoa health` | GET /predict/stats, displayed in CLI | Done |

**Benchmark Result**: 5/6 tests pass, 96.8% hit rate - feasibility VALIDATED

---

## Active

| # | Task | Expected Output | Solution Pattern | Status | C | R |
|---|------|-----------------|------------------|--------|---|---|
| P4-006 | Achieve 90% accuracy | Hit@5 >= 90% | Progressive tuning via data collection | Active | 🟢 | - |

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

**Success Criteria**: PreHook outputs predicted files + snippets. Hit rate measurable from day one.
**Research**: See details/p2-001-confidence-research.md, p2-003-prehook-research.md, p2-005-userpromptsubmit-research.md
**Strategic**: See details/strategic-log-correlation.md, strategic-hidden-insights.md

| # | Task | Expected Output | Solution Pattern | Deps | Status | C | R |
|---|------|-----------------|------------------|------|--------|---|---|
| P2-001 | Implement confidence calculation | Score 0.0-1.0 per file | calculate_confidence() in scorer.py | P1-007 | Done | 🟢 | ✓ |
| P2-002 | Extract session linkage | Get session_id, tool_use_id from hooks | Parse stdin JSON in intent-capture.py | - | Done | 🟢 | ✓ |
| P2-003 | Store predictions with session | Redis keyed by session_id | POST /predict/log with 60s TTL | P2-002 | Done | 🟢 | ✓ |
| P2-004 | Create /predict endpoint | `POST /predict/log`, `POST /predict/check`, `GET /predict/stats` | Three endpoints in indexer.py | P2-001 | Done | 🟢 | - |
| P2-005 | Implement snippet prefetch | First N lines in additionalContext | GET /predict + read_file_snippet() | P2-004 | Done | 🟢 | - |
| P2-006 | Hit/miss tracking | Record prediction hits in PostToolUse | /predict/check records hit/miss | P2-003 | Done | 🟢 | ✓ |
| P2-007 | UserPromptSubmit hook | Predict on prompt submission | predict-context.py + additionalContext | P2-005 | Done | 🟢 | - |

---

## Phase 3 - Transition Model (Week 3)

**Success Criteria**: Predictions use Claude's learned behavior patterns. Hit@5 > 70%.
**Research**: See details/p3-architecture-research.md, p3-003-semantic-research.md
**Strategic**: See details/strategic-session-reward.md (ground truth approach)

| # | Task | Expected Output | Solution Pattern | Deps | Status | C | R |
|---|------|-----------------|------------------|------|--------|---|---|
| P3-001 | Session log parser | Parse ~/.claude/projects/ JSONL | Extract Read events with timestamps | P2-006 | ✅ | 🟢 | ✓ |
| P3-002 | Transition matrix builder | P(file_B \| file_A read) probabilities | Count transitions in Redis | P3-001 | ✅ | 🟢 | ✓ |
| P3-003 | Pattern-based keyword extraction | Extract keywords from intent | Reuse INTENT_PATTERNS from hooks | - | ✅ | 🟢 | ✓ |
| P3-004 | Create /context endpoint | `POST /context` returns files+snippets | Keywords + transitions + tags | P3-002 | ✅ | 🟢 | ✓ |
| P3-005 | Add `aoa context` CLI | `aoa context "fix auth bug"` | CLI wrapper for /context | P3-004 | ✅ | 🟢 | - |
| P3-006 | Caching layer | Cache common intents | Redis normalized keyword keys, 1hr TTL | P3-004 | ✅ | 🟢 | ✓ |

---

## Phase 4 - Weight Optimization (Week 4)

**Success Criteria**: 90% Hit@5 via data-driven weight tuning. Token savings visible.
**Research**: See details/p4-accuracy-research.md, p4-metrics-research.md
**Strategic**: See details/strategic-hidden-insights.md (token economics)
**Ground Truth**: Uses Claude session logs (~/.claude/projects/) for reward signal

| # | Task | Expected Output | Solution Pattern | Deps | Status | C | R |
|---|------|-----------------|------------------|------|--------|---|---|
| P4-001 | Rolling hit rate calculation | Hit@5 over 24h window | Redis ZSET, /predict/stats, /predict/finalize | P2-006 | ✅ | 🟢 | ✓ |
| P4-002 | Thompson Sampling tuner | 8 weight configurations | WeightTuner class, 5 endpoints | P4-001 | ✅ | 🟢 | ✓ |
| P4-003 | `/metrics` endpoint | Show accuracy + savings | Unified dashboard aggregating all metrics | P4-001 | ✅ | 🟢 | ✓ |
| P4-004 | Token cost tracking | Prove $ savings from predictions | get_token_usage(), /metrics/tokens | P3-001 | ✅ | 🟢 | ✓ |
| P4-005 | `aoa metrics` CLI | View accuracy in terminal | Progress bar + token dashboard | P4-003 | ✅ | 🟢 | ✓ |
| P4-006 | Achieve 90% accuracy | Hit@5 >= 90% | Ongoing data collection + tuner learning | P4-002 | Active | 🟢 | - |

---

## Benchmarking & Knowledge Repos

**Purpose**: Validate aOa's value proposition with real-world benchmarks on large codebases.

| # | Task | Expected Output | Solution Pattern | Status | C | R |
|---|------|-----------------|------------------|--------|---|---|
| B-001 | LSP Comparison Benchmark | Fair comparison vs grep approach | Knowledge-seeking: tool calls to find answers | Done | 🟢 | - |
| B-002 | Langchain Knowledge Repo | Large repo indexed for testing | ./repos mount, 2,612 files | Done | 🟢 | - |
| B-003 | aOa vs grep benchmarking | Speed/quality comparison | 74x faster, ranked results | Done | 🟢 | - |
| B-004 | /multi endpoint | Multi-term ranked search | GET+POST support, CLI auto-detect | Done | 🟢 | - |
| B-005 | Filename Boosting | Search ranks by filename match | indexer.py:267-313 | Done | 🟢 | - |
| B-006 | Session Benchmark (30 tasks) | Generic coding benchmark | 68% token savings, 57% accuracy | Done | 🟢 | - |
| B-007 | Traffic Light Branding | Grey/yellow/green accuracy display | aoa-status.sh, intent-summary.py | Done | 🟢 | - |

**Results**:
- 5/5 knowledge benchmark accuracy (100% top-1)
- 34% fewer tool calls, 61% token savings
- 74x faster on langchain (1.6ms vs 118ms)
- Session benchmark: 68% token savings, 57% cold-repo accuracy
- `/repo/<name>/symbol` endpoint discovered for repo-specific queries
- `aoa why <file>` explains prediction signals

---

## Phases Overview

| Phase | Focus | Status | Blocked By | Success Metric |
|-------|-------|--------|------------|----------------|
| 1 | Redis Scoring Engine | ✅ Complete | - | /rank returns ranked files (6/6 rubrics) |
| 2 | Prefetch + Correlation | ✅ Complete | - | 7/7 tasks done, 2/6 benchmark tests pass |
| 3 | Transition Model | ✅ Complete | - | 6/6 tasks done, /context + CLI + caching |
| 4 | Weight Optimization | 5/6 Complete | - | 90% Hit@5 + token savings visible |
| B | Benchmarking | ✅ Complete | - | 100% knowledge accuracy, 68% token savings |
| 5 | Go Live | 2/5 | - | Outcome positioning, visuals, landing page |

---

## Completed

| # | Task | Output | Completed |
|---|------|--------|-----------|
| P1 | Phase 1 - Redis Scoring Engine | 6/6 rubrics pass, 21ms avg latency | 2025-12-23 |
| QW | Quick Wins (all 4) | 5/6 tests pass, 96.8% hit rate validated | 2025-12-23 |
| P2-002 | Session linkage | session_id + tool_use_id extraction | 2025-12-23 |
| P2-003 | Prediction storage | /predict/log with 60s TTL | 2025-12-23 |
| P2-004 | Predict endpoints | /predict/log, /predict/check, /predict/stats | 2025-12-23 |
| P2-006 | Hit/miss tracking | intent-capture.py checks predictions | 2025-12-23 |
| P2-005 | Snippet prefetch | GET /predict returns file snippets | 2025-12-23 |
| P2-007 | UserPromptSubmit hook | predict-context.py injects additionalContext | 2025-12-23 |
| P2-001 | Confidence calculation | calculate_confidence() with evidence weighting | 2025-12-23 |
| R1 | Strategic research - P2/P3/P4 | All phases researched, all tasks green | 2025-12-23 |
| R2 | Strategic overall review | System assessment, gaps identified | 2025-12-23 |
| R3 | Strategic session reward | Claude logs as ground truth | 2025-12-23 |
| R4 | Strategic log correlation | session_id/tool_use_id linkage | 2025-12-23 |
| R5 | Strategic hidden insights | Token economics, 15 use cases | 2025-12-23 |
| R6 | Strategic board refresh | Enhanced roadmap with insights | 2025-12-23 |
| P3-001 | Session log parser | session_parser.py parses 49 sessions, 165 reads | 2025-12-24 |
| P3-002 | Transition matrix builder | 57 source files, 94 transitions in Redis | 2025-12-24 |
| P3-003 | Keyword extraction | extract_keywords() + INTENT_PATTERNS | 2025-12-24 |
| P3-004 | /context endpoint | POST /context returns files+snippets | 2025-12-24 |
| P3-005 | aoa context CLI | `aoa context "intent"` and `aoa ctx` | 2025-12-24 |
| P3-006 | Caching layer | 1hr TTL, normalized keywords, 30x speedup | 2025-12-24 |
| P4-001 | Rolling hit rate | Redis ZSET, /predict/stats, /predict/finalize | 2025-12-25 |
| P4-002 | Thompson Sampling | WeightTuner class, 8 arms, 5 endpoints | 2025-12-25 |
| P4-003 | /metrics endpoint | Unified dashboard: Hit@5, trend, tuner stats | 2025-12-25 |
| P4-004 | Token cost tracking | get_token_usage(), $2,378 saved (99.55% cache) | 2025-12-25 |
| P4-005 | aoa metrics CLI | `aoa metrics` + `aoa metrics tokens` | 2025-12-25 |
| B-001 | LSP Comparison Benchmark | Knowledge-seeking benchmark, 63% token savings | 2025-12-27 |
| B-002 | Langchain Knowledge Repo | 2,612 files, 34,526 symbols indexed | 2025-12-27 |
| B-003 | aOa vs grep benchmarking | 74x faster on large repo (1.6ms vs 118ms) | 2025-12-27 |
| B-005 | Filename Boosting | Search ranks files with query in name higher | 2025-12-27 |

---

## Architecture Notes

```
Current:
  intent-capture.py -> POST /intent -> indexer.py -> SQLite

Phase 1 adds:
  intent-capture.py -> POST /intent -> indexer.py -> SQLite
                                                  -> Redis (scores)

Phase 2 adds:
  UserPromptSubmit hook -> Extract session_id, keywords
                        -> GET /predict -> scorer.py -> Redis (tags, recency, frequency)
                        -> Read snippets (first N lines)
                        <- JSON additionalContext to Claude

  PostToolUse hook -> intent-capture.py (with session_id, tool_use_id)
                   -> Check: was file predicted? -> Record hit/miss

Phase 3 adds:
  Session log parser -> ~/.claude/projects/ -> Extract Read patterns
                     -> Build transition matrix (Read A -> usually Read B)
                     -> Store in Redis transitions:{file}

  aoa context "..." -> POST /context -> transitions + tags + keywords
                    <- files + snippets + confidence

Phase 4 adds:
  Rolling metrics -> Compare predictions to actual reads (ground truth)
               -> Thompson Sampling weight tuning
               -> /metrics endpoint shows Hit@5, token savings
```

## Key Dependencies

- Redis: Already running in docker-compose
- redis-py: Need to verify installed
- Lua scripting: For atomic decay operations

---

## Strategic Insights Summary

### Key Research Documents

| Document | Focus | Key Finding |
|----------|-------|-------------|
| strategic-board-refresh.md | Enhanced roadmap | Session logs eliminate 60% of complexity |
| strategic-overall-review.md | System assessment | Cold start is biggest challenge, quick wins identified |
| strategic-session-reward.md | Ground truth approach | Claude logs provide complete reward signal |
| strategic-log-correlation.md | Linkage strategy | session_id + tool_use_id enable perfect correlation |
| strategic-hidden-insights.md | Data mining | Token economics prove ROI, 15 use cases found |

### Confidence Assessment

**🟢 All tasks green** - Complete research coverage across P2-P4

**Phase 2**: Confidence + session linkage + prediction logging
- Researched: p2-001, p2-003, p2-005
- Strategic: log-correlation, hidden-insights

**Phase 3**: Transition model (not NLP)
- Researched: p3-architecture, p3-003-semantic
- Strategic: session-reward (ground truth)

**Phase 4**: Thompson Sampling + token economics
- Researched: p4-accuracy, p4-metrics
- Strategic: hidden-insights (ROI proof)
