# Temporal Sequence Learning

Markov chain-based file access prediction for aOa.

## Quick Start

### 1. Start Services

```bash
# Start Redis
docker-compose up -d redis

# Start Status Service (includes sequence tracker)
python3 services/status/status_service.py
```

### 2. Automatic Learning

Sequence learning happens automatically through Claude Code hooks:
- Every file Read/Edit/Write is tracked
- Transitions are learned within 5-minute windows
- Probabilities update continuously

### 3. Query Predictions

```bash
# Get predictions after editing auth.py
curl 'http://localhost:9998/sequence/predict?file=/path/to/auth.py&project_id=default'

# Get session-based predictions
curl -X POST http://localhost:9998/sequence/predict \
  -H "Content-Type: application/json" \
  -d '{"session_id": "my-session", "project_id": "default"}'

# Get transition matrix
curl 'http://localhost:9998/sequence/matrix?file=/path/to/auth.py&project_id=default'

# Get stats
curl 'http://localhost:9998/sequence/stats?project_id=default'
```

## Example Output

### Prediction

```json
{
  "predictions": [
    {
      "from_file": "/project/auth.py",
      "to_file": "/project/auth_test.py",
      "probability": 0.8,
      "count": 12,
      "avg_time_delta": 180.5
    }
  ],
  "count": 1
}
```

**Interpretation:** After editing `auth.py`, there's an 80% chance you'll edit `auth_test.py` next, typically within ~3 minutes.

### Transition Matrix

```json
{
  "file": "/project/auth.py",
  "transitions": {
    "/project/auth_test.py": 0.8,
    "/project/middleware.py": 0.15,
    "/project/config.py": 0.05
  },
  "count": 3
}
```

## Testing

```bash
cd services/sequence
python3 test_sequence_learning.py
```

This simulates realistic workflows and demonstrates predictions.

## How It Works

### Markov Chains

```
P(file_B | file_A) = count(A→B) / count(A→*)
```

### Example Workflow

```
1. Edit auth.py          (t=0)
2. Edit auth_test.py     (t=2min)  → Records: auth.py → auth_test.py (120s)
3. Edit middleware.py    (t=4min)  → Records: auth_test.py → middleware.py (120s)
```

After seeing this pattern 10 times:
```
auth.py → auth_test.py (80% probability, ~120s avg)
auth.py → middleware.py (20% probability, ~240s avg)
```

## Configuration

Edit `sequence_tracker.py`:

```python
TIME_WINDOW_SECONDS = 300      # 5 minutes
MIN_TRANSITION_COUNT = 2       # Minimum significance
MAX_TRANSITIONS_PER_FILE = 20  # Pruning threshold
DECAY_FACTOR = 0.95            # Recency weighting
```

## Architecture

```
User action (Read/Edit/Write)
    ↓
intent-capture.py hook
    ↓
POST /sequence/record
    ↓
SequenceTracker.record_access()
    ↓
Redis:
  - sequences:{project}:{session} ← File access log
  - transitions:{project}:{file} ← Probability scores
  - transition_counts:{project}:{file} ← Raw counts
  - transition_timing:{project}:{file}:{target} ← Time deltas
    ↓
GET /sequence/predict
    ↓
Returns: Top N predictions with probabilities
```

## API Reference

### POST /sequence/record

Record a file access.

**Body:**
```json
{
  "session_id": "session-123",
  "project_id": "proj-uuid",
  "file": "/path/to/file.py",
  "tool": "Edit"
}
```

### GET /sequence/predict

Get predictions from a file.

**Query params:**
- `file` - Current file path
- `project_id` - Project ID (default: "default")
- `limit` - Max results (default: 5)

### POST /sequence/predict

Get predictions from session context.

**Body:**
```json
{
  "session_id": "session-123",
  "project_id": "proj-uuid",
  "limit": 10
}
```

### GET /sequence/matrix

Get full transition matrix for a file.

**Query params:**
- `file` - File path (required)
- `project_id` - Project ID (default: "default")

### GET /sequence/stats

Get learning statistics.

**Query params:**
- `project_id` - Project ID (default: "default")

## Files

- `sequence_tracker.py` - Core implementation
- `test_sequence_learning.py` - Test suite
- `README.md` - This file

## Integration

The sequence tracker is integrated into:
- ✅ `services/hooks/intent-capture.py` - Records sequences
- ✅ `services/hooks/intent-prefetch.py` - Uses predictions
- ✅ `plugin/hooks/aoa-intent-capture.py` - Plugin version
- ✅ `plugin/hooks/aoa-intent-prefetch.py` - Plugin version
- ✅ `services/status/status_service.py` - API endpoints

## Documentation

Full documentation: `docs/TEMPORAL_SEQUENCE_LEARNING.md`

## Performance

- **Record:** <10ms (O(10) - check last 10 accesses)
- **Predict:** <5ms (O(1) - Redis sorted set)
- **Storage:** ~1MB for typical project

## Future Enhancements

1. Second-order Markov chains (longer patterns)
2. Tool-aware predictions
3. Proactive prefetching
4. Workflow visualization

## Troubleshooting

**No predictions?**
- Need 5+ transitions first
- Check: `curl http://localhost:9998/sequence/stats`

**Wrong predictions?**
- Clear old data: `redis-cli KEYS "transitions:*" | xargs redis-cli DEL`
- Adjust `TIME_WINDOW_SECONDS` if needed

**Slow?**
- Reduce `MAX_TRANSITIONS_PER_FILE`
- Use local Redis instance
