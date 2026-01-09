#!/usr/bin/env python3
"""
aOa Intent Summary - UserPromptSubmit Hook

Shows branded intent summary when user submits a prompt.
Output: ⚡ aOa 87% │ 877 intents │ 0.1ms │ editing python searching
        ^^^^^^^^
        Accuracy is FIRST - bright and visible
"""

import sys
import json
import os
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

AOA_URL = os.environ.get("AOA_URL", "http://localhost:8080")

# Get project ID from .aoa/home.json
HOOK_DIR = Path(__file__).parent
PROJECT_ROOT = HOOK_DIR.parent.parent
AOA_HOME_FILE = PROJECT_ROOT / ".aoa" / "home.json"

if AOA_HOME_FILE.exists():
    _config = json.loads(AOA_HOME_FILE.read_text())
    PROJECT_ID = _config.get("project_id", "")
else:
    PROJECT_ID = ""

# ANSI colors - brighter for key metrics
CYAN = "\033[96m"       # Bright cyan for aOa brand
GREEN = "\033[92m"      # Bright green for good accuracy
YELLOW = "\033[93m"     # Bright yellow for tags
RED = "\033[91m"        # Bright red for low accuracy
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


def get_accuracy():
    """Fetch prediction accuracy from aOa metrics."""
    try:
        req = Request(f"{AOA_URL}/metrics")
        with urlopen(req, timeout=1) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            rolling = data.get('rolling', {})
            hit_pct = rolling.get('hit_at_5_pct', 0)
            evaluated = rolling.get('evaluated', 0)
            return hit_pct, evaluated
    except (URLError, Exception):
        return None, 0


def format_accuracy(hit_pct, evaluated):
    """Format accuracy with traffic lights."""
    if evaluated < 2:
        # Learning - grey (neutral, not broken)
        return f"{DIM}⚪{RESET}"
    elif evaluated < 3:
        # Calibrating - yellow light
        return f"{YELLOW}🟡{RESET}"
    else:
        # Ready - traffic light + percentage
        pct = int(hit_pct)
        if pct >= 80:
            return f"{GREEN}🟢 {BOLD}{pct}%{RESET}"
        else:
            # Yellow for anything below 80%
            return f"{YELLOW}🟡 {BOLD}{pct}%{RESET}"


def format_output(data: dict, elapsed_ms: float) -> str:
    """Format the branded output line."""
    stats = data.get('stats', {})
    records = data.get('records', [])

    total = stats.get('total_records', 0)

    # Get recent tags (last few records)
    recent_tags = set()
    for record in records[:10]:
        for tag in record.get('tags', []):
            recent_tags.add(tag.replace('#', ''))

    # Limit to 5 most relevant tags
    tags_str = ' '.join(list(recent_tags)[:5]) if recent_tags else 'calibrating...'

    # Get accuracy - THE KEY METRIC
    hit_pct, evaluated = get_accuracy()
    accuracy_str = format_accuracy(hit_pct, evaluated)

    # Build branded output - ACCURACY FIRST
    parts = [
        f"{CYAN}{BOLD}⚡ aOa{RESET} {accuracy_str}",  # Brand + accuracy together
        f"{total} intents",
        f"{GREEN}{elapsed_ms:.1f}ms{RESET}",
    ]

    header = f" {DIM}│{RESET} ".join(parts)
    tags_display = f"{YELLOW}{tags_str}{RESET}"

    return f"{header} {DIM}│{RESET} {tags_display}"


def get_recent_files(records: list) -> list:
    """Extract unique files from recent records that may need AI tagging."""
    files = set()
    for record in records[:10]:
        for f in record.get('files', []):
            # Must be absolute path, not a pattern, and have a file extension
            if (f.startswith('/') and
                not f.startswith('pattern:') and
                '.' in os.path.basename(f)):  # Has extension = is a file
                files.add(f)
    return list(files)[:5]


def request_haiku_tagging(files: list, prompt: str, session_id: str, project_id: str) -> dict:
    """Build Haiku tagging request as additionalContext."""
    if not files:
        return None

    file_list = ', '.join([os.path.basename(f) for f in files])
    prompt_snippet = prompt[:200] if prompt else "coding session"

    context = f"""## aOa Auto-Tag Request

Based on recent file activity, spawn a Haiku task to generate semantic tags.

Files: {file_list}
User context: {prompt_snippet}

Task(model="haiku", prompt="Generate 3-5 semantic hashtags for: {file_list}. Context: {prompt_snippet}. Focus on what the code does, domain, patterns. Return JSON array only: [\"#tag1\", \"#tag2\"]")

After getting tags, store via:
curl -s -X POST localhost:8080/intent -H "Content-Type: application/json" -d '{{"session_id": "{session_id}", "project_id": "{project_id}", "files": {json.dumps(files)}, "tags": <haiku_tags>}}'
"""

    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context
        }
    }


def main():
    # Read stdin for user prompt context
    prompt = ""
    session_id = ""
    try:
        hook_input = json.load(sys.stdin)
        prompt = hook_input.get('prompt', '')
        session_id = hook_input.get('session_id', '')
    except Exception:
        pass

    data, elapsed_ms = get_intent_stats()

    if data is None:
        # aOa not running - silent
        return

    if data.get('stats', {}).get('total_records', 0) == 0:
        # No intents yet - show minimal output
        print(f"{CYAN}{BOLD}⚡ aOa{RESET} {DIM}│{RESET} calibrating... {DIM}(use Claude to build intent){RESET}")
        return

    # Print status line to stderr (visible to user)
    output = format_output(data, elapsed_ms)
    print(output)

    # Request Haiku tagging for recent files (stdout JSON for Claude)
    records = data.get('records', [])
    recent_files = get_recent_files(records)
    if recent_files and prompt:
        haiku_request = request_haiku_tagging(recent_files, prompt, session_id, PROJECT_ID)
        if haiku_request:
            print(json.dumps(haiku_request))


if __name__ == "__main__":
    main()
