#!/usr/bin/env python3
"""ETNIKA B-06: working/preview consistency, design tokens, and browser geometry."""
from __future__ import annotations
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = (ROOT / "site/index.html", ROOT / "site/review-2026-11.html")
SPACE_SECTION = re.compile(r'<section id="etnika-space-photo"\b[\s\S]*?</section>')
SPACE_CSS = re.compile(r'<style id="etnika-space-owner-corrections-20261105">[\s\S]*?</style>')
SHARED_CSS = re.compile(r'<style id="etnika-v19-spacing-and-type-lock">[\s\S]*?</style>')
FORBIDDEN = "Просторный зал, профессиональный свет, лаунж-зона, большое зеркало и реквизит"
HEADLINE = '<h2 class="spf-title">Пространство <span class="red">ЭТНИКА</span></h2>'


def static_checks():
    sections, styles = [], []
    for path in FILES:
        html = path.read_text(encoding="utf-8")
        section = SPACE_SECTION.search(html)
        style = SPACE_CSS.search(html)
        shared = SHARED_CSS.search(html)
        assert section and style and shared, f"{path}: studio/shared design system missing"
        part = section.group(0)
        css = style.group(0)
        shared_code = shared.group(0)
        assert FORBIDDEN not in html, f"{path}: removed description has returned"
        assert HEADLINE in part, f"{path}: heading is missing"
        assert part.count('class="spf-img ') == 3, f"{path}: expected 3 original photos"
        assert part.count('class="spf-tab') == 5, f"{path}: expected 5 selectable categories"
        assert "height:calc(100svh - var(--etnika-nav-height,72px))!important" in css, f"{path}: fixed header not subtracted from viewport"
        assert "grid-template-rows:auto auto minmax(0,1fr) auto!important" in css, f"{path}: photos do not get remaining height"
        assert "padding:var(--etnika-photo-section-y) 0!important" in css, f"{path}: not using shared photo-section spacing"
        assert "font-size:var(--etnika-section-title)!important" in css, f"{path}: rogue title size"
        assert "font-family:var(--etnika-font-display)!important" in css, f"{path}: display font not using token"
        assert "font-family:var(--etnika-font-ui)!important" in css, f"{path}: UI font not using token"
        assert "--etnika-text-size:16px" in shared_code, f"{path}: min UI text size token missing"
        assert "--etnika-section-title:clamp(62px,6.25vw,118px)" in shared_code
        assert "--etnika-photo-section-y:clamp(20px,3.1svh,34px)" in html, f"{path}: photo-section spacing token missing"
        assert "etnika-space-title-fit-20261104" not in html, f"{path}: distorted scaleX title script returned"
        assert "11svh" not in css, f"{path}: local font shrinking returned"
        sections.append(part)
        styles.append(css)
    assert sections[0] == sections[1], "Working and staging studio sections diverged"
    assert styles[0] == styles[1], "Working and staging studio styles diverged"
    print("PASS: identical B-06 in both pages, original 3 photos and 5 tabs, no intro, shared font and spacing tokens")


def render_checks():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise SystemExit("Install playwright and its Chromium browser to run --render") from e
    sizes = [(1920,1080), (1662,896), (1366,768), (1100,800), (390,844), (375,667)]
    output = ROOT / "reports"
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for path in FILES:
            for w,h in sizes:
                page = browser.new_page(viewport={"width":w,"height":h}, device_scale_factor=1)
                page.goto(path.as_uri(), wait_until="domcontentloaded", timeout=45000)
                section = page.locator("#etnika-space-photo")
                page.evaluate("document.getElementById('etnika-space-photo').scrollIntoView({block:'start',behavior:'instant'})")
                page.evaluate("() => document.fonts.ready")
                result = page.evaluate("""() => {
                    const block = document.getElementById('etnika-space-photo');
                    const header = document.getElementById('etnika-site-header');
                    const rect = el => el.getBoundingClientRect();
                    const shell = block.querySelector('.spf-shell');
                    const heading = block.querySelector('.spf-title');
                    const top = block.querySelector('.spf-top');
                    const photos = block.querySelector('.spf-gallery');
                    const nav = block.querySelector('.spf-nav');
                    const main = block.querySelector('.spf-main');
                    const mini = [...block.querySelectorAll('.spf-small')];
                    const sample = document.createElement('span');
                    sample.style.fontSize = 'var(--etnika-section-title)';
                    document.body.appendChild(sample);
                    const expectedSize = parseFloat(getComputedStyle(sample).fontSize);
                    sample.remove();
                    return {
                       windowH: window.innerHeight,
                       headerHeight: rect(header).height,
                       shellPaddingTop: parseFloat(getComputedStyle(shell).paddingTop),
                       shellPaddingBottom: parseFloat(getComputedStyle(shell).paddingBottom),
                       section: rect(block).toJSON(),
                       shell: rect(shell).toJSON(),
                       heading: rect(heading).toJSON(),
                       top: rect(top).toJSON(),
                       photos: rect(photos).toJSON(),
                       nav: rect(nav).toJSON(),
                       main: rect(main).toJSON(),
                       mini: mini.map(m => rect(m).toJSON()),
                       titleSize: parseFloat(getComputedStyle(heading).fontSize),
                       titleFamily: getComputedStyle(heading).fontFamily,
                       expectedSize,
                       fontUi: getComputedStyle(nav.querySelector('button')).fontFamily,
                       intro: block.querySelector('.spf-intro'),
                       images: [...block.querySelectorAll('.spf-gallery img')].map(i => ({ok:i.complete && i.naturalWidth>0, src:i.currentSrc}))
                    };
                }""")
                box=result["section"]; photos=result["photos"]
                err=lambda msg: f"{path.name} {w}x{h}: {msg}; metrics {result}"
                assert abs(box["height"]-(h-result["headerHeight"]))<=2, err("block does not occupy viewport below fixed header")
                assert abs(box["top"]-result["headerHeight"])<=3, err("block starts behind the fixed header")
                assert abs(box["bottom"]-h)<=3, err("section extends outside the viewport")
                assert abs(result["shellPaddingTop"]-result["shellPaddingBottom"])<=1, err("vertical padding is not symmetrical")
                assert 19<=result["shellPaddingTop"]<=35, err("too much empty space around photographs")
                assert result["intro"] is None, err("removed text still present")
                assert result["top"]["y"]-box["y"]>=12, err("top margin missing")
                assert box["bottom"]-result["nav"]["bottom"]>=12, err("bottom margin missing")
                assert result["heading"]["bottom"]<=photos["y"]+3, err("title overlaps photos")
                assert photos["bottom"]<=result["nav"]["y"]+3, err("photos overlap category nav")
                assert photos["height"]>=0.54*(h-result["headerHeight"]), err("gallery too small")
                assert all(r["height"]>35 for r in [result["main"], *result["mini"]]), err("a photo collapsed")
                assert abs(result["titleSize"]-result["expectedSize"])<=1, err("heading deviates from shared token")
                assert "Forum" in result["titleFamily"], err("wrong heading font family")
                assert "Geologica" in result["fontUi"], err("wrong tab font family")
                assert all(i["ok"] for i in result["images"]), err("missing studio photo asset")
                page.screenshot(path=str(output / f"etnika-space-{path.stem}-{w}x{h}.png"))
                print(f"PASS: {path.name} {w}x{h}; gallery {photos['height']:.0f}px; heading {result['titleSize']:.1f}px")
                page.close()
        browser.close()


if __name__ == "__main__":
    static_checks()
    if "--render" in sys.argv:
        render_checks()
