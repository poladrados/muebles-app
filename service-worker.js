const CACHE_NAME = 'v3_cache'; // ⚠️ CAMBIADO para forzar renovación
const urlsToCache = [
  '/muebles-app/',
  '/muebles-app/manifest.json',
  '/muebles-app/images/apple-touch-icon.png'
];

// Instala el Service Worker y guarda archivos en caché (sin index.html)
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
  self.skipWaiting(); // activa inmediatamente
});

// Elimina cachés antiguas al activar el nuevo Service Worker
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames =>
      Promise.all(
        cacheNames.map(cache => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      )
    ).then(() => self.clients.claim())
  );
});

// Sirve desde caché si existe, si no, desde red
self.addEventListener('fetch', event => {
  // Nunca cachear index.html: forzar red para HTML
  if (event.request.mode === 'navigate') {
    return event.respondWith(fetch(event.request));
  }

  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});

