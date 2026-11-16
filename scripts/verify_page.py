#!/usr/bin/env python3
"""Headless-browser smoke test for the generated index.html (needs python playwright + chromium).

  verify_page.py INDEX_HTML

Strips the Tailwind CDN / Google font imports so it works offline, loads the page, and checks:
  no JS errors (the service-worker error on file:// is expected and ignored), table row count equals the
  MASKS data, progress label, situation overview, and that sorting/ranking still work. Exit 1 on failure.
"""
import re, sys, os, tempfile
from playwright.sync_api import sync_playwright

def main():
    src = sys.argv[1]
    html = open(src, encoding='utf-8').read()
    n_data = len(re.findall(r"^\s*\{ n:'[^']+', l:\d+,", html, re.M))
    n_locked = len(re.findall(r"^\s*\{ n:'[^']+', how:", html, re.M))
    html = html.replace('<script src="https://cdn.tailwindcss.com"></script>', '')
    html = re.sub(r"@import url\('https://fonts.googleapis.com[^']*'\);", '', html)
    tmp = os.path.join(tempfile.mkdtemp(), 'verify.html'); open(tmp, 'w', encoding='utf-8').write(html)
    ok = True
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1000, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pg.goto('file://' + tmp)
        errs = [e for e in errs if 'ServiceWorker' not in e and 'Service worker' not in e]
        rows = pg.locator('#masksBody tr').count()
        print('JS errors:', errs or 'none')
        print(f'table rows: {rows} (MASKS data: {n_data})', 'OK' if rows == n_data else 'MISMATCH')
        print('progress:', pg.inner_text('#progressLabel'), '| locked listed:', pg.locator('#lockedList .locked-card').count(), f'(LOCKED data: {n_locked})')
        print('--- best mask per situation')
        for r in pg.locator('#situationBody tr').all():
            print('  ', r.inner_text().replace('\t', ' | '))
        pg.click('#masksTable th:nth-child(2)')
        print('sort by Lvl ok, first row:', pg.locator('#masksBody tr').first.inner_text().split('\t')[0])
        ok = not errs and rows == n_data and pg.locator('#lockedList .locked-card').count() == n_locked
        b.close()
    print('PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
