# Full Messaging Audit - Current → Proposed

> **Purpose**: Complete inventory of all user-facing messaging
> **Status**: Audit complete, ready for review

---

## Summary

| Location | Items Audited | Changes Proposed |
|----------|---------------|------------------|
| CLI Help (`aoa help`) | 23 | 8 |
| Status Line (`aoa-status.sh`) | 5 | 2 |
| Install Script (`install.sh`) | 7 | 4 |
| README.md | 14 | 8 |
| CLAUDE.md | 11 | 3 |
| **Total** | **60** | **25** |

---

## 1. CLI Help (`cli/aoa help`)

### Header

| Line | Current | Proposed | Change? |
|------|---------|----------|---------|
| Title | `AOA` | `AOA` | No |
| Subtitle | `Bold tools for Claude Code` | `5 angles. 1 attack.` | **Yes** |

### Command Group Headers

| Current | Proposed | Rationale |
|---------|----------|-----------|
| `STATUS COMMANDS` | `ATTACK STATUS` | Attack orchestration output |
| `LOCAL SEARCH` | `SYMBOL ANGLE` | O(1) symbol lookup |
| `PATTERN SEARCH` | `SIGNAL ANGLE` | Multi-pattern / multi-term |
| `INTENT TRACKING` | `INTENT ANGLE` | Intent tracking (keep term) |
| `URL WHITELIST` | `URL WHITELIST` | No change (security, not attack) |
| `KNOWLEDGE REPOS` | `INTEL ANGLE` | External knowledge |
| `SYSTEM` | `SYSTEM` | No change |

### Command Descriptions

| Command | Current | Proposed | Change? |
|---------|---------|----------|---------|
| `status` | "Show status line (context, cost, usage)" | "Show attack status (hit rate, intents)" | **Yes** |
| `search <term>` | "Find symbol/term in local codebase" | "O(1) symbol lookup" | **Yes** |
| `multi <t1,t2>` | "Multi-term search" | "Multi-angle search" | **Yes** |
| `changes` | "Recent file changes" | Keep | No |
| `files` | "List indexed files" | Keep | No |
| `pattern` | "Multi-pattern regex search" | Keep | No |
| `intent recent` | "Recent intent records" | Keep | No |
| `intent tags` | "All tags with file counts" | Keep | No |
| `intent files` | "Files associated with an intent tag" | Keep | No |
| `intent file` | "Tags associated with a file" | Keep | No |
| `intent stats` | "Intent index statistics" | Keep | No |
| `whitelist *` | (all) | Keep | No |
| `repo list` | "List knowledge repos" | "List intel sources" | **Yes** |
| `repo add` | "Clone and index a git repo" | "Add intel source" | **Yes** |
| `repo remove` | "Remove a knowledge repo" | "Remove intel source" | **Yes** |
| `repo <n> search` | "Search in a specific repo" | "Search intel source" | **Yes** |
| `health` | "Check all services" | "Check all angles" | **Yes** |
| `memory` | "Dynamic working context" | Keep | No |
| `services` | "Visual service map with live status" | Keep | No |

### Philosophy Section

| Current | Proposed |
|---------|----------|
| "Local search is the default (your code)" | "Symbol angle is default (your code)" |
| "Knowledge repos are isolated reference material" | "Intel angle is isolated reference material" |
| "No mixing - repo code never pollutes local results" | "No mixing - intel never pollutes symbol results" |
| "Delete a repo = clean removal" | "Delete intel = clean removal" |

---

## 2. Status Line (`aoa-status.sh`)

### Output Format

| Element | Current | Proposed | Change? |
|---------|---------|----------|---------|
| Brand | `⚡ aOa` | `⚡ aOa` | No |
| Accuracy | `🟢 100%` | `🟢 100%` | No (already "hit rate") |
| Count label | `136 intents` | `136 intents` | No (keep "intents") |
| Tags | `editing python auth` | `editing python auth` | No |

### Learning State

| Current | Proposed | Change? |
|---------|----------|---------|
| `learning...` | `calibrating...` | **Yes** |

### Code Comments

| Line | Current | Proposed | Change? |
|------|---------|----------|---------|
| Line 3 | "aOa Status Line - Branded with Accuracy First" | "aOa Status Line - Attack Status" | Optional |
| Line 10 | "25 intents" (example) | Keep | No |

