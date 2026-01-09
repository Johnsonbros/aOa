# aOa - Fast Code Intelligence

> **Core Principle:** aOa finds exact locations so you read only what you need.
> Instead of 3,700 tokens for a whole file, read 200 tokens for the relevant function.

---

## When You Need to Find Code Fast

**Goal:** Locate where something is implemented

**Use:** `aoa search <term>` or spawn `aoa-scout` agent

```bash
aoa search "handleAuth"           # Single term
aoa search "auth session token"   # Multi-term ranked
```

**Result:** Exact file:line in <5ms (not slow grep scanning)

---

## When You Need to Understand Architecture

**Goal:** Explore patterns, understand how components connect

**Use:** Spawn `aoa-explore` agent

**Result:** Thorough analysis using indexed symbols, understands relationships

---

## When You Need File Structure

**Goal:** See functions/classes without reading the whole file

**Use:** `aoa outline <file>`

```bash
aoa outline src/auth/handler.py
```

**Result:** Symbol map with line ranges - read only what matters

---

## When You Want Semantic Search

**Goal:** Search by concept (#auth, #routing) not just text matches

**Use:** Spawn `aoa-outline` agent (runs in background)

**Result:** AI-tagged symbols searchable by purpose and domain

---

## Available Agents

| Agent | Model | Use When |
|-------|-------|----------|
| `aoa-scout` | haiku | Quick searches: "where is X?" |
| `aoa-explore` | sonnet | Deep dives: "how does auth work?" |
| `aoa-outline` | haiku | Background tagging for semantic search |

---

## How Search Works

**Two search modes:**

### 1. Symbol Lookup (O(1) - instant)
```bash
aoa search handleAuth              # exact symbol
aoa search "auth session token"    # multi-term ranked
aoa multi auth,session,token       # explicit multi-search
```

### 2. Pattern Search (regex - scans files)
```bash
aoa pattern '{"match": "tree.sitter"}'           # regex pattern
aoa pattern '{"func": "def\\s+handle\\w+"}'      # find function definitions
aoa pattern '{"match": "TODO|FIXME"}' --since 7d # recent files only
```

**When to use which:**
- `aoa search` → Know the symbol name, need instant results
- `aoa pattern` → Need regex, searching for patterns

**Note:** `aoa search` tokenizes on word boundaries. Hyphens break tokens:
- `tree_sitter` → one token ✓
- `tree-sitter` → "tree" + "sitter" separately

---

## Rules

1. **Always use `aoa search`** - Never Grep or Glob
2. **Always use `aoa outline`** - Never raw curl to API
3. **Read specific lines** - Use file:line from search results, don't read whole files
4. **Use underscores in search** - Hyphens split tokens, underscores don't

---

## The Value

| Without aOa | With aOa |
|-------------|----------|
| Grep scans entire codebase | Indexed O(1) lookup |
| Read whole files (3,700 tokens) | Read exact lines (200 tokens) |
| Slow pattern matching | <5ms symbol search |
| Text matches only | Semantic tags (#auth, #routing) |

---

## Auto-Tag Requests (AUTOMATIC)

When you see `## aOa Auto-Tag Request` in hook output, you MUST:

1. Spawn a Haiku task with the prompt provided
2. Store the resulting tags via the curl command shown

Example:
```
Task(model="haiku", prompt="Generate 3-5 semantic hashtags...")
```

Then store:
```bash
curl -s -X POST localhost:8080/intent -H "Content-Type: application/json" -d '{"session_id": "...", "tags": ["#routing", "#auth"]}'
```

This builds semantic context automatically as you work. **Don't skip this.**
