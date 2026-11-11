#!/usr/bin/env python3
"""Smoke-test the *published* ETNIKA page, not the checkout's HTML file."""
from __future__ import annotations

import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://nkuchenov-hash.github.io/etnika-website/site/"
EXPECTED_BUILD = "20261111-hero-first"
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)
SHA = os.environ.get("GITHUB_SHA", "manual")[:12]

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    for width, height in ((1440, 900), (390, 844)):
        page = browser.new_page(viewport={"width": width, "height": height})
        url = BASE + "?smoke=" + SHA
        last_error = None
        for attempt in range(15):
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=40000)
                if response is None or response.status >= 400:
                    raise AssertionError(f"Published site returned {response.status if response else 'no response'}")
                page.wait_for_function(
                    "() => document.querySelector('#etnika-review-flow > section') !== null",
                    timeout=8000,
                )
                page.wait_for_timeout(600)
                metrics = page.evaluate("""() => {
                    const hero=document.getElementById('etnika-hero');
                    const process=document.getElementById('etnika-process-interactive');
                    const flow=document.getElementById('etnika-review-flow');
                    const build=document.querySelector('meta[name="etnika-build"]')?.content;
                    const hr=hero?.getBoundingClientRect();
                    const pr=process?.getBoundingClientRect();
                    const center=document.elementFromPoint(innerWidth/2,innerHeight/2);
                    return {
                       build,
                       first:flow?.querySelector(':scope > section')?.id,
                       initialScrollY:scrollY,
                       heroTop:hr?.top,
                       heroBottom:hr?.bottom,
                       processTop:pr?.top,
                       middleSection:center?.closest('section')?.id,
                       headerState:document.getElementById('etnika-site-header')?.dataset.hero
                    };
                }""")
                assert metrics["build"] == EXPECTED_BUILD, f"Old deployed HTML: {metrics}"
                assert metrics["first"] == "etnika-hero", f"Wrong runtime section order: {metrics}"
                assert abs(metrics["initialScrollY"]) < 4, f"Page opened below HERO: {metrics}"
                assert metrics["heroTop"] <= 70, f"HERO starts too low: {metrics}"
                assert metrics["heroBottom"] >= height * 0.85, f"HERO is not a full first screen: {metrics}"
                assert metrics["processTop"] >= metrics["heroBottom"] - 5, f"Process overlaps HERO: {metrics}"
                assert metrics["middleSection"] == "etnika-hero", f"Process hides the visible HERO: {metrics}"
                assert metrics["headerState"] == "true", f"Header already outside HERO: {metrics}"
                path = REPORTS / f"etnika-live-first-screen-{width}x{height}.png"
                page.screenshot(path=str(path), full_page=False)
                print(f"PASS LIVE {width}x{height}: {metrics}; screenshot={path}", flush=True)
                break
            except Exception as exc:
                last_error = exc
                print(f"Live check attempt {attempt + 1} failed: {exc}", flush=True)
                if attempt == 14:
                    raise AssertionError(f"Published page did not show HERO first: {last_error}") from exc
                time.sleep(3)
        page.close()
    browser.close()
