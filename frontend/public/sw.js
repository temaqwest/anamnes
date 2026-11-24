const offlineCache = "anamnes-offline-v3"
const offlinePage = "/offline.html"

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(offlineCache)
    .then((cache) => cache.add(new Request(offlinePage, { cache: "reload" })))
    .then(() => self.skipWaiting()))
})

self.addEventListener("activate", (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(
    keys.filter((key) => key.startsWith("anamnes-offline-") && key !== offlineCache)
      .map((key) => caches.delete(key)),
  )).then(() => self.clients.claim()))
})

self.addEventListener("fetch", (event) => {
  const request = event.request
  const url = new URL(request.url)
  if (request.mode !== "navigate" || request.method !== "GET" || url.origin !== self.location.origin
    || url.pathname === "/api" || url.pathname.startsWith("/api/")) return

  event.respondWith(fetch(request).catch(async () => {
    const cache = await caches.open(offlineCache)
    return (await cache.match(offlinePage)) ?? Response.error()
  }))
})
