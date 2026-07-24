#!/usr/bin/env python3
"""Rebuild the searchable gallery (docs/) from every *.excalidrawlib in the
category folders. Run after adding or changing any library.

    python3 tools/build.py

Outputs: docs/thumbs/*.svg, docs/data/*.json, docs/icons.json, INDEX.md
"""
import json, glob, os, sys, re, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from exsvg import render

DOCS = os.path.join(ROOT, "docs")
SKIP_DIRS = {"docs", "catalogues", "tools", ".git", "node_modules"}
INDEX_URL = "https://raw.githubusercontent.com/excalidraw/excalidraw-libraries/main/libraries.json"

def author_map():
    """basename.excalidrawlib -> {author, libname} from the upstream index (cached)."""
    cache = os.path.join(HERE, ".cache", "libraries.json")
    if not os.path.exists(cache):
        try:
            os.makedirs(os.path.dirname(cache), exist_ok=True)
            req = urllib.request.Request(INDEX_URL, headers={"User-Agent": "build"})
            open(cache, "wb").write(urllib.request.urlopen(req, timeout=30).read())
        except Exception as ex:
            print("author lookup offline, skipping:", ex)
            return {}
    m = {}
    for l in json.load(open(cache)):
        src = l.get("source", "")
        base = src.split("/", 1)[1] if "/" in src else src
        if base and base not in m:
            m[base] = {"author": "; ".join(a.get("name", "") for a in l.get("authors", []) if a.get("name")),
                       "libname": l.get("name", "")}
    return m

CAT_LABEL = {
    "gcp": "GCP", "aws": "AWS", "azure": "Azure", "oracle": "Oracle Cloud",
    "architecture": "Architecture", "network": "Network",
    "cloud-k8s-devops": "Cloud / K8s / DevOps", "logos": "Logos",
    "diagrams": "Diagrams / Charts", "ui": "UI / Wireframe", "misc": "Misc / Fun",
    "brands": "Brands / Logos",
}

def catlabel(c):
    return CAT_LABEL.get(c, c.replace("-", " ").replace("_", " ").title())

def item_thumb(els, libfiles):
    """Image-based item -> wrap the embedded data URL in an SVG. Else vector render."""
    for e in els:
        if e.get("type") == "image" and e.get("fileId") in libfiles:
            w, h = e.get("width", 100), e.get("height", 100)
            url = libfiles[e["fileId"]]["dataURL"]
            return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
                    f'width="{w}" height="{h}"><image href="{url}" x="0" y="0" '
                    f'width="{w}" height="{h}"/></svg>')
    return render(els)


def _color_name(c):
    if not c or not isinstance(c, str): return None
    c = c.strip().lower()
    if c in ("transparent", "none") or c.startswith("url("): return None
    if c.startswith("#"): c = c[1:]
    if len(c) == 3: c = "".join(ch * 2 for ch in c)
    if len(c) == 8: c = c[:6]
    if len(c) != 6: return None
    try:
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    except ValueError:
        return None
    mx, mn = max(r, g, b), min(r, g, b); d = mx - mn; l = (mx + mn) / 510
    if l > 0.93: return "white"
    if l < 0.10: return "black"
    if d < 26: return "gray grey"
    if mx == r: h = ((g - b) / d) % 6
    elif mx == g: h = (b - r) / d + 2
    else: h = (r - g) / d + 4
    h *= 60
    if h < 0: h += 360
    if h < 15 or h >= 345: return "red"
    if h < 45: return "orange"
    if h < 66: return "yellow"
    if h < 170: return "green"
    if h < 200: return "teal cyan"
    if h < 255: return "blue"
    if h < 290: return "purple violet"
    return "pink magenta"

_SHAPE = {"rectangle": ["rectangle", "square", "box"], "ellipse": ["circle", "ellipse", "round"],
          "diamond": ["diamond", "rhombus"], "line": ["line"], "arrow": ["arrow"],
          "freedraw": ["sketch"], "draw": ["sketch"]}

def visual_keywords(els):
    """Shape / stroke-style / colour / fill descriptors from the elements themselves."""
    kw = set()
    for e in els:
        if not isinstance(e, dict): continue
        t = e.get("type")
        if t in ("text", "image"): continue
        kw.update(_SHAPE.get(t, []))
        if e.get("strokeStyle") in ("dashed", "dotted"):
            kw.add(e["strokeStyle"])
        for col in (e.get("strokeColor"), e.get("backgroundColor")):
            nm = _color_name(col)
            if nm: kw.update(nm.split())
        bg = e.get("backgroundColor")
        if bg and bg != "transparent" and _color_name(bg) and e.get("fillStyle") == "solid":
            kw.add("filled")
    return kw

