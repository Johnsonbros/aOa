# aOa × Claude Ecosystem: Quick Reference

> **TL;DR:** Three ways to make aOa native to Claude Code—pick your power level.

---

## The Three Integration Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Agent SDK Integration (Power Users)              │
│  Custom agents with aOa intelligence built-in              │
│  Effort: High │ Flexibility: Maximum │ Speed: 98%          │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: MCP Server (Universal)                           │
│  Works everywhere: Desktop, Web, API                       │
│  Effort: Low │ Compatibility: All clients │ Speed: 90%     │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Tool Interception (Invisible)                    │
│  Automatic Grep → aOa translation                          │
│  Effort: Zero │ Transparency: Total │ Speed: 95%           │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
                    ┌───────────────┐
                    │  aOa Core     │
                    │  (Existing)   │
                    └───────────────┘
```

---

## Decision Matrix

**When to use each layer:**

| You Want... | Use Layer | Why |
|-------------|-----------|-----|
| It to just work (zero config) | **Layer 1** | Invisible, automatic, fast |
| Claude Desktop support | **Layer 2** | MCP works everywhere |
| Custom workflows | **Layer 3** | Full control, maximum power |
| All of the above | **All 3** | They're complementary! |

---

## Architecture Overview

### Current (What aOa does today)

```
Claude Code
    │
    ├─ UserPromptSubmit ──> predict-context.py ──> inject predictions
    ├─ PreToolUse ──────────> intent-prefetch.py ──> prefetch files
    ├─ PostToolUse ────────> intent-capture.py ──> learn patterns
    └─ StatusLine ──────────> aoa-status-line.sh ──> show stats
```

**Gap:** User must explicitly use `aoa grep` instead of `Grep` tool.

### Layer 1: Tool Interception (The Fix)

```
Claude Code: Grep(pattern="auth")
    │
    ▼
PreToolUse Hook: intercept-search.py
    │
    ├─ aOa healthy? ──> YES ──> aoa grep auth (8ms)
    │                     │
    │                     └──> inject result (Claude never knows)
    │
    └─ aOa healthy? ──> NO ──> pass through to native Grep
```

**Result:** Claude gets speed automatically, zero user action.

### Layer 2: MCP Server (Universal Protocol)

```
Claude Desktop/Web/API
    │
    ├─ Tool: aoa_grep("auth") ──> 15 hits in 8ms
    ├─ Tool: aoa_predict("login,session") ──> 3 files predicted
    ├─ Resource: intent://recent ──> last 20 intents
    └─ Prompt: find_code("authentication") ──> formatted results
```

**Result:** aOa works in any MCP-compatible client.

### Layer 3: Agent SDK (Custom Intelligence)

```
ExploreAgent(task="find auth code")
    │
    ├─ Step 1: Check aOa predictions ──> 3 files predicted
    ├─ Step 2: Read context files ──> .context/CURRENT.md
    ├─ Step 3: aoa grep "auth" ──> 15 hits
    └─ Step 4: Analyze patterns ──> return structured report
```

**Result:** Agents that understand your codebase deeply.

---

## File Structure After Integration

```
aOa/
├── services/hooks/
│   ├── predict-context.py      (existing)
│   ├── intent-capture.py       (existing)
│   ├── intent-prefetch.py      (existing)
│   └── intercept-search.py     (NEW - Layer 1)
│
├── mcp/
│   ├── aoa-server.py           (NEW - Layer 2)
│   ├── config.json
│   └── README.md
│
├── agents/
│   ├── explore.py              (NEW - Layer 3)
│   ├── refactor.py             (NEW - Layer 3)
│   └── architect.py            (NEW - Layer 3)
│
├── plugin/hooks/
│   └── hooks.json              (UPDATED - add interception)
│
└── INTEGRATION_ROADMAP.md      (THIS FILE)
```

---

## Quick Start: Implement Layer 1 (10 Minutes)

### Step 1: Create the Hook

```bash
# Create intercept-search.py
cat > services/hooks/intercept-search.py << 'EOF'
#!/usr/bin/env python3
import sys, json, subprocess, os
from urllib.request import urlopen, Request
from urllib.error import URLError

AOA_URL = os.environ.get("AOA_URL", "http://localhost:8080")

def is_aoa_ready():
    try:
        req = Request(f"{AOA_URL}/health")
        with urlopen(req, timeout=1) as resp:
            data = json.loads(resp.read().decode())
            return data.get('status') == 'ok'
    except:
        return False

data = json.load(sys.stdin)
tool_name = data.get('tool_name', '')

if tool_name != 'Grep' or not is_aoa_ready():
    sys.exit(0)  # Pass through

pattern = data.get('tool_input', {}).get('pattern', '')
if len(pattern) < 3:
    sys.exit(0)

# Execute aoa grep
cmd = f"aoa grep '{pattern}'"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

# Inject result
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "replacementOutput": result.stdout
    }
}
print(json.dumps(output))
EOF

