# Context Intelligence Engine - Redis Ranking Architecture

**Date**: 2024-12-22
**Author**: GH (Growth Hacker Agent)
**Status**: Design Complete - Ready for Implementation

---

## Executive Summary

The Context Intelligence Engine is the brain of aOa. It learns from every tool call, ranks files by composite confidence scores, and prefetches the most likely files before the agent asks.

**The Loop:**
```
PostHook (LEARN) --> Redis (RANK) --> PreHook (PREFETCH)
     |                   |                   |
  Capture            Composite           Predict
  intent             scoring             context
```

**NOT code generation. NOT semantic search. YES finding things FAST in large codebases.**

---

## 1. Redis as Ranking Engine

### 1.1 Why Redis?

| Requirement | Redis Solution | Complexity |
|-------------|----------------|------------|
| Fast reads | In-memory | O(1) |
| Sorted queries | Sorted Sets (ZSET) | O(log n) |
| Atomic updates | ZINCRBY, ZADD | O(1) |
| TTL/decay | EXPIRE, score math | O(1) |
| Pub/sub | PUBLISH/SUBSCRIBE | O(subscribers) |
| Persistence | RDB/AOF | Async |

SQLite is great for cold storage and complex queries. Redis is essential for the **hot path** where latency matters (<50ms total).

### 1.2 Data Structures

#### A. File Scores (Sorted Set)

The primary ranking structure. One sorted set per scoring dimension.

```redis
# Per-dimension sorted sets
ZADD aoa:scores:recency <timestamp> "auth/session.py"
ZADD aoa:scores:frequency <count> "auth/session.py"
ZADD aoa:scores:comod <weight> "auth/session.py"
ZADD aoa:scores:intent:<tag> <count> "auth/session.py"

# Get top K files by recency
ZREVRANGE aoa:scores:recency 0 9 WITHSCORES

# Get score for a file
ZSCORE aoa:scores:frequency "auth/session.py"
```

**Why Sorted Sets?**
- `ZREVRANGE` gives top K in O(log n + k)
- `ZINCRBY` updates score atomically in O(log n)
- `ZUNIONSTORE` combines multiple dimensions
- Scores are floats - perfect for weighted ranking

#### B. Composite Scores (Computed Sorted Set)

Pre-computed final ranking using `ZUNIONSTORE` with weights.

```redis
# Combine dimensions with weights
ZUNIONSTORE aoa:composite 4 \
    aoa:scores:recency \
    aoa:scores:frequency \
    aoa:scores:comod \
    aoa:scores:intent:authentication \
    WEIGHTS 0.3 0.25 0.25 0.2

# Get top files with confidence
ZREVRANGE aoa:composite 0 4 WITHSCORES
```

**Output:**
```
1) "auth/session.py"    -> 0.92
2) "middleware/auth.py" -> 0.85
3) "tests/test_auth.py" -> 0.78
4) "config/auth.yaml"   -> 0.65
5) "api/routes/auth.py" -> 0.61
```

#### C. Intent Tag Index (Hash + Sets)

Fast bidirectional lookup between tags and files.

```redis
# Tag -> Files (Set)
SADD aoa:tag:authentication "auth/session.py" "middleware/auth.py"
SADD aoa:tag:editing "auth/session.py" "config/settings.py"

# File -> Tags (Set)
SADD aoa:file:auth/session.py "#authentication" "#editing" "#python"

# Tag frequency for ranking
ZINCRBY aoa:tag_freq "authentication" 1
```

#### D. Co-Modification Graph (Hash of Sorted Sets)

Track which files change together.

```redis
# File -> Related Files with edge weights
ZINCRBY aoa:comod:auth/session.py 1 "middleware/auth.py"
ZINCRBY aoa:comod:auth/session.py 1 "tests/test_auth.py"

# Decay old edges (run periodically)
# Multiply all scores by 0.95 (5% decay per hour)
# Custom Lua script needed (see Section 3.3)
```

#### E. Session State (Hash with TTL)

Per-session tracking for context continuity.

```redis
# Current session state
HSET aoa:session:<id> \
    current_file "auth/session.py" \
    current_intent "authentication" \
    last_access 1703289600

# Files accessed this session (sorted by recency)
ZADD aoa:session:<id>:files <timestamp> "auth/session.py"

# Auto-expire after 24 hours
EXPIRE aoa:session:<id> 86400
EXPIRE aoa:session:<id>:files 86400
```

