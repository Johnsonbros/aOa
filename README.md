# aOa - Angle O(1)f Attack

> **Stop wasting tokens. Start shipping code.**

aOa gives AI agents unlimited context through O(1) search and predictive prefetching. Instead of grep loops and read trees, agents find what they need instantly.

## The Problem

AI coding agents waste 60-70% of their context on exploration:
- Grep trees: "Let me search for auth... login... session..."
- Read loops: "Let me read these 15 files to find the pattern..."
- Token waste: 8,500 tokens to find what should take 150

## The Solution

**aOa = Learn → Rank → Prefetch**

1. **PostHook learns** - Captures every tool call, infers intent
2. **Redis ranks** - Composite scoring: recency + tags + co-mod + frequency
3. **PreHook prefetches** - "These are probably the files you're looking for"

**Result**: 2 tool calls instead of 7. 54ms instead of 2.6s. 1,150 tokens instead of 8,500.

---

## Quickstart

```bash
# Clone and run (indexes current directory by default)
git clone https://github.com/you/aOa
cd aOa
./install.sh

# Search (O(1) inverted index)
aoa search handleAuth     # <5ms

# Intent tracking (starts learning)
aoa intent recent

# Add knowledge repo
aoa repo add flask https://github.com/pallets/flask

# Search external code
aoa repo flask search Blueprint
```

---

## What You Get

| Feature | Speed | What It Does |
|---------|-------|--------------|
| **Symbol search** | <5ms | O(1) inverted index lookup |
| **Multi-term ranked** | <10ms | Density-based ranking across terms |
| **Intent tracking** | <50ms | Learns what you're working on |
| **Predictive prefetch** | <50ms | Suggests files before you ask |
| **Knowledge repos** | <5ms | Search external codebases instantly |
| **Co-modification** | O(1) | Files changed together historically |

---

## Architecture

```
USER → Gateway:8080 (ONLY exposed port)
          ↓
    Docker Network (internal: true = NO INTERNET)
          ↓
    ┌─────┼─────┬─────┬─────┐
    │     │     │     │     │
  INDEX STATUS REDIS PROXY
                       │
                       └→ (controlled internet)
                          github.com (whitelisted)
                          git.company.com (user-added)
```

**Trust guarantees:**
- All services except proxy have NO internet access
- Proxy only accesses whitelisted URLs
- All requests logged at `/audit`
- Network topology at `/network`
- Run `./scripts/verify-isolation.sh` to prove it

---

## Installation

```bash
# 1. Clone repo
git clone https://github.com/you/aOa
cd aOa

# 2. Run installer (indexes current directory by default)
./install.sh

# 3. Verify it's working
aoa health

# To index a different directory:
CODEBASE_PATH=/path/to/your/code ./install.sh
```

---

## Configuration

aOa uses **file-based config** (no API sprawl):

```
.aoa/
├── config.json          # Main settings
├── whitelist.txt        # Allowed URLs
├── session.db           # SQLite session data
└── README.md            # What's stored here
```

Edit `.aoa/whitelist.txt` to add your URLs:
```txt
github.com
gitlab.com
bitbucket.org
git.company.com         # Your private git server
```

---

## Benchmarks

Run the benchmark to see the difference:

```bash
./scripts/benchmark.sh
```

**Example output:**
```
Finding auth code (15-file codebase):

Without aOa:
  grep + read loops:  7 tool calls, 8,500 tokens, 2.6s

With aOa:
  Multi-search:       2 tool calls, 1,150 tokens, 54ms

Savings: 71% fewer calls, 86% fewer tokens, 98% faster
```

---

## How It Works

### 1. Index Time (O(n) once)

When you run `aoa init`:
- Scans all files (inverted index)
- Builds dependency graph
- Extracts symbols (tree-sitter)
- Takes 10-60s depending on codebase size

### 2. Query Time (O(1) always)

When you run `aoa search`:
- Hash lookup in index
- Returns in <5ms
- Never scans files again

### 3. Learning (continuous)

PostToolUse hook captures:
- Which files you access
- What intent tags apply
- Co-modification patterns

### 4. Prefetch (predictive)

PreToolUse hook predicts:
- "Based on your intent, you probably need these files"
- Only shows if confidence > 60%
- Gets smarter over time

---

## Transparency

**Every interaction shows you what's happening:**

```
⚡ AOA | 136 intents | 16 tags | 32.8ms | editing python searching
```

You see:
- How many intents captured
- Which tags are active
- How fast the query was
- Current activity

**No black box. No magic. Just speed.**

---

## Development

```bash
# Start services
docker compose up -d

# Watch logs
docker compose logs -f

# Rebuild after changes
docker compose build
docker compose restart

# Verify isolation
./scripts/verify-isolation.sh

# Run tests
pytest tests/
```

---

## License

MIT - Do whatever you want with it.

---

## Why "aOa"?

**Angle O(1)f Attack** - The O(1) is literally in the name.

We shift complexity from query time (where it hurts) to index time (where it's free). Pay once at startup, benefit forever after.

---

**Questions? Issues? PRs welcome.**
