# aOa × Claude Ecosystem: Antigravity Integration Roadmap

> **Making aOa invisible infrastructure—maximum intelligence, zero friction**

---

## Executive Summary

This roadmap transforms aOa from a "tool you use" to "intelligence that just works." Three complementary integration layers make aOa native to the Claude ecosystem:

1. **Tool Interception** → Automatic Grep/Glob → aOa translation (invisible speedup)
2. **MCP Server** → Universal protocol for any Claude client (Desktop, Web, API)
3. **Agent SDK** → Custom agents with native aOa awareness (power users)

**Philosophy:** Additive, not replacement. Every phase adds capability without breaking existing functionality.

---

## Current State: What Works

aOa already integrates deeply with Claude Code:

| Integration Point | What It Does | File |
|-------------------|--------------|------|
| **UserPromptSubmit** | Predicts files before Claude asks | `predict-context.py` |
| **PreToolUse** | Prefetches likely files | `intent-prefetch.py` |
| **PostToolUse** | Captures intent, learns patterns | `intent-capture.py` |
| **StatusLine** | Shows savings, confidence | `aoa-status-line.sh` |

**The problem:** Users must explicitly use `aoa grep` instead of `Grep` tool to get benefits.

**The solution:** Make aOa the *default* intelligence layer, falling back to native tools when needed.

---

## Phase 1: Intelligent Tool Interception

**Goal:** When Claude calls `Grep` or `Glob`, automatically use aOa if faster/better.

**Why this is "antigravity":**
- Zero user action required
- Works Day 1 after install
- Transparent fallback if aOa isn't ready
- Teaches Claude to prefer aOa naturally (via speed/accuracy)

### Architecture

```
Claude Code: Grep(pattern="auth")
    ↓
PreToolUse Hook: intercept-search.py
    ├─ Health check: aoa health (5ms)
    ├─ Pattern analysis: "auth" → symbol search
    ├─ Translation: Grep → aoa grep auth
    ├─ Execute: aoa grep auth (8ms)
    └─ Inject result: hookSpecificOutput.replacementOutput

If aOa down:
    → Pass through to native Grep (transparent)
```

### Implementation

**File:** `services/hooks/intercept-search.py`

```python
#!/usr/bin/env python3
"""
Tool Interception Hook - PreToolUse
Auto-translates Grep/Glob to aOa when beneficial.
"""

import sys
import json
import subprocess
import os
from urllib.request import urlopen, Request
from urllib.error import URLError

AOA_URL = os.environ.get("AOA_URL", "http://localhost:8080")

def is_aoa_ready() -> bool:
    """Check if aOa services are running."""
    try:
        req = Request(f"{AOA_URL}/health")
        with urlopen(req, timeout=1) as resp:
            data = json.loads(resp.read().decode())
            return data.get('status') == 'ok'
    except (URLError, Exception):
        return False

def should_intercept_grep(tool_input: dict) -> bool:
    """Decide if this Grep call should use aOa."""
    pattern = tool_input.get('pattern', '')

    # Don't intercept regex patterns (aOa grep is literal/symbol)
    if any(c in pattern for c in r'.*+?[]{}()^$|\\'):
        return False

    # Don't intercept very short patterns (too generic)
    if len(pattern.strip()) < 3:
        return False

    return True

def translate_grep_to_aoa(tool_input: dict) -> str:
    """Translate Grep tool params to aoa grep command."""
    pattern = tool_input.get('pattern', '').strip()
    path = tool_input.get('path', '.')
    case_insensitive = tool_input.get('-i', False)

    cmd = ['aoa', 'grep']
    if case_insensitive:
        cmd.append('-i')
    cmd.append(pattern)

    return ' '.join(cmd)

def run_aoa_grep(cmd: str, cwd: str) -> dict:
    """Execute aoa grep and return formatted result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5
        )

        # Format output for Claude (same format as Grep tool)
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'exit_code': result.returncode
        }
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None

def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        sys.exit(0)  # Pass through

    tool_name = data.get('tool_name', '')
    tool_input = data.get('tool_input', {})

    # Only intercept Grep for now (Glob later)
    if tool_name != 'Grep':
        sys.exit(0)

    # Check if aOa is ready
    if not is_aoa_ready():
        sys.exit(0)  # Fallback to native Grep

    # Check if this pattern is suitable for aOa
    if not should_intercept_grep(tool_input):
        sys.exit(0)

    # Translate and execute
    cmd = translate_grep_to_aoa(tool_input)
    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
    result = run_aoa_grep(cmd, project_dir)

    if result is None:
        sys.exit(0)  # Fallback to native

    # Return replacement output (hijack the tool call)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "replacementOutput": result['stdout'],
            "metadata": {
                "intercepted": True,
                "original_tool": "Grep",
                "aoa_command": cmd,
                "performance_gain": "~95%"  # Could calculate actual
            }
        }
    }

    print(json.dumps(output))
    sys.exit(0)

if __name__ == "__main__":
    main()
```

