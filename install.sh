#!/bin/bash
# =============================================================================
# aOa - Angle O(1)f Attack
# Installation Script
# =============================================================================
#
# 5 angles. 1 attack.
#
# This script will:
#   1. Check prerequisites (Docker)
#   2. Create .claude/ hooks for Claude Code integration
#   3. Build and start aOa services
#   4. Install the aoa CLI
#   5. Verify everything works
#
# =============================================================================

set -e

# Colors - aOa brand
CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# Get script directory (where aOa repo is)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# =============================================================================
# Header
# =============================================================================

clear
echo -e "${CYAN}${BOLD}"
echo "  ╔═══════════════════════════════════════════════════════════════╗"
echo "  ║                                                               ║"
echo "  ║     ⚡ aOa - Angle O(1)f Attack                               ║"
echo "  ║                                                               ║"
echo "  ║     5 angles. 1 attack.                                       ║"
echo "  ║     Cut Claude Code costs by 2/3.                             ║"
echo "  ║                                                               ║"
echo "  ╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo

# =============================================================================
# Step 1: Prerequisites
# =============================================================================

echo -e "${CYAN}${BOLD}[1/5] Checking Prerequisites${NC}"
echo -e "${DIM}─────────────────────────────────────────────────────────────────${NC}"
echo

# Check Docker
echo -n "  Docker........................ "
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    echo
    echo -e "  ${YELLOW}Docker is required to run aOa services.${NC}"
    echo "  Install from: https://docs.docker.com/get-docker/"
    echo
    exit 1
fi

# Check Docker Compose
echo -n "  Docker Compose................ "
if docker compose version &> /dev/null; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    echo
    echo -e "  ${YELLOW}Docker Compose is required.${NC}"
    echo "  Usually included with Docker Desktop."
    echo
    exit 1
fi

# Check Python3
echo -n "  Python 3...................... "
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${YELLOW}! Not found (hooks may not work)${NC}"
fi

echo
echo -e "  ${GREEN}Prerequisites satisfied.${NC}"
echo

# =============================================================================
# Step 2: Claude Code Integration
# =============================================================================

echo -e "${CYAN}${BOLD}[2/5] Setting Up Claude Code Integration${NC}"
echo -e "${DIM}─────────────────────────────────────────────────────────────────${NC}"
echo
echo -e "  ${DIM}This creates the .claude/ folder with hooks that predict${NC}"
echo -e "  ${DIM}what files you need before you ask for them.${NC}"
echo

# Create .claude directory
if [ -d ".claude" ]; then
    echo -e "  ${YELLOW}! .claude/ already exists${NC}"
    echo -n "  Overwrite hooks? [y/N] "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "  ${DIM}Skipping hook installation${NC}"
        SKIP_HOOKS=true
    fi
fi

