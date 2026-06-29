"""
Stage 1: PARSE
==============

What this does:
    Walks the 100 transcript folders, reads the 6 JSONs in each,
    and produces a single DataFrame with one row per call.

Input:
    $DATASET_ROOT/<call_id>/
        ├── events.json
        ├── meeting-info.json
        ├── speaker-meta.json
        ├── speakers.json
        ├── summary.json
        └── transcript.json

Output:
    data/processed/01_parsed.parquet
        One row per call with all the metadata needed by Stage 2.

Design decisions:
    - Pure code, no LLM, no embeddings. The foundation must be deterministic.
    - We extract BOTH the raw metadata AND a snapshot of the pre-computed
      labels from summary.json. We treat those as reference labels to
      evaluate against in Stage 4 — not as ground truth to copy.
    - We handle missing fields defensively. Not every transcript has
      every field, and we don't want a single bad row to break the pipeline.
    - We normalize customer domains to a single string per call so
      downstream stages can group by customer cleanly.

Cost: $0 (pure Python + pandas)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Source: the assignment's dataset folder.
# Set DATASET_ROOT in your .env file or as an environment variable.
DATASET_ROOT = Path(os.environ.get("DATASET_ROOT", "/path/to/interview-assignment/dataset"))

# Output: where this stage saves its results
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "01_parsed.parquet"

AEGIS_DOMAIN = "aegiscloud.com"  # The vendor's own domain — everything else is a customer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def customer_domain_from_attendees(attendees: list[str]) -> str | None:
    """Return the first non-Aegis domain found in attendees.

    Why "first": most calls have 1 customer + 1-2 Aegis people. The customer
    is the one with the non-aegiscloud.com email. If there are multiple
    customer domains (rare), we take the first one. For internal calls,
    this returns None.
    """
    for email in attendees:
        if "@" not in email:
            continue
        domain = email.split("@", 1)[1].lower().strip()
        if domain != AEGIS_DOMAIN:
            return domain
    return None


def customer_name_from_title(title: str, customer_domain: str | None) -> str | None:
    """Extract a clean customer name from the title when possible.

    Patterns we handle:
        - "Aegis / <Customer> - <topic>" → "<Customer>"
        - "URGENT: <Customer> - <topic>" → "<Customer>"
        - "ESCALATION: <Customer> - <topic>" → "<Customer>"
        - "Support Case #NNNN - <Customer> <issue>" → "<Customer>"
        - Internal calls (no customer) → None

    Why: the customer name in the title is sometimes cleaner than the
    email domain. We use both downstream and prefer the title when available.
    """
    if not title:
        return None

    # Aegis / <Customer> pattern
    if " / " in title:
        parts = title.split(" / ", 1)[1]
        # Strip " - <topic>" suffix
        name = parts.split(" - ", 1)[0].strip()
        if name:
            return name

    # URGENT: / ESCALATION: / INCIDENT: prefix
    for prefix in ("URGENT:", "ESCALATION:", "INCIDENT:"):
        if title.upper().startswith(prefix):
            rest = title[len(prefix):].strip()
            name = rest.split(" - ", 1)[0].strip()
            if name:
                return name

    # Support Case pattern
    if title.lower().startswith("support case"):
        # Format: "Support Case #5889 - Ridgeline Logistics Detect Latency Issues"
        parts = title.split(" - ", 1)
        if len(parts) > 1:
            # Take first 1-3 words after the dash as the customer name
            tail = parts[1].strip()
            # Try to grab a multi-word name; we'll be lenient
            words = tail.split()
            # Skip words that look like generic nouns (Detect, Backup, etc.)
            skip = {"detect", "backup", "comply", "identity", "protect", "support",
                    "logvault", "cloudprime", "false", "alert", "alerts",
                    "billing", "integration", "performance", "latency", "issue",
                    "issues", "request", "case", "system", "systems", "failures",
                    "rotation", "outage", "down", "errors", "question", "dispute"}
            name_words = []
            for w in words[:4]:
                if w.lower() in skip:
                    break
                name_words.append(w)
            if name_words:
                return " ".join(name_words)

    return None


def safe_load_json(path: Path) -> dict | list | None:
    """Load JSON, return None if file missing or malformed.

    Why: not every transcript has every file. We want the pipeline to
    continue even if one file is missing, and surface the issue in
    a 'has_<file>' column instead of crashing.
    """
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Per-call parser
# ---------------------------------------------------------------------------

def parse_one_call(call_dir: Path) -> dict:
    """Parse a single transcript folder into a flat record.

    Returns a dict with all the metadata fields. Some fields may be None
    if the corresponding JSON file is missing or malformed.
    """
    call_id = call_dir.name

    meeting = safe_load_json(call_dir / "meeting-info.json") or {}
    speaker_meta = safe_load_json(call_dir / "speaker-meta.json") or {}
    speakers = safe_load_json(call_dir / "speakers.json") or []
    events = safe_load_json(call_dir / "events.json") or []
    transcript = safe_load_json(call_dir / "transcript.json") or {}
    summary = safe_load_json(call_dir / "summary.json") or {}

    attendees = meeting.get("allEmails", []) or []
    n_aegis = sum(1 for e in attendees if e.lower().endswith(f"@{AEGIS_DOMAIN}"))
    n_customer = len(attendees) - n_aegis
    cust_domain = customer_domain_from_attendees(attendees)
    cust_name = customer_name_from_title(meeting.get("title", ""), cust_domain)

    # Pre-computed reference labels (we'll evaluate against these in Stage 4)
    pre_topics = summary.get("topics", []) or []
    pre_key_moments = summary.get("keyMoments", []) or []
    pre_action_items = summary.get("actionItems", []) or []

    return {
        # Identity
        "call_id": call_id,
        "title": meeting.get("title"),

        # Meeting metadata
        "organizer_email": meeting.get("organizerEmail"),
        "host_email": meeting.get("host"),
        "start_time": meeting.get("startTime"),
        "end_time": meeting.get("endTime"),
        "duration_min": meeting.get("duration"),

        # Attendees
        "all_attendees": attendees,
        "n_attendees_total": len(attendees),
        "n_attendees_aegis": n_aegis,
        "n_attendees_customer": n_customer,
        "customer_domain": cust_domain,
        "customer_name": cust_name,

        # Transcript shape
        "n_utterances": len(transcript.get("data", []) or []),
        "n_speakers": len(speaker_meta),
        "n_join_events": len(events),
        "n_leave_events": sum(1 for e in events if e.get("type") == "Leave"),

        # Pre-computed reference labels (NOT ground truth — we'll evaluate against these)
        "pre_topics": pre_topics,
        "pre_sentiment": summary.get("overallSentiment"),
        "pre_score": summary.get("sentimentScore"),
        "pre_key_moments": pre_key_moments,
        "pre_n_key_moments": len(pre_key_moments),
        "pre_action_items": pre_action_items,
        "pre_n_action_items": len(pre_action_items),
        "pre_summary_text": summary.get("summary"),

        # Has-* flags (defensive — surface missing files)
        "has_meeting_info": meeting != {},
        "has_speaker_meta": speaker_meta != {},
        "has_speakers": bool(speakers),
        "has_events": bool(events),
        "has_transcript": transcript != {},
        "has_summary": summary != {},
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    if not DATASET_ROOT.exists():
        print(f"ERROR: dataset folder not found: {DATASET_ROOT}", file=sys.stderr)
        return 1

    # Discover call folders
    call_dirs = sorted([p for p in DATASET_ROOT.iterdir() if p.is_dir()])
    print(f"Found {len(call_dirs)} call folders in {DATASET_ROOT}")

    # Parse each
    records = []
    for i, call_dir in enumerate(call_dirs, 1):
        try:
            rec = parse_one_call(call_dir)
            records.append(rec)
        except Exception as exc:  # noqa: BLE001 — we want to continue on any error
            print(f"  [{i}/{len(call_dirs)}] FAILED to parse {call_dir.name}: {exc}")
            continue
        if i % 20 == 0:
            print(f"  Parsed {i}/{len(call_dirs)}...")

    df = pd.DataFrame(records)
    print(f"\nParsed {len(df)} calls successfully.")

    # Output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_FILE, index=False)
    print(f"Saved to {OUTPUT_FILE}")

    # Summary
    print("\n" + "=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)
    print(f"Total calls:               {len(df)}")
    print(f"With customer_domain:      {df['customer_domain'].notna().sum()}")
    print(f"Internal (no customer):    {(df['customer_domain'].isna()).sum()}")
    print(f"Unique customers:          {df['customer_domain'].nunique()}")
    print(f"Date range:                {df['start_time'].min()} → {df['start_time'].max()}")
    print(f"Median duration (min):     {df['duration_min'].median():.1f}")
    print(f"Median utterances:         {df['n_utterances'].median():.0f}")
    print(f"\nMissing files (defensive check):")
    for col in ["has_meeting_info", "has_speaker_meta", "has_speakers",
                "has_events", "has_transcript", "has_summary"]:
        n_missing = (~df[col]).sum()
        if n_missing:
            print(f"  {col}: {n_missing} missing")
        else:
            print(f"  {col}: 0 missing")
    print(f"\nPre-computed sentiment distribution:")
    print(df["pre_sentiment"].value_counts().to_string())
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())