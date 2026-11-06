#!/usr/bin/env python3
"""ETNIKA B-08: verify tariff menu appearance, interaction, and shared heading scale."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["site/index.html", "site/review-2026-11.html"]
VIEWPORTS = [(1920, 1080), (1662, 896), (1366, 768), (390, 844), (375, 667)]
OUT = ROOT / "reports"
OUT.mkdir(exist_ok=True)

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    for source in PAGES:
        for width, height in VIEWPORTS:
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            page.goto((ROOT / source).as_uri(), wait_until="domcontentloaded", timeout=45000)
            page.evaluate("() => document.fonts.ready")
            block = page.locator("#etnika-prices-clear")
            block.scroll_into_view_if_needed()
            data = page.evaluate("""() => {
                const q = s => document.querySelector('#etnika-prices-clear ' + s);
                const rect = s => q(s).getBoundingClientRect().toJSON();
                const headline = q('.pc-title');
                const measure = document.createElement('span');
                measure.style.fontSize = 'var(--etnika-section-title)';
                document.body.appendChild(measure);
                const expectedTitleSize = parseFloat(getComputedStyle(measure).fontSize);
                measure.remove();
                const price = q('.pc-tab.is-active .pc-tab-price');
                const tabs = [...document.querySelectorAll('#etnika-prices-clear .pc-tab')];
                return {
                  width: window.innerWidth,
                  documentWidth: document.documentElement.scrollWidth,
                  heading: rect('.pc-title'),
                  tabs: rect('.pc-tabs'),
                  main: rect('.pc-main'),
                  photo: rect('.pc-photo'),
                  actions: rect('.pc-buy'),
                  block: rect('.pc-shell'),
                  titleSize: parseFloat(getComputedStyle(headline).fontSize),
                  expectedTitleSize,
                  fontFamily: getComputedStyle(headline).fontFamily,
                  tabPrices: tabs.map(t=>t.querySelector('.pc-tab-price').textContent.trim()),
                  activePrice: price.textContent.trim(),
                  photoLoaded: q('.pc-photo img').complete && q('.pc-photo img').naturalWidth > 0,
                  photoFit: getComputedStyle(q('.pc-photo img')).objectFit,
                  tabBackground: getComputedStyle(q('.pc-tab.is-active')).backgroundColor
                };
            }""")
            error = lambda msg: f"{source} {width}x{height}: {msg}: {data}"
            assert abs(data["titleSize"]-data["expectedTitleSize"]) < 1.0, error("title token overridden")
            assert "Forum" in data["fontFamily"], error("wrong heading font")
            assert data["documentWidth"] <= width+2, error("horizontal overflow")
            assert data["tabs"]["top"] >= data["heading"]["bottom"]-2, error("title overlaps tariff rows")
            assert data["photo"]["width"] > 200 and data["photo"]["height"] > 180, error("photo collapsed")
            assert data["photoLoaded"], error("photo not loaded")
            assert data["photoFit"] == "cover", error("image must use existing source without forced zoom")
            assert len(data["tabPrices"]) == 3, error("missing tariff")
            assert data["tabPrices"] == ["2 900 ₽", "4 500 ₽", "7 500 ₽"], error("weekday prices altered")
            assert data["activePrice"] == "4 500 ₽", error("wrong initial tariff")
            assert data["tabBackground"] != "rgb(169, 21, 29)", error("red card fill returned")
            page.screenshot(path=str(OUT / f"etnika-tariffs-{Path(source).stem}-{width}x{height}.png"))
            page.locator('.pc-mode-btn[data-mode="weekend"]').click()
            assert page.locator('.pc-tab[data-plan="standard"] .pc-tab-price').inner_text().strip() == "5 900 ₽", error("weekend switch failed")
            page.locator('.pc-tab[data-plan="premium"]').click()
            assert page.locator('.pc-tab[data-plan="premium"] .pc-tab-price').inner_text().strip() == "9 000 ₽", error("premium weekend price")
            page.locator('.pc-inclusions-open').click()
            assert page.locator(".pc-inclusions-dialog").evaluate("(el) => el.open"), error("details did not open")
            assert page.locator(".pc-inclusions-dialog .pc-features li").count() == 10, error("premium inclusions lost")
            page.keyboard.press("Escape")
            assert not page.locator(".pc-inclusions-dialog").evaluate("(el) => el.open"), error("dialog not dismissed")
            page.locator('.pc-tab[data-plan="express"]').click()
            page.locator('.pc-inclusions-open').click()
            assert page.locator(".pc-inclusions-dialog .pc-features li").count() == 6, error("express inclusions lost")
            page.locator('.pc-inclusions-close').click()
            print(f"PASS {source} {width}x{height}: heading {data['titleSize']:.1f}px, photo {data['photo']['width']:.0f}x{data['photo']['height']:.0f}; toggles, booking and modal")
            page.close()
    browser.close()
