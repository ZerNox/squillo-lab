// Keeps the page and its clips on the device so it opens with no network. The network still wins when it answers
// within 4 s, so a new version reaches the singer on the next visit; every answer refreshes the copy. Audio is never seen here.
const CACHE = 'helix-1', FILES = [
  './', 'manifest.webmanifest', 'rating/anchors.json', 'ref/polished.mp3', 'ref/rough.mp3',
  'demo/f2_belt.mp3', 'demo/f2_breathy.mp3', 'demo/f2_caro_straight.mp3', 'demo/f2_caro_vibrato.mp3', 'demo/f2_straight.mp3', 'demo/f2_vibrato.mp3', 'demo/f2_vocal_fry.mp3', 'demo/m2_belt.mp3', 'demo/m2_breathy.mp3', 'demo/m2_caro_straight.mp3', 'demo/m2_caro_vibrato.mp3', 'demo/m2_straight.mp3', 'demo/m2_vibrato.mp3', 'demo/m2_vocal_fry.mp3', 'font/plex-mono-400.woff2', 'font/plex-mono-500.woff2', 'font/plex-sans.woff2', 'font/syne.woff2', 'icon/icon-180.png', 'icon/icon-192.png', 'icon/icon-512.png'
];
self.addEventListener('install', e => { self.skipWaiting(); e.waitUntil(caches.open(CACHE).then(c => Promise.all(FILES.map(f => c.add(new Request(f, { cache: 'reload' })).catch(() => {}))))); });
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(k => Promise.all(k.filter(n => n !== CACHE).map(n => caches.delete(n))))));
self.addEventListener('fetch', e => { const q = e.request, u = new URL(q.url);
  if (q.method !== 'GET' || u.origin !== location.origin) return;
  e.respondWith((async () => { const c = await caches.open(CACHE), key = q.mode === 'navigate' ? './' : q, old = await c.match(key, { ignoreSearch: true }),
      net = fetch(q).then(r => { if (r.ok) c.put(key, r.clone()); return r; });
    if (!old) return net;
    net.catch(() => {}); let t; const late = new Promise(r => t = setTimeout(() => r(old), 4000));
    const r = await Promise.race([net.catch(() => old), late]); clearTimeout(t); return r; })()); });
