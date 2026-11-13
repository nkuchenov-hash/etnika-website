#!/usr/bin/env python3
"""Check real rendered CONTACTS spacing on the published ETNIKA site."""
from __future__ import annotations

import json
import os
from pathlib import Path
from playwright.sync_api import Error as PlaywrightError, sync_playwright

BASE = "https://nkuchenov-hash.github.io/etnika-website/site/"
SHA = os.environ.get("GITHUB_SHA", "manual")[:12]
OUT = Path("reports")
OUT.mkdir(exist_ok=True)
SIZES = [(1440, 900), (1366, 768), (390, 844)]
MEASURE = r"""() => {
  const section = document.getElementById('etnika-contacts-source');
  const copy = section?.querySelector('.location-copy');
  const heading = copy?.querySelector('h2');
  const reviews = document.getElementById('etnika-reviews');
  const line = reviews?.querySelector('.etnika-editorial-top');
  const rect = e => e.getBoundingClientRect();
  const pc = getComputedStyle(copy);
  const pr = getComputedStyle(reviews);
  return {
    viewport: [innerWidth, innerHeight],
    sectionHeight: rect(section).height,
    copyHeight: rect(copy).height,
    padTop: parseFloat(pc.paddingTop),
    padBottom: parseFloat(pc.paddingBottom),
    reviewsPadTop: parseFloat(pr.paddingTop),
    headingOffset: rect(heading).top - rect(copy).top,
    reviewsLineOffset: line ? rect(line).top - rect(reviews).top : null,
    captionVisible: !!document.querySelector('.etnika-map-route-note'),
    directionsVisible: !!section.querySelector('.etnika-map-directions'),
    bodyOverflow: document.documentElement.scrollWidth > innerWidth + 2
  };
}"""

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    for width, height in SIZES:
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(BASE + f"?contacts-check={SHA}", wait_until="load", timeout=50000)
        page.locator("#etnika-contacts-source h2").wait_for(timeout=20000)
        # Some on-page navigation/redirect scripts can replace the document
        # just after DOMContentLoaded. Retry the *read-only* measurements.
        data = None
        for navigation_retry in range(8):
            try:
                page.evaluate("() => document.fonts.ready")
                page.locator("#etnika-contacts-source").scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                data = page.evaluate(MEASURE)
                break
            except PlaywrightError as exc:
                if "Execution context was destroyed" not in str(exc):
                    raise
                page.wait_for_load_state("load", timeout=15000)
                page.wait_for_timeout(750)
        assert data is not None, "Published contacts geometry unavailable after page navigation retries"
        print("CONTACTS_GEOMETRY " + json.dumps(data, ensure_ascii=False), flush=True)
        assert not data["captionVisible"], ("Unrequested caption still present", data)
        assert data["directionsVisible"], ("Walking route link missing", data)
        assert not data["bodyOverflow"], ("Horizontal page overflow", data)
        assert abs(data["padTop"] - data["padBottom"]) <= 1, ("Asymmetric contacts padding", data)
        assert abs(data["padTop"] - data["reviewsPadTop"]) <= 1.1, ("Contacts do not match standard reviews section spacing", data)
        # On desktop the first text sits one standard section gap below its top.
        if width >= 1101:
            assert abs(data["headingOffset"] - data["padTop"]) <= 1.1, ("Extra gap above contacts heading", data)
            assert abs(data["sectionHeight"] - data["copyHeight"]) <= 1.1, ("Contacts section stretches past content", data)
        page.locator("#etnika-contacts-source").screenshot(path=str(OUT / f"etnika-live-contacts-{width}x{height}.png"), timeout=30000)
        page.close()
    browser.close()
print("Published contact block has equal standard top/bottom spacing, no extra caption.", flush=True)
