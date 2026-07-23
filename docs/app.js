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
};

const grid = document.getElementById("grid");
const countEl = document.getElementById("count");
const toastEl = document.getElementById("toast");

init();

async function init() {
  ICONS = await (await fetch("icons.json")).json();
  for (const i of ICONS) {
    i.search = [i.name, i.name, SYN[i.cat] || "", i.lib.replace(/[-_]/g, " "), i.catLabel]
      .join(" ").toLowerCase();
  }
  fuse = new Fuse(ICONS, {
    keys: ["search"],
    threshold: 0.34,        // fuzzy tolerance
    ignoreLocation: true,   // match anywhere in the text
    minMatchCharLength: 2,
    useExtendedSearch: true, // space-separated terms are AND-ed
  });
  buildCats();
  render();
  document.getElementById("q").addEventListener("input", (e) => {
    query = e.target.value.trim();
    render();
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
      render();
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
  let list;
  if (!query) {
    list = ICONS;
  } else {
    // extended-search: AND each whitespace term, fuzzy per term
    const pattern = query.split(/\s+/).filter(Boolean).join(" ");
    list = fuse.search(pattern).map((r) => r.item);
  }
  if (activeCat !== "all") list = list.filter((i) => i.cat === activeCat);
  return list;
}

function render() {
  const list = currentList();
  countEl.textContent = `${list.length} icon${list.length === 1 ? "" : "s"}`;
  grid.innerHTML = "";
  if (!list.length) {
    grid.innerHTML = '<div class="empty">No icons match. Try a category, or a broader term.</div>';
    return;
  }
  const frag = document.createDocumentFragment();
  for (const icon of list) {
    const card = document.createElement("div");
    card.className = "card";
    card.title = icon.name || `${icon.lib} #${icon.idx}`;
    card.innerHTML =
      `<div class="thumb"><img loading="lazy" src="thumbs/${icon.id}.svg" alt=""></div>` +
      `<div class="name">${escapeHtml(icon.name || "-")}<span class="lib">${escapeHtml(icon.lib)}</span></div>`;
    card.onclick = () => copyIcon(icon, card);
    frag.appendChild(card);
  }
  grid.appendChild(frag);
}

async function loadLib(src) {
  if (!libCache[src]) libCache[src] = await (await fetch(`data/${src}.json`)).json();
  return libCache[src];
}

async function copyIcon(icon, card) {
  try {
    const lib = await loadLib(icon.src);
    const elements = lib[icon.idx].elements;
    const payload = JSON.stringify({ type: "excalidraw/clipboard", elements, files: {} });
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
