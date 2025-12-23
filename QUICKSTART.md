# aOa Quickstart

## 5-Minute Setup

```bash
# 1. Clone
git clone https://github.com/you/aOa
cd aOa

# 2. Install (starts services)
./install.sh

# 3. Test it works
aoa health
```

## Your First Search

```bash
# Search for a term (current directory is indexed by default)
aoa search handleAuth

# Multi-term ranked search
aoa multi auth,login,session

# See what changed recently
aoa changes 1h

# List files
aoa files "*.py"
```

## Add a Knowledge Repo

```bash
# Clone and index Flask
aoa repo add flask https://github.com/pallets/flask

# Search in Flask
aoa repo flask search Blueprint

# List Flask files
aoa repo flask files "*.py"
```

## Claude Code Integration

Install hooks to enable intent tracking:

```bash
# Install hooks to your project
./src/hooks/install-hooks.sh /path/to/your/project

# Or manually copy to .claude/hooks/
cp src/hooks/intent-*.py /path/to/your/project/.claude/hooks/
cp src/hooks/settings.local.json /path/to/your/project/.claude/
```

**Restart Claude Code after installing hooks.**

On your next prompt, you'll see:
```
⚡ aOa │ 12 intents │ 5 tags │ 34ms │ reading python api
```

## Intent Tracking

The hooks learn automatically as you work:

```bash
# See what you've been working on
aoa intent recent

# See all intent tags
aoa intent tags

# Files associated with a tag
aoa intent files authentication
```

## Transparency

```bash
# View network topology
curl localhost:8080/network

# Verify isolation (no internet access except proxy)
./scripts/verify-isolation.sh

# See all requests
curl localhost:8080/audit
```

## Benchmark

```bash
# Compare aOa vs grep
./scripts/benchmark.sh /path/to/your/code
```

## Configuration

Edit `.aoa/config.json` for settings.
Edit `.aoa/whitelist.txt` to add allowed URLs.

---

**That's it. You're running O(1) search.**
