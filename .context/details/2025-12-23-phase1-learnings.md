# Phase 1 Learnings - Redis Scoring Engine

> **Date**: 2025-12-23
> **Phase**: 1 - Redis Scoring Engine
> **Status**: Complete (6/6 rubrics pass)

---

## Technical Learnings

### Redis-py API Surprises

**ZUNIONSTORE weight format**: `redis-py` uses a dict format, not a separate `weights=` parameter.

```python
# WRONG
r.zunionstore('out', ['key1', 'key2'], weights=[1.0, 2.0])

# RIGHT
r.zunionstore('out', {'key1': 1.0, 'key2': 2.0})
```

### Timestamp Score Domination

**Problem**: Raw Unix timestamps (~1.7B) completely dominated other scores (0-100 range).

**Solution**: Normalize all scores to 0-100 range BEFORE weighting.

```python
# Exponential decay with 1-hour half-life
age_hours = (now - timestamp) / 3600
recency_score = 100 * math.exp(-0.693 * age_hours)  # 0.693 = ln(2)
```

### Docker Build Context

**Problem**: `COPY ../ranking /app/ranking` fails - Docker can't access parent directories.

**Solution**: Change build context in docker-compose.yml:

```yaml
# WRONG
build:
  context: ./src/index

# RIGHT
build:
  context: ./src
  dockerfile: index/Dockerfile
```

### Redis CLI in Docker

**Problem**: Each `docker exec redis-cli` is a new connection. `SELECT 15` doesn't persist.

**Solution**: Use `-n DB` flag:

```bash
# WRONG (SELECT doesn't persist between commands)
docker exec aoa-redis redis-cli SELECT 15
docker exec aoa-redis redis-cli KEYS "*"

# RIGHT
docker exec aoa-redis redis-cli -n 15 KEYS "*"
```

---

## Architecture Decisions

### Why Compute Composite in Python (Not Redis)

Redis ZUNIONSTORE can combine sorted sets with weights, but:
1. **No normalization control** - can't normalize before weighting
2. **Score range mismatch** - timestamps vs counts vs affinity scores
3. **Debugging difficulty** - can't inspect intermediate values

**Decision**: Compute composite score in Python (`scorer.py`) for full control.

### Score Normalization Strategy

All signals normalized to 0-100 before weighting:

| Signal | Raw Range | Normalization |
|--------|-----------|---------------|
| Recency | Unix timestamp | Exponential decay (1hr half-life) |
| Frequency | 1-N count | Log scale, capped at 100 |
| Tag Affinity | 0-N | Normalized to max in set |

### Weight Distribution

```python
WEIGHTS = {
    'recency': 0.40,    # Most recent files most relevant
    'frequency': 0.30,  # Frequently accessed files important
    'tag_affinity': 0.30  # Tag context matters equally to frequency
}
```

**Rationale**: Recency weighted highest because recent work is most relevant context. Frequency and tag affinity split evenly as secondary signals.

### Intent-Capture Integration

Fire-and-forget pattern - don't block intent capture on score recording:

```python
# In intent-capture.py (PostHook)
for file_path in captured_files:
    try:
        requests.post(f"{GATEWAY}/rank/record",
                     json={"file": file_path, "tags": tags},
                     timeout=0.1)  # Fast timeout
    except:
        pass  # Don't fail intent capture if scoring fails
```

---

## Benchmark Approach

### Rubric-Based Testing

Each test has clear pass/fail criteria that:
1. **Fail before implementation** - proves test is meaningful
2. **Pass after implementation** - proves feature works

### Test Suite Structure

```
.context/benchmarks/
├── conftest.py           # Shared fixtures, Redis DB 15 isolation
├── test_rubrics.py       # 6 rubric tests
└── test_ir_metrics.py    # IR metrics (NDCG, MRR, Hit Rate) for Phase 4
```

### The 6 Rubrics

| # | Rubric | What It Tests |
|---|--------|---------------|
| 1 | Recency | Recent files rank higher than old files |
| 2 | Frequency | Frequently accessed files rank higher |
| 3 | Tag Affinity | Files with matching tags rank higher |
| 4 | Composite | Combined scoring works correctly |
| 5 | Cold Start | Graceful handling when no data exists |
| 6 | Latency | Response time under 100ms |

### Redis DB Isolation

Tests use DB 15 to avoid interfering with production data (DB 0):

```python
@pytest.fixture
def isolated_redis():
    r = redis.Redis(host='localhost', port=6379, db=15)
    r.flushdb()  # Clean slate for each test
    yield r
    r.flushdb()  # Clean up after
```

---

## Files Created

| File | Purpose |
|------|---------|
| `/src/ranking/__init__.py` | Package init, exports RedisClient, Scorer |
| `/src/ranking/redis_client.py` | Redis sorted set operations wrapper |
| `/src/ranking/scorer.py` | Composite scoring with normalization |
| `.context/benchmarks/conftest.py` | Test fixtures |
| `.context/benchmarks/test_rubrics.py` | 6 rubric tests |
| `.context/benchmarks/test_ir_metrics.py` | IR metrics for Phase 4 |

## Files Modified

| File | Changes |
|------|---------|
| `/src/index/indexer.py` | Added `/rank`, `/rank/record` endpoints, scorer init |
| `/src/index/Dockerfile` | Added redis dep, ranking module COPY |
| `/src/gateway/gateway.py` | Added `/rank` proxy routes |
| `/src/hooks/intent-capture.py` | Added POST to `/rank/record` for each file |
| `/docker-compose.yml` | Changed index build context to `./src` |

---

## Performance Results

```
6/6 rubrics pass
Average latency: 21ms (target: <100ms)
Redis operations: <1ms each
```

---

## What's Next (Phase 2)

1. **Confidence scores**: Convert composite to 0.0-1.0 confidence
2. **`/predict` endpoint**: Return predictions with confidence
3. **PreHook integration**: Output predictions to Claude Code
4. **UserPromptSubmit hook**: Predict on prompt submission

---

## Key Insight

The hardest part wasn't the algorithm - it was the integration details:
- Docker build contexts
- Redis connection handling
- Score normalization math
- Test isolation

Always prototype integration paths early.
