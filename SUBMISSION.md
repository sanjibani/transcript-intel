# Submission Package — Transcript Intelligence Take-Home

This document lists everything you need to send to the panel.

## What to send

### 1. Slide deck (PDF) — `outputs/slide_deck.pdf`

- 11 slides, 16:9 aspect ratio, 976 KB
- Self-contained: all charts embedded, no external dependencies
- Open in any PDF viewer
- Print-ready: suitable for projector / screen share

### 2. Code repository (link) — `https://github.com/sanjibani/transcript-intel`

- Public GitHub repo
- 6 pipeline stages, each a standalone script
- README + architecture doc + private interview prep notes
- Reproducible: `bash scripts/run_all.sh` runs the whole thing in 30 seconds

### 3. Video demo — record yourself following `VIDEO_SCRIPT.md`

- 5-10 minutes target, 7 is the sweet spot
- Screen recording + your voice narration
- Save as MP4, ~50-100 MB
- Upload to Loom (cleanest) or Google Drive / YouTube
- Link in your submission email

---

## How to package for submission

### Option A: Email the panel directly

If the assignment was given by email, reply with:

```
Subject: Transcript Intelligence — Submission

Hi [panel/recruiter name],

Attached: slide deck (PDF)
Linked: https://github.com/sanjibani/transcript-intel
Video: [Loom/YouTube link to your recorded demo]

Per the brief, three deliverables:
1. Slide deck (PDF) — 11 slides
2. Code repository — public GitHub link
3. Video demo — 7 min walkthrough

Happy to answer any questions ahead of the live presentation.

Best,
Sanjibani
```

### Option B: Single zipped folder

If they want a single file:

```bash
cd /Users/sabyasachichoudhary/.minimax-agent/projects
zip -r transcript-intel-submission.zip transcript-intel/ \
    -x "transcript-intel/data/processed/*" \
    -x "transcript-intel/outputs/charts/*" \
    -x "transcript-intel/.git/*" \
    -x "transcript-intel/venv/*"
```

This creates a clean zip (~5 MB) with:
- `transcript-intel/README.md` (entry point)
- `transcript-intel/outputs/slide_deck.pdf` (the deck)
- `transcript-intel/pipeline/` (the code)
- `transcript-intel/INTERVIEW_PREP.md` (encrypted — they won't be able to read it; that's fine, it's a placeholder for you)

Attach the zip to your email.

---

## Things to double-check before submitting

- [ ] `outputs/slide_deck.pdf` opens correctly on another machine
- [ ] GitHub repo is public and the link works
- [ ] The repo's main page shows the README, the pipeline folder, and a description
- [ ] No API keys or personal info in any committed file
- [ ] `.env` is in `.gitignore` (verified)
- [ ] `INTERVIEW_PREP.md` is encrypted (verified — only your GPG key can decrypt it)
- [ ] The video has clear audio and is 5-10 minutes long
- [ ] The video link is publicly accessible (Loom share, not "private")
- [ ] You can articulate the 3 insights in 30 seconds each (practice once before recording)

---

## What the panel sees when they open the repo

The first thing they'll see is the README, which has:
- The 3 insights
- Pipeline architecture
- Quick-start commands
- Validation results
- Cost story

The README is the "elevator pitch" for the project. If they only read one file, it should give them the full story.

---

## What the panel sees when they open the PDF

Slide 1: Title + TL;DR
Slide 2: The Detect Outage context (sets the stage)
Slide 3-5: The 3 insights with charts
Slide 6: Sentiment recovery (supporting chart)
Slide 7: Pipeline architecture
Slide 8: Validation against pre-computed labels
Slide 9: Cost & scale story
Slide 10: What we'd build next
Slide 11: Q&A prep

11 slides × ~2 minutes each = 22 minutes talking, leaving 8 minutes for transitions and questions. Fits the 30-minute slot.

---

## What the panel sees when they watch the video

7 minutes of:
- 45 sec: intro + dataset
- 90 sec: pipeline running end-to-end
- 3 min: the 3 insights with charts
- 60 sec: pipeline architecture (why hybrid)
- 45 sec: what's in the repo
- 30 sec: close

The video is the "second pass" through the same story the deck tells. It shows the work in action, not just the results.

---

## What you DON'T need to send

- The `data/processed/` files (regenerable, large)
- The `outputs/charts/` PNGs (regenerable, large)
- The `.env` file (has your API key)
- The `venv/` (regenerable, huge)
- The `__pycache__/` (auto-generated)
- The `.git/` directory (git internals)

The `run_all.sh` script regenerates all of these.

---

## File sizes (approximate)

| File | Size | Include? |
|---|---|---|
| `outputs/slide_deck.pdf` | 976 KB | ✓ |
| `outputs/slide_deck.html` | 490 KB | Optional (linked in repo) |
| `pipeline/*.py` (7 files) | ~50 KB total | ✓ (in repo) |
| `requirements.txt` | 1 KB | ✓ (in repo) |
| `README.md` | 5 KB | ✓ (in repo) |
| `docs/architecture.md` | 4 KB | ✓ (in repo) |
| `INTERVIEW_PREP.md` (encrypted) | 13 KB | Encrypted (in repo) |
| `VIDEO_SCRIPT.md` | 8 KB | Optional (in repo) |
| `LOCAL_SETUP.md` | 7 KB | Optional (in repo) |
| `outputs/charts/*.png` (7 files) | ~1 MB total | Regenerable, exclude from zip |
| `outputs/tables/*.csv` (3 files) | ~50 KB | Regenerable, exclude from zip |
| `data/processed/*.parquet` | ~5 MB | Regenerable, exclude from zip |

## What if the panel wants the notebook instead of the code repo?

The brief says "notebook OR code repository." A code repository is acceptable. If they specifically ask for a notebook, I can generate a Jupyter notebook from the pipeline scripts (each cell = one stage's output).

To request a notebook: ask me to convert the pipeline to a `.ipynb` and I'll add `notebook.ipynb` to the repo.