STOP = set("a an the is are be was were it its of to in on and or for with this that as at by what does do how you your can will".split())

def build():
    os.makedirs(os.path.join(DOCS, "thumbs"), exist_ok=True)
    os.makedirs(os.path.join(DOCS, "data"), exist_ok=True)
    authors = author_map()
    icons = []
    for f in sorted(glob.glob(os.path.join(ROOT, "*", "*.excalidrawlib"))):
        cat = os.path.basename(os.path.dirname(f))
        if cat in SKIP_DIRS:
            continue
        lib = os.path.basename(f)[:-len(".excalidrawlib")]
        meta = authors.get(os.path.basename(f), {})
        author = meta.get("author", "")
        libname = meta.get("libname", "")
        d = json.load(open(f))
        items = d.get("libraryItems", d.get("library", []))
        libfiles = d.get("files", {})
        src = f"{cat}__{lib}"
        payload = []
        for i, it in enumerate(items):
            els = it.get("elements", it) if isinstance(it, dict) else it
            name = (it.get("name") or "").strip() if isinstance(it, dict) else ""
            iid = f"{src}__{i}"
            # keywords from any text the icon draws inside itself (labels)
            texts = [ (e.get("text") or "").strip() for e in els
                      if isinstance(e, dict) and e.get("type") == "text" ]
            texts = [t for t in texts if t]
            vkw = visual_keywords(els)
            kw = re.sub(r"\s+", " ", " ".join(texts + sorted(vkw))).strip()
            tags = []
            for w in re.findall(r"[a-z0-9]+",
                                f"{name} {' '.join(texts)} {' '.join(sorted(vkw))}".lower()):
                if len(w) >= 2 and w not in STOP and w not in tags:
                    tags.append(w)
            tags = tags[:18]
            base = name or (texts[0] if texts else "") or libname or "Icon"
            summary = base if (not libname or libname.lower() in base.lower()) else f"{base} - {libname}"
            # Thumbnails are rendered separately by tools/render-thumbs.mjs using
            # Excalidraw's own exportToSvg (100% faithful). build.py only emits
            # data + icons.json so it never clobbers those faithful thumbnails.
            ifiles = {e["fileId"]: libfiles[e["fileId"]] for e in els
                      if e.get("fileId") in libfiles}
            entry = {"name": name, "elements": els}
            if ifiles:
                entry["files"] = ifiles
            payload.append(entry)
            icons.append({"id": iid, "name": name, "lib": lib, "libName": libname,
                          "author": author, "cat": cat, "catLabel": catlabel(cat),
                          "kw": kw, "tags": tags, "summary": summary, "src": src, "idx": i})
        json.dump(payload, open(os.path.join(DOCS, "data", src + ".json"), "w"))
    json.dump(icons, open(os.path.join(DOCS, "icons.json"), "w"))

    # searchable text index for the named ones
    idx_lines = ["# Component Index (searchable)\n",
                 "Ctrl+F for a component name. Faster: the",
                 "[web gallery](https://andreasbros.github.io/excalidraw/).\n"]
    for f in sorted(glob.glob(os.path.join(ROOT, "*", "*.excalidrawlib"))):
        cat = os.path.basename(os.path.dirname(f))
        if cat in SKIP_DIRS:
            continue
        rel = os.path.relpath(f, ROOT)
        d = json.load(open(f))
        items = d.get("libraryItems", d.get("library", []))
        names = sorted({(it.get("name") or "").strip() for it in items
                        if isinstance(it, dict) and (it.get("name") or "").strip()})
        if names:
            idx_lines.append(f"### `{rel}`  ({len(names)} named / {len(items)} total)\n")
            idx_lines.append(", ".join(names) + "\n")
        else:
            idx_lines.append(f"### `{rel}`  ({len(items)} components, all unnamed)\n")
    open(os.path.join(ROOT, "INDEX.md"), "w").write("\n".join(idx_lines))

    from collections import Counter
    by = Counter(i["catLabel"] for i in icons)
    print(f"built {len(icons)} icons  (now run: node tools/render-thumbs.mjs)")
    print("by category:", dict(by))
    return len(icons)

if __name__ == "__main__":
    build()