**Update hooks.json:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Grep",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/intercept-search.py\"",
            "timeout": 3
          }
        ]
      },
      {
        "matcher": "Read|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/aoa-intent-prefetch.py\"",
            "timeout": 2
          }
        ]
      }
    ]
  }
}
```

### Testing

```bash
# Terminal 1: Watch intent capture
aoa intent

# Terminal 2: Test with Claude Code
claude: "Find all authentication code"

# Expected behavior:
# - Claude calls Grep(pattern="authentication")
# - Hook intercepts, runs aoa grep authentication
# - Result returned in <10ms (vs 2000ms+ for Grep)
# - Intent captured showing "intercepted: Grep → aoa grep"
```

### Success Metrics

- **Invisible:** User doesn't know interception happened
- **Fast:** <10ms for aOa path vs 500-2000ms native Grep
- **Accurate:** Results match or exceed native Grep
- **Safe:** Graceful fallback 100% of the time

---

## Phase 2: MCP Server Integration

**Goal:** Package aOa as a Model Context Protocol server for universal Claude client support.

**Why this matters:**
- Works with Claude Desktop (not just CLI)
- Works with Claude Code Web
- Works with any MCP-compatible client
- Standardized interface (tools, resources, prompts)

### Architecture

```
MCP Client (Claude Desktop/Web/API)
    ↓
aOa MCP Server (stdio or SSE)
    ↓
┌─────────────────────────────────────┐
│ Tools                               │
├─────────────────────────────────────┤
│ aoa_grep(query, limit)              │
│ aoa_predict(keywords)               │
│ aoa_hot_files(limit)                │
│ aoa_intent_recent(count)            │
│ aoa_health()                        │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ Resources                           │
├─────────────────────────────────────┤
│ intent://recent                     │
│ files://hot                         │
│ files://predicted?kw=auth           │
│ context://current                   │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ Prompts                             │
├─────────────────────────────────────┤
│ find_code(concept)                  │
│ explore_intent(tag)                 │
│ get_related_files(file)             │
└─────────────────────────────────────┘
```

### Implementation

**File:** `mcp/aoa-server.py`

```python
#!/usr/bin/env python3
"""
aOa MCP Server
Exposes aOa intelligence via Model Context Protocol.

Usage:
  # stdio mode (for Claude Desktop)
  python3 aoa-server.py

  # SSE mode (for web clients)
  python3 aoa-server.py --sse --port 8081
"""

import json
import sys
import subprocess
import os
from typing import Any, Optional

# MCP SDK (anthropic/mcp-python)
# pip install mcp
from mcp.server import Server
from mcp.types import Tool, Resource, Prompt, TextContent

AOA_URL = os.environ.get("AOA_URL", "http://localhost:8080")

app = Server("aoa")

