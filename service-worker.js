const CACHE_NAME = 'v1_cache';
const urlsToCache = [
  '/muebles-app/',
  '/muebles-app/index.html',
  '/muebles-app/manifest.json',
  '/muebles-app/images/apple-touch-icon.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
