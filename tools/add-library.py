#!/usr/bin/env python3
"""Add one or more Excalidraw libraries to this repo in one go, then rebuild
the gallery.

Names come from https://libraries.excalidraw.com (the title under each library).

    # add libraries by name into a category folder, then rebuild everything:
    python3 tools/add-library.py --category misc "Robots" "Traffic signs" "Stars"

    # you can also pass the raw source path (author/file.excalidrawlib):
    python3 tools/add-library.py --category logos zanetworker/red-hat.excalidrawlib

    # just search the catalogue for a name (no download):
    python3 tools/add-library.py --search "kubernetes"

After adding, it renders thumbnails + data and regenerates docs/icons.json,
so the web gallery picks the new icons up immediately.
"""
import argparse, difflib, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, ".cache")
INDEX_URL = "https://raw.githubusercontent.com/excalidraw/excalidraw-libraries/main/libraries.json"
RAW_BASE = "https://raw.githubusercontent.com/excalidraw/excalidraw-libraries/main/libraries"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "add-library"})
    return urllib.request.urlopen(req, timeout=30).read()

def load_index(refresh=False):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, "libraries.json")
    if refresh or not os.path.exists(p):
        open(p, "wb").write(fetch(INDEX_URL))
    return json.load(open(p))

def resolve(name, libs):
    """name -> source path. Accepts an exact source path, exact name, or fuzzy name."""
    if "/" in name and name.endswith(".excalidrawlib"):
        return name
    byname = {l["name"].lower(): l for l in libs}
    key = name.lower().strip()
    if key in byname:
        return byname[key]["source"]
    subs = [n for n in byname if key in n]
    if len(subs) == 1:
        return byname[subs[0]]["source"]
    cand = subs or difflib.get_close_matches(key, list(byname), n=5, cutoff=0.5)
    if len(cand) == 1:
        return byname[cand[0]]["source"]
    if cand:
        print(f"  ! '{name}' is ambiguous. Candidates:")
        for c in cand:
            print(f"      {byname[c]['name']}   ({byname[c]['source']})")
        return None
    print(f"  ! '{name}' not found")
    return None

def add_one(source, category):
    base = source.split("/", 1)[1] if "/" in source else source
    dest_dir = os.path.join(ROOT, category)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, base)
    data = fetch(f"{RAW_BASE}/{source}")
    d = json.loads(data)
    assert d.get("type") == "excalidrawlib" or "libraryItems" in d or "library" in d, "not a library file"
    open(dest, "wb").write(data)
    n = len(d.get("libraryItems", d.get("library", [])))
    print(f"  + {category}/{base}  ({n} icons)")
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*", help="library name(s) or author/file.excalidrawlib source path(s)")
    ap.add_argument("--category", "-c", help="destination category folder (e.g. misc, ui, diagrams, gcp)")
    ap.add_argument("--search", "-s", help="search the catalogue for a term and list matches, then exit")
    ap.add_argument("--refresh", action="store_true", help="re-download the upstream library index")
    ap.add_argument("--no-build", action="store_true", help="download only, skip the rebuild")
    args = ap.parse_args()

    libs = load_index(refresh=args.refresh)

    if args.search:
        t = args.search.lower()
        hits = [l for l in libs if t in l["name"].lower() or t in l.get("description", "").lower()]
        print(f"{len(hits)} match(es) for '{args.search}':")
        for l in sorted(hits, key=lambda x: x["name"].lower()):
            print(f"  {l['name']:38} {l['source']}")
        return

    if not args.names:
        ap.error("provide library name(s), or use --search")
    if not args.category:
        ap.error("--category is required when adding (e.g. --category misc)")

    added = 0
    for name in args.names:
        src = resolve(name, libs)
        if not src:
            continue
        try:
            if add_one(src, args.category):
                added += 1
        except Exception as ex:
            print(f"  ! failed {name}: {ex}")

    print(f"\nadded {added}/{len(args.names)} librar{'y' if added == 1 else 'ies'}")
    if added and not args.no_build:
        print("rebuilding gallery...")
        sys.path.insert(0, HERE)
        import build, subprocess, shutil
        build.build()
        node = shutil.which("node")
        if node:
            print("rendering faithful thumbnails (Excalidraw exportToSvg)...")
            subprocess.run([node, os.path.join(HERE, "render-thumbs.mjs")], check=False)
        else:
            print("note: install node + `npm i puppeteer-core`, then run tools/render-thumbs.mjs")
        print("done. commit + push docs/ to publish.")

if __name__ == "__main__":
    main()
