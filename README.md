# transcript-intel

A hybrid pipeline that processes 100 call transcripts and surfaces three insights for B2B SaaS stakeholders. Built as a take-home assignment for a Transcript Intelligence product role.

## The three insights

1. **Churn risk concentration** — 4-8 accounts absorb most churn risk after the March 2026 Detect Outage. 14 customers scored HIGH risk; top 4 (Blackridge, Cobalt, Northstar, Helix) all score 90/100 on the composite risk formula.

2. **Communication gap** — 39 of 100 calls contain "no notification" / "flying blind" language from Aegis's silence during outages. Concentrated in March 11-12 (peak outage window).

3. **Convergent feature gaps** — 5 product gaps were independently identified by customers AND engineers within weeks of each other. The strongest: pipeline-health visibility (mentioned by Pinnacle customer on Apr 16 and by Detect team on Apr 28 retro).

## How to read this repo

If you have 3 minutes: read **[PLAN.md](PLAN.md)** at the repo root. It's the tour map — what each file does, where to find the key formulas, what's in scope and what isn't.

If you have 10 minutes: PLAN.md, then [`docs/architecture.md`](docs/architecture.md) for the stage-by-stage spec, then skim the module docstrings at the top of each `pipeline/*.py` file. The first ~30 lines of each script explains what it does, why the technique was chosen, and what it costs.

If you want to run it: `bash scripts/run_all.sh` from the project root.

## Pipeline architecture

```
Raw transcripts → [1 PARSE] → [2 ENRICH] → [3 EXTRACT] → [4 CLASSIFY] → [5 AGGREGATE] → [6 SURFACE]
                                          ↓
                                    Rules + ML + Embeddings + Selective LLM
```

| Stage | What | Technique | Cost |
|---|---|---|---|
| 1. Parse | Walk 100 folders → DataFrame | os.walk + json.load + pandas | $0 |
| 2. Enrich | Add call_type, urgency, products | Rules (regex) | $0 |
| 3. Extract | Competitors, comms-gap, embeddings | Regex + selective LLM + sentence-transformers | ~$0.10 |
| 4. Classify | Churn signals, feature gaps, call archetype | Validate against pre-computed + rules | $0 |
| 5. Aggregate | Per-customer, per-month, convergent gaps | Pure pandas | $0 |
| 6. Surface | 7 charts + 3 tables + slide deck | matplotlib + HTML | $0 |

Stages 1-2 are deterministic. Stages 3-4 use LLM only when rules miss. Stages 5-6 are pure code.

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline (~30 seconds)
bash scripts/run_all.sh

# Or run stages individually
python3 pipeline/01_parse.py
python3 pipeline/02_enrich.py
python3 pipeline/03_extract.py
python3 pipeline/04_classify.py
python3 pipeline/05_aggregate.py
python3 pipeline/06_surface.py

# Build the slide deck (HTML, can be printed to PDF)
python3 scripts/build_slide_deck.py

# Open the slide deck
open outputs/slide_deck.html
```

## What we extract vs. what we use as input

We're explicit about which signals we extract from text and which we use as input from the pre-computed labels.

| Signal | Source | What we did |
|---|---|---|
| Competitor mentions | Transcript text | Regex extraction (98 mentions, 30 calls) |
| Comms-gap phrases | Transcript text | Regex (57) + selective LLM (15) = 72 phrases, 53 calls |
| Churn signals | Pre-computed `keyMoments` | Used as input features for risk scoring; tagged with `caller_side` |
| Feature gaps | Pre-computed `keyMoments` | Used as input features; tagged with `caller_side` for cross-side analysis |

The architecture supports a real extraction layer for churn signals and feature gaps (regex + LLM, same as the comms-gap stage). For this 100-transcript assignment we used the pre-computed labels to keep scope tight. The "what we'd build next" slide covers the upgrade path.

## Project layout

```
transcript-intel/
├── pipeline/                  # 6 stages, each a standalone runnable script
│   ├── _llm.py               # Flexible LLM client (graceful fallback)
│   ├── 01_parse.py
│   ├── 02_enrich.py
│   ├── 03_extract.py
│   ├── 04_classify.py
│   ├── 05_aggregate.py
│   └── 06_surface.py
├── scripts/
│   ├── run_all.sh             # Run the full pipeline
│   └── build_slide_deck.py    # Build outputs/slide_deck.html
├── docs/
│   └── architecture.md        # Stage-by-stage spec
├── data/processed/            # Intermediate stage outputs (gitignored)
├── outputs/
│   ├── charts/                # 7 PNG charts (gitignored)
│   ├── tables/                # 3 CSV tables (gitignored)
│   └── slide_deck.html        # Self-contained HTML slide deck
├── README.md
├── INTERVIEW_PREP.md          # Private — encrypted via git-crypt
└── requirements.txt
```

## Cost story

| Volume | Pure LLM | Hybrid (this pipeline) |
|---|---|---|
| 100 calls (this assignment) | ~$0.50 | ~$0.30 |
| 50,000 / year | $250 | $25 |
| 500,000 / year | $2,500 | $250 |
| 5,000,000 / year | $25,000 | $2,500 |

Plus: full audit trail for every signal, deterministic outputs for non-LLM stages, <1s latency for 90% of calls.

## LLM configuration

The pipeline runs without an LLM by default (regex rules catch most signals). To enable LLM validation in Stages 3-4:

```bash
# Edit .env with your real MiniMax API key
cp .env.example .env
nano .env   # paste your LLM_API_KEY
```

The defaults in `.env.example`:
- `LLM_BASE_URL=https://api.minimax.io/v1`  ← correct endpoint for MiniMax Mavis
- `LLM_MODEL=MiniMax-Text-01`
- `LLM_API_KEY=<your-key-here>`  ← replace with real key

Then re-run `python3 pipeline/03_extract.py` — LLM will fire only on calls where regex missed but sentiment suggests a gap (typically 5-15 calls).

## License

This is a take-home assignment submission. The methodology is reusable; the dataset is provided by the hiring company.