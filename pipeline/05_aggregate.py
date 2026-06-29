"""
Stage 5: AGGREGATE
==================

What this does:
    Aggregates per-call signals into per-customer, per-month, and per-insight
    views. Computes the churn_risk_score formula.

Input:
    data/processed/04_classified.parquet

Output:
    data/processed/05_aggregated/
        per_customer.parquet      — one row per customer with churn risk score
        per_month.parquet         — sentiment trend by call type and month
        convergent_gaps.parquet   — feature gaps clustered by call-side
        per_call_pivot.parquet    — full call-level table for ad-hoc queries

Design decisions:
    - churn_risk_score is a weighted sum of: urgent call count, churn signal
      count, competitor mentions, sentiment trend, recent negative interaction.
      All terms are 0-25, capped at 100. Easy to defend in Q&A.
    - per_month aggregation is the Insight 2 chart (sentiment recovery).
    - convergent_gaps groups feature gaps by their caller_side tag — this is
      how we find customer + engineer mentions of the same gap.
    - We do NOT use unsupervised clustering for convergent gaps (yet). With
      51 gap mentions and short text snippets, embedding-based clustering
      would be noisy. Instead we aggregate by gap topic terms in Stage 6.

Cost: $0 (pure pandas)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "processed" / "04_classified.parquet"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed" / "05_aggregated"


def _safe_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        return list(value)
    except TypeError:
        return []


# ---------------------------------------------------------------------------
# Per-customer rollup
# ---------------------------------------------------------------------------

def per_customer_rollup(df: pd.DataFrame) -> pd.DataFrame:
    """One row per customer with churn risk score.

    The score is a defensible weighted sum, not magic. Each term is
    documented so it can be explained in Q&A.
    """
    # Restrict to customer-facing calls
    cust = df[df["call_type"].isin(["support", "external"])].copy()
    cust["customer_key"] = cust["customer_domain"].fillna(cust["customer_name"])

    # Sentiment trend: avg of last 30 days minus avg of first 30 days
    cust["start_dt"] = pd.to_datetime(cust["start_time"], errors="coerce")

    rows = []
    for key, grp in cust.groupby("customer_key"):
        if pd.isna(key) or key == "":
            continue
        grp_sorted = grp.sort_values("start_dt")

        # Sentiment trend
        if len(grp_sorted) >= 2:
            mid = grp_sorted["start_dt"].iloc[len(grp_sorted) // 2]
            early = grp_sorted[grp_sorted["start_dt"] < mid]["pre_score"].mean()
            late = grp_sorted[grp_sorted["start_dt"] >= mid]["pre_score"].mean()
            if pd.isna(early) or pd.isna(late):
                sentiment_trend = 0.0
            else:
                sentiment_trend = late - early
        else:
            sentiment_trend = 0.0

        # Last call date and last sentiment
        last_row = grp_sorted.iloc[-1]
        last_date = last_row["start_dt"]
        last_score = last_row.get("pre_score", 3.0) or 3.0
        days_since_last = (pd.Timestamp.utcnow().tz_localize(None) - last_date.tz_localize(None)).days if pd.notna(last_date) else 999

        # Aggregates
        n_calls = len(grp)
        n_urgent = int(grp["is_urgent_title"].sum())
        n_churn_signals = int(grp["n_churn_signals"].sum())
        n_competitor_mentions = int(grp["n_competitor_mentions"].sum())
        n_comms_gap = int(grp["n_comms_gap_phrases"].sum())
        avg_sentiment = float(grp["pre_score"].mean()) if not grp["pre_score"].isna().all() else 3.0

        # Churn risk score — the formula
        score = 0
        score += 25 if n_urgent > 0 else 0
        score += min(45, 15 * n_churn_signals)  # cap at 45
        score += 20 if n_competitor_mentions > 0 else 0
        score += 10 if sentiment_trend < -0.5 else 0
        score += 10 if (days_since_last <= 14 and last_score < 2.5) else 0
        score = min(100, score)

        # Risk tier
        if score >= 60:
            risk_tier = "HIGH"
        elif score >= 30:
            risk_tier = "MEDIUM"
        else:
            risk_tier = "LOW"

        # Sample churn quote (most recent with churn signals)
        churn_quotes = []
        for _, r in grp_sorted.iterrows():
            for sig in _safe_list(r.get("churn_signals")):
                if isinstance(sig, dict) and sig.get("quote"):
                    churn_quotes.append(sig["quote"])
        sample_quote = churn_quotes[0] if churn_quotes else ""

        rows.append({
            "customer": key,
            "customer_name": grp["customer_name"].dropna().iloc[0] if not grp["customer_name"].dropna().empty else key,
            "n_calls": n_calls,
            "first_call": grp_sorted["start_time"].iloc[0],
            "last_call": grp_sorted["start_time"].iloc[-1],
            "n_urgent_calls": n_urgent,
            "n_churn_signals": n_churn_signals,
            "n_competitor_mentions": n_competitor_mentions,
            "n_comms_gap_phrases": n_comms_gap,
            "avg_sentiment": round(avg_sentiment, 2),
            "sentiment_trend": round(sentiment_trend, 2),
            "last_sentiment": round(last_score, 2),
            "days_since_last": days_since_last,
            "churn_risk_score": score,
            "risk_tier": risk_tier,
            "sample_churn_quote": sample_quote[:200],
        })

    return pd.DataFrame(rows).sort_values("churn_risk_score", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Per-month sentiment trend
# ---------------------------------------------------------------------------

def per_month_rollup(df: pd.DataFrame) -> pd.DataFrame:
    """Sentiment by call_type and month for the Insight 2 chart."""
    df = df.copy()
    df["start_dt"] = pd.to_datetime(df["start_time"], errors="coerce")
    df["month"] = df["start_dt"].dt.to_period("M").astype(str)

    out = (df.groupby(["month", "call_type"])
             .agg(avg_sentiment=("pre_score", "mean"),
                  n_calls=("call_id", "count"),
                  avg_urgency=("urgency_score", "mean"))
             .reset_index()
             .sort_values(["month", "call_type"]))
    out["avg_sentiment"] = out["avg_sentiment"].round(2)
    out["avg_urgency"] = out["avg_urgency"].round(2)
    return out


# ---------------------------------------------------------------------------
# Convergent gaps view
# ---------------------------------------------------------------------------

def convergent_gaps_rollup(df: pd.DataFrame) -> pd.DataFrame:
    """Group feature gaps by topic, separating customer-facing vs internal.

    For each gap topic (extracted via simple keyword clustering):
      - count of customer-facing mentions
      - count of internal mentions
      - whether it's 'convergent' (both sides mentioned it)
      - sample quotes from each side

    This is the data behind Insight 3 (convergent feature gaps).
    """
    rows = []
    for _, r in df.iterrows():
        gaps = _safe_list(r.get("feature_gaps"))
        for g in gaps:
            if isinstance(g, dict):
                rows.append({
                    "call_id": r["call_id"],
                    "title": r.get("title"),
                    "call_type": r.get("call_type"),
                    "caller_side": g.get("caller_side"),
                    "quote": g.get("quote", "")[:300],
                    "speaker": g.get("speaker"),
                })

    if not rows:
        return pd.DataFrame()

    gaps_df = pd.DataFrame(rows)
    if gaps_df.empty:
        return gaps_df

    # Simple keyword clustering: pull a few key terms from the quote
    def extract_keywords(quote: str) -> str:
        """Extract 1-3 key terms from a feature_gap quote.

        Why simple keyword extraction (not embeddings): we have only 51 gaps.
        Embedding-based clustering on 51 short snippets is noisy. Keyword
        overlap is more interpretable for the panel.
        """
        if not isinstance(quote, str):
            return ""
        ql = quote.lower()
        keys = []
        # Products
        for p in ["detect", "comply", "identity", "protect", "backup", "logvault", "cloudprime"]:
            if p in ql:
                keys.append(p)
        # Gap themes — broad list to catch the convergent signals
        themes = [
            "pipeline", "pipeline health", "pipeline alert", "heartbeat", "ingestion",
            "alert", "alerts", "false positive", "alert fatigue", "alert noise",
            "restore", "granular restore", "backup", "restore wizard",
            "mfa", "sso", "scim", "ldap", "saml", "certificate", "provisioning",
            "rate limit", "api rate", "throttle",
            "audit", "compliance", "report", "reporting", "framework",
            "hipaa", "soc 2", "iso 27001", "pci", "cmdc", "gdpr",
            "dashboard", "visibility", "monitoring", "unified",
            "seats", "license", "billing", "overage",
            "self-service", "on-demand", "automation",
            "role inheritance", "session timeout", "nested role",
            "false positive", "true positive",
            "customer-facing", "internal",
        ]
        for term in themes:
            if term in ql:
                # Normalize to canonical form
                canon = term.replace(" ", "_")
                keys.append(canon)
        # Deduplicate while preserving order
        seen = set()
        ordered = []
        for k in keys:
            if k not in seen:
                seen.add(k)
                ordered.append(k)
        # Only return up to 2 most specific keys (avoid over-broad)
        return "+".join(ordered[:2]) if ordered else "other"

    gaps_df["keywords"] = gaps_df["quote"].apply(extract_keywords)
    grouped = (gaps_df.groupby("keywords")
                     .agg(n_total=("call_id", "count"),
                          n_customer_facing=("caller_side", lambda s: (s == "customer_facing").sum()),
                          n_internal=("caller_side", lambda s: (s == "internal").sum()),
                          sample_quotes=("quote", lambda s: list(s.head(3))))
                     .reset_index()
                     .sort_values("n_total", ascending=False))

    grouped["is_convergent"] = (grouped["n_customer_facing"] > 0) & (grouped["n_internal"] > 0)
    return grouped.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    if not INPUT_FILE.exists():
        print(f"ERROR: input not found. Run pipeline/04_classify.py first.", file=sys.stderr)
        return 1

    df = pd.read_parquet(INPUT_FILE)
    logger.info(f"Loaded {len(df)} calls")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 5a: per-customer rollup
    pc = per_customer_rollup(df)
    pc.to_parquet(OUTPUT_DIR / "per_customer.parquet", index=False)
    print(f"\n✓ Per-customer rollup: {len(pc)} customers → {OUTPUT_DIR / 'per_customer.parquet'}")
    print(f"  Risk tier distribution:")
    print(pc["risk_tier"].value_counts().to_string())

    # 5b: per-month sentiment
    pm = per_month_rollup(df)
    pm.to_parquet(OUTPUT_DIR / "per_month.parquet", index=False)
    print(f"\n✓ Per-month rollup: {len(pm)} rows → {OUTPUT_DIR / 'per_month.parquet'}")

    # 5c: convergent gaps
    cg = convergent_gaps_rollup(df)
    cg.to_parquet(OUTPUT_DIR / "convergent_gaps.parquet", index=False)
    print(f"\n✓ Convergent gaps: {len(cg)} topics → {OUTPUT_DIR / 'convergent_gaps.parquet'}")
    if not cg.empty:
        n_conv = int(cg["is_convergent"].sum())
        print(f"  Convergent topics (both customer + engineer mentioned): {n_conv}")
        if n_conv > 0:
            print("\n  Top convergent gaps:")
            for _, r in cg[cg["is_convergent"]].head(8).iterrows():
                print(f"    [{r['n_customer_facing']:2}cust + {r['n_internal']:2}int] {r['keywords']:35} (n={r['n_total']})")

    # 5d: per-call pivot for ad-hoc queries
    df.to_parquet(OUTPUT_DIR / "per_call_pivot.parquet", index=False)
    print(f"\n✓ Per-call pivot: {len(df)} calls → {OUTPUT_DIR / 'per_call_pivot.parquet'}")

    # Top customers by churn risk
    print("\n" + "=" * 60)
    print("TOP 10 CUSTOMERS BY CHURN RISK SCORE")
    print("=" * 60)
    top = pc.head(10)[["customer_name", "n_calls", "n_churn_signals", "n_competitor_mentions", "avg_sentiment", "churn_risk_score", "risk_tier", "sample_churn_quote"]]
    for _, r in top.iterrows():
        print(f"\n[{r['risk_tier']:6}] {r['customer_name']:35} | risk={r['churn_risk_score']:3} | calls={r['n_calls']}")
        print(f"        churn signals: {r['n_churn_signals']} | competitor mentions: {r['n_competitor_mentions']} | avg sentiment: {r['avg_sentiment']}")
        if r['sample_churn_quote']:
            print(f"        → \"{r['sample_churn_quote'][:140]}...\"")

    return 0


if __name__ == "__main__":
    sys.exit(main())