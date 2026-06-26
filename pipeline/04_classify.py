"""
Stage 4: CLASSIFY
================

What this does:
    Classifies churn signals and feature gaps per call, validating against
    the pre-computed labels in summary.json. Tags each signal with whether
    it came from our extraction or the pre-computed set, so we can measure
    agreement.

Input:
    data/processed/03_extracted.parquet

Output:
    data/processed/04_classified.parquet
        Stage 3 columns + per-call churn_signals[], feature_gaps[], and
        call_archetype.

Design decisions (for interview prep):
    - We treat pre-computed keyMoments as REFERENCE LABELS, not ground truth.
      We extract our own signals (Stage 3 + rule-based here) and compare.
    - churn_signals: union of (a) pre-computed churn_signal key moments,
      (b) any call with a competitor mention. The union is what surfaces
      churn risk; the intersection tells us where the source vendor agreed.
    - feature_gaps: same pattern. Plus we tag each gap with caller_side
      (customer_facing vs internal) — this is what feeds Insight 3.
    - call_archetype: rule-based classification using call_type + signals.
      No LLM needed — it's deterministic.

Cost: $0 (pure code, no LLM)
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "processed" / "03_extracted.parquet"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "processed" / "04_classified.parquet"


def _safe_list(value) -> list:
    """Return value as a list. Handles None, numpy arrays, and lists uniformly."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    # numpy array
    try:
        return list(value)
    except TypeError:
        return []


def classify_churn_signals(row: pd.Series) -> list[dict]:
    """Return all churn signals for this call, tagged with source.

    Sources:
      - 'precomputed': from summary.json keyMoments[type='churn_signal']
      - 'competitor_mention': from Stage 3 competitor extraction
      - 'combo_commsgap_competitor': high-signal combo (angry + shopping)

    Returns: list of {quote, source, speaker?}
    """
    signals = []

    # 1. Pre-computed
    pre_kms = _safe_list(row.get("pre_key_moments"))
    for km in pre_kms:
        if isinstance(km, dict) and km.get("type") == "churn_signal":
            signals.append({
                "quote": km.get("text", "")[:200],
                "source": "precomputed",
                "speaker": km.get("speaker"),
                "time": km.get("time"),
            })

    # 2. Competitor mention
    competitors = _safe_list(row.get("competitor_mentions"))
    if competitors:
        for c in competitors[:3]:  # cap at 3 to avoid duplication
            if isinstance(c, dict):
                signals.append({
                    "quote": c.get("quote", "")[:200],
                    "source": "competitor_mention",
                    "competitor": c.get("competitor"),
                })

    # 3. High-signal combo: comms-gap + competitor
    n_comms = int(row.get("n_comms_gap_phrases") or 0)
    n_comp = int(row.get("n_competitor_mentions") or 0)
    if n_comms >= 2 and n_comp >= 1:
        signals.append({
            "quote": "[combo: comms-gap + competitor mention in same call]",
            "source": "combo_commsgap_competitor",
        })

    return signals


def classify_feature_gaps(row: pd.Series) -> list[dict]:
    """Return feature_gap mentions, tagged with caller_side.

    caller_side is 'customer_facing' if call_type in (support, external)
    and 'internal' if call_type == 'internal'. This is what feeds Insight 3
    (convergent feature gaps).
    """
    gaps = []

    pre_kms = _safe_list(row.get("pre_key_moments"))
    call_type = row.get("call_type")
    caller_side = "customer_facing" if call_type in ("support", "external") else "internal"

    for km in pre_kms:
        if isinstance(km, dict) and km.get("type") == "feature_gap":
            gaps.append({
                "quote": km.get("text", "")[:200],
                "source": "precomputed",
                "speaker": km.get("speaker"),
                "caller_side": caller_side,
            })

    return gaps