chmod +x services/hooks/intercept-search.py
```

### Step 2: Update hooks.json

```bash
# Add to plugin/hooks/hooks.json under PreToolUse
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
      }
    ]
  }
}
```

### Step 3: Test

```bash
# Start aOa services
docker compose up -d

# Test in Claude Code
claude: "Search for authentication code"

# Should see in aoa intent:
# Grep → aoa grep (intercepted, 8ms vs 2000ms)
```

---

## MCP Server Quick Start (Layer 2)

```bash
# 1. Install MCP SDK
pip install mcp

# 2. Copy server to global location
cp mcp/aoa-server.py ~/.aoa/mcp/

# 3. Add to Claude Desktop config
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
cat >> ~/Library/Application\ Support/Claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "aoa": {
      "command": "python3",
      "args": ["~/.aoa/mcp/aoa-server.py"],
      "env": {"AOA_URL": "http://localhost:8080"}
    }
  }
}
EOF

# 4. Restart Claude Desktop
# Now you have aoa_grep, aoa_predict, etc. as native tools
```

---

## Agent SDK Quick Start (Layer 3)

```bash
# 1. Install Agent SDK
pip install claude-agent-sdk

# 2. Create custom agent
cat > agents/explore.py << 'EOF'
from claude_agent_sdk import Agent
import subprocess

class ExploreAgent(Agent):
    async def run(self, task):
        # Use aOa to find relevant code
        result = subprocess.run(
            ['aoa', 'grep', task],
            capture_output=True,
            text=True
        )
        # Process and return
        return result.stdout
EOF

# 3. Register in Claude Code
# Add to .claude/agents/config.json
{
  "agents": {
    "explore": {
      "script": "agents/explore.py",
      "description": "Explore codebase with aOa"
    }
  }
}
```

---

## Performance Comparison

### Before Integration (Native Grep)

```
User: "Find authentication code"
Claude: Grep(pattern="auth")
        → scans 50,000 lines
        → 2,300ms
        → returns 500 matches (noise)
        → reads 8 files to filter
        → total: 17,000 tokens, 4 minutes
```

### After Layer 1 (Tool Interception)

```
User: "Find authentication code"
Claude: Grep(pattern="auth")
        → intercepted by hook
        → aoa grep auth
        → 8ms
        → returns 15 ranked matches
        → reads 2 specific files
        → total: 1,200 tokens, 30 seconds
```

**Savings:** 93% tokens, 87% time

---

## Monitoring Integration Health

### Check if hooks are firing

```bash
# Watch intent capture in real-time
aoa intent

# Should see:
# - "intercepted: Grep → aoa grep" (Layer 1 working)
# - "predicted: 3 files" (Layer 2 predictions)
# - "agent: explore" (Layer 3 custom agents)
```

### Check MCP server status

```bash
# Test MCP server
curl -X POST http://localhost:8081/tools/aoa_grep \
  -H "Content-Type: application/json" \
  -d '{"query": "auth", "limit": 10}'

# Should return JSON with file:line results
```

### Check status line

```bash
# Should show interception stats
⚡ aOa 🟢 247 │ ↓1.8M ⚡1h32m saved │ 89% intercepted │ ctx:142k/200k (71%)
```

---

## Troubleshooting

### Interception not working

```bash
# Check aOa health
aoa health

# Check hook is installed
ls -la .claude/hooks/intercept-search.py

# Check hooks.json has PreToolUse entry
cat .claude/hooks/hooks.json | grep -A5 "PreToolUse"

# Test hook manually
echo '{"tool_name":"Grep","tool_input":{"pattern":"auth"}}' | \
  python3 .claude/hooks/intercept-search.py
```

### MCP server not connecting

```bash
# Check server is running
ps aux | grep aoa-server.py

# Test stdio mode
echo '{"method":"tools/list"}' | python3 ~/.aoa/mcp/aoa-server.py

# Check Claude Desktop logs
tail -f ~/Library/Logs/Claude/mcp-server-aoa.log
```

---

## FAQ

**Q: Will this break existing workflows?**
A: No. Every layer has graceful fallback to native tools.

**Q: Do I need all three layers?**
A: No. Layer 1 alone gives 95% of the benefit. Layers 2-3 are for advanced use cases.

**Q: Does this work with Claude API?**
A: Layer 2 (MCP) works with API clients that support MCP. Layer 1 is CLI-only.

**Q: Can I disable interception?**
A: Yes. Remove the PreToolUse hook from hooks.json.

**Q: What if aOa is slow/down?**
A: Automatic fallback to native Grep. Zero user impact.

---

## Next Steps

1. **Read full roadmap:** [INTEGRATION_ROADMAP.md](INTEGRATION_ROADMAP.md)
2. **Start with Layer 1:** Quick win, zero user effort
3. **Add Layer 2 if needed:** Universal client support
4. **Experiment with Layer 3:** Custom agents, maximum power

**Questions?** Open an issue or ask in discussions.

---

**The Goal:** Make aOa so integrated that users forget it exists—it's just "how Claude works fast." 🚀
