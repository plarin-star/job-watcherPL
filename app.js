// Shared by all three pages: header and navigation, data loading, and small helpers.

const PAGES = [
  ["index.html", "Today"],
  ["browse.html", "Browse"],
  ["market.html", "Market"],
];

const BAT = `<svg class="bat" viewBox="0 0 48 26" aria-hidden="true"><path d="M24 9c1-2 1.500-4 3-6 .500 2 1.500 3 3 3.500C33 3 40 2 48 6c-4 0-6 2-7 6-2-2-4-2-6 0-1 4-5 9-11 12-6-3-10-8-11-12-2-2-4-2-6 0-1-4-3-6-7-6 8-4 15-3 18 .500 1.500-.500 2.500-1.500 3-3.500 1.500 2 2 4 3 6z"/></svg>`;

// An original scarecrow for the header: crooked on its pole, with a pumpkin lantern and a holly wreath.
const SCARECROW = `<svg class="scarecrow" viewBox="0 0 200 300" aria-hidden="true">
  <defs><radialGradient id="glow"><stop offset="0" stop-color="#ffd76a" stop-opacity=".75"/><stop offset="1" stop-color="#ffd76a" stop-opacity="0"/></radialGradient></defs>
  <g transform="rotate(-6 100 290)">
    <path d="M100 300V96" stroke="#2e2118" stroke-width="8" stroke-linecap="round"/>
    <path d="M26 124L174 108" stroke="#2e2118" stroke-width="7" stroke-linecap="round"/>
    <g stroke="#d8c370" stroke-width="2.2" stroke-linecap="round">
      <path d="M30 122l-14-7M29 127l-16 1M30 132l-13 8M171 106l13-9M172 111l16-2M172 116l14 6"/>
      <path d="M72 214l-4 14M82 208l-1 15M96 218l-2 14M110 216l3 14M124 206l3 15M134 212l5 13"/>
      <path d="M90 100l-6 8M100 102v9M110 100l6 8"/>
    </g>
    <path d="M70 116L132 110 142 214 122 204 104 222 88 206 62 218z" fill="#2f4a47"/>
    <path d="M70 116L28 121 27 137 72 141zM132 110L172 105 175 121 134 136z" fill="#263c3a"/>
    <path d="M80 150l22-3 3 22-22 3z" fill="#5b3a7a"/><path d="M112 176l18-4 4 18-18 4z" fill="#7a5a2a"/>
    <path d="M80 150l22-3 3 22-22 3zM112 176l18-4 4 18-18 4zM101 114l3 104" fill="none" stroke="#f5f2cb" stroke-width="1.4" stroke-dasharray="4 3"/>
    <circle cx="103" cy="132" r="3" fill="#f5f2cb"/><circle cx="104" cy="196" r="3" fill="#f5f2cb"/>
    <path d="M78 76c0-17 10-27 23-27s23 10 23 27-9 28-23 28-23-11-23-28z" fill="#c9b98a"/>
    <path d="M84 98c6 5 28 5 34 0l3 8c-10 5-30 5-40 0z" fill="#8b7a4e"/>
    <circle cx="91" cy="74" r="5.500" fill="#2f4a47"/><circle cx="111" cy="72" r="4" fill="#5b3a7a"/>
    <path d="M89 72l4 4M93 72l-4 4M109.500 70.500l3 3M112.500 70.500l-3 3" stroke="#f5f2cb" stroke-width="1"/>
    <path d="M100 78l5 8h-9z" fill="#e08a2c"/>
    <path d="M90 91l5-3 4 4 5-4 4 3 4-3" fill="none" stroke="#4a3b22" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <ellipse cx="100" cy="55" rx="38" ry="7.500" fill="#1b1d28"/>
    <path d="M76 55C84 26 100 8 128 4c-10 14-8 32-4 51z" fill="#241a33"/>
    <path d="M77 51c14 5 32 5 46 0l1 6c-15 5-33 5-48 0z" fill="#e0485a"/>
    <path d="M30 136v34" stroke="#d8c370" stroke-width="1.500"/>
    <circle cx="30" cy="196" r="44" fill="url(#glow)"/>
    <path d="M27 172c1-5 5-7 8-6-2 2-2 4-2 7z" fill="#3f7a55"/>
    <ellipse cx="30" cy="196" rx="22" ry="19" fill="#e08a2c"/>
    <path d="M30 177c-9 6-9 32 0 38M30 177c9 6 9 32 0 38M18 181c-7 8-7 22 0 30M42 181c7 8 7 22 0 30" fill="none" stroke="#b5651d" stroke-width="1.500"/>
    <path d="M19 190l6-7 5 7zM31 190l5-7 6 7zM17 199l5 4 4-4 4 4 4-4 4 4 5-4c-2 9-7 12-13 12s-11-3-13-12z" fill="#ffe9a3"/>
    <path d="M168 120v18" stroke="#d8c370" stroke-width="1.500"/>
    <circle cx="168" cy="162" r="20" fill="none" stroke="#2f6b49" stroke-width="11"/>
    <circle cx="168" cy="162" r="20" fill="none" stroke="#5fb37c" stroke-width="4" stroke-dasharray="3 6"/>
    <g fill="#e0485a"><circle cx="152" cy="150" r="2.800"/><circle cx="186" cy="156" r="2.800"/><circle cx="158" cy="179" r="2.800"/><circle cx="181" cy="176" r="2.800"/><circle cx="168" cy="141" r="2.800"/>
      <path d="M168 181l-11-6v13zM168 181l11-6v13zM165 183l-3 12 6-4 6 4-3-12z"/></g>
  </g></svg>`;

