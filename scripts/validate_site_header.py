#!/usr/bin/env python3
"""ETNIKA header and shared editorial overline regression checks."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
FILES=[ROOT/"site/index.html"]
OVERLINE_CSS=ROOT/"site/assets/etnika-editorial-overline.css"
EDITORIAL_SECTIONS=(
    ("etnika-stories","stories-top"),
    ("etnika-space-photo","spf-top"),
    ("etnika-studio-features","b05-top"),
    ("etnika-faq","faq-top"),
    ("etnika-faq-tariffs","faq-top"),
    ("etnika-reviews","etnika-reviews-overline"),
)


def static():
    for path in FILES:
        s=path.read_text(encoding="utf-8")
        assert s.count('id="etnika-site-header"')==1,(path,"missing or duplicate site navigation")
        assert 'id="etnika-header-interaction-20261105"' in s
        assert 'id="etnika-brand-flight"' in s
        assert 'class="esh__descriptor">Студия автопортрета</span>' in s
        assert 'href="#etnika-prices-clear"' in s
        assert 'href="#etnika-gift"' in s
        assert 'href="#etnika-contacts-source"' in s
        assert 'href="https://etnika-studio.ru/otkryt-studiyu-avtoportreta"' in s
        assert 'href="https://n1268189.yclients.com/"' in s
        assert '--etnika-overline-size:clamp(9px,.62vw,11px)' in s
        assert '--etnika-overline-size:8px' in s
        assert '--etnika-menu-item-gap:clamp(26px,2.2vw,38px)' in s, (path,"roomy desktop menu token missing")
        assert '--etnika-menu-item-gap:clamp(18px,1.65vw,24px)' in s, (path,"responsive compact-desktop menu token missing")
        assert 'gap:var(--etnika-menu-item-gap);' in s, (path,"desktop nav does not use shared gap token")
        assert s.count('font-size:var(--etnika-overline-size);')==6
        assert 'assets/etnika-editorial-overline.css?v=20261106' in s, (path,"shared editorial stylesheet missing")
        for section_id, top_class in EDITORIAL_SECTIONS:
            import re
            section=re.search(r'<section id="'+section_id+r'"[\s\S]*?</section>',s)
            assert section and ('class="'+top_class+' etnika-editorial-top"') in section.group(0), (path, section_id,"overline did not use shared component")
        reviews=s.split('<style id="etnika-reviews-section-style">',1)[1].split('</style>',1)[0]
        assert 'font-size:16px' not in reviews, (path,"reviews must not override the editorial text scale")
        assert 'grid-template-columns' not in reviews, (path,"reviews must not redefine the shared overline grid")

        assert 'font-size:var(--etnika-overline-size)!important' in s
        assert 'font-size:var(--etnika-text-size)!important;font-weight:300!important;letter-spacing:.055em' not in s, "oversized studio kicker returned"
    css=OVERLINE_CSS.read_text(encoding="utf-8")
    assert 'font-size:var(--etnika-overline-size)!important' in css, "canonical editorial type token missing"
    assert 'grid-template-columns:auto minmax(80px,1fr) auto 1px auto minmax(80px,1fr)!important' in css, "canonical overline grid missing"
    assert '#etnika-reviews' in css and '#etnika-stories' in css, "reviews and sections must share editorial CSS"
    # Only one canonical site file exists; verify its header components.
    import re
    docs=[p.read_text(encoding="utf-8") for p in FILES]
    for pattern in (
        r'<header id="etnika-site-header"(?s:.*?)</header>',
        r'<style id="etnika-header-design-system-20261105">(?s:.*?)</style>',
        r'<script id="etnika-header-interaction-20261105">(?s:.*?)</script>'
    ):
        fragments=[re.search(pattern,html) for html in docs]
        assert all(fragments), "Missing common site header"

    print("PASS: canonical page contains navigation, logo transition, and shared kicker type")

def render():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        for path in FILES:
            for width,height in [(1920,1080),(1662,896),(1536,800),(1440,900),(1366,768),(1340,800),(1280,800),(1241,800),(1161,800),(390,844),(375,667)]:
                page=browser.new_page(viewport={"width":width,"height":height})
                page.goto(path.as_uri(),wait_until="domcontentloaded")
                header=page.locator("#etnika-site-header")
                hero=page.locator("#etnika-hero")
                assert header.count()==1
                page.evaluate("window.scrollTo(0,0)")
                page.wait_for_timeout(80)
                assert header.get_attribute("data-hero")=="false",(path,width,"process section must open before HERO")
                assert page.locator(".esh__descriptor").is_visible()
                assert page.locator(".esh__logo").evaluate("(el)=>getComputedStyle(el).opacity")=="1"
                before=page.evaluate("""() => ({
                    space:parseFloat(getComputedStyle(document.querySelector('#etnika-space-photo .spf-top')).fontSize),
                    other:parseFloat(getComputedStyle(document.querySelector('#etnika-stories .stories-top')).fontSize),
                    heading:getComputedStyle(document.querySelector('#etnika-space-photo .spf-title')).fontFamily
                })""")
                assert abs(before["space"]-before["other"])<0.25,(path,width,"mismatched editorial overlines",before)
                # All editorial sections, including the independently loaded review widget,
                # must use the same overline text metrics and responsive grid.
                tops=page.evaluate("""() => {
                    const ids=['etnika-stories','etnika-space-photo','etnika-studio-features',
                      'etnika-faq','etnika-faq-tariffs','etnika-reviews'];
                    return ids.map(id=>{
                      const el=document.querySelector('#'+id+' .etnika-editorial-top');
                      if(!el)return null;
                      const st=getComputedStyle(el);
                      return {id,fontSize:st.fontSize,fontFamily:st.fontFamily,
                              fontWeight:st.fontWeight,gap:st.columnGap,
                              grid:st.gridTemplateColumns,
                              lastVisible:getComputedStyle(el.children[4]).display!=='none'};
                    });
                }""")
                assert all(t is not None for t in tops),(path,width,"missing shared editorial component",tops)
                expected=tops[0]
                for t in tops[1:]:
                    for k in ("fontSize","fontFamily","fontWeight","gap"):
                        assert t[k]==expected[k],(path,width,t["id"],k,t[k],expected[k])
                    assert t["lastVisible"]==expected["lastVisible"],(path,width,"editorial breakpoint mismatch",t)

                assert "Forum" in before["heading"]
                if width<=1160:
                    toggle=page.locator(".esh__toggle")
                    assert toggle.is_visible()
                    toggle.click()
                    assert toggle.get_attribute("aria-expanded")=="true"
                    assert page.locator("#etnika-mobile-nav").is_visible()
                    page.keyboard.press("Escape")
                    assert toggle.get_attribute("aria-expanded")=="false"
                else:
                    assert page.locator(".esh__nav").is_visible()
                    assert page.locator(".esh__booking").is_visible()
                    assert page.locator(".esh__nav").evaluate("(el)=>el.scrollWidth<=el.clientWidth+2"),(path,width,"desktop nav overflows")
                    nav_metrics=page.evaluate("""() => {
                       const head=document.querySelector('#etnika-site-header');
                       const nav=head.querySelector('.esh__nav');
                       const items=[...nav.querySelectorAll('a')];
                       const visible=[...head.querySelector('.esh__inner').children]
                         .filter(el=>getComputedStyle(el).display!=='none');
                       const bounds=el=>el.getBoundingClientRect();
                       return {
                         gap:parseFloat(getComputedStyle(nav).columnGap),
                         linkGaps:items.slice(1).map((el,i)=>bounds(el).left-bounds(items[i]).right),
                         siblingGaps:visible.slice(1).map((el,i)=>bounds(el).left-bounds(visible[i]).right),
                         rightEdge:bounds(visible[visible.length-1]).right,
                         viewport:innerWidth
                       };
                    }""")
                    expected_gap=29 if width>1340 else 18
                    assert nav_metrics['gap']>=expected_gap-0.5,(path,width,"nav items too tightly spaced",nav_metrics)
                    assert all(g>=expected_gap-1 for g in nav_metrics['linkGaps']),(path,width,"nav link separation too small",nav_metrics)
                    assert all(g>=-1 for g in nav_metrics['siblingGaps']),(path,width,"header group overlap",nav_metrics)
                    assert nav_metrics['rightEdge']<=width-15,(path,width,"header overflows viewport",nav_metrics)
                page.evaluate("window.scrollTo({top:document.getElementById('etnika-hero').getBoundingClientRect().top+window.scrollY+document.getElementById('etnika-hero').offsetHeight+100,behavior:'instant'})")
                page.wait_for_timeout(400)
                assert header.get_attribute("data-hero")=="false",(path,width,"header did not acquire logo")
                assert page.locator(".esh__logo").evaluate("(el)=>getComputedStyle(el).opacity")=="1"
                assert page.locator("#etnika-brand-flight").evaluate("(el)=>getComputedStyle(el).display")=="none"
                page.close()
                print(f"PASS: {path.name} {width}x{height}: nav, logo switch and matching editorial type")
        browser.close()

if __name__=="__main__":
    static()
    if "--render" in sys.argv:
        render()
