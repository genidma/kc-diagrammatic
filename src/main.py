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

    import shutil

    youtube_url = sys.argv[1]

    print("🚀  Starting Visual Podcast Companion Pipeline")
    print("=" * 60)

    # Extract video ID to check cache
    try:
        video_id = transcript.extract_video_id(youtube_url)
        print(f"    Video ID: {video_id}")
    except ValueError as e:
        print(f"\n❌  {e}")
        sys.exit(1)

    cache_dir = ROOT / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached_segments_path = cache_dir / f"{video_id}.json"
    segments_path = ROOT / "data" / "segments.json"

    if cached_segments_path.exists():
        print(f"\n✨  [Cache Hit] Found pre-generated segments for video: {video_id}")
        print("    Skipping Transcript Extraction and LLM Segmentation calls.")
        shutil.copy(cached_segments_path, segments_path)
    else:
        print(f"\n✨  [Cache Miss] No pre-generated segments found. Running full pipeline...")
        # Layer 1: Extract transcript
        raw_transcript_path = transcript.run(youtube_url)

        # Layer 2: Extract segments
        segments_path = segments.run_segmentation(input_path=raw_transcript_path)

        # Save copy to cache
        shutil.copy(segments_path, cached_segments_path)
        print(f"    💾  [Cache Save] Saved copy → {cached_segments_path.relative_to(ROOT)}")

    # Layer 3: Render companion HTML page
    output_html_path = render.run_rendering(youtube_url=youtube_url, input_path=segments_path)

    print("=" * 60)
    print("🎉  Pipeline completed successfully!")
    print(f"    You can view your companion page at: {output_html_path.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
