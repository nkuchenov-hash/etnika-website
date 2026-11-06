#!/usr/bin/env python3
"""ETNIKA header and shared editorial overline regression checks."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
FILES=[ROOT/"site/index.html",ROOT/"site/review-2026-11.html"]

def static():
    for path in FILES:
        s=path.read_text(encoding="utf-8")
        assert s.count('id="etnika-site-header"')==1,(path,"missing or duplicate site navigation")
        assert 'id="etnika-header-interaction-20261105"' in s
        assert 'id="etnika-brand-flight"' in s
        assert 'class="esh__descriptor">Студия автопортрета</span>' in s
        assert 'href="#etnika-prices-clear"' in s
        assert 'href="#etnika-gift"' in s
        assert 'href="#etnika-contacts-source"' in s
        assert 'href="https://etnika-studio.ru/otkryt-studiyu-avtoportreta"' in s
        assert 'href="https://n1268189.yclients.com/"' in s
        assert '--etnika-overline-size:clamp(9px,.62vw,11px)' in s
        assert '--etnika-overline-size:8px' in s
        assert s.count('font-size:var(--etnika-overline-size);')==6
        assert 'font-size:var(--etnika-overline-size)!important' in s
        assert 'font-size:var(--etnika-text-size)!important;font-weight:300!important;letter-spacing:.055em' not in s, "oversized studio kicker returned"
    # Separate preview work may intentionally touch other blocks; require only shared navigation parity.
    import re
    docs=[p.read_text(encoding="utf-8") for p in FILES]
    for pattern in (
        r'<header id="etnika-site-header"[\\s\\S]*?</header>',
        r'<style id="etnika-header-design-system-20261105">[\\s\\S]*?</style>',
        r'<script id="etnika-header-interaction-20261105">[\\s\\S]*?</script>'
    ):
        fragments=[re.search(pattern,html) for html in docs]
        assert all(fragments), "Missing common site header"
        assert fragments[0].group(0)==fragments[1].group(0), "Working and preview navigation diverged"
    print("PASS: both pages contain consistent navigation, logo transition, and shared kicker type")

def render():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        for path in FILES:
            for width,height in [(1920,1080),(1662,896),(1366,768),(390,844),(375,667)]:
                page=browser.new_page(viewport={"width":width,"height":height})
                page.goto(path.as_uri(),wait_until="domcontentloaded")
                header=page.locator("#etnika-site-header")
                hero=page.locator("#etnika-hero")
                assert header.count()==1
                page.evaluate("window.scrollTo(0,0)")
                page.wait_for_timeout(80)
                assert header.get_attribute("data-hero")=="true",(path,width,"hero mode")
                assert page.locator(".esh__descriptor").is_visible()
                assert page.locator(".esh__logo").evaluate("(el)=>getComputedStyle(el).opacity")=="0"
                before=page.evaluate("""() => ({
                    space:parseFloat(getComputedStyle(document.querySelector('#etnika-space-photo .spf-top')).fontSize),
                    other:parseFloat(getComputedStyle(document.querySelector('#etnika-stories .stories-top')).fontSize),
                    heading:getComputedStyle(document.querySelector('#etnika-space-photo .spf-title')).fontFamily
                })""")
                assert abs(before["space"]-before["other"])<0.25,(path,width,"mismatched editorial overlines",before)
                assert "Forum" in before["heading"]
                if width<=1160:
                    toggle=page.locator(".esh__toggle")
                    assert toggle.is_visible()
                    toggle.click()
                    assert toggle.get_attribute("aria-expanded")=="true"
                    assert page.locator("#etnika-mobile-nav").is_visible()
                    page.keyboard.press("Escape")
                    assert toggle.get_attribute("aria-expanded")=="false"
                else:
                    assert page.locator(".esh__nav").is_visible()
                    assert page.locator(".esh__booking").is_visible()
                    assert page.locator(".esh__nav").evaluate("(el)=>el.scrollWidth<=el.clientWidth+2"),(path,width,"desktop nav overflows")
                page.evaluate("window.scrollTo({top:document.getElementById('etnika-hero').offsetHeight + 100,behavior:'instant'})")
                page.wait_for_timeout(400)
                assert header.get_attribute("data-hero")=="false",(path,width,"header did not acquire logo")
                assert page.locator(".esh__logo").evaluate("(el)=>getComputedStyle(el).opacity")=="1"
                assert page.locator("#etnika-brand-flight").evaluate("(el)=>getComputedStyle(el).display")=="none"
                page.close()
                print(f"PASS: {path.name} {width}x{height}: nav, logo switch and matching editorial type")
        browser.close()

if __name__=="__main__":
    static()
    if "--render" in sys.argv:
        render()
