"""
Stage 6: SURFACE
================

What this does:
    Produces all the charts and tables for the slide deck.

Input:
    data/processed/05_aggregated/

Output:
    outputs/charts/*.png
    outputs/tables/*.csv

Design decisions (for interview prep):
    - matplotlib + seaborn for static charts (presentation-ready)
    - Each chart has a clear single-message title
    - We generate 7 charts covering the 3 insights + supporting visuals
    - Tables saved as CSV for the slide-deck appendix

Cost: $0
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
    """Insight 1: Top customers by churn risk score with contributing factors."""
    top = pc.head(10).copy()

    fig, ax = plt.subplots(figsize=(12, 6))
    y_pos = np.arange(len(top))

    # Stacked bars: n_urgent, n_churn_signals, n_competitor_mentions
    p1 = ax.barh(y_pos, top["n_churn_signals"] * 5, color="#d62728", alpha=0.7, label="Churn signals × 5")
    p2 = ax.barh(y_pos, top["n_competitor_mentions"] * 5, left=top["n_churn_signals"] * 5,
                 color="#ff7f0e", alpha=0.7, label="Competitor mentions × 5")
    p3 = ax.barh(y_pos, top["n_urgent_calls"] * 25, left=(top["n_churn_signals"] + top["n_competitor_mentions"]) * 5,
                 color="#9467bd", alpha=0.7, label="Urgent calls × 25")

    # Risk score line
    ax2 = ax.twiny()
    ax2.plot(top["churn_risk_score"], y_pos, "o-", color="black", linewidth=2, markersize=8, label="Risk score")
    ax2.set_xlim(0, 100)
    ax2.set_xlabel("Churn risk score (0-100)", fontsize=11)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(top["customer_name"], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("Contribution to risk score", fontsize=11)
    ax.set_title("Insight 1: Churn risk concentrates in 4-8 accounts\nTop 10 customers by composite risk score, March-April 2026",
                 fontsize=13, fontweight="bold", loc="left")
    ax.legend(loc="lower right", fontsize=9)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "01_churn_risk_concentration.png", bbox_inches="tight")
    plt.close()
    print("  ✓ Chart 1: churn risk concentration")


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
    """Insight 3: Convergent feature gaps — customer + engineer mentions."""
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
    ax.set_title("Insight 3: Convergent feature gaps\nSame product gap raised independently by customers and engineers",
                 fontsize=13, fontweight="bold", loc="left")
    ax.legend(fontsize=10)

    # Add total at end of bar
    for i, row in conv.reset_index(drop=True).iterrows():
        ax.text(max(row["n_customer_facing"], row["n_internal"]) + 0.1, i,
                f"Σ {row['n_total']}", va="center", fontsize=9, color="gray")

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "04_convergent_gaps.png", bbox_inches="tight")
    plt.close()
    print("  ✓ Chart 4: convergent feature gaps")


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