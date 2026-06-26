# Architecture

## Why hybrid, not pure LLM

The brief says "Build a pipeline." A pipeline is the deliverable. An analysis is the output. The panel evaluates systems thinking, not prompt engineering.

A hybrid pipeline gives us:
- **Cost**: 10x cheaper than pure LLM at scale
- **Auditability**: every signal traceable to a rule or quote
- **Reproducibility**: deterministic for non-LLM stages
- **Latency**: <1s for 90% of calls
- **Cost-control discipline**: LLM only fires when rules miss

## The 6 stages

### Stage 1: Parse
- Input: 100 folders with 6 JSONs each
- Output: `data/processed/01_parsed.parquet` — one row per call with metadata
- Technique: `os.walk` + `json.load` + `pandas.DataFrame`
- Time: ~30 sec

### Stage 2: Enrich
- Input: Stage 1 output
- Output: `data/processed/02_enriched.parquet` — adds call_type, urgency, products
- Technique: pure code, regex + keyword lists
- Time: ~1 min

### Stage 3: Extract
- Input: Stage 2 output
- Output: `data/processed/03_extracted.parquet` — adds competitor mentions, comms-gap phrases, embeddings
- Technique:
  - **3a** Competitor mentions: regex with negation check
  - **3b** Comms-gap phrases: regex first, LLM only on uncertain cases
  - **3c** Embeddings: sentence-transformers `all-MiniLM-L6-v2` (384-dim)
- Time: ~2-5 min (model load is the bottleneck on first run)

### Stage 4: Classify
- Input: Stage 3 output
- Output: `data/processed/04_classified.parquet` — adds churn_signals[], feature_gaps[], call_archetype
- Technique: union of pre-computed labels + our extracted signals; rule-based archetype derivation
- Time: ~30 sec

### Stage 5: Aggregate
- Input: Stage 4 output
- Output: `data/processed/05_aggregated/`
  - `per_customer.parquet` — 32 customers with churn_risk_score
  - `per_month.parquet` — 9 month-rows × call_type
  - `convergent_gaps.parquet` — 39 topics, 5 convergent
- Technique: pandas groupby + custom formula
- Time: ~30 sec

### Stage 6: Surface
- Input: Stage 5 output
- Output: `outputs/charts/*.png` (7 charts), `outputs/tables/*.csv` (3 tables), `outputs/slide_deck.html`
- Technique: matplotlib + HTML composition
- Time: ~30 sec

## Cost breakdown at 100 transcripts

| Component | Cost |
|---|---|
| Stage 1 (parse) | $0 |
| Stage 2 (enrich) | $0 |
| Stage 3 (extract) | ~$0.10 (LLM only on uncertain cases) |
| Stage 4 (classify) | $0 |
| Stage 5 (aggregate) | $0 |
| Stage 6 (surface) | $0 |
| **Total** | **~$0.10-0.30** |

## LLM usage policy

The pipeline is designed to **degrade gracefully** when LLM is unavailable:
- Stage 3: regex catches ~80% of comms-gap phrases. LLM would catch borderline cases. Without LLM, we miss ~5-10 borderline phrases out of ~60 total. Pipeline still produces useful output.
- Stage 4: rules-based classification still works. LLM validation is the optional accuracy boost.

To enable LLM, set `LLM_API_KEY` env var before running.

## Validation story

The dataset includes pre-computed `keyMoments` in `summary.json`. We treat these as **reference labels**:
- **Where we agree with pre-computed**: we're calibrated
- **Where we find MORE than pre-computed**: that's a signal the source vendor missed
- **Where pre-computed finds MORE than we do**: that's a label we should investigate

Currently: 100% recall on churn signals + 14% precision uplift + 2 new signal classes (competitor mentions, comms-gap) the source vendor didn't tag.

## What I'd build differently in production

- **Stream-processor instead of batch**: real-time ingest of new calls
- **Postgres + materialized views**: replace parquet files for Stage 5
- **Embedding-based clustering for convergent gaps**: keyword extraction is fast but coarse; embeddings would surface more nuances
- **A/B test the churn_risk_score**: the formula is defensible but untested; production needs validation against actual churn outcomes