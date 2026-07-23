let ICONS = [];
let activeCat = "all";
let query = "";
const libCache = {};           // src -> [{name, elements}]

const grid = document.getElementById("grid");
const countEl = document.getElementById("count");
const toastEl = document.getElementById("toast");

init();

async function init() {
  ICONS = await (await fetch("icons.json")).json();
  buildCats();
  render();
  document.getElementById("q").addEventListener("input", (e) => {
    query = e.target.value.trim().toLowerCase();
    render();
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
    };
    wrap.appendChild(el);
  });
}

function match(icon) {
  if (activeCat !== "all" && icon.cat !== activeCat) return false;
  if (!query) return true;
  return (
    icon.name.toLowerCase().includes(query) ||
    icon.lib.toLowerCase().includes(query) ||
    icon.catLabel.toLowerCase().includes(query)
  );
}

function render() {
  const list = ICONS.filter(match);
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
