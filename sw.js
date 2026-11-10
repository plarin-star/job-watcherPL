// Service worker: makes the site installable and lets it open offline.
// Files from this site (pages, styles, scripts, data): network first, so an online visit always
// gets the newest version; the last copy is kept and used when offline.
// Fonts from Google: saved copy first, since they do not change.
const CACHE = "job-watcher-v3";
const SHELL = [
  "./", "index.html", "browse.html", "market.html", "style.css",
  "app.js", "today.js", "browse.js", "charts.js", "market.js",
  "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png",
  "data/status.json", "data/history.csv",
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(SHELL.map(u => new Request(u, { cache: "reload" }))))
      .then(() => self.skipWaiting()));
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim()));
});

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  if (url.origin === location.origin) {
    const key = url.origin + url.pathname;          // ignore ?query strings
    event.respondWith(
      fetch(req.url, { cache: "no-cache" }).then(res => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(key, copy));
        }
        return res;
      }).catch(() => caches.match(key).then(hit => hit || caches.match("index.html"))));
    return;
  }
  event.respondWith(
    caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res.ok || res.type === "opaque") {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy));
      }
      return res;
    })));
});
