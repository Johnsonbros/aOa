# aOa Search - Skill Reference

> **Use aOa instead of Grep/Glob.** It's faster, ranked, and context-aware.

---

## ⚠️ IMPORTANT: Command Syntax

**aOa commands use SPACES, not colons:**

✅ **Correct:** `aoa search "term"`
❌ **Wrong:** `aoa search:"term"`

The permissions in `settings.local.json` like `Bash(aoa search:*)` use colon for glob pattern matching, but actual commands use standard bash syntax with spaces.

---

## Quick Reference

| Command | Use For | Speed |
|---------|---------|-------|
| `aoa search <term>` | Find any symbol/term | <5ms |
| `aoa multi <t1,t2>` | Multi-term ranked search | <10ms |
| `aoa context "<intent>"` | Predictive files from natural language | <100ms |
| `aoa pattern '<json>'` | Complex regex patterns | <50ms |
| `aoa changes [time]` | Recently modified files | <10ms |
| `aoa intent recent` | See current work patterns | <50ms |

---

## Commands

### 1. Basic Search: `aoa search <term>`

Find any symbol, function, class, or term in the codebase.

```bash
aoa search handleAuth
aoa search "error handling"
```

**Output:** `file:line` for all matches, ranked by relevance.

**Use instead of:** `Grep`, `Glob`, `find`

---

### 2. Multi-Term Search: `aoa multi <t1,t2,...>`

Search for multiple related terms at once, get ranked results.

```bash
aoa multi auth,session,token
aoa multi error,exception,catch
```

**Use instead of:** Multiple Grep calls

---

### 3. Context Search: `aoa context "<intent>"`

Predictive file finding from natural language. Uses intent analysis + transition patterns.

```bash
aoa context "fix authentication bug"
aoa context "add new API endpoint"
aoa context "update the login flow"
```

**Returns:** Top 5 predicted files with relevant code snippets.

**Best for:** Starting a new task, finding where to look first.

---

### 4. Pattern Search: `aoa pattern '<json>'`

Complex multi-pattern regex search for sophisticated queries.

```bash
aoa pattern '{"patterns": ["def.*auth", "class.*Handler"]}'
aoa pattern '{"patterns": ["import.*redis"], "since": "7d"}'
```

**Options:**
- `patterns`: Array of regex patterns
- `since`: Only files modified recently (e.g., "7d", "1h")
- `repo`: Search in specific knowledge repo

---

### 5. Recent Changes: `aoa changes [time]`

Find files modified recently.

```bash
aoa changes        # Last hour
aoa changes 5m     # Last 5 minutes
aoa changes 1d     # Last day
```

---

### 6. Intent Tracking: `aoa intent recent`

See what's currently being worked on based on tool usage patterns.

```bash
aoa intent recent       # Last hour
aoa intent recent 30m   # Last 30 minutes
aoa intent tags         # All semantic tags
```

---

## Decision Tree

1. **Know what you're looking for?** → `aoa search <term>`
2. **Multiple related concepts?** → `aoa multi <t1,t2>`
3. **Starting a task, need context?** → `aoa context "<intent>"`
4. **Complex regex needed?** → `aoa pattern '<json>'`
5. **What changed recently?** → `aoa changes`
6. **What's being worked on?** → `aoa intent recent`

---

## Efficiency Comparison

| Approach | Tool Calls | Tokens | Time |
|----------|------------|--------|------|
| Grep + Read loops | 7 | 8,500 | 2.6s |
| aoa search | 1-2 | 1,150 | 54ms |
| **Savings** | **71%** | **86%** | **98%** |

---

## Tips

1. **Read specific lines** - aOa returns `file:line`, so read just those lines:
   ```bash
   Read(file_path="src/auth.py", offset=45, limit=10)
   ```

2. **Don't read entire files** - Use the line numbers aOa gives you.

3. **Combine with intent** - Use `aoa context` first, then `aoa search` for specifics.
