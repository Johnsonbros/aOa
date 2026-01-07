#!/usr/bin/env python3
"""
aOa Intent Capture - PostToolUse Hook

Captures tool usage and records intent to aOa.
Fire-and-forget, non-blocking, <10ms.
"""

import sys
import json
import re
import os
from urllib.request import Request, urlopen
from urllib.error import URLError
from datetime import datetime

AOA_URL = os.environ.get("AOA_URL", "http://localhost:8080")
# Find AOA data directory
# Option 1: Check for .aoa-config in project root (created by aoa init)
# Option 2: Use env var
# Option 3: Default to /tmp for isolated projects
HOOK_DIR = Path(__file__).parent
PROJECT_ROOT = HOOK_DIR.parent.parent  # .claude/hooks/ -> .claude/ -> project/
AOA_CONFIG = PROJECT_ROOT / ".aoa-config"

if AOA_CONFIG.exists():
    # Read AOA_DATA location from config
    import json
    config = json.loads(AOA_CONFIG.read_text())
    AOA_DATA = Path(config.get("data_dir", "/tmp/aoa"))
else:
    # Fallback: use /tmp (isolated per-project)
    AOA_DATA = Path(os.environ.get("AOA_DATA", "/tmp/aoa"))

AOA_DATA.mkdir(parents=True, exist_ok=True)
STATUS_FILE = os.environ.get("AOA_STATUS_FILE", str(AOA_DATA / "status.json"))

# Session ID fallback (overridden by Claude's session_id from stdin)
DEFAULT_SESSION_ID = os.environ.get("AOA_SESSION_ID", datetime.now().strftime("%Y%m%d"))

# Intent patterns: (regex, [tags])
INTENT_PATTERNS = [
    (r'auth|login|session|oauth|jwt|password', ['#authentication', '#security']),
    (r'test[s]?[/_]|_test\.|\bspec[s]?\b|pytest|unittest', ['#testing']),
    (r'config|settings|\.env|\.yaml|\.yml|\.json', ['#configuration']),
    (r'api|endpoint|route|handler|controller', ['#api']),
    (r'index|search|query|grep|find', ['#search']),
    (r'model|schema|entity|db|database|migration|sql', ['#data']),
    (r'component|view|template|page|ui|style|css|html', ['#frontend']),
    (r'deploy|docker|k8s|ci|cd|pipeline|github', ['#devops']),
    (r'error|exception|catch|throw|raise|fail', ['#errors']),
    (r'log|debug|trace|print|console', ['#logging']),
    (r'cache|redis|memory|store', ['#caching']),
    (r'async|await|promise|thread|concurrent', ['#async']),
    (r'hook|plugin|extension|middleware', ['#hooks']),
    (r'doc|readme|comment|docstring', ['#documentation']),
    (r'util|helper|common|shared|lib', ['#utilities']),
]

# Tool action tags
TOOL_TAGS = {
    'Read': '#reading',
    'Edit': '#editing',
    'Write': '#creating',
    'Bash': '#executing',
    'Grep': '#searching',
    'Glob': '#searching',
    'Task': '#delegating',
}


def extract_files(data: dict) -> list:
    """Extract file paths from tool input/output."""
    files = set()

    # Common field names for file paths
    for key in ['file_path', 'path', 'file', 'notebook_path']:
        if key in data.get('tool_input', {}):
            val = data['tool_input'][key]
            if val and isinstance(val, str):
                files.add(val)

    # Array of paths
    if 'paths' in data.get('tool_input', {}):
        for p in data['tool_input']['paths']:
            if p and isinstance(p, str):
                files.add(p)

    # Extract paths from bash commands
    if 'command' in data.get('tool_input', {}):
        cmd = data['tool_input']['command']
        # Match file paths in command
        matches = re.findall(r'/[\w./\-_]+\.(?:py|js|ts|go|rs|java|c|cpp|h|md|json|yaml|yml|sh|sql)', cmd)
        files.update(matches)

    # Extract from grep/glob patterns
    if 'pattern' in data.get('tool_input', {}):
        pattern = data['tool_input']['pattern']
        # If it looks like a path pattern, note it
        if '/' in pattern or '*' in pattern:
            files.add(f"pattern:{pattern}")

    return list(files)[:20]  # Limit to 20 files


