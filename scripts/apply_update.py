#!/usr/bin/env python3
"""Patch the data blocks (MASKS, LOCKED, DEFAULT_COINS) of the Tomb of the Mask index.html.

  apply_update.py INDEX_HTML --show
        Print the current data compactly (name: level) so you never need to read the whole file.

  apply_update.py INDEX_HTML SPEC.json [--out PATH] [--dry-run] [--strict]
        Apply what was read from the video. SPEC.json:

        {
          "coins": 62648,                              # optional, updates DEFAULT_COINS
          "masks": {                                   # EVERY unlocked mask seen in the video
            "Travelboy": {"lvl": 15, "cost": 750},     # cost = coin price on the UPGRADE button
            "Piggy":     {"lvl": 34, "cards": [22, 35]},  # masks showing a CARDS bar instead of UPGRADE
            "Alien":     15                            # shorthand: just a level
          },
          "locked": ["Robot", "Zombie"],               # EVERY locked (padlock + '?') mask seen
          "new_masks": {                               # only if a name is in neither index.html nor
            "Foo": {"b": {"coins": 20}, "s": "No Snakes", "unlock": "EUR 4.99"}   # references/mask_bonuses.json
          }
        }

Rules it enforces (all learned the hard way):
  * levels are read from the video, so each one is cross-checked: coin masks must satisfy cost == 50 * lvl
  * levels never go down; a decrease is reported as a probable misread
  * a mask that was LOCKED and now has a level is moved to MASKS (newly unlocked), keeping its bonuses
  * bonuses for new masks come from index.html (LOCKED entry) > spec.new_masks > references/mask_bonuses.json
  * existing masks keep their bonuses (index.html beats the wiki)
  * masks in index.html that the video did not show are kept as-is and listed as a warning
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, '..', 'references', 'mask_bonuses.json')
STAT_ORDER = ['coins', 'score', 'bonus', 'freezes', 'magnets', 'addicts']
COST_PER_LEVEL = 50

MASK_RE = re.compile(r"^\s*\{ n:'(?P<n>[^']+)', l:(?P<l>\d+), b:\{(?P<b>[^}]*)\}, s:'(?P<s>[^']*)'(?:, cards:\[(?P<c1>\d+),(?P<c2>\d+)\])? \},?\s*$")
LOCK_RE = re.compile(r"^\s*\{ n:'(?P<n>[^']+)', how:'(?P<how>[^']*)', b:\{(?P<b>[^}]*)\}, s:'(?P<s>[^']*)' \},?\s*$")

def parse_b(txt):
    out = {}
    for part in txt.split(','):
        part = part.strip()
        if part:
            k, v = part.split(':')
            out[k.strip()] = float(v) if '.' in v else int(v)
    return out

def fmt_b(b):
    return '{' + ', '.join(f"{k}:{b[k]}" for k in STAT_ORDER if k in b) + '}'

def block_bounds(html, marker):
    start = html.index(marker)
    first = html.index('\n', start) + 1
    end = html.index('        ];', first)
    return first, end

def load_blocks(html):
    if 'const MASKS = [' not in html:
        sys.exit("No 'const MASKS = [' block: this is a legacy static-table index.html. Run scripts/migrate_legacy.py first.")
    f, e = block_bounds(html, 'const MASKS = [')
    masks = []
    for line in html[f:e].splitlines():
        if not line.strip():
            continue
        m = MASK_RE.match(line)
        if not m:
            sys.exit(f'Unparseable MASKS line: {line!r}')
        d = {'n': m['n'], 'l': int(m['l']), 'b': parse_b(m['b']), 's': m['s'], 'cards': None}
        if m['c1']:
            d['cards'] = [int(m['c1']), int(m['c2'])]
        masks.append(d)
    f2, e2 = block_bounds(html, 'const LOCKED = [')
    locked = []
    for line in html[f2:e2].splitlines():
        if not line.strip():
            continue
        m = LOCK_RE.match(line)
        if not m:
            sys.exit(f'Unparseable LOCKED line: {line!r}')
        locked.append({'n': m['n'], 'how': m['how'], 'b': parse_b(m['b']), 's': m['s']})
    return masks, locked

def render(html, masks, locked, coins):
    def mline(m):
        c = f", cards:[{m['cards'][0]},{m['cards'][1]}]" if m['cards'] else ''
        return f"            {{ n:'{m['n']}', l:{m['l']}, b:{fmt_b(m['b'])}, s:'{m['s']}'{c} }},"
    def lline(m):
        return f"            {{ n:'{m['n']}', how:'{m['how']}', b:{fmt_b(m['b'])}, s:'{m['s']}' }},"
    # replace LOCKED first (it is later in the file) so earlier offsets stay valid
    f2, e2 = block_bounds(html, 'const LOCKED = [')
    html = html[:f2] + '\n'.join(lline(m) for m in locked) + '\n' + html[e2:]
    f, e = block_bounds(html, 'const MASKS = [')
    html = html[:f] + '\n'.join(mline(m) for m in masks) + '\n' + html[e:]
    if coins is not None:
        html, n = re.subn(r'const DEFAULT_COINS = \d+;', f'const DEFAULT_COINS = {coins};', html)
        if n != 1:
            sys.exit('Could not find DEFAULT_COINS')
    return html

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('index_html')
    ap.add_argument('spec', nargs='?')
    ap.add_argument('--show', action='store_true')
    ap.add_argument('--out')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--strict', action='store_true', help='treat warnings as errors')
    a = ap.parse_args()

    html = open(a.index_html, encoding='utf-8').read()
    masks, locked = load_blocks(html)
    m_coins = re.search(r'const DEFAULT_COINS = (\d+);', html)

    if a.show or not a.spec:
        print(f"coins={m_coins.group(1) if m_coins else '?'}  unlocked={len(masks)}  locked={len(locked)}  total={len(masks) + len(locked)}")
        print('UNLOCKED:', ', '.join(f"{m['n']} {m['l']}{'*' if m['cards'] else ''}" for m in masks))
        print('  (* = upgrades with cards)')
        print('LOCKED:  ', ', '.join(m['n'] for m in locked))
        return

    spec = json.load(open(a.spec))
    ref = json.load(open(REF))['masks']
    by_name = {m['n']: m for m in masks}
    lock_by = {m['n']: m for m in locked}
    warnings, errors, need_bonuses = [], [], []
    changes, unlocked_now, new_locked = [], [], []

    def entry(v):
        if isinstance(v, int):
            return {'lvl': v}
        return v

    for name, v in spec.get('masks', {}).items():
        v = entry(v)
        lvl = int(v['lvl'])
        cost = v.get('cost')
        cards = v.get('cards')
        if cards is None and cost is not None and cost != COST_PER_LEVEL * lvl:
            warnings.append(f"{name}: read Lvl {lvl} but upgrade cost {cost} (expected {COST_PER_LEVEL * lvl}) - one of them is misread; zoom in on that card")
        if cards is not None and cards[1] != lvl + 1:
            warnings.append(f"{name}: cards {cards[0]}/{cards[1]} at Lvl {lvl} (expected needed={lvl + 1}) - check the level")
        if name in by_name:
            m = by_name[name]
            if lvl < m['l']:
                warnings.append(f"{name}: level went DOWN {m['l']} -> {lvl}; probably a misread")
            if lvl != m['l']:
                changes.append((name, m['l'], lvl))
            m['l'] = lvl
            m['cards'] = list(cards) if cards else None
        else:
            if name in lock_by:
                src = lock_by.pop(name)
                b, s = src['b'], src['s']
            elif name in spec.get('new_masks', {}):
                nm = spec['new_masks'][name]; b, s = nm['b'], nm.get('s', '')
            elif name in ref:
                b, s = dict(ref[name]['b']), ref[name]['s']
            else:
                need_bonuses.append(name); continue
            m = {'n': name, 'l': lvl, 'b': b, 's': s, 'cards': list(cards) if cards else None}
            masks.append(m); by_name[name] = m
            unlocked_now.append(m)

    for name in spec.get('locked', []):
        if name in by_name:
            errors.append(f"{name} is listed as locked but also has a level")
        elif name not in lock_by:
            if name in spec.get('new_masks', {}):
                nm = spec['new_masks'][name]; b, s, how = nm['b'], nm.get('s', ''), nm.get('unlock', 'Unknown')
            elif name in ref:
                b, s, how = dict(ref[name]['b']), ref[name]['s'], ref[name]['unlock']
            else:
                need_bonuses.append(name); continue
            lock_by[name] = {'n': name, 'how': how, 'b': b, 's': s}
            new_locked.append(name)

    seen = set(spec.get('masks', {})) | set(spec.get('locked', []))
    unseen_m = [m['n'] for m in masks if m['n'] not in seen]
    unseen_l = [n for n in lock_by if n not in seen]
    if unseen_m:
        warnings.append('In index.html but not in the video/spec (kept unchanged): ' + ', '.join(unseen_m))
    if unseen_l:
        warnings.append('Locked in index.html but not in the video/spec (kept): ' + ', '.join(unseen_l))
    if need_bonuses:
        errors.append('No bonus data for: ' + ', '.join(need_bonuses) +
                      ' -> web_search "Tomb of the Mask wiki <name> mask bonus" (or parse the wiki HTML with scripts/parse_wiki_html.py) '
                      'and add them under "new_masks" in the spec.')

    locked_out = [lock_by[n] for n in lock_by]
    print(f"Level changes ({len(changes)}):", ', '.join(f"{n} {o}->{l}" for n, o, l in changes) or 'none')
    print(f"Newly unlocked ({len(unlocked_now)}):")
    for m in unlocked_now:
        print(f"   {m['n']} Lvl {m['l']}  base {fmt_b(m['b'])} {m['s']}{'  [cards]' if m['cards'] else ''}")
    if new_locked:
        print('Newly discovered locked masks:', ', '.join(new_locked))
    print(f"Totals: unlocked {len(masks)} / {len(masks) + len(locked_out)}  (locked: {', '.join(m['n'] for m in locked_out) or 'none'})")
    if spec.get('coins') is not None:
        print('Coins ->', spec['coins'])
    for w in warnings:
        print('WARNING:', w)
    for e in errors:
        print('ERROR:', e)
    if errors or (a.strict and warnings):
        sys.exit(1)
    if a.dry_run:
        print('(dry run, nothing written)'); return
    out = render(html, masks, locked_out, spec.get('coins'))
    path = a.out or a.index_html
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(out)
    print('Wrote', path)

if __name__ == '__main__':
    main()
