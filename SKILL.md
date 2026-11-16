---
name: totm-mask-updater
description: Update the user's Tomb of the Mask mask-tracker web page (index.html) from a new screen recording of the in-game Masks screen. Reads mask levels, newly unlocked masks, locked masks and the coin balance from the video, looks up bonuses for new masks, patches the page data, verifies it and delivers a tar.gz. Use this whenever the user uploads a Tomb of the Mask video or screenshots together with index.html, or says things like "update my masks", "I unlocked new masks", "update levels from this video", "refresh the mask table", even if they do not name the skill.
---

# Tomb of the Mask mask updater

The page keeps all mask data in two JS blocks (`MASKS`, `LOCKED`) and `DEFAULT_COINS`; everything else (table, progress bar, locked list, "who to upgrade" advisor, Oracle chatbot prompt) is generated from them. So an update is: read the video -> write a small JSON spec -> run `apply_update.py`. The scripts do the heavy lifting; your job is reading the cards accurately.

Scripts are in `scripts/`, run with `python3`. Do not read the whole index.html (it is ~800 lines); use `--show`.

## Workflow

1. **Locate inputs** in `/mnt/user-data/uploads`: the video (.mp4/.mov), `index.html`, optionally screenshots or the wiki HTML. Copy index.html to a work dir (`/home/claude/work/index.html`).
   - If `grep -c "const MASKS = \[" index.html` is 0, it is an older static-table version: run `scripts/migrate_legacy.py index.html --out work/index.html` first (it rebuilds the page from `assets/index_template.html`).

2. **See the current data**: `python3 scripts/apply_update.py work/index.html --show` (one compact line per mask, with levels).

3. **Extract the video**: `python3 scripts/extract_frames.py VIDEO --outdir /tmp/totm`
   It prints the sheets to view (about 11 for a 15 s recording), the estimated column count, and saves `header.png` (coin balance). Each sheet stacks two frames (#n above #n+1, separated by a magenta bar); consecutive sheets overlap by roughly one column, so you can check continuity by name.
   - View `header.png` for the coin balance, then every `sheets/pair_XX.png` in order. Do this in one pass; that is the only slow part.
   - For each card record: name, `LVL`, and the coin cost on the UPGRADE button. If the card shows a `CARDS a/b` bar instead of UPGRADE, record `cards: [a, b]` (no cost). A black `?` card with a padlock is locked: record the name only.
   - Read order is column by column, top card then bottom card. The last column may have a single card. The final sheet shows the end of the list.
   - Blurry names like MOCEMAN / C6ENT / PIGGOY are two blended frames, not real masks; use the sharp neighbour. Zoom on anything doubtful: `extract_frames.py VIDEO --zoom <seconds>` (times are in the printed manifest) and view the full-resolution crop.
   - If the user also sent screenshots of a mask's (i) popup, they give an exact "X% > Y%" you can use to confirm a level (bonus = base + 0.1 x (level-1)).

4. **Write the spec** (`/tmp/spec.json`; full example in `references/example_spec_oct2026.json`):
   ```json
   {"coins": 62648,
    "masks":  {"Travelboy": {"lvl": 15, "cost": 750}, "Piggy": {"lvl": 34, "cards": [22, 35]}},
    "locked": ["Robot", "Zombie"]}
   ```
   Include EVERY mask you saw. Always include `cost` for coin masks: it must equal 50 x level, which is the checksum that catches misread digits. Use the names exactly as the game shows them.

5. **Dry run, then apply**
   ```
   python3 scripts/apply_update.py work/index.html /tmp/spec.json --dry-run
   python3 scripts/apply_update.py work/index.html /tmp/spec.json
   ```
   The output lists level changes, newly unlocked masks (with their base bonuses), totals and warnings. Resolve every WARNING/ERROR:
   - cost != 50 x lvl -> a digit is misread; zoom in and fix.
   - level went down -> almost certainly misread.
   - "not in the video" -> a mask was skipped in the recording or missed by you; check the sheets, otherwise it is simply kept unchanged.
   - "No bonus data for X" -> a mask unknown to the page and to `references/mask_bonuses.json`: web_search `Tomb of the Mask wiki <name> mask bonus` (mode extended; fetching the fandom URL gives 402), or `scripts/parse_wiki_html.py WIKI.html <name>` if the user uploaded the wiki HTML. Add the result under `"new_masks"` in the spec, e.g. `{"Foo": {"b": {"coins": 20}, "s": "No Snakes", "unlock": "EUR 4.99"}}`.
   Bonuses for new/unlocked masks are filled automatically from the page's LOCKED entry or the bundled wiki reference; existing masks keep their bonuses (the page beats the wiki).

6. **Verify**: `python3 scripts/verify_page.py work/index.html` must print PASS (no JS errors, table rows == MASKS, locked list == LOCKED). It also prints the best mask per situation.

7. **Deliver**: the user wants modified files as a tar.gz.
   ```
   mkdir -p /mnt/user-data/outputs && tar -czf /mnt/user-data/outputs/totm-masks-update.tar.gz -C work index.html
   ```
   then `present_files` on the archive.

8. **Reply briefly**: newly unlocked masks with their bonuses, how many levels changed (name the biggest jumps), progress (e.g. 51 / 59 unlocked) and what is still locked, the new coin balance, and anything you were unsure of or that disagrees with the wiki. Mention once that a cached service worker may need its version bumped. Do not narrate the tooling.

## Things not to do
- Do not hand-edit table rows or rewrite the page; edit data only through `apply_update.py`.
- Do not change the advisor logic. The user rejected "bonus per coin" planning because only the equipped mask's bonuses apply; the advisor ranks masks per situation.
- Do not overwrite existing masks' bonuses from the wiki (it is wrong for Bull, Koala, Wizard, Fire, Eagle, A4).

## Reference
`references/game_facts.md`: game rules (bonus and cost formulas, which masks upgrade with cards), what the Masks screen and its video artefacts look like, data sources and page conventions. Read it when something looks odd.
`references/mask_bonuses.json`: base bonuses, specials and unlock methods for all 62 wiki masks.
