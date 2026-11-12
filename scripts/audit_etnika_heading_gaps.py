#!/usr/bin/env python3
"""Measure actual kicker-to-heading gaps on published ETNIKA desktop layouts."""
from pathlib import Path
import re, shutil, os, time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
EXPECTED=re.search(r'<meta name="etnika-build" content="([^"]+)"',(ROOT/'site/index.html').read_text(encoding='utf-8')).group(1)
URL='https://nkuchenov-hash.github.io/etnika-website/site/?gap-audit=20261112'
PAIRS={
  'B02 Фотостудия':('#etnika-block-02-final .etnika-b02__top','#etnika-block-02-final .etnika-b02__title'),
  'Пространство ЭТНИКА':('#etnika-space-photo .spf-top','#etnika-space-photo .spf-title'),
  'Истории гостей':('#etnika-stories .stories-top','#etnika-stories .stories-title'),
  'FAQ перед визитом':('#etnika-faq .faq-top','#etnika-faq .faq-title'),
  'Цены и тарифы':('#etnika-prices-clear .ev3-overline','#etnika-prices-clear .ev3-title'),
  'FAQ по тарифам':('#etnika-faq-tariffs .faq-top','#etnika-faq-tariffs .faq-title'),
  'Отзывы':('#etnika-reviews .etnika-reviews-overline','#etnika-reviews .etnika-reviews-heading'),
}
with sync_playwright() as p:
 chrome=shutil.which('google-chrome') or shutil.which('google-chrome-stable')
 browser=p.chromium.launch(headless=True,executable_path=chrome) if chrome else p.chromium.launch(headless=True)
 for w,h in [(390,844),(768,1024),(1024,768),(1200,800),(1440,900),(1660,930),(1920,1080)]:
  page=browser.new_page(viewport={'width':w,'height':h})
  for attempt in range(18):
   page.goto(URL+f'&sha={os.environ.get("GITHUB_SHA","manual")[:12]}&attempt={attempt}',wait_until='domcontentloaded',timeout=40000)
   ready=page.evaluate('() => !!document.getElementById("etnika-unified-editorial-heading-gaps-20261112")')
   if ready: break
   if attempt==17: raise AssertionError('Published CSS not available after 18 attempts')
   time.sleep(2)
  page.evaluate('() => document.fonts.ready')
  page.wait_for_timeout(250)
  build=page.locator('meta[name="etnika-build"]').get_attribute('content')
  assert build==EXPECTED,(build,EXPECTED)
  readings={}
  for name,(k,t) in PAIRS.items():
   d=page.evaluate("""([a,b])=>{
    const first=document.querySelector(a),last=document.querySelector(b);
    if(!first || !last)return null;
    const k=first.getBoundingClientRect(),h=last.getBoundingClientRect();
    const st=getComputedStyle(first),par=getComputedStyle(first.parentElement);
    return {gap:Math.round((h.top-k.bottom)*100)/100,overlineTop:k.top,overlineBottom:k.bottom,
      headingTop:h.top,marginBottom:st.marginBottom,parentGap:par.rowGap,display:st.display,
      visible:st.display!=='none' && k.height>0};
   }""",[k,t])
   assert d is not None and d['visible'],(name,d)
   readings[name]=d['gap']
   print('AUDIT',f'{w}x{h}',name,d,flush=True)
  baseline=readings['Пространство ЭТНИКА']
  for name,gap in readings.items():
   assert abs(gap-baseline)<=1.25, f'{w}x{h}: {name} gap={gap}px, approved reference={baseline}px'
  print('PASS ALL EDITORIAL HEADING GAPS',f'{w}x{h}',f'approved={baseline}px',readings,flush=True)
  page.close()
 browser.close()
