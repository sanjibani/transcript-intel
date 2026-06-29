"""
Stage 3: EXTRACT
================

What this does:
    Extracts structured signals from each transcript:
    - Competitor mentions (rules only — Insight 1)
    - Comms-gap phrases (rules + selective LLM — Insight 2)
    - Per-call embedding (sentence-transformers — Insight 3)
    - Per-call signal counts (churn, feature gaps, action items)

Input:
    data/processed/02_enriched.parquet

Output:
    data/processed/03_extracted.parquet
        All Stage 2 columns + extraction columns.

Design decisions (for interview prep):
    - Competitor mentions: pure rules. The list is known (SentinelShield,
      CyberNova, VaultEdge). Regex with negation check.
    - Comms-gap phrases: regex first (~80% recall), LLM only on uncertain
      cases (negative-sentiment calls where regex missed).
    - Embeddings: sentence-transformers, 384-dim, L2-normalized.
    - Signal counts: from pre-computed summary.json (we use them as
      reference labels to evaluate against, not as ground truth to copy).

Cost: ~$0.001-0.005 per call for LLM validation. ~$0.10 total at 100 calls.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from _llm import llm_call, llm_available

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "processed" / "02_enriched.parquet"
DATASET_ROOT = Path(os.environ.get("DATASET_ROOT", "/path/to/interview-assignment/dataset"))
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "processed" / "03_extracted.parquet"

# Known competitors in the data (from exploration)
COMPETITORS = ["SentinelShield", "CyberNova", "VaultEdge"]

# Comms-gap patterns (regex) — case-insensitive
COMMS_GAP_PATTERNS = [
    r"\bno notification\b",
    r"\bdidn'?t (?:notify|reach out|tell|hear|contact|alert)\b",
    r"\bno proactive\b",
    r"\bproactive(?:ly)?\b",
    r"\bnever (?:heard|got a response|got any update)\b",
    r"\bno (?:update|response|communication|outreach|status)\b",
    r"\bcommunication (?:gap|failure|breakdown|issue)\b",
    r"\bradio silent\b",
    r"\bflying blind\b",
    r"\bblind spot\b",
    r"\bmissed (?:alert|notification)\b",
    r"\b(?:had|spent) .* (?:chasing|debugging|investigating) (?:it )?on (?:our|my) (?:own|side|end)\b",
    r"\bsilent(?:ly)?\b",
    r"\bout of (?:the )?loop\b",
    r"\bno (?:heads[- ]up|heads up)\b",
    r"\bwithout (?:any )?(?:warning|notice|warning)\b",
]


# ---------------------------------------------------------------------------
# Per-call extraction helpers
# ---------------------------------------------------------------------------

def load_transcript_text(call_id: str) -> str:
    """Load the full transcript text for a single call."""
    p = DATASET_ROOT / call_id / "transcript.json"
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return " ".join(u.get("sentence", "") for u in data.get("data", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return ""


def find_competitor_mentions(text: str) -> list[dict]:
    """Find all competitor mentions in text with context.

    Returns: list of {competitor, quote, start, end}.
    Negation check: skip mentions preceded by "NOT", "n't", "no".
    """
    mentions = []
    if not text:
        return mentions

    for comp in COMPETITORS:
        # Word-boundary regex
        for m in re.finditer(rf"\b{re.escape(comp)}\b", text):
            start = max(0, m.start() - 60)
            end = min(len(text), m.end() + 60)
            context = text[start:end]

            # Negation check — skip if preceded by "not", "n't", "no"
            preceding = text[max(0, m.start()-15):m.start()].lower()
            if any(neg in preceding for neg in ["not ", "n't ", "no ", "never ", "without "]):
                # Allow if the negation is far away (>15 chars)
                if any(neg in preceding[-10:] for neg in ["not ", "n't ", "no "]):
                    continue

            mentions.append({
                "competitor": comp,
                "quote": context.strip(),
                "position": m.start(),
            })
    return mentions


def find_comms_gap_phrases_regex(text: str) -> list[dict]:
    """Find communication-gap phrases via regex."""
    phrases = []
    if not text:
        return phrases
    for pattern in COMMS_GAP_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            start = max(0, m.start() - 50)
            end = min(len(text), m.end() + 100)
            phrases.append({
                "phrase": m.group(0),
                "context": text[start:end].strip(),
                "method": "regex",
            })
    return phrases


COMMS_GAP_LLM_PROMPT = """You are analyzing a customer-support or account-management call transcript.

Does this customer explicitly complain about Aegis's COMMUNICATION or PROACTIVE OUTREACH?
Specifically: lack of notification, no proactive update, no heads-up, slow response, or being left in the dark?

Answer ONLY in this exact JSON format:
{{"answer": "YES" or "NO", "quote": "<the most relevant sentence, or empty string>"}}

