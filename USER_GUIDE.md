# aOa User Guide - For Everyone

Welcome! This guide explains how to use aOa in plain, friendly language. No technical jargon required.

---

## What Is aOa?

Think of aOa as a **smart assistant that helps Claude (the AI) find things faster in your code**.

**The Problem:** When Claude needs to understand your code, it's like searching through a massive library without a card catalog. It reads lots of files, uses lots of resources, and takes time.

**The Solution:** aOa is like giving Claude a GPS for your code. It knows exactly where everything is, so Claude can jump straight to what matters.

**Real Impact:** Instead of Claude spending 2-3 minutes and thousands of "tokens" (think: money) searching, it finds what it needs in milliseconds.

---

## Quick Start (For First-Time Users)

### Step 1: Install aOa (One Time Only)

Open your terminal and run:

```bash
git clone https://github.com/CTGS-Innovations/aOa
cd aOa
./install.sh
```

**What This Does:** Installs aOa on your computer. You only do this once, and it works for all your projects.

**How Long:** About 2-3 minutes.

---

### Step 2: Turn On aOa in Your Project

Go to your project folder and run:

```bash
cd your-project-folder
aoa init
```

**What This Does:** Turns on aOa for this specific project. It creates an index (like a table of contents) of your code.

**How Long:** A few seconds.

---

### Step 3: Say Hello to aOa

Open Claude Code in your project and type:

```
Hey aOa
```

