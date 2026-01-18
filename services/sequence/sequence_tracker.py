#!/usr/bin/env python3
"""
aOa Temporal Sequence Learning

Implements Markov chain-based sequence tracking for predictive file access.
Tracks file access sequences, timing, and calculates transition probabilities.

Key Features:
- Sequential pattern tracking (not just co-occurrence)
- Timing-aware predictions (within 5 minutes)
- Transition probability matrix stored in Redis
- Efficient pruning of low-probability transitions

Redis Schema:
- sequences:{project_id}:{session_id} - List of file accesses with timestamps
- transitions:{project_id}:{file_path} - Sorted set of transitions with scores
- transition_counts:{project_id}:{file_path} - Hash of target file → count
- transition_timing:{project_id}:{file_path}:{target} - List of time deltas

Example:
After editing auth.py, 80% of time user edits auth_test.py within 5 minutes.
Redis: transitions:proj123:auth.py → {auth_test.py: 0.8, middleware.py: 0.15}
"""

import json
import time
import redis
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter


# Time window for "related" sequences (5 minutes)
TIME_WINDOW_SECONDS = 300

# Minimum transition count to be considered significant
MIN_TRANSITION_COUNT = 2

# Maximum transitions to store per file (pruning)
MAX_TRANSITIONS_PER_FILE = 20

# Decay factor for older sequences (0.95 = 5% decay per occurrence)
DECAY_FACTOR = 0.95


@dataclass
class FileAccess:
    """Represents a single file access event."""
    file_path: str
    timestamp: float
    tool: str
    session_id: str

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> 'FileAccess':
        d = json.loads(data)
        return cls(**d)


@dataclass
class Transition:
    """Represents a file-to-file transition with probability."""
    from_file: str
    to_file: str
    probability: float
    count: int
    avg_time_delta: float  # Average seconds between accesses

    def to_dict(self) -> dict:
        return asdict(self)


