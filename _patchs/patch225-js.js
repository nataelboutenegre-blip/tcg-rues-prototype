// ---------- patch122 : ecran de chargement ----------
// patch225 : la France coupée entre Terra et Front. Le dessin est dans
// index.html : il s'anime avant même que ce script soit téléchargé. Ici, le
// contour doré suit le chargement (--pct) et, à l'arrivée dans le jeu, le
// dernier mode joué recouvre la France, comme le balayage de changement de mode.
const DM_T0 = performance.now();
let dmFini = false;
const DM_ASTUCES = [
  'marque d’une ⭐ les 5 communes que tu veux garder à la fin de la saison.',
  'la cloche 🔔 te montre ce qui t’attend : attaques, échanges, quêtes à réclamer.',
  'mets un département en ⚡ dans les réglages de la cloche : tu seras prévenu dès la 1re attaque.',
  'chaque légendaire gardée 24 h te rapporte +2 énergie par jour (10 au plus) : pense à récolter.',
  'réclame tes quêtes avant minuit : après, elles sont perdues.',
  'les communes d’outre-mer tombent aussi dans les paquets : bascule Ma France sur « Outre-mer ».',
  'en Front, une commune tombe après 3 rounds gagnés d’affilée : défends-la ou pose un bouclier.',
  'ta vitrine expose jusqu’à 20 cartes sur ton profil, en Terra comme en Front.'
];
function dmMesure(etiquette){ try{ console.info(`[démarrage] ${etiquette} : ${Math.round(performance.now() - DM_T0)} ms`); }catch(e){} }
function dmEtape(pct, texte){
  if(dmFini) return;
  const el = document.getElementById('demarrage'), t = document.getElementById('dmTexte');
  if(el){ el.style.setProperty('--pct', String(Math.max(0, Math.min(100, pct)) / 100)); el.classList.toggle('dm-corse-on', pct >= 88); }
  if(t) t.textContent = texte;
}
// la ligne de partage, inclinée de 10°, passe par le centre de la carte (dessin de 100 × 98,38)
const DM_H = 98.38, DM_TAN = Math.tan(10 * Math.PI / 180);
function dmPolys(s){
  const x = (y) => (50 + s + DM_TAN * (DM_H / 2 - y)).toFixed(2), yh = -20, yb = (DM_H + 20).toFixed(2);
  return { terra: `-60,${yh} ${x(yh)},${yh} ${x(yb)},${yb} -60,${yb}`, front: `${x(yh)},${yh} 170,${yh} 170,${yb} ${x(yb)},${yb}`, x1: x(yh), x2: x(yb) };
}
function dmSortie(el, mode){
  el.classList.add('sortie', 'm-' + mode);
  const cible = mode === 'front' ? -80 : 80, t0 = performance.now(), D = 620;
  const ease = (u) => u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
  const pT = document.getElementById('dmPolyT'), pF = document.getElementById('dmPolyF'), l = document.getElementById('dmLigne');
  const pas = (now) => {
    const u = Math.min(1, Math.max(0, (now - t0) / D)), p = dmPolys(cible * ease(u));
    if(pT && pF && l){ pT.setAttribute('points', p.terra); pF.setAttribute('points', p.front); l.setAttribute('x1', p.x1); l.setAttribute('x2', p.x2); }
    if(u < 1 && el.isConnected) requestAnimationFrame(pas);
  };
  requestAnimationFrame(pas);
  setTimeout(() => el.classList.add('fini'), 640);
  setTimeout(() => el.remove(), 1150);
}
// entree === true : on arrive dans le jeu. Sinon (accueil, connexion, 15 s) : simple fondu.
function dmFin(entree){
  if(dmFini) return;
  dmEtape(100, 'Prêt');
  dmFini = true;
  dmMesure('jeu affiché');
  const el = document.getElementById('demarrage');
  if(!el) return;
  const anim = entree === true && SAISON2 && ouvAnim && !REDUCED_MOTION && !!document.getElementById('dmPolyT');
  if(!anim){ el.classList.add('fini'); setTimeout(() => el.remove(), 600); return; }
  // l'entrée de l'écran (environ 1,3 s depuis l'ouverture de la page) se termine d'abord
  setTimeout(() => dmSortie(el, modeJeu === 'front' ? 'front' : 'terra'), Math.max(0, 1300 - performance.now()) + 250);
}
(function dmDepart(){
  const a = document.getElementById('dmAstuce');
  if(a) a.innerHTML = '<b>Astuce :</b> ' + DM_ASTUCES[Math.floor(Math.random() * DM_ASTUCES.length)];
  dmEtape(12, 'Connexion…');
})();
// jamais bloque derriere l'ecran : 15 s au plus
setTimeout(dmFin, 15000);
