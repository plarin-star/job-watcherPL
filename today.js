// Today page: what changed in the latest run.
// The four counts come first. The new and removed lists show postings in my role by default,
// a few at a time, so the page reads at a glance; one switch shows every posting, and the
// status of each board sits in a drop-down under a one-line summary.
const PREVIEW = 6;

loadData().then(({ status, rows, lastDay }) => {
  // ---- last run ----
  const when = new Date(status.run_time);
  const runline = document.getElementById("runline");
  runline.innerHTML =
    `Last run <b>${esc(when.toLocaleString(undefined, { weekday: "long", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }))}</b>` +
    ` · watching since ${fmtDay(status.first_run_date)}`;
  runline.title = status.run_time.replace("T", " ").replace("Z", " UTC");

  // ---- the lists ----
  // postings in my states come first, then by employer and title
  const order = (a, b) => ((myState(b.location) ? 1 : 0) - (myState(a.location) ? 1 : 0))
    || a.employer.localeCompare(b.employer) || a.title.localeCompare(b.title);
  const fresh = rows.filter(r => r.first_seen === lastDay && !r.first_run).sort(order);
  const gone = rows.filter(r => r.removed_date === lastDay).sort(order);
  const inRole = list => list.filter(r => r.in_role);
  const openInRole = rows.filter(r => r.status === "open" && r.in_role).length;

  // ---- the four counts, each with the part that is in my role ----
  const counts = [
    ["", status.days_with_success, "days with a successful run", `since ${fmtDay(status.first_run_date)}`],
    ["", status.open, "open postings", `${openInRole.toLocaleString()} in my role`],
    ["new", status.new_today, "new today", `${inRole(fresh).length.toLocaleString()} in my role`],
    ["gone", status.removed_today, "removed today", `${inRole(gone).length.toLocaleString()} in my role`],
  ];
  document.getElementById("counts").innerHTML = counts.map(([cls, n, label, sub]) =>
    `<div class="count ${cls}"><b>${Number(n).toLocaleString()}</b><span>${label}</span><small>${sub}</small></div>`).join("");

  const firstDay = status.days_with_success <= 1;
  const state = { mode: "role", open: { new: false, gone: false } };
  const lists = [
    { key: "new", label: "New postings", all: fresh,
      empty: firstDay ? "Nothing yet. On the first run every posting counts as already open; new ones show up from the second day." : "No new postings" },
    { key: "gone", label: "Removed postings", all: gone,
      empty: firstDay ? "Nothing yet. Removals show up from the second day of watching." : "No postings removed" },
  ];

  function render() {
    for (const L of lists) {
      const list = state.mode === "role" ? inRole(L.all) : L.all;
      const shown = state.open[L.key] ? list : list.slice(0, PREVIEW);
      document.getElementById(`${L.key}-h`).innerHTML = `${L.label} <span class="n">${list.length.toLocaleString()}</span>`;
      const where = state.mode === "role" ? " in my role" : "";
      document.getElementById(L.key).innerHTML = list.length
        ? shown.map(r => postingItem(r)).join("")
        : `<li class="plain"><span></span><span class="muted">${firstDay ? L.empty : `${L.empty}${where} in the latest run.`}</span></li>`;
      document.getElementById(L.key).classList.toggle("role-only", state.mode === "role");
      const more = document.getElementById(`${L.key}-more`);
      more.hidden = list.length <= PREVIEW;
      more.textContent = state.open[L.key] ? "Show fewer" : `Show all ${list.length.toLocaleString()}`;
    }
  }

  document.querySelectorAll(".switch button").forEach(btn => btn.addEventListener("click", () => {
    state.mode = btn.dataset.mode;
    state.open = { new: false, gone: false };
    document.querySelectorAll(".switch button").forEach(b => b.setAttribute("aria-pressed", b === btn));
    render();
  }));
  for (const L of lists) {
    document.getElementById(`${L.key}-more`).addEventListener("click", () => {
      state.open[L.key] = !state.open[L.key];
      render();
    });
  }
  render();

  // ---- job boards: one line, with the detail in a drop-down ----
  const names = Object.fromEntries(rows.map(r => [r.source, r.employer]));
  const nameOf = s => names[s.name] || s.name;
  const ok = status.sources.filter(s => s.ok);
  const failed = status.sources.filter(s => !s.ok);
  const read = ok.reduce((sum, s) => sum + s.count, 0);
  document.getElementById("src-h").innerHTML =
    `Job boards <span class="n">${ok.length} of ${status.sources.length} answered</span>`;
  document.getElementById("src-line").innerHTML = failed.length
    ? `<span class="bulb bad" aria-hidden="true"></span> ${failed.length} did not answer: <b>${failed.map(s => esc(nameOf(s))).join(", ")}</b>. ` +
      `Their postings stay open until the board answers again. The other ${ok.length} returned ${read.toLocaleString()} postings.`
    : `<span class="bulb ok" aria-hidden="true"></span> Every board answered and returned ${read.toLocaleString()} postings in total.`;
  document.getElementById("sources").innerHTML = status.sources.map(s =>
    `<li><span class="bulb ${s.ok ? "ok" : "bad"}" role="img" aria-label="${s.ok ? "answered" : "failed"}"></span>
     <span class="name">${esc(nameOf(s))}</span>
     <span class="n">${s.ok ? s.count.toLocaleString() : "failed"}</span></li>`).join("");
}).catch(showError);
