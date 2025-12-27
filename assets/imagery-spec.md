# aOa Imagery Specification

## Visual Hierarchy

```
                        ┌─────────────┐
                        │   SEARCH    │
                        │  O(1) index │
                        └──────┬──────┘
                               │
        ┌─────────────┐        │        ┌─────────────┐
        │   INTENT    │        │        │  KNOWLEDGE  │
        │  Tag affinity│───────┼────────│ External repos│
        └─────────────┘        │        └─────────────┘
                               │
                        ┌──────┴──────┐
                        │             │
                        │    O(1)     │
                        │             │
                        │   CENTER    │
                        │             │
                        └──────┬──────┘
                               │
        ┌─────────────┐        │        ┌─────────────┐
        │   RANKING   │────────┼────────│ PREDICTION  │
        │  Recency +  │        │        │  Prefetch   │
        └─────────────┘        │        └─────────────┘
                               │
                        ┌──────┴──────┐
                        │   OUTPUT    │
                        │ One Answer  │
                        └─────────────┘
```

---

## Image 1: HERO

**Purpose**: The central concept - O(1) at center with 5 attack vectors

**Visual Description**:
- Center: Large glowing "O" or circle - represents O(1), speed, intelligence
- 5 radiating paths extending outward to 5 nodes
- Each node represents one attack group
- Clean, crisp iconography
- Mind map / radial diagram style

**The 5 Attack Groups** (nodes around center):

### GROUP 1: SEARCH
**Icon Concept**: Magnifying glass, crosshair, or radar

| Method | What It Does |
|--------|--------------|
| Symbol search | O(1) inverted index lookup |
| Multi-term | Ranked by density across terms |
| Pattern search | Agent-driven regex matching |
| File glob | Pattern matching on paths |
| Changes | Recently modified files |

### GROUP 2: INTENT
**Icon Concept**: Brain, lightbulb, or neural network

| Method | What It Does |
|--------|--------------|
| Intent tracking | Learns from every tool call |
| Tag affinity | Groups files by intent (#auth, #python, #config) |
| Recent intents | What's hot right now in the session |
| Intent stats | Accumulated knowledge about patterns |

### GROUP 3: KNOWLEDGE
**Icon Concept**: Book, database, or library

| Method | What It Does |
|--------|--------------|
| Repo search | Search external codebases (Flask, React, etc.) |
| Repo multi | Multi-term ranked search in knowledge repos |
| Repo files | Browse indexed external files |
| Isolation | Knowledge never pollutes local results |

### GROUP 4: RANKING
**Icon Concept**: Stack, sorted list, or podium

| Signal | What It Does |
|--------|--------------|
| Recency | Time decay - recently touched = higher |
| Frequency | Access count - often touched = higher |
| Filename boost | Name matching (exact > prefix > contains) |
| Transitions | P(B\|A) - "after file A, you usually need B" |
| Composite score | Weighted combination of all signals |

### GROUP 5: PREDICTION
**Icon Concept**: Crystal ball, forward arrow, or target lock

| Method | What It Does |
|--------|--------------|
| Predictive prefetch | Files ready before you ask |
| Confidence scoring | Only surface high-confidence (>60%) results |
| Session learning | Gets smarter every tool call |
| Hit tracking | Measures and improves accuracy |

### OUTPUT: ONE ANSWER
**Icon Concept**: Bullseye, single point, or checkmark

| Outcome | What It Means |
|---------|---------------|
| One confident result | All methods converge to best answer |
| Explainable | `aoa why <file>` shows reasoning |
| Fast | <50ms prediction time |
| Accurate | 100% on knowledge queries |

**Style**:
- Deep navy background (#0A1628)
- Electric cyan for O and paths (#00D4FF)
- Lighter cyan variants for nodes
- Minimal, clean lines
- No text labels (icons only)
- 16:9 aspect ratio

---

## Image 2: CONVERGENCE

**Purpose**: Show how all methods flow into one confident answer

**Visual Description**:
- 5 distinct light beams/paths approaching from different angles
- They converge on a single central point
- The center is calm, stable - not explosive
- Resolution, not collision

**Style**:
- Deep navy/space background
- Cyan spectrum for beams (5 shades)
- Gold/white glow at convergence point
- Abstract, elegant geometry
- 4:3 aspect ratio

---

## Image 3: STATUS

**Purpose**: The outcome - everything is optimal

**Visual Description**:
- Minimal dashboard aesthetic
- One flat horizontal line (the O(1) promise)
- 5 small indicator dots, all green
- Spacious, not cluttered

**Style**:
- Deep navy background
- Cyan for the line
- Green (#00FF88) for indicators
- HUD / instrument panel feel
- 16:9 aspect ratio

---

## Color Palette

| Color | Hex | Use |
|-------|-----|-----|
| Deep Navy | #0A1628 | Background |
| Electric Cyan | #00D4FF | Primary accent, O, paths |
| Success Green | #00FF88 | Indicators, status |
| Warm Gold | #FFB800 | Convergence point |
| Light Cyan | #7DD8FF | Secondary nodes |

---

## Icon Style Guide

- **Line weight**: Thin, consistent (2-3px at 1K)
- **Corners**: Slightly rounded, not sharp
- **Fill**: Outline only, or subtle gradient fill
- **Glow**: Subtle outer glow on primary elements
- **Spacing**: Generous negative space

---

## The Story These Tell

1. **HERO**: "Here's how aOa thinks - O(1) intelligence at the center, multiple attack angles around it"

2. **CONVERGENCE**: "All those methods flow into one answer"

3. **STATUS**: "And here's the result - everything working, flat cost, optimal"

---

## Manual Generation Notes

When generating manually, try to match:
- The mind map structure for hero
- The calm convergence (not explosive) for convergence
- The minimal HUD aesthetic for status

Once you have a style that works, we can use that as reference for consistency.
