#!/usr/bin/env python3
"""Smoke-test the *published* ETNIKA page, not the checkout's HTML file."""
from __future__ import annotations

import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://nkuchenov-hash.github.io/etnika-website/site/"
EXPECTED_BUILD = "20261111-section-system"
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
                       headerState:document.getElementById('etnika-site-header')?.dataset.hero,
                       studioLabel:document.querySelector('#etnika-site-header .esh__descriptor')?.textContent?.trim(),
                       logoRight:document.querySelector('#etnika-hero .ec-brand')?.getBoundingClientRect().right,
                       heartLeft:document.querySelector('#etnika-hero .ec-love')?.getBoundingClientRect().left,
                       heartRight:document.querySelector('#etnika-hero .ec-love')?.getBoundingClientRect().right,
                       order:Array.from(flow?.children||[]).map(el=>el.id).slice(0,5),
                       sectionSystem:(() => {
                         const key=['etnika-block-02-final','etnika-space-photo','etnika-stories','etnika-process-interactive','etnika-studio-features','etnika-faq','etnika-prices-clear','etnika-extra','etnika-faq-tariffs','etnika-gift','etnika-reviews','etnika-contacts-source'];
                         const reference=document.createElement('i');
                         reference.style.fontSize='var(--etnika-section-title)';
                         document.body.appendChild(reference);
                         const titleToken=parseFloat(getComputedStyle(reference).fontSize);
                         reference.remove();
                         return {
                           titleToken,
                           edge:parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--et-u-edge')),
                           blocks:key.map(id=>{
                             const node=document.getElementById(id);
                             const h=node?.querySelector('h2.etnika-section-heading');
                             const st=node&&getComputedStyle(node);
                             return {id,h2:!!h,titleSize:h?parseFloat(getComputedStyle(h).fontSize):null,titleFamily:h?getComputedStyle(h).fontFamily:null,
                               height:node?.getBoundingClientRect().height, outerTop:parseFloat(st?.paddingTop||0),
                               outerBottom:parseFloat(st?.paddingBottom||0)};
                           }),
                           processLeft:document.querySelector('#etnika-process-interactive .epi-grid')?.getBoundingClientRect().left,
                           storiesLeft:document.querySelector('#etnika-stories .stories-shell')?.getBoundingClientRect().left,
                           spaceFrameHeight:document.querySelector('#etnika-space-photo .spf-shell')?.getBoundingClientRect().height,
                           b02Gap:(() => {const a=document.querySelector('#etnika-block-02-final .etnika-b02__top');const b=document.querySelector('#etnika-block-02-final .etnika-b02__main');return a&&b?b.getBoundingClientRect().top-a.getBoundingClientRect().bottom:null})()
                         };
                       })()
                    };
                }""")
                assert metrics["build"] == EXPECTED_BUILD, f"Old deployed HTML: {metrics}"
                assert metrics["first"] == "etnika-hero", f"Wrong runtime section order: {metrics}"
                assert metrics["order"][:4] == ["etnika-hero","etnika-block-02-final","etnika-space-photo","etnika-stories"], f"Wrong owner-approved section order: {metrics}"
                assert abs(metrics["initialScrollY"]) < 4, f"Page opened below HERO: {metrics}"
                assert metrics["heroTop"] <= 70, f"HERO starts too low: {metrics}"
                assert metrics["heroBottom"] >= height * 0.85, f"HERO is not a full first screen: {metrics}"
                assert metrics["processTop"] >= metrics["heroBottom"] - 5, f"Process overlaps HERO: {metrics}"
                assert metrics["middleSection"] == "etnika-hero", f"Process hides the visible HERO: {metrics}"
                assert metrics["headerState"] == "true", f"Header already outside HERO: {metrics}"
                assert metrics["studioLabel"] == "СТУДИЯ АВТОПОРТРЕТА", f"Header studio label is not uppercase: {metrics}"
                assert metrics["heartLeft"] - metrics["logoRight"] >= (9 if width <= 760 else 20), f"Heart too close to brand: {metrics}"
                assert metrics["heartRight"] <= width + 2, f"Heart overflows viewport: {metrics}"
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
