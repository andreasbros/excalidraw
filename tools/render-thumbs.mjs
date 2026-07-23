// Generate 100%-faithful thumbnails using Excalidraw's own exportToSvg,
// driven by a headless browser. Replaces the approximate Python renderer.
//
//   node tools/render-thumbs.mjs            # render all libraries
//   node tools/render-thumbs.mjs architecture   # only libs matching a substring
import puppeteer from "puppeteer-core";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(HERE);
const THUMBS = path.join(ROOT, "docs", "thumbs");
const SKIP = new Set(["docs", "catalogues", "tools", ".git", "node_modules"]);
const only = process.argv[2];
const CHROME = process.env.CHROME || "/usr/bin/google-chrome";
const EXV = "0.17.6";

fs.mkdirSync(THUMBS, { recursive: true });

const libs = [];
for (const cat of fs.readdirSync(ROOT)) {
  const cp = path.join(ROOT, cat);
  if (SKIP.has(cat) || !fs.statSync(cp).isDirectory()) continue;
  for (const f of fs.readdirSync(cp)) {
    if (f.endsWith(".excalidrawlib"))
      libs.push({ cat, lib: f.slice(0, -".excalidrawlib".length), file: path.join(cp, f) });
  }
}
const sel = only ? libs.filter((l) => `${l.cat}/${l.lib}`.includes(only)) : libs;
console.log(`rendering ${sel.length}/${libs.length} libraries via Excalidraw exportToSvg`);

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: "new", args: ["--no-sandbox", "--disable-gpu"],
});
const page = await browser.newPage();
const html = `<!doctype html><html><head><meta charset="utf-8">
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<link rel="stylesheet" href="https://unpkg.com/@excalidraw/excalidraw@${EXV}/dist/excalidraw.production.min.css"/>
<script src="https://unpkg.com/@excalidraw/excalidraw@${EXV}/dist/excalidraw.production.min.js"></script>
</head><body></body></html>`;
await page.setContent(html, { waitUntil: "networkidle0" });
await page.waitForFunction("window.ExcalidrawLib && window.ExcalidrawLib.exportToSvg", { timeout: 45000 });

let done = 0, fail = 0;
for (const { cat, lib, file } of sel) {
  const d = JSON.parse(fs.readFileSync(file, "utf8"));
  const items = d.libraryItems || d.library || [];
  const files = d.files || {};
  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    const els = it.elements || it;
    const itemFiles = {};
    for (const e of els) if (e.fileId && files[e.fileId]) itemFiles[e.fileId] = files[e.fileId];
    try {
      const svg = await page.evaluate(async (els, files) => {
        const el = await window.ExcalidrawLib.exportToSvg({
          elements: els,
          files,
          appState: { exportBackground: false, exportWithDarkMode: false },
          exportPadding: 6,
        });
        return el.outerHTML;
      }, els, itemFiles);
      // drop the external-font @font-face block so the SVG is self-contained
      const clean = svg.replace(/<style class="style-fonts">[\s\S]*?<\/style>/, "");
      fs.writeFileSync(path.join(THUMBS, `${cat}__${lib}__${i}.svg`), clean);
      done++;
    } catch (e) {
      fail++;
      console.log(`\n  fail ${cat}/${lib}#${i}: ${String(e).slice(0, 100)}`);
    }
  }
  process.stdout.write(`\r  ${done} rendered...`);
}
await browser.close();
console.log(`\ndone: ${done} rendered, ${fail} failed`);
