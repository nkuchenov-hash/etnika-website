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
        assert root.locator('.p27-photo').evaluate_all("""cards=>cards.every(c=>{const a=c.querySelector('.p27-color'),b=c.querySelector('.p27-mono');return a.src===b.src&&getComputedStyle(b).filter.includes('etnika-process-monochrome')})"""),'Mono must use same source with full-frame filter'
        assert root.locator('.p27-sub').count()==0
        descriptions=root.locator('.p27-desc').all_text_contents()
        assert 'со\u00a0студией' in descriptions[0] and 'и\u00a0знакомит' in descriptions[0],descriptions
        assert 'зеркалом\u00a0—' in descriptions[1] and 'на\u00a0экране' in descriptions[1],descriptions
        assert 'чёрно\u2011белые' in descriptions[2],descriptions
        assert '24\u00a0часов' in descriptions[4],descriptions
        facts=root.evaluate("""r=>{let p=[...r.querySelectorAll('.p27-photo')];let d=[...r.querySelectorAll('.p27-desc')];return {photos:p.map(e=>({x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height})),fonts:d.map(e=>({size:parseFloat(getComputedStyle(e).fontSize),weight:getComputedStyle(e).fontWeight})),overflow:document.documentElement.scrollWidth>innerWidth+3}}""")
        assert not facts['overflow'],facts
        assert all(x['size']==(18 if w>=761 else 16) and x['weight']=='100' for x in facts['fonts']),facts
        page.wait_for_timeout(200)
        layout=root.evaluate("""r=>{const box=e=>e.getBoundingClientRect();const heading=r.querySelector('.p27-heading');const grid=r.querySelector('.p27-grid');const photos=[...r.querySelectorAll('.p27-photo')];const copies=[...r.querySelectorAll('.p27-copy')];return {headingBottom:box(heading).bottom,guideLeft:Math.abs(box(heading).left-box(grid).left),guideRight:Math.abs(box(heading).right-box(grid).right),firstPhoto:Math.min(...photos.map(e=>box(e).top)),fonts:[heading.querySelector('h2'),heading.querySelector('h2 span'),...r.querySelectorAll('.p27-num,.p27-title')].map(e=>getComputedStyle(e).fontFamily),aligned:photos.every((e,i)=>Math.abs(box(e).left-box(copies[i]).left)<2&&Math.abs(box(e).width-box(copies[i]).width)<2&&box(e).bottom<=box(copies[i]).top+1)}}""")
        spacing=root.evaluate("""r=>{const box=e=>e.getBoundingClientRect();const kicker=r.querySelector('.p27-kicker'), heading=r.querySelector('.p27-heading'), shell=r.querySelector('.p27-shell');const probe=document.createElement('div');probe.style.cssText='position:absolute;visibility:hidden;height:var(--etnika-editorial-heading-gap);padding-top:var(--etnika-section-outer);padding-bottom:var(--etnika-section-outer);box-sizing:content-box';r.append(probe);const p=getComputedStyle(probe),style=getComputedStyle(r);const out={gap:box(heading).top-box(kicker).bottom,expectedGap:parseFloat(p.height),top:box(shell).top-box(r).top,bottom:box(r).bottom-box(shell).bottom,expectedOuter:parseFloat(p.paddingTop),paddingTop:parseFloat(style.paddingTop),paddingBottom:parseFloat(style.paddingBottom)};probe.remove();return out}""")
        print('Spacing',w,h,spacing,flush=True)
        assert abs(spacing['gap']-spacing['expectedGap'])<2,spacing
        assert all(abs(spacing[key]-spacing['expectedOuter'])<2 for key in ['paddingTop','paddingBottom','top','bottom']),spacing
        assert layout['headingBottom']<=layout['firstPhoto']+1,layout
        assert all('Forum' in f for f in layout['fonts']),layout
        if w>1100:
            assert layout['aligned'],layout
            caption_gaps=root.evaluate("""r=>{const photos=[...r.querySelectorAll('.p27-photo')];const titles=[...r.querySelectorAll('.p27-title')];return photos.map((photo,i)=>titles[i].getBoundingClientRect().top-photo.getBoundingClientRect().bottom)}""")
            assert all(g>=23 for g in caption_gaps),caption_gaps
            assert layout['guideLeft']<2 and layout['guideRight']<2,layout
            assert len({round(x['y']) for x in facts['photos']})==1,facts
            geometry=root.evaluate("""r=>{let b=r.getBoundingClientRect(),p=r.querySelector('.p27-photo').getBoundingClientRect(),n=document.getElementById('etnika-site-header').getBoundingClientRect(), copies=[...r.querySelectorAll('.p27-copy')].map(e=>e.getBoundingClientRect());return {section:b.height,available:innerHeight-n.height,photo:p.height,ratio:p.width/p.height,copyBottom:Math.max(...copies.map(x=>x.bottom))-b.top,heading:r.querySelector('.p27-heading').getBoundingClientRect().height}}""")
            print('Geometry',w,h,geometry,flush=True)
            assert abs(geometry['ratio']-430/724)<.015,geometry
            assert geometry['copyBottom']<=geometry['section']+1,geometry
            assert geometry['photo']>=min(280,h*.35),geometry
        page.mouse.move(0,0)
        page.wait_for_timeout(450)
        assert root.locator('.p27-mono').evaluate_all("a=>a.every(e=>getComputedStyle(e).opacity==='1')")
        root.screenshot(path=str(OUT/f'etnika-process-final-{w}.png'))
        photo=root.locator('.p27-photo').nth(2)
        descriptions=root.locator('.p27-desc')
        expected='0' if w>1100 else '1'
        assert descriptions.evaluate_all("a=>a.map(e=>getComputedStyle(e).opacity)")==[expected]*5
        height_before=root.evaluate("r=>r.getBoundingClientRect().height")
        photo.hover();page.wait_for_timeout(480)
        if w>1100:
            assert descriptions.evaluate_all("a=>a.map(e=>getComputedStyle(e).opacity)")==['0','0','1','0','0']
            assert photo.locator('img').evaluate_all("a=>a.every(e=>new DOMMatrix(getComputedStyle(e).transform).a>1.035)")
            assert abs(root.evaluate("r=>r.getBoundingClientRect().height")-height_before)<1
        else:
            assert descriptions.evaluate_all("a=>a.every(e=>getComputedStyle(e).opacity==='1')")
        assert photo.locator('.p27-mono').evaluate("e=>getComputedStyle(e).opacity")=='0'
        root.screenshot(path=str(OUT/f'etnika-process-final-hover-{w}.png'))
        page.mouse.move(0,0);page.wait_for_timeout(480)
        assert photo.locator('.p27-mono').evaluate("e=>getComputedStyle(e).opacity")=='1'
        if w>1100:
            assert descriptions.evaluate_all("a=>a.every(e=>getComputedStyle(e).opacity==='0')")
            assert photo.locator('img').evaluate_all("a=>a.every(e=>Math.abs(new DOMMatrix(getComputedStyle(e).transform).a-1)<.001)")
        photo.click();page.mouse.move(0,0);page.wait_for_timeout(480)
        assert photo.get_attribute('aria-pressed')=='true'
        root.locator('.p27-title').first.click()
        root.locator('.epi-modal.open').wait_for(state='visible')
        page.keyboard.press('Escape')
        assert root.locator('.epi-modal.open').count()==0
        print(f'PASS {w}x{h}: final photos, copy, hover, tap, details',flush=True)
        page.close()
    browser.close()
