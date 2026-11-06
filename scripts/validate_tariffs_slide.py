#!/usr/bin/env python3
"""Viewport and behavior regression for ETNIKA B-08 restored tariff design."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports'; OUT.mkdir(exist_ok=True)
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True)
 for name in ('index.html','review-2026-11.html'):
  for w,h in ((1920,1080),(1662,896),(1366,768),(390,844),(375,667)):
   p=b.new_page(viewport={'width':w,'height':h})
   p.goto((ROOT/'site'/name).as_uri(),wait_until='domcontentloaded',timeout=45000)
   p.evaluate('() => document.fonts.ready')
   p.locator('#etnika-prices-clear').scroll_into_view_if_needed()
   data=p.evaluate("""() => {
    const root=document.querySelector('#etnika-prices-clear'),q=s=>root.querySelector(s);
    const rect=s=>q(s).getBoundingClientRect().toJSON();
    const measure=document.createElement('div');measure.style.fontSize='var(--etnika-section-title)';document.body.appendChild(measure);
    const expected=parseFloat(getComputedStyle(measure).fontSize);measure.remove();
    const photo=q('.t7-photo');
    return {overflow:document.documentElement.scrollWidth-innerWidth,
      title:parseFloat(getComputedStyle(q('.t7-title')).fontSize),expected,
      titleFont:getComputedStyle(q('.t7-title')).fontFamily,
      visual:rect('.t7-visual'),heading:rect('.t7-title'),list:rect('.t7-list'),
      rows:[...root.querySelectorAll('.t7-plan')].map(e=>e.getBoundingClientRect().toJSON()),
      prices:[...root.querySelectorAll('.t7-cost')].map(e=>e.textContent.trim()),
      photoOk:photo.complete&&photo.naturalWidth>0,
      panelHidden:q('.t7-slide').getAttribute('aria-hidden')==='true'};
   }""")
   def check(v,msg):
    assert v, f'{name} {w}x{h} {msg}: {data}'
   check(data['overflow']<=2,'horizontal overflow')
   check(abs(data['title']-data['expected'])<1,'title scale')
   check('Forum' in data['titleFont'],'title family')
   check(data['prices']==['2 900 ₽','4 500 ₽','7 500 ₽'],'weekday prices')
   check(data['photoOk'],'photo not loading')
   check(data['visual']['height']>= (400 if w>=901 else 440),'photo too small')
   check(data['panelHidden'],'closed panel visible')
   for a,c in zip(data['rows'],data['rows'][1:]):check(c['top']>=a['bottom']-1,'overlapping row')
   if w>=901:
    check(data['rows'][0]['height']>110,'tariff rows cramped')
    check(data['visual']['left']>=data['list']['right']+20,'insufficient horizontal spacing')
    check(data['visual']['top']>=data['heading']['bottom']+14,'title and content cramped')
   p.screenshot(path=str(OUT/f'etnika-tariffs-{name.replace(".html","")}-{w}x{h}.png'))
   p.locator('.t7-mode [data-mode=weekend]').click()
   check(p.locator('.t7-plan[data-plan=standard] .t7-cost').inner_text().strip()=='5 900 ₽','weekend price')
   p.locator('.t7-plan[data-plan=premium]').click()
   check(p.locator('.t7-plan[data-plan=premium] .t7-cost').inner_text().strip()=='9 000 ₽','premium price')
   p.locator('.t7-more').click()
   check(p.locator('.t7-slide').get_attribute('aria-hidden')=='false','slide did not open')
   check(p.locator('.t7-features li').count()==10,'premium inclusions lost')
   p.screenshot(path=str(OUT/f'etnika-tariffs-drawer-{name.replace(".html","")}-{w}x{h}.png'))
   p.keyboard.press('Escape')
   check(p.locator('.t7-slide').get_attribute('aria-hidden')=='true','Escape failed')
   p.locator('.t7-plan[data-plan=express]').click()
   p.locator('.t7-more').click()
   check(p.locator('.t7-features li').count()==6,'express inclusions lost')
   p.locator('.t7-close').click()
   check(p.locator('.t7-slide').get_attribute('aria-hidden')=='true','close failed')
   print(f'PASS {name} {w}x{h}: title {data["title"]}, photo {data["visual"]["height"]:.0f}, sliding drawer, pricing',flush=True)
   p.close()
 b.close()
