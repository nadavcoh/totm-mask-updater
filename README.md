# totm-mask-updater

A Claude skill that updates the [Tomb of the Mask mask tracker](https://github.com/nadavcoh/masks-pwa) from a screen recording of the in-game **Masks** screen.

Give Claude the recording and run `/totm-mask-updater` (or say "update my masks"). Claude then:

1. fetches `index.html` from `nadavcoh/masks-pwa` (`scripts/fetch_index.sh`), so no upload is needed;
2. extracts sharp frames from the video (`scripts/extract_frames.py`) and reads every mask card: level, upgrade price or CARDS bar, locked masks, coin balance;
3. writes the readings as one line per mask and converts them to a spec (`scripts/make_spec.py`);
4. patches the data blocks of the page (`scripts/apply_update.py`), cross-checking each price against 50 x level;
5. verifies the page (`scripts/verify_page.py`);
6. commits and pushes to `main` of `nadavcoh/masks-pwa` (`scripts/push_github.sh`, token from the gh-push-mcp `git_credentials` tool). The push is the delivery: `index.html` is not presented in chat and is never sent as tar.gz.

## Layout

| Path | Purpose |
| --- | --- |
| `SKILL.md` | The workflow Claude follows (read this first) |
| `scripts/fetch_index.sh` | Download the live `index.html` from GitHub |
| `scripts/extract_frames.py` | Video to coin-balance header image and contact sheets of the mask grid |
| `scripts/make_spec.py` | Compact notes (`Name LVL COST` / `Name LVL a/b`) to the JSON spec |
| `scripts/apply_update.py` | `--show` current data; apply a spec (levels, unlocks, coins) with sanity checks |
| `scripts/verify_page.py` | Checks the patched page (data, table rows, JS errors) |
| `scripts/push_github.sh` | Clone, copy, commit and push to `main` using a short-lived token |
| `scripts/migrate_legacy.py`, `scripts/parse_wiki_html.py` | Rare cases: old static-table pages, wiki HTML |
| `references/game_facts.md` | Game rules, grid layout, quirks and lessons from past runs |
| `references/mask_bonuses.json` | Base bonuses of all 62 wiki masks (for newly unlocked masks) |
| `references/example_notes_nov2026.txt`, `references/example_spec_oct2026.json` | Worked examples of the notes and spec formats |
| `assets/index_template.html` | Page template used when migrating an old page |

## Using it

Copy the folder to a Claude skills location (or upload the zip as a skill). Pushing needs the gh-push-mcp connector with the GitHub app granted access to the target repo; if `git_credentials` reports the repo as inaccessible, add it to the app's repository list.
