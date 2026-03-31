const CACHE_NAME = "erpy-lite-v1";
const ASSETS = [
    "/",
    "/inventario",
    "/static/css/style.css",
    "/static/manifest.json"
];

// Instalación: cachea los recursos principales
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
    );
    self.skipWaiting();
});

// Activación: limpia caches antiguas
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
            )
        )
    );
    self.clients.claim();
});

// Fetch: Network-first con fallback a cache
self.addEventListener("fetch", (event) => {
    // Solo cachear peticiones GET
    if (event.request.method !== "GET") return;

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Guardar copia en cache
                const clone = response.clone();
                caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                return response;
            })
            .catch(() => {
                // Si no hay red, buscar en cache
                return caches.match(event.request);
            })
    );
});
