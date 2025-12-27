#!/usr/bin/env python3
"""
aOa Imagery Generator - Gemini API
Theme: "Angle of Attack" - Sharp, fast, precise

Usage:
    python generate-imagery.py              # Generate all images
    python generate-imagery.py hero         # Generate specific image
    python generate-imagery.py --list       # List available images

Requires: pip install google-genai pillow

API Key: Set GEMINI_API_KEY in environment or in .env file
"""

import os
import sys
from pathlib import Path

# Load .env file if it exists
def load_env():
    env_paths = [
        Path(__file__).parent / ".env",           # assets/.env
        Path(__file__).parent.parent / ".env",    # project root .env
    ]
    for env_path in env_paths:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key not in os.environ:  # Don't override existing env
                            os.environ[key] = value
            break

load_env()

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai not installed")
    print("Run: pip install google-genai pillow")
    sys.exit(1)

OUTPUT_DIR = Path(__file__).parent / "generated"
OUTPUT_DIR.mkdir(exist_ok=True)

# Brand constants
BRAND = """
Brand: aOa (Angle of Attack)
Colors: Electric cyan (#00D4FF), Hot orange (#FF6B35), Deep navy (#0A1628)
Style: Sharp, fast, precise. Fighter jet HUD aesthetic. No clutter.
"""

PROMPTS = {
    "hero": {
        "prompt": f"""
{BRAND}
Create: Hero banner showing the concept of O(1) constant-time performance.
Scene: A flat horizontal line (representing constant cost) versus an exponential curve rising steeply (representing traditional scaling).
The flat line glows electric cyan. The rising curve fades to red/orange.
Abstract, minimal, data visualization style.
Deep navy background with subtle grid.
No text, no people, no logos.
Mood: Calm efficiency vs growing chaos.
""",
        "aspect": "16:9",
        "filename": "hero.png"
    },

    "bigo": {
        "prompt": f"""
{BRAND}
Create: Abstract visualization of Big O notation - O(1) constant time.
Scene: Multiple paths/lines starting from one point.
Most lines curve upward exponentially (bad - O(n), O(n^2)).
ONE line stays perfectly flat and horizontal, glowing bright cyan (good - O(1)).
Deep navy background.
Style: Mathematical, clean, like a computer science textbook illustration made beautiful.
No text. No people.
Mood: One path is clearly the winner.
""",
        "aspect": "4:3",
        "filename": "bigo.png"
    },

    "angle": {
        "prompt": f"""
{BRAND}
Create: Visualization of precision targeting - finding the RIGHT answer.
Scene: Multiple faint target circles, but ONE is bright cyan with a perfect bullseye hit.
Geometric, angular composition suggesting a calculated approach angle.
Faint trajectory lines showing the path to the target.
Deep navy background.
Style: Precision engineering, targeting system aesthetic.
No text, no people.
Mood: Not just fast - accurate. The right answer, first try.
""",
        "aspect": "4:3",
        "filename": "angle.png"
    },

    "attack": {
        "prompt": f"""
{BRAND}
Create: Visualization of multiple attack vectors converging on a target.
Scene: FIVE distinct groups of lines/paths approaching a central glowing point from different angles.
Each group is a different shade (cyan spectrum), representing 5 attack groups.
The paths converge precisely on the target.
Deep navy background with subtle depth.
Style: Strategic, military planning aesthetic. Like attack vectors on a tactical display.
No text, no people.
Mood: Five attack groups. Fifteen methods. One confident result.
""",
        "aspect": "4:3",
        "filename": "attack.png"
    },

    "scaling": {
        "prompt": f"""
{BRAND}
Create: Before/after comparison of cost scaling.
Scene: Split composition.
LEFT: An exponential curve rising steeply, with stacked coins/cost symbols growing larger. Red/orange tones. Label area for "100K files".
RIGHT: A flat horizontal line with consistent small coins. Cyan/green tones. Same label area.
Sharp diagonal dividing line.
Deep navy background.
Style: Infographic, data visualization.
No text (we add later). No people.
Mood: Compounding cost vs flat cost.
""",
        "aspect": "16:9",
        "filename": "scaling.png"
    },

    "status": {
        "prompt": f"""
{BRAND}
Create: A futuristic status dashboard showing O(1) performance.
Scene: A horizontal bar with "O(1)" concept - flat line, instant response.
Five indicator light groups (representing 5 attack groups) all glowing green.
Floating metrics showing speed and accuracy.
Electric cyan and green on deep navy.
Style: Fighter jet cockpit HUD, instrument panel.
No readable text. No people.
Mood: All systems optimal. Constant time. Always.
""",
        "aspect": "3:1",
        "filename": "status.png"
    }
}


def generate_image(client, name: str, config: dict) -> bool:
    """Generate a single image using Gemini."""
    print(f"Generating {name}...")

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[config["prompt"]],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            )
        )

        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                # Save the image
                output_path = OUTPUT_DIR / config["filename"]
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"  Saved: {output_path}")
                return True

        # Check for text response (might indicate an issue)
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                print(f"  Response: {part.text[:200]}")

        print(f"  Warning: No image generated for {name}")
        return False

    except Exception as e:
        print(f"  Error: {e}")
        return False


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Get one at: https://aistudio.google.com/app/apikey")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Parse arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--list":
            print("Available images:")
            for name, config in PROMPTS.items():
                print(f"  {name:12} -> {config['filename']} ({config['aspect']})")
            return

        if arg == "--help":
            print(__doc__)
            return

        if arg in PROMPTS:
            generate_image(client, arg, PROMPTS[arg])
            return

        print(f"Unknown image: {arg}")
        print(f"Available: {', '.join(PROMPTS.keys())}")
        sys.exit(1)

    # Generate all
    print(f"Generating all {len(PROMPTS)} images...")
    print(f"Output: {OUTPUT_DIR}")
    print()

    success = 0
    for name, config in PROMPTS.items():
        if generate_image(client, name, config):
            success += 1
        print()

    print(f"Done: {success}/{len(PROMPTS)} images generated")


if __name__ == "__main__":
    main()
