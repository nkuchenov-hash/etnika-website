#!/usr/bin/env python3
"""Regression check: desktop ETNIKA navigation is legible and visibly reacts to hover."""
from pathlib import Path
from playwright.sync_api import sync_playwright

SITE=Path(__file__).resolve().parents[1]/'site/index.html'
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1440,'height':900},reduced_motion='reduce')
    page.goto(SITE.as_uri(),wait_until='domcontentloaded')
    anchor=page.locator('#etnika-site-header .esh__nav a').first
    anchor.wait_for(state='visible',timeout=10000)
    header=page.locator('#etnika-site-header')
    for tone,hero in [('dark','true'),('light','false')]:
        header.evaluate("(el,args)=>{el.dataset.tone=args[0];el.dataset.hero=args[1];el.classList.remove('is-open')}",[tone,hero])
        page.mouse.move(0,400)
        before=anchor.evaluate("""el=>{
            let s=getComputedStyle(el);
            return {color:s.color,weight:parseFloat(s.fontWeight),
                    transform:getComputedStyle(el,'::after').transform};
        }""")
        assert before['weight']>=300,(tone,'font too thin',before)
        anchor.hover()
        after=anchor.evaluate("""el=>{
            let s=getComputedStyle(el),a=getComputedStyle(el,'::after');
            return {color:s.color,transform:a.transform,height:parseFloat(a.height),
                    accent:a.backgroundColor};
        }""")
        assert after['transform'] != before['transform'],(tone,'hover underline is invisible',before,after)
        assert after['height']>=2,(tone,'underline too thin',after)
        assert before['color']!=after['color'],(tone,'hover text color unchanged',before,after)
        print('PASS',tone,{'before':before,'hover':after},flush=True)
    page.close()
    mobile=browser.new_page(viewport={'width':390,'height':844},reduced_motion='reduce')
    mobile.goto(SITE.as_uri(),wait_until='domcontentloaded')
    mobile.locator('#etnika-site-header .esh__toggle').click()
    link=mobile.locator('#etnika-site-header .esh__mobile > a:not(.esh__mobile-book)').first
    link.wait_for(state='visible',timeout=10000)
    before=link.evaluate("el=>({weight:parseFloat(getComputedStyle(el).fontWeight),color:getComputedStyle(el).color})")
    link.hover()
    after=link.evaluate("el=>({background:getComputedStyle(el).backgroundColor,shadow:getComputedStyle(el).boxShadow})")
    assert before['weight']>=300 and after['shadow']!='none',(before,after)
    print('PASS mobile',{'before':before,'hover':after},flush=True)
    browser.close()
