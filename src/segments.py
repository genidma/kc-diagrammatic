"""
Layer 2: LLM Segmentation
=========================
Reads data/raw_transcript.json, calls Gemini 2.5 Flash Lite via OpenRouter,
and saves structured segment data to data/segments.json.

Usage (standalone):
    python src/segments.py

Called by:
    src/main.py  ->  run()

Input:  data/raw_transcript.json
Output: data/segments.json  (array of segment objects — see schema in SETUP.md)
"""

import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# ── Windows compatibility ─────────────────────────────────────────────────────

# Force UTF-8 output (avoids cp1252 crash on emoji/unicode)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Use Windows system cert store so corporate/proxy CAs are trusted
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

# Load .env file (OPENROUTER_API_KEY, LLM_MODEL)
load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────

ROOT        = Path(__file__).parent.parent
INPUT_PATH  = ROOT / "data" / "raw_transcript.json"
OUTPUT_PATH = ROOT / "data" / "segments.json"

# ── Accent color palette (matches reference HTML design) ──────────────────────

ACCENT_COLORS = [
    "#4f98a3",  # teal
    "#6daa45",  # green
    "#da7101",  # orange
    "#7a39bb",  # purple
    "#d19900",  # gold
    "#a13544",  # red
    "#a12c7b",  # magenta
    "#006494",  # blue
    "#437a22",  # dark green
]

# ── LLM Prompts ───────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert at analyzing podcast transcripts and creating visual learning companions for visual learners.

Your task: Read a YouTube podcast transcript and identify 10-16 KEY conceptual segments. For each segment, produce structured data used to render an SVG diagram card.

OUTPUT FORMAT: Return ONLY a valid JSON array. NO markdown fences, NO explanation, NO extra text. Just the raw JSON array starting with [ and ending with ].

SEGMENT SCHEMA (each element in the array):
{
  "id": <integer, 0-indexed>,
  "title": "<punchy title, max 6 words>",
  "timeStart": <float — start time in seconds, taken from nearest [MM:SS] marker>,
  "timeEnd": <float — end time in seconds>,
  "timeLabel": "<human-readable range e.g. '0:00 - 1:45'>",
  "description": "<2-3 sentence explanation written for a visual learner. Concrete, jargon-free. Max 60 words.>",
  "quote": "<the single most memorable verbatim quote from this segment, 10-25 words>",
  "accentColor": "<MUST be one of the exact hex values in the palette below, assigned in order>",
  "svgTemplate": "<MUST be exactly one of: chart | tree | comparison | venn | funnel | flow | ladder | cycle>",
  "svgData": { <see per-template schema below — fields must match exactly> }
}

COLOR PALETTE — assign segment 0 the first color, segment 1 the second, etc. Cycle back if more than 9 segments:
["#4f98a3", "#6daa45", "#da7101", "#7a39bb", "#d19900", "#a13544", "#a12c7b", "#006494", "#437a22"]

SVG TEMPLATE SCHEMAS — pick the template that best VISUALIZES the core concept:

chart  (use for: metrics, performance graphs, data over time, quantitative comparisons)
  {
    "chartTitle": "string",
    "xLabel": "string",
    "yLabel": "string",
    "points": [[x, y], ...],        // 4-7 points; x and y are percentages 0-100
    "annotation": "string",          // short label pointing to a notable point
    "annotationAt": integer          // index in points array to annotate
  }

tree  (use for: hierarchies, folder structures, taxonomies, parent-child relationships)
  {
    "treeTitle": "string",
    "root": "string",
    "children": [
      {"label": "string", "sublabel": "string"},
      ...
    ]   // 3-5 children
  }

comparison  (use for: side-by-side A vs B contrasts, before/after, two approaches)
  {
    "titleA": "string",
    "titleB": "string",
    "descA": "string",
    "descB": "string",
    "footerA": "string",
    "footerB": "string"
  }

venn  (use for: overlapping concepts that compose or intersect, 3-part relationships)
  {
    "vennTitle": "string",
    "circles": [
      {"label": "string", "sublabel": "string"},
      {"label": "string", "sublabel": "string"},
      {"label": "string", "sublabel": "string"}
    ],
    "overlapLabel": "string"
  }

funnel  (use for: narrowing/filtering/selection processes, RAG retrieval, prioritization)
  {
    "funnelTitle": "string",
    "levels": [
      {"label": "string", "sublabel": "string"},
      ...
    ]   // 3-4 levels; widest (largest set) first, narrowest last
  }

flow  (use for: sequential steps, DAG chains, pipelines, workflows)
  {
    "flowTitle": "string",
    "steps": [
      {"label": "string", "sublabel": "string"},
      ...
    ]   // 3-5 steps in order
  }

ladder  (use for: tiered progressions, maturity models, graduated trust levels)
  {
    "ladderTitle": "string",
    "topNote": "string",            // requirement to reach top tier
    "tiers": [
      {"label": "string", "sublabel": "string"},
      ...
    ]   // 3-4 tiers; list BOTTOM tier first, TOP tier last
  }

cycle  (use for: feedback loops, iterative processes, circular flows, meta-loops)
  {
    "cycleTitle": "string",
    "centerLabel": "string",
    "nodes": [
      {"label": "string"},
      ...
    ]   // 4-6 nodes arranged around the circle
  }

