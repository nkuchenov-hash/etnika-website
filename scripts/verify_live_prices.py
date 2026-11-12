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
        geometry = page.evaluate("""() => {
          const sel = s => document.querySelector(s);
          const r = el => el.getBoundingClientRect();
          const panel = sel('#etnika-prices-clear .ev3-sheet-panel');
          const scroll = sel('#etnika-prices-clear .ev3-sheet-scroll');
          const footer = sel('#etnika-prices-clear .ev3-sheet-footer');
          const features = sel('#etnika-prices-clear .ev3-feature-list');
          const backdrop = sel('#etnika-prices-clear .ev3-scrim');
          const prices = [...document.querySelectorAll('#etnika-prices-clear .ev3-plan-price')];
          const visiblePrices = prices.filter(el => {
            const b=r(el);
            return b.top>=0 && b.bottom<=innerHeight && b.left>=0 && b.right<=innerWidth;
          });
          const exposedPrices = visiblePrices.filter(el => {
            const b=r(el);
            const elAtPoint=document.elementFromPoint(b.left+b.width/2,b.top+b.height/2);
            return !!elAtPoint && !!elAtPoint.closest('.ev3-plan');
          });
          return {
            top:r(panel).top, left:r(panel).left, right:r(panel).right, bottom:r(panel).bottom,
            height:r(panel).height, panelWidth:r(panel).width,
            footerBottom:r(footer).bottom,
            scrollClientHeight:scroll.clientHeight, scrollHeight:scroll.scrollHeight,
            featureCount:features.children.length,
            backdropPointer:getComputedStyle(backdrop).pointerEvents,
            backdropOpacity:parseFloat(getComputedStyle(backdrop).opacity),
            priceRight:Math.max(...prices.map(el=>r(el).right)),
            visiblePriceCount:visiblePrices.length, exposedPriceCount:exposedPrices.length,
            ariaModal:sel('#etnika-prices-clear .ev3-sheet').getAttribute('aria-modal')
          };
        }""")
        assert abs(geometry["top"]) <= 2 and abs(geometry["bottom"]-height) <= 2, ("Tariff drawer is not full viewport height",geometry)
        assert abs(geometry["right"]-width) <= 2, ("Drawer not flush with screen right edge",geometry)
        assert geometry["footerBottom"] <= height+2, ("Drawer booking footer below viewport",geometry)
        assert geometry["scrollClientHeight"] > 0, ("Tariff features cannot scroll",geometry)
        assert geometry["featureCount"] == 10, ("Selected premium inclusions missing",geometry)
        if width >= 1101:
            assert geometry["left"] >= geometry["priceRight"]+16, ("Full-height drawer hides tariff prices",geometry)
            assert geometry["visiblePriceCount"] == geometry["exposedPriceCount"], ("Price is obstructed by drawer or overlay",geometry)
            assert geometry["backdropOpacity"] == 0 and geometry["backdropPointer"] == "none", ("Backdrop dims or blocks prices",geometry)
            assert geometry["ariaModal"] == "false", ("Non-modal right rail must preserve tariff access",geometry)
        else:
            assert geometry["backdropPointer"] != "none", ("Mobile backdrop cannot dismiss drawer",geometry)
            assert geometry["ariaModal"] == "true", ("Mobile fullscreen drawer needs modal semantics",geometry)
        page.screenshot(path=str(OUT / f"etnika-live-prices-details-{width}x{height}.png"),full_page=False)
        page.keyboard.press("Escape")
        assert page.locator('#etnika-prices-clear .ev3-sheet').get_attribute("data-open") == "false"
        page.close()
    browser.close()
