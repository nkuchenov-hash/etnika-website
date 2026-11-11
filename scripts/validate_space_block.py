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
FRAME_CSS = re.compile(r'<style id="etnika-section-system-20261111">[\s\S]*?</style>')
FORBIDDEN = "Просторный зал, профессиональный свет, лаунж-зона, большое зеркало и реквизит"
HEADLINE = '<h2 class="spf-title etnika-section-heading">Пространство <span class="red">ЭТНИКА</span></h2>'


def static_checks():
    sections, styles = [], []
    for path in FILES:
        html = path.read_text(encoding="utf-8")
        section = SPACE_SECTION.search(html)
        style = SPACE_CSS.search(html)
        shared = SHARED_CSS.search(html)
        frame=FRAME_CSS.search(html)
        assert section and style and shared and frame, f"{path}: studio/shared design system missing"
        part = section.group(0)
        css = style.group(0)
        shared_code = shared.group(0)
        frame_code=frame.group(0)
        assert FORBIDDEN not in html, f"{path}: removed description has returned"
        assert HEADLINE in part, f"{path}: heading is missing"
        assert part.count('class="spf-img ') == 3, f"{path}: expected 3 original photos"
        assert part.count('class="spf-tab') == 5, f"{path}: expected 5 selectable categories"
        assert "height:var(--etnika-content-screen)!important" in frame_code, f"{path}: full-screen studio photo frame missing"
        assert "padding-top:var(--etnika-section-outer)!important" in frame_code, f"{path}: separate outer fields missing"
        assert "grid-template-rows:auto auto minmax(0,1fr) auto!important" in css, f"{path}: gallery must take remaining height without pushing content beyond viewport"
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
                outer=result["sectionPaddingTop"]
                assert outer>=34 and abs(outer-result["sectionPaddingBottom"])<=1, err("symmetric external top/bottom fields missing")
                assert abs(box["height"]-((h-result["headerHeight"])+2*outer))<=3, err("section must equal one content screen plus two outer fields")
                assert box["height"]>h, err("complete block must exceed viewport")
                assert abs(result["shell"]["height"]-(h-result["headerHeight"]))<=3, err("photo content frame must equal one viewport below header")
                assert abs(box["top"]-result["headerHeight"])<=3, err("studio section not aligned immediately under header")
                assert abs(result["shellPaddingTop"]-result["shellPaddingBottom"])<=1, err("CSS black padding must be equal above and below")
                assert abs((result["top"]["y"]-result["shell"]["y"])-(result["shell"]["bottom"]-result["nav"]["bottom"]))<=3, err("visible internal top/bottom margins unequal")
                assert 32<=result["shellPaddingBottom"]<=61, err("balanced black margins must be at least 32px")
                assert result["intro"] is None, err("removed text still present")
                assert result["top"]["y"]-result["shell"]["y"]>=32, err("inner black upper margin missing")
                assert result["shell"]["bottom"]-result["nav"]["bottom"]>=32, err("inner black bottom margin missing")
                assert result["heading"]["bottom"]<=photos["y"]+3, err("title overlaps photos")
                assert result["nav"]["bottom"]<=result["shell"]["bottom"]-32, err("navigation intrudes on internal bottom padding")
                assert photos["bottom"]<=result["nav"]["y"]+3, err("photos overlap category nav")
                assert photos["height"]>=(0.39*h if h<=700 else 0.48*h), err("gallery too small after accounting for the larger shared heading and kicker gap")
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
