#!/usr/bin/env python3
"""ETNIKA gift-certificate regression: no clipped content within one screen."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

SIZES = [(1102, 600), (1280, 720), (1366, 768), (1440, 900),
         (1920, 1080), (390, 844), (375, 667), (768, 1024)]

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    for width, height in SIZES:
        page = browser.new_page(viewport={"width": width, "height": height},
                                reduced_motion="reduce")
        page.goto((ROOT / "site/index.html").as_uri(),
                  wait_until="domcontentloaded", timeout=45000)
        page.wait_for_function("() => document.querySelector('#etnika-review-flow > section#etnika-gift')")
        page.evaluate("""() => {
            document.documentElement.style.scrollBehavior='auto';
            const g=document.querySelector('#etnika-review-flow > section#etnika-gift');
            const header=document.getElementById('etnika-site-header');
            const top=g.getBoundingClientRect().top+window.scrollY;
            window.scrollTo(0,top-header.getBoundingClientRect().height);
        }""")
        page.wait_for_timeout(180)
        v = page.evaluate("""() => {
            const root=document.querySelector('#etnika-review-flow > section#etnika-gift');
            const el=s=>root.querySelector(s);
            const b=e=>e.getBoundingClientRect().toJSON();
            const facts=[...root.querySelectorAll('.eg-fact')].map(b);
            return {
              section:b(root),shell:b(el('.eg-shell')),
              header:b(document.getElementById('etnika-site-header')),
              kicker:b(el('.eg-top')),main:b(el('.eg-main')),
              title:b(el('h2.eg-title')),sub:b(el('.eg-sub')),
              facts:facts,footer:b(el('.eg-footer')),note:b(el('.eg-note')),
              button:b(el('.eg-cta')),signoff:b(el('.eg-signoff')),
              viewportHeight:innerHeight,sectionScrollHeight:root.scrollHeight,
              sectionClientHeight:root.clientHeight,
              overflowsX:root.scrollWidth>root.clientWidth+2,
              content:[el('.eg-kicker').textContent,el('h2').textContent,
                el('.eg-sub').textContent,el('.eg-note').textContent,
                el('.eg-cta').textContent].every(x=>x.trim().length>0)
            };
        }""")
        label=f"{width}x{height}"
        assert v["content"],f"{label}: original text or CTA missing"
        assert len(v["facts"])==3,f"{label}: certificate facts missing"
        assert not v["overflowsX"],f"{label}: horizontal clipping of gift: {v}"
        assert v["kicker"]["bottom"]+3 <= v["main"]["top"],f"{label}: kicker overlaps headline: {v}"
        assert v["title"]["bottom"] <= v["sub"]["top"]+2,f"{label}: headline overlaps subtitle: {v}"
        assert v["sub"]["bottom"] <= v["facts"][0]["top"]+2,f"{label}: subtitle overlaps facts: {v}"
        assert v["facts"][-1]["bottom"] <= v["footer"]["top"]-2,f"{label}: facts overlap footer: {v}"
        assert v["note"]["bottom"] <= v["button"]["top"]+2,f"{label}: CTA overlaps note: {v}"
        for elem in ("kicker","title","sub","footer","button","signoff"):
            assert v[elem]["top"] >= v["section"]["top"]-2, f"{label}: {elem} above section: {v}"
            assert v[elem]["bottom"] <= v["section"]["bottom"]+2, f"{label}: {elem} clipped at section end: {v}"
        if width > 1100:
            assert abs(v["section"]["height"]-(height-v["header"]["height"]))<=2, (
                f"{label}: section longer than visible viewport below menu: {v}")
            assert v["kicker"]["top"]>=v["header"]["bottom"]+8, (
                f"{label}: label hidden under fixed navigation: {v}")
            assert v["button"]["bottom"]<=height-10, (
                f"{label}: certificate action not visible without scrolling: {v}")
            assert v["signoff"]["bottom"]<=height-8, (
                f"{label}: certificate slogan below viewport: {v}")
            assert v["sectionScrollHeight"] <= v["sectionClientHeight"]+2, (
                f"{label}: content scrolls outside fixed-height section: {v}")
        else:
            assert v["sectionScrollHeight"]<=v["sectionClientHeight"]+2, (
                f"{label}: mobile section clips content: {v}")
        page.screenshot(path=str(REPORTS/f"etnika-gift-{label}.png"),
                        full_page=False)
        print(f"PASS GIFT {label}: section={v['section']['height']:.1f}px "
              f"title={v['title']['height']:.1f}px "
              f"button-bottom={v['button']['bottom']:.1f}px "
              f"footer-bottom={v['footer']['bottom']:.1f}px",flush=True)
        page.close()
    browser.close()
