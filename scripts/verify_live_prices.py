#!/usr/bin/env python3
"""Verify the integrated V24 tariff block on the published main site."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "https://nkuchenov-hash.github.io/etnika-website/site/"
SHA = os.environ.get("GITHUB_SHA", "manual")[:12]
OUT = Path("reports")
OUT.mkdir(exist_ok=True)
BOOKING = "https://n1268189.yclients.com/"

def number(text):
    return int("".join(c for c in text if c.isdigit()))

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    for width, height in ((1920,1080),(1366,768),(1200,800),(390,844)):
        page = browser.new_page(viewport={"width":width,"height":height},device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE + "?pricing-check=" + SHA,wait_until="domcontentloaded",timeout=50000)
        section = page.locator('#etnika-prices-clear[data-tariff-build="anna-v24"]')
        host = section.locator('#etnika-tariff-host[data-initialized="true"]')
        host.wait_for(timeout=15000)
        page.evaluate("() => document.fonts.ready")
        page.evaluate("""() => {
          const e=document.getElementById('etnika-prices-clear');
          const h=document.getElementById('etnika-site-header');
          window.scrollTo({top:e.getBoundingClientRect().top+scrollY-(h?h.getBoundingClientRect().height:0),behavior:'instant'});
        }""")
        page.wait_for_timeout(350)
        assert host.locator('[data-set-choice]').count()==7
        assert number(host.locator('#set-total').inner_text())==3500
        assert host.locator('#set-book').get_attribute('href')==BOOKING
        assert page.evaluate("document.documentElement.scrollWidth") <= width+2
        page.screenshot(path=str(OUT/f"etnika-live-prices-{width}x{height}.png"))
        section.screenshot(path=str(OUT/f"etnika-live-prices-section-{width}x{height}.png"))
        def geometry():
            return host.evaluate("""e=>{
              const r=e.shadowRoot,p=r.querySelector('.stage:not([hidden])'),b=p.querySelector('.order a').getBoundingClientRect(),
                h=e.getBoundingClientRect(),t=r.querySelector('.tariff-title').getBoundingClientRect();
              return {left:b.left,width:b.width,top:b.top-h.top,titleLeft:t.left};
            }""")
        first = geometry()
        host.locator('[data-format="base"]').click()
        page.wait_for_timeout(200)
        second = geometry()
        assert abs(first["titleLeft"]-second["titleLeft"])<=2, (first,second)
        if width>1000:
            assert abs(first["left"]-second["left"])<=2 and abs(first["width"]-second["width"])<=2, (first,second)
            assert abs(first["top"]-second["top"])<=3, (first,second)
        assert host.locator('[data-bg]').count()==4
        host.locator('[data-bg="Белый"]').click()
        assert number(host.locator('#total').inner_text())==5000
        host.locator('[data-min="90"]').click()
        assert number(host.locator('#total').inner_text())==9000
        host.locator('[data-day="weekend"]').click()
        assert number(host.locator('#total').inner_text())==11000
        assert "90 минут" in host.locator('#selected-bg-meta').inner_text()
        assert host.locator('#book').get_attribute('href')==BOOKING
        for img in host.locator('#base-panel img').all():
            img.evaluate("e=>e.decode()")
            assert img.evaluate("e=>e.complete && e.naturalWidth>0")
        section.screenshot(path=str(OUT/f"etnika-live-prices-background-{width}x{height}.png"))
        host.locator('#base-panel details summary').click()
        assert host.locator('#base-panel details').get_attribute('open') is not None
        assert host.locator('#base-panel details li').count()==13
        host.locator('#base-panel details summary').click()
        host.locator('[data-format="set"]').click()
        assert number(host.locator('#set-total').inner_text())==4200
        host.locator('[data-set-choice="5"]').click()
        assert number(host.locator('#set-total').inner_text())==20000
        host.locator('#set-panel details summary').click()
        assert host.locator('#set-panel details').get_attribute('open') is not None
        assert host.locator('#set-panel details li').count()>0
        assert not errors, errors
        print(f"{width}x{height}: tariff formats, pricing, booking, inclusions and geometry passed",flush=True)
        page.close()
    browser.close()
