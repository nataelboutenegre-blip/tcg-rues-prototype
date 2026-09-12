// Service worker TerraFront : recoit les notifications, meme quand le jeu est ferme.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil((async () => {
  // a chaque nouvelle version, on vide ce que le navigateur avait garde
  const noms = await caches.keys();
  await Promise.all(noms.map(n => caches.delete(n)));
  await self.clients.claim();
})()));

self.addEventListener('message', (event) => {
  if(event.data && event.data.type === 'maj-maintenant') self.skipWaiting();
});

self.addEventListener('push', (event) => {
  let d = {};
  try { d = event.data ? event.data.json() : {}; }
  catch(e){ d = { titre: 'TerraFront', texte: event.data ? event.data.text() : '' }; }
  const url = new URL(d.url || './', self.registration.scope).href;
  // sur iPhone, chaque notification recue DOIT etre affichee, sinon Apple coupe l'abonnement
  event.waitUntil(self.registration.showNotification(d.titre || 'TerraFront', {
    body: d.texte || '',
    icon: 'icon-192.png',
    badge: 'icon-192.png',
    tag: d.tag || undefined,
    data: { url }
  }));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || self.registration.scope;
  event.waitUntil((async () => {
    const fenetres = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for(const f of fenetres){
      if(f.url.startsWith(self.registration.scope)){
        await f.focus();
        f.postMessage({ type: 'ouvrir', url });
        return;
      }
    }
    await self.clients.openWindow(url);
  })());
});
