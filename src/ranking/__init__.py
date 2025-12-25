"""
aOa Ranking Module - Predictive File Scoring

Provides file ranking based on:
- Recency: When was the file last accessed?
- Frequency: How often is the file accessed?
- Tag Affinity: Which tags are associated with the file?

Phase 4 adds:
- WeightTuner: Thompson Sampling for weight optimization

Usage:
    from ranking import Scorer, WeightTuner

    scorer = Scorer()
    tuner = WeightTuner(scorer.redis)

    # Get optimized weights
    weights = tuner.select_weights()
    scorer.weights = weights

    # Record feedback after prediction evaluation
    tuner.record_feedback(hit=True)
"""

from .redis_client import RedisClient
from .scorer import Scorer, WeightTuner

__all__ = ['RedisClient', 'Scorer', 'WeightTuner']
