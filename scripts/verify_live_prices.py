#!/usr/bin/env python3
"""Check the actual published ETNIKA tariff section and save visual evidence."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "https://nkuchenov-hash.github.io/etnika-website/site/"
SHA = os.environ.get("GITHUB_SHA", "manual")[:12]
OUT = Path("reports")
OUT.mkdir(exist_ok=True)

MEASURE = """() => {
  const section = document.querySelector('#etnika-prices-clear.ev3');
  const header = document.getElementById('etnika-site-header');
  const query = s => section.querySelector(s);
  const rect = e => e.getBoundingClientRect().toJSON();
  const title = query('.ev3-title'), modes=query('.ev3-modes');
  const photo = query('.ev3-photo'), image = query('.ev3-visual');
  const overline = query('.ev3-overline'), stage = query('.ev3-stage');
  const plans = [...section.querySelectorAll('.ev3-plan')];
  const heading = rect(title), headerRect=rect(header);
  return {
    viewport: {width: innerWidth, height: innerHeight},
    pageWidth: document.documentElement.scrollWidth,
    section: rect(section), header: headerRect, overline: rect(overline),
    title: heading, modes:rect(modes), stage:rect(stage), image:rect(image),
    lineToHeading: heading.top - rect(overline).bottom,
    titleSize: parseFloat(getComputedStyle(title).fontSize),
    sharedTitleSize: parseFloat(getComputedStyle(document.querySelector('#etnika-stories h2.etnika-section-heading')).fontSize),
    beigeBottomGap: (() => {
      const beige=document.querySelector('#etnika-faq');
      return rect(beige).bottom - rect(beige.querySelector('.faq-shell')).bottom;
    })(),
    pricingTopGap: rect(overline).top - rect(section).top,
    titleFont: getComputedStyle(title).fontFamily,
    photoLoaded: photo.complete && photo.naturalWidth > 0,
    overlineVisible: getComputedStyle(overline).display !== 'none',
    overlineChildren: overline.children.length,
    rowHeights:plans.map(p => rect(p).height),
    planOpacity: plans.map(p => getComputedStyle(p).opacity),
    planPrices:plans.map(p => p.querySelector('.ev3-plan-price').innerText.trim()),
    footer:rect(query('.ev3-actions')),
    visualEndsInsideSection:rect(image).bottom <= rect(section).bottom - 20,
    navVisible: getComputedStyle(header.querySelector('.esh__nav')).display !== 'none'
  };
}"""

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    for width, height in ((1920, 1080), (1366, 768), (1200, 800), (390, 844)):
        page = browser.new_page(viewport={"width":width,"height":height}, device_scale_factor=1)
        page.goto(BASE + "?pricing-check=" + SHA, wait_until="domcontentloaded", timeout=50000)
        page.locator("#etnika-prices-clear.ev3[data-ev3-initialized=true]").wait_for(timeout=15000)
        page.evaluate("() => document.fonts.ready")
        if width > 1160:
            nav = page.locator('#etnika-site-header .esh__nav a[href="#etnika-prices-clear"]')
            nav.click()
            page.wait_for_timeout(1100)
        else:
            # Mobile tariff content is taller than the viewport; scroll to its TOP,
            # not the element centre (Playwright's default on oversized elements).
            page.evaluate("""() => {
              const el=document.getElementById('etnika-prices-clear');
              const header=document.getElementById('etnika-site-header');
              window.scrollTo({top:el.getBoundingClientRect().top+scrollY-header.getBoundingClientRect().height,
                behavior:'instant'});
            }""")
            page.wait_for_timeout(300)

        data = page.evaluate(MEASURE)
        print(f"{width}x{height}: {data}", flush=True)
        assert data["pageWidth"] <= width + 2, ("Horizontal overflow", data)
        assert data["photoLoaded"], ("Pricing photo not loaded", data)
        assert data["overlineVisible"] and data["overlineChildren"] == 6, ("Editorial top rule missing", data)
        assert data["lineToHeading"] >= 48, ("Editorial line is too close to tariff heading", data)
        assert "Forum" in data["titleFont"], ("Incorrect title font", data)
        assert abs(data["titleSize"] - data["sharedTitleSize"]) < 1, ("Tariff H2 differs from shared heading size", data)
        assert abs(data["pricingTopGap"] - data["beigeBottomGap"]) <= 3, ("Pricing upper inset does not match beige FAQ lower inset", data)
        assert all(x == "1" for x in data["planOpacity"]), ("Faded tariff labels", data)
        assert len(data["rowHeights"]) == 3, ("Missing packages", data)
        assert data["visualEndsInsideSection"], ("Photo extends below pricing section", data)
        if width > 1160:
            assert data["overline"]["top"] >= data["header"]["bottom"] + 6, ("Overline obscured by header", data)
            assert data["title"]["top"] >= data["header"]["bottom"] + 30, ("Title obscured by header", data)
            assert 380 <= data["stage"]["height"] <= 535, ("Tariff block height is unbalanced", data)
            assert data["section"]["height"] <= height + 40, ("Tariff section has unnecessary full-height padding", data)
            assert max(data["rowHeights"]) <= 180, ("Tariff rows are over-stretched", data)
            assert data["title"]["right"] + 10 < data["modes"]["left"] or (
                data["title"]["bottom"] <= data["modes"]["top"] - 4
            ), ("Heading overlaps weekday/weekend buttons", data)
        page.screenshot(path=str(OUT / f"etnika-live-prices-{width}x{height}.png"), full_page=False)
        page.locator('#etnika-prices-clear').screenshot(
            path=str(OUT / f"etnika-live-prices-section-{width}x{height}.png")
        )
        page.locator('#etnika-prices-clear .ev3-modes [data-mode="weekend"]').click()
        assert page.locator('#etnika-prices-clear .ev3-plan[data-plan="premium"] .ev3-plan-price').inner_text().strip() == "9 000 ₽"
        page.locator('#etnika-prices-clear .ev3-plan[data-plan="premium"]').click()
        page.locator('#etnika-prices-clear .ev3-details-open').click()
        page.wait_for_timeout(550)
        assert page.locator('#etnika-prices-clear .ev3-sheet').get_attribute("data-open") == "true"
        if width > 900:
            dock = page.evaluate("""() => {
              const r=s=>document.querySelector(s).getBoundingClientRect();
              let panel=r('#etnika-prices-clear .ev3-sheet-panel');
              let photo=r('#etnika-prices-clear .ev3-visual');
              let prices=[...document.querySelectorAll('#etnika-prices-clear .ev3-plan-price')].map(e=>e.getBoundingClientRect());
              return {panelLeft:panel.left, panelRight:panel.right, photoLeft:photo.left, photoRight:photo.right,
                priceRight:Math.max(...prices.map(x=>x.right))};
            }""")
            assert dock["panelLeft"] >= dock["priceRight"] + 4, ("Details cover price column",dock)
            assert abs(dock["panelLeft"] - dock["photoLeft"]) <= 4, ("Details not aligned with photo",dock)
        page.screenshot(path=str(OUT / f"etnika-live-prices-details-{width}x{height}.png"),full_page=False)
        page.keyboard.press("Escape")
        assert page.locator('#etnika-prices-clear .ev3-sheet').get_attribute("data-open") == "false"
        page.close()
    browser.close()
