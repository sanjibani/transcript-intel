# Local Setup — Run the Pipeline Yourself

This guide walks you through running the pipeline on your own machine. If something breaks, check the troubleshooting section at the bottom.

## Prerequisites

- **macOS** (the pipeline was developed and tested on Mac; Linux should also work; Windows untested)
- **Python 3.11+** (tested on 3.14)
- **pip** (comes with Python)
- **Git**
- **~500 MB free disk space** (sentence-transformers model download)

The dataset and code repository are at:
- Code: `https://github.com/sanjibani/transcript-intel`
- Dataset: `/Users/sabyasachichoudhary/Downloads/interview-assignment/dataset/` (already on this machine)

## 5-minute setup

```bash
# 1. Clone the repo
git clone https://github.com/sanjibani/transcript-intel.git
cd transcript-intel

# 2. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) install Playwright for HTML→PDF conversion
pip install playwright
python -m playwright install chromium
```

The `requirements.txt` includes a `pydantic-core==2.41.5` pin that fixes the Python 3.14 + openai 2.43.0 compatibility issue.

## Optional: Set up the LLM

The pipeline runs WITHOUT an LLM by default (regex rules catch most signals). To enable LLM validation in Stages 3-4:

```bash
# 1. Copy the env template
cp .env.example .env

# 2. Edit .env — paste your real MiniMax API key
nano .env
# (replace the placeholder LLM_API_KEY value)
```

The .env file is gitignored — your key will never be committed. The pipeline reads it on import via `python-dotenv`.

## Run the full pipeline

```bash
bash scripts/run_all.sh
```

This runs all 6 stages in sequence. Total runtime: **~30 seconds** (or ~5 minutes on first run while sentence-transformers downloads the model).

Expected output:
- `data/processed/01_parsed.parquet` through `04_classified.parquet` (per-stage outputs)
- `data/processed/05_aggregated/` (per-customer, per-month, convergent-gaps tables)
- `outputs/charts/` (7 PNG charts)
- `outputs/tables/` (3 CSV tables)
- A summary printed to the terminal showing top customers by churn risk

## Build the slide deck

```bash
python3 scripts/build_slide_deck.py    # generates outputs/slide_deck.html
python3 scripts/html_to_pdf.py        # converts to outputs/slide_deck.pdf
```

The HTML version is self-contained (490KB, all charts embedded as base64). The PDF version is 976KB and is what you'd submit.

## Open the slide deck

```bash
# HTML (interactive, scrollable)
open outputs/slide_deck.html

# PDF (read-only, presentation-ready)
open outputs/slide_deck.pdf
```

## Inspect the stage outputs

```bash
# Each stage's output is a Parquet file
python3 -c "
import pandas as pd
df = pd.read_parquet('data/processed/05_aggregated/per_customer.parquet')
print(df[['customer_name', 'churn_risk_score', 'risk_tier', 'n_churn_signals']].head(10))
"
```

Or use any tool that reads Parquet (DuckDB CLI, VS Code extensions, etc.)

## Test the LLM alone

```bash
python3 pipeline/_llm.py
```

Should print:
```
LLM key status: sk-c...xyz4  (125 chars)
LLM base URL:   https://api.minimax.io/v1
LLM model:      MiniMax-Text-01

LLM response: 'OK'
```

If it prints "LLM not configured", your .env file isn't being read — check the path or env var names.

## What goes wrong (and how to fix it)

### `pydantic-core` import error

```
SystemError: The installed pydantic-core version (2.47.0) is incompatible...
```

Fix: `pip install pydantic-core==2.41.5`

### LLM call returns 401

```
Error code: 401 - invalid api key
```

Fix: check your .env has the right key AND the right base URL (`https://api.minimax.io/v1` for MiniMax, NOT `https://api.minimax.chat/v1` which is a different service).

### `sentence-transformers` model download fails

If you're behind a firewall or have slow internet, the first Stage 3 run might fail when downloading `all-MiniLM-L6-v2`. Fix: pre-download with `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"`.

### Charts look weird / overlapping labels

The matplotlib defaults are tuned for 1600x900. If you have a small display, increase the DPI in `pipeline/06_surface.py` (`plt.rcParams["figure.dpi"] = 100` → `150`).

### "Permission denied" when writing .env

Your auto-classifier may block direct writes to `.env` paths. Use `sed -i.bak 's|old|new|' .env` to update via shell, or open in an editor.

## File map

| Path | What it is |
|---|---|
| `pipeline/01_parse.py` through `06_surface.py` | The 6 stages of the pipeline |
| `pipeline/_llm.py` | LLM client (with graceful fallback) |
| `scripts/run_all.sh` | Runs the full pipeline |
| `scripts/build_slide_deck.py` | Generates the HTML slide deck |
| `scripts/html_to_pdf.py` | Converts HTML to PDF via Playwright |
| `data/processed/` | Per-stage outputs (Parquet files) |
| `outputs/charts/` | 7 PNG charts |
| `outputs/tables/` | 3 CSV tables |
| `outputs/slide_deck.html` | Self-contained HTML slide deck |
| `outputs/slide_deck.pdf` | PDF version of the slide deck |
| `README.md` | Project overview |
| `INTERVIEW_PREP.md` | Your private interview notes (encrypted via git-crypt) |
| `VIDEO_SCRIPT.md` | The video demo script |
| `docs/architecture.md` | Stage-by-stage architecture doc |

## How long does each step take?

| Step | First run | Subsequent runs |
|---|---|---|
| `pip install -r requirements.txt` | ~3 min | ~30 sec |
| Stage 1 (parse) | ~1 sec | ~1 sec |
| Stage 2 (enrich) | ~1 sec | ~1 sec |
| Stage 3 (extract) | ~2 min (model download) | ~5 sec |
| Stage 4 (classify) | ~1 sec | ~1 sec |
| Stage 5 (aggregate) | ~1 sec | ~1 sec |
| Stage 6 (surface) | ~5 sec | ~5 sec |
| Build slide deck | ~1 sec | ~1 sec |
| Convert to PDF | ~3 sec | ~3 sec |
| **Total** | **~5-7 min** | **~30 sec** |

The slow part on first run is the sentence-transformers model download (~80MB). After that, it's cached and runs in seconds.