# =============================================================================
# Tools
# =============================================================================

@app.tool()
async def aoa_grep(query: str, limit: int = 20) -> list[dict]:
    """
    Semantic grep across the codebase.
    Returns file:line locations with confidence scores.

    Args:
        query: Search term (symbol, keyword, or phrase)
        limit: Maximum results to return
    """
    cmd = f"aoa grep '{query}' | head -n {limit}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    # Parse output: "  path/file.py:123"
    hits = []
    for line in result.stdout.split('\n'):
        line = line.strip()
        if ':' in line and not line.startswith('⚡'):
            parts = line.rsplit(':', 1)
            if len(parts) == 2:
                hits.append({
                    'file': parts[0],
                    'line': parts[1],
                    'query': query
                })

    return hits

@app.tool()
async def aoa_predict(keywords: str, limit: int = 5) -> list[dict]:
    """
    Predict relevant files based on keywords.
    Returns files with confidence scores and snippets.

    Args:
        keywords: Comma-separated keywords
        limit: Maximum files to return
    """
    import urllib.request
    url = f"{AOA_URL}/predict?keywords={keywords}&limit={limit}&snippet_lines=10"

    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            data = json.loads(resp.read().decode())
            return data.get('files', [])
    except Exception:
        return []

@app.tool()
async def aoa_hot_files(limit: int = 10) -> list[dict]:
    """
    Get most frequently accessed files in this session.

    Args:
        limit: Maximum files to return
    """
    import urllib.request
    url = f"{AOA_URL}/hot?limit={limit}"

    try:
        with urllib.request.urlopen(url, timeout=1) as resp:
            data = json.loads(resp.read().decode())
            return data.get('files', [])
    except Exception:
        return []

@app.tool()
async def aoa_intent_recent(count: int = 10) -> list[dict]:
    """
    Get recent intent captures (what Claude has been working on).

    Args:
        count: Number of recent intents to return
    """
    import urllib.request
    url = f"{AOA_URL}/intent/recent?limit={count}"

    try:
        with urllib.request.urlopen(url, timeout=1) as resp:
            data = json.loads(resp.read().decode())
            return data.get('intents', [])
    except Exception:
        return []

@app.tool()
async def aoa_health() -> dict:
    """Check if aOa services are running and healthy."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"{AOA_URL}/health", timeout=1) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"status": "error", "message": str(e)}

# =============================================================================
# Resources
# =============================================================================

@app.resource("intent://recent")
async def get_recent_intents() -> str:
    """Recent intent captures (last 20 interactions)."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"{AOA_URL}/intent/recent?limit=20", timeout=2) as resp:
            data = json.loads(resp.read().decode())
            intents = data.get('intents', [])

            lines = ["# Recent aOa Intents\n"]
            for intent in intents:
                tool = intent.get('tool', 'unknown')
                files = ', '.join(intent.get('files', [])[:3])
                tags = ' '.join(intent.get('tags', [])[:5])
                lines.append(f"- **{tool}**: {files} {tags}")

            return '\n'.join(lines)
    except Exception:
        return "# aOa Intents\n\n*Service unavailable*"

