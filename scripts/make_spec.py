#!/usr/bin/env python3
"""Turn the compact notes you take while reading the video into the JSON spec for apply_update.py.

  make_spec.py NOTES.txt [--out /tmp/spec.json]

NOTES.txt, one mask per line, exactly as read from the cards (this is ~10x shorter than writing JSON):
    coins 44460
    Travelboy 15 750        <- name, LVL, coin price on the UPGRADE button
    Mad Mask 38 1900        <- names with spaces are fine
    Leopard 41 30/42        <- card masks: name, LVL, a/b from the CARDS bar
    locked Robot, Zombie    <- only if padlock '?' cards were seen; omit or write "locked" alone when none
    # comments and blank lines are ignored
The cost column is NOT computed here on purpose: apply_update.py checks cost == 50 x lvl, which is the
checksum that catches misread digits, so always type the price you actually saw.
"""
import json, re, sys, argparse

ap = argparse.ArgumentParser()
ap.add_argument('notes'); ap.add_argument('--out', default='/tmp/spec.json')
a = ap.parse_args()

spec = {'coins': None, 'masks': {}, 'locked': []}
row = re.compile(r'^(?P<n>.+?)\s+(?P<l>\d+)\s+(?:(?P<c>\d+)|(?P<a>\d+)\s*/\s*(?P<b>\d+))\s*$')
for ln, raw in enumerate(open(a.notes, encoding='utf-8'), 1):
    line = raw.split('#', 1)[0].strip()
    if not line:
        continue
    low = line.lower()
    if low.startswith('coins'):
        spec['coins'] = int(re.sub(r'[^\d]', '', line))
    elif low.startswith('locked'):
        spec['locked'] = [x.strip() for x in re.split(r'[,;]', line[6:].lstrip(' :')) if x.strip()]
    else:
        m = row.match(line)
        if not m:
            sys.exit(f'line {ln}: cannot parse {raw!r}  (want "Name LVL COST" or "Name LVL a/b")')
        n, lvl = m['n'], int(m['l'])
        if n in spec['masks']:
            sys.exit(f'line {ln}: {n} listed twice')
        spec['masks'][n] = {'lvl': lvl, 'cost': int(m['c'])} if m['c'] else {'lvl': lvl, 'cards': [int(m['a']), int(m['b'])]}
if spec['coins'] is None:
    del spec['coins']
json.dump(spec, open(a.out, 'w'), indent=1)
print(f"{len(spec['masks'])} masks, {len(spec['locked'])} locked, coins={spec.get('coins')} -> {a.out}")
