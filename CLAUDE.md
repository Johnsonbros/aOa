# aOa - AI Agent Instructions

**CRITICAL: This project has aOa installed. ALWAYS use `aoa search` instead of Grep/Glob.**

## Rule #1: Search with aOa First

**NEVER do this:**
```bash
# WRONG - Multiple tool calls, slow, wasteful
Grep(pattern="claudacity", path="src/")  # 1 call
Read(file1.py)                            # 2 calls
Read(file2.py)                            # 3 calls
Read(file3.py)                            # 4 calls
# = 4 tool calls, ~8,500 tokens, 2+ seconds
```

**ALWAYS do this:**
```bash
# RIGHT - One call, fast, efficient
aoa search claudacity
# Returns: file:line for ALL matches in <5ms
# Then read ONLY the specific lines you need
```

## Rule #2: aOa Returns File:Line - Use It

aOa search output:
```
⚡ 20 hits │ 4.73ms
  index/indexer.py:1308
  status_service.py:56
  status_service.py:115
```

This tells you EXACTLY where to look. Don't read entire files - read specific line ranges:
```bash
Read(file_path="src/index/indexer.py", offset=1305, limit=10)
```

## Rule #3: One Search Replaces Many Greps

**WRONG:**
```bash
Grep("auth")    # call 1
Grep("login")   # call 2
Grep("session") # call 3
```

**RIGHT:**
```bash
aoa search "auth login session"  # ONE call, ranked results
```

## Commands

| Command | Use For | Speed |
|---------|---------|-------|
| `aoa search <term>` | Finding ANY code/symbol | <5ms |
| `aoa search "term1 term2"` | Multi-term ranked | <10ms |
| `aoa health` | Check services | instant |
| `aoa intent recent` | See what's being worked on | <50ms |

## API Endpoints (localhost:8080)

For programmatic access via curl:

```bash
curl "localhost:8080/symbol?q=handleAuth"           # Symbol search
curl "localhost:8080/multi?q=auth+login+handler"    # Multi-term ranked
curl "localhost:8080/files"                          # List indexed files
curl "localhost:8080/intent/recent"                  # Recent intents
```

## Efficiency Comparison

| Approach | Tool Calls | Tokens | Time |
|----------|------------|--------|------|
| Grep + Read loops | 7 | 8,500 | 2.6s |
| aOa search | 1-2 | 1,150 | 54ms |
| **Savings** | **71%** | **86%** | **98%** |

## Decision Tree

1. **Need to find code?** → `aoa search <term>` (NOT Grep)
2. **Need multiple terms?** → `aoa search "term1 term2"` (NOT multiple Greps)
3. **Need file content?** → Read specific lines from aOa results (NOT entire files)
4. **Need to understand patterns?** → `aoa intent recent`

## Intent Tracking

Every tool call is captured automatically. The status line shows:
```
⚡ aOa │ 61 intents │ 14 tags │ 0.1ms │ searching shell markdown editing
```

This helps predict which files you'll need next.
