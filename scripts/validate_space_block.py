#!/usr/bin/env python3
"""ETNIKA B-06: canonical site design tokens and browser geometry."""
from __future__ import annotations
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = (ROOT / "site/index.html",)
SPACE_SECTION = re.compile(r'<section id="etnika-space-photo"(?=\s|>)[\s\S]*?</section>')
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
        assert "height:auto!important;min-height:calc(100svh - var(--etnika-nav-height,60px))!important" in css, f"{path}: studio must fill available height and grow if needed"
        assert "padding:0!important;margin:0!important;" in css, f"{path}: legacy v15 external frame padding still steals gallery height"
        assert "grid-template-rows:auto auto minmax(clamp(250px,32svh,350px),1fr) auto!important" in css, f"{path}: photos must receive the remaining screen height without collapsing"
        assert "padding:var(--etnika-photo-section-y) 0!important" in css, f"{path}: black margins must use a single symmetric padding rule"
        assert "font-size:var(--etnika-section-title)!important" in css, f"{path}: rogue title size"
        assert "font-family:var(--etnika-font-display)!important" in css, f"{path}: display font not using token"
        assert "font-family:var(--etnika-font-ui)!important" in css, f"{path}: UI font not using token"
        assert "--etnika-text-size:16px" in shared_code, f"{path}: min UI text size token missing"
        assert "--etnika-section-title:clamp(62px,6.25vw,118px)" in shared_code
        assert "--etnika-photo-section-y:clamp(44px,5.5svh,60px)" in html, f"{path}: desktop spacing token missing"
        assert "--etnika-photo-section-y:clamp(32px,5svh,44px)" in html, f"{path}: mobile spacing token missing"
        assert ".spf-small:hover::before" in css and "display:none!important;content:none!important" in css, f"{path}: pink hover border returned"
        assert "font-size:var(--etnika-text-size,16px)!important" in css, f"{path}: category labels must use the shared readable text size"
        assert "etnika-space-title-fit-20261104" not in html, f"{path}: distorted scaleX title script returned"
        assert "11svh" not in css, f"{path}: local font shrinking returned"
        sections.append(part)
        styles.append(css)
    print("PASS: canonical B-06 has original 3 photos and 5 tabs, no intro, shared font and spacing tokens")


def render_checks():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise SystemExit("Install playwright and its Chromium browser to run --render") from e
    sizes = [(1920,1080), (1662,896), (1536,800), (1366,768), (1100,800), (390,844), (375,667), (375,600)]
    output = ROOT / "reports"
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for path in FILES:
            for w,h in sizes:
                page = browser.new_page(viewport={"width":w,"height":h}, device_scale_factor=1)
                page.goto(path.as_uri(), wait_until="load", timeout=45000)
                section = page.locator("#etnika-space-photo")
                page.evaluate("window.scrollTo({top:document.getElementById('etnika-space-photo').getBoundingClientRect().top+window.scrollY-document.getElementById('etnika-site-header').getBoundingClientRect().height,behavior:'instant'})")
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
                       sectionPaddingTop:parseFloat(getComputedStyle(block).paddingTop),
                       sectionPaddingBottom:parseFloat(getComputedStyle(block).paddingBottom),
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
                       navFontSize:parseFloat(getComputedStyle(nav.querySelector('button')).fontSize),
                       hoverFrame:getComputedStyle(mini[0],'::before').display,
                       intro: block.querySelector('.spf-intro'),
                       images: [...block.querySelectorAll('.spf-gallery img')].map(i => ({ok:i.complete && i.naturalWidth>0, src:i.currentSrc}))
                    };
                }""")
                box=result["section"]; photos=result["photos"]
                err=lambda msg: f"{path.name} {w}x{h}: {msg}; metrics {result}"
                assert box["height"] >= h-result["headerHeight"]-2, err("studio section must fill viewport below header and grow when content needs room")
                assert result["sectionPaddingTop"]<=.5 and result["sectionPaddingBottom"]<=.5, err("legacy outer frame padding still active")
                assert abs(box["top"]-result["headerHeight"])<=3, err("studio section not aligned immediately under header")
                assert box["bottom"] >= h-3, err("section fails to fill the viewport")
                assert abs(result["shellPaddingTop"]-result["shellPaddingBottom"])<=1, err("CSS black padding must be equal above and below")
                assert abs((result["top"]["y"]-result["headerHeight"])-(box["bottom"]-result["nav"]["bottom"]))<=2, err("VISIBLE black margins above and below content are not equal")
                assert 32<=result["shellPaddingBottom"]<=61, err("balanced black margins must be at least 32px")
                assert result["intro"] is None, err("removed text still present")
                assert result["top"]["y"]-box["y"]>=32, err("black upper margin missing")
                assert box["bottom"]-result["nav"]["bottom"]>=32, err("black bottom margin missing")
                assert result["heading"]["bottom"]<=photos["y"]+3, err("title overlaps photos")
                assert photos["bottom"]<=result["nav"]["y"]+3, err("photos overlap category nav")
                assert photos["height"]>=(0.43*h if h<=600 else 0.50*h), err("gallery too small: photos must dominate the viewport")
                assert 15.5<=result["navFontSize"]<=16.5, err("category text must be readable at 16px")
                assert result["hoverFrame"]=="none", err("pink hover border still present")
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
