self.addEventListener("install", (e) => {
  console.log("Service Worker instalado");
});

self.addEventListener("fetch", (e) => {
  // No interceptamos nada, solo declaramos el SW
});
