---
name: aoa-outline
description: Deep outline with semantic tags for aOa. Use when asked to tag the codebase, generate semantic tags, or run deep outline. Processes files in batches using Haiku to generate symbol-level tags.
allowed-tools: Bash, Task
---

# aOa Outline - Deep Semantic Tagging

Add semantic tags to code outlines for powerful search.

## Overview

This skill batch-processes files to add semantic tags at the symbol level:
1. Queries `/outline/pending` for files needing tags
2. Batches files into groups of 15
3. Spawns Haiku tasks to generate per-symbol tags
4. Stores tags via `/outline/enriched`

**Idempotent**: Re-running picks up where you left off.

## Execution Steps

### Step 1: Check Pending Files

```bash
curl -s localhost:8080/outline/pending
```

Parse the response to get:
- `pending_count`: Number of files needing tags
- `pending`: Array of file objects with `file`, `language`, `reason`

If `pending_count` is 0, report "All files are tagged" and exit.

### Step 2: Batch and Process

Group pending files into batches of 15. For each batch:

1. **Get outlines** for each file in the batch:
   ```bash
   curl -s "localhost:8080/outline?file=<filepath>"
   ```

2. **Spawn a Haiku task** to analyze the batch and generate tags per symbol:

   ```
   Task(
     subagent_type="general-purpose",
     model="haiku",
     prompt="Analyze these code outlines and generate 2-5 semantic tags per SYMBOL..."
   )
   ```

3. **Store tags** after processing:
   ```bash
   # Get project ID from .aoa/home.json
   PROJECT_ID=$(jq -r '.project_id' .aoa/home.json 2>/dev/null || echo "")

   curl -s -X POST localhost:8080/outline/enriched \
     -H "Content-Type: application/json" \
     -d "{
       \"file\": \"<filepath>\",
       \"project\": \"${PROJECT_ID}\",
       \"symbols\": [
         {\"name\": \"funcName\", \"kind\": \"function\", \"line\": 10, \"end_line\": 25, \"tags\": [\"#auth\", \"#validation\"]}
       ]
     }"
   ```

   **IMPORTANT**: Always include the project ID from `.aoa/home.json`.

### Step 3: Report Progress

After each batch, report:
- Files processed in this batch
- Symbols tagged
- Total progress (e.g., "15/45 files tagged")

## Haiku Prompt Template

When spawning Haiku tasks for tag generation:

```
You are analyzing code structure to generate semantic tags.

For each SYMBOL (function, class, method) below, generate 2-5 semantic tags that describe:
- What the code DOES (e.g., "#authentication", "#file-parsing", "#api-routing")
- The DOMAIN it belongs to (e.g., "#database", "#ui", "#networking")
- Key PATTERNS used (e.g., "#singleton", "#factory", "#middleware")

Output format - JSON per file:
{
  "file": "<filepath>",
  "symbols": [
    {"name": "symbolName", "kind": "function", "line": 10, "end_line": 25, "tags": ["#tag1", "#tag2"]}
  ]
}

FILES TO ANALYZE:

[Insert outline data here]
```

## Error Handling

- **API unreachable**: Report "aOa services not running. Run `aoa health` to check."
- **File outline fails**: Skip file, continue with batch, report at end
- **Haiku task fails**: Retry once, then skip batch and continue

## Example Session

```
User: tag the codebase

Claude: Checking files needing semantic tags...

Found 45 files needing tags.
Processing in 3 batches of 15.

**Batch 1/3** (15 files, 127 symbols)
- services/index/indexer.py: 12 symbols tagged
- services/gateway/gateway.py: 8 symbols tagged
...

**Batch 2/3** (15 files, 98 symbols)
...

**Batch 3/3** (15 files, 89 symbols)
...

Tagging complete: 45 files, 314 symbols tagged.

Try: aoa search "#authentication" to find auth-related code
```

## Triggers

This skill activates on:
- "tag the codebase"
- "add semantic tags"
- "deep outline"
- "outline --deep"

## Quick Commands

| Command | Description |
|---------|-------------|
| `aoa outline --pending` | Check files needing tags |
| `aoa search "#tag"` | Search by semantic tag |
| `aoa health` | Verify services running |
