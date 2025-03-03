const CACHE_NAME = "her_shield_v2";  // Increment version
const urlsToCache = [
    "/",
    "/static/style.css",
    "/static/script.js",
    "/static/manifest.json"
];

self.addEventListener("install", (event) => {
    console.log("Service Worker installing...");
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log("Caching assets...");
            return cache.addAll(urlsToCache);
        })
    );
});

// Delete old caches on activation
self.addEventListener("activate", (event) => {
    console.log("Service Worker activated!");
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log("Deleting old cache:", cache);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
});

// Serve cached content if available, else fetch from network
self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});
