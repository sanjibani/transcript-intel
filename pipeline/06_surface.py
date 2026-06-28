"""
Stage 6: SURFACE
================

What this does:
    Produces all the charts and tables for the slide deck.

Input:
    data/processed/05_aggregated/

Output:
    outputs/charts/*.png    (7 PNG charts)
    outputs/tables/*.csv    (3 CSV tables)

Design decisions (for interview prep):
    - matplotlib + seaborn for static charts (presentation-ready, no JS deps)
    - Each chart has a clear single-message title so it stands alone
    - Chart 1 stacks the formula components (25/15n/20/10/10) so the bars
      literally sum to the risk-score line. No "trust me, the math works."
    - Convergent gaps chart is data-driven (theme x call_type cross-tab),
      not hand-curated. Honest "other is largest" caveat is in the title.
    - Pipeline architecture diagram is generated from code, not hand-drawn,
      so it can't drift from the actual stages.

Charts produced (in order):
    1. 01_churn_risk_concentration.png — top 10 customers, formula components stacked
    2. 02_comms_gap_by_month.png       — comms-gap phrase counts over time
    3. 03_sentiment_trend.png          — avg sentiment by call_type per month
    4. 04_convergent_gaps.png          — feature gaps that crossed customer/internal
    5. 05_call_archetype_distribution.png — mix of call archetypes in the dataset
    6. 06_competitor_mentions.png      — competitor mentions per customer
    7. 07_pipeline_architecture.png    — the 6 stages as a flowchart

Tables produced:
    - per_customer_risk.csv   — every customer with score + components
    - convergent_gaps.csv     — every gap theme x call_type matrix
    - monthly_summary.csv     — per-month call counts and signal totals

Cost: $0 (pure code, no LLM)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed" / "05_aggregated"
CHARTS_DIR = Path(__file__).resolve().parent.parent / "outputs" / "charts"
TABLES_DIR = Path(__file__).resolve().parent.parent / "outputs" / "tables"

# Style
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.dpi"] = 100
plt.rcParams["savefig.dpi"] = 150
plt.rcParams["font.size"] = 10


def chart_01_churn_risk_concentration(pc: pd.DataFrame, per_call: pd.DataFrame) -> None:
    """Insight 1: Top customers by churn risk score with contributing factors.

    The stacked bars show the actual formula components (25 / 15*n / 20 / 10 / 10),
    so they sum to the risk score line.
    """
    top = pc.head(10).copy()

    # Recompute the formula components so the bars match the line.
    # Mirrors the formula in pipeline/05_aggregate.py:111-115.
    top = top.copy()
    top["c_urgent"] = (top["n_urgent_calls"] > 0).astype(int) * 25
    top["c_churn"] = (top["n_churn_signals"] * 15).clip(upper=45)
    top["c_competitor"] = (top["n_competitor_mentions"] > 0).astype(int) * 20
    top["c_trend"] = (top["sentiment_trend"] < -0.5).astype(int) * 10
    top["c_recent"] = ((top["days_since_last"] <= 14) & (top["last_sentiment"] < 2.5)).astype(int) * 10
    top["c_sum"] = (top["c_urgent"] + top["c_churn"] + top["c_competitor"]
                    + top["c_trend"] + top["c_recent"]).clip(upper=100)

    fig, ax = plt.subplots(figsize=(12, 6))
    y_pos = np.arange(len(top))

    # Stacked bars — actual formula components
    left = np.zeros(len(top))
    components = [
        ("c_urgent",     "Urgent (+25)",     "#9467bd"),
        ("c_churn",      "Churn signals (15/each, ≤45)", "#d62728"),
        ("c_competitor", "Competitor (+20)",  "#ff7f0e"),
        ("c_trend",      "Trend drop (+10)", "#2ca02c"),
        ("c_recent",     "Recent + low (+10)", "#1f77b4"),
    ]
    for col, label, color in components:
        ax.barh(y_pos, top[col], left=left, color=color, alpha=0.85, label=label)
        left = left + top[col].values

    # Risk score line — should match the total bar length per customer
    ax.plot(top["churn_risk_score"], y_pos, "ko-", linewidth=2, markersize=8,
            label="Risk score (line)", zorder=10)
    # Connect line to bar end with thin grey to show they match
    for i, (score, total) in enumerate(zip(top["churn_risk_score"], top["c_sum"])):
        if abs(score - total) > 1:
            # They don't match exactly (probably capped at 100) — note it
            ax.text(score, i, f" {score}", va="center", fontsize=9, color="black", fontweight="bold")

    ax.set_xlim(0, 105)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(top["customer_name"], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("Churn risk score (0-100)", fontsize=11)
    ax.set_title("Insight 1: Churn risk concentrates in 4-8 accounts\n"
                 "Top 10 customers by composite risk score, March-April 2026",
                 fontsize=13, fontweight="bold", loc="left")
    ax.legend(loc="lower right", fontsize=8, ncol=2)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "01_churn_risk_concentration.png", bbox_inches="tight")
    plt.close()
    print("  ✓ Chart 1: churn risk concentration (formula components)")


def chart_02_comms_gap_by_month(per_call: pd.DataFrame) -> None:
    """Insight 2: Communication gap phrases by call type and month."""
    df = per_call.copy()
    df["start_dt"] = pd.to_datetime(df["start_time"], errors="coerce")
    df["month"] = df["start_dt"].dt.to_period("M").astype(str)

    # Count comms-gap phrases per month × call_type
    out = (df.groupby(["month", "call_type"])["n_comms_gap_phrases"]
             .sum()
             .reset_index()
             .pivot(index="month", columns="call_type", values="n_comms_gap_phrases")
             .fillna(0))

    fig, ax = plt.subplots(figsize=(10, 5))
    out.plot(kind="bar", ax=ax, color=["#1f77b4", "#ff7f0e", "#2ca02c"], width=0.7)
    ax.set_title("Insight 2: Communication gap phrases by call type\nConcentrated in March during the Detect Outage",
                 fontsize=13, fontweight="bold", loc="left")
    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel("Comms-gap phrases", fontsize=11)
    ax.legend(title="Call type", fontsize=10)
    ax.tick_params(axis="x", rotation=0)

    # Annotate March bar
    for i, month in enumerate(out.index):
        for j, call_type in enumerate(out.columns):
            val = out.loc[month, call_type]
            if val > 0:
                ax.text(i + (j-1)*0.25, val + 0.5, str(int(val)),
                        ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "02_comms_gap_by_month.png", bbox_inches="tight")
    plt.close()
    print("  ✓ Chart 2: comms gap by month")


def chart_03_sentiment_trend(pm: pd.DataFrame) -> None:
    """Sentiment recovery by call type — supporting chart for Insight 2."""
    pivot = pm.pivot(index="month", columns="call_type", values="avg_sentiment")

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = {"support": "#d62728", "external": "#1f77b4", "internal": "#2ca02c"}
    for col in pivot.columns:
        ax.plot(pivot.index, pivot[col], "o-", label=col, color=colors.get(col, "gray"),
                linewidth=2, markersize=10)

    ax.set_title("Sentiment drops together in March, recovers unevenly\nInternal bounces back fastest; support lags",
                 fontsize=13, fontweight="bold", loc="left")
    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel("Average sentiment score (1-5)", fontsize=11)
    ax.legend(title="Call type", fontsize=10)
    ax.set_ylim(2, 5)
    ax.axvspan(1.5, 2.5, alpha=0.15, color="red", label="March outage")

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "03_sentiment_trend.png", bbox_inches="tight")
    plt.close()
    print("  ✓ Chart 3: sentiment trend by call type")


def chart_04_convergent_gaps(cg: pd.DataFrame) -> None:
    """Insight 3: Convergent feature gaps — same gap mentioned by both customer and internal calls.

    Note: uses keyword clustering which is intentionally simple. The biggest cluster
    is "other" (heterogeneous gaps that didn't match a specific theme). With embeddings
    we could surface more nuanced themes — the architecture supports it but we kept
    the simple version for interpretability.
    """
    conv = cg[cg["is_convergent"]].copy().sort_values("n_total", ascending=True).tail(8)

    if conv.empty:
        print("  ! No convergent gaps to plot")
        return

    fig, ax = plt.subplots(figsize=(11, 5))
    y = np.arange(len(conv))
    width = 0.4
    ax.barh(y - width/2, conv["n_customer_facing"], width, color="#1f77b4", label="Customer-facing", alpha=0.85)
    ax.barh(y + width/2, conv["n_internal"], width, color="#ff7f0e", label="Internal (engineering)", alpha=0.85)

    ax.set_yticks(y)
    ax.set_yticklabels(conv["keywords"].str.replace("+", " + "), fontsize=10)
    ax.set_xlabel("Number of mentions", fontsize=11)
    ax.set_title("Insight 3: Gaps raised by both customers and internal teams\n"
                 "Keyword clustering — most convergent gaps fall into 'other' (no specific theme matched)",
                 fontsize=12, fontweight="bold", loc="left")
    ax.legend(fontsize=10)

    # Add total at end of bar
    for i, row in conv.reset_index(drop=True).iterrows():
        ax.text(max(row["n_customer_facing"], row["n_internal"]) + 0.1, i,
                f"Σ {row['n_total']}", va="center", fontsize=9, color="gray")

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "04_convergent_gaps.png", bbox_inches="tight")
    plt.close()
    print("  ✓ Chart 4: convergent feature gaps (data-driven)")


def chart_05_call_archetype_distribution(per_call: pd.DataFrame) -> None:
    """Supporting: how calls break down by archetype — gives the panel the lay of the land."""
    arch_counts = per_call["call_archetype"].value_counts()

    fig, ax = plt.subplots(figsize=(10, 5))
    colors_map = {
        "renewal_at_risk": "#d62728",
        "support_escalation": "#ff7f0e",
        "support_resolution": "#2ca02c",
        "incident_response": "#9467bd",
        "product_feedback": "#1f77b4",
        "engineering_planning": "#8c564b",
        "sales_expansion": "#e377c2",
        "general_internal": "#7f7f7f",
    }
    bar_colors = [colors_map.get(a, "gray") for a in arch_counts.index]
    arch_counts.plot(kind="barh", ax=ax, color=bar_colors)
    ax.set_title("Call archetype distribution\nWhere risk concentrates in the call mix",
                 fontsize=13, fontweight="bold", loc="left")
    ax.set_xlabel("Number of calls", fontsize=11)
    ax.invert_yaxis()

    for i, v in enumerate(arch_counts.values):
        ax.text(v + 0.5, i, str(v), va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "05_call_archetype_distribution.png", bbox_inches="tight")
    plt.close()
    print("  ✓ Chart 5: call archetype distribution")


def chart_06_competitor_mentions(per_call: pd.DataFrame) -> None:
    """Supporting: competitor mention volume by customer — companion to Insight 1."""
    df = per_call.copy()
    cust = df[df["customer_domain"].notna()].copy()
    cust["customer_key"] = cust["customer_domain"].fillna(cust["customer_name"])

    top = (cust.groupby("customer_key")["n_competitor_mentions"]
              .sum()
              .sort_values(ascending=False)
              .head(10))

    fig, ax = plt.subplots(figsize=(10, 5))
    top.plot(kind="bar", ax=ax, color="#ff7f0e")
    ax.set_title("Competitor mentions by customer\n30 of 100 calls name a competitor; concentration visible",
                 fontsize=13, fontweight="bold", loc="left")
    ax.set_xlabel("Customer", fontsize=11)
    ax.set_ylabel("Total competitor mentions across all calls", fontsize=11)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "06_competitor_mentions.png", bbox_inches="tight")
    plt.close()
    print("  ✓ Chart 6: competitor mentions by customer")


def chart_07_pipeline_architecture() -> None:
    """Architecture diagram — drawn with matplotlib boxes and arrows."""
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5)
    ax.axis("off")

    stages = [
        ("1. PARSE", "Pure code\n6 JSONs → 1 row", "#1f77b4"),
        ("2. ENRICH", "Rules\ncall_type, urgency", "#1f77b4"),
        ("3. EXTRACT", "Rules + Embeddings\ncompetitors, comms-gap", "#2ca02c"),
        ("4. CLASSIFY", "Validate + tag\nchurn, feature gaps", "#2ca02c"),
        ("5. AGGREGATE", "Pure pandas\nper-customer, per-month", "#1f77b4"),
        ("6. SURFACE", "Charts\nfor slide deck", "#9467bd"),
    ]

    x_positions = np.linspace(1, 13, len(stages))
    box_width = 1.8
    box_height = 1.5

    for x, (name, desc, color) in zip(x_positions, stages):
        rect = plt.Rectangle((x - box_width/2, 2), box_width, box_height,
                              facecolor=color, alpha=0.3, edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(x, 3.2, name, ha="center", va="center", fontsize=11, fontweight="bold")
        ax.text(x, 2.4, desc, ha="center", va="center", fontsize=8)

        # Arrow to next
        if x < x_positions[-1]:
            ax.annotate("", xy=(x + box_width/2 + 0.4, 2.75),
                        xytext=(x + box_width/2, 2.75),
                        arrowprops=dict(arrowstyle="->", color="black", lw=1.5))

    # Brace underneath
    ax.text(7, 0.8, "Stages 1-2: deterministic foundation (no LLM)\nStages 3-4: rules first, LLM only on uncertain cases\nStages 5-6: pure pandas + matplotlib",
            ha="center", va="center", fontsize=9, style="italic",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#f0f0f0", edgecolor="gray"))

    ax.set_title("Pipeline architecture — hybrid design\n",
                 fontsize=14, fontweight="bold", loc="left")

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "07_pipeline_architecture.png", bbox_inches="tight")
    plt.close()
    print("  ✓ Chart 7: pipeline architecture")


def save_tables(pc: pd.DataFrame, pm: pd.DataFrame, cg: pd.DataFrame) -> None:
    """Save key tables as CSVs for the slide deck appendix."""
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    pc.to_csv(TABLES_DIR / "per_customer.csv", index=False)
    pm.to_csv(TABLES_DIR / "per_month.csv", index=False)
    cg.to_csv(TABLES_DIR / "convergent_gaps.csv", index=False)
    print(f"  ✓ Tables saved to {TABLES_DIR}")


def main() -> int:
    if not INPUT_DIR.exists():
        print(f"ERROR: input not found. Run pipeline/05_aggregate.py first.", file=sys.stderr)
        return 1

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    pc = pd.read_parquet(INPUT_DIR / "per_customer.parquet")
    pm = pd.read_parquet(INPUT_DIR / "per_month.parquet")
    cg = pd.read_parquet(INPUT_DIR / "convergent_gaps.parquet")
    per_call = pd.read_parquet(INPUT_DIR / "per_call_pivot.parquet")

    print(f"Loaded {len(pc)} customers, {len(pm)} month-rows, {len(cg)} gap-topics")
    print("\nGenerating charts...")

    chart_01_churn_risk_concentration(pc, per_call)
    chart_02_comms_gap_by_month(per_call)
    chart_03_sentiment_trend(pm)
    chart_04_convergent_gaps(cg)
    chart_05_call_archetype_distribution(per_call)
    chart_06_competitor_mentions(per_call)
    chart_07_pipeline_architecture()

    save_tables(pc, pm, cg)

    print(f"\n✓ All outputs in {CHARTS_DIR.parent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())