---

## 3. Install Script (`install.sh`)

### Banner

| Line | Current | Proposed | Change? |
|------|---------|----------|---------|
| 30 | `⚡ aOa - Angle O(1)f Attack` | Keep | No |
| 31 | `Installation Starting...` | `Deploying 5 angles...` | **Yes** |

### Progress Messages

| Line | Current | Proposed | Change? |
|------|---------|----------|---------|
| 39 | "Checking for Docker..." | Keep | No |
| 67 | "Creating .aoa configuration..." | Keep | No |
| 158 | "Building Docker services..." | "Building attack surface..." | Optional |
| 161 | "Starting services..." | "Deploying angles..." | **Yes** |
| 165 | "Waiting for services to be healthy..." | "Waiting for angles to align..." | Optional |

### Completion

| Line | Current | Proposed | Change? |
|------|---------|----------|---------|
| 197 | `⚡ aOa Installation Complete!` | `⚡ aOa Attack Ready!` | **Yes** |

### Try It Section

| Line | Current | Proposed | Change? |
|------|---------|----------|---------|
| 202 | `aoa search <term>          Search your code` | `aoa search <term>          Symbol angle` | **Yes** |
| 203 | `aoa health                 Check services` | `aoa health                 Check angles` | **Yes** |

---

## 4. README.md

### Title & Tagline

| Line | Current | Proposed | Change? |
|------|---------|----------|---------|
| 1 | `# aOa - Angle O(1)f Attack` | Keep | No |
| 5 | `Same cost for 100 files or 100,000.` | Keep | No |

### Section Headers

| Current | Proposed | Change? |
|---------|----------|---------|
| "The Problem You Know Too Well" | Keep | No |
| "What If It Didn't Have To?" | Keep | No |
| "How It Works" | "The Five Angles" | **Yes** |
| "The Numbers" | "Hit Rate" | **Yes** |
| "Quick Start" | "Deploy" | **Yes** |
| "The Outcome" | Keep | No |
| "Why 'aOa'?" | Keep | No |
| "Trust" | Keep | No |

### How It Works Table (Lines 47-54)

| Current | Proposed |
|---------|----------|
| "5 attack groups with 15+ methods" | "5 angles converging to 1 attack" |

| Group | Current | Proposed |
|-------|---------|----------|
| **Search** | "O(1) symbol lookup, multi-term ranking, pattern matching" | **Symbol Angle**: O(1) lookup |
| **Intent** | "Learns from every tool call, builds tag affinity" | **Intent Angle**: Tracks what you're doing |
| **Knowledge** | "Searches external repos without polluting your results" | **Intel Angle**: External reference |
| **Ranking** | "Recency, frequency, filename matching, transitions" | **Signal Angle**: Multi-signal ranking |
| **Prediction** | "Prefetches files before you ask" | **Strike Angle**: Predictive hit |

### Numbers Table

| Current | Proposed | Change? |
|---------|----------|---------|
| "Tokens" | Keep | No |
| "Tool calls" | Keep | No |
| "Time" | Keep | No |
| "Accuracy" | "Hit rate" | **Yes** |

### Status Line Example (Line 89)

| Current | Proposed | Change? |
|---------|----------|---------|
| `136 intents` | Keep | No |

### Why aOa Section

| Line | Current | Proposed | Change? |
|------|---------|----------|---------|
| 100 | "O = Big O notation. O(1) constant time." | Keep | No |
| 101 | "Angle = The right approach." | "Angle = 5 approach methods" | **Yes** |
| 102 | "Attack = 5 groups, 15+ methods, converging on one answer." | "Attack = The orchestration that combines angles for accuracy" | **Yes** |

---

## 5. CLAUDE.md

### Header

| Line | Current | Proposed | Change? |
|------|---------|----------|---------|
| 1 | `# aOa - AI Agent Instructions` | `# aOa - 5 Angles. 1 Attack.` | **Yes** |
| 3 | `CRITICAL: ...ALWAYS use aoa search instead of Grep/Glob` | Keep | No |

### Rule Descriptions