### 1.3 Redis Commands Summary

| Operation | Command | Complexity |
|-----------|---------|------------|
| Record file access | `ZADD`, `ZINCRBY` | O(log n) |
| Get top K files | `ZREVRANGE` | O(log n + k) |
| Combine dimensions | `ZUNIONSTORE` | O(N log N) |
| Add tag to file | `SADD` | O(1) |
| Get files for tag | `SMEMBERS` | O(n) |
| Increment co-mod edge | `ZINCRBY` | O(log n) |
| Session lookup | `HGET`, `HSET` | O(1) |

---

## 2. The Scoring Formula

### 2.1 Signal Definitions

| Signal | Source | Range | Update Frequency |
|--------|--------|-------|------------------|
| **Recency** | File access timestamp | 0-1 (normalized) | Every access |
| **Frequency** | Access count | 0-1 (log-normalized) | Every access |
| **Tag Match** | Intent tag overlap | 0-1 | Every intent capture |
| **Co-Modification** | Historical co-changes | 0-1 | Every file save |
| **Session Affinity** | Same-session co-access | 0-1 | Every access |

### 2.2 Normalization

All scores must be normalized to 0-1 range for fair weighting.

```python
def normalize_recency(timestamp: int, now: int, half_life: int = 3600) -> float:
    """Exponential decay with 1-hour half-life."""
    age = now - timestamp
    return 2 ** (-age / half_life)

def normalize_frequency(count: int, max_count: int = 100) -> float:
    """Log-normalized frequency (diminishing returns)."""
    return min(1.0, math.log(count + 1) / math.log(max_count + 1))

def normalize_comod(weight: float, max_weight: float = 10.0) -> float:
    """Linear normalization with cap."""
    return min(1.0, weight / max_weight)
```

### 2.3 Composite Score Formula

```python
def compute_confidence(file: str, intent_tags: List[str], session_id: str) -> float:
    """
    Compute composite confidence score for a file.

    Returns: float between 0 and 1
    """
    weights = {
        'recency': 0.30,      # Recent files are likely relevant
        'frequency': 0.20,    # Frequently accessed = important
        'tag_match': 0.25,    # Intent tag overlap is strong signal
        'comod': 0.15,        # Co-modification patterns
        'session': 0.10,      # Same-session affinity
    }

    scores = {
        'recency': get_recency_score(file),
        'frequency': get_frequency_score(file),
        'tag_match': get_tag_match_score(file, intent_tags),
        'comod': get_comod_score(file, current_file),
        'session': get_session_affinity(file, session_id),
    }

    return sum(weights[k] * scores[k] for k in weights)
```

### 2.4 Weight Tuning

Start with these defaults, then tune based on prefetch accuracy metrics:

| Signal | Default Weight | Rationale |
|--------|----------------|-----------|
| Recency | 0.30 | Most predictive for "what's next" |
| Tag Match | 0.25 | Intent is strong signal when available |
| Frequency | 0.20 | Popular files are likely needed |
| Co-mod | 0.15 | Historical patterns matter |
| Session | 0.10 | Session context is noisy |

**Tuning Strategy:**
1. Log all prefetch predictions
2. Track hit rate (file was actually accessed)
3. Adjust weights toward signals with higher hit rate
4. Re-evaluate weekly

### 2.5 Avoiding Score Explosion/Starvation

**Problem 1: Score Explosion**
- Frequently accessed files get unbounded scores
- Solution: Normalize to 0-1 range, use log scaling

**Problem 2: Score Starvation**
- New files never get accessed because old files dominate
- Solution: Exploration bonus for files with low access count

**Problem 3: Intent Flooding**
- Same tag repeated many times inflates score
- Solution: Cap tag contributions per file

```python
# Anti-starvation: exploration bonus
if file_access_count < 3:
    score += 0.1 * (3 - file_access_count)  # Bonus for new files

# Anti-flooding: cap tag matches
tag_matches = min(5, len(matching_tags))  # Max 5 tags count
tag_score = tag_matches / 5.0
```

---

