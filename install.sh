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
# Mode Selection
# =============================================================================
# Default: unified (single container, simpler)
# --compose: multi-container with docker-compose (full isolation)

USE_COMPOSE=0
if [[ "$1" == "--compose" ]]; then
    USE_COMPOSE=1
    shift
fi

# =============================================================================
# Uninstall Mode
# =============================================================================

if [[ "$1" == "--uninstall" ]]; then
    echo -e "${CYAN}${BOLD}"
    echo "  ╔═══════════════════════════════════════════════════════════════╗"
    echo "  ║                                                               ║"
    echo "  ║     ⚡ aOa Uninstaller                                        ║"
    echo "  ║                                                               ║"
    echo "  ╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo

    echo -e "${YELLOW}${BOLD}The following will be removed:${NC}"
    echo

    # Check what exists
    FOUND_ITEMS=0

    # 1. Docker containers/services (check both unified and compose)
    cd "$SCRIPT_DIR"
    AOA_UNIFIED=0
    AOA_COMPOSE=0
    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^aoa$"; then
        AOA_UNIFIED=1
        echo -e "  ${DIM}•${NC} Docker container: ${BOLD}aoa${NC} (unified)"
        FOUND_ITEMS=$((FOUND_ITEMS + 1))
    fi
    AOA_COMPOSE_COUNT=$(docker compose ps -q 2>/dev/null | wc -l)
    if [ "$AOA_COMPOSE_COUNT" -gt 0 ]; then
        AOA_COMPOSE=1
        echo -e "  ${DIM}•${NC} Docker services: ${BOLD}${AOA_COMPOSE_COUNT} running${NC} (compose)"
        FOUND_ITEMS=$((FOUND_ITEMS + 1))
    fi
    # Check for images (both unified 'aoa' and compose 'aoa-*')
    AOA_IMAGES=$(docker images --format '{{.Repository}}' 2>/dev/null | grep -cE "^aoa([-_]|$)" || true)
    if [ "$AOA_IMAGES" -gt 0 ]; then
        echo -e "  ${DIM}•${NC} Docker images: ${BOLD}${AOA_IMAGES} images${NC}"
        FOUND_ITEMS=$((FOUND_ITEMS + 1))
    fi

    # 2. aOa files in .claude (only our files, not the whole directory)
    AOA_HOOKS=$(ls .claude/hooks/aoa-* 2>/dev/null | wc -l)
    AOA_SKILL=$([ -f ".claude/skills/aoa.md" ] && echo 1 || echo 0)

    # Check settings.local.json - compare to our template
    AOA_SETTINGS=0
    AOA_SETTINGS_CLEAN=0
    if [ -f ".claude/settings.local.json" ]; then
        AOA_SETTINGS=1
        # Generate our known template hash
        EXPECTED_HASH=$(cat << 'EOFTEMPLATE' | md5sum | cut -d' ' -f1
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
EOFTEMPLATE
)
        ACTUAL_HASH=$(md5sum .claude/settings.local.json 2>/dev/null | cut -d' ' -f1)
        if [ "$EXPECTED_HASH" = "$ACTUAL_HASH" ]; then
            AOA_SETTINGS_CLEAN=1
        fi
    fi

    if [ "$AOA_HOOKS" -gt 0 ]; then
        echo -e "  ${DIM}•${NC} Hooks: ${BOLD}.claude/hooks/aoa-*${NC} ${DIM}(${AOA_HOOKS} files)${NC}"
        FOUND_ITEMS=$((FOUND_ITEMS + 1))
    fi
    if [ "$AOA_SKILL" -eq 1 ]; then
        echo -e "  ${DIM}•${NC} Skill: ${BOLD}.claude/skills/aoa.md${NC}"
        FOUND_ITEMS=$((FOUND_ITEMS + 1))
    fi
    if [ "$AOA_SETTINGS" -eq 1 ]; then
        if [ "$AOA_SETTINGS_CLEAN" -eq 1 ]; then
            echo -e "  ${DIM}•${NC} Settings: ${BOLD}.claude/settings.local.json${NC} ${DIM}(unmodified)${NC}"
        else
            echo -e "  ${DIM}•${NC} Settings: ${BOLD}.claude/settings.local.json${NC} ${YELLOW}(customized)${NC}"
        fi
        FOUND_ITEMS=$((FOUND_ITEMS + 1))
    fi

    # 3. CLI
    if [ -f "/usr/local/bin/aoa" ]; then
        echo -e "  ${DIM}•${NC} CLI: ${BOLD}/usr/local/bin/aoa${NC}"
        FOUND_ITEMS=$((FOUND_ITEMS + 1))
    fi
    if [ -f "$HOME/bin/aoa" ]; then
        echo -e "  ${DIM}•${NC} CLI: ${BOLD}~/bin/aoa${NC}"
        FOUND_ITEMS=$((FOUND_ITEMS + 1))
    fi

    echo

    if [ $FOUND_ITEMS -eq 0 ]; then
        echo -e "  ${DIM}Nothing to uninstall - aOa not found.${NC}"
        echo
        exit 0
    fi

    echo -n -e "${YELLOW}Proceed with uninstall? [y/N] ${NC}"
    read -r response
    echo

    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "  ${DIM}Uninstall cancelled.${NC}"
        echo
        exit 0
    fi

    # Perform uninstall
    echo -e "${CYAN}${BOLD}Removing aOa...${NC}"
    echo

    # 1. Stop and remove Docker containers/services (both modes)
    if [ "$AOA_UNIFIED" -eq 1 ]; then
        echo -n "  Stopping container............ "
        docker stop aoa > /dev/null 2>&1 || true
        docker rm aoa > /dev/null 2>&1 || true
        echo -e "${GREEN}✓${NC}"
    fi
    if [ "$AOA_COMPOSE" -eq 1 ]; then
        echo -n "  Stopping services............. "
        docker compose down --volumes --remove-orphans > /dev/null 2>&1 || true
        echo -e "${GREEN}✓${NC}"
    fi

    # 2. Remove Docker images (both unified 'aoa' and compose 'aoa-*')
    if docker images --format '{{.Repository}}' 2>/dev/null | grep -qE "^aoa([-_]|$)"; then
        echo -n "  Removing images............... "
        docker images --format '{{.Repository}}:{{.Tag}}' | grep -E "^aoa([-_]|$)" | xargs -r docker rmi > /dev/null 2>&1 || true
        echo -e "${GREEN}✓${NC}"
    fi

    # 3. Remove only aOa files from .claude (preserve user's other hooks)
    if [ "$AOA_HOOKS" -gt 0 ]; then
        echo -n "  Removing aOa hooks............ "
        rm -f .claude/hooks/aoa-* 2>/dev/null
        echo -e "${GREEN}✓${NC}"
    fi
    if [ "$AOA_SKILL" -eq 1 ]; then
        echo -n "  Removing aOa skill............ "
        rm -f .claude/skills/aoa.md 2>/dev/null
        echo -e "${GREEN}✓${NC}"
    fi
    if [ "$AOA_SETTINGS" -eq 1 ]; then
        if [ "$AOA_SETTINGS_CLEAN" -eq 1 ]; then
            echo -n "  Removing settings............. "
            rm -f .claude/settings.local.json 2>/dev/null
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "  ${YELLOW}! Settings customized - preserving .claude/settings.local.json${NC}"
            SETTINGS_PRESERVED=1
        fi
    fi

    # 4. Remove CLI
    if [ -f "/usr/local/bin/aoa" ]; then
        echo -n "  Removing /usr/local/bin/aoa... "
        rm -f /usr/local/bin/aoa 2>/dev/null || sudo rm -f /usr/local/bin/aoa
        echo -e "${GREEN}✓${NC}"
    fi
    if [ -f "$HOME/bin/aoa" ]; then
        echo -n "  Removing ~/bin/aoa............ "
        rm -f "$HOME/bin/aoa"
        echo -e "${GREEN}✓${NC}"
    fi

    echo
    echo -e "  ${GREEN}${BOLD}✓ aOa uninstalled successfully${NC}"
    echo

    # Guidance for customized settings
    if [ "${SETTINGS_PRESERVED:-0}" -eq 1 ]; then
        echo -e "  ${YELLOW}${BOLD}Manual cleanup needed:${NC}"
        echo -e "  ${DIM}Your .claude/settings.local.json has custom changes.${NC}"
        echo -e "  ${DIM}Remove these aOa sections if desired:${NC}"
        echo
        echo -e "  ${DIM}• permissions.allow: Bash(aoa *) entries${NC}"
        echo -e "  ${DIM}• hooks.UserPromptSubmit: aoa-intent-summary.py, aoa-predict-context.py${NC}"
        echo -e "  ${DIM}• hooks.PreToolUse: aoa-intent-prefetch.py${NC}"
        echo -e "  ${DIM}• hooks.PostToolUse: aoa-intent-capture.py${NC}"
        echo -e "  ${DIM}• statusLine: aoa-status-line.sh${NC}"
        echo
    fi

    exit 0
