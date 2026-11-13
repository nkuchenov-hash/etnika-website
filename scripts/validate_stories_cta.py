#!/usr/bin/env python3
"""Regression: ETNIKA guest-story photo mosaic must grow in document flow for its booking CTA."""
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
REPORTS=ROOT/"reports"
REPORTS.mkdir(exist_ok=True)

with sync_playwright() as pw:
    chrome=shutil.which('google-chrome') or shutil.which('google-chrome-stable')
    browser=pw.chromium.launch(headless=True,executable_path=chrome) if chrome else pw.chromium.launch(headless=True)
    for w,h in [(1440,900),(1714,911),(1920,1080),(390,844)]:
        page=browser.new_page(viewport={'width':w,'height':h})
        page.goto((ROOT/'site/index.html').as_uri(),wait_until='domcontentloaded',timeout=45000)
        page.wait_for_function("() => document.querySelector('#etnika-review-flow > section#etnika-stories') !== null",timeout=15000)
        page.evaluate("() => document.fonts.ready")
        page.evaluate("() => document.querySelector('#etnika-stories').scrollIntoView({block:'start',behavior:'instant'})")
        page.wait_for_timeout(300)
        v=page.evaluate("""() => {
            const el=q=>document.querySelector(q);
            const rect=e=>{const r=e.getBoundingClientRect(); return {top:r.top,bottom:r.bottom,height:r.height};};
            const section=el('#etnika-stories'), grid=el('#etnika-stories .stories-grid'),
              cta=el('#etnika-stories-booking-cta'), next=el('#etnika-process-interactive');
            const padding=parseFloat(getComputedStyle(section).paddingBottom)||0;
            const r1={section:rect(section),grid:rect(grid),cta:rect(cta),next:rect(next),padding,
               cards:section.querySelectorAll('.story-card').length,
               link:cta.querySelector('a').href,
               sectionStyle:{height:getComputedStyle(section).height,maxHeight:getComputedStyle(section).maxHeight,
                 overflow:getComputedStyle(section).overflow},
               gridStyle:{height:getComputedStyle(grid).height,flex:getComputedStyle(grid).flex}};
            cta.style.setProperty('display','none','important');
            r1.withoutCTA=section.getBoundingClientRect().height;
            cta.style.removeProperty('display');
            r1.withCTA=section.getBoundingClientRect().height;
            r1.delta=r1.withCTA-r1.withoutCTA;
            return r1;
        }""")
        path=REPORTS/f'etnika-stories-cta-{w}x{h}.png'
        page.screenshot(path=str(path),full_page=False)
        print(f"STORIES {w}x{h}: {v}",flush=True)
        assert v['cards']==8,f"{w}x{h}: missing photo cards: {v}"
        assert v['grid']['bottom']<=v['cta']['top']-8,f"{w}x{h}: CTA overlaps photo grid: {v}"
        assert v['cta']['bottom']+v['padding']<=v['section']['bottom']+3,f"{w}x{h}: CTA overflows the section: {v}"
        assert v['next']['top']>=v['section']['bottom']-3,f"{w}x{h}: next block overlaps gallery: {v}"
        assert v['delta']>=65,f"{w}x{h}: adding CTA does not increase gallery section height enough: {v}"
        assert 'n1268189.yclients.com' in v['link'],f"{w}x{h}: booking link changed: {v}"
        page.close()
    browser.close()
print('ETNIKA guest-story CTA layout: PASS',flush=True)