// A snowy hillside for the bottom of the header: crooked pines, one with a star, and a few bats.
function skyline() {
  const pine = (x, h, lean, star) => {
    const w = h * 0.42, top = 96 - h;
    const tiers = [0, 1, 2].map(i => {
      const y0 = top + (h * 0.26) * i, y1 = y0 + h * 0.4, half = w * (0.45 + i * 0.27);
      return `M${x} ${y0}L${x + half} ${y1}Q${x} ${y1 - 5} ${x - half} ${y1}Z`;
    }).join("");
    return `<g transform="rotate(${lean} ${x} 96)"><path d="M${x - 2} 100V${96 - h * 0.2}h4V100z" fill="#0b1512"/><path d="${tiers}" fill="#12261f"/>` +
      `<path d="${[0, 1, 2].map(i => { const y1 = top + (h * 0.26) * i + h * 0.4, half = w * (0.45 + i * 0.27); return `M${x - half} ${y1}Q${x} ${y1 - 5} ${x + half} ${y1}`; }).join("")}" fill="none" stroke="#e8ecf6" stroke-width="2.200" stroke-linecap="round" opacity=".8"/>` +
      (star ? `<path transform="translate(${x} ${top - 3})" d="M0-9l2.600 6 6.400.600-4.800 4.300 1.400 6.300L0 5l-5.600 3.200 1.400-6.300-4.800-4.300 6.400-.600z" fill="#f6dc94"/>` : "") + `</g>`;
  };
  const pines = [[60, 56, -5], [150, 78, 4, 1], [250, 44, -8], [430, 60, 6], [560, 40, -4], [700, 66, 5], [1130, 58, -6], [1180, 40, 7]]
    .map(p => pine(...p)).join("");
  const bat = (x, y, s) => `<path transform="translate(${x} ${y}) scale(${s})" d="M0 0c2-3 5-4 8-3-1 1-1 2-1 3 2-2 5-2 7 0 0-1 0-2-1-3 3-1 6 0 8 3-3 0-5 1-6 3-2-2-4-2-5 0-1-2-3-2-5 0-1-2-3-3-5-3z" fill="#0a0c18"/>`;
  return `<svg class="skyline" viewBox="0 0 1200 120" preserveAspectRatio="none" aria-hidden="true">
    ${bat(610, 14, 1.100)}${bat(690, 30, 0.800)}${bat(520, 34, 0.700)}
    <path d="M0 120V84c160-22 300-6 460-12s300-20 440-6 220 10 300-4v58z" fill="#1c2340"/>
    ${pines}
    <path d="M0 120V100c140-14 260 4 400-4s280-16 430-4 250 8 370-6v34z" fill="#dfe5f3"/>
    <path d="M0 120v-8c200-10 380 6 600-2s400-6 600 0v10z" fill="#0c0f1c"/></svg>`;
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
        <p class="tagline">Investment and banking analyst openings at 25 firms, unwrapped fresh every morning.</p>
      </div>
      ${SCARECROW}
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
  web.innerHTML = `<svg class="web" viewBox="0 0 100 100" aria-hidden="true" fill="none" stroke="#aab2c8" stroke-width="0.8">
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
