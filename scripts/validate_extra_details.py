#!/usr/bin/env python3
"""Browser regression: Extra Details must show complete prices and readable labels."""
import json
from pathlib import Path
from threading import Thread
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)
PORT = 18764
handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT))
server = ThreadingHTTPServer(("127.0.0.1", PORT), handler)
thread = Thread(target=server.serve_forever, daemon=True)
thread.start()

JS = r"""() => {
  const section = document.querySelector('#etnika-extra');
  const rect = el => el.getBoundingClientRect();
  const rgb = v => (v.match(/[0-9.]+/g)||[]).slice(0,3).map(Number);
  const lum = color => {
    const v=rgb(color).map(x=>x/255).map(x=>x<=.04045?x/12.92:Math.pow((x+.055)/1.055,2.4));
    return v[0]*.2126 + v[1]*.7152 + v[2]*.0722;
  };
  const contrast = color => (1.05)/(lum(color)+.05); // section background is white
  const items=[...section.querySelectorAll('.ee-item')];
  return {
    section:rect(section).toJSON(),
    prices:items.map(item=>{
      const box=item.querySelector('.ee-price-number');
      const price=item.querySelector('.ee-item-price');
      const style=getComputedStyle(box);
      const canvas=document.createElement('canvas');
      const ctx=canvas.getContext('2d');
      ctx.font=style.font;
      const metric=ctx.measureText(box.textContent.trim());
      const note=price.querySelector('small');
      const label=item.querySelector('.ee-item-title');
      const noteStyle=note?getComputedStyle(note):null;
      const labelStyle=getComputedStyle(label);
      const b=rect(box),outer=rect(price),sectionBox=rect(section);
      const overflowParent=[item,price,box].map(el=>getComputedStyle(el).overflow);
      return {
        text:box.textContent.trim(), numberBoxHeight:b.height,
        glyphInkHeight:metric.actualBoundingBoxAscent+metric.actualBoundingBoxDescent,
        fullyInsideContainer:b.bottom<=outer.bottom+1 && b.top>=outer.top-1,
        fullyInsideSection:b.bottom<=sectionBox.bottom-8,
        overflows:overflowParent, priceFont:style.fontFamily,
        labelFontPx:parseFloat(labelStyle.fontSize),
        labelWeight:labelStyle.fontWeight,
        labelContrast:contrast(labelStyle.color),
        note:note?.textContent.trim()||null,
        noteFontPx:noteStyle?parseFloat(noteStyle.fontSize):null,
        noteContrast:noteStyle?contrast(noteStyle.color):null
      };
    })
  };
}"""

try:
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True,args=["--no-sandbox"])
        for width,height in [(1920,1080),(1366,768),(390,844)]:
            page=browser.new_page(viewport={"width":width,"height":height},device_scale_factor=1)
            page.goto(f"http://127.0.0.1:{PORT}/site/index.html",wait_until="domcontentloaded",timeout=45000)
            page.evaluate("() => document.fonts.ready")
            page.locator("#etnika-extra").scroll_into_view_if_needed()
            values=page.evaluate(JS)
            print(json.dumps({"viewport":f"{width}x{height}",**values},ensure_ascii=False),flush=True)
            prices=values["prices"]
            assert [x["text"] for x in prices]==["1600 ₽","1200 ₽","600–1000 ₽"]
            assert all(x["fullyInsideContainer"] and x["fullyInsideSection"] for x in prices), "Price box clipped"
            assert all(x["numberBoxHeight"]>x["glyphInkHeight"]+3 for x in prices), "Glyph bounds too tight"
            assert all(x["labelContrast"]>=7 and float(x["labelWeight"])>=300 for x in prices), "Service text too faint"
            assert [x["note"] for x in prices]==[None,"до двух за сессию","за одну вещь"]
            assert all(x["noteFontPx"]>=14 and x["noteContrast"]>=6 for x in prices if x["note"]), "Price notes too faint/small"
            assert all(all(v=="visible" for v in x["overflows"]) for x in prices), "A price wrapper clips overflowing glyphs"
            page.locator("#etnika-extra").screenshot(path=str(REPORTS/f"extra-details-{width}x{height}.png"),animations="disabled")
            page.close()
        browser.close()
finally:
    server.shutdown()
