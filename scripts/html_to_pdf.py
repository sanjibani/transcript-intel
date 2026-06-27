"""
Convert the slide deck HTML to PDF using Playwright + headless Chromium.

Why Playwright (not wkhtmltopdf or LaTeX):
- Renders the exact same way a browser would
- Handles embedded base64 images natively
- Page size and margins can be controlled
- Runs headless on macOS without Qt or display server

Output: outputs/slide_deck.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
HTML_FILE = OUTPUT_DIR / "slide_deck.html"
PDF_FILE = OUTPUT_DIR / "slide_deck.pdf"


def main() -> int:
    if not HTML_FILE.exists():
        print(f"ERROR: {HTML_FILE} not found. Run scripts/build_slide_deck.py first.", file=sys.stderr)
        return 1

    from playwright.sync_api import sync_playwright

    print(f"Converting {HTML_FILE} → {PDF_FILE}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 16:9 slide aspect, fits standard projector / screen
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        page.goto(f"file://{HTML_FILE}")
        # Wait for any base64 images to decode
        page.wait_for_load_state("networkidle")
        # Save as PDF — full page per slide, no extra margin
        page.pdf(
            path=str(PDF_FILE),
            width="1600px",
            height="900px",
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            print_background=True,
            prefer_css_page_size=True,
        )
        browser.close()

    size_kb = PDF_FILE.stat().st_size / 1024
    print(f"✓ PDF written: {PDF_FILE} ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())