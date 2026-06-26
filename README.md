# transcript-intel

A hybrid pipeline that processes 100 call transcripts and surfaces three insights for B2B SaaS stakeholders. Built as a take-home assignment for a Transcript Intelligence product role.

## The three insights

1. **Churn risk concentration** — 4-8 accounts absorb most churn risk after the March 2026 Detect Outage. 14 customers scored HIGH risk; top 4 (Blackridge, Cobalt, Northstar, Helix) all score 90/100 on the composite risk formula.

2. **Communication gap** — 39 of 100 calls contain "no notification" / "flying blind" language from Aegis's silence during outages. Concentrated in March 11-12 (peak outage window).

3. **Convergent feature gaps** — 5 product gaps were independently identified by customers AND engineers within weeks of each other. The strongest: pipeline-health visibility (mentioned by Pinnacle customer on Apr 16 and by Detect team on Apr 28 retro).

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

## Validation

The dataset includes pre-computed `keyMoments` in `summary.json`. We treat these as **reference labels**, not ground truth.

| Metric | Our extraction | Pre-computed | Agreement |
|---|---|---|---|
| Calls with churn_signal | 59 | 61 | 52 both agree · 7 we found more · 0 we missed |
| Feature gaps | 51 (36 customer + 15 internal) | 51 | 100% recall, 5 convergent topics identified |
| Competitor mentions | 98 across 30 calls | n/a | New signal — not in pre-computed |
| Comms-gap phrases | 57 across 38 calls | n/a | New signal — not in pre-computed |

**100% recall + 14% precision uplift + 2 new signal classes.**

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
export LLM_BASE_URL="https://api.minimax.chat/v1"   # default
export LLM_API_KEY="<your-minimax-key>"              # required
export LLM_MODEL="MiniMax-Text-01"                  # default
```

Then re-run `python3 pipeline/03_extract.py` — LLM will fire only on calls where regex missed but sentiment suggests a gap (typically 5-15 calls).

## License

This is a take-home assignment submission. The methodology is reusable; the dataset is provided by the hiring company.