#!/usr/bin/env python3
"""Smoke-test the *published* ETNIKA page, not the checkout's HTML file."""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://nkuchenov-hash.github.io/etnika-website/site/"
EXPECTED_BUILD = re.search(r'<meta name="etnika-build" content="([^"]+)"', (Path(__file__).resolve().parents[1] / "site/index.html").read_text(encoding="utf-8")).group(1)
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)
SHA = os.environ.get("GITHUB_SHA", "manual")[:12]

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    for width, height in ((1440, 900), (390, 844)):
        page = browser.new_page(viewport={"width": width, "height": height})
        url = BASE + "?smoke=" + SHA
        last_error = None
        for attempt in range(15):
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=40000)
                if response is None or response.status >= 400:
                    raise AssertionError(f"Published site returned {response.status if response else 'no response'}")
                page.wait_for_function(
                    "() => document.querySelector('#etnika-review-flow > section') !== null",
                    timeout=8000,
                )
                page.wait_for_timeout(600)
                metrics = page.evaluate("""() => {
                    const hero=document.getElementById('etnika-hero');
                    const process=document.getElementById('etnika-process-interactive');
                    const flow=document.getElementById('etnika-review-flow');
                    const build=document.querySelector('meta[name="etnika-build"]')?.content;
                    const hr=hero?.getBoundingClientRect();
                    const pr=process?.getBoundingClientRect();
                    const center=document.elementFromPoint(innerWidth/2,innerHeight/2);
                    return {
                       build,
                       first:flow?.querySelector(':scope > section')?.id,
                       initialScrollY:scrollY,
                       heroTop:hr?.top,
                       heroBottom:hr?.bottom,
                       processTop:pr?.top,
                       middleSection:center?.closest('section')?.id,
                       headerState:document.getElementById('etnika-site-header')?.dataset.hero,
                       studioLabel:document.querySelector('#etnika-site-header .esh__descriptor')?.textContent?.trim(),
                       logoRight:document.querySelector('#etnika-hero .ec-brand')?.getBoundingClientRect().right,
                       heartLeft:document.querySelector('#etnika-hero .ec-love')?.getBoundingClientRect().left,
                       heartRight:document.querySelector('#etnika-hero .ec-love')?.getBoundingClientRect().right,
                       order:Array.from(flow?.children||[]).map(el=>el.id).slice(0,5),
                       sectionSystem:(() => {
                         const key=['etnika-block-02-final','etnika-space-photo','etnika-stories','etnika-process-interactive','etnika-studio-features','etnika-faq','etnika-prices-clear','etnika-extra','etnika-faq-tariffs','etnika-gift','etnika-reviews','etnika-contacts-source'];
                         const reference=document.createElement('i');
                         reference.style.fontSize='var(--etnika-section-title)';
                         document.body.appendChild(reference);
                         const titleToken=parseFloat(getComputedStyle(reference).fontSize);
                         reference.remove();
                         return {
                           titleToken,
                           edge:parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--et-u-edge')),
                           blocks:key.map(id=>{
                             const node=document.getElementById(id);
                             const h=node?.querySelector('h2.etnika-section-heading');
                             const st=node&&getComputedStyle(node);
                             return {id,h2:!!h,titleSize:h?parseFloat(getComputedStyle(h).fontSize):null,titleFamily:h?getComputedStyle(h).fontFamily:null,
                               height:node?.getBoundingClientRect().height, outerTop:parseFloat(st?.paddingTop||0),
                               outerBottom:parseFloat(st?.paddingBottom||0)};
                           }),
                           processLeft:document.querySelector('#etnika-process-interactive .epi-grid')?.getBoundingClientRect().left,
                           processWidth:document.querySelector('#etnika-process-interactive .epi-grid')?.getBoundingClientRect().width,
                           processHeadingCenter:(() => {const r=document.querySelector('#etnika-process-interactive .epi-head h2')?.getBoundingClientRect();return r?.left+r?.width/2})(),
                           processHeaderBottom:document.querySelector('#etnika-process-interactive .epi-head')?.getBoundingClientRect().bottom,
                           processPhotosTop:document.querySelector('#etnika-process-interactive .epi-grid')?.getBoundingClientRect().top,
                           whyBackground:getComputedStyle(document.getElementById('etnika-block-02-final')).backgroundColor,
                           extraSubheading:parseFloat(getComputedStyle(document.querySelector('#etnika-extra .ee-title')).fontSize),
                           tariffFaqHeight:document.getElementById('etnika-faq-tariffs')?.getBoundingClientRect().height,
                           reviewsHeight:document.getElementById('etnika-reviews')?.getBoundingClientRect().height,
                           mapFrameHeight:document.querySelector('#etnika-contacts-source .location-map')?.getBoundingClientRect().height,
                           mapBlockHeight:document.getElementById('etnika-contacts-source')?.getBoundingClientRect().height,
                           mapFrameTop:document.querySelector('#etnika-contacts-source .location-map')?.getBoundingClientRect().top,
                           mapBlockTop:document.getElementById('etnika-contacts-source')?.getBoundingClientRect().top,
                           routeIcons:document.querySelectorAll('#etnika-contacts-source .etnika-route-icon').length,
                           storiesLeft:document.querySelector('#etnika-stories .stories-shell')?.getBoundingClientRect().left,
                           spaceFrameHeight:document.querySelector('#etnika-space-photo .spf-shell')?.getBoundingClientRect().height,
                           b02Gap:(() => {const a=document.querySelector('#etnika-block-02-final .etnika-b02__top');const b=document.querySelector('#etnika-block-02-final .etnika-b02__main');return a&&b?b.getBoundingClientRect().top-a.getBoundingClientRect().bottom:null})(),
                           fullScreenMedia:(() => {
                             const height=el=>el?.getBoundingClientRect().height;
                             const b02=document.getElementById('etnika-block-02-final');
                             const space=document.getElementById('etnika-space-photo');
                             return {
                               b02Block:height(b02),b02Photo:height(b02?.querySelector('.etnika-editorial-photos')),
                               spaceSection:height(space),spaceGallery:height(space?.querySelector('.spf-gallery')),
                               storiesGrid:height(document.querySelector('#etnika-stories .stories-grid')),
                               processGrid:height(document.querySelector('#etnika-process-interactive .epi-grid')),
                               featuresMain:height(document.querySelector('#etnika-studio-features .etnika-editorial-benefits')),
                               pricesVisual:height(document.querySelector('#etnika-prices-clear .ev3-visual')),
                               extraGallery:height(document.querySelector('#etnika-extra .ee-gallery')),
                               giftShell:height(document.querySelector('#etnika-gift .eg-shell'))
                             };
                           })()
                         };
                       })()
                    };
                }""")
                assert metrics["build"] == EXPECTED_BUILD, f"Old deployed HTML: {metrics}"
                assert metrics["first"] == "etnika-hero", f"Wrong runtime section order: {metrics}"
                assert metrics["order"][:4] == ["etnika-hero","etnika-block-02-final","etnika-space-photo","etnika-stories"], f"Wrong owner-approved section order: {metrics}"
                assert abs(metrics["initialScrollY"]) < 4, f"Page opened below HERO: {metrics}"
                assert metrics["heroTop"] <= 70, f"HERO starts too low: {metrics}"
                assert metrics["heroBottom"] >= height * 0.85, f"HERO is not a full first screen: {metrics}"
                assert metrics["processTop"] >= metrics["heroBottom"] - 5, f"Process overlaps HERO: {metrics}"
                assert metrics["middleSection"] == "etnika-hero", f"Process hides the visible HERO: {metrics}"
                assert metrics["headerState"] == "true", f"Header already outside HERO: {metrics}"
                system = metrics["sectionSystem"]
                assert len(system["blocks"]) == 12, f"Missing content sections: {system}"
                for block in system["blocks"]:
                    if block["id"] == "etnika-extra":
                        assert not block["h2"], f"Extras is a subsection, must NOT use the primary heading token: {block}"
                    else:
                        assert block["h2"], f"Missing shared section heading: {block}"
                        if block["id"] in ("etnika-gift","etnika-studio-features"):
                            assert 32 <= block["titleSize"] <= 100, f"Editorial headline unexpectedly sized: {block}"
                        else:
                            assert abs(block["titleSize"]-system["titleToken"]) < 1, f"Nonstandard H2 size: {block}"
                        assert "Forum" in block["titleFamily"], f"Nonstandard H2 font: {block}"
                    if block["id"] in ("etnika-block-02-final","etnika-studio-features","etnika-process-interactive"):
                        assert block["height"] > 0, f"Missing editorial section: {block}"
                        continue
                    if width >= 1101 and block["id"] == "etnika-contacts-source":
                        assert block["outerTop"] == 0 and block["outerBottom"] == 0, f"Full-bleed map cannot have section padding: {block}"
                    else:
                        assert block["outerTop"] >= 20 and abs(block["outerTop"]-block["outerBottom"]) < 2, f"Broken outer fields: {block}"
                    if width >= 1101 and block["id"] not in ("etnika-faq-tariffs","etnika-reviews","etnika-prices-clear","etnika-gift"):
                        assert block["height"] > height, f"Full-screen content+fields should exceed viewport: {block}"
                assert system["processPhotosTop"] >= system["processHeaderBottom"]-2, f"Process header overlaps photo grid: {system}"
                assert system["processLeft"] >= -2 and system["processLeft"]+system["processWidth"]<=width+2, f"Process grid overflows viewport: {system}"
                assert system["whyBackground"] == "rgb(255, 255, 255)", f"About and Why must share a white background: {system}"
                assert system["extraSubheading"] < system["titleToken"], f"Extras subsection headline too large: {system}"
                assert system["routeIcons"] == 3, f"Missing route icons: {system}"
                if width >= 1101:
                    assert abs(system["mapFrameTop"]-system["mapBlockTop"]) <= 2, f"Map has an unwanted upper inset: {system}"
                    assert abs(system["mapFrameHeight"]-system["mapBlockHeight"]) <= 3, f"Map has an unwanted lower inset: {system}"
                    assert system["tariffFaqHeight"] < height, f"Tariff FAQ is too tall: {system}"
                assert abs(system["spaceFrameHeight"]-height) <= 3, f"Studio content is shorter than the viewport: {system}"
                media=system["fullScreenMedia"]
                if width >= 1101:
                    assert media["spaceGallery"] >= height*.56, f"Studio photos too small: {media}"
                    assert media["storiesGrid"] >= height*.56, f"Stories photos too small: {media}"
                    assert media["extraGallery"] >= height*.85, f"Extra gallery does not fill viewport: {media}"
                    assert height-85 <= media["giftShell"] <= height, f"Gift content frame does not match visible viewport below fixed navigation: {media}"
                assert metrics["studioLabel"] == "СТУДИЯ АВТОПОРТРЕТА", f"Header studio label is not uppercase: {metrics}"
                assert metrics["heartLeft"] - metrics["logoRight"] >= (9 if width <= 760 else 20), f"Heart too close to brand: {metrics}"
                assert metrics["heartRight"] <= width + 2, f"Heart overflows viewport: {metrics}"
                path = REPORTS / f"etnika-live-first-screen-{width}x{height}.png"
                page.screenshot(path=str(path), full_page=False)
                if width >= 1101:
                    # Confirm the actual visitor interaction for the editorial layout.
                    cards=page.locator('#etnika-process-interactive .epi-card')
                    assert cards.count()==5
                    card=cards.first
                    card.scroll_into_view_if_needed()
                    assert card.locator('.epi-desc').is_visible(), "Step description must be visible without hover"
                    card.locator('.epi-more').click()
                    page.locator('#etnika-process-interactive .epi-modal.open').wait_for(state="visible",timeout=6000)
                    page.locator('#etnika-process-interactive .epi-close').click()
                    assert page.locator('#etnika-process-interactive .epi-modal.open').count()==0,"Modal would not close"
                    about=page.locator('#etnika-block-02-final')
                    assert about.locator('.etnika-editorial-photo img').count()==8
                    assert about.locator('#etnika-studio-features .etnika-editorial-benefits details').count()==6
                    about.screenshot(path=str(REPORTS / "etnika-live-b02-fit.png"))
                    page.locator('#etnika-space-photo').scroll_into_view_if_needed()
                    page.mouse.move(0,0)
                    page.wait_for_timeout(300)
                    photoStyles=page.evaluate("""() => {
                        const root=document.getElementById('etnika-space-photo');
                        const cards=[root.querySelector('.spf-main'),...root.querySelectorAll('.spf-small')];
                        return {
                          line:getComputedStyle(root.querySelector('.spf-top .spf-line')).backgroundColor,
                          divider:getComputedStyle(root.querySelector('.spf-top .spf-divider')).backgroundColor,
                          labels:cards.map(card=>({
                            opacity:getComputedStyle(card.querySelector('.spf-label')).opacity,
                            title:card.querySelector('.spf-label-title').textContent.trim(),
                            weight:getComputedStyle(card.querySelector('.spf-label-title')).fontWeight,
                            detailOpacity:getComputedStyle(card.querySelector('.spf-label-sub')).opacity,
                            detailVisibility:getComputedStyle(card.querySelector('.spf-label-sub')).visibility
                          }))
                        };
                    }""")
                    assert photoStyles["line"]=="rgba(255, 255, 255, 0.42)",f"Published studio editorial line invisible: {photoStyles}"
                    assert photoStyles["divider"]=="rgba(255, 255, 255, 0.42)",f"Published studio editorial divider invisible: {photoStyles}"
                    assert all(item["title"] and item["opacity"]=="1" and item["weight"]=="300" for item in photoStyles["labels"]),f"Default photo titles invisible or too heavy: {photoStyles}"
                    assert all(item["detailVisibility"]=="hidden" for item in photoStyles["labels"]),f"All detail labels exposed before hover: {photoStyles}"
                    page.screenshot(path=str(REPORTS / "etnika-live-space-alignment.png"),full_page=False)
                    photo=page.locator('#etnika-space-photo .spf-main')
                    photo.hover()
                    page.wait_for_timeout(350)
                    active=photo.locator('.spf-label-sub').evaluate("(el)=>({opacity:getComputedStyle(el).opacity,visibility:getComputedStyle(el).visibility})")
                    assert float(active["opacity"])>.95 and active["visibility"]=="visible",f"Published studio description not revealed on hover: {active}"
                    page.screenshot(path=str(REPORTS / "etnika-live-space-hover.png"),full_page=False)
                    print(f"PASS LIVE editorial B02/SPACE {width}x{height}",flush=True)
                print(f"PASS LIVE {width}x{height}: {metrics}; screenshot={path}", flush=True)
                break
            except Exception as exc:
                last_error = exc
                print(f"Live check attempt {attempt + 1} failed: {exc}", flush=True)
                if attempt == 14:
                    raise AssertionError(f"Published page did not show HERO first: {last_error}") from exc
                time.sleep(3)
        page.close()
    browser.close()
