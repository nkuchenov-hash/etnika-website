#!/usr/bin/env python3
"""Viewport geometry regression for WHY ETNIKA (owner screenshot 2026-11-11)."""
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"
OUT.mkdir(exist_ok=True)

with sync_playwright() as pw:
    chrome=shutil.which('google-chrome') or shutil.which('google-chrome-stable')
    browser=pw.chromium.launch(headless=True,executable_path=chrome) if chrome else pw.chromium.launch(headless=True)
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
            shell:r('#etnika-studio-features .b05-shell'), main:r('#etnika-studio-features .b05-main'),
            metrics:(()=>{let e=document.querySelector('#etnika-studio-features .b05-shell');let m=document.querySelector('#etnika-studio-features .b05-main');let a=document.querySelector('#etnika-studio-features');const cs=(x)=>({height:getComputedStyle(x).height,minHeight:getComputedStyle(x).minHeight,maxHeight:getComputedStyle(x).maxHeight,boxSizing:getComputedStyle(x).boxSizing,display:getComputedStyle(x).display,paddingTop:getComputedStyle(x).paddingTop});return {section:cs(a),shell:cs(e),main:cs(m),nav:getComputedStyle(document.documentElement).getPropertyValue('--etnika-nav-height')};})(),
            stage:r(q+'.b05-stage'),copy:r(q+'.b05-copy'),
            title:r(q+'.b05-title'), intro:r(q+'.b05-intro'), meta:r(q+'.b05-meta'),
            first:r(q+'.b05-item:first-child'), list:r(q+'.b05-list'),
            titleFont:parseFloat(getComputedStyle(document.querySelector(q+'.b05-title')).fontSize),
            titleFamily:getComputedStyle(document.querySelector(q+'.b05-title')).fontFamily,
            listRows:Array.from(document.querySelectorAll(q+'.b05-item'),e=>e.getBoundingClientRect().height),
            bottom:r(q+'.b05-stage-bottom'),
            caption:r(q+'.b05-caption'),prev:r(q+'.b05-prev'),
            next:r(q+'.b05-next'),last:r(q+'.b05-item:last-child'),
            counter:r(q+'.b05-counter'),bodyWidth:document.documentElement.scrollWidth,
            imageOK:(()=>{let x=document.querySelector(q+'.b05-stage-image');return x.complete&&x.naturalWidth>0;})(),
            background:getComputedStyle(document.querySelector(q+'.b05-stage')).backgroundImage
          };
        }""")
        path=OUT/f'etnika-why-{w}x{h}.png'
        page.screenshot(path=str(path),full_page=False)
        print(f"WHY {w}x{h}: section={v['section']['top']:.1f}..{v['section']['bottom']:.1f}, shell={v['shell']['height']:.1f}, main={v['main']['height']:.1f}, computed={v['metrics']}, photo={v['stage']['top']:.1f}..{v['stage']['bottom']:.1f}, heading={v['title']['top']:.1f}..{v['title']['bottom']:.1f}, final={v['last']['bottom']:.1f}, caption={v['caption']['bottom']:.1f}, imageOK={v['imageOK']}, background={v['background']}",flush=True)
        err=lambda m:f'{w}x{h}: {m}: {v}'
        assert abs(v['stage']['top']-v['header']['bottom'])<4,err("photo does not start below fixed menu")
        assert v['title']['top']>=v['header']['bottom']+6,err("title obscured by menu")
        # Editorial hierarchy: headline matches the one shared sitewide size.
        # All six advantages form a compact intentional stack, not a stretched grid.
        expected_title=max(62,min(w*.0625,118))
        assert abs(v['titleFont']-expected_title)<2.5,err(f"heading out of design-system scale: {v['titleFont']}, expected {expected_title}")
        assert 'Forum' in v['titleFamily'],err("heading font not Forum")
        assert len(v['listRows'])==6 and max(v['listRows'])<=82,err("selector rows stretched")
        assert max(v['listRows'])-min(v['listRows'])<=2,err("uneven selector heights")
        assert v['intro']['top']>=v['title']['bottom']+7,err("heading and intro collide")
        assert v['meta']['top']>=v['intro']['bottom']+7,err("intro and facts collide")
        assert v['list']['top']>=v['meta']['bottom']+7,err("facts and selectors collide")
        assert v['title']['top']>=v['copy']['top']+9,err("top content padding lost")
        assert v['last']['bottom']<=v['copy']['bottom']-9,err("bottom content padding lost")
        group_mid=(v['title']['top']+v['last']['bottom'])/2
        copy_mid=(v['copy']['top']+v['copy']['bottom'])/2
        assert abs(group_mid-copy_mid)<35,err("right-side composition not visually centered")
        print(f"TYPE {w}x{h}: Forum {v['titleFont']:.1f}px, rows {[round(n) for n in v['listRows']]}, centered delta={group_mid-copy_mid:.1f}px",flush=True)

        assert v['stage']['right']<=v['copy']['left']+2,err("photo is not left of copy")
        assert abs(v['stage']['bottom']-v['section']['bottom'])<4,err("photo is not full block height")
        assert v['last']['bottom']<=v['section']['bottom']-8,err("sixth advantage clipped")
        assert v['caption']['left']>=v['stage']['left']+8,err("photo caption clipped on left")
        assert v['caption']['right']<=v['stage']['right']-8,err("photo caption clipped on right")
        for key in ('bottom','caption','prev','next'):
            assert v[key]['bottom']<=v['stage']['bottom']-8,err(f"{key} clipped below photo")
        assert v['counter']['top']>=v['stage']['top']+6,err("counter hidden behind menu")
        assert v['bodyWidth']<=w+3,err("horizontal overflow")
        assert v['imageOK'] or 'etnika-hero-red-wide.jpg' in v['background'],err("photo failed to load and fallback absent")
        if h>=900:
            assert v['section']['bottom']<=h+12,err("one-screen desktop composition too tall")
        print(f"WHY ETNIKA OK {w}x{h}: photo ({v['stage']['top']:.1f}..{v['stage']['bottom']:.1f}), title {v['title']['top']:.1f}, last {v['last']['bottom']:.1f}, caption {v['caption']['bottom']:.1f}",flush=True)
        # Exercise the REAL fragment navigation, which is affected by the global
        # html scroll-padding and this section's own scroll-margin.
        page.evaluate("""() => document.getElementById('etnika-studio-features').scrollIntoView({behavior:'instant',block:'start'})""")
        page.wait_for_timeout(150)
        anchor=page.evaluate("""() => ({
          header:document.getElementById('etnika-site-header').getBoundingClientRect().bottom,
          photo:document.querySelector('#etnika-studio-features .b05-stage').getBoundingClientRect().top,
          heading:document.querySelector('#etnika-studio-features .b05-title').getBoundingClientRect().top,
          bottom:document.querySelector('#etnika-studio-features .b05-stage-bottom').getBoundingClientRect().bottom,
          last:document.querySelector('#etnika-studio-features .b05-item:last-child').getBoundingClientRect().bottom
        })""")
        print(f"ANCHOR {w}x{h}: {anchor}",flush=True)
        assert abs(anchor['photo']-anchor['header'])<=4,err("fragment scroll overlays photo with menu")
        assert anchor['heading']>=anchor['header']+6,err("fragment scroll hides heading under menu")
        assert anchor['bottom']<=h-8 and anchor['last']<=h-8,err("fragment scroll clips caption or final selector")
        page.close()
    browser.close()
