// Browse page: open postings with a role switch, filters, title search, sort, apply links and a shortlist.
loadData().then(({ rows, lastDay }) => {
  const open = rows.filter(r => r.status === "open");
  for (const r of open) r.days_open = daysBetween(r.first_seen, lastDay);
  const $ = id => document.getElementById(id);
  const state = { view: "role", limit: 100 };
  let starred = Shortlist.all();

  const fillSelect = (el, values, anyLabel) => {
    const counts = new Map();
    for (const v of values) if (v) counts.set(v, (counts.get(v) || 0) + 1);
    const keep = el.value;
    el.innerHTML = `<option value="">${anyLabel}</option>` + [...counts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 300)
      .map(([v, n]) => `<option value="${esc(v)}">${esc(v)} (${n})</option>`).join("");
    if ([...el.options].some(o => o.value === keep)) el.value = keep;
  };

  const inView = r => state.view === "all" || (state.view === "role" && r.in_role) || (state.view === "starred" && starred.has(r.posting_id));

  function refreshOptions() {
    const pool = open.filter(inView);
    fillSelect($("employer"), pool.map(r => r.employer), "All employers");
    fillSelect($("location"), pool.map(r => r.location), "All locations");
  }

  function render() {
    const q = $("q").value.trim().toLowerCase();
    const employer = $("employer").value, location = $("location").value;
    const [lo, hi] = $("days").value ? $("days").value.split("-").map(Number) : [0, Infinity];
    const list = open.filter(r => inView(r)
      && (!q || r.title.toLowerCase().includes(q))
      && (!employer || r.employer === employer)
      && (!location || r.location === location)
      && r.days_open >= lo && r.days_open <= hi);
    const dir = $("sort").value === "new" ? -1 : 1;
    list.sort((a, b) => dir * a.first_seen.localeCompare(b.first_seen) || a.employer.localeCompare(b.employer) || a.title.localeCompare(b.title));

    $("resultline").textContent = `${plural(list.length, "open posting")} match.`;
    $("list").innerHTML = list.length
      ? list.slice(0, state.limit).map(r => postingItem(r, {
          star: true, starred: starred.has(r.posting_id), apply: true,
          note: r.first_run ? `open since before ${fmtDay(r.first_seen)}` : `first seen ${fmtDay(r.first_seen)}, ${plural(r.days_open, "day")} open`,
        })).join("")
      : `<li><span></span><span class="muted">${state.view === "starred" ? "Your shortlist is empty. Star a posting to save it here." : "No open postings match. Try clearing a filter."}</span></li>`;
    $("more").hidden = list.length <= state.limit;
    $("more").textContent = `Show more (${(list.length - state.limit).toLocaleString()} left)`;
  }

  const setView = view => {
    state.view = view; state.limit = 100;
    for (const [id, v] of [["show-role", "role"], ["show-all", "all"], ["show-starred", "starred"]])
      $(id).setAttribute("aria-pressed", String(v === view));
    refreshOptions(); render();
  };
  $("show-role").onclick = () => setView("role");
  $("show-all").onclick = () => setView("all");
  $("show-starred").onclick = () => setView("starred");
  for (const id of ["q", "employer", "location", "days", "sort"])
    $(id).addEventListener("input", () => { state.limit = 100; render(); });
  $("more").onclick = () => { state.limit += 200; render(); };
  $("list").addEventListener("click", e => {
    const btn = e.target.closest(".star");
    if (!btn) return;
    btn.setAttribute("aria-pressed", String(Shortlist.toggle(btn.dataset.id)));
    starred = Shortlist.all();
    if (state.view === "starred") render();
  });
  setView("role");
}).catch(showError);
