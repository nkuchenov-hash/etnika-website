#!/usr/bin/env python3
"""Check eight unique B02 full-height photos: no subject cropping or repeats."""
from pathlib import Path
import hashlib
import math
import re
import shutil
import time
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'site/index.html').read_text(encoding='utf-8')
B02=HTML.split('<section id="etnika-block-02-final"',1)[1].split('</section>',1)[0]
FILES=re.findall(r'<img[^>]*class="etnika-b02__slide[^"]*"[^>]*src="([^"]+)"',B02,re.S)
assert len(FILES)==8, f'B02 must have eight real photographs, got: {FILES}'
assert len(FILES)==len(set(FILES)),f'Duplicate photo inside B02: {FILES}'
assert all(x.startswith('assets/b02/framed/') for x in FILES),FILES
others=HTML.replace(B02,'')
for filename in FILES:
 assert filename not in others, f'B02 photo reused in another site section: {filename}'
 assert (ROOT/'site'/filename).is_file(), f'Missing published photo: {filename}'
 assert filename not in HTML.split('<section id="etnika-prices-clear"',1)[-1],f'Tariff duplicate: {filename}'
print('PASS UNIQUE B02 PHOTOS: 8, no cross-section file reuse',flush=True)

original_dimensions={}
hashes=[]
for name in FILES:
 p=ROOT/'site'/name
 orig=ROOT/'site'/name.replace('/framed/','/')
 with Image.open(p) as im,Image.open(orig) as source:
  ow,oh=source.size
  w,h=im.size
  margin=(w-ow)/2
  assert 0.953 <= w/h <= 0.956,(name,w,h)
  assert margin>=200,(name,w,ow)
  assert h==oh,(name,h,oh)
  original_dimensions[name]=(ow,oh,margin)
  hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
  print(f'PHOTO_FILE {name} original={ow}x{oh} adapted={w}x{h} safe_side_margin={margin}',flush=True)
assert len(set(hashes))==len(hashes),'Duplicate B02 pixels'
URL='https://nkuchenov-hash.github.io/etnika-website/site/?b02-uncropped-check=20261113'
OUT=ROOT/'reports'/'b02-framing'
OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 chrome=shutil.which('google-chrome') or shutil.which('google-chrome-stable')
 browser=p.chromium.launch(headless=True,executable_path=chrome) if chrome else p.chromium.launch(headless=True)
 for width,height in [(1366,768),(1660,930),(1920,1080),(390,844)]:
  page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
  for attempt in range(18):
   page.goto(URL+f'&size={width}&attempt={attempt}',wait_until='domcontentloaded',timeout=45000)
   if page.locator('#etnika-b02-uncropped-photos-20261113').count() and page.locator('#etnika-block-02-final img[src*="/framed/"]').count()==8:
    break
   if attempt==17:raise AssertionError(f'Unpublished B02 photo markup at {width}x{height}')
   time.sleep(2)
  page.evaluate('() => document.fonts.ready')
  photos=page.locator('#etnika-block-02-final img.etnika-b02__slide')
  page.evaluate("""async () => {
    await Promise.all([...document.querySelectorAll('#etnika-block-02-final img.etnika-b02__slide')].map(i=>i.decode()));
  }""")
  for i,name in enumerate(FILES):
   props=photos.nth(i).evaluate("""e => {
     const r=e.getBoundingClientRect(),c=getComputedStyle(e);
     const stage=e.parentElement.getBoundingClientRect();
     return {src:new URL(e.currentSrc).pathname.split('/site/')[1],
       naturalW:e.naturalWidth,naturalH:e.naturalHeight,
       stageW:stage.width,stageH:stage.height,fit:c.objectFit,
       position:c.objectPosition,opacity:c.opacity,transform:c.transform};
   }""")
   assert props['src']==name,(name,props)
   assert props['naturalW']>0 and props['naturalH']>0,(name,props)
   ow,oh,margin=original_dimensions[name]
   if width>=1101:
    assert props['fit']=='cover',props
    scale=max(props['stageW']/props['naturalW'],props['stageH']/props['naturalH'])
    crop_x=(props['naturalW']-props['stageW']/scale)/2
    crop_y=(props['naturalH']-props['stageH']/scale)/2
    assert crop_x < margin-30,(name,props,crop_x,margin)
    assert crop_y < 2,(name,props,crop_y)
    print(f'PASS FRAME {width}x{height} photo={i+1}/{len(FILES)} full_subject=true '
          f'background_crop_x={max(0,crop_x):.1f}px original_protection={margin:.1f}px',flush=True)
   else:
    assert props['fit']=='contain',props
    print(f'PASS MOBILE {width}x{height} photo={i+1}/{len(FILES)} fits_entire_frame=true',flush=True)
   if width in (1660,390):
    photos.nth(i).evaluate("""(e)=>{
       const slides=[...e.parentElement.querySelectorAll('img.etnika-b02__slide')];
       slides.forEach(x=>{x.classList.remove('is-active','is-entering');x.style.transition='none'});
       e.classList.add('is-active');
    }""")
    page.wait_for_timeout(60)
    page.locator('#etnika-block-02-final .etnika-b02__media').screenshot(
       path=str(OUT/f'b02-{width}x{height}-{i+1:02d}.png'))
  page.close()
 browser.close()
print('PASS PUBLISHED SITE: 8 unique photographs, no crop of actual people, desktop and mobile',flush=True)
