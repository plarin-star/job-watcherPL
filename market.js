// Market page: six findings, every number calculated here from data/history.csv.
loadData().then(({ status, rows, lastDay }) => {
  const firstDay = status.first_run_date;
  const days = [];
  for (let d = dayNumber(firstDay); d <= dayNumber(lastDay); d++) days.push(new Date(d * 86400000).toISOString().slice(0, 10));
  const labels = days.map(fmtDay);
  const countBy = (list, key) => list.reduce((m, r) => m.set(key(r), (m.get(key(r)) || 0) + 1), new Map());
  const top = (map, n) => [...map.entries()].filter(([k]) => k).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, n)
    .map(([label, value]) => ({ label, value }));
  const open = rows.filter(r => r.status === "open");
  const tracked = rows.filter(r => !r.first_run);          // start date known
  const early = `The tool started watching on ${fmtDay(firstDay)}, so this section fills in as the history grows.`;

  document.getElementById("market-lede").textContent =
    `${plural(rows.length, "posting")} seen across ${plural(days.length, "day")} of watching, ` +
    `${fmtDay(firstDay)} to ${fmtDay(lastDay)}. Postings that were already open on a firm's first day have no known start date and are left out where noted.`;

  const findings = document.getElementById("findings");
  function section(heading, paragraph, draw) {
    const s = document.createElement("section");
    s.className = "panel finding";
    s.innerHTML = `<h2>${esc(heading)}</h2><p>${esc(paragraph)}</p>`;
    const host = document.createElement("div");
    s.append(host);
    findings.append(s);
    draw(host);
  }

  // 1. New postings per day (first-run postings left out), all postings and my role.
  const newAll = countBy(tracked, r => r.first_seen), newRole = countBy(tracked.filter(r => r.in_role), r => r.first_seen);
  const allVals = days.map(d => newAll.get(d) || 0), roleVals = days.map(d => newRole.get(d) || 0);
  const totalNew = allVals.reduce((a, b) => a + b, 0), totalRole = roleVals.reduce((a, b) => a + b, 0);
  section(
    totalNew ? `${plural(totalNew, "new posting")} appeared, ${totalRole.toLocaleString()} of them in my role` : "No new postings have appeared yet",
    totalNew
      ? `Postings first seen on each day. ${fmtDay(firstDay)} is zero by definition: everything listed on the first day was already open, so its start date is unknown. ` +
        `The busiest day was ${labels[allVals.indexOf(Math.max(...allVals))]} with ${Math.max(...allVals).toLocaleString()} new postings. ` +
        `My role is about ${Math.round((totalRole / totalNew) * 100) || "<1"}% of the flow, so it gets its own scale on the right.`
      : `New postings are counted from the day after a firm is first watched. ${early}`,
    host => {
      host.className = "pair";
      const half = (title, values, color) => {
        const box = document.createElement("div");
        box.innerHTML = `<h3 class="chart-title">${title}</h3>`;
        host.append(box);
        barsV(box, days.map((d, i) => ({ label: labels[i], value: values[i] })), { color, W: 380, H: 230, unit: " new", table: false });
      };
      half("All postings", allVals, COLOR.all);
      half("My role", roleVals, COLOR.role);
      const tbl = document.createElement("div");
      tbl.className = "pair-wide";
      host.append(tbl);
      dataTable(tbl, ["Day", "All postings", "My role"], days.map((d, i) => [labels[i], allVals[i], roleVals[i]]));
    });

  // 2. Removed postings per day.
  const gone = countBy(rows.filter(r => r.removed_date), r => r.removed_date);
  const goneVals = days.map(d => gone.get(d) || 0), totalGone = goneVals.reduce((a, b) => a + b, 0);
  section(
    totalGone ? `${plural(totalGone, "posting")} came down` : "No postings have been removed yet",
    totalGone
      ? `A posting counts as removed on the first day its firm's board answers without it, so ${fmtDay(firstDay)} has none. The most removals came on ${labels[goneVals.indexOf(Math.max(...goneVals))]}.`
      : `A posting counts as removed on the first day its firm's board answers without it. ${early}`,
    host => barsV(host, days.map((d, i) => ({ label: labels[i], value: goneVals[i] })), { unit: " removed", tableHead: ["Day", "Removed"] }));

  // 3. Open postings per employer as of the last run.
  const perEmployer = top(countBy(open, r => r.employer), 100);
  section(
    perEmployer.length ? `${perEmployer[0].label} has the most open postings, ${perEmployer[0].value.toLocaleString()}` : "No open postings",
    `Open postings at each firm as of the last run on ${fmtDay(lastDay)}, ${open.length.toLocaleString()} in total across ${perEmployer.length} firms. This counts every posting on the board, not only my role.`,
    host => barsH(host, perEmployer, { unit: " open", tableHead: ["Employer", "Open postings"] }));

  // 4. Days open: removed, non-first-run postings; removed date minus first-seen date; median.
  const spans = tracked.filter(r => r.status === "removed" && r.removed_date).map(r => daysBetween(r.first_seen, r.removed_date)).sort((a, b) => a - b);
  const median = spans.length ? (spans.length % 2 ? spans[(spans.length - 1) / 2] : (spans[spans.length / 2 - 1] + spans[spans.length / 2]) / 2) : null;
  section(
    spans.length ? `A posting stays up for a median of ${plural(median, "day")}` : "Not enough history yet to measure how long postings stay up",
    spans.length
      ? `Based on ${plural(spans.length, "posting")} that the tool saw both appear and disappear: the removed date minus the first-seen date. The chart shows how many postings lasted each number of days.`
      : `This needs postings that the tool saw both appear and disappear. ${early}`,
    host => {
      const lo = spans.length ? spans[0] : 1, max = spans.length ? spans[spans.length - 1] : 7, hist = countBy(spans, d => d);
      const items = Array.from({ length: max - lo + 1 }, (_, i) => ({ label: plural(lo + i, "day"), value: hist.get(lo + i) || 0 }));
      barsV(host, items, { unit: " postings", tableHead: ["Days open", "Postings"] });
    });

  // 5. Share removed within seven days: non-first-run postings first seen at least 7 days before the last run.
  const eligible = tracked.filter(r => daysBetween(r.first_seen, lastDay) >= 7);
  const quick = eligible.filter(r => r.status === "removed" && r.removed_date && daysBetween(r.first_seen, r.removed_date) <= 7);
  const share = eligible.length ? quick.length / eligible.length : null;
  const firstNew = tracked.map(r => r.first_seen).sort()[0];
  const readyDay = firstNew ? new Date((dayNumber(firstNew) + 7) * 86400000).toISOString().slice(0, 10) : null;
  section(
    share === null ? "Not enough history yet to say how many postings close within a week"
      : `${Math.round(share * 100)}% of postings came down within seven days`,
    share === null
      ? `This counts only postings first seen at least seven days before the last run, so each one has had a full week to close. ` +
        (readyDay ? `The earliest new postings were first seen on ${fmtDay(firstNew)}, so they reach a full week at the ${fmtDay(readyDay)} run and this section fills in by itself from then.` : early)
      : `Of ${plural(eligible.length, "posting")} first seen at least seven days before the last run, ${quick.length.toLocaleString()} were removed seven days or less after they first appeared. ` +
        `First-run postings are left out because their start date is unknown.`,
    host => share === null
      ? (host.innerHTML = `<div class="chart-empty">Waiting for postings with a full week of history${readyDay ? ` · first data after the ${fmtDay(readyDay)} run` : ""}</div>`)
      : splitBar(host, [
          { label: "Removed within 7 days", value: quick.length, color: COLOR.role },
          { label: "Still up after 7 days", value: eligible.length - quick.length, color: COLOR.rest },
        ]));

  // 6. Top locations among open postings.
  const notPlace = loc => /^\d+ Locations?$/i.test(loc);        // "2 Locations" is a count, not a place
  const multi = open.filter(r => notPlace(r.location)).length;
  const places = top(countBy(open.filter(r => !notPlace(r.location)), r => r.location), 12);
  const city = loc => loc.split(",")[0].trim().toLowerCase();
  const cities = top(countBy(open.filter(r => r.location && !notPlace(r.location)), r => city(r.location)), 1)[0];
  const spellings = cities ? new Set(open.filter(r => city(r.location) === cities.label).map(r => r.location)).size : 0;
  const cityName = cities ? cities.label.replace(/\b[a-z]/g, c => c.toUpperCase()) : "";
  section(
    cities ? `${cityName} is the top city, with ${plural(cities.value, "open posting")}` : "No locations to show",
    `The twelve most common locations among the ${open.length.toLocaleString()} open postings, written exactly as each firm writes them. ` +
    (cities ? `Firms spell the same city differently, so ${cityName} appears ${spellings} ways; the headline adds those together. ` : "") +
    (multi ? `${plural(multi, "posting")} list only a count such as "2 Locations" instead of a place, and are left out.` : ""),
    host => barsH(host, places, { unit: " open", tableHead: ["Location", "Open postings"] }));
}).catch(showError);
