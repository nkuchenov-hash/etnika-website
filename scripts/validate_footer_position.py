#!/usr/bin/env python3
"""Regression: the ETNIKA footer must render after contacts, never before the site."""
from pathlib import Path
from playwright.sync_api import sync_playwright

SITE=Path(__file__).resolve().parents[1]/"site/index.html"
with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True)
    for width,height in [(1440,900),(390,844),(375,667)]:
        page=browser.new_page(viewport={"width":width,"height":height})
        page.goto(SITE.as_uri(),wait_until="domcontentloaded")
        page.wait_for_function("""() => {
            const flow=document.getElementById('etnika-review-flow');
            const footer=document.getElementById('etnika-site-footer');
            return flow && footer && flow.nextElementSibling===footer;
        }""",timeout=10000)
        data=page.evaluate("""() => {
            const flow=document.getElementById('etnika-review-flow');
            const footer=document.getElementById('etnika-site-footer');
            const contacts=document.getElementById('etnika-contacts-source');
            const c=contacts.getBoundingClientRect(),f=footer.getBoundingClientRect();
            return {
                footerAfterMain: flow.nextElementSibling===footer,
                footerInBody: footer.parentElement===document.body,
                contactLast: flow.lastElementChild===contacts,
                gap: f.top-c.bottom,
                footerHeight: f.height,
                footerDisplay:getComputedStyle(footer).display,
                footerPosition:getComputedStyle(footer).position,
                links:footer.querySelectorAll('a[href]').length,
                legal:footer.textContent.includes('Политика конфиденциальности') &&
                      footer.textContent.includes('Договор-оферта'),
                logo:footer.textContent.includes('ЭТНИКА')
            };
        }""")
        assert data["footerAfterMain"] and data["footerInBody"] and data["contactLast"],(width,data)
        assert data["gap"]>=-2,(width,"footer overlaps or precedes contacts",data)
        assert data["footerHeight"]>150 and data["footerDisplay"]!="none",(width,data)
        assert data["footerPosition"] in ("static","relative"),(width,data)
        assert data["legal"] and data["logo"] and data["links"]>=10,(width,data)
        print("PASS footer after contacts",width,"x",height,data)
        page.close()
    browser.close()
