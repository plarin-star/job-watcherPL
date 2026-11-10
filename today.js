// Today page: last run time, source status, the four counts, and the new and removed lists.
loadData().then(({ status, rows, lastDay }) => {
  const when = new Date(status.run_time);
  document.getElementById("runline").textContent =
    `Last run: ${when.toLocaleString(undefined, { dateStyle: "full", timeStyle: "short" })} ` +
    `(${status.run_time.replace("T", " ").replace("Z", " UTC")}). Watching since ${fmtDay(status.first_run_date)}.`;

  const counts = [
    ["", status.days_with_success, "days with a successful run"],
    ["", status.open, "open postings"],
    ["new", status.new_today, "new today"],
    ["gone", status.removed_today, "removed today"],
  ];
  document.getElementById("counts").innerHTML = counts.map(([cls, n, label]) =>
    `<div class="count ${cls}"><b>${Number(n).toLocaleString()}</b><span>${label}</span></div>`).join("");

  const byRole = (a, b) => (b.in_role - a.in_role) || a.employer.localeCompare(b.employer) || a.title.localeCompare(b.title);
  const fresh = rows.filter(r => r.first_seen === lastDay && !r.first_run).sort(byRole);
  const gone = rows.filter(r => r.removed_date === lastDay).sort(byRole);
  const fill = (id, headId, label, list, empty) => {
    document.getElementById(headId).textContent = `${label} (${list.length.toLocaleString()})`;
    const shown = list.slice(0, 200).map(r => postingItem(r)).join("");
    const rest = list.length > 200 ? `<li class="plain"><span></span><span class="muted">…and ${list.length - 200} more. See Browse for everything open.</span></li>` : "";
    document.getElementById(id).innerHTML = list.length ? shown + rest : `<li class="plain"><span></span><span class="muted">${empty}</span></li>`;
  };
  const firstDay = status.days_with_success <= 1;
  fill("new", "new-h", "New postings", fresh, firstDay
    ? "Nothing yet. Today was the first run, so every posting counts as already open. New ones show up from tomorrow."
    : "No new postings in the latest run.");
  fill("gone", "gone-h", "Removed postings", gone, firstDay
    ? "Nothing yet. Removals show up from the second day of watching."
    : "No postings were removed in the latest run.");

  const ok = status.sources.filter(s => s.ok).length;
  document.getElementById("src-h").textContent = `Sources (${ok} of ${status.sources.length} answered)`;
  const names = Object.fromEntries(rows.map(r => [r.source, r.employer]));
  document.getElementById("sources").innerHTML = status.sources.map(s =>
    `<li><span class="bulb ${s.ok ? "ok" : "bad"}" role="img" aria-label="${s.ok ? "answered" : "failed"}"></span>
     <span class="name">${esc(names[s.name] || s.name)}</span>
     <span class="n">${s.ok ? s.count.toLocaleString() : "failed"}</span></li>`).join("");
}).catch(showError);
