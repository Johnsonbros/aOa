# aOa Hook Integration Insights

> **Purpose**: Document how to integrate aOa's intent tracking hooks into Claude Code
> **Tested**: Working in aOa project
> **Branding**: Transparent, colored output showing what's being tracked

---

## What the Hooks Do

| Hook | Event | Purpose | Visible? |
|------|-------|---------|----------|
| `intent-capture.py` | PostToolUse | Learn from every tool call | No* |
| `intent-prefetch.py` | PreToolUse | Predict files before access | No* |
| `intent-summary.py` | UserPromptSubmit | Show intent summary | **YES** |

*Only visible in verbose mode (Ctrl+O)

## Critical Discovery: Hook Output Visibility

**The Problem**: We wanted to show intent tags after every tool call, but PostToolUse stdout is hidden by default.

**The Solution**: Use `UserPromptSubmit` hook instead.

| Hook Type | stdout Behavior | When Visible |
|-----------|-----------------|--------------|
| `PostToolUse` | Hidden | Only in verbose mode (Ctrl+O) |
| `PreToolUse` | Hidden | Only in verbose mode (Ctrl+O) |
| `UserPromptSubmit` | **ALWAYS SHOWN** | Every user message |
| `SessionStart` | **ALWAYS SHOWN** | Session start |

**Why This Works**:
- `UserPromptSubmit` fires when user sends a message
- Its stdout is injected as context (Claude sees it, user sees it)
- Shows intent summary at the perfect time (start of each interaction)

**Implementation**:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [{
          "type": "command",
          "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/intent-summary.py\"",
          "timeout": 2
        }]
      }
    ]
  }
}
```

Result: User sees `⚡ AOA │ 157 intents │ 16 tags │ 102.7ms` before every response.

---

## Hook 1: Intent Capture (PostToolUse)

**File**: `.claude/hooks/intent-capture.py`

**What it does**:
- Fires after Read, Edit, Write, Bash, Grep, Glob
- Extracts file paths from tool input
- Infers intent tags from file patterns (auth → `#authentication`, test → `#testing`)
- Sends to aOa: `POST localhost:8080/intent`

**Key Features**:
- File pattern matching for ~15 common intent patterns
- Tool action tags (`#reading`, `#editing`, `#creating`)
- Fire-and-forget (non-blocking, <10ms)
- Graceful failure (never blocks Claude)

**Tag Inference Examples**:
```python
INTENT_PATTERNS = [
    (r'auth|login|session|oauth|jwt', ['#authentication', '#security']),
    (r'test[s]?[/_]|_test\.|\bspec[s]?\b', ['#testing']),
    (r'config|settings|\.env', ['#configuration']),
    (r'api|endpoint|route|handler', ['#api']),
    (r'index|search|query', ['#search']),
]
```

---

## Hook 2: Intent Prefetch (PreToolUse)

**File**: `.claude/hooks/intent-prefetch.py`

**What it does**:
- Fires before Read, Edit, Write
- Queries aOa for related files: `GET localhost:8080/intent/file?path=X`
- Returns suggestions if confidence > threshold
- Only activates after 10+ recorded intents

