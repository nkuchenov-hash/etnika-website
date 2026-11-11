#!/usr/bin/env python3
"""Viewport geometry regression for WHY ETNIKA (owner screenshot 2026-11-11)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"
OUT.mkdir(exist_ok=True)

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    for w,h in [(1366,768),(1440,900),(1635,928),(1920,1080)]:
        page=browser.new_page(viewport={"width":w,"height":h})
        page.goto((ROOT/"site/index.html").as_uri(),wait_until="load",timeout=45000)
        page.evaluate("() => document.fonts.ready")
        page.wait_for_function("() => document.querySelector('#etnika-review-flow > section')?.id==='etnika-hero'")
        page.evaluate("""() => {
          const el=document.getElementById('etnika-studio-features');
          window.scrollTo({top:el.getBoundingClientRect().top+scrollY,behavior:'instant'});
        }""")
        page.wait_for_timeout(250)
        v=page.evaluate("""() => {
          const r=s=>document.querySelector(s).getBoundingClientRect().toJSON();
          const q='#etnika-studio-features ';
          return {
            header:r('#etnika-site-header'),section:r('#etnika-studio-features'),
            stage:r(q+'.b05-stage'),copy:r(q+'.b05-copy'),
            title:r(q+'.b05-title'),bottom:r(q+'.b05-stage-bottom'),
            caption:r(q+'.b05-caption'),prev:r(q+'.b05-prev'),
            next:r(q+'.b05-next'),last:r(q+'.b05-item:last-child'),
            counter:r(q+'.b05-counter'),bodyWidth:document.documentElement.scrollWidth,
            imageOK:(()=>{let x=document.querySelector(q+'.b05-stage-image');return x.complete&&x.naturalWidth>0;})()
          };
        }""")
        err=lambda m:f'{w}x{h}: {m}: {v}'
        assert abs(v['stage']['top']-v['header']['bottom'])<4,err("photo does not start below fixed menu")
        assert v['title']['top']>=v['header']['bottom']+6,err("title obscured by menu")
        assert v['stage']['right']<=v['copy']['left']+2,err("photo is not left of copy")
        assert abs(v['stage']['bottom']-v['section']['bottom'])<4,err("photo is not full block height")
        assert v['last']['bottom']<=v['section']['bottom']-8,err("sixth advantage clipped")
        assert v['caption']['left']>=v['stage']['left']+8,err("photo caption clipped on left")
        assert v['caption']['right']<=v['stage']['right']-8,err("photo caption clipped on right")
        for key in ('bottom','caption','prev','next'):
            assert v[key]['bottom']<=v['stage']['bottom']-8,err(f"{key} clipped below photo")
        assert v['counter']['top']>=v['stage']['top']+6,err("counter hidden behind menu")
        assert v['bodyWidth']<=w+3,err("horizontal overflow")
        assert v['imageOK'],err("photo failed to load")
        if h>=900:
            assert v['section']['bottom']<=h+12,err("one-screen desktop composition too tall")
        page.screenshot(path=str(OUT/f'etnika-why-{w}x{h}.png'),full_page=False)
        print(f"WHY ETNIKA OK {w}x{h}: photo ({v['stage']['top']:.1f}..{v['stage']['bottom']:.1f}), title {v['title']['top']:.1f}, last {v['last']['bottom']:.1f}, caption {v['caption']['bottom']:.1f}",flush=True)
        page.close()
    browser.close()
