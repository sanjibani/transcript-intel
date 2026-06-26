#!/bin/bash
# Run the full pipeline end-to-end.
# Stages 1-4 are deterministic. Stage 3 will use LLM only if env vars are set.
set -e
cd "$(dirname "$0")/.."

echo "============================================================"
echo "  Transcript Intelligence Pipeline — full run"
echo "============================================================"

echo ""
echo "[1/6] Parse — walking 100 transcript folders..."
python3 pipeline/01_parse.py | tail -5

echo ""
echo "[2/6] Enrich — adding business tags..."
python3 pipeline/02_enrich.py | tail -10

echo ""
echo "[3/6] Extract — competitor mentions, comms-gap, embeddings..."
python3 pipeline/03_extract.py 2>&1 | grep -E "^(✓|  )" | tail -20

echo ""
echo "[4/6] Classify — churn signals, feature gaps..."
python3 pipeline/04_classify.py 2>&1 | grep -E "^(✓|  )" | tail -20

echo ""
echo "[5/6] Aggregate — per-customer, per-month, convergent gaps..."
python3 pipeline/05_aggregate.py 2>&1 | grep -E "^(✓|  )" | tail -20

echo ""
echo "[6/6] Surface — charts and tables..."
python3 pipeline/06_surface.py 2>&1 | grep -E "^(✓|  )" | tail -10

echo ""
echo "============================================================"
echo "  Done. Outputs:"
echo "    data/processed/   — intermediate stage outputs"
echo "    outputs/charts/   — 7 PNG charts"
echo "    outputs/tables/   — 3 CSV tables"
echo "============================================================"