## 3. The Learn -> Rank -> Prefetch Pipeline

### 3.1 PostHook: LEARN (Data Capture)

**Trigger**: After every tool call (PostToolUse hook)

**Input**: Tool name, file paths, inferred tags, session ID

**Actions**:
1. Update recency score for each file
2. Increment frequency counter
3. Add intent tags to file
4. Update co-modification edges (if within time window)
5. Update session affinity

```python
# PostHook -> Redis flow
def on_post_tool_use(tool: str, files: List[str], tags: List[str], session_id: str):
    now = int(time.time())

    for file in files:
        # 1. Recency (timestamp as score)
        redis.zadd('aoa:scores:recency', {file: now})

        # 2. Frequency (increment)
        redis.zincrby('aoa:scores:frequency', 1, file)

        # 3. Intent tags
        for tag in tags:
            redis.sadd(f'aoa:tag:{tag}', file)
            redis.sadd(f'aoa:file:{file}', tag)
            redis.zincrby(f'aoa:scores:intent:{tag}', 1, file)

        # 4. Co-modification (within 5 min window)
        recent = redis.zrevrangebyscore('aoa:scores:recency', now, now - 300)
        for other in recent:
            if other != file:
                redis.zincrby(f'aoa:comod:{file}', 1, other)
                redis.zincrby(f'aoa:comod:{other}', 1, file)

        # 5. Session affinity
        redis.zadd(f'aoa:session:{session_id}:files', {file: now})

    return True  # Fire and forget
```

**Latency Budget**: <10ms (non-blocking, async)

### 3.2 Redis: RANK (Score Computation)

**Trigger**: On-demand when PreHook requests ranking

**Strategy A: Pre-computed (recommended)**

Compute composite scores periodically and on access.

```python
def recompute_composite(intent_tags: List[str] = None):
    """
    Recompute composite ranking using ZUNIONSTORE.
    Call this after significant updates or on a schedule.
    """
    keys = [
        'aoa:scores:recency',
        'aoa:scores:frequency',
        'aoa:scores:comod_normalized',
    ]
    weights = [0.30, 0.20, 0.15]

    # Add intent-specific scores if we have current intent
    if intent_tags:
        for tag in intent_tags[:3]:  # Top 3 tags only
            key = f'aoa:scores:intent:{tag}'
            if redis.exists(key):
                keys.append(key)
                weights.append(0.25 / len(intent_tags))

    # Compute union with weights
    redis.zunionstore('aoa:composite', keys, weights)

    # Set TTL to force recomputation
    redis.expire('aoa:composite', 60)  # 1 minute TTL
```

**Strategy B: On-demand (for per-request customization)**

Compute scores at query time for maximum freshness.

```python
def get_ranked_files(intent_tags: List[str], limit: int = 5) -> List[Tuple[str, float]]:
    """
    Get top files ranked by composite score.
    Returns list of (file, confidence) tuples.
    """
    # Build temporary composite for this query
    temp_key = f'aoa:temp:{uuid4()}'

    try:
        recompute_composite_to(temp_key, intent_tags)
        results = redis.zrevrange(temp_key, 0, limit - 1, withscores=True)
        return [(f.decode(), score) for f, score in results]
    finally:
        redis.delete(temp_key)
```

**Latency Budget**: <20ms

### 3.3 PreHook: PREFETCH (Prediction)

**Trigger**: Before file operations (PreToolUse hook)

**Input**: Current file being accessed, session ID

**Output**: List of likely-needed files with confidence scores

```python
def on_pre_tool_use(tool: str, current_file: str, session_id: str) -> dict:
    """
    Predict which files will be needed next.
    Returns prefetch suggestions if confidence is high enough.
    """
    if tool not in ('Read', 'Edit', 'Write'):
        return {}  # Only prefetch for file operations

    # Get current intent tags from the file
    tags = list(redis.smembers(f'aoa:file:{current_file}'))

    # Get ranked files
    candidates = get_ranked_files(tags, limit=10)

    # Filter by confidence threshold
    threshold = get_confidence_threshold(session_id)
    suggestions = [
        (file, score) for file, score in candidates
        if score >= threshold and file != current_file
    ][:5]

    if not suggestions:
        return {}

    return {
        'confidence': suggestions[0][1],
        'suggestions': [
            {'file': f, 'score': round(s, 2)}
            for f, s in suggestions
        ]
    }
```

