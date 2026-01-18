# Performance Telemetry Dashboard API

The `/metrics` endpoint provides comprehensive performance telemetry for the aOa system, helping you track prediction accuracy, service latencies, cache efficiency, and token savings.

## Quick Start

```bash
# Get all metrics
curl http://localhost:8080/metrics

# Get metrics with pretty formatting
curl http://localhost:8080/metrics | jq
```

## Endpoint

**GET** `/metrics`

Query Parameters:
- `project_id` (optional): UUID for per-project metrics

## Response Structure

### 1. Prediction Accuracy

Track how well aOa predicts which files you'll need next.

```json
{
  "hit_at_5": 0.72,
  "hit_at_5_pct": 72.0,
  "target": 0.90,
  "target_pct": 90.0,
  "gap": 0.18,
  "trend": "improving"
}
```

- **hit_at_5**: Fraction of predictions where at least one of the top 5 predicted files was accessed (0.0 to 1.0)
- **hit_at_5_pct**: Same as hit_at_5 but as percentage (0 to 100)
- **target**: Target accuracy goal (90%)
- **gap**: How far from target
- **trend**: `improving`, `declining`, `stable`, or `insufficient_data`

### 2. Rolling Window Stats

24-hour rolling window accuracy metrics.

```json
{
  "rolling": {
    "window_hours": 24,
    "total_predictions": 150,
    "evaluated": 120,
    "pending": 30,
    "hits": 86,
    "misses": 34,
    "hit_at_5": 0.7167,
    "hit_at_5_pct": 71.7
  }
}
```

### 3. Adaptive Weight Learning (Thompson Sampling)

Shows which prediction strategy is performing best for your workflow.

```json
{
  "tuner": {
    "best_arm": "recency-heavy",
    "best_arm_idx": 2,
    "best_weights": {
      "recency": 0.5,
      "frequency": 0.3,
      "tags": 0.2
    },
    "best_mean": 0.7800,
    "total_samples": 150
  }
}
```

### 4. Service Latencies (NEW)

P50, P95, and P99 latencies for each service and operation.

```json
{
  "latency": {
    "index": {
      "symbol": {
        "count": 245,
        "p50": 3.2,
        "p95": 12.5,
        "p99": 24.8,
        "min": 1.1,
        "max": 45.2,
        "avg": 5.6
      },
      "multi": {
        "count": 89,
        "p50": 5.4,
        "p95": 18.2,
        "p99": 32.1,
        "min": 2.3,
        "max": 52.8,
        "avg": 8.9
      }
    },
    "status": {
      "status": {
        "count": 312,
        "p50": 1.8,
        "p95": 4.2,
        "p99": 8.5,
        "min": 0.5,
        "max": 12.3,
        "avg": 2.1
      }
    },
    "gateway": {
      "symbol": {
        "count": 245,
        "p50": 4.1,
        "p95": 14.3,
        "p99": 28.9,
        "min": 2.2,
        "max": 48.1,
        "avg": 6.8
      }
    }
  }
}
```

All latencies are in **milliseconds**.

### 5. Cache Hit Rates (NEW)

Redis cache and symbol table statistics.

```json
{
  "cache": {
    "redis": {
      "hits": 8542,
      "misses": 1234,
      "hit_rate": 87.38,
      "total_keys": 1547
    },
    "symbol_table": {
      "total_symbols": 45823,
      "total_files": 2341
    }
  }
}
```

### 6. Token Savings

Real measurements of token savings from using aOa.

```json
{
  "savings": {
    "tokens": 847234,
    "baseline": 1234567,
    "actual": 387333,
    "measured_records": 1523,
    "time_sec": 6354.26
  }
}
```

- **tokens**: Total tokens saved
- **baseline**: What Claude would have used without aOa
- **actual**: What Claude actually used with aOa
- **measured_records**: Number of tool calls measured
- **time_sec**: Estimated time saved (at 7.5ms per token)

### 7. Legacy Cumulative Stats

All-time hit/miss counters.

```json
{
  "legacy": {
    "hits": 200,
    "misses": 100,
    "total": 300,
    "hit_rate": 66.7
  }
}
```

## What the Metrics Tell You

### Prediction Accuracy
- **Above 80%**: aOa is accurately predicting your workflow
- **60-80%**: Good performance, still learning patterns
- **Below 60%**: Early stage, needs more data

