#!/bin/bash
# =============================================================================
# aOa Imagery Generator - Gemini API
# Requires: GEMINI_API_KEY environment variable
# =============================================================================

OUTPUT_DIR="$(dirname "$0")/generated"
mkdir -p "$OUTPUT_DIR"

if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: GEMINI_API_KEY not set"
    echo "Get one at: https://aistudio.google.com/app/apikey"
    exit 1
fi

# Run the Python generator
python3 "$(dirname "$0")/generate-imagery.py" "$@"