**What Happens:** aOa will:
1. Confirm it's working
2. Show you that searching is already active
3. Start "tagging" your code in the background (this is free and doesn't block you)

You'll see something like:

```
⚡ aOa activated

Your codebase is already indexed—fast symbol search works right now.
Try it: `aoa grep [anything]`

I found 247 files that need semantic compression.
Let me tag these in the background. This is FREE—doesn't use your tokens.

Takes about 2-3 minutes. To watch progress, open another terminal:
  aoa intent

Keep coding. I'm not blocking you.
```

**That's It!** aOa is now working for you.

---

## How to Use aOa Daily

Once aOa is set up, you don't need to do anything special. It works automatically in the background. But here are some useful commands:

### Finding Code

Instead of asking Claude to search through files, use these commands:

#### 1. **Search for a Word or Symbol**

```bash
aoa grep authentication
```

**What It Does:** Finds every place "authentication" appears in your code. Lightning fast.

**When to Use:** When you need to find where something is defined or used.

---

#### 2. **Search for Multiple Things**

```bash
aoa grep "login password session"
```

**What It Does:** Finds files that mention login OR password OR session, ranked by relevance.

**When to Use:** When you're looking for related concepts.

---

#### 3. **Find Files That Have ALL Terms**

```bash
aoa grep -a login,password,session
```

**What It Does:** Finds files that contain login AND password AND session.

**When to Use:** When you need files that deal with multiple specific things together.

---

#### 4. **Find Files by Name**

```bash
aoa find "*.py"
aoa locate auth
```

**What It Does:**
- `aoa find` - Finds files matching a pattern (like all Python files)
- `aoa locate` - Quickly finds files with "auth" in the name

**When to Use:** When you know the file name or type you're looking for.

---

#### 5. **See Your Project Structure**

```bash
aoa tree
aoa tree src/
```

**What It Does:** Shows you a visual tree of your folders and files.

**When to Use:** When you want to understand how your project is organized.

---

#### 6. **See What You've Been Working On**

```bash
aoa hot
```

**What It Does:** Shows the files you access most often.

**When to Use:** When you want to quickly get back to your frequently used files.

---

### Understanding aOa's Learning

aOa learns from your work. Here's how to see what it knows:

#### **Watch aOa Learn in Real-Time**

```bash
aoa intent
```

**What It Does:** Shows you what aOa is learning as you work. It's like watching the AI's "thoughts."

**What You See:**
- What files are being read
- What searches are happening
- How much time and tokens are being saved

**Example Output:**
```
aOa Activity                                                 Session

SAVINGS         ↓847k tokens ⚡47m (rolling avg)
PREDICTIONS     97% accuracy (312 of 321 hits)

ACTION     SOURCE   aOa IMPACT                TAGS
Grep       Claude   ↓94% (4.2k → 252)         #llm #orchestration
Read       Claude   ↓87% (3.8k → 494)         #prompt-engineering
```

**When to Use:** When you're curious about how aOa is helping, or when setting up a new project.

---

#### **See Recent Activity**

```bash
aoa intent recent
```

**What It Does:** Shows what you've been working on recently.

**When to Use:** To remember what you were doing, or to understand patterns in your work.

---

### Checking aOa's Health

#### **Is aOa Running?**

```bash
aoa health
```

**What It Does:** Checks if aOa services are working properly.

**What to Expect:** Green checkmarks if everything is good, red X's if something needs attention.

---

## Understanding the Status Line

When you're working with Claude Code and aOa is active, you'll see a status line at the bottom:

```
⚡ aOa 🟢 69 │ ↓80k ⚡2m58s saved │ ctx:36k/200k (18%) │ Opus 4.5
```

**What Each Part Means:**

| Part | Meaning |
|------|---------|
| `⚡ aOa` | aOa is active |
| `🟢` | Traffic light (see below) |
| `69` | Number of things aOa has learned this session |
| `↓80k` | 80,000 tokens saved (that's money!) |
| `⚡2m58s` | Almost 3 minutes of search time saved |
| `ctx:36k/200k` | Using 36k out of 200k available context |
| `(18%)` | Using 18% of your context window |
| `Opus 4.5` | Which Claude model you're using |

---

### Traffic Light Colors

aOa uses a traffic light system to show how confident it is:

| Color | Meaning | What's Happening |
|-------|---------|------------------|
| ⚪ **Gray** | Learning | aOa is just getting to know your codebase (0-30 observations) |
| 🟡 **Yellow** | Predicting | aOa is making predictions and building accuracy |
| 🟢 **Green** | Confident | aOa knows your codebase well and is saving you lots of time |

**What This Means for You:**
- **Gray**: Give it a few minutes to learn
- **Yellow**: It's working but still learning patterns
- **Green**: You're getting maximum benefit!

---

## Common Use Cases

### Use Case 1: "I Want to Understand This Codebase"

**You Say to Claude:** "Help me understand how authentication works in this project"

**What Happens:**
1. aOa instantly finds all authentication-related files
2. Claude reads only the relevant parts
3. You get an answer in seconds instead of minutes

**Old Way:** 15-20 file reads, 3-4 minutes, thousands of tokens
**aOa Way:** 2-3 targeted reads, 30 seconds, hundreds of tokens

---

### Use Case 2: "I Need to Fix a Bug"

**You Say to Claude:** "There's a bug in the login function"

**What Happens:**
1. aOa knows exactly where the login function is
2. It also knows related files (session management, validation, etc.)
3. Claude has full context immediately

**Old Way:** Search multiple times, read many files, lose track of what's connected
**aOa Way:** Jump straight to the issue with all relevant context ready

---

### Use Case 3: "I Want to Add a Feature"

**You Say to Claude:** "Add a password reset feature"

**What Happens:**
1. aOa finds existing auth patterns in your codebase
2. Claude sees how you've structured similar features
3. The new code matches your existing style automatically

**Old Way:** Generic code that doesn't match your patterns
**aOa Way:** Code that fits seamlessly into your existing architecture

---

### Use Case 4: "I'm Starting a New Session"

**Scenario:** You stopped coding yesterday, coming back today

**What Happens:**
1. aOa already knows what you were working on
2. It has those files ready
3. Claude picks up right where you left off

**Old Way:** Claude rediscovers everything from scratch every session
**aOa Way:** Instant context, no rediscovery needed

---

## Best Practices

### 1. **Let aOa Tag in the Background**

When you first run `Hey aOa`, let the background tagging complete. You can keep working while it runs.

**Why:** Tagging adds "meaning" to your code, not just keywords. It's free (doesn't use your tokens) and makes search much smarter.

---

### 2. **Use `aoa grep` Instead of Asking Claude to Search**

**Instead of:**
```
"Claude, search for all the database connection code"
```

**Do this:**
```bash
aoa grep database connection
```

**Why:** It's faster, cheaper, and you can see results immediately.

---

### 3. **Check `aoa hot` When Resuming Work**

**When you start working:**
```bash
aoa hot
```

**Why:** Quickly see what you've been working on recently.

---

### 4. **Watch `aoa intent` When Learning**

**When exploring a new codebase:**

Open two terminals:
- Terminal 1: Work with Claude Code
- Terminal 2: Run `aoa intent` to watch what's being learned

**Why:** You'll understand how aOa learns and see the token savings in real-time.

---

### 5. **Let aOa Learn Your Patterns**

The more you use Claude Code with aOa, the smarter it gets. Early sessions might be ⚪ gray or 🟡 yellow, but you'll quickly see 🟢 green as it learns.

**Why:** aOa learns YOUR codebase, YOUR patterns, YOUR style. Give it time to understand.

---

## Troubleshooting

### "aoa: command not found"

**Problem:** The aOa CLI isn't in your PATH.

**Solution:**
```bash
cd ~/.aoa
./install.sh
```

Then restart your terminal.

---

### "Services not running"

**Problem:** Docker containers aren't running.

**Solution:**
```bash
cd ~/.aoa
docker-compose up -d
```

Or if using single container:
```bash
docker start aoa
```

---

### "No results found"

**Problem:** You're searching for something that doesn't exist, or the index needs updating.

**Solution:**
1. Check your spelling
2. Try broader search terms
3. Run `aoa health` to ensure services are running

---

### "Status line shows ⚪ gray for a long time"

**Problem:** Not enough activity for aOa to learn.

**Solution:** This is normal. Just keep coding. After 10-20 interactions with Claude, you'll see it change to 🟡 yellow and then 🟢 green.

---

## Privacy and Data

### Where Is Your Data?

**On your computer.** aOa runs in Docker containers on your local machine.

**Nothing leaves your computer.** No cloud services, no external APIs.

---

### What Does aOa Store?

1. **File index** - A searchable index of your code
2. **Intent data** - What you've been working on (file names, search terms, tags)
3. **Predictions** - Files it thinks you'll need next

**All stored locally** in `~/.aoa/data/`

---

### Can I Delete My Data?

**Yes.** Remove aOa from a project:
```bash
aoa remove
```

**Full uninstall:**
```bash
cd ~/.aoa
./install.sh --uninstall
```

Everything gets deleted. We leave no trace.

---

## Advanced Features (Optional)

### Working with Multiple Projects

aOa keeps each project separate. You can have:

```
~/.aoa/
├── work-project/    ← aoa init
├── side-project/    ← aoa init
└── experiment/      ← aoa init
```

Each project has its own index. They don't interfere with each other.

---

### Using the API

aOa has a simple web API for advanced use:

```bash
# Search
curl "localhost:8080/symbol?q=authentication"

# Multi-term search
curl "localhost:8080/multi?q=auth+login+session"

# Recent activity
curl "localhost:8080/intent/recent"
```

**When to Use:** If you want to integrate aOa into your own tools.

---

## Getting Help

### Commands Quick Reference

| Task | Command |
|------|---------|
| Search for code | `aoa grep <term>` |
| Find files | `aoa find "*.py"` |
| Quick file lookup | `aoa locate <name>` |
| See structure | `aoa tree` |
| Frequently used files | `aoa hot` |
| Watch learning | `aoa intent` |
| Recent activity | `aoa intent recent` |
| Check health | `aoa health` |

---

### Need More Help?

1. **Check status:** `aoa health`
2. **Read the README:** [README.md](README.md)
3. **Ask Claude:** "How do I use aOa to..."
4. **Report issues:** https://github.com/CTGS-Innovations/aOa/issues

---

## Summary

**aOa makes Claude faster and cheaper by giving it a map of your code.**

**Three steps to start:**
1. `./install.sh` (one time)
2. `aoa init` (per project)
3. `Hey aOa` (in Claude Code)

**Daily usage:**
- Use `aoa grep` to find code
- Use `aoa hot` to see what you've been working on
- Watch the status line to see savings

**The result:**
- ⚡ Faster development
- 💰 Lower costs (fewer tokens)
- 🧠 Smarter AI that remembers your codebase

**Welcome to the O(1) advantage. Happy coding!**
