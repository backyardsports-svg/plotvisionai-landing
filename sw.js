/* Network-first. The install step stores the homepage and its hero photos so
   an installed launch still opens PlotVisionAI when the network is down.
   Later visits try the network first and fall back to that cache. */
var CACHE = "plotvisionai-v3";
var SHELL = [
  "/",
  "/styles.css",
  "/hero-lock.css",
  "/script.js",
  "/config.js",
  "/assets/hero-home-01-before.jpg",
  "/assets/hero-home-01-after.jpg",
  "/assets/hero-home-01-before-2x.jpg",
  "/assets/hero-home-01-after-2x.jpg"
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (cache) {
      return cache.addAll(SHELL);
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (key) {
        return key !== CACHE;
      }).map(function (key) {
        return caches.delete(key);
      }));
    }).then(function () {
      return self.clients.claim();
    })
  );
});

self.addEventListener("fetch", function (event) {
  var request = event.request;
  if (request.method !== "GET") return;

  var url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    fetch(request)
      .then(function (response) {
        if (response && response.ok && response.type === "basic") {
          var copy = response.clone();
          caches.open(CACHE).then(function (cache) {
            cache.put(request, copy);
          }).catch(function () {});
        }
        return response;
      })
      .catch(function () {
        return caches.match(request).then(function (cached) {
          if (cached) return cached;
          /* Only the installed start URL may fall back to the saved homepage.
             Any other address should fail instead of showing the wrong page. */
          if (request.mode === "navigate" && (url.pathname === "/" || url.pathname === "/index.html")) {
            return caches.match("/");
          }
          return Promise.reject(new Error("offline"));
        });
      })
  );
});
