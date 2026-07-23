let ICONS = [];
let activeCat = "all";
let query = "";
let fuse = null;
const libCache = {};           // src -> [{name, elements}]

// Provider / domain synonyms so "google cloud run" finds the GCP "Cloud Run" icon,
// "amazon s3" finds AWS, etc. Folded into each icon's searchable text.
const SYN = {
  gcp: "google gcp google-cloud gce gke",
  aws: "amazon aws",
  azure: "microsoft azure ms",
  oracle: "oracle oci oracle-cloud",
  "cloud-k8s-devops": "cloud kubernetes k8s devops",
  network: "network networking infrastructure",
  architecture: "architecture system-design software",
  logos: "logo brand",
  diagrams: "diagram chart graph flow",
  ui: "ui wireframe mockup web app",
  misc: "misc fun",
  brands: "brand logo company",
};

const grid = document.getElementById("grid");
const countEl = document.getElementById("count");
const toastEl = document.getElementById("toast");

init();

async function init() {
  ICONS = await (await fetch("icons.json")).json();
  for (const i of ICONS) {
    // searchable text: name (weighted x2), author, library name, filename,
    // category (slug + label) and provider synonyms
    i.search = [i.name, i.name, i.author || "", i.libName || "",
                i.lib.replace(/[-_]/g, " "), i.cat, i.catLabel, SYN[i.cat] || ""]
      .join(" ").toLowerCase();
  }
  fuse = new Fuse(ICONS, {
    keys: ["search"],
    threshold: 0.4,         // recall; the ranker below handles precision
    ignoreLocation: true,   // match anywhere in the text
    minMatchCharLength: 2,
    includeScore: true,     // used to rank fuzzy matches below exact/phrase ones
  });
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";
  const saved = loadState();
  query = (saved && saved.query) || "";
  activeCat = (saved && saved.cat) || "all";
  const qInput = document.getElementById("q");
  qInput.value = query;
  buildCats();
  if (saved && (saved.scrollY || saved.rendered)) restoreRender(saved);
  else renderFresh();

  let searchTimer;
  qInput.addEventListener("input", (e) => {
    query = e.target.value.trim();
    clearTimeout(searchTimer);
    searchTimer = setTimeout(renderFresh, 130); // debounce so typing stays smooth
  });
  // remember position so browser Back / reload returns to the same spot
  addEventListener("pagehide", saveState);
  addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") saveState();
  });
  // Mobile: toggle the collapsible filters panel
  const ft = document.getElementById("filterToggle");
  const filters = document.getElementById("filters");
  ft.addEventListener("click", () => {
    const open = filters.classList.toggle("open");
    ft.classList.toggle("open", open);
    ft.setAttribute("aria-expanded", String(open));
  });
}

function buildCats() {
  const cats = ["all", ...new Set(ICONS.map((i) => i.cat))];
  const labels = { all: "All" };
  ICONS.forEach((i) => (labels[i.cat] = i.catLabel));
  const wrap = document.getElementById("cats");
  wrap.innerHTML = "";
  cats.forEach((c) => {
    const n = c === "all" ? ICONS.length : ICONS.filter((i) => i.cat === c).length;
    const el = document.createElement("span");
    el.className = "chip" + (c === activeCat ? " active" : "");
    el.textContent = `${labels[c]} (${n})`;
    el.onclick = () => {
      activeCat = c;
      document.querySelectorAll(".chip").forEach((x) => x.classList.remove("active"));
      el.classList.add("active");
      renderFresh();
      // collapse the panel on mobile after choosing (no effect on desktop)
      const filters = document.getElementById("filters");
      const ft = document.getElementById("filterToggle");
      filters.classList.remove("open");
      ft.classList.remove("open");
      ft.setAttribute("aria-expanded", "false");
    };
    wrap.appendChild(el);
  });
}

function currentList() {
  let list = query ? searchRanked(query) : ICONS;
  if (activeCat !== "all") list = list.filter((i) => i.cat === activeCat);
  return list;
}

// Fuzzy but graded: exact name > name prefix/phrase > all words in name >
// all words anywhere (AND) > single word / fuzzy. Matches name, author,
// library name, filename, category and synonyms.
function searchRanked(raw) {
  const q = raw.toLowerCase().trim();
  const tokens = q.split(/\s+/).filter(Boolean);
  const cand = new Map(); // id -> { i, fz: best per-token fuzzy score }
  for (const t of tokens) {
    for (const r of fuse.search(t)) {
      const fz = r.score ?? 1;
      const cur = cand.get(r.item.id);
      if (!cur || fz < cur.fz) cand.set(r.item.id, { i: r.item, fz });
    }
  }
  // substring safety net for the whole phrase (catches anything fuzzy missed)
  for (const i of ICONS) {
    if (!cand.has(i.id) && i.search.includes(q)) cand.set(i.id, { i, fz: 0.5 });
  }
  const scored = [];
  for (const { i, fz } of cand.values()) {
    const name = i.name.toLowerCase();
    let s = (1 - fz) * 20;                 // fuzzy quality
    if (name === q) s += 1000;             // exact name -> very top
    else if (name.startsWith(q)) s += 600;
    else if (name.includes(q)) s += 400;   // phrase in name
    if ((i.libName || "").toLowerCase().includes(q)) s += 180; // query is the library's name
    let nameHits = 0, anyHits = 0;
    for (const t of tokens) {
      const inName = name.includes(t);
      if (inName) nameHits++;
      if (inName || i.search.includes(t)) anyHits++;
    }
    // name words are worth much more than synonym/author/category words
    s += nameHits * 120 + (anyHits - nameHits) * 15;
    if (nameHits === tokens.length) s += 200;      // all words in the name
    else if (anyHits === tokens.length) s += 80;   // all words matched somewhere (AND)
    scored.push({ i, s });
  }
  scored.sort((a, b) => b.s - a.s);
  return scored.map((x) => x.i);
}

