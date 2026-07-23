#!/usr/bin/env python3
"""Build image-based .excalidrawlib files from logo image files.

    python3 tools/make-brand-lib.py <src-dir>

<src-dir> holds <brand>/<variant>.(svg|png|jpg). One brands/<brand>.excalidrawlib
is written per brand, each item an Excalidraw image element with the logo embedded
as a data URL, plus a top-level files map. build.py knows how to render + copy these.
"""
import base64, glob, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "brands")

NAME_MAP = {
    "moodys": "Moody's",
    "moodys-analytics": "Moody's Analytics",
    "anthropic": "Anthropic",
    "claude": "Claude",
    "gemini": "Gemini",
    "openai": "OpenAI",
    "chatgpt": "ChatGPT",
    "hsbc-symbol-mono": "HSBC symbol (mono)",
    "hsbc-hexagon": "HSBC hexagon",
    "hsbc-wordmark": "HSBC wordmark",
    "nillion": "Nillion",
    "simzip": "sim.zip",
    "simzip-white": "sim.zip (white)",
    "simzip-mark": "sim.zip mark",
    "tele1": "TELE1",
}

def pretty(stem):
    if stem in NAME_MAP:
        return NAME_MAP[stem]
    return stem.replace("-", " ").replace("_", " ").strip().title()

def dims(path):
    if path.lower().endswith(".svg"):
        t = open(path, encoding="utf-8", errors="ignore").read(4000)
        m = re.search(r'viewBox\s*=\s*["\']\s*[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)', t)
        if m:
            return float(m.group(1)), float(m.group(2))
        w = re.search(r'\bwidth\s*=\s*["\']?([\d.]+)', t)
        h = re.search(r'\bheight\s*=\s*["\']?([\d.]+)', t)
        if w and h:
            return float(w.group(1)), float(h.group(1))
        return 100.0, 100.0
    from PIL import Image
    with Image.open(path) as im:
        return float(im.width), float(im.height)

def mime(path):
    p = path.lower()
    if p.endswith(".svg"):
        return "image/svg+xml"
    if p.endswith(".png"):
        return "image/png"
    if p.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    return "application/octet-stream"

def build_brand(brand, files):
    items, filemap = [], {}
    for path in sorted(files):
        stem = os.path.splitext(os.path.basename(path))[0]
        raw = open(path, "rb").read()
        b64 = base64.b64encode(raw).decode()
        fid = hashlib.sha1(raw).hexdigest()
        w, h = dims(path)
        scale = 110.0 / max(w, h)
        W, H = round(w * scale, 2), round(h * scale, 2)
        seed = int(fid[:8], 16)
        el = {
            "type": "image", "version": 1, "versionNonce": seed, "index": "a0",
            "id": fid[:16], "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
            "roughness": 0, "opacity": 100, "angle": 0, "x": 0, "y": 0,
            "strokeColor": "transparent", "backgroundColor": "transparent",
            "width": W, "height": H, "seed": seed, "groupIds": [], "frameId": None,
            "roundness": None, "boundElements": None, "updated": 1, "link": None,
            "locked": False, "status": "saved", "fileId": fid, "scale": [1, 1], "crop": None,
        }
        filemap[fid] = {
            "mimeType": mime(path), "id": fid,
            "dataURL": f"data:{mime(path)};base64,{b64}",
            "created": 1700000000000, "lastRetrieved": 1700000000000,
        }
        items.append({"id": fid[:16], "status": "unpublished", "created": 1700000000000,
                      "name": pretty(stem), "elements": [el]})
    lib = {"type": "excalidrawlib", "version": 2,
           "source": "andreasbros/excalidraw brand logos", "libraryItems": items, "files": filemap}
    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, f"{brand}.excalidrawlib")
    json.dump(lib, open(dest, "w"))
    print(f"  {os.path.relpath(dest, ROOT)}  ({len(items)} logos)")

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/brandlogos"
    brands = sorted(d for d in os.listdir(src) if os.path.isdir(os.path.join(src, d)))
    for b in brands:
        files = glob.glob(os.path.join(src, b, "*.svg")) + \
                glob.glob(os.path.join(src, b, "*.png")) + \
                glob.glob(os.path.join(src, b, "*.jpg"))
        if files:
            build_brand(b, files)

if __name__ == "__main__":
    main()
