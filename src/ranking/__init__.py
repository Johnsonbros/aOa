"""
aOa Ranking Module - Predictive File Scoring

Provides file ranking based on:
- Recency: When was the file last accessed?
- Frequency: How often is the file accessed?
- Tag Affinity: Which tags are associated with the file?

Usage:
    from ranking import Scorer

    scorer = Scorer()
    scorer.record_access("/src/api/routes.py", tags=["api", "python"])

    top_files = scorer.get_ranked_files(tags=["api"], limit=10)
"""

from .redis_client import RedisClient
from .scorer import Scorer

__all__ = ['RedisClient', 'Scorer']
