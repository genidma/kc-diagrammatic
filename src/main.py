"""
Visual Podcast Companion — CLI Orchestrator
===========================================
Wires Layers 1, 2, and 3 together into a single pipeline.

Usage:
    python src/main.py "https://www.youtube.com/watch?v=VIDEO_ID"
"""

import sys
from pathlib import Path

# Force UTF-8 output on Windows (avoids cp1252 crash on emoji/unicode)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import sys
from pathlib import Path

# Add project root to sys.path to make src package importable when running directly
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import layers
from src import transcript, segments, render

def main():
    if len(sys.argv) < 2:
        print("❌  Usage: python src/main.py <youtube_url>")
        print('    Example: python src/main.py "https://www.youtube.com/watch?v=uYURYHhpmKc"')
        sys.exit(1)

    youtube_url = sys.argv[1]

    print("🚀  Starting Visual Podcast Companion Pipeline")
    print("=" * 60)

    # Layer 1: Extract transcript
    raw_transcript_path = transcript.run(youtube_url)

    # Layer 2: Extract segments
    segments_path = segments.run_segmentation(input_path=raw_transcript_path)

    # Layer 3: Render companion HTML page
    output_html_path = render.run_rendering(youtube_url=youtube_url, input_path=segments_path)

    print("=" * 60)
    print("🎉  Pipeline completed successfully!")
    print(f"    You can view your companion page at: {output_html_path.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
