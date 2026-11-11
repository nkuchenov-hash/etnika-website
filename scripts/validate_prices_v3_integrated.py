#!/usr/bin/env python3
"""Validate ETNIKA v3 tariff block in the actual complete site, not just prototype."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports';OUT.mkdir(exist_ok=True)
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True)
 for w,h in [(1920,1080),(1662,896),(1366,768),(390,844),(375,667)]:
  page=browser.new_page(viewport={'width':w,'height':h},device_scale_factor=1)
  page.goto((ROOT/'site/index.html').as_uri(),wait_until='load',timeout=50000)
  page.locator('#etnika-prices-clear.ev3[data-ev3-initialized=true]').wait_for(timeout=12000)
  page.evaluate('() => document.fonts.ready')
  block=page.locator('#etnika-prices-clear.ev3')
  block.scroll_into_view_if_needed()
  values=page.evaluate("""() => {
   let root=document.querySelector('#etnika-prices-clear.ev3');
   let q=s=>root.querySelector(s),r=e=>e.getBoundingClientRect().toJSON();
   let photo=q('.ev3-photo');
   return {stage:r(q('.ev3-stage')),title:r(q('.ev3-title')),photo:r(q('.ev3-visual')),
     pageWidth:document.documentElement.scrollWidth,font:getComputedStyle(q('.ev3-title')).fontFamily,
     dark:getComputedStyle(q('.ev3-plan[data-plan=express] .ev3-plan-name')).color,
     opacity:getComputedStyle(q('.ev3-plan[data-plan=express]')).opacity,
     photoLoaded:photo.complete&&photo.naturalWidth>0,
     rowTop:getComputedStyle(q('.ev3-plan')).borderTopWidth};
  }""")
  assert values['pageWidth']<=w+2,(w,'horizontal overflow',values)
  assert values['photoLoaded'],(w,'missing photo',values)
  assert values['opacity']=='1',(w,'faded plans',values)
  assert values['rowTop']=='0px',(w,'unwanted rule',values)
  assert values['dark']=='rgb(24, 23, 23)',(w,'muted plan names',values)
  assert values['stage']['top']>=values['title']['bottom']+18,(w,'heading cramped',values)
  assert 'Forum' in values['font'],(w,'heading font',values)
  page.locator('.ev3-modes [data-mode=weekend]').click()
  assert page.locator('.ev3-plan[data-plan=premium] .ev3-plan-price').inner_text().strip()=='9 000 ₽'
  page.locator('.ev3-plan[data-plan=premium]').click()
  page.locator('.ev3-details-open').click()
  assert page.locator('.ev3-sheet').get_attribute('data-open')=='true'
  page.wait_for_timeout(600)  # Wait for 480ms slide-in before measuring the panel's final bounds.
  assert page.locator('.ev3-feature-list li').count()==10
  if w>900:
   # On a desktop the sheet is confined to the photograph, not over tariff prices.
   geometry=page.evaluate("""() => {
     const a=document.querySelector('#etnika-prices-clear .ev3-sheet-panel').getBoundingClientRect();
     const b=document.querySelector('#etnika-prices-clear .ev3-visual').getBoundingClientRect();
     const prices=[...document.querySelectorAll('#etnika-prices-clear .ev3-plan-price')].map(el=>el.getBoundingClientRect());
     return {panelLeft:a.left,panelRight:a.right,photoLeft:b.left,photoRight:b.right,
       priceRight:Math.max(...prices.map(p=>p.right))};
   }""")
   assert geometry['panelLeft']>=geometry['priceRight']+4,(w,'sheet overlaps prices',geometry)
   assert abs(geometry['panelLeft']-geometry['photoLeft'])<=3,(w,'sheet must dock to photograph',geometry)
   assert abs(geometry['panelRight']-geometry['photoRight'])<=3,(w,'sheet must not exceed photograph',geometry)
  else:
   assert page.locator('.ev3-sheet-panel').evaluate('(x)=>x.getBoundingClientRect().width')>=min(800,w*.94)-3
  page.wait_for_timeout(520)
  page.screenshot(path=str(OUT/f'etnika-v3-integrated-panel-{w}x{h}.png'))
  page.keyboard.press('Escape')
  assert page.locator('.ev3-sheet').get_attribute('data-open')=='false'
  page.screenshot(path=str(OUT/f'etnika-v3-integrated-{w}x{h}.png'))
  print(f'PASS full site {w}x{h}: no fade, correct prices, header spacing and readable drawer',flush=True)
  page.close()
 browser.close()
