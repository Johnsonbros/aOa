#!/usr/bin/env python3
"""
aOa Intent Prefetch - PreToolUse Hook

Predicts related files before tool execution using temporal sequence learning.
Uses Markov chain-based predictions instead of just tag co-occurrence.

Only activates after learning from real usage patterns.
"""

import sys
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

# Read config from .aoa/home.json if available
HOOK_DIR = Path(__file__).parent
PROJECT_ROOT = HOOK_DIR.parent.parent
AOA_HOME_FILE = PROJECT_ROOT / ".aoa" / "home.json"

if AOA_HOME_FILE.exists():
    _config = json.loads(AOA_HOME_FILE.read_text())
    PROJECT_ID = _config.get("project_id", "default")
else:
    PROJECT_ID = "default"

# Status service URL (handles sequence predictions)
STATUS_URL = os.environ.get("STATUS_URL", "http://localhost:9998")
MIN_TRANSITIONS = 5  # Don't prefetch until we have enough sequence data


def get_sequence_stats() -> dict:
    """Check sequence learning statistics."""
    try:
        req = Request(f"{STATUS_URL}/sequence/stats?project_id={PROJECT_ID}")
        with urlopen(req, timeout=1) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except (URLError, Exception):
        return {}


def get_sequence_predictions(file_path: str, session_id: str) -> list:
    """
    Get sequence-based predictions for next files.

    Uses Markov chain transition probabilities learned from actual usage.
    Returns files sorted by probability with timing estimates.
    """
    try:
        # Use session context for richer predictions
        payload = json.dumps({
            "file": file_path,
            "session_id": session_id,
            "project_id": PROJECT_ID,
            "limit": 5
        }).encode('utf-8')

        req = Request(
            f"{STATUS_URL}/sequence/predict",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urlopen(req, timeout=1) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            predictions = data.get('predictions', [])

            # Return just the file paths for now
            # Each prediction has: from_file, to_file, probability, count, avg_time_delta
            return [p['to_file'] for p in predictions]

    except (URLError, Exception):
        return []


def get_related_files_fallback(file_path: str) -> list:
    """
    Fallback to tag-based co-occurrence if sequence data not available.

    This is the old method - used only when we don't have enough sequence data yet.
    """
    try:
        AOA_URL = os.environ.get("AOA_URL", "http://localhost:8080")

        # Get tags for this file
        req = Request(f"{AOA_URL}/intent/file?path={file_path}")
        with urlopen(req, timeout=1) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            tags = data.get('tags', [])

        if not tags:
            return []

        # Get files for the most common tag
        related = set()
        for tag in tags[:3]:  # Top 3 tags
            req = Request(f"{AOA_URL}/intent/files?tag={tag}")
            with urlopen(req, timeout=1) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                for f in data.get('files', []):
                    if f != file_path:
                        related.add(f)

        return list(related)[:5]  # Top 5 related files

    except (URLError, Exception):
        return []


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        return

    # Extract file path and session ID from tool input
    tool_input = data.get('tool_input', {})
    file_path = tool_input.get('file_path') or tool_input.get('path')
    session_id = data.get('session_id', '')

    if not file_path:
        return

    # Check if we have enough sequence data
    stats = get_sequence_stats()
    total_transitions = stats.get('total_transitions', 0)

    if total_transitions >= MIN_TRANSITIONS:
        # Use sequence-based predictions (Markov chains)
        related = get_sequence_predictions(file_path, session_id)
    else:
        # Fall back to tag-based co-occurrence
        related = get_related_files_fallback(file_path)

    if related:
        # Future: inject suggestions into Claude's context
        # For now, just output for debugging (visible in verbose mode)
        # Could enable with: print(f"[aOa] Predicted: {', '.join(related)}")
        pass


if __name__ == "__main__":
    main()
