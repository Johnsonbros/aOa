#!/bin/bash
# =============================================================================
# aOa - Angle O(1)f Attack
# Global Installation Script
# =============================================================================
#
# 5 angles. 1 attack.
#
# This script installs aOa GLOBALLY to ~/.aoa/
# Then use 'aoa init' in any project to enable it.
#
# Install once, use everywhere.
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

# Get script directory (where aOa repo is cloned)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Global install location
AOA_HOME="$HOME/.aoa"

# =============================================================================
# Mode Selection (can be set via flags)
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
    echo "  ║     ⚡ aOa Global Uninstaller                                 ║"
    echo "  ║                                                               ║"
    echo "  ╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo

    echo -e "${YELLOW}${BOLD}The following will be removed:${NC}"
    echo

    FOUND_ITEMS=0

    # 1. Docker containers (check both unified and compose)
    AOA_UNIFIED=0
    AOA_COMPOSE=0
    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^aoa$"; then
        AOA_UNIFIED=1
        echo -e "  ${DIM}•${NC} Docker container: ${BOLD}aoa${NC} (unified)"
        FOUND_ITEMS=$((FOUND_ITEMS + 1))
    fi
    if [ -f "$AOA_HOME/docker-compose.yml" ]; then
        AOA_COMPOSE_COUNT=$(cd "$AOA_HOME" && docker compose ps -q 2>/dev/null | wc -l)
        if [ "$AOA_COMPOSE_COUNT" -gt 0 ]; then
            AOA_COMPOSE=1
            echo -e "  ${DIM}•${NC} Docker services: ${BOLD}${AOA_COMPOSE_COUNT} running${NC} (compose)"
            FOUND_ITEMS=$((FOUND_ITEMS + 1))
        fi
    fi

    # 2. Docker images (both unified 'aoa' and compose 'aoa-*')
    AOA_IMAGES=$(docker images --format '{{.Repository}}' 2>/dev/null | grep -cE "^aoa([-_]|$)" || true)
    if [ "$AOA_IMAGES" -gt 0 ]; then
        echo -e "  ${DIM}•${NC} Docker images: ${BOLD}${AOA_IMAGES} images${NC}"
        FOUND_ITEMS=$((FOUND_ITEMS + 1))
    fi

    # 3. Global install directory
    if [ -d "$AOA_HOME" ]; then
        SIZE=$(du -sh "$AOA_HOME" 2>/dev/null | cut -f1)
        echo -e "  ${DIM}•${NC} Global install: ${BOLD}$AOA_HOME${NC} ${DIM}(${SIZE})${NC}"
        FOUND_ITEMS=$((FOUND_ITEMS + 1))
    fi

    # 4. CLI in PATH
    if [ -f "$HOME/bin/aoa" ]; then
        echo -e "  ${DIM}•${NC} CLI: ${BOLD}~/bin/aoa${NC}"
        FOUND_ITEMS=$((FOUND_ITEMS + 1))
    fi

    # 5. Check for registered projects (will clean them up)
    PROJECTS_TO_CLEAN=()
    if [ -f "$AOA_HOME/projects.json" ]; then
        PROJECT_COUNT=$(jq 'length' "$AOA_HOME/projects.json" 2>/dev/null || echo 0)
        if [ "$PROJECT_COUNT" -gt 0 ]; then
            echo -e "  ${DIM}•${NC} Registered projects: ${BOLD}${PROJECT_COUNT}${NC} ${DIM}(will clean aOa files)${NC}"
            # Store project paths for cleanup
            while IFS= read -r path; do
                PROJECTS_TO_CLEAN+=("$path")
            done < <(jq -r '.[].path' "$AOA_HOME/projects.json" 2>/dev/null)
            FOUND_ITEMS=$((FOUND_ITEMS + 1))
        fi
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
        cd "$AOA_HOME" && docker compose down --volumes --remove-orphans > /dev/null 2>&1 || true
        echo -e "${GREEN}✓${NC}"
    fi

    # 2. Remove Docker images (both unified 'aoa' and compose 'aoa-*')
    if docker images --format '{{.Repository}}' 2>/dev/null | grep -qE "^aoa([-_]|$)"; then
        echo -n "  Removing images............... "
        docker images --format '{{.Repository}}:{{.Tag}}' | grep -E "^aoa([-_]|$)" | xargs -r docker rmi > /dev/null 2>&1 || true
        echo -e "${GREEN}✓${NC}"
    fi

    # 3. Clean up registered projects (BEFORE removing ~/.aoa/)
    if [ ${#PROJECTS_TO_CLEAN[@]} -gt 0 ]; then
        echo -e "  Cleaning projects:"
        for proj_path in "${PROJECTS_TO_CLEAN[@]}"; do
            if [ -d "$proj_path" ]; then
                proj_name=$(basename "$proj_path")
                echo -n "    ${proj_name}... "

                # Remove aOa hooks (aoa-* prefix)
                rm -f "$proj_path/.claude/hooks/aoa-"* 2>/dev/null

                # Remove aOa skills
                rm -f "$proj_path/.claude/skills/aoa.md" 2>/dev/null

                # Remove aOa agents
                rm -f "$proj_path/.claude/agents/aoa-"* 2>/dev/null

                # Check settings.local.json - only remove if unchanged from template
                if [ -f "$proj_path/.claude/settings.local.json" ] && [ -f "$AOA_HOME/settings.template.json" ]; then
                    TEMPLATE_HASH=$(md5sum "$AOA_HOME/settings.template.json" 2>/dev/null | cut -d' ' -f1)
                    SETTINGS_HASH=$(md5sum "$proj_path/.claude/settings.local.json" 2>/dev/null | cut -d' ' -f1)

                    if [ "$TEMPLATE_HASH" = "$SETTINGS_HASH" ]; then
                        rm -f "$proj_path/.claude/settings.local.json"
                        echo -e "${GREEN}✓${NC}"
                    else
                        echo -e "${GREEN}✓${NC} ${YELLOW}(settings.local.json has customizations - preserved)${NC}"
                    fi
                else
                    echo -e "${GREEN}✓${NC}"
                fi

                # Clean up empty .claude subdirs
                rmdir "$proj_path/.claude/hooks" 2>/dev/null || true
                rmdir "$proj_path/.claude/skills" 2>/dev/null || true
                rmdir "$proj_path/.claude/agents" 2>/dev/null || true
                rmdir "$proj_path/.claude" 2>/dev/null || true
            fi
        done
    fi

    # 4. Remove global install
    if [ -d "$AOA_HOME" ]; then
        echo -n "  Removing ~/.aoa/.............. "
        rm -rf "$AOA_HOME"
        echo -e "${GREEN}✓${NC}"
    fi

    # 5. Remove CLI
    if [ -f "$HOME/bin/aoa" ]; then
        echo -n "  Removing ~/bin/aoa............ "
        rm -f "$HOME/bin/aoa"
        echo -e "${GREEN}✓${NC}"
    fi

    echo
    echo -e "  ${GREEN}${BOLD}✓ aOa uninstalled${NC}"
    echo

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
echo -e "  ${BOLD}Global Installation${NC}"
echo -e "  ${DIM}Install once to ~/.aoa/, then 'aoa init' in any project.${NC}"
echo
echo -e "  ${DIM}This installer will:${NC}"
echo -e "  ${DIM}  1. Check prerequisites (Docker)${NC}"
echo -e "  ${DIM}  2. Create ~/.aoa/ with services${NC}"
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

# Check Python3
echo -n "  Python 3...................... "
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${YELLOW}! Not found (hooks may not work)${NC}"
fi

# Check jq
echo -n "  jq............................ "
if command -v jq &> /dev/null; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${YELLOW}! Not found (CLI features limited)${NC}"
fi

echo
echo -e "  ${GREEN}Prerequisites satisfied.${NC}"
echo
sleep 1
echo -n -e "  ${DIM}Press Enter to continue...${NC}"
read -r
echo

# =============================================================================
# Step 2: Create Global Directory
# =============================================================================

echo -e "${CYAN}${BOLD}[2/5] Setting Up Global Installation${NC}"
echo -e "${DIM}─────────────────────────────────────────────────────────────────${NC}"
echo
echo -e "  ${DIM}Installing to: ${AOA_HOME}${NC}"
echo

# Create directory structure
mkdir -p "$AOA_HOME"/{indexes,repos,bin,services,hooks}

# Copy service files
echo -n "  Copying services.............. "
cp -r "$SCRIPT_DIR/services/"* "$AOA_HOME/services/" 2>/dev/null || true
echo -e "${GREEN}✓${NC}"

# Copy Dockerfile
echo -n "  Copying Dockerfile............ "
cp "$SCRIPT_DIR/Dockerfile" "$AOA_HOME/"
echo -e "${GREEN}✓${NC}"

# Copy hook templates (for aoa init)
echo -n "  Copying hook templates........ "
cp "$SCRIPT_DIR/plugin/hooks/"*.py "$AOA_HOME/hooks/" 2>/dev/null || true
cp "$SCRIPT_DIR/plugin/hooks/"*.sh "$AOA_HOME/hooks/" 2>/dev/null || true
echo -e "${GREEN}✓${NC}"

# Copy skills template
echo -n "  Copying skill templates....... "
mkdir -p "$AOA_HOME/skills"
cp "$SCRIPT_DIR/plugin/skills/"*.md "$AOA_HOME/skills/" 2>/dev/null || true
echo -e "${GREEN}✓${NC}"

# Copy agent templates
echo -n "  Copying agent templates....... "
mkdir -p "$AOA_HOME/agents"
cp "$SCRIPT_DIR/plugin/agents/"*.md "$AOA_HOME/agents/" 2>/dev/null || true
echo -e "${GREEN}✓${NC}"

# Create empty projects.json
echo -n "  Initializing projects......... "
echo "[]" > "$AOA_HOME/projects.json"
echo -e "${GREEN}✓${NC}"

# Create settings template (for aoa init)
echo -n "  Creating settings template.... "
cat > "$AOA_HOME/settings.template.json" << 'EOFCONFIG'
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

echo
echo -e "  ${GREEN}Global directory ready.${NC}"
echo
sleep 1

# =============================================================================
# Step 3: Build Docker Image
# =============================================================================

echo -e "${CYAN}${BOLD}[3/5] Building aOa Services${NC}"
echo -e "${DIM}─────────────────────────────────────────────────────────────────${NC}"
echo

cd "$AOA_HOME"

# Copy the remaining files needed for build
cp -r "$SCRIPT_DIR/cli" "$AOA_HOME/" 2>/dev/null || true

if [ "$USE_COMPOSE" -eq 1 ]; then
    echo -e "  ${DIM}Building Docker images (compose mode)...${NC}"
    echo -e "  ${DIM}This may take a minute on first run.${NC}"
    echo
    # Copy docker-compose.yml to global location
    cp "$SCRIPT_DIR/docker-compose.yml" "$AOA_HOME/"
    cd "$AOA_HOME"
    docker compose build --quiet
else
    echo -e "  ${DIM}Building unified Docker image...${NC}"
    echo -e "  ${DIM}This may take a minute on first run.${NC}"
    echo
    docker build -t aoa "$AOA_HOME" --quiet
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

# Clean up ANY existing aOa containers (both modes) to prevent conflicts
docker compose -f "$AOA_HOME/docker-compose.yml" down 2>/dev/null || true
docker stop aoa 2>/dev/null || true
docker rm aoa 2>/dev/null || true

if [ "$USE_COMPOSE" -eq 1 ]; then
    # Start all services via docker-compose
    cd "$AOA_HOME"
    export CODEBASE_PATH="$HOME"
    export USER_HOME="$HOME"
    docker compose up -d
else
    # Start unified single container
    # Mount user's home directory so indexer can access all projects
    docker run -d \
        --name aoa \
        -p 8080:8080 \
        -v "${HOME}:/userhome:ro" \
        -v "${AOA_HOME}/repos:/repos:rw" \
        -v "${AOA_HOME}/indexes:/indexes:rw" \
        -v "${AOA_HOME}:/config:rw" \
        -v "${HOME}/.claude:/claude-sessions:ro" \
        -e "USER_HOME=${HOME}" \
        --restart unless-stopped \
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

# Copy CLI to ~/.aoa/bin
cp "$SCRIPT_DIR/cli/aoa" "$AOA_HOME/bin/aoa"
chmod +x "$AOA_HOME/bin/aoa"

# Symlink or copy to ~/bin
mkdir -p "$HOME/bin"
ln -sf "$AOA_HOME/bin/aoa" "$HOME/bin/aoa"
echo -e "  ${GREEN}✓ Installed to ~/bin/aoa${NC}"

# Check if ~/bin is in PATH
PATH_UPDATED=0
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
        if ! grep -q 'export PATH="\$HOME/bin:\$PATH"' "$SHELL_CONFIG" 2>/dev/null; then
            echo "" >> "$SHELL_CONFIG"
            echo "# Added by aOa installer" >> "$SHELL_CONFIG"
            echo 'export PATH="$HOME/bin:$PATH"' >> "$SHELL_CONFIG"
            echo -e "  ${GREEN}✓ Added ~/bin to PATH in ${SHELL_CONFIG##*/}${NC}"
            PATH_UPDATED=1
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
echo "  ║     ⚡ aOa Installed Globally!                                ║"
echo "  ║                                                               ║"
echo "  ╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo

echo -e "${GREEN}${BOLD}What was installed:${NC}"
echo -e "  ${DIM}•${NC} ~/.aoa/               ${DIM}- Global installation directory${NC}"
if [ "$USE_COMPOSE" -eq 1 ]; then
    echo -e "  ${DIM}•${NC} Docker Compose        ${DIM}- 5 containers on port 8080${NC}"
else
    echo -e "  ${DIM}•${NC} Docker container      ${DIM}- Unified container on port 8080${NC}"
fi
echo -e "  ${DIM}•${NC} aoa CLI               ${DIM}- Command line interface${NC}"
echo

echo -e "${YELLOW}${BOLD}Next steps:${NC}"
if [ "$PATH_UPDATED" -eq 1 ]; then
    echo -e "  ${BOLD}1. Restart your terminal${NC} ${DIM}(or run: source ~/${SHELL_CONFIG##*/})${NC}"
    echo
fi
echo -e "  ${BOLD}Enable aOa in any project:${NC}"
echo -e "  ${DIM}\$${NC} cd ~/your-project"
echo -e "  ${DIM}\$${NC} aoa init"
echo

echo -e "${CYAN}${BOLD}Quick test:${NC}"
echo -e "  ${DIM}\$${NC} aoa health         ${DIM}# Check services${NC}"
echo -e "  ${DIM}\$${NC} aoa projects       ${DIM}# List enabled projects${NC}"
echo

echo -e "${DIM}Global install: ${AOA_HOME}${NC}"
echo