fi

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
echo -e "  ${DIM}This installer will:${NC}"
echo -e "  ${DIM}  1. Check prerequisites (Docker, Python)${NC}"
echo -e "  ${DIM}  2. Set up Claude Code hooks in .claude/${NC}"
echo -e "  ${DIM}  3. Build the aOa Docker image${NC}"
echo -e "  ${DIM}  4. Start aOa services${NC}"
echo -e "  ${DIM}  5. Install the aoa CLI${NC}"
echo

# Choose deployment mode (unless already set via --compose flag)
if [ "$USE_COMPOSE" -eq 0 ]; then
    echo -e "  ${CYAN}${BOLD}Choose deployment mode:${NC}"
    echo
    echo -e "  ${BOLD}[1]${NC} Single Container ${GREEN}(Recommended)${NC}"
    echo -e "      ${DIM}• One container, one port (8080)${NC}"
    echo -e "      ${DIM}• All services via supervisord${NC}"
    echo -e "      ${DIM}• Simpler, fewer resources${NC}"
    echo
    echo -e "  ${BOLD}[2]${NC} Docker Compose"
    echo -e "      ${DIM}• 5 separate containers${NC}"
    echo -e "      ${DIM}• Network isolation between services${NC}"
    echo -e "      ${DIM}• Better for debugging/development${NC}"
    echo
    echo -n -e "  ${YELLOW}Enter choice [1/2]: ${NC}"
    read -r mode_choice
    echo
    if [ "$mode_choice" = "2" ]; then
        USE_COMPOSE=1
        echo -e "  ${DIM}Using Docker Compose mode${NC}"
    else
        USE_COMPOSE=0
        echo -e "  ${DIM}Using single container mode${NC}"
    fi
    echo
