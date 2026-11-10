// Shared by all three pages: header and navigation, data loading, and small helpers.

const PAGES = [
  ["index.html", "Today"],
  ["browse.html", "Browse"],
  ["market.html", "Market"],
];

function renderChrome() {
  const here = location.pathname.split("/").pop() || "index.html";
  const links = PAGES.map(([href, label]) =>
    `<a href="${href}"${href === here ? ' aria-current="page"' : ""}>${label}</a>`).join("");
  const header = document.createElement("header");
  header.className = "masthead";
  header.innerHTML = `
    <div class="lights" aria-hidden="true">${"<i></i>".repeat(18)}</div>
    <div class="masthead-inner">
      <div class="moon" aria-hidden="true"></div>
      <p class="wordmark">Job Watcher</p>
      <p class="tagline">Investment and banking analyst openings at 25 firms, checked every day while the town sleeps.</p>
      <nav class="nav" aria-label="Pages">${links}</nav>
    </div>`;
  document.body.prepend(header);

  const snow = document.createElement("div");
  snow.className = "snow";
  snow.setAttribute("aria-hidden", "true");
  for (let i = 0; i < 28; i++) {
    const flake = document.createElement("i");
    flake.style.left = `${(i * 37) % 100}%`;
    flake.style.animationDuration = `${9 + (i % 7) * 2}s`;
    flake.style.animationDelay = `${-(i * 1.3)}s`;
    const size = 3 + (i % 3) * 2;
    flake.style.width = flake.style.height = `${size}px`;
    snow.append(flake);
  }
  document.body.prepend(snow);

  const footer = document.createElement("footer");
  footer.innerHTML = `Built from <a href="data/history.csv">history.csv</a> and <a href="data/status.json">status.json</a>. Every number on this site is calculated in your browser.`;
  document.body.append(footer);
}

// Parse CSV text (quoted fields, commas and newlines inside quotes) into objects.
function parseCSV(text) {
  const rows = [];
  let row = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; } else quoted = false;
      } else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
    else if (c !== "\r") field += c;
  }
  if (field !== "" || row.length) { row.push(field); rows.push(row); }
  const header = rows.shift() || [];
  return rows.filter(r => r.length === header.length)
    .map(r => Object.fromEntries(header.map((h, i) => [h, r[i]])));
}

// Load both data files. The service worker answers from its saved copy when offline.
async function loadData() {
  const [statusRes, historyRes] = await Promise.all([
    fetch("data/status.json", { cache: "no-store" }),
    fetch("data/history.csv", { cache: "no-store" }),
  ]);
  if (!statusRes.ok || !historyRes.ok) throw new Error("data files did not load");
  const status = await statusRes.json();
  const rows = parseCSV(await historyRes.text());
  for (const r of rows) {
    r.in_role = r.in_role === "true";
    r.first_run = r.first_run === "true";
  }
  return { status, rows, lastDay: status.run_time.slice(0, 10) };
}

const dayNumber = d => Math.round(Date.parse(d + "T00:00:00Z") / 86400000);
const daysBetween = (from, to) => dayNumber(to) - dayNumber(from);
const fmtDay = d => new Date(d + "T00:00:00Z").toLocaleDateString(undefined, { month: "short", day: "numeric", timeZone: "UTC" });
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const plural = (n, word) => `${n.toLocaleString()} ${word}${n === 1 ? "" : "s"}`;

// Shortlist: posting ids saved in this browser.
const Shortlist = {
  key: "job-watcher-shortlist",
  all() { try { return new Set(JSON.parse(localStorage.getItem(this.key) || "[]")); } catch { return new Set(); } },
  toggle(id) {
    const s = this.all();
    s.has(id) ? s.delete(id) : s.add(id);
    try { localStorage.setItem(this.key, JSON.stringify([...s])); } catch {}
    return s.has(id);
  },
};

function postingItem(r, { star = false, starred = false, apply = false, note = "" } = {}) {
  const starBtn = star
    ? `<button class="star" data-id="${esc(r.posting_id)}" aria-pressed="${starred}" aria-label="Save ${esc(r.title)} to shortlist" title="Save to shortlist">★</button>`
    : `<span></span>`;
  const role = r.in_role ? `<span class="tag">my role</span>` : "";
  const where = r.location ? `, ${esc(r.location)}` : "";
  return `<li>${starBtn}
    <span><a class="title" href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>${role}</span>
    ${apply ? `<a class="apply" href="${esc(r.url)}" target="_blank" rel="noopener">Apply</a>` : ""}
    <span class="meta">${esc(r.employer)}${where}${note ? ` · ${note}` : ""}</span></li>`;
}

function showError(err) {
  document.querySelector("main").innerHTML =
    `<div class="panel notice"><h2>The data did not load</h2><p>Check your connection and reload the page. Once the site has loaded while online, it also opens offline with the last data it saw.</p><p class="muted">${esc(err.message)}</p></div>`;
}

renderChrome();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
