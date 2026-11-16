---
name: totm-mask-updater
description: Update the user's Tomb of the Mask mask-tracker web page (index.html, GitHub repo nadavcoh/masks-pwa) from a screen recording of the in-game Masks screen. Reads mask levels, newly unlocked masks, locked masks and the coin balance from the video, looks up bonuses for new masks, patches the page data, verifies it and pushes it to GitHub (the push is the delivery; index.html is not presented in chat). Use this whenever the user uploads a Tomb of the Mask video or screenshots (with or without index.html), invokes /totm-mask-updater, or says things like "update my masks", "I unlocked new masks", "update levels from this video", "refresh the mask table", even if they do not name the skill.
---

# Tomb of the Mask mask updater

The page keeps all mask data in two JS blocks (`MASKS`, `LOCKED`) and `DEFAULT_COINS`; everything else (table, progress bar, locked list, "who to upgrade" advisor, Oracle chatbot prompt) is generated from them. So an update is: read the video -> write a small JSON spec -> run `apply_update.py`. The scripts do the heavy lifting; your job is reading the cards accurately.

Scripts are in `scripts/`: `fetch_index.sh` (pull the page from GitHub), `extract_frames.py`, `make_spec.py`, `apply_update.py`, `verify_page.py`, `push_github.sh` (push to main), plus `migrate_legacy.py` and `parse_wiki_html.py` for rare cases. Do not read the whole index.html (it is ~800 lines); use `--show`.

## Workflow

1. **Locate inputs**: the video (.mp4/.mov) in `/mnt/user-data/uploads`, optionally screenshots or the wiki HTML.
   - **index.html: do not ask the user to upload it.** The live page is the GitHub repo `nadavcoh/masks-pwa` (branch `main`). Run `scripts/fetch_index.sh` (default destination `/home/claude/work/index.html`). Only use an uploaded index.html if the user attached one (then it is the authority and the push in step 7 is offered, not automatic).
   - If `grep -c "const MASKS = \[" index.html` is 0, it is an older static-table version: run `scripts/migrate_legacy.py index.html --out work/index.html` first (it rebuilds the page from `assets/index_template.html`).

2. **See the current data**: `python3 scripts/apply_update.py work/index.html --show` (one compact line per mask, with levels).

