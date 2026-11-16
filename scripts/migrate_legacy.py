#!/usr/bin/env python3
"""Convert an OLD static-table index.html (hand-written <tr> rows, no 'const MASKS' block) into the
current data-driven page, using assets/index_template.html as the shell.

  migrate_legacy.py OLD_INDEX.html --out NEW_INDEX.html

Each row's displayed % is converted back to a Lvl-1 base (shown value - 0.1 * (lvl - 1)). The result has
an empty LOCKED list and no card masks: follow with apply_update.py and a spec to set those.
"""
import argparse, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply_update as au

COLS = ['coins', 'score', 'bonus', 'freezes', 'magnets', 'addicts']

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('old'); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    old = open(a.old, encoding='utf-8').read()
    tb = re.search(r'<tbody.*?</tbody>', old, re.S)
    if not tb: sys.exit('No <tbody> found in the old file')
    masks = []
    for r in re.findall(r'<tr.*?</tr>', tb.group(0), re.S):
        tds = [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)]
        if len(tds) < 10: continue
        lvl = int(tds[1]); b = {}
        for k, v in zip(COLS, tds[2:8]):
            if v != '-':
                # bases are always multiples of 5 in this game, so round away the 0.1%/level part
                b[k] = int(round((float(v.rstrip('%')) - 0.1 * (lvl - 1)) / 5) * 5)
        if tds[0] in ('Travelboy', 'Nikandr') and not b:
            b = {'coins': 0}   # confirmed in game: coin bonus starts at 0% and grows +0.1%/level
        s = tds[8] if tds[8] not in ('-', 'None') else ''
        masks.append({'n': tds[0], 'l': lvl, 'b': b, 's': s, 'cards': None})
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'index_template.html'), encoding='utf-8').read()
    au.load_blocks(tpl)  # sanity: template has the blocks
    out = au.render(tpl, masks, [], None)
    open(a.out, 'w', encoding='utf-8').write(out)
    print(f'Migrated {len(masks)} masks -> {a.out}. Locked list is empty; run apply_update.py with a spec next.')

if __name__ == '__main__':
    main()
