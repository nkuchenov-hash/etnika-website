#!/usr/bin/env python3
"""Check the actual About block against the supplied 766px-wide reference geometry."""
from pathlib import Path
import shutil, sys, json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"; OUT.mkdir(exist_ok=True)
URL="https://nkuchenov-hash.github.io/etnika-website/site/?v=a64fc3a0" if "--live" in sys.argv else (ROOT/"site/index.html").as_uri()
chrome=shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
# Reference coordinates relative to white section's top-left (50,30).
REFERENCE=[(426,39,202,237),(647,117,92,138),(376,298,140,143),(537,298,202,271)]
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path=chrome)
    errors=[]
    for w,h in [(766,685),(1366,768),(1600,900),(1920,1080),(2560,1080),(390,844)]:
        page=browser.new_page(viewport={"width":w,"height":h},device_scale_factor=1)
        try:
            page.goto(URL,wait_until="domcontentloaded",timeout=45000)
            page.wait_for_function("() => !!document.querySelector('#etnika-review-flow > #etnika-block-02-final')")
            page.evaluate("() => document.fonts.ready")
            about=page.locator("#etnika-block-02-final")
            page.evaluate("""async () => {
                const imgs=[...document.querySelectorAll('#etnika-block-02-final .etnika-spread-photo img')];
                imgs.forEach(i=>i.loading='eager'); await Promise.all(imgs.map(i=>i.decode()));
            }""")
            page.add_style_tag(content='#etnika-site-header,#etnika-brand-flight{visibility:hidden!important}')
            about.scroll_into_view_if_needed()
            about.screenshot(path=str(OUT/f"etnika-about-reference-{w}x{h}.png"))
            facts=about.evaluate("""a => {
                const box=e=>e.getBoundingClientRect().toJSON();
                return {section:box(a),intro:box(a.querySelector('.etnika-about-intro')),
                  why:box(a.querySelector('#etnika-studio-features')),
                  title:parseFloat(getComputedStyle(a.querySelector('.etnika-b02__title')).fontSize),
                  whyTitle:parseFloat(getComputedStyle(a.querySelector('#etnika-why-title')).fontSize),
                  images:[...a.querySelectorAll('.etnika-spread-photo img')].map(i=>({src:i.getAttribute('src'),natural:i.naturalWidth,box:box(i)})),
                  background:getComputedStyle(a).backgroundColor,pageWidth:document.documentElement.scrollWidth,
                  details:a.querySelectorAll('.etnika-editorial-benefits details').length};
            }""")
            assert len(facts["images"])==4 and len({i["src"] for i in facts["images"]})==4
            assert facts["details"]==4
            assert facts["background"]=="rgb(255, 255, 255)"
            assert facts["pageWidth"]<=w+2
            assert abs(facts["title"]-facts["whyTitle"])<.1
            sec=facts["section"]
            deltas=[]
            for image, target in zip(facts["images"],REFERENCE):
                r=image["box"]
                assert image["natural"]>0 and r["width"]>0 and r["height"]>0
                assert r["left"]>=sec["left"]-1 and r["right"]<=sec["right"]+1
                if w>700:
                    k=sec["width"]/766
                    actual=(r["x"]-sec["x"],r["y"]-sec["y"],r["width"],r["height"])
                    delta=[round(v-t*k,2) for v,t in zip(actual,target)]
                    deltas.append(delta)
                    # Column placement is quantized to 1% of section width.
                    assert abs(delta[0])<=sec["width"]*.011+1,delta
                    assert abs(delta[2])<=sec["width"]*.011+1,delta
                    assert abs(delta[3])<=sec["width"]*.018+1,delta
                    assert abs(delta[1])<=sec["width"]*.025+1,delta
            print(f"ABOUT {w}x{h}: photo geometry deltas in CSS pixels {deltas}",flush=True)
            (OUT/f"etnika-about-reference-{w}x{h}.json").write_text(json.dumps({"facts":facts,"photo_pixel_deltas":deltas},ensure_ascii=False,indent=2))
            benefits=about.locator(".etnika-editorial-benefits details")
            benefits.first.locator("summary").click()
            assert benefits.first.get_attribute("open") is not None
            benefits.first.locator("summary").click()
            print(f"PASS About reference {w}x{h}",flush=True)
        except Exception as e:
            errors.append(f"{w}x{h}: {e}")
            print(f"FAIL {w}x{h}: {e}",flush=True)
        finally:
            page.close()
    browser.close()
    assert not errors,"; ".join(errors)
