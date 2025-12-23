"""
aOa Scorer - File Ranking by Recency, Frequency, and Tag Affinity

Provides predictive file scoring for prefetch optimization.
"""

import time
from typing import Dict, List, Optional, Tuple

from .redis_client import RedisClient


class Scorer:
    """
    File scorer using multiple signals:
    - Recency: Unix timestamp of last access (higher = more recent)
    - Frequency: Count of accesses (higher = more frequent)
    - Tag Affinity: Score per tag association (higher = stronger affinity)
    """

    # Default weights for composite scoring
    DEFAULT_WEIGHTS = {
        'recency': 0.4,    # Recent files are important
        'frequency': 0.3,  # Frequently accessed files matter
        'tag': 0.3,        # Tag matches are relevant
    }

    # Decay settings
    RECENCY_HALF_LIFE = 3600  # 1 hour: recency score halves

    def __init__(self, redis_client: Optional[RedisClient] = None, db: Optional[int] = None):
        """
        Initialize scorer.

        Args:
            redis_client: Existing RedisClient instance (optional)
            db: Database number for testing (optional)
        """
        self.redis = redis_client or RedisClient(db=db)
        self.weights = self.DEFAULT_WEIGHTS.copy()

    # =========================================================================
    # Recording Access
    # =========================================================================

    def record_access(self, file_path: str, tags: Optional[List[str]] = None,
                      timestamp: Optional[int] = None) -> Dict[str, float]:
        """
        Record a file access, updating all scoring signals.

        Args:
            file_path: Path to the file being accessed
            tags: List of tags associated with this access
            timestamp: Unix timestamp (defaults to now)

        Returns:
            Dict with updated scores for each signal
        """
        ts = timestamp or int(time.time())
        tags = tags or []

        scores = {}

        # Update recency (set to timestamp - higher is more recent)
        recency_key = RedisClient.PREFIX_RECENCY
        self.redis.zadd(recency_key, ts, file_path)
        scores['recency'] = float(ts)

        # Update frequency (increment by 1)
        frequency_key = RedisClient.PREFIX_FREQUENCY
        scores['frequency'] = self.redis.zincrby(frequency_key, 1, file_path)

        # Update tag affinity (increment each tag's score for this file)
        for tag in tags:
            tag_key = f"{RedisClient.PREFIX_TAG}:{tag}"
            self.redis.zincrby(tag_key, 1, file_path)
            scores[f'tag:{tag}'] = self.redis.zscore(tag_key, file_path)

        return scores

    # =========================================================================
    # Score Retrieval
    # =========================================================================

    def get_recency_score(self, file_path: str) -> Optional[float]:
        """Get recency score for a file (timestamp of last access)."""
        return self.redis.zscore(RedisClient.PREFIX_RECENCY, file_path)

    def get_frequency_score(self, file_path: str) -> Optional[float]:
        """Get frequency score for a file (access count)."""
        return self.redis.zscore(RedisClient.PREFIX_FREQUENCY, file_path)

    def get_tag_score(self, file_path: str, tag: str) -> Optional[float]:
        """Get tag affinity score for a file and tag."""
        tag_key = f"{RedisClient.PREFIX_TAG}:{tag}"
        return self.redis.zscore(tag_key, file_path)

    # =========================================================================
    # Ranking
    # =========================================================================

    def get_ranked_files(self, tags: Optional[List[str]] = None,
                         limit: int = 10, db: Optional[int] = None) -> List[Dict]:
        """
        Get files ranked by composite score.

        Args:
            tags: Filter/boost by these tags (optional)
            limit: Maximum number of files to return
            db: Database number (for benchmark testing)

        Returns:
            List of dicts with 'file', 'score', and individual signal scores
        """
        import math

        if db is not None:
            self.redis.client.select(db)

        now = time.time()

        # Get all files from recency and frequency sets
        recency_files = self.redis.zrange(RedisClient.PREFIX_RECENCY, 0, -1,
                                          desc=True, withscores=True)
        frequency_files = self.redis.zrange(RedisClient.PREFIX_FREQUENCY, 0, -1,
                                            desc=True, withscores=True)

        # Build file -> scores map
        file_scores = {}

        # Process recency scores (normalize to 0-100 based on age)
        for file_path, timestamp in recency_files:
            age_seconds = now - timestamp
            # Exponential decay: score = 100 * e^(-age / half_life)
            # Half life = 1 hour = 3600 seconds
            recency_score = 100 * math.exp(-age_seconds / self.RECENCY_HALF_LIFE)
            file_scores[file_path] = {'recency': recency_score, 'frequency': 0, 'tags': {}}

        # Process frequency scores (already in reasonable range)
        max_freq = max((f[1] for f in frequency_files), default=1)
        for file_path, freq in frequency_files:
            # Normalize to 0-100 range
            freq_score = (freq / max_freq) * 100 if max_freq > 0 else 0
            if file_path not in file_scores:
                file_scores[file_path] = {'recency': 0, 'frequency': 0, 'tags': {}}
            file_scores[file_path]['frequency'] = freq_score

        # Process tag scores if tags specified
        if tags:
            for tag in tags:
                tag_key = f"{RedisClient.PREFIX_TAG}:{tag}"
                tag_files = self.redis.zrange(tag_key, 0, -1, desc=True, withscores=True)
                max_tag = max((f[1] for f in tag_files), default=1)
                for file_path, tag_score in tag_files:
                    # Normalize to 0-100 range
                    normalized_tag = (tag_score / max_tag) * 100 if max_tag > 0 else 0
                    if file_path not in file_scores:
                        file_scores[file_path] = {'recency': 0, 'frequency': 0, 'tags': {}}
                    file_scores[file_path]['tags'][tag] = normalized_tag

        # If no files, return empty
        if not file_scores:
            return []

        # Calculate composite scores
        for file_path, scores in file_scores.items():
            composite = (
                scores['recency'] * self.weights['recency'] +
                scores['frequency'] * self.weights['frequency']
            )

            # Add tag contribution
            if tags and scores['tags']:
                tag_weight = self.weights['tag'] / len(tags)
                for tag in tags:
                    composite += scores['tags'].get(tag, 0) * tag_weight

            scores['composite'] = composite

        # Sort by composite score and return top N
        sorted_files = sorted(file_scores.items(),
                              key=lambda x: x[1]['composite'],
                              reverse=True)[:limit]

        # Build response
        ranked_files = []
        for file_path, scores in sorted_files:
            entry = {
                'file': file_path,
                'score': round(scores['composite'], 4),
                'recency': round(scores['recency'], 2),
                'frequency': round(scores['frequency'], 2),
            }
            if tags and scores['tags']:
                entry['tags'] = {k: round(v, 2) for k, v in scores['tags'].items()}
            ranked_files.append(entry)

        return ranked_files

    def get_top_files_by_recency(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get files sorted by most recent access."""
        return self.redis.zrange(RedisClient.PREFIX_RECENCY, 0, limit - 1,
                                 desc=True, withscores=True)

    def get_top_files_by_frequency(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get files sorted by most frequent access."""
        return self.redis.zrange(RedisClient.PREFIX_FREQUENCY, 0, limit - 1,
                                 desc=True, withscores=True)

    def get_files_for_tag(self, tag: str, limit: int = 10) -> List[Tuple[str, float]]:
        """Get files with highest affinity for a tag."""
        tag_key = f"{RedisClient.PREFIX_TAG}:{tag}"
        return self.redis.zrange(tag_key, 0, limit - 1, desc=True, withscores=True)

    # =========================================================================
    # Weight Management
    # =========================================================================

    def set_weights(self, recency: float = None, frequency: float = None,
                    tag: float = None) -> Dict[str, float]:
        """
        Update scoring weights.

        Args:
            recency: Weight for recency signal (0.0-1.0)
            frequency: Weight for frequency signal (0.0-1.0)
            tag: Weight for tag affinity signal (0.0-1.0)

        Returns:
            Current weights after update
        """
        if recency is not None:
            self.weights['recency'] = max(0.0, min(1.0, recency))
        if frequency is not None:
            self.weights['frequency'] = max(0.0, min(1.0, frequency))
        if tag is not None:
            self.weights['tag'] = max(0.0, min(1.0, tag))

        return self.weights.copy()

    def get_weights(self) -> Dict[str, float]:
        """Get current scoring weights."""
        return self.weights.copy()

    # =========================================================================
    # Decay (P1-008)
    # =========================================================================

    def apply_decay(self, half_life_seconds: int = None) -> int:
        """
        Apply time-based decay to recency scores.

        This reduces scores for files that haven't been accessed recently,
        allowing frequently-but-not-recently accessed files to fade.

        Args:
            half_life_seconds: Time for score to decay by half (default: 1 hour)

        Returns:
            Number of files affected
        """
        half_life = half_life_seconds or self.RECENCY_HALF_LIFE
        now = int(time.time())

        # Lua script for atomic decay
        decay_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local half_life = tonumber(ARGV[2])

        local members = redis.call('ZRANGE', key, 0, -1, 'WITHSCORES')
        local count = 0

        for i = 1, #members, 2 do
            local member = members[i]
            local old_score = tonumber(members[i + 1])
            local age = now - old_score

            if age > 0 then
                -- Exponential decay: new_score = old_score * (0.5 ^ (age / half_life))
                local decay_factor = math.pow(0.5, age / half_life)
                local new_score = old_score * decay_factor

                redis.call('ZADD', key, new_score, member)
                count = count + 1
            end
        end

        return count
        """

        return self.redis.eval(decay_script,
                               [RedisClient.PREFIX_RECENCY],
                               [now, half_life])

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_stats(self) -> Dict:
        """Get statistics about current scoring state."""
        recency_count = self.redis.zcard(RedisClient.PREFIX_RECENCY)
        frequency_count = self.redis.zcard(RedisClient.PREFIX_FREQUENCY)

        # Count tag keys
        tag_keys = self.redis.keys(f"{RedisClient.PREFIX_TAG}:*")
        tag_count = len(tag_keys)

        total_tag_entries = sum(self.redis.zcard(k) for k in tag_keys)

        return {
            'files_tracked': recency_count,
            'frequency_entries': frequency_count,
            'tags_tracked': tag_count,
            'tag_associations': total_tag_entries,
            'weights': self.weights.copy(),
        }

    def clear_all(self) -> int:
        """Clear all scoring data. Use with caution!"""
        keys = []
        keys.extend(self.redis.keys(f"{RedisClient.PREFIX_RECENCY}*"))
        keys.extend(self.redis.keys(f"{RedisClient.PREFIX_FREQUENCY}*"))
        keys.extend(self.redis.keys(f"{RedisClient.PREFIX_TAG}:*"))
        keys.extend(self.redis.keys(f"{RedisClient.PREFIX_COMPOSITE}:*"))

        if keys:
            return self.redis.delete(*keys)
        return 0
