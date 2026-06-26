# Transcript Intelligence Pipeline

A hybrid pipeline that processes call transcripts and surfaces insights for stakeholders across a B2B SaaS company.

## What this is

A take-home assignment for a Transcript Intelligence product role. The pipeline:

1. Parses 100 transcripts (support calls, account-manager/customer calls, internal team calls)
2. Extracts structured signals (churn indicators, communication gaps, feature gaps)
3. Aggregates per-customer, per-month, per-call-type
4. Surfaces three core insights for stakeholders

## Pipeline Architecture

```
Raw transcripts → [1 PARSE] → [2 ENRICH] → [3 EXTRACT] → [4 CLASSIFY] → [5 AGGREGATE] → [6 SURFACE]
                                          ↓
                                    Rules + ML + Embeddings + Selective LLM
```

Each stage has a single responsibility and a clean input/output contract. Stages 1-2 are deterministic code. Stage 3 uses rules first, embeddings for clustering. Stage 4 uses selective LLM for semantic edge cases. Stages 5-6 are pure pandas + matplotlib.

See [`docs/architecture.md`](docs/architecture.md) for the full stage-by-stage spec.

## Insights surfaced

- **Churn risk concentration** — 4-8 accounts absorb most churn risk after a March 2026 outage
- **Communication gap** — 39 of 100 calls show "no notification" / "flying blind" patterns
- **Convergent feature gaps** — product gaps identified independently by customers and engineers

## Quick start

```bash
pip install -r requirements.txt
python pipeline/01_parse.py        # ~30s
python pipeline/02_enrich.py       # ~1 min
python pipeline/03_extract.py      # ~5 min
python pipeline/04_classify.py     # ~2 min
python pipeline/05_aggregate.py    # ~30s
python pipeline/06_surface.py      # ~30s
```

Or open `notebook.ipynb` for a walkthrough.

## Project layout

```
transcript-intel/
├── pipeline/         # 6 stages, each a standalone runnable script
├── docs/             # architecture diagrams and decisions
├── outputs/          # generated charts and tables (gitignored)
├── data/             # raw and processed data (gitignored)
├── notebook.ipynb    # master walkthrough
└── INTERVIEW_PREP.md # private notes — never committed
```

## Cost story

At 100 transcripts, the pipeline runs for **~$0.30 in LLM API calls** total. The bulk of work is rules-based and free. A pure-LLM approach would cost $5-10 for the same work; at 100x scale, the difference is $30 vs $5,000.

## License

This is a take-home assignment submission. The methodology is reusable; the dataset is provided by the hiring company.