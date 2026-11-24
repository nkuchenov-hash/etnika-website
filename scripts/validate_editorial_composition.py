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
    for w,h in [(1600,900),(1440,900),(1366,768),(1920,1080),(2560,1080),(3440,1440),(1024,768),(390,844)]:
        page=browser.new_page(viewport={"width":w,"height":h},device_scale_factor=1)
        for attempt in range(12 if LIVE else 1):
            page.goto(URL+(f"?editorial-check={attempt}" if LIVE else ""),wait_until="domcontentloaded",timeout=45000)
            if page.locator('meta[name="etnika-build"][content="20261124-body-desktop18-v12"]').count(): break
            if not LIVE or attempt==11: raise AssertionError("Current editorial version is not deployed")
            time.sleep(3)
        page.wait_for_function("() => !!document.querySelector('#etnika-block-02-final .etnika-editorial-why')")
        hero=page.locator("#etnika-hero")
        page.evaluate("() => document.fonts.ready")
        page.locator("#etnika-hero .ec-slide--red .ec-photo").evaluate("(e)=>e.decode()")
        hero_metrics=page.evaluate("""() => {
          const p=document.querySelector('#etnika-hero .ec-slide--red .ec-photo'), h=document.querySelector('#etnika-hero .ec-love');
          const title=document.querySelector('#etnika-block-02-final .etnika-b02__title'), token=document.createElement('i');
          token.style.fontSize='var(--etnika-section-title)';document.body.append(token);
          const pr=p.getBoundingClientRect(), hr=h.getBoundingClientRect(), logo=document.querySelector('#etnika-hero .ec-brand').getBoundingClientRect(), bottom=document.querySelector('#etnika-hero .ec-bottom').getBoundingClientRect();
          // The original uncropped HERO source has figure+chair bounds x=.415..595, y=.36..96.
          const subject={left:pr.left+.415*pr.width,right:pr.left+.595*pr.width,top:pr.top+.36*pr.height,bottom:pr.top+.96*pr.height};
          const result={subject,heartRight:hr.right,logoRight:logo.right,bottomTop:bottom.top,fit:getComputedStyle(p).objectFit,position:getComputedStyle(p).objectPosition,
            heart:getComputedStyle(h).filter, title:parseFloat(getComputedStyle(title).fontSize),
            token:parseFloat(getComputedStyle(token).fontSize)};
          token.remove();return result;
        }""")
        assert 'url(' not in hero_metrics["heart"],hero_metrics
        assert abs(hero_metrics["title"]-hero_metrics["token"])<1,hero_metrics
        if w/h>2752/1536 and w>760: assert hero_metrics["fit"]=="contain",hero_metrics
        if w>760:
            assert hero_metrics["subject"]["left"]>max(hero_metrics["heartRight"],hero_metrics["logoRight"])+12, f"Portrait touches logo or heart: {hero_metrics}"
            assert hero_metrics["subject"]["right"]<w-12, f"Portrait clipped at right edge: {hero_metrics}"
            assert hero_metrics["subject"]["bottom"]<hero_metrics["bottomTop"]-12, f"Portrait overlaps bottom navigation: {hero_metrics}"
        hero.screenshot(path=str(OUT/f"etnika-hero-{'LIVE-' if LIVE else ''}{w}x{h}.png"))
        minimum=18 if w>=1920 else 16
        typography=page.evaluate("""() => [...document.querySelectorAll(
          '#etnika-process-interactive .epi-desc, #etnika-process-interactive .epi-more, #etnika-process-interactive .epi-sub, #etnika-block-02-final .etnika-b02__description, #etnika-block-02-final .etnika-b02__feature, .etnika-editorial-benefits summary, .etnika-editorial-benefits p, .etnika-editorial-metrics span'
        )].map(e=>({label:e.textContent.trim().slice(0,90),size:parseFloat(getComputedStyle(e).fontSize)}))""")
        assert typography and all(t["size"]>=minimum-.1 for t in typography), f"Forbidden small text at {w}px: {typography}"
        if w>=761:
            body_roles=page.evaluate("""() => [...document.querySelectorAll(
              '#etnika-block-02-final .etnika-b02__description, #etnika-process-interactive .epi-sub, #etnika-process-interactive .epi-desc, #etnika-faq .faq-answer p, #etnika-space-photo .spf-intro, #etnika-studio-features .etnika-editorial-benefits details p, #etnika-gift .eg-sub, #etnika-faq-tariffs .faq-answer p, #etnika-contacts-source .location-copy p, #etnika-reviews .urw-text'
            )].map(e=>({text:e.textContent.trim().slice(0,80),size:parseFloat(getComputedStyle(e).fontSize),family:getComputedStyle(e).fontFamily,weight:getComputedStyle(e).fontWeight}))""")
            assert body_roles and all(abs(t["size"]-18)<.1 and "Geologica" in t["family"] and t["weight"]=="100" for t in body_roles),f"Body typography mismatch at {w}: {body_roles}"
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
          return {about:r(a),copy:r(c),why:r(why),background:getComputedStyle(a).backgroundColor, bodySize:parseFloat(getComputedStyle(a.querySelector('.etnika-b02__description')).fontSize), titleLines:[...a.querySelectorAll('.etnika-title-line')].map(e=>{const t=document.createRange();t.selectNodeContents(e);return {box:t.getBoundingClientRect().toJSON(),rects:t.getClientRects().length}}),
            bodyWidth:document.documentElement.scrollWidth,viewport:innerWidth,
            images:[...a.querySelectorAll('.etnika-editorial-photo img')].map(e=>({src:e.getAttribute('src'),natural:e.naturalWidth,ratio:e.naturalWidth/e.naturalHeight,box:r(e),fit:getComputedStyle(e).objectFit})),
            steps:[...document.querySelectorAll('#etnika-process-interactive .epi-card')].map(e=>({title:e.querySelector('h3').textContent.replace(/\s+/g,' '),desc:e.querySelector('.epi-desc').textContent,visible:getComputedStyle(e.querySelector('.epi-reveal')).visibility,opacity:getComputedStyle(e.querySelector('.epi-reveal')).opacity,rect:r(e)}))
          };
        }""")
        assert facts["background"]=="rgb(255, 255, 255)",facts
        assert {x["src"] for x in facts["images"]}=={"assets/b02/b02-06-red-blonde.webp","assets/b02/b02-03-cool.webp"},facts
        for im in facts["images"]:
            assert im["natural"]>0 and im["box"]["width"]>0 and im["box"]["height"]>0,im
            assert abs(im["box"]["width"]/im["box"]["height"]-im["ratio"])<.025,im
            assert im["box"]["left"]>=-2 and im["box"]["right"]<=w+2,im
        assert facts["bodyWidth"]<=w+3,facts
        assert facts["why"]["bottom"]<=facts["about"]["bottom"]+2,facts
        assert abs(facts["bodySize"]-18)<.1,facts
        assert len(facts["titleLines"])==2,facts
        first,second=[x["box"] for x in facts["images"]]
        if w>1100:
            assert first["left"]>=facts["copy"]["right"]-1,facts
            assert abs(facts["why"]["left"]-facts["copy"]["left"])<3,facts
            assert facts["why"]["top"]-facts["copy"]["bottom"]>=114,facts
            assert all(x["rects"]==1 and x["box"]["right"]<first["left"]-2 for x in facts["titleLines"]),facts
            assert second["top"]>first["bottom"],facts
        else:
            assert first["top"]>=facts["copy"]["bottom"]-1,facts
            assert facts["why"]["top"]>=max(first["bottom"],second["bottom"])-1,facts
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
