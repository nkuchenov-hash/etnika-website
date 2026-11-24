#!/usr/bin/env python3
"""Regression: B02 remains a single editorial spread after all page scripts run."""
from pathlib import Path
import shutil, sys, json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"; OUT.mkdir(exist_ok=True)
URL="https://nkuchenov-hash.github.io/etnika-website/site/?v=about-six-v20" if "--live" in sys.argv else (ROOT/"site/index.html").as_uri()
chrome=shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path=chrome)
    errors=[]
    for w,h in [(766,685),(1366,768),(1600,900),(1920,1080),(2560,1080),(390,844),(375,667)]:
        page=browser.new_page(viewport={"width":w,"height":h},device_scale_factor=1)
        try:
            page.goto(URL,wait_until="load",timeout=45000)
            page.evaluate("() => document.fonts.ready")
            about=page.locator("#etnika-block-02-final")
            assert about.locator(":scope .b02r-layout > #etnika-studio-features.b02r-why").count()==1, "Advantages moved outside B02"
            assert page.locator("#etnika-review-flow > #etnika-studio-features").count()==0
            page.evaluate("""async () => {
                const imgs=[...document.querySelectorAll('#etnika-block-02-final .b02r-photo img')];
                imgs.forEach(i=>i.loading='eager'); await Promise.all(imgs.map(i=>i.decode()));
            }""")
            page.add_style_tag(content='#etnika-site-header,#etnika-brand-flight{visibility:hidden!important}')
            about.scroll_into_view_if_needed()
            about.screenshot(path=str(OUT/f"etnika-about-reference-{w}x{h}.png"))
            facts=about.evaluate("""a => {
                const box=e=>e.getBoundingClientRect().toJSON(), q=s=>a.querySelector(s);
                return {section:box(a),canvas:box(q('.b02r-canvas')),intro:box(q('.b02r-intro')),
                  why:box(q('#etnika-studio-features')),upper:box(q('.b02r-gallery-upper')),lower:box(q('.b02r-gallery-lower')),
                  title:parseFloat(getComputedStyle(q('.b02r-title')).fontSize),
                  whyTitle:parseFloat(getComputedStyle(q('#etnika-why-title')).fontSize),
                  images:[...a.querySelectorAll('.b02r-photo img')].map(i=>({src:i.getAttribute('src'),natural:i.naturalWidth,box:box(i)})),
                  background:getComputedStyle(a).backgroundColor,
                  details:a.querySelectorAll('.b02r-benefits details').length,
                  summaryDisplay:getComputedStyle(q('.b02r-benefits summary')).display,
                  body:[...a.querySelectorAll('.b02r-description p,.b02r-benefits summary,.b02r-benefits p')].map(e=>({size:parseFloat(getComputedStyle(e).fontSize),weight:getComputedStyle(e).fontWeight}))};
            }""")
            (OUT/f"etnika-about-reference-{w}x{h}.json").write_text(json.dumps(facts,ensure_ascii=False,indent=2))
            assert len(facts["images"])==6 and len({i["src"] for i in facts["images"]})==6
            assert facts["details"]==4 and facts["summaryDisplay"]=="grid"
            assert facts["background"]=="rgb(255, 255, 255)"
            assert abs(facts["title"]-facts["whyTitle"])<.1
            assert all(x["size"]==(18 if w>=761 else 16) and x["weight"]=="100" for x in facts["body"]),facts["body"]
            for image in facts["images"]:
                r=image["box"]; sec=facts["canvas"]
                assert image["natural"]>0 and r["width"]>0 and r["height"]>0
                assert r["left"]>=sec["left"]-1 and r["right"]<=sec["right"]+1
            if w>900:
                assert facts["intro"]["right"]<=facts["upper"]["left"]+1
                assert facts["why"]["right"]<=facts["lower"]["left"]+1
                assert abs(facts["why"]["top"]-facts["lower"]["top"])<=2
            else:
                assert facts["upper"]["top"]>=facts["intro"]["bottom"]-1
                assert facts["why"]["top"]>=facts["upper"]["bottom"]-1
                assert facts["lower"]["top"]>=facts["why"]["bottom"]-1
            benefits=about.locator(".b02r-benefits details")
            for item in benefits.all():
                item.locator("summary").click()
                assert item.get_attribute("open") is not None
                item.locator("summary").click()
            print(f"PASS About six-photo spread {w}x{h}",flush=True)
        except Exception as e:
            errors.append(f"{w}x{h}: {e}")
            print(f"FAIL {w}x{h}: {e}",flush=True)
        finally:
            page.close()
    browser.close()
    assert not errors,"; ".join(errors)
