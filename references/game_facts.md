# Tomb of the Mask: facts learned while building the mask tracker

Read this when something in the video or the data looks odd. Everything here was verified in a real session (Oct 2026).

## Game rules
- A mask's bonus = base % + 0.1% x (level - 1). Confirmed with the in-game (i) popup: Travelboy Lvl 15 "1.4% > 1.5%", Nikandr Lvl 21 "2.0% > 2.1%".
- Coin upgrade cost = 50 x current level (Lvl 1 = 50, Lvl 17 = 850, Lvl 26 = 1300). Used as a checksum against misread levels.
- Base bonuses are always multiples of 5 (Travelboy and Nikandr are 0 and grow from there).
- "More Coins" works everywhere (Stage Mode and Arcade). Every other bonus (score, bonus levels, freezes, magnets, coin addicts) is Arcade only. No Snakes / No Monkeys are fixed perks and do not level.
- Only the EQUIPPED mask's bonuses count. They are never summed across masks. The user explicitly rejected a "bonus per coin across all masks" upgrade plan; the page's advisor therefore ranks masks per situation (best mask for coins, score, bonus levels, freezes, magnets, coin addicts) and shows the cost to catch the leader. Do not reintroduce aggregate or greedy-plan logic.
- Some masks upgrade with CARDS instead of coins (as of Oct 2026: Piggy, Piranha, Octopus). Their card shows a "CARDS a/b" bar where the UPGRADE button would be, and b = level + 1. Octopus has a cyan card. A mask can switch category between videos, so always take it from the video.

## The Masks screen in the recording
- Bottom nav "MASKS" tab; a horizontally scrolling grid, 2 rows. Order is column by column: top card, then the one under it, then the next column. The last column can hold a single card (Spooky in Oct 2026) with an empty slot under it.
- Unlocked card: name, sprite, (i) button, "LVL n", green "UPGRADE (coin) cost". Card-upgrade masks show CARDS a/b instead.
- Locked card: black "?" silhouette, padlock, a CARDS bar with a long truncated number (e.g. "1019/2"). Ignore the numbers; only the NAME matters. Locked masks have no level.
- Coin balance is the number top-left of the header (extract_frames.py saves it as header.png). Oct 2026 values: 61,818 then 62,648.
- Mask names are exactly as displayed in game: Travelboy (one word), Mad Mask, Anonym, A4, Spooky, Nikandr.
- Scroll-blur artefacts: while the grid moves, two frames blend, producing fake names such as "MOCEMAN", "C6ENT", "PIGGOY", "A4:PY", "RABBI". They are never real. The extractor already picks the slowest (sharpest) frames; if a card is still ambiguous, zoom with `extract_frames.py VIDEO --zoom <seconds>`.
- At the end the recording opens the iOS control center (to stop recording). Those frames have ~0% yellow and the extractor drops them automatically.
- Oct 2026 grid: 59 masks total (51 unlocked, 8 locked: Robot, Zombie, Anonym, Mouse, Gas, Nerd, Cup, Eye), 30 columns.

## Where data comes from
- index.html is the authority for masks it already contains. The wiki is wrong or garbled for Bull, Koala, Wizard, Fire, Eagle and A4, so never overwrite existing bases from the wiki.
- For NEW masks use, in order: references/mask_bonuses.json (all 62 wiki masks, already bundled and used automatically by apply_update.py) > web search > the wiki HTML the user uploaded (scripts/parse_wiki_html.py).
- Fetching https://tomb-of-the-mask.fandom.com/wiki/Masks directly returns HTTP 402. A web_search such as `Tomb of the Mask wiki Alien mask Slime mask Assassin mask Piggy mask Black mask bonus` (mode "extended") returned the wiki Masks table in the results.
- The wiki also lists Spider, Creepy and Sponge, which were not in the app in Oct 2026. If they show up in a future video their data is already in the bundled reference.
- Wiki columns: Coins, Magnets, Coin Addicts, Freezes, Bonus Levels, Score Boosters, No Snakes, No Monkeys. The page's keys are coins, score, bonus, freezes, magnets, addicts.
- Unlock methods shown on the page for locked masks come from the wiki ("WOF" = Wheel of Fortune, prices in EUR, "Premium subscription"). Anonym's is unknown.

## Page conventions (do not change without being asked)
- All mask data lives in two JS blocks near the top of the script in index.html: `const MASKS = [...]` and `const LOCKED = [...]`, plus `DEFAULT_COINS`. The table, progress bar, locked list, advisor and Oracle chatbot prompt are all generated from them. Update data only; do not hand-edit table rows.
- The user wants modified/new code files delivered as a tar.gz archive (present it with present_files), not as loose files.
- The page registers a service worker (sw.js, not part of the upload). If it caches index.html, the user must bump its cache version for the update to show; mention this once in the final reply.
