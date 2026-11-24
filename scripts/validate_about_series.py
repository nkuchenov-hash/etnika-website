#!/usr/bin/env python3
"""Regression: B02 remains a single editorial spread after all page scripts run."""
from pathlib import Path
import shutil, sys, json, re, time, os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"; OUT.mkdir(exist_ok=True)
LIVE="--live" in sys.argv
EXPECTED=re.search(r'<meta name="etnika-build" content="([^"]+)"', (ROOT/"site/index.html").read_text()).group(1)
URL="https://nkuchenov-hash.github.io/etnika-website/site/" if LIVE else (ROOT/"site/index.html").as_uri()
chrome=shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path=chrome)
    errors=[]
    for w,h in [(766,685),(1366,768),(1600,900),(1920,1080),(2560,1080),(390,844),(375,667)]:
        page=browser.new_page(viewport={"width":w,"height":h},device_scale_factor=1)
        try:
            for attempt in range(12 if LIVE else 1):
                target=URL+f"?build={EXPECTED}&run={os.getenv('GITHUB_RUN_ID','local')}&attempt={attempt}" if LIVE else URL
                page.goto(target,wait_until="load",timeout=45000)
                actual=page.locator('meta[name="etnika-build"]').get_attribute("content")
                print(f"Expected build {EXPECTED}; received {actual}",flush=True)
                if actual==EXPECTED: break
                if not LIVE or attempt==11: raise AssertionError(f"Wrong deployed build: {actual}, expected {EXPECTED}")
                time.sleep(3)
            page.evaluate("() => document.fonts.ready")
            about=page.locator("#etnika-block-02-final")
            assert about.locator(".etnika-about-left > #etnika-studio-features").count()==1
            assert page.locator("#etnika-review-flow > #etnika-studio-features").count()==0
            assert about.locator(".etnika-b02__description p").count()==2
            assert about.locator(".etnika-b02__feature").count()==4
            assert about.locator(".etnika-editorial-benefits details").count()==6
            assert about.locator(".etnika-editorial-metrics strong").count()==3
            assert about.locator(".etnika-spread-photo img").count()==4
            assert about.locator(".bp-photo-toggle").count()==0
            facts=page.evaluate("""() => {
                const q=s=>document.querySelector(s), r=e=>e.getBoundingClientRect();
                const layout=r(q('#etnika-block-02-final .etnika-about-layout'));
                const ref=r(q('#etnika-space-photo .spf-shell'));
                const kicker=q('#etnika-block-02-final .etnika-about-kicker');
                const title=q('#etnika-block-02-final .etnika-about-intro .etnika-b02__title');
                const probe=document.createElement('div');
                probe.style.cssText='position:absolute;height:var(--etnika-editorial-heading-gap);width:0';
                document.body.append(probe);const target=r(probe).height;probe.remove();
                const why=q('#etnika-why-title'), a=getComputedStyle(title), b=getComputedStyle(why);
                const sameTypography=['fontFamily','fontSize','fontWeight','lineHeight','letterSpacing','textTransform'].every(k=>a[k]===b[k]);
                const spaceTop=q('#etnika-space-photo .spf-top'), spaceTitle=q('#etnika-space-photo .spf-title');
                return {sameTypography,left:layout.left,right:layout.right,refLeft:ref.left,refRight:ref.right,
                  headingGap:r(title).top-r(kicker).bottom,referenceHeadingGap:r(spaceTitle).top-r(spaceTop).bottom,
                  sharedGap:target,kickerMargin:parseFloat(getComputedStyle(kicker).marginBottom),
                  body:[...document.querySelectorAll('#etnika-block-02-final .etnika-b02__description p,#etnika-block-02-final .etnika-editorial-benefits p,#etnika-block-02-final .etnika-editorial-benefits summary,#etnika-block-02-final .etnika-b02__feature')].map(e=>({size:parseFloat(getComputedStyle(e).fontSize),weight:getComputedStyle(e).fontWeight})),
                  images:[...document.querySelectorAll('#etnika-block-02-final .etnika-spread-photo img')].map(e=>e.getAttribute('src'))};
            }""")
            print(json.dumps(facts,ensure_ascii=False),flush=True)
            (OUT/f"etnika-about-reference-{w}x{h}.json").write_text(json.dumps(facts,ensure_ascii=False,indent=2))
            page.add_style_tag(content='#etnika-site-header,#etnika-brand-flight{visibility:hidden!important}')
            page.evaluate("""async () => {
                const imgs=[...document.querySelectorAll('#etnika-block-02-final .etnika-spread-photo img')];
                imgs.forEach(i=>i.loading='eager'); await Promise.all(imgs.map(i=>i.decode()));
            }""")
            about.screenshot(path=str(OUT/f"etnika-about-reference-{w}x{h}.png"))
            assert abs(facts["left"]-facts["refLeft"])<=2 and abs(facts["right"]-facts["refRight"])<=2, facts
            assert abs(facts["headingGap"]-facts["sharedGap"])<=2, facts
            assert abs(facts["kickerMargin"]-facts["sharedGap"])<=2, facts
            assert len(set(facts["images"]))==4
            assert facts["sameTypography"], facts
            assert all(x["size"]==(18 if w>=761 else 16) for x in facts["body"]), facts["body"]
            print(f"PASS shared B02 width and heading gap {w}x{h}",flush=True)
        except Exception as e:
            errors.append(f"{w}x{h}: {e}")
            print(f"FAIL {w}x{h}: {e}",flush=True)
        finally:
            page.close()
    browser.close()
    assert not errors,"; ".join(errors)
