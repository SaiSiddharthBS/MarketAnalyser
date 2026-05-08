const CACHE_NAME = 'marketpulse-v15';
const ASSETS = [
    '/',
    '/static/css/styles.css',
    '/static/js/app.js',
    '/static/js/api.js',
    '/static/js/charts.js',
    '/static/images/icon-192.png',
    '/static/images/icon-512.png',
    '/static/images/apple-touch-icon.png',
    '/static/images/favicon-32.png',
    'https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap'
];

self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
    );
});

self.addEventListener('fetch', (e) => {
    // Only cache GET requests
    if (e.request.method !== 'GET') return;
    
    // Don't cache API calls
    if (e.request.url.includes('/api/')) return;

    e.respondWith(
        caches.match(e.request).then((response) => {
            return response || fetch(e.request).then((fetchRes) => {
                return caches.open(CACHE_NAME).then((cache) => {
                    cache.put(e.request, fetchRes.clone());
                    return fetchRes;
                });
            });
        }).catch(() => {
            // Fallback for offline if needed
        })
    );
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
            );
        })
    );
});
