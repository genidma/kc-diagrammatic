"""
Layer 1: Transcript Extraction
==============================
Fetches a YouTube video transcript and saves it to data/raw_transcript.json.

Usage (standalone):
    python src/transcript.py "https://www.youtube.com/watch?v=uYURYHhpmKc"

Called by:
    src/main.py  →  run(youtube_url)

Output format (data/raw_transcript.json):
    [
        {"text": "Welcome to the podcast.", "start": 0.0, "duration": 2.5},
        ...
    ]
"""

import json
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi

# youtube-transcript-api v1.x restructured some exception names.
# Import defensively so the code works across minor version bumps.
try:
    from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
except ImportError:
    # Fallback: treat all retrieval errors as a single base class
    from youtube_transcript_api import CouldNotRetrieveTranscript  # type: ignore
    TranscriptsDisabled = CouldNotRetrieveTranscript  # type: ignore
    NoTranscriptFound = CouldNotRetrieveTranscript    # type: ignore
    VideoUnavailable = CouldNotRetrieveTranscript     # type: ignore

# Force UTF-8 output on Windows (avoids cp1252 crash on emoji/unicode)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Use the Windows system certificate store so corporate/proxy CAs are trusted.
# Falls back silently if truststore is not installed.
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass



# ── Paths ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_PATH = DATA_DIR / "raw_transcript.json"


# ── Helpers ──────────────────────────────────────────────────────────────────

def extract_video_id(url: str) -> str:
    """
    Extract the YouTube video ID from any common URL format.

    Supports:
        https://www.youtube.com/watch?v=VIDEO_ID
        https://youtu.be/VIDEO_ID
        https://www.youtube.com/watch?v=VIDEO_ID&t=123s
        https://youtu.be/VIDEO_ID?si=abc123
    """
    parsed = urlparse(url.strip())

    # Short link: youtu.be/VIDEO_ID
    if parsed.hostname in ("youtu.be", "www.youtu.be"):
        video_id = parsed.path.lstrip("/").split("?")[0]
        if video_id:
            return video_id

    # Standard link: youtube.com/watch?v=VIDEO_ID
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]

    raise ValueError(
        f"Could not extract a video ID from: {url}\n"
        "Expected formats:\n"
        "  https://www.youtube.com/watch?v=VIDEO_ID\n"
        "  https://youtu.be/VIDEO_ID"
    )


def fetch_transcript(video_id: str) -> list[dict]:
    """
    Fetch the transcript for a given YouTube video ID.

    Returns a list of dicts: [{text, start, duration}, ...]
    Tries English first; falls back to the first available language.

    Note: youtube-transcript-api v1.x uses an instance-based API.
    """
    api = YouTubeTranscriptApi()

    try:
        # Prefer English transcript
        fetched = api.fetch(video_id, languages=["en"])
    except NoTranscriptFound:
        # Fall back to any available language
        print("   Warning: No English transcript found -- trying any available language...")
        transcript_list = api.list(video_id)
        first = next(iter(transcript_list))
        fetched = first.fetch()

    # v1.x returns FetchedTranscript (iterable of snippet objects).
    # Normalise to plain dicts for consistent downstream handling.
    return [
        {"text": s.text, "start": s.start, "duration": s.duration}
        for s in fetched
    ]


def format_duration(total_seconds: float) -> str:
    """Convert seconds to MM:SS display string."""
    mins = int(total_seconds) // 60
    secs = int(total_seconds) % 60
    return f"{mins}:{secs:02d}"


def save_transcript(transcript: list[dict], path: Path) -> None:
    """Write transcript JSON to disk, creating parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(transcript, f, indent=2, ensure_ascii=False)


# ── Main entry point ─────────────────────────────────────────────────────────

def run(youtube_url: str, output_path: Path = OUTPUT_PATH) -> Path:
    """
    Full Layer 1 pipeline.

    Args:
        youtube_url:  Any valid YouTube video URL.
        output_path:  Where to save raw_transcript.json (default: data/).

    Returns:
        Path to the saved transcript JSON file.
    """
    print(f"\n🎧  [Layer 1] Transcript Extraction")
    print(f"    URL: {youtube_url}")

    # Step 1: Extract video ID
    try:
        video_id = extract_video_id(youtube_url)
        print(f"    Video ID: {video_id}")
    except ValueError as e:
        print(f"\n❌  {e}")
        sys.exit(1)

    # Step 2: Fetch transcript
    try:
        print(f"    Fetching transcript...")
        transcript = fetch_transcript(video_id)
    except TranscriptsDisabled:
        print(f"\n❌  Transcripts are disabled for video: {video_id}")
        print("    Try a different video with captions enabled.")
        sys.exit(1)
    except NoTranscriptFound:
        print(f"\n❌  No transcript found for video: {video_id}")
        print("    The video may not have captions in any language.")
        sys.exit(1)
    except VideoUnavailable:
        print(f"\n❌  Video unavailable: {video_id}")
        print("    The video may be private, deleted, or age-restricted.")
        sys.exit(1)

    # Step 3: Print summary
    total_duration = transcript[-1]["start"] + transcript[-1]["duration"]
    print(f"    ✅  {len(transcript)} segments — total duration: {format_duration(total_duration)}")

    # Step 4: Save to disk
    save_transcript(transcript, output_path)
    print(f"    💾  Saved → {output_path.relative_to(ROOT)}")

    return output_path


# ── Standalone run ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/transcript.py <youtube_url>")
        print('Example: python src/transcript.py "https://youtu.be/uYURYHhpmKc"')
        sys.exit(1)

    run(sys.argv[1])
