// Service worker: makes the site installable and lets it open offline.
// Data files: network first, so online visits always get fresh data; the last copy is kept for offline.
// Everything else (pages, styles, scripts, fonts): saved copy first, refreshed in the background.
const CACHE = "job-watcher-v1";
const SHELL = [
  "./", "index.html", "browse.html", "market.html", "style.css",
  "app.js", "today.js", "browse.js", "charts.js", "market.js",
  "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png",
];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
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
  const isData = url.origin === location.origin && url.pathname.includes("/data/");

  if (isData) {
    event.respondWith(
      fetch(req).then(res => {
        if (res.ok) caches.open(CACHE).then(c => c.put(url.pathname, res.clone()));
        return res.clone();
      }).catch(() => caches.match(url.pathname)));
    return;
  }
  event.respondWith(
    caches.match(req, { ignoreSearch: true }).then(hit => {
      const fresh = fetch(req).then(res => {
        if (res.ok || res.type === "opaque") caches.open(CACHE).then(c => c.put(req, res.clone()));
        return res.clone();
      }).catch(() => hit);
      return hit || fresh;
    }));
});
