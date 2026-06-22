# 🎧 Visual Podcast Companion

> **Transform any YouTube podcast into a visual, segment-by-segment learning companion — built for visual learners.**

Inspired by the Feynman technique of breaking complex ideas into simple, digestible chunks. This tool takes a YouTube URL, extracts the transcript, uses an LLM to identify key conceptual segments, and renders a beautiful HTML companion page with inline SVG diagrams, timestamps, pull quotes, and YouTube deep links — so you can follow along visually.

---

## 🖼️ Reference Output

The file [`agent-skills-companion.html`](./agent-skills-companion.html) in this repo is the **reference output** — hand-crafted by Perplexity for the YouTube video [Agent Skills Podcast](https://www.youtube.com/watch?v=uYURYHhpmKc). Every design and architecture decision made in this project should produce output that looks and feels like this file.

---

## 🏗️ Architecture

The system is a **4-layer pipeline**, designed so each layer is independently testable:

```
YouTube URL
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  LAYER 1: Transcript Extraction (Python)            │
│  youtube-transcript-api → data/raw_transcript.json  │
│  Input:  YouTube URL string                         │
│  Output: [{text, start, duration}, ...]             │
└─────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  LAYER 2: Segmentation + SVG Spec (Gemini LLM)      │
│  raw_transcript.json → data/segments.json           │
│  Input:  Raw transcript JSON                        │
│  Output: [{title, timeRange, description, quote,    │
│            accentColor, svgTemplate, svgData}, ...] │
└─────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  LAYER 3: HTML + SVG Render (Python + Jinja2)       │
│  segments.json → output/companion.html              │
│  Input:  Structured segment data                    │
│  Output: Standalone HTML file (no external deps)    │
└─────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  LAYER 4: Web App (Next.js)                         │
│  Frontend: URL input form, progress state           │
│  API Route: shells out to Python CLI                │
│  Result: Rendered companion page in the browser     │
└─────────────────────────────────────────────────────┘
```

> **Important for AI models / developers picking up this project**: The Python pipeline (Layers 1–3) and the Next.js web app (Layer 4) live in the **same repo**. The Next.js API route calls the Python CLI as a subprocess. This avoids the need for a separate backend service and keeps deployment simple.

---

## 🎨 SVG Strategy Decision

**Decision: Template-based SVGs (not raw LLM-generated SVGs)**

The LLM picks the right template type and provides JSON data to fill it. Python renders the actual SVG using Jinja2 templates. This was chosen over having the LLM generate raw SVG code for the following reasons:

| Criterion | Raw SVG (rejected) | Templates (chosen) |
|---|---|---|
| **Consistency** | ❌ Varies wildly between runs | ✅ Uniform visual style |
| **Debugging** | ❌ SVG syntax errors are opaque | ✅ Fix the template, fix all output |
| **LLM token cost** | ❌ SVG is verbose (~500+ tokens/diagram) | ✅ LLM outputs compact JSON (~50 tokens) |
| **Breakage risk** | ❌ LLMs hallucinate SVG attributes | ✅ Python renders — no hallucination risk |
| **Speed** | ❌ Slower (more tokens generated) | ✅ Faster inference |

### The 8 SVG Template Types

| Template | Use case | Example from reference HTML |
|---|---|---|
| `chart` | Line/bar charts, metrics over time | Seg 01 — Performance vs Context Size |
| `tree` | Hierarchy, folder structures | Seg 02 — Anatomy of a Skill Folder |
| `comparison` | Side-by-side A vs B | Seg 03 — Two Creation Paths |
| `venn` | Overlapping concepts | Seg 04 — Skills vs MCP vs agents.md |
| `funnel` | Narrowing / filtering / RAG | Seg 06 — 40K Skills → Top 5 |
| `flow` | DAG-style step chains | Seg 09 — EDD + Trajectory Scoring |
| `ladder` | Tiered progressions | Seg 10 — 3-Tier Production Ladder |
| `cycle` | Circular / feedback loops | Seg 11 — Meta-Skills feedback loop |

---

## 🔑 LLM Provider

**Gemini via Google AI Studio (free tier)**

- Free tier is generous with no credit card required
- Gemini 1.5 Flash / Pro supports a **1.5M token context window** — handles very long podcast transcripts in a single call
- The `google-generativeai` Python SDK is well-maintained
- Sign up and get your free API key at: https://aistudio.google.com/

---

## 📁 Repo Structure

```
kc-diagrammatic/
│
├── agent-skills-companion.html   # ⭐ Reference output — the design target
│
├── src/                          # Python pipeline (Layers 1–3)
│   ├── main.py                   # CLI entrypoint: python src/main.py <youtube_url>
│   ├── transcript.py             # Layer 1: YouTube transcript extractor
│   ├── segments.py               # Layer 2: LLM-based segmentation + SVG spec
│   ├── render.py                 # Layer 3: HTML + SVG renderer (Jinja2)
│   └── svg_templates/            # 8 Jinja2 SVG template files
│       ├── chart.svg.jinja
│       ├── tree.svg.jinja
│       ├── comparison.svg.jinja
│       ├── venn.svg.jinja
│       ├── funnel.svg.jinja
│       ├── flow.svg.jinja
│       ├── ladder.svg.jinja
│       └── cycle.svg.jinja
│
├── templates/
│   └── companion.html.jinja      # HTML output template (mirrors reference design)
│
├── data/                         # ⚠️ .gitignore'd — intermediate files only
│   ├── raw_transcript.json       # Output of Layer 1
│   └── segments.json             # Output of Layer 2
│
├── output/                       # ⚠️ .gitignore'd — generated HTML files
│   └── companion.html
│
├── web/                          # Next.js web app (Layer 4)
│   ├── app/
│   │   ├── page.tsx              # Landing page with YouTube URL input
│   │   ├── api/
│   │   │   └── generate/
│   │   │       └── route.ts      # API route: calls Python CLI as subprocess
│   │   └── companion/
│   │       └── page.tsx          # Renders the generated companion page
│   └── components/
│       ├── URLInput.tsx
│       ├── LoadingState.tsx
│       └── SegmentPreview.tsx
│
├── tests/
│   └── test_segments.py          # Eval cases for segment extraction quality
│
├── requirements.txt              # Python dependencies
├── .env                          # ⚠️ NEVER COMMIT — your API keys live here
├── .env.example                  # Safe to commit — template with no real keys
├── .gitignore
└── README.md                     # This file
```

---

## ⚙️ Setup

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the web app — Phase 2 only)
- A free Google AI Studio API key: https://aistudio.google.com/

