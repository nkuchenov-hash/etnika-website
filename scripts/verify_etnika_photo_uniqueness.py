#!/usr/bin/env python3
"""Verify published ETNIKA B02 uses eight distinct actual photos, not the legacy five."""
from pathlib import Path
import shutil,time
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
URL="https://nkuchenov-hash.github.io/etnika-website/site/?photos=b02-unique-20261113"
EXPECTED=[
"b02-02-dark.webp","b02-06-red-blonde.webp","b02-03-cool.webp",
"b02-05-ivory.webp","b02-04-purple.webp","b02-07-bw.webp",
"b02-08-taupe.webp","b02-10-red-seated.webp"
]
OUT=ROOT/'reports'
OUT.mkdir(exist_ok=True)
with sync_playwright() as pw:
    chrome=shutil.which('google-chrome') or shutil.which('google-chrome-stable')
    browser=pw.chromium.launch(headless=True,executable_path=chrome) if chrome else pw.chromium.launch(headless=True)
    for w,h in [(1366,768),(1660,930),(1920,1080)]:
        page=browser.new_page(viewport={'width':w,'height':h})
        for attempt in range(20):
            page.goto(URL+f'&w={w}&attempt={attempt}',wait_until='domcontentloaded',timeout=45000)
            pages=page.eval_on_selector_all('#etnika-block-02-final .etnika-b02__slide','es=>es.map(e=>e.getAttribute("src"))')
            active=page.eval_on_selector_all('#etnika-block-02-final .etnika-b02__slide','es=>es.map(e=>new URL(e.src).pathname.split("/").pop())')
            if active==EXPECTED:break
            print('WAIT_PUBLISHED_B02',w,attempt,active,flush=True)
            if attempt==19:raise AssertionError(f'The old repeated photo sources remain live at {w}: {active}')
            time.sleep(2)
        page.evaluate("() => document.fonts.ready")
        images=page.locator('#etnika-block-02-final .etnika-b02__slide')
        assert images.count()==8,images.count()
        page.wait_for_function("""() => {
          const xs=[...document.querySelectorAll('#etnika-block-02-final .etnika-b02__slide')];
          return xs.length===8&&xs.every(e=>e.complete&&e.naturalWidth>500&&e.naturalHeight>500);
        }""",timeout=30000)
        unique=page.evaluate("""() => {
          const media=document.querySelector('#etnika-block-02-final .etnika-b02__media');
          const photos=[...media.querySelectorAll('img.etnika-b02__slide')];
          const other=[...document.querySelectorAll('img')].filter(i=>!media.contains(i));
          return {
            urls:photos.map(i=>new URL(i.src).pathname),
            widths:photos.map(i=>i.naturalWidth),
            elsewhere:other.map(i=>new URL(i.src).pathname),
            count:document.querySelector('#etnika-block-02-final .etnika-b02__counter')?.textContent.trim(),
            active:photos.filter(i=>i.classList.contains('is-active')).length
          };
        }""")
        assert len(set(unique['urls']))==8,unique
        assert not (set(unique['urls'])&set(unique['elsewhere'])),'A B02 PHOTO APPEARS ELSEWHERE ON THE PAGE'
        assert unique['count']=='01 / 08',unique['count']
        assert unique['active']==1,unique['active']
        assert min(unique['widths'])>500,unique['widths']
        print('PASS LIVE EXCLUSIVE B02',w,len(unique['urls']),unique['urls'],flush=True)
        if w==1660:
            page.locator('#etnika-block-02-final .etnika-b02__arrow--next').click()
            page.wait_for_timeout(150)
            assert page.locator('#etnika-block-02-final .etnika-b02__counter').text_content().strip()=='02 / 08'
            page.screenshot(path=str(OUT/'b02-exclusive-eight-photos-1660x930.png'),full_page=False)
            print('PASS B02 CAROUSEL: counter=02 / 08, all eight assets loaded',flush=True)
        page.close()
    browser.close()