def infer_tags(files: list, tool: str) -> list:
    """Infer intent tags from file paths and tool."""
    tags = set()

    # Add tool action tag
    if tool in TOOL_TAGS:
        tags.add(TOOL_TAGS[tool])

    # Match files against patterns
    combined = ' '.join(files).lower()
    for pattern, pattern_tags in INTENT_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            tags.update(pattern_tags)

    # Language tags based on extension
    for f in files:
        if f.endswith('.py'):
            tags.add('#python')
        elif f.endswith(('.js', '.ts', '.tsx', '.jsx')):
            tags.add('#javascript')
        elif f.endswith('.go'):
            tags.add('#go')
        elif f.endswith('.rs'):
            tags.add('#rust')
        elif f.endswith(('.c', '.cpp', '.h')):
            tags.add('#cpp')
        elif f.endswith('.java'):
            tags.add('#java')
        elif f.endswith('.sh'):
            tags.add('#shell')
        elif f.endswith('.sql'):
            tags.add('#sql')
        elif f.endswith('.md'):
            tags.add('#markdown')

    return list(tags)


def update_status_file(tool: str, files: list, tags: list):
    """Update local status file for status line display."""
    try:
        os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)

        # Read existing or create new
        status = {"intents": 0, "tags": [], "recent": [], "last_tool": None}
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r') as f:
                status = json.load(f)

        # Update
        status["intents"] = status.get("intents", 0) + 1
        status["last_tool"] = tool
        status["last_files"] = files[:3]

        # Merge tags (keep unique, limit to 20)
        all_tags = set(status.get("tags", []))
        all_tags.update(tags)
        status["tags"] = list(all_tags)[:20]

        # Recent activity (last 5 tags used)
        recent = status.get("recent", [])
        for tag in tags:
            if tag not in recent:
                recent.insert(0, tag)
        status["recent"] = recent[:5]

        status["updated"] = datetime.now().isoformat()

        with open(STATUS_FILE, 'w') as f:
            json.dump(status, f)
    except Exception:
        pass  # Never block


def check_prediction_hit(session_id: str, file_path: str):
    """Check if this file access was predicted (QW-3: Phase 2)."""
    if not file_path or file_path.startswith('pattern:'):
        return

    try:
        payload = json.dumps({
            'session_id': session_id,
            'file': file_path
        }).encode('utf-8')

        req = Request(
            f"{AOA_URL}/predict/check",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urlopen(req, timeout=1)
    except (URLError, Exception):
        pass  # Fire and forget


def send_intent(tool: str, files: list, tags: list, session_id: str, tool_use_id: str = None):
    """Send intent to aOa (fire-and-forget)."""
    if not files:
        return

    # Update local status file (for status line)
    update_status_file(tool, files, tags)

    # Check if this file was predicted (QW-3: Phase 2 hit/miss tracking)
    # Only check for Read operations - those are what we're trying to predict
    if tool == 'Read':
        for file_path in files:
            check_prediction_hit(session_id, file_path)

    payload = json.dumps({
        "session_id": session_id,
        "tool": tool,
        "files": files,
        "tags": tags,
        "tool_use_id": tool_use_id,  # Claude's correlation key
    }).encode('utf-8')

    try:
        req = Request(
            f"{AOA_URL}/intent",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urlopen(req, timeout=2)
    except (URLError, Exception):
        pass  # Graceful failure - never block Claude

    # Record file accesses for ranking (Phase 1)
    # Strip # from tags for scoring
    score_tags = [t.lstrip('#') for t in tags]
    for file_path in files:
        # Skip pattern entries and non-file paths
        if file_path.startswith('pattern:') or not file_path.startswith('/'):
            continue
        try:
            score_payload = json.dumps({
                "file": file_path,
                "tags": score_tags,
            }).encode('utf-8')
            req = Request(
                f"{AOA_URL}/rank/record",
                data=score_payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            urlopen(req, timeout=1)
        except (URLError, Exception):
            pass  # Never block


def main():
    # Debug mode: AOA_DEBUG=1 python3 intent-capture.py
    debug = os.environ.get("AOA_DEBUG", "0") == "1"

    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, Exception) as e:
        if debug:
            print(f"[aOa] JSON parse error: {e}", file=sys.stderr)
        return

    if debug:
        print(f"[aOa] Input: {json.dumps(data, indent=2)}", file=sys.stderr)

    # Extract Claude's correlation keys (QW-1: Phase 2 session linkage)
    session_id = data.get('session_id', DEFAULT_SESSION_ID)
    tool_use_id = data.get('tool_use_id')  # Claude's toolu_xxx ID

    tool = data.get('tool_name', data.get('tool', 'unknown'))
    files = extract_files(data)
    tags = infer_tags(files, tool)

    if debug:
        print(f"[aOa] Session: {session_id}, Tool: {tool}, Files: {files}, Tags: {tags}", file=sys.stderr)

    send_intent(tool, files, tags, session_id, tool_use_id)


if __name__ == "__main__":
    main()