if [ -z "$SKIP_HOOKS" ]; then
    mkdir -p .claude/hooks
    mkdir -p .claude/skills

    # Copy hooks from plugin directory
    echo -n "  Copying hooks................. "
    cp "$SCRIPT_DIR/plugin/hooks/"*.py .claude/hooks/ 2>/dev/null || true
    cp "$SCRIPT_DIR/plugin/hooks/"*.sh .claude/hooks/ 2>/dev/null || true
    chmod +x .claude/hooks/*.py .claude/hooks/*.sh 2>/dev/null || true
    echo -e "${GREEN}✓${NC}"

    # Copy skills
    echo -n "  Copying skills................ "
    cp "$SCRIPT_DIR/plugin/skills/"*.md .claude/skills/ 2>/dev/null || true
    echo -e "${GREEN}✓${NC}"

    # Create settings.local.json
    echo -n "  Creating settings............. "
    cat > .claude/settings.local.json << 'EOFCONFIG'
{
  "permissions": {
    "allow": [
      "Bash(aoa search:*)",
      "Bash(aoa health:*)",
      "Bash(aoa help:*)",
      "Bash(aoa metrics:*)",
      "Bash(aoa intent:*)",
      "Bash(aoa services:*)",
      "Bash(aoa changes:*)",
      "Bash(aoa why:*)",
      "Bash(docker-compose:*)",
      "Bash(docker ps:*)",
      "Bash(docker logs:*)",
      "Bash(curl:*)",
      "Bash(ls:*)"
    ]
  },
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/aoa-intent-summary.py\"",
            "timeout": 2
          },
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/aoa-predict-context.py\"",
            "timeout": 3
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Read|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/aoa-intent-prefetch.py\"",
            "timeout": 2
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Read|Edit|Write|Bash|Grep|Glob",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/aoa-intent-capture.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  },
  "statusLine": {
    "type": "command",
    "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/aoa-status-line.sh\""
  }
}
EOFCONFIG
    echo -e "${GREEN}✓${NC}"
fi

echo
echo -e "  ${GREEN}Claude Code integration ready.${NC}"
echo -e "  ${DIM}Files created in .claude/ - feel free to inspect them.${NC}"
echo

# =============================================================================
# Step 3: Build Docker Image
# =============================================================================

echo -e "${CYAN}${BOLD}[3/5] Building aOa Services${NC}"
echo -e "${DIM}─────────────────────────────────────────────────────────────────${NC}"
echo
echo -e "  ${DIM}Building unified Docker image with all services...${NC}"
echo

docker build -t aoa "$SCRIPT_DIR" --quiet
echo
echo -e "  ${GREEN}✓ Docker image built${NC}"
echo

# =============================================================================
# Step 4: Start Services
# =============================================================================

echo -e "${CYAN}${BOLD}[4/5] Starting aOa Services${NC}"
echo -e "${DIM}─────────────────────────────────────────────────────────────────${NC}"
echo

# Stop existing container if running
docker stop aoa 2>/dev/null || true
docker rm aoa 2>/dev/null || true

# Start new container
CODEBASE_PATH="${CODEBASE_PATH:-$(pwd)}"
echo -e "  ${DIM}Indexing: ${CODEBASE_PATH}${NC}"
echo

docker run -d \
    --name aoa \
    -p 8080:8080 \
    -v "${CODEBASE_PATH}:/codebase:ro" \
    aoa > /dev/null

echo -n "  Starting services"
for i in {1..5}; do
    echo -n "."
    sleep 1
done
echo

# Verify services are running
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Services running on port 8080${NC}"
else
    echo -e "  ${YELLOW}! Services starting... (may take a moment)${NC}"
fi
echo

# =============================================================================
# Step 5: Install CLI
# =============================================================================

echo -e "${CYAN}${BOLD}[5/5] Installing aOa CLI${NC}"
echo -e "${DIM}─────────────────────────────────────────────────────────────────${NC}"
echo

# Install CLI
if [ -w /usr/local/bin ]; then
    cp "$SCRIPT_DIR/cli/aoa" /usr/local/bin/aoa
    chmod +x /usr/local/bin/aoa
    echo -e "  ${GREEN}✓ Installed to /usr/local/bin/aoa${NC}"
else
    mkdir -p ~/bin
    cp "$SCRIPT_DIR/cli/aoa" ~/bin/aoa
    chmod +x ~/bin/aoa
    echo -e "  ${GREEN}✓ Installed to ~/bin/aoa${NC}"

    # Check if ~/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
        echo -e "  ${YELLOW}! Add ~/bin to your PATH:${NC}"
        echo -e "  ${DIM}  export PATH=\"\$HOME/bin:\$PATH\"${NC}"
    fi
fi
echo

# =============================================================================
# Complete
# =============================================================================

echo -e "${CYAN}${BOLD}"
echo "  ╔═══════════════════════════════════════════════════════════════╗"
echo "  ║                                                               ║"
echo "  ║     ⚡ aOa Attack Ready!                                      ║"
echo "  ║                                                               ║"
echo "  ╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo

echo -e "${GREEN}${BOLD}What was installed:${NC}"
echo -e "  ${DIM}•${NC} .claude/hooks/     ${DIM}- Prediction hooks for Claude Code${NC}"
echo -e "  ${DIM}•${NC} .claude/skills/    ${DIM}- aOa command reference${NC}"
echo -e "  ${DIM}•${NC} Docker container   ${DIM}- Backend services on port 8080${NC}"
echo -e "  ${DIM}•${NC} aoa CLI            ${DIM}- Command line interface${NC}"
echo

echo -e "${YELLOW}${BOLD}Next step:${NC}"
echo -e "  ${BOLD}Restart Claude Code${NC} to activate the hooks."
echo

echo -e "${CYAN}${BOLD}Try it:${NC}"
echo -e "  ${DIM}\$${NC} aoa health         ${DIM}# Check services${NC}"
echo -e "  ${DIM}\$${NC} aoa search auth    ${DIM}# Search your codebase${NC}"
echo -e "  ${DIM}\$${NC} aoa help           ${DIM}# See all commands${NC}"
echo

echo -e "${DIM}Indexed: ${CODEBASE_PATH}${NC}"
echo -e "${DIM}Config:  .claude/settings.local.json${NC}"
echo
