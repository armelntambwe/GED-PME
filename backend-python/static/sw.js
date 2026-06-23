// Service Worker GED-PME — shell hors-ligne
const CACHE_NAME = 'ged-pme-v4';

const SHELL_URLS = [
    '/',
    '/login',
    '/dashboard-employee',
    '/offline.html',
    '/offline-queue.js',
    '/static/js/ged-offline-store.js',
    '/static/js/ged-employee-app.js',
    '/static/css/ged-theme.css',
    '/static/css/ged-dashboard.css',
    '/static/css/sharepoint-home.css',
    '/static/manifest.json',
    '/static/img/default-avatar.svg',
    'https://code.jquery.com/jquery-3.7.1.min.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://cdn.jsdelivr.net/npm/chart.js',
];

function isApiRequest(url) {
    const p = url.pathname;
    return p.startsWith('/documents') ||
        p.startsWith('/api/') ||
        p.startsWith('/categories') ||
        p.startsWith('/notifications') ||
        p.startsWith('/login') && url.search.includes('json');
}

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(async (cache) => {
            await Promise.allSettled(SHELL_URLS.map((u) => cache.add(u).catch(() => null)));
            self.skipWaiting();
        })
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
        ).then(() => self.clients.claim())
    );
});

self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    if (request.method !== 'GET') return;

    const url = new URL(request.url);
    if (url.origin !== self.location.origin && !SHELL_URLS.includes(request.url)) {
        // CDN : cache-first si disponible
        event.respondWith(
            caches.match(request).then((cached) =>
                cached || fetch(request).then((res) => {
                    if (res.ok) {
                        const clone = res.clone();
                        caches.open(CACHE_NAME).then((c) => c.put(request, clone));
                    }
                    return res;
                }).catch(() => cached)
            )
        );
        return;
    }

    if (isApiRequest(url)) return;

    event.respondWith(
        caches.match(request).then((cached) => {
            const network = fetch(request).then((res) => {
                if (res && res.ok) {
                    const clone = res.clone();
                    caches.open(CACHE_NAME).then((c) => c.put(request, clone));
                }
                return res;
            }).catch(() => null);

            return network.then((res) => {
                if (res) return res;
                if (cached) return cached;
                if (request.mode === 'navigate') {
                    return caches.match('/dashboard-employee')
                        || caches.match('/offline.html');
                }
                return new Response('Hors ligne', { status: 503 });
            });
        })
    );
});
