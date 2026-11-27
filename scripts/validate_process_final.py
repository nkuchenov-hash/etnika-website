from pathlib import Path
import sys,time,os,re
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports';OUT.mkdir(exist_ok=True)
LIVE='--live' in sys.argv
BUILD=re.search(r'<meta name="etnika-build" content="([^"]+)"',(ROOT/'site/index.html').read_text()).group(1)
URL='https://nkuchenov-hash.github.io/etnika-website/site/' if LIVE else (ROOT/'site/index.html').as_uri()
with sync_playwright() as p:
    browser=p.chromium.launch()
    for w,h in [(1920,1080),(2048,736),(1662,896),(1440,900),(1366,768),(2560,1080),(1024,768),(390,844)]:
        page=browser.new_page(viewport={'width':w,'height':h})
        for i in range(12 if LIVE else 1):
            page.goto(URL+(f'?build={BUILD}&run={os.getenv("GITHUB_RUN_ID","local")}&attempt={i}' if LIVE else ''),wait_until='load')
            if page.locator('meta[name="etnika-build"]').get_attribute('content')==BUILD:break
            if not LIVE or i==11:raise AssertionError('Wrong deployed build')
            time.sleep(3)
        root=page.locator('#etnika-process-interactive')
        root.scroll_into_view_if_needed()
        page.evaluate('() => document.fonts.ready')
        root.evaluate("""async r=>{let imgs=[...r.querySelectorAll('.p27-photo img')];imgs.forEach(i=>i.loading='eager');await Promise.all(imgs.map(i=>i.decode()))}""")
        assert root.locator('.p27-title').all_text_contents()==['Знакомство','Первый кадр','Выбор','Съёмка','Результат']
        assert root.locator('.p27-photo img').count()==10
        facts=root.evaluate("""r=>{let p=[...r.querySelectorAll('.p27-photo')];let d=[...r.querySelectorAll('.p27-desc')];return {photos:p.map(e=>({x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height})),fonts:d.map(e=>({size:parseFloat(getComputedStyle(e).fontSize),weight:getComputedStyle(e).fontWeight})),overflow:document.documentElement.scrollWidth>innerWidth+3}}""")
        assert not facts['overflow'],facts
        assert all(x['size']==(18 if w>=761 else 16) and x['weight']=='100' for x in facts['fonts']),facts
        page.wait_for_timeout(200)
        if w>1100:
            assert len({round(x['y']) for x in facts['photos']})==1,facts
            geometry=root.evaluate("""r=>{let b=r.getBoundingClientRect(),p=r.querySelector('.p27-photo').getBoundingClientRect(),n=document.getElementById('etnika-site-header').getBoundingClientRect(), copies=[...r.querySelectorAll('.p27-copy')].map(e=>e.getBoundingClientRect());return {section:b.height,available:innerHeight-n.height,photo:p.height,ratio:p.width/p.height,copyBottom:Math.max(...copies.map(x=>x.bottom))-b.top,heading:r.querySelector('.p27-heading').getBoundingClientRect().height}}""")
            print('Geometry',w,h,geometry,flush=True)
            assert abs(geometry['ratio']-430/724)<.015,geometry
            assert geometry['copyBottom']<=geometry['section']+1,geometry
            assert geometry['photo']<=h*.57,geometry
            if h>=850:assert geometry['section']<=geometry['available']+8,geometry
        page.mouse.move(0,0)
        page.wait_for_timeout(450)
        assert root.locator('.p27-mono').evaluate_all("a=>a.every(e=>getComputedStyle(e).opacity==='1')")
        root.screenshot(path=str(OUT/f'etnika-process-final-{w}.png'))
        photo=root.locator('.p27-photo').nth(2)
        photo.hover();page.wait_for_timeout(480)
        assert photo.locator('.p27-mono').evaluate("e=>getComputedStyle(e).opacity")=='0'
        root.screenshot(path=str(OUT/f'etnika-process-final-hover-{w}.png'))
        page.mouse.move(0,0);page.wait_for_timeout(480)
        assert photo.locator('.p27-mono').evaluate("e=>getComputedStyle(e).opacity")=='1'
        photo.click();page.mouse.move(0,0);page.wait_for_timeout(480)
        assert photo.get_attribute('aria-pressed')=='true'
        root.locator('.p27-title').first.click()
        root.locator('.epi-modal.open').wait_for(state='visible')
        page.keyboard.press('Escape')
        assert root.locator('.epi-modal.open').count()==0
        print(f'PASS {w}x{h}: final photos, copy, hover, tap, details',flush=True)
        page.close()
    browser.close()
