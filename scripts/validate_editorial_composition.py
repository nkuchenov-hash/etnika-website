#!/usr/bin/env python3
"""Check the editorial About/Why composition and five-step process at real viewports."""
from pathlib import Path
import shutil, sys, time
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"
OUT.mkdir(exist_ok=True)
LIVE="--live" in sys.argv
URL="https://nkuchenov-hash.github.io/etnika-website/site/" if LIVE else (ROOT/"site/index.html").as_uri()
CHROME=shutil.which("google-chrome") or shutil.which("google-chrome-stable")
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path=CHROME) if CHROME else pw.chromium.launch(headless=True)
    for w,h in [(1440,900),(1366,768),(1024,768),(390,844)]:
        page=browser.new_page(viewport={"width":w,"height":h},device_scale_factor=1)
        for attempt in range(12 if LIVE else 1):
            page.goto(URL+(f"?editorial-check={attempt}" if LIVE else ""),wait_until="domcontentloaded",timeout=45000)
            if page.locator("#etnika-process-editorial-20261124").count(): break
            if not LIVE or attempt==11: raise AssertionError("Current editorial version is not deployed")
            time.sleep(3)
        page.wait_for_function("() => !!document.querySelector('#etnika-block-02-final .etnika-editorial-why')")
        about=page.locator("#etnika-block-02-final")
        about.scroll_into_view_if_needed()
        page.evaluate("() => document.fonts.ready")
        page.evaluate("""async () => {
            const imgs=[...document.querySelectorAll('.etnika-editorial-photo img')];
            imgs.forEach(img=>img.loading='eager');
            await Promise.all(imgs.map(img=>img.decode()));
        }""")
        facts=page.evaluate("""() => {
          const a=document.querySelector('#etnika-block-02-final'), p=a.querySelector('.etnika-editorial-photos'),
          c=a.querySelector('.etnika-b02__copy'), why=a.querySelector('#etnika-studio-features');
          const r=e=>e.getBoundingClientRect().toJSON();
          return {about:r(a),photos:r(p),copy:r(c),why:r(why),background:getComputedStyle(a).backgroundColor,
            bodyWidth:document.documentElement.scrollWidth,viewport:innerWidth,
            images:[...p.querySelectorAll('img')].map(e=>({src:e.getAttribute('src'),natural:e.naturalWidth,ratio:e.naturalWidth/e.naturalHeight,box:r(e),fit:getComputedStyle(e).objectFit})),
            steps:[...document.querySelectorAll('#etnika-process-interactive .epi-card')].map(e=>({title:e.querySelector('h3').textContent.replace(/\s+/g,' '),desc:e.querySelector('.epi-desc').textContent,visible:getComputedStyle(e.querySelector('.epi-reveal')).visibility,opacity:getComputedStyle(e.querySelector('.epi-reveal')).opacity,rect:r(e)}))
          };
        }""")
        assert facts["background"]=="rgb(255, 255, 255)",facts
        assert len(facts["images"])==4 and len({x["src"] for x in facts["images"]})==4,facts
        for im in facts["images"]:
            assert im["natural"]>0 and im["box"]["width"]>0 and im["box"]["height"]>0,im
            assert abs(im["box"]["width"]/im["box"]["height"]-im["ratio"])<.025,im
            assert im["box"]["left"]>=-2 and im["box"]["right"]<=w+2,im
        assert facts["bodyWidth"]<=w+3,facts
        assert facts["why"]["bottom"]<=facts["about"]["bottom"]+2,facts
        if w>1100:
            assert facts["photos"]["left"]>=facts["copy"]["right"]-1,facts
            assert abs(facts["why"]["left"]-facts["copy"]["left"])<3,facts
        else:
            assert facts["photos"]["top"]>=facts["copy"]["bottom"]-1,facts
            assert facts["why"]["top"]>=facts["photos"]["bottom"]-1,facts
        benefits=about.locator(".etnika-editorial-benefits details")
        assert benefits.count()==6
        benefits.first.locator("summary").click()
        assert benefits.first.get_attribute("open") is not None
        assert benefits.first.locator("p").is_visible()
        benefits.first.locator("summary").click()
        about.screenshot(path=str(OUT/f"etnika-why-{'LIVE-' if LIVE else ''}{w}x{h}.png"))
        assert [x["title"] for x in facts["steps"]]==["Знакомство","Подготовка","Первый кадр","Свобода творчества","Ваши фотографии"],facts
        assert all(x["desc"] and x["visible"]=="visible" and float(x["opacity"])>.95 for x in facts["steps"]),facts
        if w>1100:
            assert len({round(x["rect"]["top"]) for x in facts["steps"]})==1,facts
        process=page.locator("#etnika-process-interactive")
        process.scroll_into_view_if_needed()
        process.screenshot(path=str(OUT/f"etnika-process-{'LIVE-' if LIVE else ''}{w}x{h}.png"))
        process.locator(".epi-more").first.click()
        process.locator(".epi-modal.open").wait_for(state="visible")
        page.keyboard.press("Escape")
        assert process.locator(".epi-modal.open").count()==0
        print(f"PASS editorial About + Why + process at {w}x{h}",flush=True)
        page.close()
    browser.close()