**Latency Budget**: <20ms

### 3.4 Full Pipeline Latency

```
PostHook capture:    <10ms (async, non-blocking)
Redis ranking:       <20ms (pre-computed or on-demand)
PreHook prediction:  <20ms (includes Redis query)
-----------------------------------------
Total user-facing:   <50ms (target met)
```

---

## 4. SQLite vs Redis - Separation of Concerns

### 4.1 Redis (Hot Path)

**Use Redis for:**
- Real-time scores and rankings
- Session state
- Fast lookups (tag -> files, file -> tags)
- Pub/sub for multi-agent coordination
- TTL-based expiration

**Data in Redis:**
```
aoa:scores:*          # Sorted sets for each dimension
aoa:composite         # Pre-computed composite ranking
aoa:tag:*             # Tag -> files sets
aoa:file:*            # File -> tags sets
aoa:comod:*           # Co-modification edges
aoa:session:*         # Session state and files
```

### 4.2 SQLite (Cold Storage)

**Use SQLite for:**
- Persistent intent history (audit log)
- Complex queries (date ranges, aggregations)
- Analytics and reporting
- Backup/sync for Redis data
- Configuration and settings

**Tables in SQLite:**
```sql
CREATE TABLE intent_log (
    id INTEGER PRIMARY KEY,
    timestamp INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    tool TEXT NOT NULL,
    files TEXT NOT NULL,  -- JSON array
    tags TEXT NOT NULL,   -- JSON array
    INDEX idx_timestamp (timestamp),
    INDEX idx_session (session_id)
);

CREATE TABLE file_stats (
    file TEXT PRIMARY KEY,
    total_accesses INTEGER DEFAULT 0,
    last_access INTEGER,
    first_access INTEGER,
    avg_session_duration REAL
);

CREATE TABLE tag_stats (
    tag TEXT PRIMARY KEY,
    total_uses INTEGER DEFAULT 0,
    files_count INTEGER DEFAULT 0
);
```

### 4.3 Sync Strategy

**Redis -> SQLite (Periodic Backup)**
- Every 5 minutes: Dump intent log to SQLite
- On shutdown: Flush all pending writes

**SQLite -> Redis (On Startup)**
- Load last 24 hours of intent data
- Rebuild scores from historical access patterns

```python
def sync_to_sqlite():
    """Periodic sync of Redis data to SQLite."""
    # Get pending intents from Redis list
    pending = redis.lrange('aoa:pending_intents', 0, -1)

    with sqlite3.connect('aoa.db') as conn:
        for intent_json in pending:
            intent = json.loads(intent_json)
            conn.execute(
                'INSERT INTO intent_log (timestamp, session_id, tool, files, tags) VALUES (?, ?, ?, ?, ?)',
                (intent['timestamp'], intent['session_id'], intent['tool'],
                 json.dumps(intent['files']), json.dumps(intent['tags']))
            )

    # Clear synced items
    redis.delete('aoa:pending_intents')

def load_from_sqlite():
    """On startup: rebuild Redis from SQLite."""
    cutoff = int(time.time()) - 86400  # Last 24 hours

    with sqlite3.connect('aoa.db') as conn:
        rows = conn.execute(
            'SELECT * FROM intent_log WHERE timestamp > ?',
            (cutoff,)
        ).fetchall()

    for row in rows:
        files = json.loads(row['files'])
        tags = json.loads(row['tags'])
        # Replay into Redis (but don't re-log to SQLite)
        replay_intent(row['timestamp'], row['session_id'], row['tool'], files, tags)
```

---

## 5. Confidence Threshold

### 5.1 When to Prefetch vs Stay Silent

| Confidence | Action | Rationale |
|------------|--------|-----------|
| >= 0.80 | Prefetch + Show | High confidence, show user |
| 0.60 - 0.79 | Prefetch silently | Good confidence, don't distract |
| 0.40 - 0.59 | Maybe prefetch | Only if cache is cold |
| < 0.40 | Stay silent | Not enough signal |

### 5.2 Adaptive Threshold

Start with a default, then adjust based on user feedback.

