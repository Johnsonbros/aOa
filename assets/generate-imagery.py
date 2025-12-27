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
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".env",
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
                        if key not in os.environ:
                            os.environ[key] = value
            break

load_env()

try:
    from google import genai
    from google.genai import types
    import PIL.Image
    from io import BytesIO
except ImportError:
    print("Error: google-genai not installed")
    print("Run: pip install google-genai pillow")
    sys.exit(1)

OUTPUT_DIR = Path(__file__).parent / "generated"
OUTPUT_DIR.mkdir(exist_ok=True)

# =============================================================================
# Visual Storytelling: 3 Images, 1 Journey
# =============================================================================
#
# 1. HERO - The Problem/Solution in one image
#    "I want to be on the flat line, not the rising curve"
#
# 2. CONVERGENCE - Multiple methods, one answer
#    "Many inputs flow into one calm, confident result"
#
# 3. STATUS - The outcome achieved
#    "Everything is working. I can relax."
# =============================================================================

STYLE = """
Overall Style & Mood:
- Theme: Futuristic, high-tech, data-driven, speed, and intelligence
- Aesthetic: Professional "award-winning ad campaign," clean, neon-glowing, dynamic
- Background: Deep dark navy blue (#0A1628) with subtle faint textures like digital starfield, circuit patterns, or radiating light particles for depth without clutter

Central Element:
- Focal point: Prominent, glowing circular hub at center
- Effect: Brightest element with intense electric cyan glow and radiating starburst/light-streak effect

Connecting Lines (Vectors):
- Style: Sharp, angular, dynamic - stylized "attack vectors" or energy beams cutting through space
- Color: Electric cyan with bright neon glow

Outer Nodes:
- Layout: Radial pattern around center
- Iconography: Minimalist, line-art style icons, glowing electric cyan
- Clean, organized composition

Color Palette:
- Primary (Glow): Electric Cyan (#00D4FF)
- Secondary (Background): Deep Navy Blue (#0A1628)
- Tertiary (Accents): White or Pale Cyan (#E0FFFF)

Effects:
- Neon Bloom: All cyan elements have soft neon bloom/glow effect, light-emitting
- Generous negative space, organized, not cluttered
- Professional, polished, award-winning quality

No text. No people. No logos.
"""

PROMPTS = {
    "hero": {
        "prompt": f"""
{STYLE}

Create: Central hub with 5 attack vectors radiating outward.

Scene:
- CENTER: Prominent glowing circular hub - the O(1) core. Brightest element with intense electric cyan glow and radiating starburst effect. This represents speed and intelligence.
- VECTORS: 5 sharp, angular energy beams cutting outward from center to 5 outer nodes. Stylized attack vectors, not simple lines.
- OUTER NODES: 5 minimalist line-art icons arranged radially:
  1. Search (magnifying glass icon)
  2. Intent (brain/neural icon)
  3. Knowledge (database icon)
  4. Ranking (stacked bars icon)
  5. Prediction (forward arrow icon)

Each node glows with neon bloom effect. All connected by dynamic cyan energy beams.
""",
        "aspect": "16:9",
        "filename": "hero.png"
    },

    "convergence": {
        "prompt": f"""
{STYLE}

Create: Five attack vectors converging to one answer.

Scene:
- 5 sharp angular energy beams approaching from different directions
- Each beam slightly different shade of cyan spectrum
- All converging precisely on a single bright focal point at center
- The convergence point has intense white/gold glow - the confident answer
- This is resolution, not explosion. Calm precision.
- Radiating light particles around the convergence point

The feeling: multiple attack angles, one confident result.
""",
        "aspect": "4:3",
        "filename": "convergence.png"
    },

    "status": {
        "prompt": f"""
{STYLE}

Create: Optimal status dashboard - everything working.

Scene:
- Clean horizontal composition
- One flat glowing cyan line across center (the O(1) promise kept)
- 5 small indicator nodes below, all glowing bright green (#00FF88)
- Subtle starburst/radial glow from each indicator
- Generous negative space, not cluttered
- Faint circuit pattern texture in background

This is the outcome state - all systems optimal, flat cost, confident.
HUD aesthetic, professional dashboard feel.
""",
        "aspect": "16:9",
        "filename": "status.png"
    }
}


def generate_image(client, name: str, config: dict) -> bool:
    """Generate a single image using Gemini Pro Image."""
    print(f"Generating {name}...")

    # Supported: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
    aspect = config.get("aspect", "4:3")

    try:
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=config["prompt"],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect,
                    image_size="1K"
                ),
            )
        )

        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                image = PIL.Image.open(BytesIO(part.inline_data.data))
                output_path = OUTPUT_DIR / config["filename"]
                image.save(output_path)
                print(f"  Saved: {output_path} ({image.size[0]}x{image.size[1]})")
                return True

        print(f"  Warning: No image generated for {name}")
        return False

    except Exception as e:
        print(f"  Error: {e}")
        return False


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set")
        print("Set in environment or in .env file")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--list":
            print("Available images (3 for cohesive story):")
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
    print(f"Generating {len(PROMPTS)} images for visual story...")
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
