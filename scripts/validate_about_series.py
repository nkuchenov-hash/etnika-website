#!/usr/bin/env python3
"""Visual and geometric QA of the complete original-photo About spread."""
from pathlib import Path
import shutil,sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"; OUT.mkdir(exist_ok=True)
URL="https://nkuchenov-hash.github.io/etnika-website/site/?v=c911bd94" if "--live" in sys.argv else (ROOT/"site/index.html").as_uri()
chrome=shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path=chrome)
    errors=[]
    for w,h in [(1600,900),(1366,768),(1920,1080),(2560,1080),(390,844)]:
        page=browser.new_page(viewport={"width":w,"height":h},device_scale_factor=1)
        try:
            page.goto(URL,wait_until="domcontentloaded",timeout=45000)
            page.wait_for_function("() => !!document.querySelector('#etnika-block-02-final .etnika-editorial-why')")
            page.evaluate("() => document.fonts.ready")
            about=page.locator("#etnika-block-02-final")
            page.evaluate("""async () => {
              const imgs=[...document.querySelectorAll('#etnika-block-02-final .etnika-spread-photo img')];
              imgs.forEach(i=>i.loading='eager');await Promise.all(imgs.map(i=>i.decode()));
            }""")
            about.scroll_into_view_if_needed()
            # Hide fixed chrome in the full-section screenshot only; leave layout unchanged.
            page.add_style_tag(content='#etnika-site-header,#etnika-brand-flight{visibility:hidden!important}')
            about.screenshot(path=str(OUT/f"etnika-why-series-{w}x{h}.png"))
            facts=page.evaluate("""() => {
                const a=document.querySelector('#etnika-block-02-final');
                const box=e=>e.getBoundingClientRect().toJSON();
                const copy=a.querySelector('.etnika-about-intro'),why=a.querySelector('#etnika-studio-features');
                const d=getComputedStyle(a.querySelector('.etnika-b02__description'));
                return {section:box(a),copy:box(copy),why:box(why),kicker:box(a.querySelector('.etnika-about-kicker')),heading:box(a.querySelector('.etnika-b02__title')),mosaic:box(a.querySelector('.etnika-about-mosaic')),tableCount:a.querySelectorAll('.etnika-b02__features').length,
                  bodySize:parseFloat(d.fontSize),bodyWeight:d.fontWeight,font:d.fontFamily,
                  lines:[...a.querySelectorAll('.etnika-title-line')].map(e=>{const r=document.createRange();r.selectNodeContents(e);return {box:r.getBoundingClientRect().toJSON(),count:r.getClientRects().length}}),
                  images:[...a.querySelectorAll('.etnika-spread-photo img')].map(i=>({src:i.getAttribute('src'),width:i.naturalWidth,height:i.naturalHeight,box:box(i)})),
                  background:getComputedStyle(a).backgroundColor,pageWidth:document.documentElement.scrollWidth
                };
            }""")
            print(f"ABOUT {w}x{h}: {facts}",flush=True)
            assert len(facts["images"])==8 and len({i["src"] for i in facts["images"]})==8
            assert all(i["width"]>0 and i["box"]["width"]>0 for i in facts["images"])
            for i in facts["images"]:
                r=i["box"]
                assert abs(r["width"]/r["height"]-i["width"]/i["height"])<.02,i
                assert r["left"]>=-1 and r["right"]<=w+1,i
            assert facts["background"]=="rgb(255, 255, 255)"
            assert facts["pageWidth"]<=w+2
            assert facts["why"]["top"]>facts["copy"]["bottom"]+40
            assert facts["tableCount"]==0
            assert facts["heading"]["top"]-facts["kicker"]["bottom"]>=29
            if w>1100:
                assert all(line["count"]==1 and line["box"]["right"]<=facts["copy"]["right"]+2 for line in facts["lines"]),facts["lines"]
                assert facts["images"][0]["box"]["width"]>facts["images"][1]["box"]["width"]*1.4
                assert facts["images"][3]["box"]["width"]>facts["images"][2]["box"]["width"]*1.4
                assert facts["mosaic"]["left"]>facts["copy"]["right"]
                assert abs(facts["copy"]["left"]-(w-facts["mosaic"]["right"]))<3 or w>2300
                assert facts["why"]["top"]-facts["copy"]["bottom"]<161
                assert facts["bodySize"]==18 and facts["bodyWeight"]=="100" and "Geologica" in facts["font"]
            benefits=about.locator(".etnika-editorial-benefits details")
            assert benefits.count()==6
            benefits.first.locator("summary").click()
            assert benefits.first.get_attribute("open") is not None
            benefits.first.locator("summary").click()
            print(f"PASS About editorial {w}x{h}",flush=True)
        except Exception as e:
            errors.append(f"{w}x{h}: {e}")
            print(f"FAIL {w}x{h}: {e}",flush=True)
        finally:
            page.close()
    browser.close()
    assert not errors,"; ".join(errors)
