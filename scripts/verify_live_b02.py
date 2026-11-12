#!/usr/bin/env python3
"""Verify the *published* B02 split heights and visible centered copy in Chrome."""
from pathlib import Path
import re
import shutil
import time
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'site/index.html').read_text(encoding='utf-8')
BUILD=re.search(r'<meta name="etnika-build" content="([^"]+)"',html).group(1)
URL="https://nkuchenov-hash.github.io/etnika-website/site/?verify=b02-split-height"
OUT=ROOT/'reports'
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    chrome=shutil.which('google-chrome') or shutil.which('google-chrome-stable')
    browser=p.chromium.launch(headless=True,executable_path=chrome) if chrome else p.chromium.launch(headless=True)
    for w,h in [(1660,930),(1366,768),(1920,1080)]:
        page=browser.new_page(viewport={'width':w,'height':h},device_scale_factor=1)
        result=None
        for attempt in range(6):
            page.goto(URL+f'&size={w}&attempt={attempt}',wait_until='domcontentloaded',timeout=45000)
            page.evaluate('() => document.fonts.ready')
            page.wait_for_timeout(500)
            build=page.locator('meta[name="etnika-build"]').get_attribute('content')
            if build==BUILD: break
            if attempt==5:raise AssertionError(f'Old live HTML at {w}x{h}: {build!r}, expected {BUILD!r}')
            time.sleep(2)
        page.evaluate("""() => {
          const b=document.getElementById('etnika-block-02-final');
          const nav=document.getElementById('etnika-site-header');
          window.scrollTo({top:scrollY+b.getBoundingClientRect().top-nav.getBoundingClientRect().height,behavior:'instant'});
        }""")
        page.wait_for_timeout(150)
        result=page.evaluate("""() => {
          const b=document.getElementById('etnika-block-02-final');
          const nav=document.getElementById('etnika-site-header');
          const q=s=>b.querySelector(s);
          const r=e=>{const x=e.getBoundingClientRect();return {top:x.top,bottom:x.bottom,height:x.height,mid:(x.top+x.bottom)/2}};
          const copy=q('.etnika-b02__copy'),comp=q('.etnika-b02__composition');
          const media=q('.etnika-b02__media');
          return {block:r(b),header:r(nav),copy:r(copy),comp:r(comp),
            overline:r(q('.etnika-b02__top')),title:r(q('.etnika-b02__title')),
            features:r(q('.etnika-b02__features')),media:r(media),
            bottomOverlay:r(q('.etnika-b02__media-bottom')),
            imageLoaded:[...media.querySelectorAll('img')].some(i=>i.complete&&i.naturalWidth>0),
            copyPosition:getComputedStyle(copy).position,compPosition:getComputedStyle(comp).position,
            compTransform:getComputedStyle(comp).transform};
        }""")
        print(f'LIVE B02 {w}x{h}: {result}',flush=True)
        assert abs(result['block']['top']-result['header']['bottom'])<3, 'B02 not aligned under navigation'
        assert abs(result['block']['height']-(h-result['header']['height']))<3, 'VISIBLE SECTION TOO TALL OR TOO SHORT'
        assert result['media']['height']>h+90, 'PHOTOGRAPHIC MEDIA NOT TALLER THAN SCREEN'
        assert abs(result['copy']['height']-result['block']['height'])<3, 'COPY MUST FILL VISIBLE SECTION'
        assert abs(result['comp']['mid']-result['copy']['mid'])<2, 'TEXT NOT VERTICALLY CENTERED'
        assert abs((result['comp']['top']-result['copy']['top'])-(result['copy']['bottom']-result['comp']['bottom']))<2, 'UNEQUAL TOP/BOTTOM TEXT SPACE'
        assert result['overline']['top']>=result['header']['bottom']+8,'overline behind header'
        assert result['title']['top']>result['overline']['bottom']+20,'title sticks to overline'
        assert result['features']['bottom']<result['block']['bottom']-35,'features outside visible screen'
        assert result['bottomOverlay']['bottom']<h-15,'image controls below screen fold'
        assert result['copyPosition']=='relative' and result['compPosition']=='static' and result['compTransform']=='none', 'scroll-bound content repositioning'
        assert result['imageLoaded'],'photo not loaded'
        page.screenshot(path=str(OUT/f'etnika-live-b02-split-{w}x{h}.png'),full_page=False)
        print(f'PASS LIVE B02 {w}x{h}: section={result["block"]["height"]:.0f}, copy={result["copy"]["height"]:.0f}, top_space={result["comp"]["top"]-result["copy"]["top"]:.1f}, bottom_space={result["copy"]["bottom"]-result["comp"]["bottom"]:.1f}, center_error={result["comp"]["mid"]-result["copy"]["mid"]:.1f}',flush=True)
        page.close()
    browser.close()
