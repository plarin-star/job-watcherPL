// Small SVG charts drawn by hand: vertical bars, horizontal bars, two-series lines, and a split bar.
// Every chart gets a hover tooltip and a "View the numbers" table underneath.

const COLOR = { all: "#8a76d6", role: "#e0485a", rest: "#36405f" };
const SVGNS = "http://www.w3.org/2000/svg";

function svgEl(name, attrs = {}, text) {
  const el = document.createElementNS(SVGNS, name);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  if (text !== undefined) el.textContent = text;
  return el;
}

function niceMax(v) {
  if (v <= 5) return 5;
  const pow = 10 ** Math.floor(Math.log10(v));
  return [1, 2, 2.5, 5, 10].map(m => m * pow).find(m => m >= v);
}

function chartShell(host, width, height) {
  host.classList.add("chart");
  const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img" });
  const tip = document.createElement("div");
  tip.className = "tip";
  host.append(svg, tip);
  const show = (evt, text) => {
    const box = host.getBoundingClientRect();
    tip.textContent = text;
    tip.style.display = "block";
    tip.style.left = `${evt.clientX - box.left}px`;
    tip.style.top = `${evt.clientY - box.top}px`;
  };
  const hide = () => { tip.style.display = "none"; };
  const hover = (el, text) => {
    el.addEventListener("pointermove", e => show(e, text));
    el.addEventListener("pointerleave", hide);
  };
  return { svg, hover };
}

function yAxis(svg, max, x0, x1, y0, y1) {
  for (let i = 0; i <= 5; i++) {
    const v = (max / 5) * i, y = y0 - (y0 - y1) * (i / 5);
    svg.append(svgEl("line", { class: "grid", x1: x0, x2: x1, y1: y, y2: y }));
    svg.append(svgEl("text", { x: x0 - 8, y: y + 4, "text-anchor": "end" }, v.toLocaleString()));
  }
}