### Latencies
- **P50 < 10ms**: Excellent responsiveness
- **P95 < 50ms**: Good 95th percentile performance
- **P99 > 100ms**: Investigate slow outliers

### Cache Hit Rate
- **Above 85%**: Excellent cache utilization
- **70-85%**: Good caching efficiency
- **Below 70%**: May need cache tuning

### Token Savings
The `savings` metrics show real money and time saved:
- Average Claude pricing: ~$3-15 per 1M tokens
- With 847k tokens saved, that's roughly **$2.54 to $12.71 saved**
- Time saved: ~1.76 hours of context loading avoided

## Monitoring Tips

### Track Trends Over Time

```bash
# Poll metrics every minute and log
while true; do
  curl -s http://localhost:8080/metrics | jq '{
    accuracy: .hit_at_5_pct,
    latency_p50: .latency.index.symbol.p50,
    cache_rate: .cache.redis.hit_rate,
    tokens_saved: .savings.tokens
  }' >> metrics.log
  sleep 60
done
```

### Set Up Alerts

```bash
# Alert if accuracy drops below 60%
ACCURACY=$(curl -s http://localhost:8080/metrics | jq '.hit_at_5_pct')
if (( $(echo "$ACCURACY < 60" | bc -l) )); then
  echo "ALERT: Prediction accuracy dropped to $ACCURACY%"
fi
```

### Visualize in Grafana

The metrics are designed to integrate with monitoring tools:
1. Export metrics to Prometheus format
2. Visualize P50/P95/P99 latencies as line charts
3. Track cache hit rates as gauges
4. Plot accuracy trends over time

## Related Endpoints

- **GET** `/metrics/tokens` - Detailed token usage from Claude sessions
- **GET** `/predict/stats` - Prediction statistics only
- **GET** `/tuner/stats` - Adaptive weight tuning details
- **GET** `/status/json` - Session status and costs

## Example: Full Response

See the complete response structure:

```bash
curl http://localhost:8080/metrics | jq
```

```json
{
  "hit_at_5": 0.7167,
  "hit_at_5_pct": 71.7,
  "target": 0.9,
  "target_pct": 90,
  "gap": 0.1833,
  "trend": "improving",
  "rolling": {
    "window_hours": 24,
    "total_predictions": 150,
    "evaluated": 120,
    "pending": 30,
    "hits": 86,
    "misses": 34,
    "hit_at_5": 0.7167,
    "hit_at_5_pct": 71.7
  },
  "tuner": {
    "best_arm": "recency-heavy",
    "best_arm_idx": 2,
    "best_weights": {
      "recency": 0.5,
      "frequency": 0.3,
      "tags": 0.2
    },
    "best_mean": 0.78,
    "total_samples": 150
  },
  "legacy": {
    "hits": 200,
    "misses": 100,
    "total": 300,
    "hit_rate": 66.7
  },
  "savings": {
    "tokens": 847234,
    "baseline": 1234567,
    "actual": 387333,
    "measured_records": 1523,
    "time_sec": 6354.26
  },
  "latency": {
    "index": {
      "symbol": {
        "count": 245,
        "p50": 3.2,
        "p95": 12.5,
        "p99": 24.8,
        "min": 1.1,
        "max": 45.2,
        "avg": 5.6
      }
    },
    "status": {
      "status": {
        "count": 312,
        "p50": 1.8,
        "p95": 4.2,
        "p99": 8.5,
        "min": 0.5,
        "max": 12.3,
        "avg": 2.1
      }
    }
  },
  "cache": {
    "redis": {
      "hits": 8542,
      "misses": 1234,
      "hit_rate": 87.38,
      "total_keys": 1547
    },
    "symbol_table": {
      "total_symbols": 45823,
      "total_files": 2341
    }
  }
}
```

## Impact & ROI

This feature provides **Medium Impact** with **Low Effort**:

✅ **Users see the value**: Real metrics on token/time savings
✅ **Developers optimize**: P50/P95/P99 latencies highlight bottlenecks
✅ **Easy to implement**: Built on existing infrastructure
⚠️ **Not end-user facing**: Primarily for power users and monitoring

## Next Steps

1. **Monitor Daily**: Check `/metrics` to see how aOa performs
2. **Optimize Bottlenecks**: Use latency data to find slow operations
3. **Track ROI**: Calculate cost savings from token reductions
4. **Set Alerts**: Notify when accuracy or performance degrades
