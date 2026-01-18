# Adaptive Weight Learning (Thompson Sampling)

**Status**: ✅ Implemented (Phase 4)
**Impact**: High | **Effort**: Medium | **ROI**: Very Good

## Overview

aOa uses adaptive weight learning to automatically optimize prediction accuracy. Instead of hardcoded weights for recency, frequency, and tag affinity, the system learns which weight configurations work best for your specific project using Thompson Sampling - a principled multi-armed bandit algorithm.

## The Problem

Different projects need different ranking weights:
- **Test-heavy projects**: Frequently jump between test and implementation files → high recency weight
- **Monolithic codebases**: Work in the same core files repeatedly → high frequency weight
- **Microservices**: Navigate by tags/features → high tag weight

Previously, `scorer.py` used hardcoded weights (recency: 0.4, frequency: 0.3, tag: 0.3). This worked okay on average, but wasn't optimal for any specific project.

## The Solution

### Thompson Sampling

We implement Thompson Sampling with 8 discrete weight configurations ("arms"):

1. **recency-heavy** (0.5, 0.3, 0.2) - For rapidly changing context
2. **balanced-rf** (0.4, 0.4, 0.2) - Balance recency and frequency
3. **default** (0.4, 0.3, 0.3) - Original weights
4. **frequency-heavy** (0.3, 0.4, 0.3) - For repeated core files
5. **tag-heavy** (0.3, 0.3, 0.4) - For tag-driven navigation
6. **low-recency** (0.2, 0.4, 0.4) - Stable, tag-focused work
7. **high-rec-low-freq** (0.5, 0.2, 0.3) - Fast exploration
8. **equal** (0.33, 0.33, 0.34) - Uniform weights

Each arm maintains a Beta distribution representing its probability of success. When making a prediction:

1. **Sample** from each arm's Beta(α, β) distribution
2. **Select** the arm with the highest sample
3. **Predict** using that arm's weights
4. **Record** hit/miss feedback to update the arm's distribution

Over time, successful arms get higher α (successes), unsuccessful arms get higher β (failures), and the system naturally converges to the best weights for your project.

## Architecture

### Components Modified

1. **scorer.py** (`/services/ranking/scorer.py`)
   - `WeightTuner` class already existed (lines 417-591)
   - Implements Thompson Sampling with Beta distributions
   - Persists arm statistics in Redis

2. **indexer.py** (`/services/index/indexer.py`)
   - `/rank` endpoint: Uses tuner to select weights (default: adaptive=true)
   - `/predict/log`: Stores arm_idx with each prediction
   - `/predict/check`: Records hit/miss feedback to tuner
   - `/predict/finalize`: Records feedback for timed-out predictions
   - `/tuner/*` endpoints: Already implemented for API access

3. **CLI** (`/cli/aoa`)
   - New `aoa tuner` command with subcommands:
     - `aoa tuner stats` - Show all arm performance
     - `aoa tuner best` - Show best performing weights
     - `aoa tuner reset` - Reset learning to priors

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Prediction Request                        │
│                   GET /rank?adaptive=true                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              WeightTuner.select_weights()                    │
│  Sample from Beta(α,β) for each arm → select best sample    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│            Apply weights to Scorer.get_ranked_files()        │
│    Returns ranked files + arm_idx used                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              POST /predict/log (arm_idx stored)              │
│    Prediction logged with which arm was used                │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│         User reads file → POST /predict/check                │
│         Hit detected → tuner.record_feedback(hit=True)       │
│         Miss detected → tuner.record_feedback(hit=False)     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Beta distribution updated in Redis              │
│    Successful arms: α += 1  │  Failed arms: β += 1          │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### API

```bash
# Get adaptive weights for a prediction (exploration)
curl "localhost:8080/tuner/weights"
# {
#   "weights": {"recency": 0.5, "frequency": 0.3, "tag": 0.2},
#   "arm_idx": 0,
#   "arm_name": "recency-heavy"
# }

# Get best performing weights (exploitation)
curl "localhost:8080/tuner/best"
# {
#   "weights": {"recency": 0.4, "frequency": 0.4, "tag": 0.2},
#   "arm_idx": 1,
#   "arm_name": "balanced-rf",
#   "mean": 0.7834
# }

# Get all arm statistics
curl "localhost:8080/tuner/stats"
# {
#   "arms": [
#     {
#       "arm_idx": 1,
#       "name": "balanced-rf",
#       "weights": {"recency": 0.4, "frequency": 0.4, "tag": 0.2},
#       "alpha": 48,
#       "beta": 15,
#       "mean": 0.7619,
#       "samples": 61
#     },
#     ...
#   ],
#   "total_samples": 150
# }

# Record manual feedback
curl -X POST "localhost:8080/tuner/feedback" \
  -H "Content-Type: application/json" \
  -d '{"arm_idx": 1, "hit": true}'

# Reset all learning (caution!)
curl -X POST "localhost:8080/tuner/reset"
```

