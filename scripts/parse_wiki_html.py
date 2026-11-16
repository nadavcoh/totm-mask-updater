#!/usr/bin/env python3
"""Parse a saved Tomb of the Mask Wiki 'Masks' page (Fandom HTML) into the same shape as
references/mask_bonuses.json ('masks' section). Use when web search can't find a new mask's bonuses
and the user uploaded the wiki HTML (fetching the fandom URL directly returns HTTP 402).

  parse_wiki_html.py WIKI.html [Name ...]     # prints JSON for the named masks (or all if none given)
Paste the printed entries into SPEC.json under "new_masks" (only needs b / s / unlock).
"""
import json, re, sys

WC = ['coins', 'magnets', 'addicts', 'freezes', 'bonus', 'score']   # wiki column order

def unlock(raw):
    r = raw.strip()
    if not r: return 'Unknown'
    if r == 'WOF': return 'Wheel of Fortune'
    if r.lower().startswith('sub'): return 'Premium subscription'
    m = re.match(r'coins (\d+)', r)
    if m: return f'{m.group(1)} coins'
    m = re.match(r'video ads? (\d+)', r)
    if m: return f'{m.group(1)} video ads'
    return r

def main():
    html = open(sys.argv[1], encoding='utf-8', errors='ignore').read()
    want = set(sys.argv[2:])
    table = [t for t in re.findall(r'<table.*?</table>', html, flags=re.S) if 'More Coins' in t][0]
    out = {}
    for r in re.findall(r'<tr.*?</tr>', table, flags=re.S)[1:]:
        c = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', x)).strip() for x in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, flags=re.S)]
        if len(c) < 11 or (want and c[0] not in want):
            continue
        b = {k: int(float(c[3 + i])) for i, k in enumerate(WC) if c[3 + i] and not c[3 + i].startswith('-')}
        s = 'No Snakes' if c[9] == 'Y' else ('No Monkeys' if c[10] == 'Y' else '')
        out[c[0]] = {'b': b, 's': s, 'unlock': unlock(c[1])}
    print(json.dumps(out, indent=1))

if __name__ == '__main__':
    main()