fi

echo -n -e "  ${YELLOW}Press Enter to continue...${NC}"
read -r
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
sleep 1
echo -n -e "  ${DIM}Press Enter to continue...${NC}"
read -r
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

    # Create repos directory for intel repos (gitignored)
    echo -n "  Creating repos directory...... "
    mkdir -p "$SCRIPT_DIR/repos" 2>/dev/null
    if [ -w "$SCRIPT_DIR/repos" ]; then
        cat > "$SCRIPT_DIR/repos/.gitignore" << 'EOF'
# Intel repos - indexed for search, not committed
# These are cloned via aOa proxy for reference/learning
*
!.gitignore
EOF
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}! Permission issue - run: sudo chown -R \$(id -u):\$(id -g) $SCRIPT_DIR/repos${NC}"
    fi

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
sleep 1
echo -n -e "  ${DIM}Press Enter to continue...${NC}"
read -r
echo

# =============================================================================
# Step 3: Build Docker Image
# =============================================================================

echo -e "${CYAN}${BOLD}[3/5] Building aOa Services${NC}"
echo -e "${DIM}─────────────────────────────────────────────────────────────────${NC}"
echo

cd "$SCRIPT_DIR"

if [ "$USE_COMPOSE" -eq 1 ]; then
    echo -e "  ${DIM}Building Docker images (compose mode)...${NC}"
    echo -e "  ${DIM}This may take a minute on first run.${NC}"
    echo
    docker compose build --quiet
else
    echo -e "  ${DIM}Building unified Docker image...${NC}"
    echo -e "  ${DIM}This may take a minute on first run.${NC}"
    echo
    docker build -t aoa "$SCRIPT_DIR" --quiet
fi

echo
echo -e "  ${GREEN}✓ Docker image(s) built${NC}"
echo
sleep 1

# =============================================================================
# Step 4: Start Services
# =============================================================================

echo -e "${CYAN}${BOLD}[4/5] Starting aOa Services${NC}"
echo -e "${DIM}─────────────────────────────────────────────────────────────────${NC}"
echo

# Set codebase path
CODEBASE_PATH="${CODEBASE_PATH:-$(pwd)}"
echo -e "  ${DIM}Indexing: ${CODEBASE_PATH}${NC}"
echo

