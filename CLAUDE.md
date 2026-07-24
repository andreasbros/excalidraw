# CLAUDE.md — how this repo works

Self-hosted, searchable **Excalidraw icon gallery** (works behind a proxy that blocks
`libraries.excalidraw.com`). Live at <https://andreasbros.github.io/excalidraw/> via
GitHub Pages (source: `main` branch, `/docs`).

## Layout

```
<category>/*.excalidrawlib   # the icon libraries, grouped into category folders
                             # (gcp, aws, azure, oracle, architecture, network,
                             #  cloud-k8s-devops, logos, diagrams, ui, misc, brands)
brands/                      # brand/company logos, IMAGE-based .excalidrawlib
docs/                        # the published gallery (GitHub Pages root)
  index.html app.js style.css
  icons.json                # index: one record per icon (see fields below)
  data/<cat>__<lib>.json     # per-library payload: [{name, elements, files?}]
  thumbs/<id>.svg            # one faithful thumbnail per icon
  vendor/fuse.min.js         # vendored fuzzy search (no CDN)
  icons/ manifest.webmanifest# PWA icon + manifest
tools/                       # build pipeline (see below)
catalogues/                  # optional per-library .excalidraw browse scenes
NOTICE.md                    # trademark disclaimer for brand logos
```

### Icon id / share ref (stable, global)
`id = <category>__<library>__<index>` e.g. `gcp__gcp-icons__5`. It is BOTH the thumbnail
filename (`thumbs/<id>.svg`) and the share/deep-link ref (`…/#<id>`). Reused everywhere —
keep it stable (don't recategorise a library casually).

## The build pipeline (`tools/`)

Two steps, always run in order:

```bash
python3 tools/build.py            # 1. data + icons.json + keywords/tags/summary
node    tools/render-thumbs.mjs   # 2. faithful thumbnails (needs puppeteer-core)
```

- **`build.py`** scans every `*/*.excalidrawlib`, writes `docs/data/*.json` and
  `docs/icons.json`. It does NOT render thumbnails (so it never clobbers the faithful
  ones). Per icon it computes:
  - `name`, `lib`, `libName`, `author` (author/libName pulled from the upstream
    `libraries.json`, cached in `tools/.cache/`), `cat`, `catLabel`, `src`, `idx`.
  - `kw` — search keywords: embedded **text labels** drawn inside the icon + **visual
    descriptors** read from the element data (shape, colour, `dashed`/`dotted`, `filled`)
    via `visual_keywords()` / `_color_name()`.
  - `tags` — clean deduped display keywords; `summary` — one-line description.
  - Then MERGES `tools/vision.json` if present (see vision pipeline) to overwrite
    `summary` and prepend vision keywords.
- **`render-thumbs.mjs`** drives headless Chromium (puppeteer-core → `/usr/bin/google-chrome`)
  to run Excalidraw's own `exportToSvg` on every item = 100% faithful (rough.js hand-drawn
  style, hachure fills, gradients, brand images). It strips the external `@font-face`
  `<style>` block so the SVGs are self-contained/proxy-safe (text falls back to a system
  font). One-time setup: `cd tools && npm i puppeteer-core`.

### Add more libraries (one command)
```bash
python3 tools/add-library.py --category misc "Robots" "Traffic signs"   # by name
python3 tools/add-library.py --category logos author/file.excalidrawlib # by source path
python3 tools/add-library.py --search kubernetes                        # search catalogue
```
It resolves the name against the upstream index, downloads into the category folder,
runs `build.py`, then runs `render-thumbs.mjs`. Then `git add -A && git commit && git push`.

### Add brand/company logos (image-based)
1. Drop SVG/PNG logos into `/tmp/brandlogos/<brand>/<variant>.svg`.
2. `python3 tools/make-brand-lib.py /tmp/brandlogos` → writes `brands/<brand>.excalidrawlib`
   with each logo embedded as an Excalidraw **image element** + a top-level `files` map.
3. `python3 tools/build.py && node tools/render-thumbs.mjs`.
Sources: Simple Icons (`raw.githubusercontent.com/simple-icons/simple-icons`),
VectorLogo.zone, Wikimedia `Special:FilePath/<Name>.svg`, GitHub org avatars. Add every
brand to `NOTICE.md` (generic trademark disclaimer, no company names in the text).

## Vision keyword/summary pipeline (what each icon depicts)

Metadata keywords miss "what is drawn" (a padlock, a robot, a brand). To capture that:

1. `docs/_sheets/` — `build.py`-adjacent script renders **labeled contact sheets** (30
   icons per sheet, 6-col grid, red index per cell) to PNG via headless Chrome, plus a
   `manifest.json` mapping sheet → ordered icon ids.
2. **Fan out to parallel vision subagents** (Agent tool, `general-purpose`, ~4 sheets each).
   Each Reads the PNGs (Read shows images) + manifest and returns
   `[{id, kw:[...], summary:"..."}]`. Have them WRITE the JSON to files
   (`/tmp/vision/vNN.json`) via SendMessage rather than only returning text — easier to merge.
3. Merge all into `tools/vision.json` (committed). `build.py` folds it into `summary`/`tags`/`kw`.

## Search (`docs/app.js`)

Fuse.js candidate pool (per-token) + a custom graded ranker: exact name > name prefix/
phrase > library-name match > all-words-in-name > all-words-anywhere (AND) > fuzzy.
Multi-word queries filter to full matches. Search text = name(x2) + author + libName +
filename + category + provider synonyms + `kw` + `summary`. Infinite scroll (100/chunk,
IntersectionObserver), session-state restore, clicking an icon opens the lightbox modal
(preview + Copy/Share/Download + carousel), deep-link `#<id>`.

## Deploy / gotchas

- Commit `docs/` + the changed `*.excalidrawlib` and push; GitHub Pages redeploys `main /docs`.
- Clicking an icon copies Excalidraw clipboard JSON: `{type:"excalidraw/clipboard",elements,files}`.
- `.gitignore`: `tools/.cache/`, `tools/node_modules/`.
- Headless Chrome sometimes won't exit cleanly (virtual-time) but still writes the file;
  ImageMagick can't render the nested-SVG data-URIs — always verify thumbnails in a real
  browser, not `convert`.
