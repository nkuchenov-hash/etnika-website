#!/usr/bin/env python3
"""Verify the PUBLIC ETNIKA Why section against the owner-approved layout.
Unlike local rendering, this catches missing or cancelled GitHub Pages deploys."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import os, shutil

OUT=Path("reports")
OUT.mkdir(exist_ok=True)
BASE="https://nkuchenov-hash.github.io/etnika-website/site/"
CHROME=shutil.which("google-chrome") or shutil.which("google-chrome-stable")
assert CHROME, "GitHub runner Chrome is required"

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path=CHROME)
    for width,height in [(1366,768),(1635,928)]:
        page=browser.new_page(viewport={"width":width,"height":height})
        page.goto(BASE+"?why-live-check="+os.environ.get("GITHUB_SHA","manual")[:12],wait_until="domcontentloaded",timeout=45000)
        page.wait_for_function("() => !!document.querySelector('#etnika-review-flow #etnika-studio-features .b05-copy')",timeout=30000)
        page.evaluate("() => document.fonts.ready")
        page.evaluate("""() => {
          const target=document.getElementById('etnika-studio-features');
          target.scrollIntoView({block:'start',behavior:'instant'});
        }""")
        page.wait_for_timeout(450)
        v=page.evaluate("""() => {
          const q=s=>document.querySelector('#etnika-studio-features '+s);
          const rect=e=>e.getBoundingClientRect().toJSON();
          const rows=[...document.querySelectorAll('#etnika-studio-features .b05-item')];
          const head=q('.b05-title');
          const photo=q('.b05-stage-image');
          return {
            header:rect(document.getElementById('etnika-site-header')),
            section:rect(document.getElementById('etnika-studio-features')),
            stage:rect(q('.b05-stage')),copy:rect(q('.b05-copy')),
            title:rect(head),intro:rect(q('.b05-intro')),
            facts:rect(q('.b05-meta')),list:rect(q('.b05-list')),
            last:rect(rows[rows.length-1]),caption:rect(q('.b05-stage-bottom')),
            font:parseFloat(getComputedStyle(head).fontSize),
            family:getComputedStyle(head).fontFamily,
            rowHeights:rows.map(e=>e.getBoundingClientRect().height),
            photoLoaded:photo.complete&&photo.naturalWidth>0,
            photoFallback:getComputedStyle(q('.b05-stage')).backgroundImage
          };
        }""")
        path=OUT/f"etnika-why-LIVE-{width}x{height}.png"
        page.screenshot(path=str(path),full_page=False)
        print(f"PUBLIC {width}x{height}: title_y={v['title']['top']:.1f}, title_size={v['font']:.1f}, "
              f"rows={[round(n) for n in v['rowHeights']]}, photo_bottom={v['stage']['bottom']:.1f}, "
              f"last_bottom={v['last']['bottom']:.1f}, caption_bottom={v['caption']['bottom']:.1f}, photo={v['photoLoaded']}",flush=True)
        expected=max(62,min(width*.0625,118))
        assert abs(v['font']-expected)<2, f"PUBLIC SITE IS OLD: heading {v['font']}, expected {expected}"
        assert 'Forum' in v['family'], f"Wrong title font: {v}"
        assert v['title']['top']>=v['header']['bottom']+35, f"PUBLIC SITE IS OLD: heading glued to menu: {v}"
        assert len(v['rowHeights'])==6 and max(v['rowHeights'])<=82, f"PUBLIC SITE IS OLD: stretched list: {v}"
        assert max(v['rowHeights'])-min(v['rowHeights'])<=2, f"Uneven row heights: {v}"
        assert v['last']['bottom']<=height-16, f"Last selector clipped: {v}"
        assert v['caption']['bottom']<=height-10, f"Photo caption clipped: {v}"
        assert abs(v['stage']['top']-v['header']['bottom'])<4, f"Photo starts under nav: {v}"
        assert abs(v['stage']['bottom']-height)<4, f"Photo does not fill screen: {v}"
        assert v['photoLoaded'] or "etnika-hero-red-wide.jpg" in v['photoFallback'], "Photo and fallback unavailable"
        page.close()
    browser.close()