# Clean up ANY existing aOa containers (both modes) to prevent conflicts
docker compose down 2>/dev/null || true
docker stop aoa 2>/dev/null || true
docker rm aoa 2>/dev/null || true

# Ensure directories exist before Docker starts
mkdir -p "$SCRIPT_DIR/repos" "$SCRIPT_DIR/.aoa"

if [ "$USE_COMPOSE" -eq 1 ]; then
    # Start all services via docker-compose
    export CODEBASE_PATH
    docker compose up -d
else
    # Start unified single container
    docker run -d \
        --name aoa \
        -p 8080:8080 \
        -v "${CODEBASE_PATH}:/codebase:ro" \
        -v "${SCRIPT_DIR}/repos:/repos:rw" \
        -v "${SCRIPT_DIR}/.aoa:/config:rw" \
        -v "${HOME}/.claude:/claude-sessions:ro" \
        aoa > /dev/null
fi

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
sleep 1

# =============================================================================
# Step 5: Install CLI
# =============================================================================

echo -e "${CYAN}${BOLD}[5/5] Installing aOa CLI${NC}"
echo -e "${DIM}─────────────────────────────────────────────────────────────────${NC}"
echo

# Install CLI
PATH_UPDATED=0
if [ -w /usr/local/bin ]; then
    cp "$SCRIPT_DIR/cli/aoa" /usr/local/bin/aoa
    chmod +x /usr/local/bin/aoa
    echo -e "  ${GREEN}✓ Installed to /usr/local/bin/aoa${NC}"
else
    mkdir -p ~/bin
    cp "$SCRIPT_DIR/cli/aoa" ~/bin/aoa
    chmod +x ~/bin/aoa
    echo -e "  ${GREEN}✓ Installed to ~/bin/aoa${NC}"

    # Check if ~/bin is in PATH - if not, add it
    if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
        # Detect shell config file
        SHELL_CONFIG=""
        if [ -n "$ZSH_VERSION" ] || [ -f "$HOME/.zshrc" ]; then
            SHELL_CONFIG="$HOME/.zshrc"
        elif [ -f "$HOME/.bashrc" ]; then
            SHELL_CONFIG="$HOME/.bashrc"
        elif [ -f "$HOME/.bash_profile" ]; then
            SHELL_CONFIG="$HOME/.bash_profile"
        fi

        if [ -n "$SHELL_CONFIG" ]; then
            # Check if we already added it
            if ! grep -q 'export PATH="\$HOME/bin:\$PATH"' "$SHELL_CONFIG" 2>/dev/null; then
                echo "" >> "$SHELL_CONFIG"
                echo "# Added by aOa installer" >> "$SHELL_CONFIG"
                echo 'export PATH="$HOME/bin:$PATH"' >> "$SHELL_CONFIG"
                echo -e "  ${GREEN}✓ Added ~/bin to PATH in ${SHELL_CONFIG##*/}${NC}"
                PATH_UPDATED=1
            fi
        else
            echo -e "  ${YELLOW}! Could not detect shell config file${NC}"
            echo -e "  ${DIM}  Add this to your shell config:${NC}"
            echo -e "  ${DIM}  export PATH=\"\$HOME/bin:\$PATH\"${NC}"
        fi
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

echo -e "${YELLOW}${BOLD}Next steps:${NC}"
if [ "$PATH_UPDATED" -eq 1 ]; then
    echo -e "  ${BOLD}1. Restart your terminal${NC} ${DIM}(or run: source ~/${SHELL_CONFIG##*/})${NC}"
    echo -e "  ${BOLD}2. Restart Claude Code${NC} to activate the hooks"
else
    echo -e "  ${BOLD}Restart Claude Code${NC} to activate the hooks."
fi
echo

echo -e "${CYAN}${BOLD}Try it:${NC}"
if [ "$PATH_UPDATED" -eq 1 ]; then
    echo -e "  ${DIM}After restarting terminal:${NC}"
fi
echo -e "  ${DIM}\$${NC} aoa health         ${DIM}# Check services${NC}"
echo -e "  ${DIM}\$${NC} aoa search auth    ${DIM}# Search your codebase${NC}"
echo -e "  ${DIM}\$${NC} aoa help           ${DIM}# See all commands${NC}"
echo

echo -e "${DIM}Indexed: ${CODEBASE_PATH}${NC}"
echo -e "${DIM}Config:  .claude/settings.local.json${NC}"
echo
