#!/usr/bin/env python3
"""Owner regression: the B02 content fits the visible screen and B02/SPACE
editorial labels share horizontal guides. Validate actual rendered geometry."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports'
OUT.mkdir(exist_ok=True)

def near(a,b,slack=3):
    return abs(a-b)<=slack

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    for w,h in [(1366,768),(1440,900),(1618,928),(1662,896),(1920,1080),(2048,1145)]:
        page=browser.new_page(viewport={'width':w,'height':h})
        page.goto((ROOT/'site/index.html').as_uri(),wait_until='load',timeout=45000)
        page.evaluate('() => document.fonts.ready')
        page.wait_for_function("() => document.querySelector('#etnika-review-flow > section')?.id==='etnika-hero'")
        page.evaluate("""() => {
          const header=document.getElementById('etnika-site-header');
          const b02=document.getElementById('etnika-block-02-final');
          window.scrollTo({top:b02.getBoundingClientRect().top+scrollY-header.getBoundingClientRect().height,behavior:'instant'});
        }""")
        page.wait_for_timeout(200)
        v=page.evaluate("""() => {
            const q=s=>document.querySelector(s);
            const rect=e=>e.getBoundingClientRect().toJSON();
            const b=q('#etnika-block-02-final'),space=q('#etnika-space-photo');
            const top=q('#etnika-block-02-final .etnika-b02__top');
            const stop=q('#etnika-space-photo .spf-top');
            const feat=q('#etnika-block-02-final .etnika-b02__features');
            const media=q('#etnika-block-02-final .etnika-b02__media');
            const box=(el)=>rect(el);
            return {
              header:box(q('#etnika-site-header')),
              block:box(b),media:box(media),
              overline:box(top),topLabel:box(top.children[0]),topAccent:box(top.children[2]),
              spaceOverline:box(stop),spaceLabel:box(stop.children[0]),spaceAccent:box(stop.children[2]),
              title:box(q('#etnika-block-02-final .etnika-b02__title')),
              description:box(q('#etnika-block-02-final .etnika-b02__description')),
              features:box(feat),

              lastFeature:box(feat.lastElementChild),
              overlayTop:box(q('#etnika-block-02-final .etnika-b02__media-top')),
              overlayBottom:box(q('#etnika-block-02-final .etnika-b02__media-bottom')),
              counter:box(q('#etnika-block-02-final .etnika-b02__counter')),
              stamp:box(q('#etnika-block-02-final .etnika-b02__stamp')),
              caption:box(q('#etnika-block-02-final .etnika-b02__caption')),
              prev:box(q('#etnika-block-02-final .etnika-b02__arrow--prev')),
              next:box(q('#etnika-block-02-final .etnika-b02__arrow--next')),
              bottomControls:box(q('#etnika-block-02-final .etnika-b02__controls')),
              heroHeight:box(q('#etnika-hero')).height,
              pictureOk:[...media.querySelectorAll('img')].some(i=>i.complete&&i.naturalWidth>0),
              bodyWidth:document.documentElement.scrollWidth,
            };
        }""")
        err=lambda msg:f'{w}x{h}: {msg}: {v}'
        assert near(v['topLabel']['left'],v['spaceLabel']['left'],2),err('ETNIKA label not at shared left guide')
        assert near(v['topAccent']['left'],v['spaceAccent']['left'],3),err('red overline accent columns not aligned')
        assert v['overline']['top']>=v['header']['bottom']+8,err('top editorial label hidden under menu')
        assert v['features']['bottom']<=h-12,err('BOTTOM FEATURE ROW IS BELOW THE VISIBLE SCREEN')
        assert v['features']['top']>v['description']['bottom']-2,err('features collide with description')
        assert v['title']['top']>=v['overline']['bottom']+25,err('editorial header collides with title')
        assert v['pictureOk'],err('hero/second-block photograph failed to load')
        assert near(v['media']['height'],v['block']['height'],3),err('photo not filling full section')

        assert v['bodyWidth']<=w+2,err('horizontal overflow')
        assert v['counter']['top']>=v['header']['bottom']+8,err('photo counter hidden under sticky navigation')
        assert v['stamp']['top']>=v['header']['bottom']+8,err('Moscow photo stamp hidden under menu')
        assert v['stamp']['bottom']<=h-50,err('photo stamp extends below screen')
        assert v['overlayBottom']['bottom']<=h-18,err('PHOTO CAPTION/ARROWS BELOW THE SCREEN')
        assert v['caption']['bottom']<=h-18,err('photo description below screen')
        assert v['prev']['bottom']<=h-18 and v['next']['bottom']<=h-18,err('carousel arrows below screen')
        assert v['overlayBottom']['top']>v['header']['bottom']+60,err('photo caption collides with top overlays')
        path=OUT/f'etnika-b02-space-guides-{w}x{h}.png'
        page.screenshot(path=str(path),full_page=False)
        print(f"PASS GUIDES {w}x{h}: labels {v['topLabel']['left']:.1f}/{v['spaceLabel']['left']:.1f}, accents {v['topAccent']['left']:.1f}/{v['spaceAccent']['left']:.1f}, features bottom {v['features']['bottom']:.1f} < screen {h}, photo {v['media']['height']:.1f}px, stamp top {v['stamp']['top']:.1f}, photo caption bottom {v['overlayBottom']['bottom']:.1f}",flush=True)
        page.close()
    browser.close()
