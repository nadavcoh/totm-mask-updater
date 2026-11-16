# Tomb of the Mask: facts learned while building the mask tracker

Read this when something in the video or the data looks odd. Everything here was verified in a real session (Oct 2026).

## Game rules
- A mask's bonus = base % + 0.1% x (level - 1). Confirmed with the in-game (i) popup: Travelboy Lvl 15 "1.4% > 1.5%", Nikandr Lvl 21 "2.0% > 2.1%".
- Coin upgrade cost = 50 x current level (Lvl 1 = 50, Lvl 17 = 850, Lvl 26 = 1300). Used as a checksum against misread levels.
- Base bonuses are always multiples of 5 (Travelboy and Nikandr are 0 and grow from there).
- "More Coins" works everywhere (Stage Mode and Arcade). Every other bonus (score, bonus levels, freezes, magnets, coin addicts) is Arcade only. No Snakes / No Monkeys are fixed perks and do not level.
- Only the EQUIPPED mask's bonuses count. They are never summed across masks. The user explicitly rejected a "bonus per coin across all masks" upgrade plan; the page's advisor therefore ranks masks per situation (best mask for coins, score, bonus levels, freezes, magnets, coin addicts) and shows the cost to catch the leader. Do not reintroduce aggregate or greedy-plan logic.
- Some masks upgrade with CARDS instead of coins. Their card shows a "CARDS a/b" bar where the UPGRADE button would be, and b = level + 1. Octopus has a cyan card. The set CHANGES between videos: Oct 2026 the page flagged 13 masks (Samurai, Frankie, Vampire, Mad Mask, Piranha, Robin, King, Leopard, Octopus, Demon, Froggy, Eagle, Piggy); in the Nov 16 2026 video only Leopard (30/42 at Lvl 41) and Octopus (6/37 at Lvl 36) showed CARDS and all others showed coin prices (e.g. Piggy Lvl 39 = 1,950). apply_update.py clears the card flag when you give a cost, so always record each mask by what its card shows in that video.

## The Masks screen in the recording
- Bottom nav "MASKS" tab; a horizontally scrolling grid, 2 rows. Order is column by column: top card, then the one under it, then the next column. The last column can hold a single card (Spooky in Oct 2026) with an empty slot under it.
- Unlocked card: name, sprite, (i) button, "LVL n", green "UPGRADE (coin) cost". Card-upgrade masks show CARDS a/b instead.
- Locked card: black "?" silhouette, padlock, a CARDS bar with a long truncated number (e.g. "1019/2"). Ignore the numbers; only the NAME matters. Locked masks have no level.
- Coin balance is the number top-left of the header (extract_frames.py saves it as header.png). Oct 2026 values: 61,818 then 62,648.
- Mask names are exactly as displayed in game: Travelboy (one word), Mad Mask, Anonym, A4, Spooky, Nikandr.
- Scroll-blur artefacts: while the grid moves, two frames blend, producing fake names such as "MOCEMAN", "C6ENT", "PIGGOY", "A4:PY", "RABBI". They are never real. The extractor already picks the slowest (sharpest) frames; if a card is still ambiguous, zoom with `extract_frames.py VIDEO --zoom <seconds>`.
- At the end the recording opens the iOS control center (to stop recording). Those frames have ~0% yellow and the extractor drops them automatically.
- Oct 2026 grid: 59 masks total (51 unlocked, 8 locked: Robot, Zombie, Anonym, Mouse, Gas, Nerd, Cup, Eye), 30 columns.
- Nov 16 2026 grid: 59 / 59 unlocked, nothing locked (spec `"locked": []`). Newly unlocked masks sit at their normal grid position (not at the end) with Lvl 1 and price 50 (Robot, Anonym, Mouse, Zombie, Gas, Nerd, Eye, Black, Slime...). Cup jumped 1 -> 45, so big jumps between videos are normal. Column order (top / bottom): Travelboy/Cyclop, Spaceman/Agent, Monkey/Chef, Bull/Crow, Plague/Koala, Bear/Samurai, Dog/Demon, Pumpkin/Spectrum, Robot/Alien, Kitty/Assassin, Cowboy/Zombie, Piggy/Anonym, Hippo/Pirate, Viking/Eagle, Mouse/Rabbit, Froggy/Diver, Robin/Knight, Shapito/King, Frankie/Slime, Black/Skull, Jester/Screamy, Voodoo/Gas, Wizard/Vampire, Nerd/Nikandr, Mad Mask/Cup, Smile/Eye, Sleepy/Fire, A4/Leopard, Piranha/Octopus, Spooky/(empty). Use it to check continuity between sheets and that nothing was skipped; the order can change when masks are added.
- Coin balance Nov 16 2026: 44,460 (the page had 5,327).

