#!/bin/bash
# =============================================================================
# aOa Hook Installer
# =============================================================================
#
# Installs aOa intent hooks into your Claude Code project.
#
# Usage:
#   ./install-hooks.sh [path] [mode]
#
# Modes:
#   both        - Status line + inline on prompt (default)
#   statusline  - Status line only (persistent, minimal)
#   inline      - Inline on prompt only
#   capture     - No display, just tracking
#
# Examples:
#   ./install-hooks.sh                     # Current dir, both modes
#   ./install-hooks.sh . statusline        # Status line only
#   ./install-hooks.sh /my/project inline  # Inline only
#
# After running, RESTART Claude Code for hooks to take effect.
#
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${1:-.}"
MODE="${2:-both}"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}⚡ aOa Hook Installer${NC}"
echo
echo "Mode: ${MODE}"
echo

# Create .claude/hooks directory
mkdir -p "${TARGET_DIR}/.claude/hooks"

# Copy hook files
cp "${SCRIPT_DIR}/intent-capture.py" "${TARGET_DIR}/.claude/hooks/"
cp "${SCRIPT_DIR}/intent-summary.py" "${TARGET_DIR}/.claude/hooks/"
cp "${SCRIPT_DIR}/intent-prefetch.py" "${TARGET_DIR}/.claude/hooks/"
cp "${SCRIPT_DIR}/aoa-status.sh" "${TARGET_DIR}/.claude/hooks/"

# Make executable
chmod +x "${TARGET_DIR}/.claude/hooks/"*.py
chmod +x "${TARGET_DIR}/.claude/hooks/"*.sh

echo -e "${GREEN}✓${NC} Copied hooks to ${TARGET_DIR}/.claude/hooks/"

# Select settings file based on mode
case "$MODE" in
    statusline|status)
        SETTINGS_FILE="settings-statusline-only.json"
        DISPLAY_MSG="Status line (persistent)"
        ;;
    inline)
        SETTINGS_FILE="settings-inline-only.json"
        DISPLAY_MSG="Inline on prompt"
        ;;
    capture|none)
        SETTINGS_FILE="settings-capture-only.json"
        DISPLAY_MSG="Capture only (no display)"
        ;;
    both|*)
        SETTINGS_FILE="settings.local.json"
        DISPLAY_MSG="Status line + inline"
        ;;
esac

# Check if settings.local.json exists
if [ -f "${TARGET_DIR}/.claude/settings.local.json" ]; then
    echo -e "${YELLOW}!${NC} settings.local.json already exists"
    echo "  Merge from: ${SCRIPT_DIR}/${SETTINGS_FILE}"
    echo
else
    cp "${SCRIPT_DIR}/${SETTINGS_FILE}" "${TARGET_DIR}/.claude/settings.local.json"
    echo -e "${GREEN}✓${NC} Created settings.local.json (${DISPLAY_MSG})"
fi

echo
echo -e "${BOLD}Display mode: ${DISPLAY_MSG}${NC}"
echo
echo -e "${BOLD}Next steps:${NC}"
echo "  1. Restart Claude Code (hooks load at session start)"
echo "  2. Start using Claude - the hooks learn automatically"
echo "  3. Check progress: aoa intent recent"
echo
echo -e "${CYAN}To change mode later:${NC}"
echo "  ./install-hooks.sh ${TARGET_DIR} [both|statusline|inline|capture]"
echo
