"""
Layer 3: HTML + SVG Render
===========================
Loads segments.json, renders each SVG diagram using Jinja2 templates,
and compiles them into a standalone companion.html page.

Usage (standalone):
    python src/render.py [youtube_url]
"""

import json
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Force UTF-8 output on Windows (avoids cp1252 crash on emoji/unicode)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
TEMPLATE_DIR = ROOT / "templates"
SVG_TEMPLATE_DIR = Path(__file__).parent / "svg_templates"
INPUT_PATH = DATA_DIR / "segments.json"
OUTPUT_DIR = ROOT / "output"
OUTPUT_PATH = OUTPUT_DIR / "companion.html"


# ── Duration Formatting Helper ────────────────────────────────────────────────
def format_duration(total_seconds: float) -> str:
    """Convert seconds to MM:SS or HH:MM:SS display string."""
    mins = int(total_seconds) // 60
    secs = int(total_seconds) % 60
    hours = mins // 60
    if hours > 0:
        mins = mins % 60
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


# ── Render Engine ────────────────────────────────────────────────────────────
def run_rendering(youtube_url: str = "https://www.youtube.com/watch?v=uYURYHhpmKc", 
                  input_path: Path = INPUT_PATH, 
                  output_path: Path = OUTPUT_PATH) -> Path:
    print(f"\n🎨  [Layer 3] HTML + SVG Rendering")

    # Step 1: Load segment data
    if not input_path.exists():
        print(f"❌  Input file not found: {input_path}")
        print("    Please run Layer 2 (src/segments.py) first.")
        sys.exit(1)

    print(f"    Loading segment data from {input_path.relative_to(ROOT)}...")
    with open(input_path, "r", encoding="utf-8") as f:
        segments = json.load(f)

    # Step 2: Initialize Jinja2 environments
    # One for SVG templates and one for the main HTML template
    svg_env = Environment(
        loader=FileSystemLoader(SVG_TEMPLATE_DIR),
        autoescape=select_autoescape(['svg', 'xml'])
    )
    html_env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )

    # Step 3: Render each segment's SVG
    print("    Rendering SVG diagrams...")
    for segment in segments:
        template_name = f"{segment['svgTemplate']}.svg.jinja"
        try:
            template = svg_env.get_template(template_name)
            
            # Prepare render context by combining SVG data and accent color
            context = {
                "accentColor": segment["accentColor"],
                **segment["svgData"]
            }
            
            # Render SVG string
            rendered_svg = template.render(context)
            segment["rendered_svg"] = rendered_svg

        except Exception as e:
            print(f"   Warning: Failed to render SVG for segment {segment['id']} ({template_name}): {e}")
            # Fallback to an empty SVG if it fails
            segment["rendered_svg"] = f'<svg viewBox="0 0 180 96" xmlns="http://www.w3.org/2000/svg" style="background:var(--surf2);border-radius:6px;"><text x="90" y="50" text-anchor="middle" font-size="8" fill="#888">Diagram: {segment["svgTemplate"]}</text></svg>'

    # Step 4: Calculate totals
    total_seconds = 0
    if segments:
        # Check if the final segment has timeEnd
        last_seg = segments[-1]
        total_seconds = last_seg.get("timeEnd", 0)
    
    total_dur_str = format_duration(total_seconds)

    # Step 5: Render final companion HTML page
    print(f"    Compiling final HTML page...")
    html_template = html_env.get_template("companion.html.jinja")
    
    # We can customize the podcast title. Usually, we can infer it or use a default.
    podcast_title = "Agent Skills Podcast" if "uYURYHhpmKc" in youtube_url else "Visual Podcast Companion"

    final_html = html_template.render(
        podcast_title=podcast_title,
        segments=segments,
        total_duration=total_dur_str,
        youtube_url=youtube_url
    )

    # Step 6: Save output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"    ✅  Successfully rendered HTML companion page.")
    print(f"    💾  Saved → {output_path.relative_to(ROOT)}")
    return output_path


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=uYURYHhpmKc"
    run_rendering(url)