## Where data comes from
- index.html is the authority for masks it already contains. The wiki is wrong or garbled for Bull, Koala, Wizard, Fire, Eagle and A4, so never overwrite existing bases from the wiki.
- For NEW masks use, in order: references/mask_bonuses.json (all 62 wiki masks, already bundled and used automatically by apply_update.py) > web search > the wiki HTML the user uploaded (scripts/parse_wiki_html.py).
- Fetching https://tomb-of-the-mask.fandom.com/wiki/Masks directly returns HTTP 402. A web_search such as `Tomb of the Mask wiki Alien mask Slime mask Assassin mask Piggy mask Black mask bonus` (mode "extended") returned the wiki Masks table in the results.
- The wiki also lists Spider, Creepy and Sponge, which were not in the app in Oct 2026. If they show up in a future video their data is already in the bundled reference.
- Wiki columns: Coins, Magnets, Coin Addicts, Freezes, Bonus Levels, Score Boosters, No Snakes, No Monkeys. The page's keys are coins, score, bonus, freezes, magnets, addicts.
- Unlock methods shown on the page for locked masks come from the wiki ("WOF" = Wheel of Fortune, prices in EUR, "Premium subscription"). Anonym's is unknown.

## Page conventions (do not change without being asked)
- All mask data lives in two JS blocks near the top of the script in index.html: `const MASKS = [...]` and `const LOCKED = [...]`, plus `DEFAULT_COINS`. The table, progress bar, locked list, advisor and Oracle chatbot prompt are all generated from them. Update data only; do not hand-edit table rows.
- The user does NOT want code delivered as tar.gz (saved preference). Push index.html to GitHub and do not present it in chat either (the user said so on Nov 16 2026). (An earlier version of this skill said tar.gz; that was superseded.)
- The page lives in the GitHub repo nadavcoh/masks-pwa (main): index.html, manifest.json, sw.js, icons/ and the wiki Masks page saved as HTML and PDF. Pull it from there instead of asking for an upload and push the result back to main (scripts/fetch_index.sh, scripts/push_github.sh). The user's older commits there are "Update from iOS: date"; ours use "Update masks from video YYYY-MM-DD: ...".
- The page registers a service worker. In the repo, sw.js uses `const CACHE_NAME = 'totm-masks-__COMMIT_HASH__'`, a placeholder filled per commit, so no manual cache bump is needed after a push. Only mention a bump if a sw.js without that placeholder shows up.

## Tooling lessons
- The bash tool runs /bin/sh: no process substitution (`diff <(a) <(b)` fails). Use `bash -c`, `cmp` or `git diff --stat`.
- The gh-push-mcp tools are deferred: load them with tool_search first. `git_credentials` mode=write returns a ~1 h token for one repo; use it only via an http.extraheader (scripts/push_github.sh does), never print or store it. github.com and raw.githubusercontent.com are on the sandbox allow-list, so git clone/push and curl work from bash.
- A "repository does not exist or is not accessible to the parent installation" error from git_credentials means the GitHub app installation lacks that repo (it can be a repo that exists and is empty). The user fixes it in the app's repository access; then it works on the next try.
- A fresh empty repo clones fine; push with `HEAD:refs/heads/main` (push_github.sh does).
- apply_update.py, verify_page.py and extract_frames.py needed no changes in the Nov 2026 run: 363 frames -> 11 sheets, 59 masks read in one pass, dry-run showed 8 level changes and 3 unlocks, verify PASS. The only slow part is viewing the sheets.