```python
class AdaptiveThreshold:
    def __init__(self, default: float = 0.60):
        self.default = default
        self.session_thresholds = {}

    def get(self, session_id: str) -> float:
        """Get threshold for session, with adaptation."""
        key = f'aoa:threshold:{session_id}'
        stored = redis.get(key)
        if stored:
            return float(stored)
        return self.default

    def feedback(self, session_id: str, was_helpful: bool):
        """Adjust threshold based on user feedback."""
        key = f'aoa:threshold:{session_id}'
        current = self.get(session_id)

        if was_helpful:
            # Lower threshold (show more suggestions)
            new = max(0.40, current - 0.05)
        else:
            # Raise threshold (show fewer suggestions)
            new = min(0.90, current + 0.05)

        redis.set(key, new)
        redis.expire(key, 86400)  # Reset daily
```

### 5.3 User Tuning

Allow users to set their preference:

```bash
# Conservative (fewer suggestions, higher confidence)
aoa config threshold 0.80

# Balanced (default)
aoa config threshold 0.60

# Aggressive (more suggestions, lower confidence)
aoa config threshold 0.40
```

### 5.4 Avoiding Noise

**Problem**: Low-confidence spam floods the user with useless suggestions.

**Solutions**:

1. **Minimum confidence floor** (0.40)
   - Never show below this regardless of settings

2. **Rate limiting**
   - Max 1 prefetch suggestion per 30 seconds
   - Reset on user action

3. **Diminishing returns**
   - After 3 ignored suggestions, raise threshold temporarily

```python
def should_show_prefetch(session_id: str, confidence: float) -> bool:
    """Decide whether to show prefetch to user."""
    # Floor
    if confidence < 0.40:
        return False

    # Check threshold
    threshold = get_threshold(session_id)
    if confidence < threshold:
        return False

    # Rate limit
    last_shown = redis.get(f'aoa:last_prefetch:{session_id}')
    if last_shown and (time.time() - float(last_shown)) < 30:
        return False

    # Ignore penalty
    ignores = int(redis.get(f'aoa:ignores:{session_id}') or 0)
    if ignores >= 3:
        if confidence < (threshold + 0.10):
            return False

    return True
```

---

## 6. Implementation Roadmap

### Phase 1: Core Redis Integration (Day 1)

| Task | Deliverable |
|------|-------------|
| Setup Redis connection | `redis_client.py` |
| Implement score updates | `on_post_tool_use()` |
| Implement ranking query | `get_ranked_files()` |
| Update PostHook | Write to Redis |
| Update PreHook | Read from Redis |

### Phase 2: Composite Scoring (Day 2)

| Task | Deliverable |
|------|-------------|
| Implement normalization | Score math functions |
| Implement ZUNIONSTORE | Composite ranking |
| Add decay mechanism | Lua script for decay |
| Add co-mod tracking | Edge weight updates |

### Phase 3: SQLite Sync (Day 3)

| Task | Deliverable |
|------|-------------|
| Create SQLite schema | `aoa.db` tables |
| Implement sync jobs | Periodic backup |
| Implement startup load | Rebuild from history |
| Add analytics queries | Stats endpoints |

### Phase 4: Confidence Tuning (Day 4)

| Task | Deliverable |
|------|-------------|
| Implement adaptive threshold | Per-session adjustment |
| Add user config | `aoa config threshold` |
| Add rate limiting | Noise reduction |
| Add metrics logging | Prefetch accuracy tracking |

---

## 7. Redis Lua Scripts

### 7.1 Decay All Scores

```lua
-- decay_scores.lua
-- Multiply all scores in a sorted set by decay factor
-- KEYS[1] = sorted set key
-- ARGV[1] = decay factor (e.g., 0.95)

local members = redis.call('ZRANGE', KEYS[1], 0, -1, 'WITHSCORES')
local decay = tonumber(ARGV[1])

for i = 1, #members, 2 do
    local member = members[i]
    local score = tonumber(members[i + 1])
    local new_score = score * decay

    if new_score < 0.01 then
        redis.call('ZREM', KEYS[1], member)
    else
        redis.call('ZADD', KEYS[1], new_score, member)
    end
end

return #members / 2
```

