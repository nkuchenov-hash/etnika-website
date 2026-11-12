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
          const copy=q('.etnika-b02__copy'),comp=q('.etnika-b02__composition'),stack=q('.etnika-b02__stack');
          const media=q('.etnika-b02__media');
          return {block:r(b),header:r(nav),copy:r(copy),comp:r(comp),stack:r(stack),
            overline:r(q('.etnika-b02__top')),title:r(q('.etnika-b02__title')),
            features:r(q('.etnika-b02__features')),media:r(media),
            bottomOverlay:r(q('.etnika-b02__media-bottom')),
            imageLoaded:[...media.querySelectorAll('img')].some(i=>i.complete&&i.naturalWidth>0),
            copyPosition:getComputedStyle(copy).position,compPosition:getComputedStyle(comp).position,
            compTransform:getComputedStyle(comp).transform};
        }""")
        print(f'LIVE B02 {w}x{h}: {result}',flush=True)
        assert abs(result['block']['top']-result['header']['bottom'])<3, 'B02 not aligned under navigation'
        assert result['block']['height']>h+60, 'B02 SECTION NOT TALLER THAN SCREEN'
        assert result['media']['height']>h+60, 'PHOTOGRAPHIC MEDIA NOT TALLER THAN SCREEN'
        assert abs(result['media']['height']-result['block']['height'])<3, 'PHOTO MUST FILL FULL EXTENDED SECTION'
        assert abs(result['copy']['height']-(h-result['header']['height']))<3, 'COPY MUST OCCUPY ONE SCREEN UNDER MENU'
        assert result['copy']['top']-result['block']['top']>65, 'PHOTO DOES NOT EXTEND ABOVE CONTENT'
        assert abs((result['copy']['top']-result['block']['top'])-(result['block']['bottom']-result['copy']['bottom']))<2, 'PHOTO NOT EXTENDED EQUALLY ABOVE AND BELOW COPY'
        assert abs(result['stack']['mid']-result['copy']['mid'])<2, 'EDITORIAL+TITLE+BENEFITS NOT VERTICALLY CENTERED'
        assert abs((result['stack']['top']-result['copy']['top'])-(result['copy']['bottom']-result['stack']['bottom']))<2, 'UNEQUAL WHITESPACE ABOVE EDITORIAL LINE AND BELOW BENEFITS'
        assert abs(result['stack']['top']-result['overline']['top'])<2, 'EDITORIAL LINE OUTSIDE THE CENTERED GROUP'
        assert abs(result['stack']['bottom']-result['features']['bottom'])<2, 'BENEFITS OUTSIDE THE CENTERED GROUP'
        assert result['overline']['top']>=result['header']['bottom']+8,'overline behind header'
        assert result['title']['top']>result['overline']['bottom']+20,'title sticks to overline'
        assert result['features']['bottom']<result['copy']['bottom']-35,'features outside centered content area'
        assert result['bottomOverlay']['bottom']<h-15,'image controls below screen fold'
        assert result['copyPosition']=='relative' and result['compPosition']=='static' and result['compTransform']=='none', 'scroll-bound content repositioning'
        assert result['imageLoaded'],'photo not loaded'
        if w==1660:
            media=page.locator('#etnika-block-02-final .etnika-b02__media')
            assert media.evaluate("(e)=>getComputedStyle(e).backgroundColor")=='rgb(232, 229, 226)', 'RED SLIDER BACKGROUND MUST BE REMOVED'
            slide=page.locator('#etnika-block-02-final .etnika-b02__slide')
            assert slide.first.evaluate("(e)=>getComputedStyle(e).transitionDuration")=='1.35s', 'PHOTO TRANSITION SHOULD BE GENTLE'
            page.wait_for_function("""() => {const e=document.querySelectorAll('#etnika-block-02-final .etnika-b02__slide')[1];return e.complete&&e.naturalWidth>0;}""",timeout=12000)
            page.locator('#etnika-block-02-final .etnika-b02__arrow--next').click()
            page.wait_for_timeout(120)
            middle=page.evaluate("""() => {
              const b=document.getElementById('etnika-block-02-final');
              const slides=[...b.querySelectorAll('.etnika-b02__slide')];
              return {outgoingActive:slides[0].classList.contains('is-active'),
                 incoming:slides[1].classList.contains('is-entering'),
                 outgoingOpacity:getComputedStyle(slides[0]).opacity,
                 incomingOpacity:parseFloat(getComputedStyle(slides[1]).opacity),
                 counter:b.querySelector('.etnika-b02__counter').textContent.trim()};
            }""")
            assert middle['outgoingActive'] and middle['incoming'] and middle['outgoingOpacity']=='1',f'RED FLASH: outgoing image faded prematurely: {middle}'
            assert 0<middle['incomingOpacity']<1, f'Incoming slide should fade over previous photo: {middle}'
            assert middle['counter']=='02 / 05',middle
            page.wait_for_timeout(1450)
            done=page.evaluate("""() => {
              const b=document.getElementById('etnika-block-02-final');
              const slides=[...b.querySelectorAll('.etnika-b02__slide')];
              return {active:slides.map((e,i)=>e.classList.contains('is-active')?i:null).filter(i=>i!==null),
                entering:b.querySelectorAll('.etnika-b02__slide.is-entering').length};
            }""")
            assert done=={'active':[1],'entering':0},f'Transition did not complete cleanly: {done}'
            print('PASS LIVE B02 SLIDER: no red flash, 1.35s image-on-image fade, counter and arrows work',flush=True)
                page.screenshot(path=str(OUT/f'etnika-live-b02-split-{w}x{h}.png'),full_page=False)
        print(f'PASS LIVE B02 {w}x{h}: section={result["block"]["height"]:.0f}, copy={result["copy"]["height"]:.0f}, top_space={result["stack"]["top"]-result["copy"]["top"]:.1f}, bottom_space={result["copy"]["bottom"]-result["stack"]["bottom"]:.1f}, center_error={result["stack"]["mid"]-result["copy"]["mid"]:.1f}',flush=True)
        page.close()
    browser.close()
