# Setup guide

This turns the files in this folder into a live, animated GitHub
profile README. Everything here has been built and test-run already
(the scraper and heatmap renderer were verified end-to-end against a
real GitHub account's contribution data) — the only two things left
are **your** photo and **your** GitHub username.

## 0. One-time repo setup

GitHub gives every account one special repo: a repo whose name is
*exactly your username*. Its `README.md` renders at the top of your
profile page.

```bash
# replace YOUR_USERNAME with your actual GitHub username
gh repo create YOUR_USERNAME --public --clone
cd YOUR_USERNAME
```

Copy every file from this folder into that repo (keeping the folder
structure: `scripts/`, `.github/workflows/`, `README.md`, etc).

## 1. Install the toolchain

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt
```

The portrait step (`pillow`, `numpy`, `opencv-python`, `rembg`) only
ever runs locally when you change your photo. The daily automation
only needs `requests` and `beautifulsoup4`.

## 2. Generate the ASCII portrait (one time, or whenever your photo changes)

```bash
python scripts/prep_photo.py source-photo.jpg      # -> source-prepped.png
python scripts/make_ascii_svg.py                   # -> ascii-portrait.svg
```

`prep_photo.py` removes the background, composites onto white, and
boosts local contrast (CLAHE) so a flatly-lit face doesn't convert to
a dark blob. `make_ascii_svg.py` downsamples that to a ~100x53
character grid and picks a glyph per pixel from a brightness ramp.

## 3. Fill in and generate the info card

Open `scripts/make_info_card.py` and edit the `USER`, `HOST`, and
`ROWS` values at the top to your own `Now` / `Prev` / `Stack` /
`Highlights` lines — the draft copy in there right now is just a
starting point. Then:

```bash
python scripts/make_info_card.py                  # -> info-card.svg
```

## 4. Point the heatmap scraper at your account

Open `scripts/fetch_contributions.py` and replace:

```python
USERNAME = "YOUR_GITHUB_USERNAME"
```

with your real GitHub username. Then generate it once locally to
confirm it works:

```bash
python scripts/fetch_contributions.py              # -> data/contributions.json
python scripts/render_heatmap_svg.py                # -> contrib-heatmap.svg
```

No token or GraphQL API needed — it reads the same public HTML
fragment (`github.com/users/<username>/contributions`) your profile
page already uses.

## 5. Commit and push

```bash
git add .
git commit -m "profile: ascii portrait + info card + contribution heatmap"
git push
```

Your profile page will now show the terminal-style layout.

## 6. Turn on the daily refresh

The workflow at `.github/workflows/update-profile-art.yml` re-scrapes
and re-renders **only the heatmap** every day at ~06:17 UTC and commits
the result (the portrait and info card are static — regenerate those
yourself only when your photo or details change).

Trigger it once by hand to confirm it works: go to the repo's
**Actions** tab → **Update profile art** → **Run workflow**. Check
that it commits an updated `contrib-heatmap.svg`.

---

### Why this works as "animated" on GitHub

GitHub strips `<script>` tags from READMEs and sanitizes almost all
inline CSS on the page itself — but SVGs referenced via `<img>` are
loaded as separate image resources, so their internal SMIL/CSS
animations still play in the browser. That's the whole trick: push all
motion inside the SVG files, and let `README.md` just place them.

Two markdown gotchas worth knowing if you tweak the layout:
- Inline `style="margin-top:..."` is stripped — the only spacing
  GitHub honors is `<br>`.
- `<h1>`/`<h2>` draw a full-width underline rule; use `<h3>` if you
  don't want it.
