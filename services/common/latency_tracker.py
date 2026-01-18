#!/usr/bin/env python3
"""
Latency Tracker - Service performance monitoring

Tracks request latencies for all aOa services and calculates
P50, P95, and P99 percentiles using Redis sorted sets.

Usage:
    from common.latency_tracker import LatencyTracker

    tracker = LatencyTracker(redis_client)

    # Record a latency
    tracker.record('index', 'symbol_search', 4.5)  # 4.5ms

    # Get percentiles
    stats = tracker.get_percentiles('index')
    # Returns: {'p50': 3.2, 'p95': 12.5, 'p99': 24.8}
"""

import time
import redis
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class LatencyStats:
    """Latency statistics for a service operation."""
    service: str
    operation: str
    count: int
    p50: float
    p95: float
    p99: float
    min: float
    max: float
    avg: float


class LatencyTracker:
    """
    Track request latencies across services.

    Uses Redis sorted sets to store recent latencies (rolling window).
    Calculates percentiles efficiently without storing all data points.
    """

    # How many latency samples to keep per service (rolling window)
    MAX_SAMPLES = 1000

    # How long to keep latency data (seconds) - 1 hour
    TTL_SECONDS = 3600

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize latency tracker.

        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client

    def record(self, service: str, operation: str, latency_ms: float):
        """
        Record a latency measurement.

        Args:
            service: Service name (e.g., 'index', 'status', 'gateway')
            operation: Operation name (e.g., 'symbol_search', 'intent_track')
            latency_ms: Latency in milliseconds
        """
        now = time.time()

        # Store in sorted set: score = latency (for percentile calc)
        # Member = timestamp:latency (for uniqueness and cleanup)
        key = f"aoa:latency:{service}:{operation}"
        member = f"{now}:{latency_ms}"

        # Add to sorted set
        self.redis.zadd(key, {member: latency_ms})

        # Trim to keep only recent samples
        self.redis.zremrangebyrank(key, 0, -(self.MAX_SAMPLES + 1))

        # Set expiry
        self.redis.expire(key, self.TTL_SECONDS)

        # Also track aggregate stats
        stats_key = f"aoa:latency:stats:{service}:{operation}"
        pipe = self.redis.pipeline()
        pipe.hincrby(stats_key, 'count', 1)
        pipe.hincrbyfloat(stats_key, 'total_ms', latency_ms)
        pipe.expire(stats_key, self.TTL_SECONDS)
        pipe.execute()

    def get_percentiles(self, service: str, operation: str) -> Optional[Dict[str, float]]:
        """
        Calculate P50, P95, P99 percentiles for a service operation.

        Args:
            service: Service name
            operation: Operation name

        Returns:
            Dict with p50, p95, p99, min, max, avg, count
            None if no data available
        """
        key = f"aoa:latency:{service}:{operation}"

        # Get total count
        count = self.redis.zcard(key)
        if count == 0:
            return None

        # Calculate percentile ranks
        p50_rank = int(count * 0.50)
        p95_rank = int(count * 0.95)
        p99_rank = int(count * 0.99)

        # Get values at those ranks
        # zrange returns members sorted by score (latency)
        p50_member = self.redis.zrange(key, p50_rank, p50_rank)
        p95_member = self.redis.zrange(key, p95_rank, p95_rank)
        p99_member = self.redis.zrange(key, p99_rank, p99_rank)

        # Get min and max
        min_member = self.redis.zrange(key, 0, 0, withscores=True)
        max_member = self.redis.zrange(key, -1, -1, withscores=True)

        # Extract latencies from members (format: "timestamp:latency")
        def extract_latency(members):
            if not members:
                return 0.0
            member = members[0]
            if isinstance(member, tuple):  # withscores=True
                return float(member[1])
            if isinstance(member, bytes):
                member = member.decode('utf-8')
            return float(member.split(':')[-1])

        p50 = extract_latency(p50_member)
        p95 = extract_latency(p95_member)
        p99 = extract_latency(p99_member)
        min_val = extract_latency(min_member)
        max_val = extract_latency(max_member)

        # Get average from stats
        stats_key = f"aoa:latency:stats:{service}:{operation}"
        total_ms = float(self.redis.hget(stats_key, 'total_ms') or 0)
        avg = total_ms / count if count > 0 else 0.0

        return {
            'count': count,
            'p50': round(p50, 2),
            'p95': round(p95, 2),
            'p99': round(p99, 2),
            'min': round(min_val, 2),
            'max': round(max_val, 2),
            'avg': round(avg, 2),
        }

    def get_service_stats(self, service: str) -> Dict[str, Dict[str, float]]:
        """
        Get all operation stats for a service.

        Args:
            service: Service name

        Returns:
            Dict mapping operation names to their stats
        """
        # Find all operations for this service
        pattern = f"aoa:latency:{service}:*"
        keys = self.redis.keys(pattern)

        stats = {}
        for key in keys:
            # Extract operation name from key
            # Format: aoa:latency:service:operation
            if isinstance(key, bytes):
                key = key.decode('utf-8')

            parts = key.split(':')
            if len(parts) >= 4:
                operation = ':'.join(parts[3:])  # Handle operations with colons
                op_stats = self.get_percentiles(service, operation)
                if op_stats:
                    stats[operation] = op_stats

        return stats

    def get_all_services(self) -> List[str]:
        """Get list of all services being tracked."""
        pattern = "aoa:latency:*"
        keys = self.redis.keys(pattern)

        services = set()
        for key in keys:
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            parts = key.split(':')
            if len(parts) >= 3:
                services.add(parts[2])

        return sorted(list(services))

    def get_all_stats(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Get latency stats for all services and operations.

        Returns:
            Nested dict: {service: {operation: stats}}
        """
        all_stats = {}
        services = self.get_all_services()

        for service in services:
            all_stats[service] = self.get_service_stats(service)

        return all_stats

    def clear_service(self, service: str):
        """Clear all latency data for a service."""
        pattern = f"aoa:latency:{service}:*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)

        stats_pattern = f"aoa:latency:stats:{service}:*"
        stats_keys = self.redis.keys(stats_pattern)
        if stats_keys:
            self.redis.delete(*stats_keys)

    def clear_all(self):
        """Clear all latency tracking data."""
        pattern = "aoa:latency:*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
