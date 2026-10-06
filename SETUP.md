# Tim-1e Profile README — Build Notes

This repository is the GitHub profile README for `Tim-1e`.
The look is a "field file": every panel is a hand-written SVG built by the scripts in `scripts/`.

## Two views

The README holds two exclusive `<details name="view">` blocks (GitHub keeps the `name` attribute, so opening
one closes the other; no JS). Their `<summary>` images are wrapped in `<picture>` so GitHub does not turn them
into links.

- **Field File** (default, open): the generated panels below.
- **Classic**: the original cards in `assets/classic/`, `stats-classic.svg` / `top-langs-classic.svg`,
  and the action's default `profile-season-animate.svg`.

The profile-views counter appears only once (shared badge row above both views): images inside a closed
`<details>` still load, so a second counter would double count.

## Layout

```text
assets/hero.svg            animated hero + path-traced viewport (1 → 256 spp)
assets/nav/*.svg           navigation tabs
assets/sections/*.svg      section headers
assets/profile.svg         operator profile (rotating wireframe + attribute radar)
assets/loadout.svg         languages and tools
assets/missions/*.svg      project cards
assets/archive-feed.svg    latest blog entries (synced from RSS by Actions)
assets/footer.svg
assets/src/                fonts (woff2 subsets + metrics), icons, viewport frames
```

## Rebuilding

```bash
# optional: re-render the viewport frames (numpy + pillow, ~4 min on one core)
python scripts/render_viewport.py

# rebuild every SVG (standard library; installs of fonttools+brotli shrink the embedded fonts)
python scripts/build_assets.py
```

Edit texts, projects and the loadout directly in `scripts/build_assets.py`.

Preview: `python scripts/preview.py` writes `_preview.html` (git-ignored) — the README in a GitHub-like
848px column with dark/light switches; append `#classic` to the URL to start on the Classic view.
Scripts must stay Python 3.10 compatible (no reuse of an f-string's quote inside `{}`).

## Workflows

All use the built-in `GITHUB_TOKEN`; `Settings -> Actions -> General -> Workflow permissions`
must be `Read and write permissions`.

| Workflow | Output | Runs |
| --- | --- | --- |
| `profile-3d.yml` | default set incl. `profile-season-animate.svg` (Classic) + `profile-field.svg` (theme: `.github/profile-3d.json`) | daily, on push of its settings |
| `readme-stats.yml` | `assets/github-stats/stats.svg`, `top-langs.svg` + `*-classic.svg` (tokyonight) | daily, on push of the workflow |
| `archive-feed.yml` | `assets/archive-feed.svg` from `https://blog.princival.com/rss.xml` | daily, on push of the scripts |

Stats cards are committed into the repository so the profile does not depend on the public
`github-readme-stats.vercel.app` deployment (which is frequently paused with `503 DEPLOYMENT_PAUSED`).
