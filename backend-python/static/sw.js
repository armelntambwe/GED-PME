// ============================================
// static/sw.js - Service Worker pour mode hors-ligne
// ============================================

const CACHE_NAME = 'ged-pme-cache-v1';
const API_URL = 'http://localhost:5000';

// Fichiers à mettre en cache
const urlsToCache = [
  '/',
  '/index.html',
  '/offline.html',
  '/sw.js',
  '/offline-queue.js'
];

// Installation du service worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('📦 Cache ouvert');
        return cache.addAll(urlsToCache);
      })
  );
});

// Interception des requêtes
self.addEventListener('fetch', event => {
  // ✅ IGNORER LES MÉTHODES POST (upload, etc.)
  if (event.request.method === 'POST') {
    // Ne pas essayer de cacher, laisser passer normalement
    event.respondWith(fetch(event.request));
    return;
  }
  
  // ✅ IGNORER LES REQUÊTES API (optionnel)
  if (event.request.url.includes('/documents/') || 
      event.request.url.includes('/login') || 
      event.request.url.includes('/register')) {
    event.respondWith(fetch(event.request));
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Si en cache, retourne la version cachée
        if (response) {
          return response;
        }

        // Sinon, va chercher sur le réseau
        return fetch(event.request).then(
          networkResponse => {
            // Vérifie si la réponse est valide
            if (!networkResponse || networkResponse.status !== 200) {
              return networkResponse;
            }

            // Met en cache la nouvelle réponse
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });

            return networkResponse;
          }
        ).catch(() => {
          // Si réseau indisponible et que la requête est pour une page
          if (event.request.mode === 'navigate') {
            return caches.match('/offline.html');
          }
        });
      })
  );
});