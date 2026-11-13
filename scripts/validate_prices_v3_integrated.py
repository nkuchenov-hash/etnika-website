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
   let photo=q('.ev3-photo'),title=q('.ev3-title'),span=title.querySelector('span');
   const overline=q('.ev3-overline'),other=document.querySelector('#etnika-stories .etnika-editorial-top');
   let firstText=title.firstChild,range=document.createRange();
   range.selectNodeContents(firstText);let titleTextRects=[...range.getClientRects()].map(r);
   return {stage:r(q('.ev3-stage')),title:r(title),photo:r(q('.ev3-visual')),
     titleLineSame:!!titleTextRects.length && Math.abs(titleTextRects[0].top-span.getBoundingClientRect().top)<9,
     titleSpanDisplay:getComputedStyle(span).display,
     modeLeft:r(q('.ev3-modes')).left,
     modes:r(q('.ev3-modes')),
     titleRight:r(title).right,
     overlineCount:overline.children.length,
     overlineGrid:getComputedStyle(overline).display,
     overlineCols:getComputedStyle(overline).gridTemplateColumns.split(' ').length,
     overlineTextSize:getComputedStyle(overline).fontSize,
     otherOverlineSize:other?getComputedStyle(other).fontSize:null,
     pageWidth:document.documentElement.scrollWidth,font:getComputedStyle(q('.ev3-title')).fontFamily,
     dark:getComputedStyle(q('.ev3-plan[data-plan=express] .ev3-plan-name')).color,
     opacity:getComputedStyle(q('.ev3-plan[data-plan=express]')).opacity,
     photoLoaded:photo.complete&&photo.naturalWidth>0,
     rowTop:getComputedStyle(q('.ev3-plan')).borderTopWidth,
     rowHeights:[...root.querySelectorAll('.ev3-plan')].map(e=>e.getBoundingClientRect().height),
     titleFontSize:parseFloat(getComputedStyle(title).fontSize),
     referenceTitleSize:parseFloat(getComputedStyle(document.querySelector('#etnika-stories h2.etnika-section-heading')).fontSize),
     stageHeight:r(q('.ev3-stage')).height};
  }""")
  assert values['pageWidth']<=w+2,(w,'horizontal overflow',values)
  assert values['photoLoaded'],(w,'missing photo',values)
  assert values['overlineCount']==6,(w,'overline must share 6-cell structure',values)
  assert values['overlineGrid']=='grid',(w,'overline not using common editorial grid',values)
  assert values['overlineCols']==(6 if w>1100 else 3),(w,'wrong shared overline columns',values)
  assert values['overlineTextSize']==values['otherOverlineSize'],(w,'overline font differs from other sections',values)
  if w>=1360:
   assert values['titleLineSame'],(w,'title does not fit on one line at wide desktop width',values)
  if w>=1200:
   assert values['titleRight']+16<values['modeLeft'] or values['title']['bottom']+4<=values['modes']['top'],(w,'title overlaps day switch',values)
  day=page.evaluate("""() => {
    const root=document.querySelector('#etnika-prices-clear .ev3-modes');
    const active=root.querySelector('[aria-pressed=true]');
    const st=getComputedStyle(active);
    return {background:st.backgroundColor,color:st.color,height:active.getBoundingClientRect().height,
            label:getComputedStyle(root,'::before').content};
  }""")
  assert day['background']=='rgb(169, 21, 29)' and day['color']=='rgb(255, 255, 255)',(w,'selected day is not prominent',day)
  assert day['height']>=48 and 'ДЕНЬ СЪЁМКИ' in day['label'],(w,'day selector lacks size or label',day)
  assert values['opacity']=='1',(w,'faded plans',values)
  assert values['rowTop']=='0px',(w,'unwanted rule',values)
  assert values['dark']=='rgb(24, 23, 23)',(w,'muted plan names',values)
  assert values['stage']['top']>=values['title']['bottom']+18,(w,'heading cramped',values)
  assert 'Forum' in values['font'],(w,'heading font',values)
  if w>=1200:
   assert abs(values['titleFontSize']-values['referenceTitleSize'])<1,(w,'pricing heading differs from shared H2',values)
   assert values['stageHeight']<=675,(w,'oversized editorial stage',values)
   assert 115<=min(values['rowHeights']) and max(values['rowHeights'])<=215,(w,'editorial tariff rows are out of proportion',values)
   assert values['stageHeight']>=430,(w,'stage became too small',values)
  page.locator('.ev3-modes [data-mode=weekend]').click()
  assert page.locator('.ev3-plan[data-plan=premium] .ev3-plan-price').inner_text().strip()=='9 000 ₽'
  page.locator('.ev3-plan[data-plan=premium]').click()
  page.locator('.ev3-details-open').click()
  assert page.locator('.ev3-sheet').get_attribute('data-open')=='true'
  page.wait_for_timeout(600)  # Wait for 480ms slide-in before measuring the panel's final bounds.
  assert page.locator('.ev3-feature-list li').count()==10
  geometry=page.evaluate("""() => {
    const r=s=>document.querySelector(s).getBoundingClientRect();
    const panel=r('#etnika-prices-clear .ev3-sheet-panel');
    const footer=r('#etnika-prices-clear .ev3-sheet-footer');
    const prices=[...document.querySelectorAll('#etnika-prices-clear .ev3-plan-price')].map(e=>e.getBoundingClientRect());
    const backdrop=getComputedStyle(document.querySelector('#etnika-prices-clear .ev3-scrim'));
    return {top:panel.top, bottom:panel.bottom, right:panel.right, left:panel.left,
      width:panel.width, footerBottom:footer.bottom,
      priceRight:Math.max(...prices.map(x=>x.right)),
      backdropOpacity:parseFloat(backdrop.opacity),backdropPointer:backdrop.pointerEvents};
  }""")
  assert abs(geometry['top'])<=2 and abs(geometry['bottom']-h)<=2,(w,'tariff sheet must fill entire viewport height',geometry)
  assert abs(geometry['right']-w)<=2,(w,'tariff sheet must slide from screen right edge',geometry)
  assert geometry['footerBottom']<=h+2,(w,'booking footer is clipped below viewport',geometry)
  if w>=1101:
   assert geometry['left']>=geometry['priceRight']+16,(w,'full-height drawer covers tariff prices',geometry)
   assert geometry['backdropOpacity']==0 and geometry['backdropPointer']=='none',(w,'backdrop obscures prices',geometry)
  else:
   assert geometry['width']>=min(800,w*.94)-4,(w,'mobile drawer too narrow',geometry)
  page.wait_for_timeout(520)
  page.screenshot(path=str(OUT/f'etnika-v3-integrated-panel-{w}x{h}.png'))
  page.keyboard.press('Escape')
  assert page.locator('.ev3-sheet').get_attribute('data-open')=='false'
  page.screenshot(path=str(OUT/f'etnika-v3-integrated-{w}x{h}.png'))
  # Assert the real header navigation brings the top of the prices section
  # below the fixed header; a full-page screenshot hides this regression.
  navlink=page.locator('#etnika-site-header .esh__nav a[href="#etnika-prices-clear"]')
  if navlink.count() and w>1100:
   navlink.click()
   page.wait_for_timeout(950)
   anchor=page.evaluate("""() => {
     let root=document.querySelector('#etnika-prices-clear');
     let header=document.querySelector('#etnika-site-header');
     const box=(s)=>root.querySelector(s).getBoundingClientRect().toJSON();
     return {headerBottom:header.getBoundingClientRect().bottom,
       overline:box('.ev3-overline'),
       title:box('.ev3-title'),
       stage:box('.ev3-stage'),
       section:root.getBoundingClientRect().toJSON(),
       stageHeight:box('.ev3-stage').height,
       titleSize:parseFloat(getComputedStyle(root.querySelector('.ev3-title')).fontSize)};
   }""")
   assert anchor['overline']['top']>=anchor['headerBottom']+8,(w,'section top clipped by navigation',anchor)
   assert anchor['title']['top']>=anchor['headerBottom']+35,(w,'title under fixed header',anchor)
   assert anchor['stageHeight']<=675,(w,'editorial stage exceeds design bounds',anchor)
   assert anchor['section']['height']<=h+240,(w,'pricing section has excessive scrolling',anchor)
   page.screenshot(path=str(OUT/f'etnika-v3-anchor-{w}x{h}.png'))

  print(f'PASS full site {w}x{h}: no fade, correct prices, header spacing and readable drawer',flush=True)
  page.close()
 browser.close()
