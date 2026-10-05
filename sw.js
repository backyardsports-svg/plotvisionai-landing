/* Cleanup stub. Browsers that already installed this site still check /sw.js.
   This worker drops every cache and unregisters itself so the visit returns
   to a normal webpage. New pages do not register a service worker. */
self.addEventListener("install", function () {
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (key) {
        return caches.delete(key);
      }));
    }).then(function () {
      return self.clients.claim();
    }).then(function () {
      return self.registration.unregister();
    }).then(function () {
      return self.clients.matchAll({ type: "window" });
    }).then(function (windowClients) {
      windowClients.forEach(function (client) {
        if (client.url && typeof client.navigate === "function") {
          client.navigate(client.url);
        }
      });
    })
  );
});
