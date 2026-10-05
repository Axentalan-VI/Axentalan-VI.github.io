# axentalan-vi.github.io

Personal portfolio for Ahmed Elfiky — AI Engineer.
Live at <https://axentalan-vi.github.io>.

Plain static site: HTML, CSS and vanilla JavaScript, with no build step and no
runtime dependencies. All content lives in `data/profile.json` and
`data/projects.json`; `assets/app.js` renders it.

## Adding or editing a project

Edit `data/projects.json`. One object per project:

| Field | Meaning |
|---|---|
| `id` | Unique slug, used as the DOM id |
| `title` | Display name |
| `track` | `"ml"` or `"agents"` — drives the filter |
| `featured` | `true` for a full card, `false` for a compact one |
| `problem` | One sentence: what the problem is |
| `approach` | 2–3 bullets (featured cards only) |
| `constraint` | The hard constraint the solution had to meet, or `null` |
| `tags` | Technology tags |
| `status` | `"in-progress"`, `"submitted"` or `"completed"` |
| `repo` | Repository URL, or `null` for no link |
| `competition` | Competition URL, or `null` for no link |
| `outcome` | Verified leaderboard result, or `null` |

Nothing else needs to change — no markup edits.

## Local preview

```bash
cd site
python -m http.server 8000
```

Then open <http://localhost:8000>. Opening `index.html` directly from the
filesystem will **not** work: the JSON is loaded with `fetch`, which browsers
block over `file://`. That is expected, not a bug.

## Checks before pushing

```bash
python -m pytest tests/ -v        # data integrity and content rules
python scripts/check_links.py     # every outbound URL returns 200
```

Outcomes shown on the cards come from the owner's own Kaggle submission
history. Refresh them with:

```bash
KAGGLE_CONFIG_DIR=E:/Kaggle PYTHONUTF8=1 python scripts/fetch_scores.py
```