### 1. Clone and enter the repo

```bash
git clone <your-repo-url>
cd kc-diagrammatic
```

### 2. Set up Python environment

```bash
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure your API key

```bash
cp .env.example .env
# Open .env and replace the placeholder with your real API key
```

Your `.env` file should look like:

```
GOOGLE_AI_STUDIO_API_KEY=your_actual_key_here
LLM_PROVIDER=gemini
```

> ⚠️ **`.env` is in `.gitignore`**. Never commit your actual API key. Only `.env.example` (with placeholder values) is committed to the repo.

---

## 🚀 Phase 1 — Python Pipeline (Local CLI)

Run the full pipeline from the command line:

```bash
python src/main.py "https://www.youtube.com/watch?v=uYURYHhpmKc"
```

This will:
1. Fetch the transcript → `data/raw_transcript.json`
2. Call Gemini to extract segments → `data/segments.json`
3. Render the companion HTML → `output/companion.html`

Open `output/companion.html` in your browser to see the result.

### Phase 1 File Responsibilities

| File | Layer | Responsibility |
|---|---|---|
| `src/main.py` | Orchestrator | CLI entrypoint, wires layers 1–3 together |
| `src/transcript.py` | Layer 1 | Calls `youtube-transcript-api`, saves JSON |
| `src/segments.py` | Layer 2 | Prompts Gemini, parses structured output, saves JSON |
| `src/render.py` | Layer 3 | Loads Jinja2 templates, renders SVGs + HTML |
| `src/svg_templates/*.jinja` | Layer 3 | One template per diagram type (8 total) |
| `templates/companion.html.jinja` | Layer 3 | Full-page HTML template |

### Running tests

```bash
python -m pytest tests/
```

---

## 🌐 Phase 2 — Web App (Next.js)

The Next.js app wraps the Python pipeline behind a web interface.

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000, paste a YouTube URL, and the companion page is generated in the browser.

### How the Web App Calls Python

> **Note for AI models**: This is the key integration point between Phase 1 and Phase 2.

The Next.js API route (`web/app/api/generate/route.ts`) shells out to the Python CLI:

```typescript
// Simplified example of the API route
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs';

const execAsync = promisify(exec);

export async function POST(request: Request) {
  const { youtubeUrl } = await request.json();
  const repoRoot = path.resolve(process.cwd(), '..');
  await execAsync(`python ${repoRoot}/src/main.py "${youtubeUrl}"`);
  const html = fs.readFileSync(`${repoRoot}/output/companion.html`, 'utf-8');
  return new Response(html, { headers: { 'Content-Type': 'text/html' } });
}
```

The Python script writes `output/companion.html` to disk, and the API route reads and returns it. **No separate Python web server is needed.**

---

## 🗺️ Deployment Roadmap

| Phase | Status | Target |
|---|---|---|
| Python pipeline (local CLI) | 🔲 In progress | Works on local machine |
| Next.js web app (local) | 🔲 Planned | Runs at localhost:3000 |
| Deploy to Vercel / Railway | 🔲 Issue tracked | Public URL, shareable with others |

> **Issue to track**: Full-stack deployment — Python backend + Next.js frontend on Vercel or Railway. This is a separate milestone after the local pipeline is working and fully tested.

---

## 📦 Python Dependencies

| Package | Purpose |
|---|---|
| `youtube-transcript-api` | Fetch transcripts from YouTube (no auth required for public videos) |
| `google-generativeai` | Gemini API client (Google AI Studio) |
| `jinja2` | SVG and HTML template rendering |
| `python-dotenv` | Load `.env` variables into `os.environ` |
| `pytest` | Test runner for segment extraction eval cases |

Install all at once:

```bash
pip install -r requirements.txt
```

---

## 📝 Design Principles

1. **Determinism over prompt engineering** — Python scripts handle data transformation; LLMs handle reasoning only
2. **File message bus** — each layer writes its output to disk; the next layer reads from disk (no in-memory coupling between layers)
3. **Reference HTML is the spec** — `agent-skills-companion.html` is the design and content target for all pipeline output
4. **Templates, not raw generation** — SVG Jinja2 templates produce consistent, debuggable output vs. raw LLM-generated SVG code
5. **Local first** — the full pipeline must work entirely on a local machine before any cloud deployment is attempted

---

*Built with ❤️ for visual learners.*
