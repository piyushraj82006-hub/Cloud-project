/* CloudGuard DR — Service Worker */
/* Cache-first for static assets, network-first for navigation */

const CACHE_NAME = 'cloudguard-v1'
const STATIC_CACHE = 'cloudguard-static-v1'

// Assets to pre-cache on install
const PRE_CACHE = [
  '/',
  '/index.html',
]

// Install — pre-cache shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(PRE_CACHE))
      .then(() => self.skipWaiting())
  )
})

// Activate — clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME && key !== STATIC_CACHE)
          .map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  )
})

// Fetch strategies
self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)

  // Skip non-GET and cross-origin
  if (request.method !== 'GET' || url.origin !== self.location.origin) {
    return
  }

  // Navigation requests — network-first, fallback to cached shell
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const clone = response.clone()
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone))
          return response
        })
        .catch(() => caches.match('/index.html'))
    )
    return
  }

  // Static assets (JS, CSS, images, fonts) — cache-first
  if (
    url.pathname.endsWith('.js') ||
    url.pathname.endsWith('.css') ||
    url.pathname.match(/\.(png|jpg|jpeg|gif|svg|ico|woff2?|ttf|eot)$/)
  ) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached
        return fetch(request).then((response) => {
          const clone = response.clone()
          caches.open(STATIC_CACHE).then((cache) => cache.put(request, clone))
          return response
        })
      })
    )
    return
  }

  // Everything else — network-first
  event.respondWith(
    fetch(request)
      .then((response) => {
        const clone = response.clone()
        caches.open(CACHE_NAME).then((cache) => cache.put(request, clone))
        return response
      })
      .catch(() => caches.match(request))
  )
})