Usage:
```python
# Decay recency scores by 5% per hour
redis.eval(DECAY_SCRIPT, 1, 'aoa:scores:recency', 0.95)
```

### 7.2 Atomic Score Update

```lua
-- update_score.lua
-- Update multiple scores atomically
-- KEYS = score keys to update
-- ARGV = alternating (file, increment) pairs

for i = 1, #ARGV, 2 do
    local file = ARGV[i]
    local incr = tonumber(ARGV[i + 1])

    for j = 1, #KEYS do
        redis.call('ZINCRBY', KEYS[j], incr, file)
    end
end

return 'OK'
```

---

## 8. API Endpoints

### New Endpoints for Intelligence Engine

```python
@app.route('/rank', methods=['POST'])
def get_ranking():
    """
    Get ranked files for current context.

    POST body:
    {
        "intent_tags": ["#authentication", "#editing"],
        "current_file": "auth/session.py",
        "session_id": "abc123",
        "limit": 5
    }

    Returns:
    {
        "confidence": 0.87,
        "suggestions": [
            {"file": "middleware/auth.py", "score": 0.85},
            {"file": "tests/test_auth.py", "score": 0.78}
        ],
        "ms": 12.5
    }
    """

@app.route('/feedback', methods=['POST'])
def record_feedback():
    """
    Record user feedback on prefetch quality.

    POST body:
    {
        "session_id": "abc123",
        "was_helpful": true
    }
    """

@app.route('/threshold', methods=['GET', 'POST'])
def threshold():
    """
    Get or set confidence threshold.

    GET: Returns current threshold
    POST: Sets new threshold {"value": 0.70}
    """
```

---

## 9. Metrics and Monitoring

### Key Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Prefetch accuracy | >70% | Files prefetched that were accessed |
| Prefetch latency | <50ms | Time from request to response |
| Redis memory | <100MB | `INFO memory` |
| Score staleness | <5 min | Time since last composite recompute |

### Logging

```python
# Log prefetch predictions for accuracy tracking
def log_prefetch(session_id: str, predictions: List[str], accessed: str):
    """Log prediction accuracy for tuning."""
    hit = accessed in predictions

    redis.lpush('aoa:prefetch_log', json.dumps({
        'timestamp': time.time(),
        'session_id': session_id,
        'predictions': predictions,
        'accessed': accessed,
        'hit': hit
    }))

    # Trim to last 1000
    redis.ltrim('aoa:prefetch_log', 0, 999)
```

---

## 10. Summary

### What Redis Stores

| Key Pattern | Data Structure | Purpose |
|-------------|----------------|---------|
| `aoa:scores:*` | Sorted Set | Per-dimension scores |
| `aoa:composite` | Sorted Set | Pre-computed ranking |
| `aoa:tag:*` | Set | Tag -> files mapping |
| `aoa:file:*` | Set | File -> tags mapping |
| `aoa:comod:*` | Sorted Set | Co-modification edges |
| `aoa:session:*` | Hash + Sorted Set | Session state |
| `aoa:threshold:*` | String | Per-session threshold |

### What SQLite Stores

| Table | Purpose |
|-------|---------|
| `intent_log` | Audit trail of all intents |
| `file_stats` | Aggregate file statistics |
| `tag_stats` | Aggregate tag statistics |

### The Flow

```
1. User triggers tool call
2. PostHook captures intent
3. PostHook writes to Redis (async, <10ms)
4. [Background] Composite score recomputed
5. User triggers next tool call
6. PreHook queries Redis ranking (<20ms)
7. If confidence > threshold:
   - Show: "Start with these files..."
8. User continues (with or without suggestion)
9. Accuracy logged for tuning
```

**This is the core of aOa. Context-aware. Learning. Fast.**

---

## Next Steps

1. [ ] Implement Redis client wrapper (`/home/corey/claudacity/index/redis_client.py`)
2. [ ] Update PostHook to write to Redis
3. [ ] Update PreHook to query Redis ranking
4. [ ] Add composite score computation
5. [ ] Add SQLite sync jobs
6. [ ] Add `/rank` API endpoint
7. [ ] Add prefetch accuracy logging
8. [ ] Tune weights based on accuracy data

---

*Document created by GH (Growth Hacker Agent) - 2024-12-22*