// ---- Chunked / infinite-scroll rendering (keeps the DOM small for 1500+ icons) ----
const CHUNK = 100;
let renderList = [];
let renderCursor = 0;
let sentinel = null;
const io = new IntersectionObserver(
  (entries) => { if (entries.some((e) => e.isIntersecting)) appendChunk(); },
  { rootMargin: "800px 0px" } // preload before hitting the bottom; viewport-based, so resolution-independent
);

function makeCard(icon) {
  const card = document.createElement("div");
  card.className = "card";
  const libName = icon.libName || icon.lib.replace(/[-_]/g, " ");
  card.title = icon.name ? `${icon.name}  ·  ${libName}` : libName;
  // show icon name (primary) + library name (secondary, muted); if unnamed, show the library name
  const meta = icon.name
    ? `<div class="name">${escapeHtml(icon.name)}</div><div class="lib">${escapeHtml(libName)}</div>`
    : `<div class="name">${escapeHtml(libName)}</div>`;
  card.innerHTML =
    `<div class="thumb"><img loading="lazy" src="thumbs/${icon.id}.svg" alt=""></div>` +
    `<div class="meta">${meta}</div>`;
  card.onclick = () => copyIcon(icon, card);
  return card;
}

function appendChunk() {
  if (sentinel) { io.unobserve(sentinel); sentinel.remove(); sentinel = null; }
  const end = Math.min(renderCursor + CHUNK, renderList.length);
  const frag = document.createDocumentFragment();
  for (let i = renderCursor; i < end; i++) frag.appendChild(makeCard(renderList[i]));
  grid.appendChild(frag);
  renderCursor = end;
  if (renderCursor < renderList.length) {
    sentinel = document.createElement("div");
    sentinel.style.cssText = "grid-column:1/-1;height:1px";
    grid.appendChild(sentinel);
    io.observe(sentinel); // if still on screen (large display), it fires again and loads more
  }
}

function resetGrid() {
  if (sentinel) { io.unobserve(sentinel); sentinel = null; }
  renderList = currentList();
  countEl.textContent = `${renderList.length} icon${renderList.length === 1 ? "" : "s"}`;
  grid.innerHTML = "";
  renderCursor = 0;
  if (!renderList.length) {
    grid.innerHTML = '<div class="empty">No icons match. Try a category, or a broader term.</div>';
    return false;
  }
  return true;
}

function renderFresh() {
  if (resetGrid()) appendChunk();
  scrollTo(0, 0); // new result set -> back to top
}

function restoreRender(saved) {
  if (!resetGrid()) return;
  const target = Math.max(CHUNK, saved.rendered || CHUNK);
  do { appendChunk(); } while (renderCursor < renderList.length && renderCursor < target);
  requestAnimationFrame(() => scrollTo(0, saved.scrollY || 0));
}

// ---- Session state so Back / reload restores query, category and scroll ----
function saveState() {
  try {
    sessionStorage.setItem("gallery", JSON.stringify({
      query, cat: activeCat, scrollY: window.scrollY, rendered: renderCursor,
    }));
  } catch (e) {}
}
function loadState() {
  try { return JSON.parse(sessionStorage.getItem("gallery")); } catch (e) { return null; }
}

async function loadLib(src) {
  if (!libCache[src]) libCache[src] = await (await fetch(`data/${src}.json`)).json();
  return libCache[src];
}

async function copyIcon(icon, card) {
  try {
    const lib = await loadLib(icon.src);
    const item = lib[icon.idx];
    const payload = JSON.stringify({
      type: "excalidraw/clipboard",
      elements: item.elements,
      files: item.files || {}, // image-based icons (brand logos) carry their file data
    });
    await navigator.clipboard.writeText(payload);
    card.classList.add("copied");
    setTimeout(() => card.classList.remove("copied"), 700);
    toast("Copied ✓  Paste into Excalidraw (Ctrl/Cmd+V)");
  } catch (e) {
    toast("Copy failed - your browser blocked clipboard access");
  }
}

let toastTimer;
function toast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove("show"), 1800);
}

function escapeHtml(s) {
  return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}
