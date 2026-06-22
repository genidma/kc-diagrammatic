"""
Layer 2: Segmentation + SVG Spec
================================
Reads raw transcript JSON, calls Gemini (via OpenRouter) to identify key conceptual segments,
chooses an SVG template for each segment, and writes segments.json.

Usage:
    python src/segments.py
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Force UTF-8 output on Windows (avoids cp1252 crash on emoji/unicode)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load environment variables
ROOT = Path(__file__).parent.parent
load_dotenv(dotenv_path=ROOT / ".env")

# ── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = ROOT / "data"
INPUT_PATH = DATA_DIR / "raw_transcript.json"
OUTPUT_PATH = DATA_DIR / "segments.json"


# ── Time Formatting Helper ───────────────────────────────────────────────────
def format_timestamp(seconds: float) -> str:
    """Convert float seconds to M:SS or H:MM:SS format."""
    total_secs = int(seconds)
    hours = total_secs // 3600
    mins = (total_secs % 3600) // 60
    secs = total_secs % 60
    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


# ── Segments Extraction ──────────────────────────────────────────────────────
def run_segmentation(input_path: Path = INPUT_PATH, output_path: Path = OUTPUT_PATH) -> Path:
    print(f"\n🧠  [Layer 2] Segmentation & SVG Spec Generation")

    # Step 1: Load raw transcript
    if not input_path.exists():
        print(f"❌  Input file not found: {input_path}")
        print("    Please run Layer 1 (src/transcript.py) first.")
        sys.exit(1)

    print(f"    Loading transcript from {input_path.relative_to(ROOT)}...")
    with open(input_path, "r", encoding="utf-8") as f:
        raw_transcript = json.load(f)

    # Step 2: Format transcript for the LLM
    # We include timestamps so the LLM can identify the exact time ranges.
    formatted_lines = []
    for s in raw_transcript:
        start_str = format_timestamp(s["start"])
        formatted_lines.append(f"[{start_str}] {s['text']}")
    full_transcript_text = "\n".join(formatted_lines)

    # Step 3: Call OpenRouter API
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌  OPENROUTER_API_KEY is not set in the environment or .env file.")
        print("    Please add it to .env: OPENROUTER_API_KEY=your_key")
        sys.exit(1)

    model = os.getenv("LLM_MODEL", "google/gemini-2.5-flash-lite")
    print(f"    Calling OpenRouter model: {model}...")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    system_prompt = """You are a podcast visualization assistant. Your task is to segment a podcast transcript into logical, conceptual, and chronological sections (segments).
For each segment, you will also specify a corresponding diagram template and the raw data required to render it as a visual companion.

You MUST choose one of the following 8 SVG templates for each segment:
1. `chart` — Use for line/bar charts, metrics, trends, or performance comparisons over time/context.
   svgData schema:
   {
     "title": "Title of the chart",
     "points": [[x1, y1], [x2, y2], ...],  // Coordinates on a 180x96 canvas. x ranges from 18 to 175, y ranges from 8 to 85.
     "annotation": "Brief annotation label (optional)",
     "xLabel": "X axis label (e.g. 'Context window')",
     "yLabel": "Y axis label (e.g. 'Accuracy')"
   }

2. `tree` — Use for hierarchies, folder structures, or anatomical breakdowns.
   svgData schema:
   {
     "root": "Root node name (e.g., 'skill-name/ (folder)')",
     "children": ["child1", "child2", "child3", "child4"], // Exactly 4 children/subfolders
     "sublabels": ["label1", "label2", "label3", "label4"], // Sub-labels corresponding to the children
     "note": "A footer note/caption under the tree diagram"
   }

3. `comparison` — Use for side-by-side A vs B comparisons, two paths, or contrasting setups.
   svgData schema:
   {
     "left": {
       "title": "Left column title",
       "icon": "Single emoji (e.g., 📄 or ❌)",
       "lines": ["Line 1 description", "Line 2 description"],
       "footer": "Left footer text"
     },
     "right": {
       "title": "Right column title",
       "icon": "Single emoji",
       "lines": ["Line 1", "Line 2"],
       "footer": "Right footer text"
     }
   }

