// THE SYSTEM — Service Worker
// Caches the app shell for full offline use.
// On first load: caches index.html, manifest, icon.
// On subsequent loads: serves from cache, updates in background.

const CACHE = 'darkroom-v1';
const BASE  = '/The-Blank-Slate-Chaos';

const SHELL = [
  BASE + '/',
  BASE + '/index.html',
  BASE + '/manifest.json',
  BASE + '/icon.svg',
];

// ── INSTALL — cache shell ────────────────────────────────────────
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(SHELL))
  );
  self.skipWaiting();
});

// ── ACTIVATE — clean old caches ─────────────────────────────────
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── FETCH — cache first for shell, network first for API ─────────
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Always go network for: Cloudflare worker, GitHub API, external
  if (
    url.hostname.includes('workers.dev') ||
    url.hostname.includes('api.') ||
    url.hostname.includes('groq') ||
    e.request.method !== 'GET'
  ) {
    e.respondWith(fetch(e.request));
    return;
  }

  // Shell files — cache first, update in background (stale-while-revalidate)
  e.respondWith(
    caches.open(CACHE).then(async cache => {
      const cached = await cache.match(e.request);
      const fetchPromise = fetch(e.request).then(res => {
        if (res && res.status === 200) cache.put(e.request, res.clone());
        return res;
      }).catch(() => null);

      return cached || fetchPromise;
    })
  );
});