@app.resource("files://hot")
async def get_hot_files() -> str:
    """Most frequently accessed files (top 15)."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"{AOA_URL}/hot?limit=15", timeout=1) as resp:
            data = json.loads(resp.read().decode())
            files = data.get('files', [])

            lines = ["# Hot Files (Most Accessed)\n"]
            for i, file_info in enumerate(files, 1):
                path = file_info.get('path', 'unknown')
                score = file_info.get('score', 0)
                lines.append(f"{i}. `{path}` (score: {score:.1f})")

            return '\n'.join(lines)
    except Exception:
        return "# Hot Files\n\n*Service unavailable*"

# =============================================================================
# Prompts
# =============================================================================

@app.prompt()
async def find_code(concept: str) -> str:
    """
    Find code related to a concept using semantic search.

    Args:
        concept: The concept to search for (e.g., "authentication", "user login")
    """
    # Call aoa_grep tool and format results
    hits = await aoa_grep(concept, limit=10)

    if not hits:
        return f"No code found for concept: {concept}"

    lines = [f"# Code Related to: {concept}\n"]
    for hit in hits:
        lines.append(f"- `{hit['file']}:{hit['line']}`")

    lines.append(f"\n*Found {len(hits)} locations. Use Read tool to examine.*")
    return '\n'.join(lines)

# =============================================================================
# Server
# =============================================================================

if __name__ == "__main__":
    import asyncio

    # Run stdio server
    asyncio.run(app.run())
```

**MCP Server Configuration:**

**File:** `mcp/config.json`

```json
{
  "mcpServers": {
    "aoa": {
      "command": "python3",
      "args": ["/path/to/aoa/mcp/aoa-server.py"],
      "env": {
        "AOA_URL": "http://localhost:8080"
      }
    }
  }
}
```

### Installation for Claude Desktop

```bash
# 1. Install MCP SDK
pip install mcp

# 2. Copy aoa-server.py to global location
cp mcp/aoa-server.py ~/.aoa/mcp/

# 3. Add to Claude Desktop config
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# Windows: %APPDATA%/Claude/claude_desktop_config.json

{
  "mcpServers": {
    "aoa": {
      "command": "python3",
      "args": ["~/.aoa/mcp/aoa-server.py"],
      "env": {
        "AOA_URL": "http://localhost:8080"
      }
    }
  }
}

# 4. Restart Claude Desktop
# Now aOa tools are available: aoa_grep, aoa_predict, etc.
```

### Usage in Claude Desktop

```
User: "Use aoa_grep to find all authentication code"

Claude: [Calls aoa_grep tool with query="authentication"]
        Returns: 15 hits in 8ms

        I found authentication code in these locations:
        - src/auth/login.py:45
        - src/middleware/auth.py:89
        - tests/test_auth.py:23
        ...
```

---

## Phase 3: Agent SDK Integration

**Goal:** Create custom agents that use aOa intelligence natively.

### Example Agent: "Explore"

**File:** `agents/explore.py`

```python
"""
Explore Agent - aOa-aware codebase explorer
Uses aOa predictions, hot files, and intent clusters before searching.
"""

from claude_agent_sdk import Agent, tools

class ExploreAgent(Agent):
    """Intelligent codebase explorer powered by aOa."""

    def __init__(self):
        super().__init__(
            name="explore",
            description="Explore codebase using aOa semantic intelligence"
        )
        self.aoa_available = self.check_aoa()

    def check_aoa(self) -> bool:
        """Check if aOa services are running."""
        import subprocess
        result = subprocess.run(['aoa', 'health'], capture_output=True)
        return result.returncode == 0

    async def run(self, task: str):
        """Execute exploration task with aOa intelligence."""

        # Step 1: Check aOa predictions
        if self.aoa_available:
            predictions = await self.get_aoa_predictions(task)
            if predictions:
                self.log(f"aOa predicted {len(predictions)} relevant files")
                await self.examine_files(predictions)
                return

        # Step 2: Use hot files as starting point
        hot_files = await self.get_hot_files()
        if hot_files:
            self.log(f"Starting with {len(hot_files)} hot files")
            await self.examine_files(hot_files)
            return

        # Step 3: Fallback to semantic grep
        results = await self.aoa_grep(task)
        await self.examine_files(results)

    async def get_aoa_predictions(self, keywords: str) -> list:
        """Get aOa predictions for keywords."""
        import subprocess
        result = subprocess.run(
            ['aoa', 'predict', keywords],
            capture_output=True,
            text=True
        )
        # Parse output...
        return []

    async def aoa_grep(self, query: str) -> list:
        """Search using aOa grep."""
        import subprocess
        result = subprocess.run(
            ['aoa', 'grep', query],
            capture_output=True,
            text=True
        )
        # Parse file:line results...
        return []
```

---

## Integration Benefits Matrix

| Phase | User Effort | Speed Gain | Universal Support | Power User |
|-------|-------------|------------|-------------------|------------|
| **Tool Interception** | 0% (automatic) | 95% | CLI only | ⭐⭐ |
| **MCP Server** | 5% (one-time config) | 90% | All clients | ⭐⭐⭐ |
| **Agent SDK** | 20% (custom agents) | 98% | CLI + custom | ⭐⭐⭐⭐⭐ |

---

## Implementation Timeline

### Week 1: Tool Interception
- [ ] Implement `intercept-search.py` hook
- [ ] Add health check + fallback logic
- [ ] Update `hooks.json` with PreToolUse interceptor
- [ ] Test with sample projects
- [ ] Document behavior in CLAUDE.md

### Week 2-3: MCP Server
- [ ] Implement `aoa-server.py` with MCP SDK
- [ ] Add tools: grep, predict, hot_files, intent_recent
- [ ] Add resources: intent://recent, files://hot
- [ ] Add prompts: find_code, explore_intent
- [ ] Test with Claude Desktop
- [ ] Create installation guide

### Week 4-5: Agent SDK
- [ ] Create ExploreAgent example
- [ ] Create RefactorAgent example
- [ ] Document agent patterns
- [ ] Publish to templates/examples
- [ ] Create video walkthrough

---

## Success Criteria

### Phase 1 (Tool Interception)
- ✅ 95%+ of Grep calls auto-routed to aOa
- ✅ <10ms response time for aOa path
- ✅ 100% graceful fallback when aOa unavailable
- ✅ Zero user complaints about behavior changes

### Phase 2 (MCP Server)
- ✅ Works in Claude Desktop without errors
- ✅ All tools callable from any MCP client
- ✅ Resources update in real-time
- ✅ Installation guide is <5 steps

### Phase 3 (Agent SDK)
- ✅ 3+ example agents published
- ✅ Documentation with code samples
- ✅ Community adoption (other developers use patterns)

---

## Rollout Strategy

### For Existing Users
```bash
# Update aOa (pulls new hooks + MCP server)
cd ~/.aoa && git pull && ./install.sh

# Enable tool interception (automatic - just update hooks)
cd your-project && aoa init --upgrade

# Enable MCP server (optional - for Claude Desktop users)
aoa mcp setup
```

### For New Users
```bash
# One command - gets everything
curl -sSL https://get-aoa.dev | bash

# Then in any project
cd your-project && aoa init
```

---

## Technical Debt Prevention

1. **Docker Parity Rule** - All hooks must work in both docker-compose and monolithic modes
2. **Graceful Degradation** - Every integration point must have a fallback
3. **Performance Budget** - Hooks must complete in <100ms (including network calls)
4. **Testing Matrix** - Test on macOS, Linux, Windows WSL
5. **Documentation First** - Write docs before implementing (README-driven development)

---

## Questions for User

Before implementing, clarify:

1. **Priority:** Which phase to start with? (Recommend: Phase 1 → fast win)
2. **MCP SDK:** Do you want to use official `anthropic/mcp-python` or build custom?
3. **Breaking Changes:** OK to update hook signatures if needed?
4. **Telemetry:** Should we track interception hit/miss rates?
5. **Community:** Open source the MCP server as a separate repo?

---

## Next Steps

Once you approve the approach:

1. **I'll implement Phase 1** (Tool Interception) - ~2 hours work
2. **Test with real workflows** - verify savings, accuracy
3. **Document in CLAUDE.md** - update instructions
4. **Commit + Push to branch** - `claude/integrate-claude-ecosystem-VeUJl`
5. **Create PR** - with before/after metrics

**Ready to proceed?** 🚀