4. `venn` — Use for overlapping concepts or intersecting areas.
   svgData schema:
   {
     "left": { "title": "Left circle title", "label": "Left circle subtitle" },
     "right": { "title": "Right circle title", "label": "Right circle subtitle" },
     "top": { "title": "Top circle title", "label": "Top circle subtitle" },
     "center": ["Intersection label line 1", "Intersection label line 2"]
   }

5. `funnel` — Use for filtering, progressive disclosure, RAG, or narrowing choices.
   svgData schema:
   {
     "stages": ["Top Stage Label", "Middle Stage Label", "Bottom Stage Label"] // Exactly 3 stages from top to bottom
   }

6. `flow` — Use for sequential step chains, pipelines, or Directed Acyclic Graphs (DAGs).
   svgData schema:
   {
     "steps": ["Step 1 Label", "Step 2 Label", "Step 3 Label"], // Exactly 3 sequential steps
     "sublabels": ["Sublabel 1", "Sublabel 2", "Sublabel 3"] // Corresponds to the steps (optional/descriptive)
   }

7. `ladder` — Use for tiered progressions, maturity levels, or gradual graduation.
   svgData schema:
   {
     "tiers": [
       { "name": "Top Tier Name", "color": "#437a22", "desc": "Top tier description" },
       { "name": "Middle Tier Name", "color": "#d19900", "desc": "Middle tier description" },
       { "name": "Bottom Tier Name", "color": "#4f98a3", "desc": "Bottom tier description" }
     ] // Exactly 3 tiers from top to bottom
   }

8. `cycle` — Use for circular feedback loops, loops, or continuous iterations.
   svgData schema:
   {
     "center": "Single emoji (e.g. 🤖 or 🔄)",
     "steps": ["Step 1", "Step 2", "Step 3", "Step 4"] // Exactly 4 circular steps
   }

Output requirements:
- Split the transcript into 10–16 logical segments.
- Each segment must have:
  - `id`: integer starting from 0.
  - `title`: clean, punchy title.
  - `timeStart`: integer seconds where the segment starts in the podcast.
  - `timeEnd`: integer seconds where the segment ends.
  - `timeLabel`: string representation (e.g. "0:00 – 1:45" or "1:46 – 3:14").
  - `description`: A 2-3 sentence summary of the segment's core lesson or discussion.
  - `quote`: A compelling highlight quote from this segment's transcript.
  - `accentColor`: Hex color string representing the visual theme for this card (e.g., `#4f98a3`, `#6daa45`, `#da7101`, `#7a39bb`, `#a13544`, `#006494`).
  - `svgTemplate`: One of the 8 strings specified above.
  - `svgData`: Dict matching the selected template schema.

Return your response ONLY as a valid JSON array of objects. Do not include markdown code block formatting (like ```json ... ```). Begin with `[` and end with `]`.
"""

    prompt = f"Here is the podcast transcript to segment and visualize:\n\n{full_transcript_text}"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )

        raw_response = response.choices[0].message.content.strip()

        # Clean markdown code blocks if the model ignored instructions
        if raw_response.startswith("```"):
            lines = raw_response.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                raw_response = "\n".join(lines[1:-1]).strip()

        # Parse JSON
        segments = json.loads(raw_response)

        # Validate structure
        if not isinstance(segments, list):
            raise ValueError("LLM output is not a JSON list")

        # Save to disk
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)

        print(f"    ✅  Successfully extracted {len(segments)} segments.")
        print(f"    💾  Saved → {output_path.relative_to(ROOT)}")
        return output_path

    except Exception as e:
        print(f"\n❌  Failed to complete Layer 2 segment extraction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_segmentation()