class SequenceTracker:
    """
    Tracks file access sequences and learns transition probabilities.

    Uses Markov chains to model P(file_B | file_A) - the probability
    of accessing file_B given that file_A was just accessed.
    """

    def __init__(self, redis_client: redis.Redis, project_id: str = "default"):
        self.redis = redis_client
        self.project_id = project_id

    # =========================================================================
    # Sequence Recording
    # =========================================================================

    def record_access(self, file_path: str, tool: str, session_id: str) -> None:
        """
        Record a file access and update transition probabilities.

        This is called from the intent-capture hook for every file access.
        It updates both the sequence history and transition probabilities.
        """
        if not file_path or file_path.startswith('pattern:') or file_path.startswith('cmd:'):
            return

        now = time.time()
        access = FileAccess(
            file_path=file_path,
            timestamp=now,
            tool=tool,
            session_id=session_id
        )

        # Get recent accesses in this session (within time window)
        sequence_key = f"sequences:{self.project_id}:{session_id}"
        recent = self._get_recent_accesses(sequence_key, now)

        # Record transitions from recent files to this file
        for prev_access in recent:
            time_delta = now - prev_access.timestamp
            if time_delta <= TIME_WINDOW_SECONDS:
                self._record_transition(
                    from_file=prev_access.file_path,
                    to_file=file_path,
                    time_delta=time_delta,
                    session_id=session_id
                )

        # Add this access to the sequence
        self.redis.lpush(sequence_key, access.to_json())

        # Keep only last 100 accesses per session
        self.redis.ltrim(sequence_key, 0, 99)

        # Expire session data after 24 hours
        self.redis.expire(sequence_key, 86400)

    def _get_recent_accesses(self, sequence_key: str, current_time: float) -> List[FileAccess]:
        """Get recent file accesses within the time window."""
        accesses = []
        raw_data = self.redis.lrange(sequence_key, 0, 9)  # Last 10 accesses

        for data in raw_data:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            try:
                access = FileAccess.from_json(data)
                if current_time - access.timestamp <= TIME_WINDOW_SECONDS:
                    accesses.append(access)
            except (json.JSONDecodeError, TypeError):
                continue

        return accesses

    def _record_transition(self, from_file: str, to_file: str,
                          time_delta: float, session_id: str) -> None:
        """
        Record a file-to-file transition and update probabilities.

        Updates:
        1. Transition count
        2. Timing information
        3. Probability scores (recalculated)
        """
        if from_file == to_file:
            return  # Skip self-transitions

        # Increment transition count
        count_key = f"transition_counts:{self.project_id}:{from_file}"
        new_count = self.redis.hincrby(count_key, to_file, 1)

        # Record timing
        timing_key = f"transition_timing:{self.project_id}:{from_file}:{to_file}"
        self.redis.lpush(timing_key, time_delta)
        self.redis.ltrim(timing_key, 0, 99)  # Keep last 100 timings
        self.redis.expire(timing_key, 86400 * 7)  # 7 days

        # Recalculate probabilities for this source file
        self._update_probabilities(from_file)

    def _update_probabilities(self, from_file: str) -> None:
        """
        Recalculate transition probabilities for a given source file.

        Uses raw counts to compute P(to_file | from_file) for all targets.
        Applies pruning to keep only top transitions.
        """
        count_key = f"transition_counts:{self.project_id}:{from_file}"
        counts = self.redis.hgetall(count_key)

        if not counts:
            return

        # Convert bytes to strings and ints
        counts = {
            k.decode('utf-8') if isinstance(k, bytes) else k:
            int(v) if isinstance(v, bytes) else v
            for k, v in counts.items()
        }

        # Calculate total transitions
        total = sum(counts.values())

        if total == 0:
            return

        # Calculate probabilities and store in sorted set
        transitions_key = f"transitions:{self.project_id}:{from_file}"

        # Clear old scores
        self.redis.delete(transitions_key)

        # Add new scores (sorted by probability)
        for to_file, count in counts.items():
            if count >= MIN_TRANSITION_COUNT:
                probability = count / total
                # Store as sorted set with probability as score
                self.redis.zadd(transitions_key, {to_file: probability})

        # Prune to top N transitions
        self.redis.zremrangebyrank(transitions_key, 0, -(MAX_TRANSITIONS_PER_FILE + 1))

        # Expire after 7 days
        self.redis.expire(transitions_key, 86400 * 7)

    # =========================================================================
    # Prediction
    # =========================================================================

    def predict_next_files(self, current_file: str, limit: int = 5) -> List[Transition]:
        """
        Predict the most likely next files based on current file.

        Returns list of transitions sorted by probability (highest first).
        Includes timing information for each transition.
        """
        if not current_file:
            return []

        transitions_key = f"transitions:{self.project_id}:{current_file}"

        # Get top transitions (sorted by score descending)
        results = self.redis.zrevrange(transitions_key, 0, limit - 1, withscores=True)

        if not results:
            return []

        transitions = []
        count_key = f"transition_counts:{self.project_id}:{current_file}"

        for to_file, probability in results:
            if isinstance(to_file, bytes):
                to_file = to_file.decode('utf-8')

            # Get count
            count = self.redis.hget(count_key, to_file)
            count = int(count) if count else 0

            # Get average timing
            avg_time = self._get_avg_time_delta(current_file, to_file)

            transitions.append(Transition(
                from_file=current_file,
                to_file=to_file,
                probability=float(probability),
                count=count,
                avg_time_delta=avg_time
            ))

        return transitions

    def predict_from_recent(self, session_id: str, limit: int = 10) -> List[Transition]:
        """
        Predict next files based on recent session activity.

        Combines predictions from multiple recent files, weighted by recency.
        """
        sequence_key = f"sequences:{self.project_id}:{session_id}"
        recent = self.redis.lrange(sequence_key, 0, 4)  # Last 5 accesses

        if not recent:
            return []

        # Collect predictions from each recent file, weighted by recency
        all_predictions = defaultdict(lambda: {'prob': 0.0, 'count': 0, 'time': 0.0})

        for idx, data in enumerate(recent):
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            try:
                access = FileAccess.from_json(data)
                predictions = self.predict_next_files(access.file_path, limit)

                # Weight by recency (most recent = highest weight)
                weight = DECAY_FACTOR ** idx

                for pred in predictions:
                    key = pred.to_file
                    all_predictions[key]['prob'] += pred.probability * weight
                    all_predictions[key]['count'] += pred.count
                    all_predictions[key]['time'] += pred.avg_time_delta
            except (json.JSONDecodeError, TypeError):
                continue

        # Convert to Transition objects and sort
        results = []
        for to_file, data in all_predictions.items():
            results.append(Transition(
                from_file="<recent>",
                to_file=to_file,
                probability=data['prob'],
                count=data['count'],
                avg_time_delta=data['time']
            ))

        results.sort(key=lambda t: t.probability, reverse=True)
        return results[:limit]

    def _get_avg_time_delta(self, from_file: str, to_file: str) -> float:
        """Get average time between from_file and to_file accesses."""
        timing_key = f"transition_timing:{self.project_id}:{from_file}:{to_file}"
        timings = self.redis.lrange(timing_key, 0, -1)

        if not timings:
            return 0.0

        # Convert to floats
        float_timings = []
        for t in timings:
            try:
                float_timings.append(float(t))
            except (ValueError, TypeError):
                continue

        if not float_timings:
            return 0.0

        return sum(float_timings) / len(float_timings)

    # =========================================================================
    # Analytics
    # =========================================================================

    def get_transition_matrix(self, file_path: str) -> Dict[str, float]:
        """Get all transitions from a file as a probability distribution."""
        transitions_key = f"transitions:{self.project_id}:{file_path}"
        results = self.redis.zrevrange(transitions_key, 0, -1, withscores=True)

        matrix = {}
        for to_file, prob in results:
            if isinstance(to_file, bytes):
                to_file = to_file.decode('utf-8')
            matrix[to_file] = float(prob)

        return matrix

    def get_top_sequences(self, min_length: int = 3, limit: int = 10) -> List[Dict]:
        """
        Get top file access sequences across all sessions.

        Returns common patterns like: auth.py → auth_test.py → config.py
        """
        # This would require scanning all sessions - expensive
        # For now, return empty (can be implemented with a background job)
        return []

    def get_sequence_stats(self) -> Dict:
        """Get statistics about sequence learning."""
        # Count total transitions
        pattern = f"transitions:{self.project_id}:*"
        transition_keys = list(self.redis.scan_iter(match=pattern, count=1000))

        total_sources = len(transition_keys)
        total_transitions = 0

        for key in transition_keys[:100]:  # Sample first 100 to avoid slowdown
            count = self.redis.zcard(key)
            total_transitions += count

        # Estimate total
        if total_sources > 100:
            total_transitions = int(total_transitions * (total_sources / 100))

        return {
            'total_source_files': total_sources,
            'total_transitions': total_transitions,
            'avg_transitions_per_file': total_transitions / total_sources if total_sources > 0 else 0,
        }


# =============================================================================
# Utility Functions
# =============================================================================

def format_prediction(transitions: List[Transition]) -> str:
    """Format predictions for human-readable output."""
    if not transitions:
        return "No predictions available"

    lines = ["Predicted next files:"]
    for idx, t in enumerate(transitions, 1):
        time_str = f"{int(t.avg_time_delta)}s" if t.avg_time_delta > 0 else "?"
        lines.append(
            f"  {idx}. {t.to_file} "
            f"({int(t.probability * 100)}% prob, "
            f"~{time_str} avg, "
            f"{t.count} times)"
        )
    return "\n".join(lines)
