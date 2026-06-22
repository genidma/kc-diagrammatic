# 🚀 Setup & Handoff Guide

> Everything you need to get up and running on any machine, or to hand this project to a new developer or AI model.

---

## 1. Git Remote Setup (First Time Only)

The repo is initialized locally. To push to GitHub:

### Step 1 — Create the GitHub repo
1. Go to https://github.com/new
2. Name it `kc-diagrammatic` (or your preferred name)
3. Set to **Private** (recommended — your `.env` pattern depends on this)
4. **Do NOT** initialize with README, .gitignore, or license (we already have these)
5. Click **Create repository**

### Step 2 — Add the remote and push
```bash
git remote add origin https://github.com/YOUR_USERNAME/kc-diagrammatic.git
git branch -M main
git push -u origin main
```

> **Note:** If you use SSH instead of HTTPS:
> ```bash
> git remote add origin git@github.com:YOUR_USERNAME/kc-diagrammatic.git
> ```

---

## 2. New Machine Setup (Cloning)

### Step 1 — Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/kc-diagrammatic.git
cd kc-diagrammatic
```

### Step 2 — Create your `.env` file
```bash
copy .env.example .env
```
Then open `.env` and fill in your values:
```
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx
LLM_MODEL=google/gemini-2.5-flash-lite
```
Get your OpenRouter API key at: https://openrouter.ai/

### Step 3 — Create the Python virtual environment
```bash
python -m venv venv
```

### Step 4 — Install dependencies
> **Windows note:** If you're on a corporate/managed machine with a custom SSL cert, use the `--trusted-host` flags below. Otherwise, plain `pip install -r requirements.txt` works.

```bash
# Standard install:
venv\Scripts\pip install -r requirements.txt

# If you get SSL certificate errors (common on managed Windows machines):
venv\Scripts\pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Step 5 — Verify Layer 1 works
```bash
venv\Scripts\python src/transcript.py "https://www.youtube.com/watch?v=uYURYHhpmKc"
```
Expected output:
```
🎧  [Layer 1] Transcript Extraction
    Video ID: uYURYHhpmKc
    Fetching transcript...
    ✅  795 segments — total duration: 23:43
    💾  Saved → data\raw_transcript.json
```

---

## 3. What's Been Built (Current State)

| Layer | File | Status | What it does |
|---|---|---|---|
| 1 | `src/transcript.py` | ✅ **Done & verified** | YouTube URL → `data/raw_transcript.json` |
| 2 | `src/segments.py` | 🔲 Next | Transcript JSON → LLM → `data/segments.json` |
| 3 | `src/render.py` | 🔲 Planned | segments.json → `output/companion.html` |
| 3 | `src/svg_templates/` | 🔲 Planned | 8 Jinja2 SVG templates |
| 3 | `templates/companion.html.jinja` | 🔲 Planned | Full-page HTML template |
| CLI | `src/main.py` | 🔲 Planned | One command runs the full pipeline |
| 4 | `web/` | 🔲 Planned | Next.js web app wrapping the pipeline |

---

## 4. Next Steps — Build Order

### Layer 2: `src/segments.py`

This is the LLM call. It reads `data/raw_transcript.json` and calls Gemini 2.5 Flash Lite via OpenRouter to extract 10–16 conceptual segments.

**Each segment in `data/segments.json` should have:**
```json
{
  "id": 0,
  "title": "The Context Paradox",
  "timeStart": 0,
  "timeEnd": 105,
  "timeLabel": "0:00 – 1:45",
  "description": "More context = dumber results...",
  "quote": "The science shows it actually gets dumber.",
  "accentColor": "#4f98a3",
  "svgTemplate": "chart",
  "svgData": {
    "title": "Performance vs Context Size",
    "points": [[0,95],[30,90],[60,70],[90,45],[120,20]],
    "annotation": "drops off a cliff"
  }
}
```

**The 8 SVG template types the LLM can pick from:**

| Template name | When to use |
|---|---|
| `chart` | Line/bar charts, metrics over time |
| `tree` | Hierarchy, folder structures |
| `comparison` | Side-by-side A vs B |
| `venn` | Overlapping concepts |
| `funnel` | Narrowing / filtering (e.g. RAG top-5) |
| `flow` | DAG-style step chains |
| `ladder` | Tiered progressions |
| `cycle` | Circular / feedback loops |

**To build `src/segments.py`, an AI model needs to:**
1. Load `data/raw_transcript.json`
2. Concatenate the `text` fields into a readable string (optionally with timestamps)
3. Send to OpenRouter using the `openai` SDK:
   - `base_url = "https://openrouter.ai/api/v1"`
   - `api_key = os.getenv("OPENROUTER_API_KEY")`
   - `model = os.getenv("LLM_MODEL")` → `google/gemini-2.5-flash-lite`
4. Prompt the LLM to return a **JSON array** of segment objects (schema above)
5. Parse and validate the JSON
6. Save to `data/segments.json`

**Reference output to match:** See `agent-skills-companion.html` — the 14 segment cards in that file are the gold standard for what segments.json should produce.

---

### Layer 3: `src/render.py` + SVG templates

After segments.json is working, build:
1. `src/svg_templates/` — 8 Jinja2 `.svg.jinja` files, one per template type
2. `templates/companion.html.jinja` — full-page HTML matching the design of `agent-skills-companion.html`
3. `src/render.py` — loads segments.json, renders each SVG, assembles the HTML page

---

### CLI: `src/main.py`

Orchestrates all three layers in sequence:
```bash
venv\Scripts\python src/main.py "https://www.youtube.com/watch?v=SOME_VIDEO"
# → fetches transcript → calls LLM → renders HTML
# → open output/companion.html in browser
```

---

### Layer 4: `web/` (Next.js)

After the CLI pipeline is working end-to-end:
```bash
cd web
npx -y create-next-app@latest ./
npm run dev
```
The Next.js API route at `web/app/api/generate/route.ts` will shell out to `python src/main.py` and serve the result.

---

## 5. Key Design Decisions (Don't Change Without Reading This)

| Decision | Choice | Why |
|---|---|---|
| LLM Provider | OpenRouter (`google/gemini-2.5-flash-lite`) | Free-tier friendly, 1M context, cheap |
| SVG approach | Templates (Jinja2) — LLM fills data, Python renders | Consistent output, no hallucinated SVG attributes |
| Transcript source | `youtube-transcript-api` v1.x | Free, no auth for public videos |
| SSL on Windows | `truststore` package | Corporate CA support via Windows cert store |
| Web framework | Next.js | Full-stack, easy Vercel deploy |
| File message bus | Each layer writes to disk, next reads from disk | No in-memory coupling between layers |

---

## 6. Useful Commands (Quick Reference)

```bash
# Activate venv (do this first in every new terminal)
venv\Scripts\activate

# Run just the transcript layer
venv\Scripts\python src/transcript.py "https://youtu.be/VIDEO_ID"

# Run just the segmentation layer (once segments.py is built)
venv\Scripts\python src/segments.py

# Run the full pipeline (once main.py is built)
venv\Scripts\python src/main.py "https://youtu.be/VIDEO_ID"

# Run tests
venv\Scripts\python -m pytest tests/

# Install a new package (always use venv pip)
venv\Scripts\pip install package-name

# Check git status
git status

# Commit progress
git add .
git commit -m "feat: description of what you built"
git push
```

---

*Last updated after Layer 1 completion. Layer 2 is the next build target.*
