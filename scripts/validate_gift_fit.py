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
              computedSectionHeight:getComputedStyle(root).height,
              computedSectionMinHeight:getComputedStyle(root).minHeight,
              computedShellHeight:getComputedStyle(el('.eg-shell')).height,
              computedShellMinHeight:getComputedStyle(el('.eg-shell')).minHeight,
              computedRootDisplay:getComputedStyle(root).display,
              sharedHeading:(() => {
                const ref=document.querySelector('#etnika-faq-tariffs h2.etnika-section-heading');
                const cs=getComputedStyle(ref);
                return {font:cs.fontFamily,size:parseFloat(cs.fontSize),
                    weight:cs.fontWeight,lineHeight:cs.lineHeight,
                    spacing:cs.letterSpacing};
              })(),
              actualHeading:(() => {
                const cs=getComputedStyle(el('h2.eg-title'));
                return {font:cs.fontFamily,size:parseFloat(cs.fontSize),
                    weight:cs.fontWeight,lineHeight:cs.lineHeight,
                    spacing:cs.letterSpacing};
              })(),
              topLineLength:el('.eg-top-rule').getBoundingClientRect().width,
              signoffLineLength:parseFloat(getComputedStyle(el('.eg-signoff'),'::before').width),
              topRuleDisplay:getComputedStyle(el('.eg-top-rule')).display,
              headingSize:parseFloat(getComputedStyle(el('h2.eg-title')).fontSize),
              subtitleSize:parseFloat(getComputedStyle(el('.eg-sub')).fontSize),
              factLabelSize:parseFloat(getComputedStyle(el('.eg-fact span')).fontSize),
              noteSize:parseFloat(getComputedStyle(el('.eg-note')).fontSize),
              buttonSize:parseFloat(getComputedStyle(el('.eg-cta > span:first-child')).fontSize),
              videoPlaying:!el('.eg-video video').paused,
              kickerWeight:Number(getComputedStyle(el('.eg-kicker')).fontWeight),
              subWeight:Number(getComputedStyle(el('.eg-sub')).fontWeight),
              factWeight:Number(getComputedStyle(el('.eg-fact span')).fontWeight),
              noteWeight:Number(getComputedStyle(el('.eg-note')).fontWeight),
              ctaWeight:Number(getComputedStyle(el('.eg-cta > span:first-child')).fontWeight),
              signoffWeight:Number(getComputedStyle(el('.eg-signoff')).fontWeight),
              signoffRuleDisplay:getComputedStyle(el('.eg-signoff'),'::before').display,
              headingLineScroll:[...root.querySelectorAll('.eg-title-line')].map(x=>({
                scroll:x.scrollWidth,width:x.clientWidth
              })),
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
        assert "Forum" in v["headingFont"],f"{label}: non-Forum headline: {v}"
        assert max(v[w] for w in ("kickerWeight","subWeight","factWeight",
                  "noteWeight","ctaWeight","signoffWeight"))<=200, (
            f"{label}: Geologica became heavier than approved thin type: {v}")
        assert v["topRuleDisplay"]=="block" and v["signoffRuleDisplay"]=="block", (
            f"{label}: one of the original editorial hairlines is missing: {v}")
        assert v["topLineLength"]>=40 and v["signoffLineLength"]>=35, (
            f"{label}: the signature label hairlines are too short: {v}")
        assert v["actualHeading"]==v["sharedHeading"], (
            f"{label}: certificate heading typography differs from sitewide heading: {v}")
        if width>1100:
            assert all(x["scroll"]<=x["width"]+3 for x in v["headingLineScroll"]), (
                f"{label}: heading runs outside the left column: {v}")
            assert v["kicker"]["left"]>=38, (
                f"{label}: insufficient horizontal breathing room: {v}")
            assert v["kicker"]["top"]>=v["section"]["top"]+22, (
                f"{label}: caption is pressed against video top edge: {v}")
            assert v["footer"]["bottom"]<=v["section"]["bottom"]-20, (
                f"{label}: CTA/signoff are pressed against video bottom edge: {v}")
            assert 0<=v["footer"]["top"]-v["main"]["bottom"]<=max(280, .29*height), (
                f"{label}: headline and CTA are detached by excessive space: {v}")
            top_margin=v["kicker"]["top"]-v["section"]["top"]
            bottom_margin=v["section"]["bottom"]-v["footer"]["bottom"]
            assert abs(top_margin-bottom_margin)<5, (
                f"{label}: unlike other full-screen blocks, outer margins are not balanced: {v}")
        assert v["headingSize"]>=43,f"{label}: headline unreadable: {v}"
        assert v["subtitleSize"]>=16,f"{label}: explanatory text too small: {v}"
        assert v["noteSize"]>=16,f"{label}: CTA note too small: {v}"
        assert v["buttonSize"]>=15,f"{label}: CTA caption too small: {v}"
        if width>1100:
            assert v["factLabelSize"]>=14,f"{label}: facts label too small: {v}"
            assert v["main"]["width"] <= 810,f"{label}: headline takes over the entire photo: {v}"
        assert v["title"]["right"] <= v["section"]["right"]-20, (
            f"{label}: title extends beyond the gift composition: {v}")
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
        # The section prefers one viewport but NEVER cuts off CTA or copy
        # when its natural content is taller on short/narrow screens.
        visible_height=height-v["header"]["height"]
        assert v["section"]["height"] >= 400, (
            f"{label}: gift collapsed and cannot show its complete content: {v}")
        if width>1100:
            assert v["section"]["height"]>=visible_height-2, (
                f"{label}: gift video no longer fills the entire screen: {v}")
            if width>=1280 and height>=720:
                assert v["section"]["height"]<=visible_height+8, (
                    f"{label}: gift exceeds viewport although there is room: {v}")
        assert v["sectionScrollHeight"]<=v["sectionClientHeight"]+2, (
            f"{label}: gift content is clipped or internally scrolling: {v}")
        if width>=1280 and height>=720:
            assert v["section"]["height"]<=visible_height+4, (
                f"{label}: gift section is taller than usable viewport: {v}")
            assert v["button"]["bottom"]<=height+4, (
                f"{label}: gift purchase CTA clipped by the bottom of screen: {v}")
        if width > 1100 and v["section"]["height"] <= visible_height+2:
            assert v["kicker"]["top"]>=v["header"]["bottom"]+8, (
                f"{label}: label hidden under fixed navigation: {v}")
            assert v["button"]["bottom"]<=height-10, (
                f"{label}: certificate button not visible within fitted section: {v}")
            assert v["signoff"]["bottom"]<=height-8, (
                f"{label}: certificate signoff below viewport: {v}")
        # Key regression from 12 Nov: FAQ must be followed by a real,
        # visible certificate section before reviews; never skip it.
        sequence=page.evaluate("""() => Array.from(
            document.querySelectorAll('#etnika-review-flow > section[id]'),
            el => el.id)""")
        assert sequence.index("etnika-faq-tariffs")+1 == sequence.index("etnika-gift"), (
            f"{label}: gift must be immediately after tariffs FAQ: {sequence}")
        assert sequence.index("etnika-gift")+1 == sequence.index("etnika-reviews"), (
            f"{label}: reviews must follow gift, not replace it: {sequence}")
        assert v["section"]["height"]>=min(400,visible_height-2), (
            f"{label}: gift visually collapsed, scrolling will skip it: {v}")
        page.screenshot(path=str(REPORTS/f"etnika-gift-{label}.png"),
                        full_page=False)
        print(f"PASS GIFT {label}: section={v['section']['height']:.1f}px "
              f"title={v['title']['height']:.1f}px "
              f"button-bottom={v['button']['bottom']:.1f}px "
              f"footer-bottom={v['footer']['bottom']:.1f}px "
              f"min-height={v['computedSectionMinHeight']} "
              f"shell-min-height={v['computedShellMinHeight']} "
              f"title-font={v['headingFont']} CTA-text={v['buttonSize']}",flush=True)
        page.close()
    browser.close()
