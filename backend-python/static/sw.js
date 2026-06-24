// Service Worker GED-PME — shell hors-ligne (employé uniquement)
const CACHE_NAME = 'ged-pme-v5';

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
        (p.startsWith('/login') && url.search.includes('json'));
}

/** Ne jamais intercepter : extensions, antivirus (Kaspersky), blob, etc. */
function shouldBypass(request) {
    const url = new URL(request.url);
    const scheme = url.protocol;
    if (scheme !== 'http:' && scheme !== 'https:') return true;
    if (/kaspersky|kis\.v2\.scr/i.test(url.hostname)) return true;
    if (url.origin === self.location.origin) return false;
    return !SHELL_URLS.includes(request.url);
}

function safeCachePut(cache, request, response) {
    if (!response || !response.ok) return Promise.resolve();
    try {
        return cache.put(request, response.clone()).catch(function () {});
    } catch (e) {
        return Promise.resolve();
    }
}

self.addEventListener('install', function (event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function (cache) {
            return Promise.allSettled(
                SHELL_URLS.map(function (u) { return cache.add(u).catch(function () {}); })
            );
        }).then(function () { return self.skipWaiting(); })
    );
});

self.addEventListener('activate', function (event) {
    event.waitUntil(
        caches.keys().then(function (keys) {
            return Promise.all(
                keys.filter(function (k) { return k !== CACHE_NAME; }).map(function (k) { return caches.delete(k); })
            );
        }).then(function () { return self.clients.claim(); })
    );
});

self.addEventListener('message', function (event) {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

self.addEventListener('fetch', function (event) {
    var request = event.request;
    if (request.method !== 'GET') return;
    if (shouldBypass(request)) return;

    var url = new URL(request.url);

    if (isApiRequest(url)) return;

    event.respondWith(
        caches.match(request).then(function (cached) {
            return fetch(request).then(function (res) {
                if (res && res.ok) {
                    caches.open(CACHE_NAME).then(function (cache) {
                        safeCachePut(cache, request, res);
                    });
                }
                return res;
            }).catch(function () {
                if (cached) return cached;
                if (request.mode === 'navigate') {
                    return caches.match('/dashboard-employee')
                        .then(function (r) { return r || caches.match('/offline.html'); });
                }
                return cached || new Response('', { status: 504, statusText: 'Offline' });
            });
        })
    );
});