### CLI

```bash
# View arm performance
aoa tuner stats

# Adaptive Weight Learning (Thompson Sampling)
#
#   Total Samples: 150
#
# Arm Performance (sorted by success rate)
#
#   balanced-rf: 76% success (61 samples) - weights: r=0.4 f=0.4 t=0.2
#   recency-heavy: 72% success (43 samples) - weights: r=0.5 f=0.3 t=0.2
#   default: 68% success (28 samples) - weights: r=0.4 f=0.3 t=0.3
#
# All arms: aoa tuner stats --json

# View best weights
aoa tuner best

# Best Performing Weights
#
#   Arm:        balanced-rf
#   Success:    76%
#
#   Weights:
#     Recency:   0.4
#     Frequency: 0.4
#     Tag:       0.2

# Reset learning
aoa tuner reset
# This will reset all adaptive weight learning data.
# Are you sure? (y/N)
```

### Ranking with Adaptive Weights

```bash
# Use adaptive weights (default)
curl "localhost:8080/rank?tag=python&limit=5"

# Disable adaptive weights (use default)
curl "localhost:8080/rank?tag=python&limit=5&adaptive=false"
```

Response includes which arm was used:
```json
{
  "files": ["/src/main.py", "/src/api.py", ...],
  "details": [...],
  "weights": {"recency": 0.4, "frequency": 0.4, "tag": 0.2},
  "arm_idx": 1,
  "arm_name": "balanced-rf",
  "adaptive": true,
  "ms": 4.2
}
```

## Monitoring

### Prediction Stats

Prediction statistics now include tuner performance:

```bash
curl "localhost:8080/predict/stats"
```

```json
{
  "hits": 120,
  "misses": 30,
  "total": 150,
  "hit_rate": 80.0,
  "rolling": {
    "window_hours": 24,
    "total_predictions": 150,
    "evaluated": 150,
    "hits": 120,
    "hit_at_5": 0.80
  },
  "tuner": {
    "arms": [...],
    "total_samples": 150
  }
}
```

### Metrics Dashboard

```bash
aoa metrics
```

Shows overall accuracy including which weights are performing best.

## Key Benefits

1. **Personalized**: Learns your specific project's patterns
2. **Automatic**: No manual tuning required
3. **Principled**: Thompson Sampling is provably optimal for exploration-exploitation tradeoffs
4. **Transparent**: View arm performance anytime with `aoa tuner stats`
5. **Safe**: Defaults to balanced exploration; never gets stuck on bad weights

## Technical Details

### Thompson Sampling Properties

- **Regret Bound**: O(log T) expected regret over T rounds
- **Exploration**: Naturally balances trying new arms vs exploiting good ones
- **Bayesian**: Uses full posterior distribution, not just point estimates
- **Prior**: Starts with Beta(1,1) uniform prior (no bias)

### Redis Keys

```
aoa:tuner:arm:<idx>        Hash: {alpha: int, beta: int}
aoa:rolling:data:<pred_id> Hash: {..., arm_idx: str, hit: "0"|"1"}
```

### Prediction Lifecycle

1. **Log** - Prediction created with arm_idx
2. **Check** - File read triggers hit/miss detection
3. **Feedback** - Tuner updated immediately on hit
4. **Finalize** - Timed-out predictions (5 min) marked as misses

## Future Enhancements

- **Per-project tuning**: Separate arm stats per project UUID
- **Context-aware arms**: Different weights for different contexts (tests vs features)
- **Dynamic arm creation**: Add new weight combinations based on performance
- **Confidence intervals**: Show uncertainty in arm estimates

## References

- Thompson Sampling: [Chapelle & Li, 2011](https://papers.nips.cc/paper/2011/hash/e53a0a2978c28872a4505bdb51db06dc-Abstract.html)
- Beta-Bernoulli Bandits: [Agrawal & Goyal, 2012](https://arxiv.org/abs/1111.1797)
- Implementation: `services/ranking/scorer.py:417-591` (WeightTuner class)
