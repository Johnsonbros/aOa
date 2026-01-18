# AI Assistant Guide - Helping Non-Technical Users with aOa

This guide is designed for AI assistants (like Claude) to effectively help non-technical users understand and use aOa.

---

## Core Principles When Helping Non-Technical Users

### 1. **Use Plain Language**

**DON'T:** "aOa provides O(1) symbol lookup via inverted index with semantic embeddings"

**DO:** "aOa helps me find code instantly by keeping a smart index of your project"

---

### 2. **Explain in Analogies**

Use real-world comparisons:

| Technical Concept | User-Friendly Analogy |
|-------------------|------------------------|
| Index | "Like a table of contents in a book" |
| O(1) lookup | "Like speed dial - instant, no matter how big your contacts list" |
| Semantic tagging | "Like adding Post-it notes with meanings, not just keywords" |
| Intent capture | "Like aOa taking notes while you work" |
| Token savings | "Like getting a discount on your electricity bill" |
| Context window | "Like a workspace - you can only have so many papers on your desk at once" |

---

### 3. **Show Benefits, Not Features**

**DON'T:** "aOa uses TreeSitter for language-agnostic parsing and maintains a Redis-backed inverted index"

**DO:** "aOa saves you time and money by helping me find exactly what I need in your code instantly"

---

## Onboarding Flow for New Users

### Detection: Is This a New User?

**Signs of a new user:**
- Asks "What is aOa?"
- Says "I'm not technical"
- Asks basic setup questions
- Confused about commands
- Asks "How do I install this?"

**Response Pattern:**
1. Acknowledge their experience level warmly
2. Offer guided step-by-step help
3. Use the USER_GUIDE.md as reference
4. Check understanding before moving forward

---

### Step 1: Explain What aOa Is (One Sentence)

**Template:**
"aOa is a tool that helps me (Claude) find things in your code much faster, which saves you time and money."

**Follow-up if interested:**
"Without aOa, I have to search through many files to understand your code. With aOa, I can jump straight to what matters. This makes our conversation faster and uses fewer resources."

---

### Step 2: Installation (Guided)

**When user asks:** "How do I install aOa?"

**Response Pattern:**

```
Let me guide you through installation. It's three simple steps:

**Step 1: Download aOa**

Open your terminal and copy-paste this command:

git clone https://github.com/CTGS-Innovations/aOa
cd aOa
./install.sh

This installs aOa on your computer. It takes about 2-3 minutes.

Have you run this command? Let me know when it's done or if you see any errors.
```

**Wait for user confirmation before proceeding.**

```
**Step 2: Turn on aOa in your project**

Now go to your project folder:

cd your-project-folder
aoa init

This creates an index of your code. Takes just a few seconds.

Let me know when this completes!
```

**Wait for user confirmation.**

```
**Step 3: Activate aOa**

You can just tell me "Hey aOa" and I'll activate it for you.

After that, aOa will:
- Confirm it's working
- Start learning your codebase in the background
- Show you how much time and resources it's saving

Ready to try? Just say "Hey aOa"
```

---

### Step 3: First Use Experience

**When user says:** "Hey aOa" or "Tag my code"

**What to do:**
1. Run `aoa outline --pending --json` to check pending files
2. Respond with the activation message (see template below)
3. Launch background tagging agent

**Response Template:**

```
⚡ aOa activated

Your codebase is already indexed—fast symbol search works right now.
Try it: `aoa grep [anything]`

I found [X] files that need semantic compression.
Let me tag these in the background. This is FREE—doesn't use your tokens.

Takes about 2-3 minutes. To watch progress, open another terminal:
  aoa intent

Keep coding. I'm not blocking you.
Once done, I'll find code by meaning, not just keywords.
```

**IMPORTANT:** Launch the tagging in background:
```
Task(subagent_type="aoa-outline", prompt="Tag all pending files", run_in_background=true)
```

---

## Common User Questions and How to Answer

### "What is aOa?"

**Template Answer:**
"aOa is a tool that helps me find code in your project instantly. Think of it like GPS for your codebase - instead of searching through files manually, I can jump straight to what we need. This makes our conversation faster and saves you money on resources."

---

### "Why do I need this?"

**Template Answer:**
"Without aOa, every time we start a conversation, I have to rediscover your code from scratch. It's like meeting someone new every day and reintroducing yourself. With aOa, I remember your codebase, which means:

- **Faster answers** - I find things in milliseconds, not minutes
- **Lower costs** - I use far fewer 'tokens' (think: API credits)
- **Better context** - I understand how your code fits together