IMPORTANT RULES:
1. Segments must be chronological and non-overlapping, covering the full transcript.
2. timeStart/timeEnd must be real seconds derived from the [MM:SS] markers in the transcript.
3. Quotes must be verbatim from the transcript — do not paraphrase.
4. svgData fields must match the chosen template schema exactly (no extra or missing keys).
5. Choose the svgTemplate that most naturally VISUALIZES the concept, not just any template.
6. Descriptions must be written for visual learners — concrete, simple, no jargon.
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def format_transcript(transcript: list[dict]) -> str:
    """
    Convert 795 raw word-level chunks into a clean readable transcript
    with [MM:SS] timestamp markers every ~30 seconds.

    This gives the LLM enough temporal context to set accurate timeStart/timeEnd
    without overwhelming it with 795 individual timestamps.
    """
    lines   = []
    buffer  = []
    last_ts = -30.0  # force a marker at the very start

    for chunk in transcript:
        start = chunk["start"]
        text  = chunk["text"].strip().replace("\n", " ")

        if start - last_ts >= 30:
            if buffer:
                lines.append(" ".join(buffer))
                buffer = []
            mins = int(start) // 60
            secs = int(start) % 60
            lines.append(f"\n[{mins}:{secs:02d}]")
            last_ts = start

        buffer.append(text)

    if buffer:
        lines.append(" ".join(buffer))

    return "\n".join(lines)


def extract_json_array(raw: str) -> list[dict]:
    """
    Robustly extract a JSON array from the LLM response.
    Strips markdown code fences if the model includes them despite instructions.
    """
    text = raw.strip()

    # Strip markdown fences (```json ... ``` or ``` ... ```)
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text)
    text = text.strip()

    # Find the outermost [ ... ] array
    start = text.find("[")
    end   = text.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON array found in LLM response.")

    return json.loads(text[start:end])


def validate_and_normalise(segments: list[dict]) -> list[dict]:
    """
    Validate required fields and normalise accent colors.
    Forces colors from our palette so the renderer never gets an unexpected value.
    """
    REQUIRED = [
        "id", "title", "timeStart", "timeEnd", "timeLabel",
        "description", "quote", "accentColor", "svgTemplate", "svgData",
    ]
    VALID_TEMPLATES = {
        "chart", "tree", "comparison", "venn", "funnel", "flow", "ladder", "cycle"
    }

    for i, seg in enumerate(segments):
        missing = [f for f in REQUIRED if f not in seg]
        if missing:
            raise ValueError(f"Segment {i} is missing required fields: {missing}")

        # Always enforce palette color (LLM sometimes drifts)
        seg["accentColor"] = ACCENT_COLORS[i % len(ACCENT_COLORS)]

        # Guard against unknown template names
        if seg["svgTemplate"] not in VALID_TEMPLATES:
            print(f"   Warning: segment {i} returned unknown template "
                  f"'{seg['svgTemplate']}' — defaulting to 'flow'")
            seg["svgTemplate"] = "flow"

    return segments


# ── Main entry point ──────────────────────────────────────────────────────────

def run(
    input_path:  Path = INPUT_PATH,
    output_path: Path = OUTPUT_PATH,
) -> Path:
    """
    Full Layer 2 pipeline.

    Args:
        input_path:   Path to raw_transcript.json  (default: data/)
        output_path:  Where to save segments.json   (default: data/)

    Returns:
        Path to the saved segments JSON file.
    """
    print("\n🧠  [Layer 2] LLM Segmentation")

    # ── Step 1: Load transcript ───────────────────────────────────────────────
    if not input_path.exists():
        print(f"\n❌  Transcript not found at: {input_path}")
        print("    Run Layer 1 first: python src/transcript.py <youtube_url>")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        transcript = json.load(f)

    total_dur = transcript[-1]["start"] + transcript[-1]["duration"]
    mins, secs = int(total_dur) // 60, int(total_dur) % 60
    print(f"    Loaded {len(transcript)} transcript chunks  ({mins}:{secs:02d} total)")

    # ── Step 2: Format for LLM ────────────────────────────────────────────────
    formatted = format_transcript(transcript)
    word_count = len(formatted.split())
    print(f"    Formatted transcript: ~{word_count:,} words")

    # ── Step 3: Build OpenRouter client ───────────────────────────────────────
    api_key = os.getenv("OPENROUTER_API_KEY")
    model   = os.getenv("LLM_MODEL", "google/gemini-2.5-flash-lite")

    if not api_key:
        print("\n❌  OPENROUTER_API_KEY not set.")
        print("    Copy .env.example -> .env and add your OpenRouter key.")
        sys.exit(1)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    # ── Step 4: Call the LLM ──────────────────────────────────────────────────
    print(f"    Calling {model} via OpenRouter...")

    user_prompt = (
        "Here is the full podcast transcript with [MM:SS] timestamp markers.\n"
        "Analyze it carefully and return the JSON segment array as instructed.\n\n"
        f"TRANSCRIPT:\n{formatted}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.3,    # Low temp for consistent structured output
        max_tokens=8192,
    )

    raw_output = response.choices[0].message.content
    usage      = response.usage
    print(f"    Tokens — input: {usage.prompt_tokens:,}  |  output: {usage.completion_tokens:,}")

    # ── Step 5: Parse + validate ──────────────────────────────────────────────
    print("    Parsing JSON response...")
    try:
        segments = extract_json_array(raw_output)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"\n❌  Failed to parse LLM response as JSON: {e}")
        debug_path = output_path.parent / "segments_debug.txt"
        debug_path.write_text(raw_output, encoding="utf-8")
        print(f"    Raw LLM output saved for inspection: {debug_path.relative_to(ROOT)}")
        sys.exit(1)

    segments = validate_and_normalise(segments)

    print(f"    ✅  {len(segments)} segments extracted and validated:")
    for seg in segments:
        print(f"        [{seg['timeLabel']:>13s}]  {seg['svgTemplate']:<12s}  {seg['title']}")

    # ── Step 6: Save ──────────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)

    print(f"    💾  Saved -> {output_path.relative_to(ROOT)}")
    return output_path


# ── Standalone run ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run()
