# Messaging Unification - Working Draft

> **Purpose**: Unified "Angle of Attack" branding
> **Status**: SELECTED - Option A (Angles + Attack)

---

## The Model

### Two-Layer Concept

```
┌─────────────────────────────────────────────────┐
│                  THE ATTACK                      │
│   Sophisticated ranking + orchestration          │
│   Combines all angles → High hit rate            │
└──────────────────────┬──────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ Symbol  │   │ Pattern │   │  Intel  │  ...
   │  Angle  │   │  Angle  │   │  Angle  │
   └─────────┘   └─────────┘   └─────────┘
        │              │              │
   O(1) lookup   History-based   External docs
```

**Layer 1 - The Angles**: Individual approach methods
**Layer 2 - The Attack**: Orchestration that combines angles for accuracy

### The Vocabulary

| Term | Meaning |
|------|---------|
| **Angle** | One approach method (there are 5) |
| **Attack** | The strategy combining all angles |
| **Intent** | What the user is trying to do (concrete, tracked) |
| **Hit** | Accurate prediction based on intent |
| **Hit Rate** | Accuracy % of combined attack |
| **Target** | The file/symbol being acquired |

**Note**: "Intent" stays. It's not abstract - it's the literal mapping of what's happening in the system. We track intent, we predict from intent. That's the core.

---

## The O(1) Advantage

### Everything is O(1)

| Operation | Cost | How |
|-----------|------|-----|
| Symbol lookup | O(1) | Pre-built index |
| Intent capture | O(1) | Lazy, end-of-request hook |
| Intent-based prediction | O(1) | Tag → file mapping |

### Intent Capture Cost

**Per request**: ~10-20 tokens

- 5 intent tags × ~2 tokens each = ~10 tokens
- Hook overhead = ~5-10 tokens
- **Total**: 10-20 tokens per request, captured lazily at end

This is the price of omniscience. 10-20 tokens to know what you're working on.

### What Intent Gives You (That LSP Can't)

| Capability | LSP/ctags | aOa Intent |
|------------|-----------|------------|
| Code structure | Yes | Yes (via Symbol Angle) |
| What you're trying to do | No | Yes |
| Cross-file workflow patterns | No | Yes |
| Language agnostic | Partial | Full |
| Learns from your behavior | No | Yes |

**The gap**: LSP knows code. aOa knows code + intent.

- LSP: "Here are all functions named `auth`"
- aOa: "You're working on auth, and based on your intent, you'll need `session.py` next"

**Why this matters**:
- LSP is language-specific, requires setup per language
- Intent is language-agnostic - same 10-20 tokens works on Python, Rust, Go, anything
- Intent tracks workflow, not just symbols
- Intent enables prediction that structure-only tools can't

---

## The Five Angles

| Angle | What It Does | CLI |
|-------|--------------|-----|
| **Symbol Angle** | O(1) index lookup | `aoa search` |
| **Intent Angle** | What the user is doing, tracked | `aoa intent` |
| **Intel Angle** | External knowledge repos | `aoa repo` |
| **Signal Angle** | Multi-term ranking | `aoa multi` |
| **Strike Angle** | Predictive prefetch | `aoa context` |

**Tagline**: "5 angles. 1 attack. High hit rate."

---

## What Changes

### CLI Help Header

| Current | New |
|---------|-----|
| `Bold tools for Claude Code` | `5 angles. 1 attack. High hit rate.` |

### CLI Command Groups

**Current:**
```
STATUS COMMANDS
LOCAL SEARCH
PATTERN SEARCH
INTENT TRACKING
URL WHITELIST
KNOWLEDGE REPOS
```

**New:**
```
SYMBOL ANGLE
  search <term>         O(1) symbol lookup
  files [pattern]       File listing

INTENT ANGLE
  intent recent         Recent intents tracked
  intent tags           Intent categories
  intent files <tag>    Files by intent

SIGNAL ANGLE
  multi <t1,t2,...>     Multi-angle query
  changes [time]        Recent file changes

INTEL ANGLE
  repo list             External knowledge sources
  repo add <n> <url>    Add intel source
  repo <name> search    Search external docs

STRIKE ANGLE
  context <prompt>      Predict targets for intent
  why <file>            Explain hit reasoning

ATTACK STATUS
  health                System status
  status                Hit rate + angles active
  services              Running services
```

### Status Line

| Current | New |
|---------|-----|
| `105 intents` | Keep as-is (intent is concrete, not abstract) |
| `searching shell markdown` | Same (these are intent tags) |

### README Sections

| Current | New |
|---------|-----|
| How It Works | The Five Angles |
| The Numbers | Hit Rate |
| Quick Start | Deploy |

### install.sh

| Current | New |
|---------|-----|
| `Installation Starting...` | `Deploying 5 angles...` |
| `Installation Complete!` | `Attack ready. Hit rate: calibrating...` |

### CLAUDE.md

| Current | New |
|---------|-----|
| `Bold tools for Claude Code` | `5 angles. 1 attack.` |

---

## Implementation Order

### Quick Wins (< 5 min each)

1. [ ] CLI help header → `5 angles. 1 attack. High hit rate.`
2. [ ] install.sh welcome → `Deploying 5 angles...`
3. [ ] install.sh complete → `Attack ready.`
4. [ ] CLAUDE.md intro → `5 angles. 1 attack.`

### Medium (10-15 min each)

5. [ ] CLI command groups → SYMBOL ANGLE, INTENT ANGLE, etc.
7. [ ] README section headers → The Five Angles, Hit Rate, Deploy

### Larger

8. [ ] README body copy to use angles/attack terminology
9. [ ] Landing page copy (if created)

---

## Decisions Made

- **Keep CLI commands as-is**: `aoa search`, `aoa intent`, etc. (don't rename to `aoa symbol`)
- **Rename GROUP headers only**: Group commands under angle names
- **Keep "intent"**: It's concrete - the literal mapping of what's happening. Not abstract.
- **"hit rate"**: The accuracy metric stays as "hit rate" (already attack-themed)