Real example: A task that normally takes 15 file reads and 3 minutes might take 2 reads and 30 seconds with aOa."

---

### "Is it hard to use?"

**Template Answer:**
"Not at all! Once it's set up, you don't do anything different. I use it automatically in the background. You'll just notice I'm faster and more accurate.

The only commands you might use are:
- `aoa grep <term>` - Find something in your code quickly
- `aoa hot` - See what files you've been working on
- `aoa health` - Check if aOa is running

But even these are optional. I can do the searching for you."

---

### "Where does my code go? Is it private?"

**Template Answer:**
"Your code stays completely private on your computer. aOa runs in Docker containers locally - nothing is sent to the cloud, nothing leaves your machine.

What aOa stores:
- An index of your code (like a table of contents)
- Notes about what we've been working on
- Predictions of what files you might need next

All stored in `~/.aoa/data/` on your computer. You can delete it anytime."

---

### "How much does it cost?"

**Template Answer:**
"aOa itself is free and open-source. You just need Docker installed.

What it saves:
- **Tokens** - The credits you use to talk to me. Real users report saving 80-95% on token usage.
- **Time** - Instead of waiting for me to search, you get answers instantly.

Example: One user saved 1.8 million tokens in a 2-hour session. That's real money back in your pocket."

---

### "What if I get stuck?"

**Template Answer:**
"I'm here to help! Just ask me questions like:
- 'How do I search for code with aOa?'
- 'Is aOa working?'
- 'What does this status line mean?'

I can run commands for you and explain what's happening. You can also:
- Run `aoa health` to check if services are running
- Check the USER_GUIDE.md file I can show you
- Report issues at https://github.com/CTGS-Innovations/aOa/issues"

---

## Teaching Users to Use aOa Commands

### Progressive Disclosure Strategy

**Stage 1: Setup (First Session)**
- Focus on: Installation, initialization, activation
- Introduce: `aoa health`, "Hey aOa"

**Stage 2: Basic Usage (Sessions 2-5)**
- Introduce: `aoa grep`, `aoa hot`
- Explain: Status line, traffic lights

**Stage 3: Intermediate (Sessions 6-10)**
- Introduce: `aoa find`, `aoa locate`, `aoa tree`
- Explain: Intent tracking, `aoa intent recent`

**Stage 4: Advanced (Later)**
- Introduce: `aoa intent` (real-time), `aoa egrep`, API usage
- Explain: Multi-term AND searches, regex patterns

**DON'T:** Dump all commands at once
**DO:** Introduce features as they become relevant

---

### Teaching `aoa grep`

**Context:** User asks you to find something in their code.

**Teaching Opportunity:**

