#!/usr/bin/env python3
"""
aOa Intent Summary - UserPromptSubmit Hook

Shows branded intent summary when user submits a prompt.
Output: ⚡ aOa │ 25 intents │ 19 tags │ 39.7ms │ reading javascript configuration python searching

Reads from local status file (same as statusLine) with API fallback.
"""

import sys
import json
import os
import time
from urllib.request import Request, urlopen
from urllib.error import URLError

AOA_URL = os.environ.get("AOA_URL", "http://localhost:8080")
STATUS_FILE = os.environ.get("AOA_STATUS_FILE", os.path.expanduser("~/.aoa/status.json"))

# ANSI colors
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def get_local_status():
    """Read from local status file (same source as statusLine)."""
    start = time.time()

    if not os.path.exists(STATUS_FILE):
        return None, 0

    try:
        with open(STATUS_FILE, 'r') as f:
            data = json.load(f)
        elapsed_ms = (time.time() - start) * 1000
        return data, elapsed_ms
    except Exception:
        return None, 0


def get_api_stats():
    """Fetch intent stats from aOa API (fallback)."""
    start = time.time()

    try:
        req = Request(f"{AOA_URL}/intent/recent?since=3600&limit=50")
        with urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        elapsed_ms = (time.time() - start) * 1000

        # Convert API format to local format
        stats = data.get('stats', {})
        records = data.get('records', [])

        recent_tags = []
        for record in records[:10]:
            for tag in record.get('tags', []):
                if tag not in recent_tags:
                    recent_tags.append(tag)

        return {
            'intents': stats.get('total_records', 0),
            'tags': list(set(t for r in records for t in r.get('tags', [])))[:20],
            'recent': recent_tags[:5],
        }, elapsed_ms
    except (URLError, Exception):
        return None, 0


def format_output(data: dict, elapsed_ms: float) -> str:
    """Format the branded output line (matches statusLine format)."""
    intents = data.get('intents', 0)
    tags = data.get('tags', [])
    recent = data.get('recent', [])

    tags_count = len(tags)

    # Format recent tags (strip # prefix)
    recent_str = ' '.join(t.replace('#', '') for t in recent[:5]) if recent else 'learning...'

    # Build branded output - matches statusLine format
    parts = [
        f"{CYAN}{BOLD}⚡ aOa{RESET}",
        f"{intents} intents",
        f"{tags_count} tags",
        f"{GREEN}{elapsed_ms:.1f}ms{RESET}",
    ]

    header = f" {DIM}│{RESET} ".join(parts)
    tags_display = f"{YELLOW}{recent_str}{RESET}"

    return f"{header} {DIM}│{RESET} {tags_display}"


def main():
    # Read stdin (hook input) but we don't need it
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    # Try local status file first (same source as statusLine)
    data, elapsed_ms = get_local_status()

    # Fall back to API if local file doesn't exist
    if data is None:
        data, elapsed_ms = get_api_stats()

    if data is None:
        # Neither available - silent
        return

    if data.get('intents', 0) == 0:
        # No intents yet - show minimal output
        print(f"{CYAN}{BOLD}⚡ aOa{RESET} {DIM}│{RESET} learning...")
        return

    output = format_output(data, elapsed_ms)
    print(output)


if __name__ == "__main__":
    main()
