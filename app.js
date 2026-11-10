// Shared by all three pages: header and navigation, data loading, and small helpers.

const PAGES = [
  ["index.html", "Today"],
  ["browse.html", "Browse"],
  ["market.html", "Market"],
];

const BAT = `<svg class="bat" viewBox="0 0 48 26" aria-hidden="true"><path d="M24 9c1-2 1.500-4 3-6 .500 2 1.500 3 3 3.500C33 3 40 2 48 6c-4 0-6 2-7 6-2-2-4-2-6 0-1 4-5 9-11 12-6-3-10-8-11-12-2-2-4-2-6 0-1-4-3-6-7-6 8-4 15-3 18 .500 1.500-.500 2.500-1.500 3-3.500 1.500 2 2 4 3 6z"/></svg>`;

// A graveyard skyline for the bottom of the header: tombstones, crosses, a bare tree and an iron fence.
function skyline() {
  const stones = [[90, 34, 46], [210, 26, 38], [300, 40, 52], [520, 30, 40], [640, 44, 50], [860, 28, 42], [1010, 38, 48], [1120, 24, 36]]
    .map(([x, w, h], i) => `<path transform="rotate(${[-6, 5, -3, 7, -4, 3, -7, 5][i]} ${x} 100)" d="M${x - w / 2} 104V${100 - h + w / 2}a${w / 2} ${w / 2} 0 0 1 ${w} 0V104z"/>`).join("");
  const crosses = [[410, 50], [760, 44], [940, 36]]
    .map(([x, h]) => `<path d="M${x - 4} 104V${104 - h}h8V104zM${x - 14} ${104 - h + 12}h28v7h-28z"/>`).join("");
  let fence = "";
  for (let x = 0; x <= 1200; x += 20) fence += `<path d="M${x} 104V78l3-8 3 8v26z"/>`;
  return `<svg class="skyline" viewBox="0 0 1200 112" preserveAspectRatio="none" aria-hidden="true" fill="#0a0b10">
    <path d="M0 112V96c120-10 240 6 380-2s260-12 420-2 280 6 400-4v24z"/>
    ${stones}${crosses}
    <g opacity="0.9">${fence}<path d="M0 84h1200v3H0zM0 96h1200v3H0z"/></g>
    <g stroke="#0a0b10" stroke-width="5" fill="none" stroke-linecap="round">
      <path d="M152 104V52M152 76l-22-20M152 66l20-22M130 56l-10-16M172 44l4-16M152 52l-8-22M152 52l12-14"/>
    </g></svg>`;
}

function renderChrome() {
  const here = location.pathname.split("/").pop() || "index.html";
  const links = PAGES.map(([href, label]) =>
    `<a href="${href}"${href === here ? ' aria-current="page"' : ""}>${label}</a>`).join("");
  const header = document.createElement("header");
  header.innerHTML = `
    <div class="masthead">
      <div class="lights" aria-hidden="true">${"<i></i>".repeat(20)}</div>
      <div class="masthead-inner">
        <div class="moon" aria-hidden="true"></div>
        <p class="wordmark">Job Watcher</p>
        <p class="tagline">Investment and banking analyst openings at 25 firms, dug up fresh every morning.</p>
      </div>
      ${skyline()}
    </div>
    <div class="navbar"><nav class="nav" aria-label="Pages">${links}</nav></div>`;
  document.body.prepend(header);

  const snow = document.createElement("div");
  snow.className = "snow";
  snow.setAttribute("aria-hidden", "true");
  for (let i = 0; i < 26; i++) {
    const flake = document.createElement("i");
    flake.style.left = `${(i * 37) % 100}%`;
    flake.style.animationDuration = `${10 + (i % 7) * 2}s`;
    flake.style.animationDelay = `${-(i * 1.3)}s`;
    const size = 2 + (i % 3) * 2;
    flake.style.width = flake.style.height = `${size}px`;
    snow.append(flake);
  }
  document.body.prepend(snow);

  const web = document.createElement("div");
  web.innerHTML = `<svg class="web" viewBox="0 0 100 100" aria-hidden="true" fill="none" stroke="#8aa8a1" stroke-width="0.8">
    <path d="M100 100L0 100M100 100L100 0M100 100L8 62M100 100L30 30M100 100L62 8"/>
    <path d="M100 78Q90 80 84 93 77 88 78 100M100 56Q82 60 70 87 56 80 56 100M100 34Q74 40 55 81 34 72 34 100M100 12Q66 20 41 75 14 64 12 100"/></svg>`;
  document.body.append(web.firstChild);

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

// Application status for shortlisted postings, saved in this browser.
const STATUSES = [["applied", "Applied"], ["interviewing", "Interviewing"], ["rejected", "Rejected"]];
const Status = {
  key: "job-watcher-status",
  all() { try { return JSON.parse(localStorage.getItem(this.key) || "{}"); } catch { return {}; } },
  toggle(id, status) {
    const m = this.all();
    if (m[id] === status) delete m[id]; else m[id] = status;
    try { localStorage.setItem(this.key, JSON.stringify(m)); } catch {}
    return m[id] || "";
  },
};

function postingItem(r, { star = false, starred = false, apply = false, note = "", status = null } = {}) {
  const starBtn = star
    ? `<button class="star" data-id="${esc(r.posting_id)}" aria-pressed="${starred}" aria-label="Save ${esc(r.title)} to shortlist" title="Save to shortlist">★</button>`
    : `<span></span>`;
  const role = r.in_role ? `<span class="tag">my role</span>` : "";
  const where = r.location ? `, ${esc(r.location)}` : "";
  const tombs = status === null ? "" : `<span class="tombs" role="group" aria-label="Application status">${STATUSES.map(([key, label]) =>
    `<button type="button" class="tomb" data-id="${esc(r.posting_id)}" data-status="${key}" aria-pressed="${status === key}">${label}</button>`).join("")}</span>`;
  return `<li>${starBtn}
    <span><a class="title" href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>${role}</span>
    ${apply ? `<a class="apply" href="${esc(r.url)}" target="_blank" rel="noopener">Apply</a>` : ""}
    <span class="meta">${BAT}<span>${esc(r.employer)}${where}${note ? ` · ${note}` : ""}</span></span>${tombs}</li>`;
}

function showError(err) {
  document.querySelector("main").innerHTML =
    `<div class="panel notice"><h2>The data did not load</h2><p>Check your connection and reload the page. Once the site has loaded while online, it also opens offline with the last data it saw.</p><p class="muted">${esc(err.message)}</p></div>`;
}

renderChrome();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