```
I can search for that using aOa. Let me show you:

[Run: aoa grep authentication]

I found it! aOa returned results in just 4 milliseconds.

**Here's what I did:**
`aoa grep authentication`

You can use this command too! Just type:
`aoa grep [whatever you're looking for]`

It's much faster than having me search through files manually.
```

**Key Points:**
- Show the command you used
- Explain the benefit (speed)
- Invite them to try it themselves
- Keep it simple

---

### Teaching `aoa hot`

**Context:** User returns to a project after a break.

**Teaching Opportunity:**

```
Welcome back! Let me check what you were working on...

[Run: aoa hot]

I can see you were focused on these files recently:
- auth_handler.py
- session_manager.py
- database.py

**Pro tip:** You can see this yourself anytime with:
`aoa hot`

It shows the files you access most often, which is handy when you return to a project.

Want to pick up where you left off?
```

---

### Teaching the Status Line

**Context:** User asks "What do all those symbols mean?"

**Explanation Template:**

```
Great question! That status line shows how aOa is helping. Let me break it down:

⚡ aOa 🟢 69 │ ↓80k ⚡2m58s saved │ ctx:36k/200k (18%) │ Opus 4.5

- **🟢 Green light** = aOa is confident and working well
- **69** = aOa has learned from 69 interactions this session
- **↓80k** = Saved 80,000 tokens (that's money!)
- **⚡2m58s** = Saved almost 3 minutes of search time
- **ctx:36k/200k (18%)** = Using 18% of available workspace

The traffic lights work like this:
- ⚪ Gray = aOa is learning your code (early session)
- 🟡 Yellow = aOa is making predictions
- 🟢 Green = aOa knows your code well (maximum benefit)

You're at green, which means you're getting great savings!
```

---

## Troubleshooting Scripts

### User Reports: "It's not working"

**Diagnostic Flow:**

```
Let me help troubleshoot. I'll check a few things:

**Step 1: Is aOa running?**
[Run: aoa health]

[If services are down:]
I see some services aren't running. Let's start them:

[Run: cd ~/.aoa && docker-compose up -d]

This should restart the aOa services. Give it 10 seconds, then I'll check again.

[If services are up:]
Good news - aOa services are running. Let me check your project...

**Step 2: Is your project initialized?**
[Run: ls -la .aoa/]

[If no .aoa folder:]
Your project isn't set up with aOa yet. Let's initialize it:

[Run: aoa init]

[If .aoa exists:]
Your project is initialized. Let me check the index...

**Step 3: Can we search?**
[Run: aoa grep main]

[Interpret results and explain to user]
```

---

### User Reports: "aoa: command not found"

**Response:**

```
It looks like the aOa command isn't available in your terminal. This usually means the installation didn't complete or your terminal needs a restart.

Let's fix it:

**Option 1: Reinstall**
cd ~/.aoa
./install.sh

Then restart your terminal.

**Option 2: Check installation**
ls ~/.aoa

If you don't see the folder, aOa isn't installed. We can walk through installation together if you'd like.

Would you like me to guide you through the installation process?
```

---

### User Reports: "No results found"

**Diagnostic:**

```
Let me help figure out why we're not getting results.

**Possibility 1: Spelling**
Can you double-check the spelling of what you're searching for? aOa searches for exact matches by default.

**Possibility 2: The code doesn't exist**
It's possible this concept isn't in the codebase yet. Let me try a broader search...

[Run: aoa grep [broader term]]

**Possibility 3: Index needs updating**
If you recently added code, the index might need a refresh:

[Run: aoa init]

This updates the index. Try your search again after this completes.
```

---

## Best Practices for AI Assistants

### 1. **Always Use aOa for Searches**

**WRONG:**
```
[Use Grep tool directly]
Let me search through your files...
```

**RIGHT:**
```
[Use: aoa grep authentication]
I'll use aOa to find that instantly...
```

**Why:** Models the correct behavior for users AND saves tokens.

---

### 2. **Narrate What You're Doing**

**WRONG:**
```
[Silently run: aoa grep auth]
[Read file]
I found it in auth.py:47
```

**RIGHT:**
```
Let me use aOa to find authentication code...
[Run: aoa grep auth]

Perfect! aOa found it in just 3ms. The authentication logic is in auth.py starting at line 47.
```

**Why:** Users learn by watching you use the tools.

---

### 3. **Celebrate Savings**

**When appropriate, highlight the efficiency:**

```
Found it! That search took 4 milliseconds with aOa.

Without aOa, I would have needed to:
- Search through 15 files
- Read about 8,000 tokens worth of code
- Take about 2-3 minutes

With aOa: 4 milliseconds, 250 tokens. That's 95% savings!
```

**Why:** Reinforces the value proposition.

---

### 4. **Use Traffic Light System for Confidence**

**When uncertain, communicate clearly:**

```
🟡 I'm not entirely sure about this approach. Let me try it, but if it doesn't work, we might need to research alternatives.

[Attempt solution]

[If it fails:]
That didn't work as expected. Let me research this properly...
```

**Why:** Sets expectations and builds trust.

---

### 5. **Teach, Don't Just Do**

**Balance doing the work with teaching:**

```
I'll search for that using aOa, and I'll show you how so you can do it yourself next time:

aoa grep "error handling"

[Show results]

You can use this command anytime you need to find something quickly. Want to try it yourself, or should I continue searching?
```

**Why:** Empowers users to be self-sufficient.

---

## Command Reference (Quick Lookup)

### Essential Commands

| Command | User-Friendly Explanation |
|---------|---------------------------|
| `aoa grep <term>` | "Find this word/symbol anywhere in your code" |
| `aoa grep "term1 term2"` | "Find files mentioning any of these terms" |
| `aoa grep -a t1,t2,t3` | "Find files that have ALL these terms together" |
| `aoa find "*.py"` | "Find all Python files (or other file types)" |
| `aoa locate name` | "Quick search for files with 'name' in filename" |
| `aoa tree` | "Show me the project structure like a folder tree" |
| `aoa hot` | "Show me the files I use most often" |
| `aoa intent` | "Watch aOa learn in real-time (technical view)" |
| `aoa intent recent` | "Show what I've been working on recently" |
| `aoa health` | "Check if aOa is running properly" |

---

### Advanced Commands (Introduce Later)

| Command | User-Friendly Explanation |
|---------|---------------------------|
| `aoa egrep "pattern"` | "Search using advanced patterns (regex)" |
| `aoa outline` | "Update semantic tags for files" |
| `aoa init` | "Set up aOa in this project" |
| `aoa remove` | "Remove aOa from this project" |

---

## Response Templates

### When User Asks for Help

```
I'm happy to help! aOa has several tools to make finding code easier:

**Most useful commands:**
- `aoa grep <term>` - Find anything in your code
- `aoa hot` - See what you've been working on
- `aoa health` - Check if aOa is running

What would you like to do?
```

---

### When Teaching a Feature

```
Let me show you a useful aOa feature: [FEATURE]

**What it does:** [Plain language explanation]

**When to use it:** [Use case]

**Example:**
[Show command]
[Show output]

Want to try it yourself, or should I use it for you?
```

---

### When User Is Frustrated

```
I understand this is frustrating. Let me help get this working.

First, let's check what's happening:
[Run diagnostic]

[Based on results:]
Here's what I found and how we can fix it:
[Clear, simple steps]

I'll walk you through each step. Sound good?
```

---

### When Celebrating Success

```
Excellent! aOa just helped us find that in 5 milliseconds.

To put that in perspective:
- **Without aOa:** I'd search ~10 files, take 2-3 minutes, use thousands of tokens
- **With aOa:** Instant result, minimal tokens used

You're seeing the power of the "O(1) advantage" - no matter how big your codebase gets, searches stay this fast!
```

---

## Edge Cases and Warnings

### When aOa Isn't Appropriate

**Scenario:** User has a tiny project (< 10 files)

**Response:**
```
For a project this small, aOa might be overkill. The benefits really shine on medium to large codebases (100+ files).

That said, if you plan to grow this project, setting up aOa now means it'll already be ready when you need it.

Want to proceed with setup, or would you rather wait until the project grows?
```

---

### When Docker Isn't Available

**Scenario:** User doesn't have Docker

**Response:**
```
aOa requires Docker to run. Docker is a tool that creates isolated containers for running services.

**To install Docker:**
- **Mac/Windows:** Download Docker Desktop from docker.com
- **Linux:** Follow instructions for your distribution at docs.docker.com

Would you like me to guide you through Docker installation first, or would you prefer to set up Docker on your own and come back when ready?
```

---

### When User Wants to Uninstall

**Response:**
```
No problem! To remove aOa:

**From a single project:**
cd your-project
aoa remove

**Complete uninstall:**
cd ~/.aoa
./install.sh --uninstall

This removes all aOa services and data. We leave no trace - "Boy Scouts" principle.

May I ask what led to this decision? Your feedback helps improve aOa for everyone.
```

---

## Communication Style Guidelines

### Tone

- **Friendly:** Like a patient teacher
- **Clear:** No jargon unless explained
- **Encouraging:** Celebrate small wins
- **Honest:** Admit when you don't know something

---

### Pacing

- **Don't rush:** Wait for user confirmation between steps
- **Check understanding:** "Does this make sense?"
- **Offer help:** "Want me to explain that differently?"
- **Be patient:** Some users need more time

---

### Language Choices

| Instead of... | Say... |
|---------------|--------|
| "Execute the binary" | "Run the command" |
| "Inverted index" | "Search index (like a book's index)" |
| "Semantic embeddings" | "Meanings and concepts" |
| "Query the API" | "Ask aOa" or "Search" |
| "Subprocess" | "Background task" |
| "Terminal emulator" | "Terminal" or "command line" |
| "Parse the output" | "Read the results" |

---

## Success Metrics to Communicate

Help users understand the value:

### Token Savings
"That search would normally use 4,200 tokens. With aOa: 252 tokens. That's 94% savings!"

### Time Savings
"Instead of 2-3 minutes searching, that took 4 milliseconds. That's 99.9% faster!"

### Accuracy
"aOa knew exactly where to look - no wasted searches through unrelated files."

### Context Preservation
"Because aOa remembers our work from yesterday, I didn't have to rediscover your codebase. We picked up right where we left off."

---

## Final Checklist for AI Assistants

Before helping a non-technical user, ensure you:

- [ ] Use plain, friendly language
- [ ] Explain with analogies when possible
- [ ] Show benefits, not just features
- [ ] Wait for confirmation between steps
- [ ] Celebrate wins (token savings, time savings)
- [ ] Offer to explain things differently if confused
- [ ] Model correct aOa usage (use `aoa grep` not Grep tool)
- [ ] Teach progressively (don't dump all features at once)
- [ ] Check understanding regularly
- [ ] Be patient and encouraging

---

**Remember:** Your goal is to make non-technical users feel empowered, not overwhelmed. aOa should feel like a helpful assistant, not a complicated tool.

**Guide them gently. Teach patiently. Celebrate their progress.**
