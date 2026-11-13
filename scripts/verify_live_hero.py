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
                           whyBackground:getComputedStyle(document.getElementById('etnika-studio-features')).backgroundColor,
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
                               b02Block:height(b02),b02Photo:height(b02?.querySelector('.etnika-b02__media')),
                               spaceSection:height(space),spaceGallery:height(space?.querySelector('.spf-gallery')),
                               storiesGrid:height(document.querySelector('#etnika-stories .stories-grid')),
                               processGrid:height(document.querySelector('#etnika-process-interactive .epi-grid')),
                               featuresMain:height(document.querySelector('#etnika-studio-features .b05-main')),
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
                        if block["id"] == "etnika-gift":
                            assert 42 <= block["titleSize"] <= 90, f"Gift headline unexpectedly sized: {block}"
                        else:
                            assert abs(block["titleSize"]-system["titleToken"]) < 1, f"Nonstandard H2 size: {block}"
                        assert "Forum" in block["titleFamily"], f"Nonstandard H2 font: {block}"
                    if width >= 1101 and block["id"] in ("etnika-block-02-final","etnika-contacts-source"):
                        assert block["outerTop"] == 0 and block["outerBottom"] == 0, f"Full-bleed image/map cannot have section padding: {block}"
                    elif width >= 1101 and block["id"] == "etnika-process-interactive":
                        assert block["outerTop"] == 0 and block["outerBottom"] >= 34, f"Process heading is a separate unpadded top section: {block}"
                    else:
                        assert block["outerTop"] >= 20 and abs(block["outerTop"]-block["outerBottom"]) < 2, f"Broken outer fields: {block}"
                    if width >= 1101 and block["id"] == "etnika-block-02-final":
                        assert height+20 < block["height"] < height+95, f"B02 section needs moderate and balanced photographic extension: {block}"
                    elif width >= 1101 and block["id"] not in ("etnika-faq-tariffs","etnika-reviews","etnika-prices-clear","etnika-gift"):
                        assert block["height"] > height, f"Full-screen content+fields should exceed viewport: {block}"
                if width >= 1101:
                    assert abs(system["processLeft"]) < 2, f"Process photos must be FULL BLEED: {system}"
                    assert abs(system["processWidth"]-width) < 3, f"Process grid does not span viewport: {system}"
                    assert abs(system["processHeadingCenter"]-width/2) < 3, f"Process title not centered: {system}"
                    assert system["processPhotosTop"] >= system["processHeaderBottom"]-2, f"Process header overlaps photo grid: {system}"
                else:
                    assert abs(system["processLeft"]-system["storiesLeft"]) <= 2, f"Mobile process alignment broken: {system}"
                assert system["whyBackground"] == "rgb(255, 255, 255)", f"WHY ETNIKA should be pure white: {system}"
                assert system["extraSubheading"] < system["titleToken"], f"Extras subsection headline too large: {system}"
                assert system["routeIcons"] == 3, f"Missing route icons: {system}"
                if width >= 1101:
                    assert abs(system["mapFrameTop"]-system["mapBlockTop"]) <= 2, f"Map has an unwanted upper inset: {system}"
                    assert abs(system["mapFrameHeight"]-system["mapBlockHeight"]) <= 3, f"Map has an unwanted lower inset: {system}"
                    assert system["tariffFaqHeight"] < height, f"Tariff FAQ is too tall: {system}"
                assert system["b02Gap"] >= 30, f"Insufficient gap after editorial overline: {system}"
                assert abs(system["spaceFrameHeight"]-height) <= 3, f"Studio content is shorter than the viewport: {system}"
                media=system["fullScreenMedia"]
                if width >= 1101:
                    assert media["b02Photo"] > height+20, f"B02 photographic media must be taller than one viewport: {media}"
                    assert media["spaceGallery"] >= height*.56, f"Studio photos too small: {media}"
                    assert media["storiesGrid"] >= height*.56, f"Stories photos too small: {media}"
                    assert abs(media["processGrid"] - height) < 3, f"Process PHOTO GRID must be a full viewport tall: {media}"
                    assert media["extraGallery"] >= height*.85, f"Extra gallery does not fill viewport: {media}"
                    assert height-85 <= media["giftShell"] <= height, f"Gift content frame does not match visible viewport below fixed navigation: {media}"
                assert metrics["studioLabel"] == "СТУДИЯ АВТОПОРТРЕТА", f"Header studio label is not uppercase: {metrics}"
                assert metrics["heartLeft"] - metrics["logoRight"] >= (9 if width <= 760 else 20), f"Heart too close to brand: {metrics}"
                assert metrics["heartRight"] <= width + 2, f"Heart overflows viewport: {metrics}"
                path = REPORTS / f"etnika-live-first-screen-{width}x{height}.png"
                page.screenshot(path=str(path), full_page=False)
                if width >= 1101:
                    # Confirm the actual visitor interaction, not only CSS selectors.
                    card=page.locator('#etnika-process-interactive .epi-card').first
                    card.wait_for(state="visible",timeout=10000)
                    page.mouse.move(0,0)
                    card.scroll_into_view_if_needed()
                    page.mouse.move(0,0)
                    page.wait_for_timeout(300)
                    idle=card.locator('.epi-reveal').evaluate("(e)=>({opacity:getComputedStyle(e).opacity,visibility:getComputedStyle(e).visibility})")
                    assert idle["opacity"]=="0" and idle["visibility"]=="hidden",f"Process details exposed before hover: {idle}"
                    card.hover()
                    page.wait_for_function("""() => {
                      const c=document.querySelector('#etnika-process-interactive .epi-card');
                      return Number(getComputedStyle(c.querySelector('.epi-reveal')).opacity)>.95
                        && getComputedStyle(c.querySelector('.epi-more')).backgroundColor==='rgb(169, 21, 29)';
                    }""",timeout=5000)
                    card.screenshot(path=str(REPORTS / "etnika-live-process-hover.png"))
                    card.locator('.epi-more').click()
                    page.locator('#etnika-process-interactive .epi-modal.open').wait_for(state="visible",timeout=6000)
                    assert page.locator('#etnika-process-interactive .epi-arrow.next').is_visible(),"Process modal navigation is hidden"
                    page.locator('#etnika-process-interactive .epi-close').click()
                    assert page.locator('#etnika-process-interactive .epi-modal.open').count()==0,"Modal would not close"
                    page.locator('#etnika-studio-features').scroll_into_view_if_needed()
                    page.screenshot(path=str(REPORTS / "etnika-live-why-white.png"),full_page=False)
                    # Live first-screen regression: the B02 lower feature row must
                    # be visible before scrolling further; the next block uses
                    # exactly the same editorial label + accent left guides.
                    page.evaluate("""() => {
                        const b=document.getElementById('etnika-block-02-final');
                        const h=document.getElementById('etnika-site-header').getBoundingClientRect().height;
                        window.scrollTo({top:b.getBoundingClientRect().top+scrollY-h,behavior:'instant'});
                    }""")
                    page.wait_for_timeout(250)
                    guide=page.evaluate("""() => {
                        const r=s=>document.querySelector(s).getBoundingClientRect();
                        const top=document.querySelector('#etnika-block-02-final .etnika-b02__top');
                        const sp=document.querySelector('#etnika-space-photo .spf-top');
                        return {
                          labelX:r('#etnika-block-02-final .etnika-b02__top span:first-child').left,
                          spaceLabelX:r('#etnika-space-photo .spf-top > :first-child').left,
                          accentX:r('#etnika-block-02-final .etnika-b02__top-accent').left,
                          spaceAccentX:r('#etnika-space-photo .spf-accent').left,
                          featuresBottom:r('#etnika-block-02-final .etnika-b02__features').bottom,
                          featuresTop:r('#etnika-block-02-final .etnika-b02__features').top,
                          copyTop:r('#etnika-block-02-final .etnika-b02__top').top,
                          mediaHeight:r('#etnika-block-02-final .etnika-b02__media').height,
                          sectionHeight:r('#etnika-block-02-final').height,
                          blockTop:r('#etnika-block-02-final').top,
                          mainTop:r('#etnika-block-02-final .etnika-b02__main').top,
                          compositionMid:(() => {const r=document.querySelector('#etnika-block-02-final .etnika-b02__composition').getBoundingClientRect();return r.top+r.height/2;})(),
                          blockMid:(() => {const r=document.querySelector('#etnika-block-02-final').getBoundingClientRect();return r.top+r.height/2;})(),
                          stampTop:r('#etnika-block-02-final .etnika-b02__stamp').top,
                          counterTop:r('#etnika-block-02-final .etnika-b02__counter').top,
                          captionBottom:r('#etnika-block-02-final .etnika-b02__caption').bottom,
                          controlsBottom:r('#etnika-block-02-final .etnika-b02__controls').bottom,
                          overlayBottom:r('#etnika-block-02-final .etnika-b02__media-bottom').bottom,
                          arrowBottom:r('#etnika-block-02-final .etnika-b02__arrow--next').bottom,
                          headerBottom:r('#etnika-site-header').bottom
                        };
                    }""")
                    assert abs(guide["labelX"]-guide["spaceLabelX"])<=2, f"Live shared B02/space left edge mismatch: {guide}"
                    assert abs(guide["accentX"]-guide["spaceAccentX"])<=3, f"Live overline accents misaligned: {guide}"
                    assert guide["featuresBottom"] < guide["blockTop"] + guide["sectionHeight"] - 12, f"B02 benefits extend below its enlarged block: {guide}"
                    assert abs(guide["compositionMid"]-guide["blockMid"]) <= 2, f"Published B02 text composition not centered: {guide}"
                    assert abs((guide["mainTop"]+guide["featuresBottom"])/2-guide["blockMid"]) <= 2, f"Published B02 title and benefits do not center as a group: {guide}"
                    assert abs(guide["mediaHeight"]-guide["sectionHeight"])<=3, f"Live B02 photo shrunk again: {guide}"
                    assert guide["stampTop"]>=guide["headerBottom"]+8, f"Live photo 'Moscow' title hidden behind menu: {guide}"
                    assert guide["counterTop"]>=guide["headerBottom"]+8, f"Live photo count hidden behind menu: {guide}"
                    assert guide["overlayBottom"]<=guide["blockTop"]+guide["sectionHeight"]-48, f"Live photo overlays not inset from photo bottom: {guide}"
                    assert guide["captionBottom"]<=guide["blockTop"]+guide["sectionHeight"]-48, f"Live B02 caption outside expected photo edge: {guide}"
                    assert guide["controlsBottom"]<=guide["blockTop"]+guide["sectionHeight"]-48 and guide["arrowBottom"]<=guide["blockTop"]+guide["sectionHeight"]-48, f"Live carousel navigation outside photographic outer inset: {guide}"
                    page.screenshot(path=str(REPORTS / "etnika-live-b02-fit.png"),full_page=False)
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
                    print(f"PASS LIVE B02/SPACE {width}x{height}: {guide}",flush=True)
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
