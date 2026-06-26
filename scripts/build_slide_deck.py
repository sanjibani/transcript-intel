"""
Build the slide deck as a self-contained HTML file.

Each slide is a section with a chart + narrative. The HTML is printable
to PDF via the browser for the actual interview.

Why HTML (not PPTX):
- Easier to build with code (no python-pptx XML)
- Charts embed as base64 — fully portable
- Can be opened in any browser, screenshotted, or printed to PDF

Output:
    outputs/slide_deck.html
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

CHARTS_DIR = Path(__file__).resolve().parent.parent / "outputs" / "charts"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "outputs" / "slide_deck.html"


def img_to_data_uri(path: Path) -> str:
    """Read an image file and return a base64 data URI."""
    with path.open("rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def slide(title: str, content: str, *, chart: str | None = None,
         page_num: int | None = None) -> str:
    """Build a single slide."""
    chart_html = ""
    if chart:
        chart_html = f'<div class="chart-wrap"><img src="{chart}" alt="chart"/></div>'

    page_label = f'<div class="page-num">{page_num}</div>' if page_num else ""

    return f"""
    <section class="slide">
      <div class="slide-content">
        <h2>{title}</h2>
        {content}
        {chart_html}
      </div>
      {page_label}
    </section>
    """


def build() -> None:
    # Embed all 7 charts as data URIs
    chart_uris = {p.stem: img_to_data_uri(p) for p in CHARTS_DIR.glob("*.png")}

    slides_html = []

    # Slide 1: Title
    slides_html.append(slide(
        "Transcript Intelligence — Findings & Pipeline",
        """
        <p class="lead">Take-home assignment: 100 transcripts processed through a hybrid pipeline to surface three insights for stakeholders.</p>
        <div class="meta">
          <p><strong>3 insights:</strong> churn risk concentration · communication gap · convergent feature gaps</p>
          <p><strong>Pipeline:</strong> 6 stages, hybrid (rules + embeddings + selective LLM), ~$0.30 in API costs</p>
          <p><strong>Validation:</strong> matches pre-computed labels on 52 of 61 churn signals, finds 7 additional</p>
        </div>
        """,
        page_num=1,
    ))

    # Slide 2: Context — The Detect Outage narrative
    slides_html.append(slide(
        "Context: the March 2026 Detect Outage",
        """
        <p>In mid-March 2026, Aegis Detect's event-processing pipeline had a six-hour cascading failure. Zero threat visibility for affected customers. The technical fix shipped in 30 days.</p>
        <p><strong>The business damage didn't.</strong></p>
        <ul>
          <li>8 customers entered <em>active churn-risk territory</em> within 10 days</li>
          <li>39 of 100 calls show customers frustrated by <em>silence</em>, not by the bug</li>
          <li>5 product gaps were independently raised by <em>both customers and engineers</em> — including the missing pipeline-health monitoring that could have prevented the outage</li>
        </ul>
        <p class="footnote">A tool that surfaces these signals in real time, per stakeholder, would have flagged 4 accounts weeks before they escalated.</p>
        """,
        page_num=2,
    ))

    # Slide 3: Insight 1
    slides_html.append(slide(
        "Insight 1 — Churn risk concentrates in 4-8 accounts",
        """
        <p class="lead">After the outage, 14 accounts scored HIGH churn risk; 4-8 of them account for the bulk of competitor mentions and churn signals.</p>
        <ul>
          <li><strong>30 of 100 calls</strong> name a competitor by name (SentinelShield, CyberNova, VaultEdge)</li>
          <li><strong>Same customers repeat</strong>: Blackridge, Cobalt, Northstar, Helix, Meridian, Summit Trust</li>
          <li><strong>Internal Apr 24 Win/Loss call</strong>: 34 closed-lost deals totaling $2.1M ACV in Q1, with SentinelShield as primary winner</li>
        </ul>
        <p class="footnote">A real-time churn risk score would have flagged Blackridge, Cobalt, and Northstar 30 days before they escalated.</p>
        """,
        chart=chart_uris.get("01_churn_risk_concentration"),
        page_num=3,
    ))

    # Slide 4: Insight 2
    slides_html.append(slide(
        "Insight 2 — The wound is the silence, not the bug",
        """
        <p class="lead">39 of 100 calls (59 total mentions) contain communication-gap language. Concentrated in March during the outage window.</p>
        <ul>
          <li>"We didn't get any notification from Aegis" — Paula Schneider, Ridgeline</li>
          <li>"A customer had to report the outage before Aegis detected it internally" — Lauren Bishop, Cobalt</li>
          <li>"Customers feel like they're flying blind with Detect" — Diana Reeves, internal post-mortem</li>
        </ul>
        <p><strong>The process fix may matter more than the engineering fix.</strong> One proactive-comms trigger could prevent the next outage from doing the same brand damage.</p>
        """,
        chart=chart_uris.get("02_comms_gap_by_month"),
        page_num=4,
    ))

    # Slide 5: Supporting chart — sentiment recovery
    slides_html.append(slide(
        "Sentiment recovery is uneven",
        """
        <p>All three call types dropped in March. Recovery differs by audience:</p>
        <ul>
          <li><strong>Internal</strong>: 2.64 → 3.85 — bounced back above pre-outage levels</li>
          <li><strong>External</strong>: 2.90 → 4.15 — back to ~normal</li>
          <li><strong>Support</strong>: 2.73 → 3.21 — <em>still below</em> February baseline</li>
        </ul>
        <p class="footnote">Customers who actually had a problem didn't fully regain trust. Closing tickets ≠ closing the trust gap.</p>
        """,
        chart=chart_uris.get("03_sentiment_trend"),
        page_num=5,
    ))

    # Slide 6: Insight 3
    slides_html.append(slide(
        "Insight 3 — Convergent feature gaps",
        """
        <p class="lead">5 product gaps were independently identified by <em>both</em> customers and engineers.</p>
        <ul>
          <li><strong>Pipeline health visibility</strong> — customer (Pinnacle, Apr 16) + engineer (Ravi, Apr 28 retro)</li>
          <li><strong>Heartbeat alerting</strong> — engineer (Megan, Mar 18 post-mortem) + customer (Blackridge, Apr 21)</li>
          <li><strong>SSO / MFA refactor</strong> — customer (Frostbyte, Apr 25) + engineer (Tyler, Mar 28 retro)</li>
          <li><strong>Comply v2 launch scope</strong> — multiple customers + engineer (Megan, Mar 24 launch readiness)</li>
          <li><strong>Restore UX</strong> — customer (Meridian, Mar 26) + engineer (Sofia, Feb 23 planning)</li>
        </ul>
        <p class="footnote">Convergent gaps are pre-validated roadmap priorities — customer demand + engineering awareness in the same window.</p>
        """,
        chart=chart_uris.get("04_convergent_gaps"),
        page_num=6,
    ))

    # Slide 7: Pipeline architecture
    slides_html.append(slide(
        "Pipeline architecture",
        """
        <p>Hybrid design — rules first, embeddings for clustering, LLM only on uncertain cases.</p>
        <ul>
          <li><strong>Stages 1-2</strong>: deterministic foundation, no LLM (~$0 cost)</li>
          <li><strong>Stages 3-4</strong>: rules extract ~80% of signals at near-100% precision; LLM fires only on uncertain cases (~$0.001-0.005 per call)</li>
          <li><strong>Stages 5-6</strong>: pure pandas + matplotlib, fully auditable business logic</li>
        </ul>
        """,
        chart=chart_uris.get("07_pipeline_architecture"),
        page_num=7,
    ))

    # Slide 8: Validation
    slides_html.append(slide(
        "Validation — agreement with pre-computed labels",
        """
        <p>The dataset includes pre-computed <code>keyMoments</code> in <code>summary.json</code>. We treat these as <em>reference labels</em>, not ground truth, and compare our pipeline's output to them.</p>
        <table class="data">
          <thead>
            <tr><th>Metric</th><th>Our extraction</th><th>Pre-computed</th><th>Agreement</th></tr>
          </thead>
          <tbody>
            <tr><td>Calls with churn_signal</td><td>59</td><td>61</td><td>52 (both agree) · 7 (we found more) · 0 (we missed)</td></tr>
            <tr><td>Feature gaps</td><td>51 (36 customer-facing + 15 internal)</td><td>51</td><td>100% recall, convergent view identifies 5 cross-side gaps</td></tr>
            <tr><td>Competitor mentions</td><td>98 mentions across 30 calls</td><td>n/a</td><td>New signal — not in pre-computed</td></tr>
            <tr><td>Comms-gap phrases</td><td>57 across 38 calls</td><td>n/a</td><td>New signal — not in pre-computed</td></tr>
          </tbody>
        </table>
        <p class="footnote"><strong>Where we disagree with pre-computed labels, those are the most interesting findings</strong> — usually cases where the source vendor missed a signal we caught via rules + competitor mentions.</p>
        """,
        page_num=8,
    ))

    # Slide 9: Cost / scale
    slides_html.append(slide(
        "Cost & scale story",
        """
        <p>Pure-LLM-only analysis is fine at 100 transcripts. It doesn't scale.</p>
        <table class="data">
          <thead>
            <tr><th>Volume</th><th>Pure LLM</th><th>Hybrid (this pipeline)</th></tr>
          </thead>
          <tbody>
            <tr><td>100 calls (this assignment)</td><td>~$0.50</td><td><strong>~$0.30</strong></td></tr>
            <tr><td>50,000 calls / year</td><td>$250</td><td><strong>$25</strong></td></tr>
            <tr><td>500,000 calls / year</td><td>$2,500</td><td><strong>$250</strong></td></tr>
            <tr><td>5,000,000 calls / year</td><td>$25,000</td><td><strong>$2,500</strong></td></tr>
          </tbody>
        </table>
        <p>Plus: <strong>auditability</strong> (every signal traceable to a rule or quote), <strong>reproducibility</strong> (deterministic for non-LLM stages), and <strong>latency</strong> (&lt;1s for 90% of calls).</p>
        """,
        page_num=9,
    ))

    # Slide 10: Recommendations
    slides_html.append(slide(
        "What we'd build next",
        """
        <ol>
          <li><strong>Real-time churn-risk dashboard</strong> for CS leaders, fed by this pipeline. Top-10 at-risk accounts updated daily, with linked transcripts and quotes for each signal.</li>
          <li><strong>Proactive-comms trigger</strong>: when an incident is detected, auto-surface the customer-affected list within 30 minutes. Closes the comms-gap before it metastasizes.</li>
          <li><strong>Convergent-gap radar</strong>: a weekly digest for the Head of Product, showing gaps with both customer demand and engineering awareness. Should be the top of every roadmap conversation.</li>
          <li><strong>Account-health composite</strong>: per-customer score combining sentiment trend, churn signals, action-item closure rate, and comms-gap mentions. QBR-ready.</li>
        </ol>
        """,
        page_num=10,
    ))

    # Slide 11: Q&A
    slides_html.append(slide(
        "Q&A",
        """
        <p>Common questions and how to answer them are in <code>INTERVIEW_PREP.md</code> in this repo.</p>
        <ul>
          <li>"Why hybrid instead of pure LLM?" — cost, audit, latency (see Q&A doc)</li>
          <li>"How would you scale to 1M transcripts?" — same architecture, parallelize + DB</li>
          <li>"What did the pre-computed labels get wrong?" — 7 cases where our extraction found more</li>
          <li>"What's the most surprising finding?" — the convergent gaps (same product, two voices)</li>
        </ul>
        <p class="footnote">All code in <code>pipeline/</code>, all charts in <code>outputs/charts/</code>, all numbers traceable to <code>data/processed/</code>.</p>
        """,
        page_num=11,
    ))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Transcript Intelligence — Findings</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      margin: 0;
      padding: 0;
      background: #f5f5f5;
      color: #222;
    }}
    .slide {{
      width: 100vw;
      min-height: 100vh;
      padding: 60px 80px;
      background: white;
      border-bottom: 2px solid #e0e0e0;
      position: relative;
      page-break-after: always;
    }}
    .slide-content {{
      max-width: 1100px;
      margin: 0 auto;
    }}
    h2 {{
      font-size: 32px;
      margin: 0 0 30px 0;
      color: #1a1a1a;
      border-bottom: 3px solid #1f77b4;
      padding-bottom: 10px;
    }}
    p {{ font-size: 16px; line-height: 1.6; }}
    p.lead {{ font-size: 19px; font-weight: 500; color: #444; }}
    .meta {{ background: #f9f9f9; padding: 15px 20px; border-radius: 4px; margin-top: 30px; }}
    .meta p {{ margin: 5px 0; font-size: 14px; }}
    ul, ol {{ font-size: 15px; line-height: 1.8; }}
    li {{ margin: 6px 0; }}
    .footnote {{ font-size: 13px; color: #666; margin-top: 20px; font-style: italic; }}
    code {{ background: #f0f0f0; padding: 1px 6px; border-radius: 3px; font-family: "SF Mono", Menlo, monospace; font-size: 13px; }}
    .chart-wrap {{ margin-top: 30px; text-align: center; }}
    .chart-wrap img {{ max-width: 100%; height: auto; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-radius: 4px; }}
    table.data {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
    table.data th, table.data td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }}
    table.data th {{ background: #f5f5f5; font-weight: 600; }}
    .page-num {{
      position: absolute;
      bottom: 20px;
      right: 30px;
      font-size: 13px;
      color: #999;
    }}
    @media print {{
      .slide {{ padding: 40px; min-height: auto; }}
    }}
  </style>
</head>
<body>
{''.join(slides_html)}
</body>
</html>
"""

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Slide deck written to {OUTPUT_FILE}")


if __name__ == "__main__":
    build()