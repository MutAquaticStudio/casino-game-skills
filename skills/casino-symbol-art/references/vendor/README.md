# Vendored art toolkits

Two third-party toolkits, copied in so the skill works offline. Casino-specific guidance for
both is in `../svg-craft.md` and `../raster-art.md`; read those first, not the vendored files.

| Folder | Source | License | What it gives |
|---|---|---|---|
| `svg-design/` | https://github.com/tryopendata/skills, plugin `opendesign`, skill `svg-design` v1.3.2 | MIT, see `svg-design/LICENSE` | Hand-written SVG craft: path commands, arc flags, gradients/masks/filters, icon grids, logo process, SVGO, accessibility, SVG animation |
| `claude-drawing/` | https://github.com/cloveric/claude-drawing-skill | MIT, see `claude-drawing/LICENSE` | A numpy + Pillow painting library (`lib/`, 83 modules, 82 styles), 86 example scripts (`examples/`), and the full API and failure checklist (`GUIDE.md`, Chinese) |

What was changed from upstream:
- `SKILL.md` was renamed `GUIDE.md` in both folders so a skill loader does not treat it as a
  separate skill. File contents are unchanged.
- `svg-design/`: `references/` and `assets/preview.html` copied as is.
- `claude-drawing/`: copied `lib/`, `examples/*.py`, `docs/STYLES.md`, `docs/PRINCIPLES.md`,
  `docs/USAGE.md`, `requirements.txt`, `LICENSE`. **Not copied:** the 151 MB of example
  JPG/GIF renders, `docs/thumbs`, `docs/hero.jpg` and the translated docs. Look at the upstream
  repo to see what each style looks like.
- Run examples from this folder: `python3 examples/<name>.py out.png`. They find `lib/` by
  relative path. Needs `pip install -r requirements.txt` (numpy, Pillow).

Stake rules still win over anything in these guides: art must be original (no copied
characters, logos, stock images or a named artist's artwork), and the build stays static with
no remote fonts or images. Upstream examples (`examples/*.py`) are study material; do not ship
their output as a game's art.

To update: re-clone upstream, replace the folder, re-apply the two changes above.