**Key Features**:
- Minimum data requirement (prevents noise during bootstrap)
- Top-5 related files based on shared intent tags
- Silent by default (future: inject into Claude's context)

---

## Hook 3: Intent Summary (UserPromptSubmit)

**File**: `.claude/hooks/intent-summary.py`

**What it does**:
- Fires when user submits a prompt
- Queries aOa: `GET localhost:8080/intent/recent`
- Shows branded summary with metrics

**Branded Output** (with timing):
```python
# Build the branded output with ANSI colors
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

parts = [
    f"{CYAN}{BOLD}⚡ AOA{RESET}",
    f"{total} intents",
    f"{tags_count} tags",
    f"{GREEN}{elapsed_ms:.1f}ms{RESET}",
]

header = f" {DIM}│{RESET} ".join(parts)
tags_display = f"{YELLOW}{tags_str}{RESET}"

output = f"{header} {DIM}│{RESET} {tags_display}"
```

**Example Output**:
```
⚡ AOA │ 136 intents │ 16 tags │ 34.0ms │ editing python searching
```

Shows:
- **⚡ AOA** - Cyan, bold branding
- **136 intents** - Total captured
- **16 tags** - Unique tags
- **34.0ms** - Query time (green, transparent)
- **editing python searching** - Recent activity (yellow)

---

## Installation Steps

### 1. Create Hook Files

Place in `.claude/hooks/` (project-level) or `~/.claude/hooks/` (user-level):

```bash
mkdir -p .claude/hooks
# Copy the three Python files (see appendix for full code)
chmod +x .claude/hooks/*.py
```

### 2. Configure settings.local.json

**File**: `.claude/settings.local.json`

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/intent-summary.py\"",
            "timeout": 2
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Read|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/intent-prefetch.py\"",
            "timeout": 2
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Read|Edit|Write|Bash|Grep|Glob",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/intent-capture.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### 3. Restart Claude Code

Hooks are loaded at session start. Exit and re-enter to activate.

---

## Verification

After restart, you should see on your next prompt:

```
⚡ AOA │ X intents │ Y tags │ Zms │ recent tags
```

If not showing:
1. Check hooks are executable: `ls -la .claude/hooks/*.py`
2. Check settings: `cat .claude/settings.local.json`
3. Verify aOa is running: `curl localhost:8080/intent/stats`
4. Test hook directly: `echo '{}' | python3 .claude/hooks/intent-summary.py`

---

## Optimization Techniques

### Bash Command Optimization

There's also a `bash-optimizer.sh` hook that can reduce redundant commands, but it's optional for aOa.

### Key Points

1. **Fire-and-forget**: PostToolUse hooks are async, never block
2. **Graceful degradation**: If aOa is down, hooks silently fail
3. **Rate limiting**: Summary only shows on user prompts (not every tool call)
4. **Bounded data**: Prefetch only after 10+ intents to avoid cold-start noise

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Claude Code Session                                         │
│                                                               │
│  User types prompt                                            │
│    ↓                                                          │
│  UserPromptSubmit hook → intent-summary.py                   │
│    ↓                                                          │
│  GET localhost:8080/intent/recent                            │
│    ↓                                                          │
│  ⚡ AOA │ 136 intents │ 16 tags │ 34ms  ← USER SEES THIS    │
│                                                               │
│  Claude performs tool calls (Read, Edit, etc.)               │
│    ↓                                                          │
│  PreToolUse hook → intent-prefetch.py                        │
│    ↓                                                          │
│  GET localhost:8080/intent/file?path=auth.py                 │
│    ↓                                                          │
│  (suggestions returned, future: inject into Claude context)  │
│                                                               │
│  Tool executes                                                │
│    ↓                                                          │
│  PostToolUse hook → intent-capture.py                        │
│    ↓                                                          │
│  POST localhost:8080/intent                                  │
│    body: {tool, files, tags, session_id}                     │
│    ↓                                                          │
│  Redis updated with scores                                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Hook not firing

```bash
# Check if aOa is running
curl localhost:8080/health

# Test hook manually
echo '{}' | python3 .claude/hooks/intent-summary.py
# Should output: ⚡ AOA │ X intents │ ...

# Check hook permissions
ls -la .claude/hooks/
# Should be -rwx--x--x (executable)
```

### No branded output

The `⚡ AOA` output only appears from `UserPromptSubmit` hook. Make sure:
- Hook is configured in settings.local.json
- aOa gateway is running on localhost:8080
- You've restarted Claude Code after adding hooks

### Intent not being captured

```bash
# Check intent stats
curl localhost:8080/intent/stats
# Should show: {"total_records": N, ...}

# If N is 0, PostToolUse hook isn't working
# Test it:
echo '{"tool_name": "Read", "tool_input": {"file_path": "/test.py"}, "session_id": "test"}' \
  | python3 .claude/hooks/intent-capture.py
```

---

## Performance Impact

| Hook | Latency | Blocking? |
|------|---------|-----------|
| UserPromptSubmit | ~35ms | No (async) |
| PreToolUse | ~20ms | No (async) |
| PostToolUse | ~10ms | No (fire-and-forget) |

**Total overhead**: <65ms per interaction, amortized across tool calls.

**Value**: Saves 60-70% of context tokens through better search and prefetch.

---

## Advanced: Custom Tag Patterns

Edit `intent-capture.py` to add your own patterns:

```python
# Add to INTENT_PATTERNS
(r'payment|stripe|checkout', ['#payments', '#commerce']),
(r'ml|model|training|inference', ['#machine-learning']),
(r'deploy|ci|cd|pipeline', ['#devops']),
```

Tags will automatically be tracked and used for prefetch ranking.

---

## Next Steps

Once hooks are working:
1. Use Claude Code normally (the hooks learn automatically)
2. After 50+ tool calls, check: `aoa intent recent`
3. See the patterns: `aoa intent tags`
4. Watch prefetch get smarter over time

**The system learns your codebase without you thinking about it.**

---

*For full technical details, see `.context/deployment_plan/DEPLOYMENT.md` in the aOa repo.*
