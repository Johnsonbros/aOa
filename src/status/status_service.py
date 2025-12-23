#!/usr/bin/env python3
"""
aOa Status Service
Real-time Claude Code session monitoring backed by Redis.

Tracks: model, tokens, cache, context, cost, weekly usage, time.

Usage:
    pip install flask redis
    python status_service.py
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from flask import Flask, jsonify, request, Response

import redis

app = Flask(__name__)

# =============================================================================
# Configuration
# =============================================================================

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
PORT = int(os.environ.get('STATUS_PORT', 9998))

# Model pricing (per 1M tokens) - as of late 2024
PRICING = {
    'claude-opus-4': {'input': 15.00, 'output': 75.00, 'cache_read': 1.50, 'cache_write': 18.75},
    'claude-sonnet-4': {'input': 3.00, 'output': 15.00, 'cache_read': 0.30, 'cache_write': 3.75},
    'claude-haiku-4': {'input': 0.25, 'output': 1.25, 'cache_read': 0.025, 'cache_write': 0.3125},
    # Aliases
    'opus-4': {'input': 15.00, 'output': 75.00, 'cache_read': 1.50, 'cache_write': 18.75},
    'sonnet-4': {'input': 3.00, 'output': 15.00, 'cache_read': 0.30, 'cache_write': 3.75},
    'haiku-4': {'input': 0.25, 'output': 1.25, 'cache_read': 0.025, 'cache_write': 0.3125},
}

# Context window sizes
CONTEXT_LIMITS = {
    'claude-opus-4': 200000,
    'claude-sonnet-4': 200000,
    'claude-haiku-4': 200000,
    'opus-4': 200000,
    'sonnet-4': 200000,
    'haiku-4': 200000,
}

# Redis keys
class Keys:
    SESSION = "aoa:session"           # Hash: session state
    METRICS = "aoa:metrics"           # Hash: running totals
    HISTORY = "aoa:history"           # List: recent events
    DAILY = "aoa:daily:{date}"        # Hash: daily stats
    WEEKLY = "aoa:weekly"             # Hash: weekly tracking
    PROJECT = "aoa:project:{name}"    # Hash: per-project totals

# =============================================================================
# Data Models
# =============================================================================

@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    
    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens
    
    @property
    def cache_hit_rate(self) -> float:
        total_input = self.input_tokens + self.cache_read_tokens
        if total_input == 0:
            return 0.0
        return self.cache_read_tokens / total_input

@dataclass
class SessionState:
    model: str = "unknown"
    context_used: int = 0
    context_max: int = 200000
    tokens: TokenUsage = field(default_factory=TokenUsage)
    session_cost: float = 0.0
    total_cost: float = 0.0
    session_start: float = 0.0
    last_activity: float = 0.0
    request_count: int = 0
    weekly_usage_pct: float = 0.0
    project: str = "default"

@dataclass
class StatusLine:
    """The formatted status line."""
    model: str
    context: str          # "42k/200k"
    tokens_in: str        # "12.4k"
    tokens_out: str       # "3.2k"
    cache_pct: str        # "89%"
    session_cost: str     # "$0.47"
    total_cost: str       # "$8.23"
    weekly_pct: str       # "78%"
    weekly_bar: str       # "████████░░"
    duration: str         # "00:34:12"
    
    def format(self) -> str:
        return (
            f"aOa ─ {self.model} │ "
            f"ctx: {self.context} │ "
            f"in: {self.tokens_in} out: {self.tokens_out} │ "
            f"cache: {self.cache_pct} │ "
            f"session: {self.session_cost} │ "
            f"total: {self.total_cost} │ "
            f"weekly: {self.weekly_bar} {self.weekly_pct} │ "
            f"{self.duration}"
        )

# =============================================================================
# Status Manager
# =============================================================================

class StatusManager:
    def __init__(self, redis_url: str):
        self.r = redis.from_url(redis_url, decode_responses=True)
        self._ensure_session()
    
    def _ensure_session(self):
        """Initialize session if needed."""
        if not self.r.hexists(Keys.SESSION, 'session_start'):
            now = time.time()
            self.r.hset(Keys.SESSION, mapping={
                'model': 'unknown',
                'context_used': 0,
                'input_tokens': 0,
                'output_tokens': 0,
                'cache_read_tokens': 0,
                'cache_write_tokens': 0,
                'session_cost': 0.0,
                'request_count': 0,
                'session_start': now,
                'last_activity': now,
                'project': 'default',
            })
    
    # =========================================================================
    # Event Recording
    # =========================================================================
    
    def record_request(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        context_used: int = 0,
    ):
        """Record a Claude API request."""
        now = time.time()
        
        # Calculate cost
        pricing = PRICING.get(model, PRICING['sonnet-4'])
        cost = (
            (input_tokens / 1_000_000) * pricing['input'] +
            (output_tokens / 1_000_000) * pricing['output'] +
            (cache_read_tokens / 1_000_000) * pricing['cache_read'] +
            (cache_write_tokens / 1_000_000) * pricing['cache_write']
        )
        
        # Update session
        pipe = self.r.pipeline()
        pipe.hset(Keys.SESSION, 'model', model)
        pipe.hset(Keys.SESSION, 'context_used', context_used)
        pipe.hset(Keys.SESSION, 'last_activity', now)
        pipe.hincrby(Keys.SESSION, 'input_tokens', input_tokens)
        pipe.hincrby(Keys.SESSION, 'output_tokens', output_tokens)
        pipe.hincrby(Keys.SESSION, 'cache_read_tokens', cache_read_tokens)
        pipe.hincrby(Keys.SESSION, 'cache_write_tokens', cache_write_tokens)
        pipe.hincrbyfloat(Keys.SESSION, 'session_cost', cost)
        pipe.hincrby(Keys.SESSION, 'request_count', 1)
        
        # Update totals
        pipe.hincrbyfloat(Keys.METRICS, 'total_cost', cost)
        pipe.hincrby(Keys.METRICS, 'total_requests', 1)
        pipe.hincrby(Keys.METRICS, 'total_input_tokens', input_tokens)
        pipe.hincrby(Keys.METRICS, 'total_output_tokens', output_tokens)
        
        # Daily tracking
        today = datetime.now().strftime('%Y-%m-%d')
        daily_key = Keys.DAILY.format(date=today)
        pipe.hincrbyfloat(daily_key, 'cost', cost)
        pipe.hincrby(daily_key, 'requests', 1)
        pipe.expire(daily_key, 86400 * 30)  # Keep 30 days
        
        # Weekly tracking
        pipe.hincrbyfloat(Keys.WEEKLY, 'cost', cost)
        pipe.hincrby(Keys.WEEKLY, 'requests', 1)
        
        # History
        event = json.dumps({
            'type': 'request',
            'model': model,
            'input': input_tokens,
            'output': output_tokens,
            'cache_read': cache_read_tokens,
            'cost': round(cost, 4),
            'ts': now,
        })
        pipe.lpush(Keys.HISTORY, event)
        pipe.ltrim(Keys.HISTORY, 0, 999)
        
        pipe.execute()
        
        return cost
    
    def record_model_switch(self, model: str):
        """Record a model change."""
        self.r.hset(Keys.SESSION, 'model', model)
        event = json.dumps({
            'type': 'model_switch',
            'model': model,
            'ts': time.time(),
        })
        self.r.lpush(Keys.HISTORY, event)
    
    def record_block(self, block_type: str, duration_seconds: int = 0):
        """Record a rate limit block."""
        event = json.dumps({
            'type': 'block',
            'block_type': block_type,
            'duration': duration_seconds,
            'ts': time.time(),
        })
        self.r.lpush(Keys.HISTORY, event)
        self.r.hincrby(Keys.METRICS, 'blocks_total', 1)
    
    def set_weekly_estimate(self, percentage: float):
        """Set estimated weekly usage percentage."""
        self.r.hset(Keys.WEEKLY, 'estimated_pct', percentage)
    
    def reset_session(self):
        """Reset session stats (keep totals)."""
        now = time.time()
        self.r.hset(Keys.SESSION, mapping={
            'context_used': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'cache_read_tokens': 0,
            'cache_write_tokens': 0,
            'session_cost': 0.0,
            'request_count': 0,
            'session_start': now,
            'last_activity': now,
        })
    
    def reset_weekly(self):
        """Reset weekly stats (call on week boundary)."""
        self.r.delete(Keys.WEEKLY)
    
    # =========================================================================
    # Status Retrieval
    # =========================================================================
    
    def get_session(self) -> SessionState:
        """Get current session state."""
        data = self.r.hgetall(Keys.SESSION)
        metrics = self.r.hgetall(Keys.METRICS)
        weekly = self.r.hgetall(Keys.WEEKLY)
        
        model = data.get('model', 'unknown')
        
        return SessionState(
            model=model,
            context_used=int(data.get('context_used', 0)),
            context_max=CONTEXT_LIMITS.get(model, 200000),
            tokens=TokenUsage(
                input_tokens=int(data.get('input_tokens', 0)),
                output_tokens=int(data.get('output_tokens', 0)),
                cache_read_tokens=int(data.get('cache_read_tokens', 0)),
                cache_write_tokens=int(data.get('cache_write_tokens', 0)),
            ),
            session_cost=float(data.get('session_cost', 0)),
            total_cost=float(metrics.get('total_cost', 0)),
            session_start=float(data.get('session_start', time.time())),
            last_activity=float(data.get('last_activity', time.time())),
            request_count=int(data.get('request_count', 0)),
            weekly_usage_pct=float(weekly.get('estimated_pct', 0)),
            project=data.get('project', 'default'),
        )
    
    def get_status_line(self) -> StatusLine:
        """Get formatted status line."""
        session = self.get_session()
        
        # Format helpers
        def fmt_tokens(n: int) -> str:
            if n >= 1000:
                return f"{n/1000:.1f}k"
            return str(n)
        
        def fmt_cost(c: float) -> str:
            return f"${c:.2f}"
        
        def fmt_duration(start: float) -> str:
            elapsed = int(time.time() - start)
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        def fmt_bar(pct: float, width: int = 10) -> str:
            filled = int(pct / 100 * width)
            return '█' * filled + '░' * (width - filled)
        
        # Context
        ctx_used_k = session.context_used // 1000
        ctx_max_k = session.context_max // 1000
        context = f"{ctx_used_k}k/{ctx_max_k}k"
        
        # Cache hit rate
        cache_pct = int(session.tokens.cache_hit_rate * 100)
        
        # Weekly percentage
        weekly_pct = min(100, session.weekly_usage_pct)
        
        return StatusLine(
            model=session.model.replace('claude-', ''),
            context=context,
            tokens_in=fmt_tokens(session.tokens.input_tokens),
            tokens_out=fmt_tokens(session.tokens.output_tokens),
            cache_pct=f"{cache_pct}%",
            session_cost=fmt_cost(session.session_cost),
            total_cost=fmt_cost(session.total_cost),
            weekly_pct=f"{int(weekly_pct)}%",
            weekly_bar=fmt_bar(weekly_pct),
            duration=fmt_duration(session.session_start),
        )
    
    def get_history(self, limit: int = 50) -> List[dict]:
        """Get recent events."""
        events = self.r.lrange(Keys.HISTORY, 0, limit - 1)
        return [json.loads(e) for e in events]


# =============================================================================
# Flask API
# =============================================================================

manager: Optional[StatusManager] = None

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'aoa-status'})

@app.route('/status')
def status():
    """Get formatted status line."""
    line = manager.get_status_line()
    return Response(line.format(), mimetype='text/plain')

@app.route('/status/json')
def status_json():
    """Get full status as JSON."""
    session = manager.get_session()
    return jsonify({
        'model': session.model,
        'context_used': session.context_used,
        'context_max': session.context_max,
        'tokens': {
            'input': session.tokens.input_tokens,
            'output': session.tokens.output_tokens,
            'cache_read': session.tokens.cache_read_tokens,
            'cache_write': session.tokens.cache_write_tokens,
            'cache_hit_rate': round(session.tokens.cache_hit_rate, 3),
        },
        'cost': {
            'session': round(session.session_cost, 4),
            'total': round(session.total_cost, 4),
        },
        'weekly_usage_pct': session.weekly_usage_pct,
        'session_duration_seconds': int(time.time() - session.session_start),
        'request_count': session.request_count,
        'project': session.project,
    })

@app.route('/status/line')
def status_line_only():
    """Get just the status line components."""
    line = manager.get_status_line()
    return jsonify(asdict(line))

@app.route('/session')
def session():
    """Get session info."""
    session = manager.get_session()
    return jsonify(asdict(session))

@app.route('/session/reset', methods=['POST'])
def session_reset():
    """Reset session stats."""
    manager.reset_session()
    return jsonify({'status': 'ok', 'message': 'Session reset'})

@app.route('/history')
def history():
    """Get recent events."""
    limit = int(request.args.get('limit', 50))
    events = manager.get_history(limit)
    return jsonify({'events': events})

@app.route('/event', methods=['POST'])
def record_event():
    """Record an event from Claude Code."""
    data = request.json
    event_type = data.get('type')
    
    if event_type == 'request':
        cost = manager.record_request(
            model=data.get('model', 'unknown'),
            input_tokens=data.get('input_tokens', 0),
            output_tokens=data.get('output_tokens', 0),
            cache_read_tokens=data.get('cache_read_tokens', 0),
            cache_write_tokens=data.get('cache_write_tokens', 0),
            context_used=data.get('context_used', 0),
        )
        return jsonify({'status': 'ok', 'cost': cost})
    
    elif event_type == 'model_switch':
        manager.record_model_switch(data.get('model', 'unknown'))
        return jsonify({'status': 'ok'})
    
    elif event_type == 'block':
        manager.record_block(
            block_type=data.get('block_type', 'unknown'),
            duration_seconds=data.get('duration', 0),
        )
        return jsonify({'status': 'ok'})
    
    elif event_type == 'weekly_estimate':
        manager.set_weekly_estimate(data.get('percentage', 0))
        return jsonify({'status': 'ok'})
    
    else:
        return jsonify({'status': 'error', 'message': f'Unknown event type: {event_type}'}), 400

@app.route('/weekly/reset', methods=['POST'])
def weekly_reset():
    """Reset weekly stats."""
    manager.reset_weekly()
    return jsonify({'status': 'ok', 'message': 'Weekly stats reset'})


# =============================================================================
# Main
# =============================================================================

def main():
    global manager
    
    print(f"Starting aOa Status Service")
    print(f"Redis: {REDIS_URL}")
    print(f"Port: {PORT}")
    
    manager = StatusManager(REDIS_URL)
    
    app.run(host='0.0.0.0', port=PORT, threaded=True)

if __name__ == '__main__':
    main()
