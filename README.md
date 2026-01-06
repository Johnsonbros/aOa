# aOa - Angle O(1)f Attack

![The O(1) Advantage](assets/generated/hero.png)

> **Same cost for 100 files or 100,000.**

---

## The Problem You Know Too Well

Watch any AI coding session. This happens every time:

```
Claude: "Let me search for authentication..."
Claude: "Let me also check login..."
Claude: "I should look at session handling..."
Claude: "Let me read these 8 files..."
Claude: "Now I understand the pattern."
```

**6,600 tokens.** Just to find what was obvious to you from the start.

The cost compounds. Bigger codebases mean more searching. More searching means more tokens. More tokens means more money. The orange line keeps rising.

---

## What If It Didn't Have To?

```
You: "Fix the auth bug"
aOa: [Already loaded: auth.py, session.py, middleware.py]
Claude: "I see the issue. Line 47."
```

**150 tokens.** Same result.

aOa learns what you need and has it ready. The cost stays flat—whether you have 100 files or 100,000.

---

## The Five Angles

![Five angles, one attack](assets/generated/convergence.png)

aOa approaches every search from **5 angles**, converging on **1 attack**:

| Angle | What It Does |
|-------|--------------|
| **Symbol** | O(1) lookup across your entire codebase |
| **Intent** | Learns from every tool call, builds tag affinity |
| **Intel** | Searches external repos without polluting your results |
| **Signal** | Recency, frequency, filename matching, transitions |
| **Strike** | Prefetches files before you ask |

All five angles converge into **one confident answer**.

---

## Hit Rate

| Metric | Without aOa | With aOa | Savings |
|--------|-------------|----------|---------|
| Tool calls | 7 | 2 | 71% |
| Tokens | 8,500 | 1,150 | **86%** |
| Time | 2.6s | 54ms | 98% |
| Hit rate | ~70% | **100%** | Perfect |

---

## Deploy

```bash
git clone https://github.com/anthropics/aoa && cd aoa
./install.sh
aoa health
```

That's it. All five angles deploy and start calibrating immediately.

---

## The Outcome

![All systems optimal](assets/generated/status.png)

Your status line shows what's happening:

```
⚡ aOa 🟢 100% │ 136 intents │ 45ms │ editing python auth
```

The more you use Claude, the smarter aOa gets. Every tool call teaches it your patterns. Every session makes predictions more accurate.

---

## Why "aOa"?

**Angle O(1)f Attack**

- **O** = Big O notation. O(1) constant time. Same cost regardless of size.
- **Angle** = 5 approach methods (Symbol, Intent, Intel, Signal, Strike).
- **Attack** = The orchestration that combines all angles for accuracy.

---

## Trust

- Runs locally (Docker)
- No data leaves your machine
- Every prediction is explainable (`aoa why <file>`)
- Open source, MIT licensed

---

**The flat line wins.**

