#!/usr/bin/env python3
"""B02 static vertical alignment: equal top/bottom space and no sticky scroll motion."""
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'
REPORTS.mkdir(exist_ok=True)

with sync_playwright() as p:
    chrome = shutil.which('google-chrome') or shutil.which('google-chrome-stable')
    browser = p.chromium.launch(headless=True, executable_path=chrome) if chrome else p.chromium.launch(headless=True)
    for width, height in [(1366, 768), (1440, 900), (1660, 930), (1920, 1080)]:
        page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1)
        page.goto((ROOT / 'site/index.html').as_uri(), wait_until='domcontentloaded', timeout=45000)
        page.wait_for_timeout(300)
        for depth in [-60, 0, 120, 180]:
            page.evaluate("""depth => {
                const b=document.getElementById('etnika-block-02-final');
                window.scrollTo({top:window.scrollY+b.getBoundingClientRect().top+depth,behavior:'instant'});
            }""", depth)
            page.wait_for_timeout(90)
            v=page.evaluate("""() => {
              const q=s=>document.querySelector('#etnika-block-02-final '+s);
              const box=e=>{const x=e.getBoundingClientRect();return {top:x.top,bottom:x.bottom,height:x.height,center:x.top+x.height/2};};
              const block=document.getElementById('etnika-block-02-final');
              return {
                block:box(block),copy:box(q('.etnika-b02__copy')),
                composition:box(q('.etnika-b02__composition')),
                title:box(q('.etnika-b02__title')),
                overline:box(q('.etnika-b02__top')),
                desc:box(q('.etnika-b02__description')),
                features:box(q('.etnika-b02__features')),
                media:box(q('.etnika-b02__media')),
                controls:box(q('.etnika-b02__media-bottom')),
                position:getComputedStyle(q('.etnika-b02__copy')).position,
                groupPosition:getComputedStyle(q('.etnika-b02__composition')).position,
                groupTransform:getComputedStyle(q('.etnika-b02__composition')).transform,
                overflow:getComputedStyle(block).overflow,
              };
            }""")
            msg=f'{width}x{height}, scroll depth {depth}: {v}'
            print('B02 GEOMETRY',msg,flush=True)
            assert v['position']=='relative',msg
            assert v['groupPosition']=='static',msg
            assert v['groupTransform']=='none',msg
            assert v['block']['height']>height+90,msg
            assert abs(v['copy']['height']-(height-60))<=3,msg
            assert abs(v['media']['height']-v['block']['height'])<3,msg
            assert v['overline']['top']-v['block']['top']>=24,msg
            assert v['title']['top']>=v['overline']['bottom']+16,msg
            assert v['desc']['bottom']<v['features']['top']-10,msg
            assert v['features']['bottom']<=v['copy']['bottom']-70,msg
            assert abs(v['copy']['center']-v['composition']['center'])<3,msg
            assert v['composition']['top']-v['copy']['top']>=70,msg
            assert abs((v['composition']['top']-v['copy']['top'])-(v['copy']['bottom']-v['composition']['bottom']))<2,msg
            assert v['controls']['bottom']<=v['block']['bottom']-14,msg
            if depth==180 and width==1660:
                page.screenshot(path=str(REPORTS/'etnika-b02-owner-1660x930-mid-scroll.png'))
        page.close()
    browser.close()
