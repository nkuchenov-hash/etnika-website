#!/usr/bin/env python3
"""ETNIKA B-08 v3 isolated visual and interaction checks."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports'
OUT.mkdir(exist_ok=True)
PATH=(ROOT/'site/prices-review-v3.html').as_uri()
SIZES=[(1920,1080),(1662,896),(1366,768),(1280,720),(1024,768),(390,844),(375,667)]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 for w,h in SIZES:
  page=browser.new_page(viewport={"width":w,"height":h},device_scale_factor=1)
  errors=[]
  page.on("pageerror",lambda error:errors.append(str(error)))
  page.goto(PATH,wait_until="load",timeout=30000)
  page.evaluate("() => document.fonts.ready")
  info=page.evaluate("""() => {
    const root=document.querySelector('#etnika-prices-clear');
    const q=s=>root.querySelector(s),r=e=>e.getBoundingClientRect().toJSON();
    const title=q('.ev3-title'),photo=q('.ev3-photo');
    const f=document.createElement('div');f.style.fontSize='var(--etnika-section-title)';
    document.body.appendChild(f);const expected=parseFloat(getComputedStyle(f).fontSize);f.remove();
    const rows=[...root.querySelectorAll('.ev3-plan')];
    const first=rows[0];
    return {pageWidth:document.documentElement.scrollWidth,expected,titleSize:parseFloat(getComputedStyle(title).fontSize),
      titleFont:getComputedStyle(title).fontFamily, title:r(title), stage:r(q('.ev3-stage')),
      photo:r(q('.ev3-visual')), photoNaturalWidth:photo.naturalWidth,
      rows:rows.map(e=>r(e)),rowOpacity:getComputedStyle(first).opacity,
      rowNameOpacity:getComputedStyle(first.querySelector('.ev3-plan-name')).opacity,
      rowTopBorder:getComputedStyle(first).borderTopWidth,
      rowColor:getComputedStyle(first.querySelector('.ev3-plan-name')).color,
      modes:[...root.querySelectorAll('.ev3-modes button')].map(x=>x.getAttribute('aria-pressed')),
      prices:rows.map(x=>x.querySelector('.ev3-plan-price').textContent.trim())
    };
  }""")
  def verify(flag,msg):
   assert flag,f"FAIL {w}x{h}: {msg}: {info}; JS errors: {errors}"
  verify(not errors,"JS runtime error")
  verify(info["pageWidth"]<=w+2,"horizontal overflow")
  verify(abs(info["expected"]-info["titleSize"])<=1,"heading deviates from design token")
  verify("Forum" in info["titleFont"],"heading font")
  verify(info["rowOpacity"]=="1" and info["rowNameOpacity"]=="1","unselected row faded")
  verify(info["rowColor"] in ("rgb(24, 23, 23)","rgb(25, 25, 25)"),"unselected name isn't black")
  verify(info["rowTopBorder"]=="0px","extra line immediately below heading")
  verify(info["prices"]==["2 900 ₽","4 500 ₽","7 500 ₽"],"weekday prices")
  verify(info["photoNaturalWidth"]>0,"photo doesn't load")
  verify(info["photo"]["width"]>=300 and info["photo"]["height"]>=440,"photo too small")
  if w>=901:
   verify(info["stage"]["top"]>info["title"]["bottom"]+20,"heading and tariffs too close")
   verify(all(x["height"]>=(115 if h<=810 else 125) for x in info["rows"]),"tariff rows cramped")
  verify(all(b["top"]>=a["bottom"]-1 for a,b in zip(info["rows"],info["rows"][1:])),"rows overlap")
  page.screenshot(path=str(OUT/f"etnika-prices-v3-{w}x{h}.png"),full_page=True)
  page.locator(".ev3-modes [data-mode=weekend]").click()
  verify(page.locator(".ev3-plan[data-plan=standard] .ev3-plan-price").inner_text().strip()=="5 900 ₽","weekend standard price")
  page.locator(".ev3-plan[data-plan=premium]").click()
  verify(page.locator(".ev3-plan[data-plan=premium] .ev3-plan-price").inner_text().strip()=="9 000 ₽","weekend premium price")
  page.locator(".ev3-details-open").click()
  verify(page.locator(".ev3-sheet").get_attribute("data-open")=="true","drawer did not open")
  verify(page.locator(".ev3-feature-list li").count()==10,"premium features missing")
  verify(page.locator(".ev3-sheet-panel").evaluate("(x)=>x.getBoundingClientRect().width")>=(min(950,w*.79)-2 if w>=901 else w*.95),"drawer is too narrow")
  verify(page.locator(".ev3-feature-list li").first.evaluate("(x)=>parseFloat(getComputedStyle(x).fontSize)")>=16,"drawer text too small")
  page.wait_for_timeout(550)
  page.screenshot(path=str(OUT/f"etnika-prices-v3-open-{w}x{h}.png"))
  page.keyboard.press("Escape")
  verify(page.locator(".ev3-sheet").get_attribute("data-open")=="false","drawer Escape close failed")
  page.locator(".ev3-plan[data-plan=express]").click()
  page.locator(".ev3-details-open").click()
  verify(page.locator(".ev3-feature-list li").count()==6,"express features missing")
  page.locator(".ev3-close").click()
  verify(page.locator(".ev3-sheet").get_attribute("data-open")=="false","drawer close button failed")
  verify(not errors,"late JS runtime errors")
  print(f"PASS {w}x{h}: rows {[round(x['height']) for x in info['rows']]}; photo {round(info['photo']['width'])}x{round(info['photo']['height'])}, wide drawer, prices, Escape",flush=True)
  page.close()
 browser.close()