| Section | Current | Proposed | Change? |
|---------|---------|----------|---------|
| Rule #1 | "Search with aOa First" | "Symbol Angle First" | **Yes** |
| Rule #2 | "aOa Returns File:Line" | Keep | No |
| Rule #3 | "One Search Replaces Many Greps" | "One Angle Replaces Many Tools" | **Yes** |

### Commands Table

| Current | Proposed | Change? |
|---------|----------|---------|
| `aoa search <term>` - "Finding ANY code/symbol" | "Symbol angle lookup" | Optional |
| `aoa search "term1 term2"` - "Multi-term ranked" | "Multi-angle ranked" | Optional |
| `aoa intent recent` - "See what's being worked on" | Keep | No |

### Intent Tracking Section

| Line | Current | Proposed | Change? |
|------|---------|----------|---------|
| 143 | "Every tool call is captured automatically" | Keep | No |
| 146 | Status example shows "61 intents" | Keep | No |
| 149 | "This helps predict which files you'll need next" | Keep | No |

---

## 6. Terminology Consistency Matrix

### Core Terms (Keep)

| Term | Used In | Meaning |
|------|---------|---------|
| **intent** | Everywhere | What the user is doing (tracked) |
| **intents** | Status line | Count of intent records |
| **hit rate** | Status line, metrics | Prediction accuracy % |
| **target** | Internal | File/symbol being found |

### New Terms (Introduce)

| Term | Replace | Context |
|------|---------|---------|
| **angle** | "group", "method" | 5 approach methods |
| **attack** | "combined answer" | The orchestration |
| **symbol angle** | "local search" | O(1) index lookup |
| **intent angle** | "intent tracking" | Intent-based prediction |
| **intel angle** | "knowledge repos" | External reference |
| **signal angle** | "multi-term", "ranking" | Combined ranking |
| **strike angle** | "prediction", "prefetch" | Predictive file loading |

### Avoid

| Term | Why | Use Instead |
|------|-----|-------------|
| "pattern" (for intent) | Too abstract | "intent" |
| "vector" | Military jargon | "angle" |
| "lock" | Action, not approach | Use naturally if fits |
| "acquisition" | Corporate jargon | "lookup", "hit" |

---

## 7. Implementation Checklist

### Phase 1: Quick Wins (5 min total)

- [ ] `cli/aoa` line ~881: Subtitle → "5 angles. 1 attack."
- [ ] `install.sh` line 31: "Deploying 5 angles..."
- [ ] `install.sh` line 197: "Attack Ready!"
- [ ] `aoa-status.sh` line 71,80: "learning..." → "calibrating..."

### Phase 2: CLI Groups (15 min)

- [ ] `cli/aoa` help section headers → SYMBOL ANGLE, INTENT ANGLE, etc.
- [ ] `cli/aoa` command descriptions where noted above

### Phase 3: README (10 min)

- [ ] Section headers: "The Five Angles", "Hit Rate", "Deploy"
- [ ] Table: Update group names to angle names
- [ ] "Why aOa" section: Update definitions

### Phase 4: CLAUDE.md (5 min)

- [ ] Header: "5 Angles. 1 Attack."
- [ ] Rule names where noted

### Phase 5: Verify Consistency

- [ ] Run `grep -r "attack group" .` → should be 0
- [ ] Run `grep -r "knowledge repo" .` → should only be in legacy/docs
- [ ] Status line still shows "intents" (intentional - keep)

---

## 8. Visual Diff Example

### CLI Help (Before)

```
                              AOA
                       Bold tools for Claude Code

STATUS COMMANDS
  status                 Show status line (context, cost, usage)

LOCAL SEARCH
  search <term>          Find symbol/term in local codebase
```

### CLI Help (After)

```
                              AOA
                       5 angles. 1 attack.

ATTACK STATUS
  status                 Show attack status (hit rate, intents)

SYMBOL ANGLE
  search <term>          O(1) symbol lookup
```

---

## 9. What Does NOT Change

| Element | Why |
|---------|-----|
| "intents" in status line | Intent is concrete, keep it |
| CLI command names (`aoa search`, `aoa intent`) | User muscle memory |
| "hit rate" | Already attack-themed |
| Traffic light colors | Universal understanding |
| Config file names | Breaking change, not worth it |
| API endpoint paths | Breaking change |

