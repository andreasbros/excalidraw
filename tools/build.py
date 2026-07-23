#!/usr/bin/env python3
"""Rebuild the searchable gallery (docs/) from every *.excalidrawlib in the
category folders. Run after adding or changing any library.

    python3 tools/build.py

Outputs: docs/thumbs/*.svg, docs/data/*.json, docs/icons.json, INDEX.md
"""
import json, glob, os, sys, urllib.request
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
}

def catlabel(c):
    return CAT_LABEL.get(c, c.replace("-", " ").replace("_", " ").title())

def build():
    os.makedirs(os.path.join(DOCS, "thumbs"), exist_ok=True)
    os.makedirs(os.path.join(DOCS, "data"), exist_ok=True)
    authors = author_map()
    icons = []
    nthumb = 0
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
        src = f"{cat}__{lib}"
        payload = []
        for i, it in enumerate(items):
            els = it.get("elements", it) if isinstance(it, dict) else it
            name = (it.get("name") or "").strip() if isinstance(it, dict) else ""
            iid = f"{src}__{i}"
            try:
                open(os.path.join(DOCS, "thumbs", iid + ".svg"), "w").write(render(els))
                nthumb += 1
            except Exception as ex:
                print("thumb fail", iid, ex)
                continue
            payload.append({"name": name, "elements": els})
            icons.append({"id": iid, "name": name, "lib": lib, "libName": libname,
                          "author": author, "cat": cat, "catLabel": catlabel(cat),
                          "src": src, "idx": i})
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
    print(f"built {len(icons)} icons, {nthumb} thumbs")
    print("by category:", dict(by))
    return len(icons)

if __name__ == "__main__":
    build()