Transcript:
{transcript}
"""


def find_comms_gap_phrases_llm(text: str) -> list[dict]:
    """Find communication-gap phrases via LLM (used only on uncertain cases)."""
    if not text or not llm_available():
        return []
    # Truncate to first 4000 chars to save tokens
    truncated = text[:4000]
    prompt = COMMS_GAP_LLM_PROMPT.format(transcript=truncated)
    response = llm_call(prompt, max_tokens=300)
    if not response:
        return []
    try:
        # Parse JSON from response (handle markdown code fences)
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        result = json.loads(cleaned)
        if result.get("answer", "").upper() == "YES" and result.get("quote"):
            return [{
                "phrase": result["quote"][:80],
                "context": result["quote"],
                "method": "llm",
            }]
    except (json.JSONDecodeError, KeyError):
        logger.debug(f"LLM response not parseable: {response[:100]}")
    return []


def compute_embedding(text: str, model) -> np.ndarray | None:
    """Compute a 384-dim embedding for the call text."""
    if not text or model is None:
        return None
    # Truncate to ~8000 chars to stay well under model max length
    truncated = text[:8000]
    try:
        emb = model.encode(truncated, normalize_embeddings=True, show_progress_bar=False)
        return emb
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Embedding failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    if not INPUT_FILE.exists():
        print(f"ERROR: input not found. Run pipeline/02_enrich.py first.", file=sys.stderr)
        return 1

    df = pd.read_parquet(INPUT_FILE)
    logger.info(f"Loaded {len(df)} calls")

    # Load sentence-transformers model (CPU)
    logger.info("Loading sentence-transformers model (this takes ~30s on first run)...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to load sentence-transformers: {exc}")
        model = None

    # Load sentence-transformers embedding for stage 3c
    # Load LLM availability flag
    use_llm = llm_available()
    logger.info(f"LLM available: {use_llm}")

    # Per-row extraction
    competitor_lists = []
    comms_gap_lists = []
    embeddings = []
    n_competitors = []
    n_comms_gaps = []

    for i, row in df.iterrows():
        call_id = row["call_id"]
        text = load_transcript_text(call_id)

        # 3a: competitor mentions
        comps = find_competitor_mentions(text)
        competitor_lists.append(comps)
        n_competitors.append(len(comps))

        # 3b: comms-gap phrases (regex first, then LLM only on uncertain cases)
        regex_phrases = find_comms_gap_phrases_regex(text)
        # Only fire LLM on calls where regex missed but sentiment suggests gap
        if not regex_phrases and use_llm and row.get("pre_score", 3.0) < 3.0:
            llm_phrases = find_comms_gap_phrases_llm(text)
        else:
            llm_phrases = []
        all_phrases = regex_phrases + llm_phrases
        comms_gap_lists.append(all_phrases)
        n_comms_gaps.append(len(all_phrases))

        # 3c: embedding
        emb = compute_embedding(text, model) if model else None
        embeddings.append(emb)

        if (i + 1) % 20 == 0:
            logger.info(f"  Processed {i+1}/{len(df)} calls...")

    # Add to DataFrame
    df["competitor_mentions"] = competitor_lists
    df["n_competitor_mentions"] = n_competitors
    df["comms_gap_phrases"] = comms_gap_lists
    df["n_comms_gap_phrases"] = n_comms_gaps
    df["embedding"] = embeddings

    # Output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_FILE, index=False)
    logger.info(f"Saved to {OUTPUT_FILE}")

    # Summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    total_competitors = sum(n_competitors)
    total_comms_gaps = sum(n_comms_gaps)
    calls_with_competitor = sum(1 for n in n_competitors if n > 0)
    calls_with_comms_gap = sum(1 for n in n_comms_gaps if n > 0)

    print(f"\nCompetitor mentions:")
    print(f"  Total mentions:    {total_competitors}")
    print(f"  Calls mentioning:  {calls_with_competitor} of {len(df)}")
    from collections import Counter
    comp_counter = Counter()
    for lst in competitor_lists:
        for m in lst:
            comp_counter[m["competitor"]] += 1
    for c, n in comp_counter.most_common():
        print(f"    {c}: {n} mentions")

    print(f"\nComms-gap phrases:")
    print(f"  Total phrases:     {total_comms_gaps}")
    print(f"  Calls mentioning:  {calls_with_comms_gap} of {len(df)}")
    regex_count = sum(1 for lst in comms_gap_lists for p in lst if p["method"] == "regex")
    llm_count = sum(1 for lst in comms_gap_lists for p in lst if p["method"] == "llm")
    print(f"    regex matches:   {regex_count}")
    print(f"    LLM-only matches:{llm_count}")
    if not use_llm:
        print(f"    (LLM not configured — some borderline cases missed)")

    print(f"\nEmbeddings computed:")
    n_with_emb = sum(1 for e in embeddings if e is not None)
    print(f"  {n_with_emb} of {len(df)} calls have embeddings")
    if model is None:
        print(f"  (sentence-transformers unavailable — embeddings skipped)")

    return 0


if __name__ == "__main__":
    sys.exit(main())