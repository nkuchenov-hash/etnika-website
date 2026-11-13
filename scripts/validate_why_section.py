#!/usr/bin/env python3
"""Viewport geometry regression for WHY ETNIKA (owner screenshot 2026-11-11)."""
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"
OUT.mkdir(exist_ok=True)

with sync_playwright() as pw:
    chrome=shutil.which('google-chrome') or shutil.which('google-chrome-stable')
    browser=pw.chromium.launch(headless=True,executable_path=chrome) if chrome else pw.chromium.launch(headless=True)
    for w,h in [(1366,768),(1440,900),(1635,928),(1920,1080)]:
        page=browser.new_page(viewport={"width":w,"height":h})
        page.goto((ROOT/"site/index.html").as_uri(),wait_until="load",timeout=45000)
        page.evaluate("() => document.fonts.ready")
        page.wait_for_function("() => document.querySelector('#etnika-review-flow > section')?.id==='etnika-hero'")
        # Align the section through the actual sticky-header-aware scroll system.
        # No artificial white strip is allowed above the photograph.
        page.evaluate("""() =>
          document.getElementById('etnika-studio-features')
            .scrollIntoView({block:'start',behavior:'instant'})""")
        page.wait_for_timeout(250)
        v=page.evaluate("""() => {
          const r=s=>document.querySelector(s).getBoundingClientRect().toJSON();
          const q='#etnika-studio-features ';
          return {
            header:r('#etnika-site-header'),section:r('#etnika-studio-features'),
            shell:r('#etnika-studio-features .b05-shell'), main:r('#etnika-studio-features .b05-main'),
            metrics:(()=>{let e=document.querySelector('#etnika-studio-features .b05-shell');let m=document.querySelector('#etnika-studio-features .b05-main');let a=document.querySelector('#etnika-studio-features');const cs=(x)=>({height:getComputedStyle(x).height,minHeight:getComputedStyle(x).minHeight,maxHeight:getComputedStyle(x).maxHeight,boxSizing:getComputedStyle(x).boxSizing,display:getComputedStyle(x).display,paddingTop:getComputedStyle(x).paddingTop});return {section:cs(a),shell:cs(e),main:cs(m),nav:getComputedStyle(document.documentElement).getPropertyValue('--etnika-nav-height')};})(),
            stage:r(q+'.b05-stage'),copy:r(q+'.b05-copy'),
            title:r(q+'.b05-title'), intro:r(q+'.b05-intro'), meta:r(q+'.b05-meta'),
            first:r(q+'.b05-item:first-child'), list:r(q+'.b05-list'),
            titleFont:parseFloat(getComputedStyle(document.querySelector(q+'.b05-title')).fontSize),
            titleFamily:getComputedStyle(document.querySelector(q+'.b05-title')).fontFamily,
            listRows:Array.from(document.querySelectorAll(q+'.b05-item'),e=>e.getBoundingClientRect().height),
            bottom:r(q+'.b05-stage-bottom'),
            caption:r(q+'.b05-caption'),prev:r(q+'.b05-prev'),
            next:r(q+'.b05-next'),nav:r(q+'.b05-nav'),
            imageTransform:getComputedStyle(document.querySelector(q+'.b05-stage-image')).transform,
            arrowCSS:(()=>{const a=getComputedStyle(document.querySelector(q+'.b05-prev'));const n=getComputedStyle(document.querySelector(q+'.b05-nav'));return {width:a.width,height:a.height,border:a.borderTopWidth,background:a.backgroundColor,navBorder:n.borderBottomWidth,navWidth:n.width,svgWidth:getComputedStyle(document.querySelector(q+'.b05-prev svg')).width,svgBox:document.querySelector(q+'.b05-prev svg').getAttribute('viewBox')};})(),
            otherArrowCSS:(()=>{const a=getComputedStyle(document.querySelector('#etnika-block-02-final .etnika-b02__arrow'));return {width:a.width,height:a.height,border:a.borderTopWidth,background:a.backgroundColor,svgWidth:getComputedStyle(document.querySelector('#etnika-block-02-final .etnika-b02__arrow svg')).width,svgBox:document.querySelector('#etnika-block-02-final .etnika-b02__arrow svg').getAttribute('viewBox')};})(),
            next:r(q+'.b05-next'),last:r(q+'.b05-item:last-child'),
            counter:r(q+'.b05-counter'),bodyWidth:document.documentElement.scrollWidth,
            imageOK:(()=>{let x=document.querySelector(q+'.b05-stage-image');return x.complete&&x.naturalWidth>0;})(),
            background:getComputedStyle(document.querySelector(q+'.b05-stage')).backgroundImage
          };
        }""")
        path=OUT/f'etnika-why-{w}x{h}.png'
        page.screenshot(path=str(path),full_page=False)
        print(f"WHY {w}x{h}: section={v['section']['top']:.1f}..{v['section']['bottom']:.1f}, shell={v['shell']['height']:.1f}, main={v['main']['height']:.1f}, computed={v['metrics']}, photo={v['stage']['top']:.1f}..{v['stage']['bottom']:.1f}, heading={v['title']['top']:.1f}..{v['title']['bottom']:.1f}, final={v['last']['bottom']:.1f}, caption={v['caption']['bottom']:.1f}, imageOK={v['imageOK']}, background={v['background']}",flush=True)
        err=lambda m:f'{w}x{h}: {m}: {v}'
        assert abs(v['stage']['top']-v['header']['bottom'])<4,err("photo does not start below fixed menu")
        assert abs(v['stage']['top']-v['section']['top'])<2,err("white padding strip above left photo")
        assert abs(v['section']['top']-v['header']['bottom'])<4,err("whole block should begin immediately below menu")
        assert v['metrics']['section']['paddingTop']=='0px',err("section still contains extra top padding")
        assert v['title']['top']>=v['header']['bottom']+6,err("title obscured by menu")
        # Editorial hierarchy: headline matches the one shared sitewide size.
        # All six advantages form a compact intentional stack, not a stretched grid.
        expected_title=max(62,min(w*.0625,118))
        assert abs(v['titleFont']-expected_title)<2.5,err(f"heading out of design-system scale: {v['titleFont']}, expected {expected_title}")
        assert 'Forum' in v['titleFamily'],err("heading font not Forum")
        assert len(v['listRows'])==6 and max(v['listRows'])<=82,err("selector rows stretched")
        assert max(v['listRows'])-min(v['listRows'])<=2,err("uneven selector heights")
        assert v['intro']['top']>=v['title']['bottom']+7,err("heading and intro collide")
        assert v['meta']['top']>=v['intro']['bottom']+7,err("intro and facts collide")
        assert v['list']['top']>=v['meta']['bottom']+7,err("facts and selectors collide")
        assert v['title']['top']>=v['copy']['top']+9,err("top content padding lost")
        assert v['last']['bottom']<=v['copy']['bottom']-9,err("bottom content padding lost")
        group_mid=(v['title']['top']+v['last']['bottom'])/2
        copy_mid=(v['copy']['top']+v['copy']['bottom'])/2
        assert abs(group_mid-copy_mid)<35,err("right-side composition not visually centered")
        print(f"TYPE {w}x{h}: Forum {v['titleFont']:.1f}px, rows {[round(n) for n in v['listRows']]}, centered delta={group_mid-copy_mid:.1f}px",flush=True)

        assert v['stage']['right']<=v['copy']['left']+2,err("photo is not left of copy")
        assert abs(v['stage']['bottom']-v['section']['bottom'])<4,err("photo is not full block height")
        assert v['last']['bottom']<=v['section']['bottom']-8,err("sixth advantage clipped")
        assert v['caption']['left']>=v['stage']['left']+8,err("photo caption clipped on left")
        assert v['caption']['right']<=v['stage']['right']-8,err("photo caption clipped on right")
        # The image and all photo-overlay elements obey the global site grid.
        # Shared ETNIKA layout: site content grid + a small extra horizontal
        # inset, and the SAME outer vertical field used for editorial
        # overlines/line-and-text in neighboring sections.
        shared_edge=max(180,(w-2600)/2) if w>=1920 else (max(40,(w-1320)/2) if w<=1440 else max(80,(w-1760)/2))
        edge=shared_edge+max(12,min(w*.01,20))
        vertical=max(72,min(h*.09,112))
        assert abs(v['caption']['left']-v['stage']['left']-edge)<2,err("caption not on expanded site grid")
        assert abs(v['counter']['left']-v['caption']['left'])<2,err("photo counter and caption misaligned")
        assert abs(v['nav']['right']-(v['stage']['right']-edge))<2,err("arrows not aligned to right photo inset")
        assert abs(v['counter']['top']-v['stage']['top']-vertical)<2,err("counter top inset differs from editorial field")
        assert abs(v['stage']['bottom']-v['bottom']['bottom']-vertical)<2,err("caption bottom inset differs from editorial field")
        assert edge>shared_edge and vertical>40,err("overlay inset has not increased")
        # Archive-photo correction (13 Nov): the old scale(1.035) cut off heads.
        # Keep the image unzoomed and use the approved slide focal point instead.
        assert v['imageTransform']=='none',err("portrait is zoomed and may crop its head")
        # Use precisely the same visible arrow vocabulary as the photo slider
        # in the 'ФОТОСТУДИЯ БЕЗ ФОТОГРАФА' block.
        for prop in ('width','height','border','background','svgWidth','svgBox'):
            assert v['arrowCSS'][prop]==v['otherArrowCSS'][prop],err(f"arrow differs from block 02: {prop}")
        assert v['arrowCSS']['navBorder']=='1px',err("photo arrows missing shared underline")
        print(f"PHOTO-GRID {w}x{h}: left/right inset {edge:.1f}, top/bottom inset {vertical:.1f}; arrows match block 02",flush=True)
        for key in ('bottom','caption','prev','next'):
            assert v[key]['bottom']<=v['stage']['bottom']-8,err(f"{key} clipped below photo")
        assert v['counter']['top']>=v['stage']['top']+6,err("counter hidden behind menu")
        assert v['bodyWidth']<=w+3,err("horizontal overflow")
        assert v['imageOK'] or 'etnika-hero-red-wide.jpg' in v['background'],err("photo failed to load and fallback absent")
        # Owner 2026-11-13: the section is intentionally 10svh taller
        # than the former one-screen version, while its top remains below nav.
        assert abs(v['section']['bottom']-h*1.10)<=4,err("taller section height not applied")
        assert abs(v['stage']['height']-(h*1.10-v['header']['height']))<=4,err("photo not stretched with taller section")
        assert v['bottom']['bottom']<=v['stage']['bottom']-40,err("caption missing bottom breathing room")
        assert v['last']['bottom']<=v['section']['bottom']-8,err("last advantage exceeds section")
        print(f"WHY ETNIKA OK {w}x{h}: photo ({v['stage']['top']:.1f}..{v['stage']['bottom']:.1f}), title {v['title']['top']:.1f}, last {v['last']['bottom']:.1f}, caption {v['caption']['bottom']:.1f}",flush=True)
        # Exercise the REAL fragment navigation, which is affected by the global
        # html scroll-padding and this section's own scroll-margin.
        page.evaluate("""() => document.getElementById('etnika-studio-features').scrollIntoView({behavior:'instant',block:'start'})""")
        page.wait_for_timeout(150)
        anchor=page.evaluate("""() => ({
          header:document.getElementById('etnika-site-header').getBoundingClientRect().bottom,
          photo:document.querySelector('#etnika-studio-features .b05-stage').getBoundingClientRect().top,
          heading:document.querySelector('#etnika-studio-features .b05-title').getBoundingClientRect().top,
          bottom:document.querySelector('#etnika-studio-features .b05-stage-bottom').getBoundingClientRect().bottom,
          last:document.querySelector('#etnika-studio-features .b05-item:last-child').getBoundingClientRect().bottom
        })""")
        print(f"ANCHOR {w}x{h}: {anchor}",flush=True)
        assert abs(anchor['photo']-anchor['header'])<=4,err("fragment scroll overlays photo with menu")
        assert anchor['heading']>=anchor['header']+6,err("fragment scroll hides heading under menu")
        assert anchor['bottom']<=h*1.10-8 and anchor['last']<=h*1.10-8,err("fragment scroll clips caption or final selector")
        # Show the bottom of the deliberately taller block as well, not only
        # its initial viewport; this catches hidden arrows/captions.
        page.evaluate("() => window.scrollBy({top:innerHeight*.10,behavior:'instant'})")
        page.wait_for_timeout(130)
        atBottom=page.evaluate("""() => ({
          stage:document.querySelector('#etnika-studio-features .b05-stage').getBoundingClientRect().bottom,
          caption:document.querySelector('#etnika-studio-features .b05-stage-bottom').getBoundingClientRect().bottom,
          last:document.querySelector('#etnika-studio-features .b05-item:last-child').getBoundingClientRect().bottom
        })""")
        assert abs(atBottom['stage']-h)<=4,err("taller block cannot scroll to photo bottom")
        assert atBottom['caption']<=h-35 and atBottom['last']<=h-7,err("overlay or text clipped after scrolling")
        page.screenshot(path=str(OUT/f'etnika-why-bottom-{w}x{h}.png'),full_page=False)
        if w==1366:
            # The old carousel had NO timer. Ensure slide 02 appears by itself
            # after six seconds without pressing any controls.
            initial=page.locator('#etnika-studio-features .b05-counter').inner_text().strip()
            assert initial=='01 / 06',f"Unexpected carousel start: {initial}"
            page.wait_for_timeout(6350)
            advanced=page.locator('#etnika-studio-features .b05-counter').inner_text().strip()
            assert advanced=='02 / 06',f"Carousel failed to advance automatically after 6s: {advanced}"
            assert page.locator('#etnika-studio-features .b05-item.is-active').get_attribute('data-index')=='1'
            # Clicking a manual selector still works and gets a fresh interval.
            page.locator('#etnika-studio-features .b05-item[data-index="4"]').click()
            assert page.locator('#etnika-studio-features .b05-counter').inner_text().strip()=='05 / 06'

            # Owner 13 Nov: after clicking an item and leaving the cursor on it,
            # the carousel must NOT rotate, even if the normal 6s has elapsed.
            page.wait_for_timeout(6350)
            assert page.locator('#etnika-studio-features .b05-counter').inner_text().strip()=='05 / 06', 'AUTOPLAY continued while mouse hovered over selected benefit'

            # Press and hold the mouse over that row, then drag out. The clock
            # must remain stopped until the pointer button is released.
            page.mouse.down()
            stage=page.locator('#etnika-studio-features .b05-stage').bounding_box()
            page.mouse.move(stage['x']+45,stage['y']+100,steps=4)
            page.wait_for_timeout(6350)
            assert page.locator('#etnika-studio-features .b05-counter').inner_text().strip()=='05 / 06', 'AUTOPLAY continued during mouse hold'

            # Release off-row; a fresh full six-second countdown should start.
            page.mouse.up()
            page.wait_for_timeout(6350)
            assert page.locator('#etnika-studio-features .b05-counter').inner_text().strip()=='06 / 06', 'AUTOPLAY did not resume after cursor left and mouse released'
            print('AUTOPLAY: advances in 6s, pauses on selected-item hover and press-hold, resumes after release and leave',flush=True)
        page.close()
    # Responsive safety: the same editorial breathing room must not push
    # the caption or arrows outside the image on tablets and phones.
    for w,h in [(1024,768),(390,844)]:
        page=browser.new_page(viewport={"width":w,"height":h},is_mobile=False)
        page.goto((ROOT/"site/index.html").as_uri(),wait_until="load",timeout=45000)
        page.evaluate("() => document.fonts.ready")
        page.evaluate("""() =>
          document.getElementById('etnika-studio-features')
            .scrollIntoView({block:'start',behavior:'instant'})""")
        page.wait_for_timeout(200)
        v=page.evaluate("""() => {
          const q=x=>document.querySelector('#etnika-studio-features '+x);
          const r=e=>e.getBoundingClientRect().toJSON();
          return {
            stage:r(q('.b05-stage')),top:r(q('.b05-stage-top')),
            bottom:r(q('.b05-stage-bottom')),caption:r(q('.b05-caption')),
            nav:r(q('.b05-nav')),counter:r(q('.b05-counter')),
            image: q('.b05-stage-image').naturalWidth
          };
        }""")
        x=(20 if w<=700 else 30)+max(8,min(w*.012,14))
        y=max(36,min(h*.06,60))
        err=lambda m:f"Responsive {w}x{h}: {m} {v}"
        assert abs(v['counter']['left']-v['stage']['left']-x)<2,err("counter horizontal inset")
        assert abs(v['caption']['left']-v['stage']['left']-x)<2,err("caption horizontal inset")
        assert abs(v['counter']['top']-v['stage']['top']-y)<2,err("counter editorial top inset")
        assert abs(v['stage']['bottom']-v['bottom']['bottom']-y)<2,err("caption editorial bottom inset")
        assert v['bottom']['top']>v['top']['bottom']+8,err("top and bottom overlays overlap")
        assert v['nav']['right']<v['stage']['right']-x+2,err("arrows exceed photo inset")
        assert v['image']>0,err("photo missing")
        page.screenshot(path=str(OUT/f'etnika-why-responsive-{w}x{h}.png'),full_page=False)
        print(f"RESPONSIVE PHOTO-GRID {w}x{h}: left/right {x:.1f}px, top/bottom {y:.1f}px; captions and arrows fit",flush=True)
        page.close()
    browser.close()