def derive_call_archetype(row: pd.Series) -> str:
    """Rule-based call archetype classification.

    Returns one of:
      - 'renewal_at_risk'    : external call with churn signals + competitor mention
      - 'support_resolution' : support call without churn signals
      - 'support_escalation' : support call with churn signals
      - 'product_feedback'   : external call with feature_gap mentions
      - 'engineering_planning': internal call without churn signals
      - 'incident_response'  : call with high urgency_score
      - 'sales_expansion'    : external call, no churn, no gaps, positive sentiment
      - 'general_internal'   : catchall for remaining internal calls
    """
    call_type = row.get("call_type")
    urgency = row.get("urgency_score", 0)
    n_churn = len(row.get("churn_signals", []) or [])
    has_competitor = (row.get("n_competitor_mentions", 0) or 0) > 0
    n_gaps = len(row.get("feature_gaps", []) or [])
    sentiment_score = row.get("pre_score", 3.0) or 3.0

    # Incident response takes priority (urgency 3 or outage + urgency 2)
    if urgency >= 3:
        return "incident_response"
    if urgency == 2 and call_type in ("support", "external"):
        return "support_escalation" if call_type == "support" else "renewal_at_risk"

    # Renewal at risk: external with churn signals
    if call_type == "external" and (n_churn >= 1 or has_competitor):
        return "renewal_at_risk"

    # Support resolution vs escalation
    if call_type == "support":
        return "support_resolution" if n_churn == 0 else "support_escalation"

    # Product feedback: external with feature gaps
    if call_type == "external" and n_gaps >= 1:
        return "product_feedback"

    # Sales expansion: external, positive, no churn, no gaps
    if call_type == "external" and sentiment_score >= 4.0:
        return "sales_expansion"

    # Engineering / internal
    if call_type == "internal":
        return "engineering_planning"

    return "general_internal"


def main() -> int:
    if not INPUT_FILE.exists():
        print(f"ERROR: input not found. Run pipeline/03_extract.py first.", file=sys.stderr)
        return 1

    df = pd.read_parquet(INPUT_FILE)
    logger.info(f"Loaded {len(df)} calls")

    # Apply classification
    df["churn_signals"] = df.apply(classify_churn_signals, axis=1)
    df["n_churn_signals"] = df["churn_signals"].apply(len)

    df["feature_gaps"] = df.apply(classify_feature_gaps, axis=1)
    df["n_feature_gaps"] = df["feature_gaps"].apply(len)
    df["n_customer_facing_gaps"] = df["feature_gaps"].apply(
        lambda gs: sum(1 for g in (gs or []) if g.get("caller_side") == "customer_facing")
    )
    df["n_internal_gaps"] = df["feature_gaps"].apply(
        lambda gs: sum(1 for g in (gs or []) if g.get("caller_side") == "internal")
    )

    df["call_archetype"] = df.apply(derive_call_archetype, axis=1)

    # Output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_FILE, index=False)
    logger.info(f"Saved to {OUTPUT_FILE}")

    # Summary
    print("\n" + "=" * 60)
    print("CLASSIFICATION SUMMARY")
    print("=" * 60)
    print("\nChurn signals:")
    total_churn = df["n_churn_signals"].sum()
    calls_with_churn = (df["n_churn_signals"] > 0).sum()
    print(f"  Total signals:    {total_churn}")
    print(f"  Calls with ≥1:    {calls_with_churn} of {len(df)}")

    # Validate: how often do our extracted signals agree with pre-computed?
    pre_churn = df["pre_key_moments"].apply(
        lambda kms: sum(1 for km in _safe_list(kms) if isinstance(km, dict) and km.get("type") == "churn_signal")
    )
    our_churn = df["n_churn_signals"]
    pre_count = pre_churn.sum()
    our_only = ((our_churn > 0) & (pre_churn == 0)).sum()
    pre_only = ((our_churn == 0) & (pre_churn > 0)).sum()
    both = ((our_churn > 0) & (pre_churn > 0)).sum()
    print(f"\n  Pre-computed churn_signal moments: {pre_count}")
    print(f"  Calls where BOTH pre-computed AND our extraction found churn: {both}")
    print(f"  Calls where ONLY our extraction found churn: {our_only}")
    print(f"  Calls where ONLY pre-computed found churn: {pre_only}")

    print("\nFeature gaps:")
    total_gaps = df["n_feature_gaps"].sum()
    calls_with_gaps = (df["n_feature_gaps"] > 0).sum()
    print(f"  Total gaps:           {total_gaps}")
    print(f"  Calls with ≥1:        {calls_with_gaps}")
    print(f"  Customer-facing gaps: {df['n_customer_facing_gaps'].sum()}")
    print(f"  Internal gaps:        {df['n_internal_gaps'].sum()}")

    print("\nCall archetype distribution:")
    print(df["call_archetype"].value_counts().to_string())

    # Top churn-risk calls
    print("\nTop 10 calls by churn signals:")
    top = df.nlargest(10, "n_churn_signals")[["title", "call_type", "n_churn_signals", "n_competitor_mentions", "urgency_score"]]
    for _, r in top.iterrows():
        print(f"  [{r['urgency_score']}] {r['call_type']:8} | signals={r['n_churn_signals']:2} | competitors={r['n_competitor_mentions']:2} | {r['title'][:65]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())