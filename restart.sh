#!/bin/bash
# =============================================================================
# aOa Reset - Clean slate for testing install.sh
# =============================================================================

set -e

echo "Stopping containers..."
docker compose down -v 2>/dev/null || true

echo "Removing .aoa data..."
rm -rf .aoa

echo
echo "Ready. Run ./install.sh"