function dataTable(host, head, rows) {
  const d = document.createElement("details");
  d.className = "data";
  d.innerHTML = `<summary>View the numbers</summary><table><thead><tr>${head.map(h => `<th>${esc(h)}</th>`).join("")}</tr></thead>
    <tbody>${rows.map(r => `<tr>${r.map(c => `<td>${esc(typeof c === "number" ? c.toLocaleString() : c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  host.append(d);
}

// Vertical bars. items: [{label, value}]
function barsV(host, items, { unit = "", color = COLOR.all, tableHead = ["", "Count"] } = {}) {
  const W = 760, H = 260, L = 48, R = 12, T = 18, B = 34;
  const { svg, hover } = chartShell(host, W, H);
  const max = niceMax(Math.max(1, ...items.map(d => d.value)));
  yAxis(svg, max, L, W - R, H - B, T);
  const step = (W - L - R) / items.length, bw = Math.min(46, step - 2);
  const every = Math.ceil(items.length / 12);
  items.forEach((d, i) => {
    const cx = L + step * (i + 0.5), h = (d.value / max) * (H - B - T);
    if (d.value > 0) {
      const r = Math.min(4, h, bw / 2), x = cx - bw / 2, y = H - B - h;
      svg.append(svgEl("path", { fill: color,
        d: `M${x},${H - B}V${y + r}Q${x},${y} ${x + r},${y}H${x + bw - r}Q${x + bw},${y} ${x + bw},${y + r}V${H - B}Z` }));
      if (items.length <= 16) svg.append(svgEl("text", { class: "val", x: cx, y: y - 5, "text-anchor": "middle" }, d.value.toLocaleString()));
    }
    if (i % every === 0) svg.append(svgEl("text", { x: cx, y: H - B + 18, "text-anchor": "middle" }, d.label));
    const hit = svgEl("rect", { x: cx - step / 2, y: T, width: step, height: H - B - T, fill: "transparent" });
    hover(hit, `${d.label}: ${d.value.toLocaleString()}${unit}`);
    svg.append(hit);
  });
  dataTable(host, tableHead, items.map(d => [d.label, d.value]));
}

// Horizontal bars. items: [{label, value}], largest first.
function barsH(host, items, { unit = "", color = COLOR.all, tableHead = ["", "Count"] } = {}) {
  const row = 26, L = 190, R = 60, W = 760, H = items.length * row + 8;
  const { svg, hover } = chartShell(host, W, H);
  const max = Math.max(1, ...items.map(d => d.value));
  items.forEach((d, i) => {
    const y = 4 + i * row, w = Math.max(2, (d.value / max) * (W - L - R)), r = Math.min(4, w);
    const name = d.label.length > 28 ? d.label.slice(0, 27) + "…" : d.label;
    svg.append(svgEl("text", { x: L - 10, y: y + 15, "text-anchor": "end" }, name));
    svg.append(svgEl("path", { fill: color,
      d: `M${L},${y + 3}H${L + w - r}Q${L + w},${y + 3} ${L + w},${y + 3 + r}V${y + 19 - r}Q${L + w},${y + 19} ${L + w - r},${y + 19}H${L}Z` }));
    svg.append(svgEl("text", { class: "val", x: L + w + 6, y: y + 15 }, d.value.toLocaleString()));
    const hit = svgEl("rect", { x: 0, y, width: W, height: row, fill: "transparent" });
    hover(hit, `${d.label}: ${d.value.toLocaleString()}${unit}`);
    svg.append(hit);
  });
  dataTable(host, tableHead, items.map(d => [d.label, d.value]));
}

// Two lines on one axis. labels: [..]; series: [{name, color, values}]
function lines(host, labels, series, { tableHead } = {}) {
  const W = 760, H = 270, L = 48, R = 96, T = 18, B = 34;
  const { svg, hover } = chartShell(host, W, H);
  const max = niceMax(Math.max(1, ...series.flatMap(s => s.values)));
  yAxis(svg, max, L, W - R, H - B, T);
  const n = labels.length;
  const X = i => n === 1 ? (L + W - R) / 2 : L + ((W - L - R) * i) / (n - 1);
  const Y = v => H - B - (v / max) * (H - B - T);
  const every = Math.ceil(n / 10);
  labels.forEach((lab, i) => { if (i % every === 0) svg.append(svgEl("text", { x: X(i), y: H - B + 18, "text-anchor": "middle" }, lab)); });
  const ends = [];
  for (const s of series) {
    svg.append(svgEl("path", { fill: "none", stroke: s.color, "stroke-width": 2, "stroke-linejoin": "round",
      d: s.values.map((v, i) => `${i ? "L" : "M"}${X(i)},${Y(v)}`).join("") }));
    s.values.forEach((v, i) => svg.append(svgEl("circle", { cx: X(i), cy: Y(v), r: 4, fill: s.color, stroke: "#141a2e", "stroke-width": 2 })));
    ends.push({ s, y: Y(s.values[n - 1]) });
  }
  ends.sort((a, b) => a.y - b.y);
  if (ends.length > 1 && ends[1].y - ends[0].y < 14) ends[1].y = ends[0].y + 14;  // keep end labels apart
  for (const e of ends) svg.append(svgEl("text", { class: "val", x: X(n - 1) + 10, y: e.y + 4 }, e.s.name));
  const step = n === 1 ? W - L - R : (W - L - R) / (n - 1);
  labels.forEach((lab, i) => {
    const hit = svgEl("rect", { x: X(i) - step / 2, y: T, width: step, height: H - B - T, fill: "transparent" });
    hover(hit, `${lab}: ` + series.map(s => `${s.name} ${s.values[i].toLocaleString()}`).join(", "));
    svg.append(hit);
  });
  const legend = document.createElement("div");
  legend.className = "legend";
  legend.innerHTML = series.map(s => `<span><i style="background:${s.color}"></i>${esc(s.name)}</span>`).join("");
  host.append(legend);
  dataTable(host, tableHead || ["Day", ...series.map(s => s.name)], labels.map((lab, i) => [lab, ...series.map(s => s.values[i])]));
}

// One bar split in two parts. parts: [{label, value, color}]
function splitBar(host, parts) {
  const W = 760, H = 74;
  const { svg, hover } = chartShell(host, W, H);
  const total = parts.reduce((t, p) => t + p.value, 0) || 1;
  let x = 0;
  parts.forEach((p, i) => {
    const w = (p.value / total) * W;
    if (w > 0) {
      const seg = svgEl("rect", { x: x + (i ? 2 : 0), y: 8, width: Math.max(0, w - (i ? 2 : 0)), height: 30, rx: 4, fill: p.color });
      hover(seg, `${p.label}: ${p.value.toLocaleString()} (${Math.round((p.value / total) * 100)}%)`);
      svg.append(seg);
    }
    x += w;
  });
  svg.append(svgEl("text", { class: "val", x: 0, y: 60 }, `${parts[0].label}: ${parts[0].value.toLocaleString()}`));
  svg.append(svgEl("text", { class: "val", x: W, y: 60, "text-anchor": "end" }, `${parts[1].label}: ${parts[1].value.toLocaleString()}`));
  const legend = document.createElement("div");
  legend.className = "legend";
  legend.innerHTML = parts.map(p => `<span><i style="background:${p.color}"></i>${esc(p.label)}</span>`).join("");
  host.append(legend);
  dataTable(host, ["Group", "Postings"], parts.map(p => [p.label, p.value]));
}
