#!/usr/bin/env python3
"""
aOa Intent Summary - UserPromptSubmit Hook

Shows branded intent summary when user submits a prompt.
Output: ⚡ AOA │ 136 intents │ 16 tags │ 34.0ms │ editing python searching
"""

import sys
import json
import os
import time
from urllib.request import Request, urlopen
from urllib.error import URLError

AOA_URL = os.environ.get("AOA_URL", "http://localhost:8080")

# ANSI colors
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def get_intent_stats():
    """Fetch intent stats from aOa."""
    start = time.time()

    try:
        req = Request(f"{AOA_URL}/intent/recent?since=3600&limit=50")
        with urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except (URLError, Exception):
        return None, 0

    elapsed_ms = (time.time() - start) * 1000
    return data, elapsed_ms


def format_output(data: dict, elapsed_ms: float) -> str:
    """Format the branded output line."""
    stats = data.get('stats', {})
    records = data.get('records', [])

    total = stats.get('total_records', 0)
    tags_count = stats.get('unique_tags', 0)

    # Get recent tags (last few records)
    recent_tags = set()
    for record in records[:10]:
        for tag in record.get('tags', []):
            recent_tags.add(tag.replace('#', ''))

    # Limit to 5 most relevant tags
    tags_str = ' '.join(list(recent_tags)[:5]) if recent_tags else 'learning...'

    # Build branded output
    parts = [
        f"{CYAN}{BOLD}⚡ aOa{RESET}",
        f"{total} intents",
        f"{tags_count} tags",
        f"{GREEN}{elapsed_ms:.1f}ms{RESET}",
    ]

    header = f" {DIM}│{RESET} ".join(parts)
    tags_display = f"{YELLOW}{tags_str}{RESET}"

    return f"{header} {DIM}│{RESET} {tags_display}"


def main():
    # Read stdin (hook input) but we don't need it
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    data, elapsed_ms = get_intent_stats()

    if data is None:
        # aOa not running - silent
        return

    if data.get('stats', {}).get('total_records', 0) == 0:
        # No intents yet - show minimal output
        print(f"{CYAN}{BOLD}⚡ aOa{RESET} {DIM}│{RESET} learning... {DIM}(use Claude to build intent){RESET}")
        return

    output = format_output(data, elapsed_ms)
    print(output)


if __name__ == "__main__":
    main()