3. **Extract the video**: `python3 scripts/extract_frames.py VIDEO --outdir /tmp/totm`
   It prints the sheets to view (about 11 for a 15 s recording), the estimated column count, and saves `header.png` (coin balance). Each sheet stacks two frames (#n above #n+1, separated by a magenta bar); consecutive sheets overlap by roughly one column, so you can check continuity by name.
   - View `header.png` for the coin balance, then every `sheets/pair_XX.png` in order. Do this in one pass; that is the only slow part, so say in one line what you are doing before you start it (the user sees nothing while sheets load). The last sheet is often a single frame that just repeats the end of the list: it confirms the final column and can be skimmed.
   - For each card record: name, `LVL`, and the coin cost on the UPGRADE button. If the card shows a `CARDS a/b` bar instead of UPGRADE, record `cards: [a, b]` (no cost). A black `?` card with a padlock is locked: record the name only.
   - Read order is column by column, top card then bottom card. The last column may have a single card. The final sheet shows the end of the list.
   - Blurry names like MOCEMAN / C6ENT / PIGGOY are two blended frames, not real masks; use the sharp neighbour. Zoom on anything doubtful: `extract_frames.py VIDEO --zoom <seconds>` (times are in the printed manifest) and view the full-resolution crop.
   - If the user also sent screenshots of a mask's (i) popup, they give an exact "X% > Y%" you can use to confirm a level (bonus = base + 0.1 x (level-1)).

4. **Write the spec** the short way: take notes in `/tmp/notes.txt`, one mask per line, then `python3 scripts/make_spec.py /tmp/notes.txt` (writes `/tmp/spec.json`). Format (full example: `references/example_notes_nov2026.txt`):
   ```
   coins 44460
   Travelboy 15 750        # name, LVL, coin price on the UPGRADE button
   Mad Mask 38 1900
   Leopard 41 30/42        # card masks: a/b from the CARDS bar, no price
   locked Robot, Zombie    # only when padlock '?' cards were seen
   ```
   Include EVERY mask you saw. Always type the price you actually read: it must equal 50 x level, which is the checksum that catches misread digits (make_spec.py deliberately does not compute it). Use the names exactly as the game shows them. Record each mask by what its card shows NOW (UPGRADE price vs CARDS bar): which masks use cards changes between videos, so never carry the old `*` over (see `references/game_facts.md`). Writing the JSON by hand also works (`references/example_spec_oct2026.json`).

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

7. **Deliver and push** (the user's standing workflow: pull index.html from GitHub, update it, push it back):
   - **Do not present index.html** (no `present_files`, no copy to outputs): the user said not to, the push to GitHub is the delivery. If the push is impossible (access error, or the user uploaded the page and did not want a push), say so and only then offer the file. Never deliver code as tar.gz either (saved preference; the old version of this skill said the opposite).
   - Push to `main` of `nadavcoh/masks-pwa`: when the page came from GitHub, do it right after verify PASS and every warning is resolved, without asking again (the user answered "Push" every time). When the user uploaded their own index.html, offer instead of pushing.
     1. Load the connector tools: `tool_search` query `gh-push-mcp` (they are deferred).
     2. `git_credentials` with `repo: nadavcoh/masks-pwa`, `mode: write`. The token appears in the tool result.
     3. `TOKEN='<token>' scripts/push_github.sh nadavcoh/masks-pwa "<message>" /home/claude/work/index.html=index.html` (clones, copies, commits, pushes to main, prints the new commit). Never echo the token, write it to a file, or put it in a URL; the script scrubs it from output. `DRY_RUN=1` skips the push.
     4. Commit message format: `Update masks from video YYYY-MM-DD: unlock A, B; N level changes; coins X`.
   - If `git_credentials` says the repo "does not exist or is not accessible to the parent installation", the GitHub app has no access to that repo: tell the user to add it to the app's repository list and stop. Do not retry in a loop.
   - Pushing directly to `main` is what the user wants for all of his repos (the connector is configured to allow it). Do not open branches or PRs.

8. **Reply briefly**: newly unlocked masks with their bonuses, how many levels changed (name the biggest jumps), progress (e.g. 59 / 59 unlocked) and what is still locked, the old -> new coin balance, the pushed commit hash, and anything you were unsure of or that disagrees with the wiki. Mention if masks switched between coin and card upgrades. Service worker: the repo's `sw.js` names its cache `totm-masks-__COMMIT_HASH__`, so a new commit refreshes it by itself; say only "reload once or twice if the PWA shows old data". Do not narrate the tooling. Refer to files by name, not "above"/"below".

## Things not to do
- Do not ask the user to upload index.html (fetch it from GitHub), do not wait for permission to push after a clean verify, do not present index.html as a file, and do not deliver tar.gz.
- Do not run `diff <(...)` in the bash tool (it is /bin/sh); use `git diff --stat` or `cmp`.
- Do not hand-edit table rows or rewrite the page; edit data only through `apply_update.py`.
- Do not change the advisor logic. The user rejected "bonus per coin" planning because only the equipped mask's bonuses apply; the advisor ranks masks per situation.
- Do not overwrite existing masks' bonuses from the wiki (it is wrong for Bull, Koala, Wizard, Fire, Eagle, A4).

## Reference
`references/game_facts.md`: game rules (bonus and cost formulas, which masks upgrade with cards), what the Masks screen and its video artefacts look like, data sources and page conventions. Read it when something looks odd.
`references/mask_bonuses.json`: base bonuses, specials and unlock methods for all 62 wiki masks.
