#!/bin/bash
# =============================================================================
# aOa Installation Script
# =============================================================================
#
# What this does:
# 1. Checks for Docker (installs if missing)
# 2. Creates .aoa config directory with templates
# 3. Starts services via docker compose
# 4. Installs aoa CLI
# 5. Runs verification
#
# Usage:
#   ./install.sh
#
# Or one-liner:
#   curl -sSL https://aoa.dev/install.sh | sh
#
# =============================================================================

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "  ⚡ aOa - Angle O(1)f Attack"
echo "     Installation Starting..."
echo -e "${NC}"
echo

# =============================================================================
# 1. Check Docker
# =============================================================================

echo -n "Checking for Docker... "
if command -v docker &> /dev/null; then
    echo -e "${GREEN}Found${NC}"
else
    echo -e "${YELLOW}Not found${NC}"
    echo
    echo "Docker is required. Install from:"
    echo "  https://docs.docker.com/get-docker/"
    echo
    exit 1
fi

echo -n "Checking Docker Compose... "
if docker compose version &> /dev/null; then
    echo -e "${GREEN}Found${NC}"
else
    echo -e "${YELLOW}Not found${NC}"
    echo
    echo "Docker Compose is required (usually included with Docker Desktop)"
    exit 1
fi

echo

# =============================================================================
# 2. Create .aoa Config Directory
# =============================================================================

echo "Creating .aoa configuration..."

mkdir -p .aoa

# Default config
cat > .aoa/config.json << 'EOF'
{
  "gateway_port": 8080,
  "max_repo_size_mb": 500,
  "clone_timeout": 300,
  "confidence_threshold": 0.60,
  "learning_phase_minimum": 50
}
EOF

# Default whitelist
cat > .aoa/whitelist.txt << 'EOF'
github.com
gitlab.com
bitbucket.org
EOF

# README explaining what's stored
cat > .aoa/README.md << 'EOF'
# .aOa Directory

This directory contains aOa's configuration and persistent data.

## Files

| File | Purpose |
|------|---------|
| `config.json` | Main configuration |
| `whitelist.txt` | Allowed URLs (one per line) |
| `session.db` | SQLite session data (created on first run) |
| `index.db` | SQLite index cache (created on first run) |

## Configuration

Edit `config.json` to change settings:
- `gateway_port`: Port for aOa gateway (default: 8080)
- `max_repo_size_mb`: Max size for cloned repos (default: 500)
- `clone_timeout`: Timeout for git operations (default: 300s)
- `confidence_threshold`: Prefetch confidence threshold (default: 0.60)
- `learning_phase_minimum`: Tool calls before prefetch starts (default: 50)

## Whitelist

Edit `whitelist.txt` to add allowed URLs:
```
github.com
gitlab.com
bitbucket.org
git.company.com         # Your private git server
docs.internal.org       # Your internal docs
```

Only HTTPS URLs to these hosts will be allowed.

## Data Storage

- `session.db`: Intent history, session state (SQLite)
- `index.db`: Cached index data (SQLite)
- Redis: Hot-path data (in Docker volume, not here)

## Resetting

To reset all data:
```bash
rm -rf .aoa/session.db .aoa/index.db
docker compose down -v  # Also clears Redis
./install.sh            # Rebuild
```
EOF

echo -e "  ${GREEN}✓${NC} Created .aoa/ directory"
echo -e "  ${GREEN}✓${NC} config.json"
echo -e "  ${GREEN}✓${NC} whitelist.txt"
echo -e "  ${GREEN}✓${NC} README.md"
echo

# =============================================================================
# 3. Build and Start Services
# =============================================================================

# Use current directory as codebase root (override with CODEBASE_PATH env var)
export CODEBASE_PATH="${CODEBASE_PATH:-.}"

echo "Codebase path: ${CODEBASE_PATH} ($(cd "${CODEBASE_PATH}" && pwd))"
echo

echo "Building Docker services..."
docker compose build --quiet

echo "Starting services..."
docker compose up -d

echo
echo "Waiting for services to be healthy..."
sleep 5

# =============================================================================
# 4. Install CLI
# =============================================================================

echo "Installing aoa CLI..."

# Copy CLI to /usr/local/bin or ~/bin
if [ -w /usr/local/bin ]; then
    cp cli/aoa /usr/local/bin/aoa
    chmod +x /usr/local/bin/aoa
    echo -e "  ${GREEN}✓${NC} Installed to /usr/local/bin/aoa"
else
    mkdir -p ~/bin
    cp cli/aoa ~/bin/aoa
    chmod +x ~/bin/aoa
    echo -e "  ${YELLOW}!${NC} Installed to ~/bin/aoa"
    echo -e "  ${YELLOW}!${NC} Add ~/bin to your PATH if needed"
fi

echo

# =============================================================================
# 5. Verify Installation
# =============================================================================

echo "Verifying installation..."
./scripts/verify-isolation.sh

echo
echo -e "${GREEN}${BOLD}⚡ aOa Installation Complete!${NC}"
echo
echo "Indexed: $(cd "${CODEBASE_PATH}" && pwd)"
echo
echo "Try it:"
echo "  aoa search <term>          Search your code"
echo "  aoa health                 Check services"
echo "  curl localhost:8080/network  View network topology"
echo
echo "To index a different directory:"
echo "  CODEBASE_PATH=/other/path docker compose up -d"
echo
echo "Config: .aoa/config.json | Whitelist: .aoa/whitelist.txt"
echo
