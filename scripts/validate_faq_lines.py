#!/usr/bin/env python3
"""Regression for the owner-marked FAQ lines and symmetrical outer spacing."""
import json
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / "site/index.html").as_uri()
OUT = ROOT / "reports"
OUT.mkdir(exist_ok=True)

MEASURE = r"""() => {
  const section = document.querySelector('#etnika-review-flow > section#etnika-faq');
  if (!section) throw new Error('FAQ must be inside the production review flow');
  const top = section.querySelector('.faq-topline');
  const shell = section.querySelector('.faq-shell');
  const main = section.querySelector('.faq-main');
  const firstBorder = section.querySelector('.faq-list');
  const lastBorder = section.querySelector('.faq-item:last-child');
  if (![top, shell, main, firstBorder, lastBorder].every(Boolean)) throw new Error('Missing FAQ geometry element');
  const sr = section.getBoundingClientRect();
  const tr = top.getBoundingClientRect();
  const sh = shell.getBoundingClientRect();
  const mr = main.getBoundingClientRect();
  const rule = getComputedStyle(shell,'::after');
  const mainStyle = getComputedStyle(main);
  return {
    topGap: (tr.top + tr.height / 2) - sr.top,
    bottomGap: sr.bottom - sh.bottom + 0.5,
    lowerSeparation: sh.bottom - mr.bottom,
    topColor: getComputedStyle(top).backgroundColor,
    topOpacity: getComputedStyle(top).opacity,
    bottomColor: rule.backgroundColor,
    bottomOpacity: rule.opacity,
    upperStroke: {x: (tr.left + tr.width / 2) - sr.left, y: (tr.top + tr.height / 2) - sr.top},
    lowerStroke: {x: (sh.left + sh.width / 2) - sr.left, y: (sh.bottom - 0.5) - sr.top},
    bottomRuleHeight: rule.height,
    bottomRuleContent: rule.content,
    firstBorderWidth: getComputedStyle(firstBorder).borderTopWidth,
    lastBorderWidth: getComputedStyle(lastBorder).borderBottomWidth,
    faqBottom: sr.bottom,
    mainDisplay: mainStyle.display,
    sectionHeight: sr.height
  };
}"""

def darkest_rendered_pixel(image, position):
    """Compare pixels actually painted by Chromium, not just CSS declarations."""
    x = max(0, min(image.width - 1, round(position["x"])))
    y = round(position["y"])
    pixels = [image.getpixel((x, yy)) for yy in range(max(0, y - 3), min(image.height, y + 4))]
    return min(pixels, key=sum)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for name, width, height in (("desktop", 2048, 1093), ("laptop", 1280, 800), ("phone", 390, 844)):
        page = browser.new_page(viewport={"width":width, "height":height}, device_scale_factor=1)
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_selector("#etnika-review-flow > section#etnika-faq", timeout=15000)
            section = page.locator("#etnika-review-flow > section#etnika-faq")
            section.scroll_into_view_if_needed(timeout=15000)
            m = page.evaluate(MEASURE)
            capture = OUT / f"etnika-faq-lines-{name}.png"
            section.screenshot(path=str(capture), timeout=30000)
            with Image.open(capture) as snapshot:
                top_pixel = darkest_rendered_pixel(snapshot.convert("RGB"), m["upperStroke"])
                bottom_pixel = darkest_rendered_pixel(snapshot.convert("RGB"), m["lowerStroke"])
            print(f"{name}: {json.dumps(m, ensure_ascii=False)}; rendered top={top_pixel}, bottom={bottom_pixel}")
            assert max(abs(a-b) for a, b in zip(top_pixel, bottom_pixel)) <= 8, (
                f"{name}: bottom rule visually differs from top: {bottom_pixel} vs {top_pixel}"
            )
            assert m["topColor"] == m["bottomColor"], f"{name}: mismatched gray strokes"
            assert m["firstBorderWidth"] == "0px", f"{name}: first crossed-out stroke still visible"
            assert m["lastBorderWidth"] == "0px", f"{name}: last crossed-out stroke still visible"
            assert m["bottomRuleContent"] not in ("none", "normal"), f"{name}: no independent lower rule"
            assert m["bottomRuleHeight"] == "1px", f"{name}: bottom line must be a 1px hairline"
            assert abs(m["topGap"] - m["bottomGap"]) < 3, f"{name}: uneven upper/lower whitespace"
            assert m["lowerSeparation"] >= 25, f"{name}: last question too close to lower rule"
        finally:
            page.close()
    browser.close()
print("FAQ line and spacing checks: PASS")
