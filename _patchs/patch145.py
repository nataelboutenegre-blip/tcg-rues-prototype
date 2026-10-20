# -*- coding: utf-8 -*-
u"""
patch145 — la carte du Front ne gèle plus (retours de Maroli, Boule2Pain,
H34VEN, LeoLesel, 20 octobre).

Mesuré sur la vraie carte (29 413 communes possédées, zoom 3) : chaque image
d'un déplacement ou d'un zoom repeignait ~15 000 communes et 173 000 points,
trois traits par joueur. Ce n'est pas le serveur, c'est l'appareil du joueur.

1. Pendant un geste (glisser, molette, pincement), on déplace l'image déjà
   peinte au lieu de tout repeindre ; la carte nette est repeinte 160 ms
   après le dernier mouvement. ?rendu=complet désactive (porte de sortie).
2. Le rendu complet ne peint plus que les communes dans l'écran (boîte de
   chaque commune calculée une fois), et ne refait plus à chaque image la
   table des communes possédées ni la projection de toutes les communes.
3. Les données de la carte se recalculent quand les listes sont rechargées
   (avant : seulement si leur taille changeait — une commune passée d'un
   joueur à un autre pouvait rester de l'ancienne couleur).
4. Conquête depuis la carte : la commune change de couleur tout de suite,
   le rechargement complet (des dizaines de milliers de lignes en saison 1)
   passe 8 s plus tard sans bloquer, comme dans l'onglet Combat (patch135).
5. Fenêtres (fiche d'une commune…) plus hautes que l'écran du téléphone :
   le haut et la croix sortaient de l'écran sans pouvoir y revenir
   (LeoLesel). Le fond défile, la fenêtre ne se centre que si elle tient.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

js = lire('app.js')
assert 'patch145' not in js, u'patch145 deja applique'

# ---------- 2. departements visibles : coordonnees deja projetees ----------
js = rempl(js, u"""  const ajouter = (c) => {
    if(c.lat == null) return;
    const p = project(c.lat, c.lon);
    const x = p.x * MAP_W * ech * mapZoom + mapPanX, y = p.y * MAP_H * ech * mapZoom + mapPanY;
    if(x > -60 && x < w + 60 && y > -60 && y < h + 60) vus.add(c.dept);
  };""", u"""  const ajouter = (c) => {
    if(c.lat == null) return;
    // patch145 : la liste de la carte porte deja ses coordonnees projetees
    let mx = c.x, my = c.y;
    if(mx == null){ const p = project(c.lat, c.lon); mx = p.x * MAP_W; my = p.y * MAP_H; }
    const x = mx * ech * mapZoom + mapPanX, y = my * ech * mapZoom + mapPanY;
    if(x > -60 && x < w + 60 && y > -60 && y < h + 60) vus.add(c.dept);
  };""", 'departementsVisibles')

# ---------- 1. geste : on deplace l'image deja peinte ----------
js = rempl(js, u"""  if(canvasActif()){ demanderDessin(); return; }
  signalerMouvementCarte();""", u"""  if(canvasActif()){ signalerGesteCanvas(); demanderDessin(); return; }   // patch145
  signalerMouvementCarte();""", 'applyMapTransform')

js = rempl(js, u"""function canvasActif(){
  return MODE_CANVAS && CV.ctx;
}""", u"""function canvasActif(){
  return MODE_CANVAS && CV.ctx;
}

// ---------- patch145 : la carte ne gele plus pendant un geste ----------
// Repeindre 15 000 communes a chaque image d'un deplacement faisait geler les
// telephones. Pendant le geste on deplace (et agrandit) l'image deja peinte ;
// 160 ms apres le dernier mouvement, la carte nette est repeinte une fois.
// ?rendu=complet : porte de sortie, tout est repeint a chaque image comme avant.
const RENDU_INSTANTANE = new URLSearchParams(location.search).get('rendu') !== 'complet';
CV.instantane = null;          // { cv, k, tx, ty } : la derniere carte nette
CV.geste = false;
CV.finGeste = null;
CV.boitesCommunes = new Map(); // code commune -> [x0, y0, x1, y1] en unites de carte

function signalerGesteCanvas(){
  if(!RENDU_INSTANTANE) return;
  CV.geste = true;
  clearTimeout(CV.finGeste);
  CV.finGeste = setTimeout(() => { CV.geste = false; demanderDessin(); }, 160);
}

function peindreMer(ctx){
  const L = CV.largeur * CV.dpr, H = CV.hauteur * CV.dpr;
  const g = ctx.createRadialGradient(L * 0.45, H * 0.4, 0, L * 0.45, H * 0.4, L * 0.75);
  g.addColorStop(0, '#12294A');
  g.addColorStop(1, '#081427');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, L, H);
}

// Renvoie false quand l'image gardee ne convient pas : on repeint alors tout.
function dessinerInstantane(k, tx, ty){
  const s = CV.instantane, ctx = CV.ctx;
  if(!s || s.cv.width !== ctx.canvas.width || s.cv.height !== ctx.canvas.height) return false;
  const r = k / s.k;
  if(!(r > 1 / 6 && r < 6)) return false;   // trop loin de l'image gardee : flou illisible
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  peindreMer(ctx);
  // ce que l'image ne couvre pas (le bord decouvert en glissant) montre la
  // terre sans territoires plutot que la mer
  const fond = cheminsDuFond();
  if(fond){
    ctx.setTransform(k, 0, 0, k, tx, ty);
    ctx.fillStyle = '#1C3860';
    ctx.fill(fond.terre);
  }
  // un point de l'image gardee : u = s.k * m + s.tx ; a l'ecran : k * m + tx
  ctx.setTransform(r, 0, 0, r, tx - r * s.tx, ty - r * s.ty);
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(s.cv, 0, 0);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  return true;
}

function memoriserInstantane(k, tx, ty){
  if(!RENDU_INSTANTANE) return;
  const cv = CV.ctx.canvas;
  if(!CV.instantane) CV.instantane = { cv: document.createElement('canvas') };
  const s = CV.instantane;
  if(s.cv.width !== cv.width || s.cv.height !== cv.height){ s.cv.width = cv.width; s.cv.height = cv.height; }
  s.cv.getContext('2d').drawImage(cv, 0, 0);
  s.k = k; s.tx = tx; s.ty = ty;
}

// La partie de la carte a l'ecran, en unites de carte, avec une marge en pixels
function vueCarteUnites(marge){
  const e = echelleCarte() * mapZoom;
  return [(-marge - mapPanX) / e, (-marge - mapPanY) / e,
          (CV.largeur + marge - mapPanX) / e, (CV.hauteur + marge - mapPanY) / e];
}

function boiteCommune(code, poly){
  let b = CV.boitesCommunes.get(code);
  if(b) return b;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for(const anneau of poly) for(const pt of anneau){
    const p = project(pt[1], pt[0]);
    const x = p.x * MAP_W, y = p.y * MAP_H;
    if(x < x0) x0 = x; if(x > x1) x1 = x;
    if(y < y0) y0 = y; if(y > y1) y1 = y;
  }
  b = [x0, y0, x1, y1];
  CV.boitesCommunes.set(code, b);
  return b;
}

// Un numero par objet Map : une liste rechargee (meme de meme taille) change
// la signature des donnees de la carte.
const JETONS_CARTE = new WeakMap();
let jetonCarteSuivant = 1;
function jetonCarte(o){
  if(!o) return 0;
  let j = JETONS_CARTE.get(o);
  if(!j){ j = jetonCarteSuivant++; JETONS_CARTE.set(o, j); }
  return j;
}""", 'outils patch145')

js = rempl(js, u"""  const ctx = CV.ctx;
  const k = echelleCarte() * mapZoom * CV.dpr;
  const tx = mapPanX * CV.dpr, ty = mapPanY * CV.dpr;

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, CV.largeur * CV.dpr, CV.hauteur * CV.dpr);

  // la mer, en degrade comme dans le SVG
  const g = ctx.createRadialGradient(
    CV.largeur * CV.dpr * 0.45, CV.hauteur * CV.dpr * 0.4, 0,
    CV.largeur * CV.dpr * 0.45, CV.hauteur * CV.dpr * 0.4, CV.largeur * CV.dpr * 0.75);
  g.addColorStop(0, '#12294A');
  g.addColorStop(1, '#081427');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, CV.largeur * CV.dpr, CV.hauteur * CV.dpr);
""", u"""  const ctx = CV.ctx;
  const k = echelleCarte() * mapZoom * CV.dpr;
  const tx = mapPanX * CV.dpr, ty = mapPanY * CV.dpr;
  if(CV.geste && dessinerInstantane(k, tx, ty)) return;   // patch145

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, CV.largeur * CV.dpr, CV.hauteur * CV.dpr);

  // la mer, en degrade comme dans le SVG
  peindreMer(ctx);
""", 'dessinerCanvas debut')

js = rempl(js, u"""  ctx.setTransform(1, 0, 0, 1, 0, 0);
  dessinerNomsRegions(ctx);
}""", u"""  ctx.setTransform(1, 0, 0, 1, 0, 0);
  dessinerNomsRegions(ctx);
  memoriserInstantane(k, tx, ty);   // patch145
}""", 'dessinerCanvas fin')

# ---------- 3. signature des donnees + coordonnees projetees ----------
js = rempl(js, u"""  const signature = [collectionMap.size, othersMap.size, showOthers ? 1 : 0, bandeDeZoom(),""",
               u"""  const signature = [jetonCarte(collectionMap), collectionMap.size, jetonCarte(othersMap), othersMap.size,   // patch145
                     showOthers ? 1 : 0, bandeDeZoom(),""", 'signature')

js = rempl(js, u"""    if(showOthers && visible) liste.push({ code: e.code, nom: e.nom, dept: e.dept, lat: e.lat, lon: e.lon, tier: e.tier.id, joueur: e.joueurId });""",
               u"""    if(showOthers && visible) liste.push(entreeCarte(e, e.joueurId));   // patch145""", 'liste autres')
js = rempl(js, u"""function territoiresVisibles(){
  const joueurs = new Map();
  joueurs.set(ID_MOI, { id: ID_MOI, pseudo: 'Toi', couleur: COULEUR_MOI, fonce: couleurFoncee(COULEUR_MOI), moi: true, nb: 0 });
  const liste = [];
  for(const e of collectionMap.values()){
    if(!METRO_DEPT_RE.test(e.dept) || e.lat == null) continue;
    liste.push({ code: e.code, nom: e.nom, dept: e.dept, lat: e.lat, lon: e.lon, tier: e.tier.id, joueur: ID_MOI });""", u"""// patch145 : projetee une fois par chargement, et non plus a chaque image
function entreeCarte(e, joueur){
  const p = project(e.lat, e.lon);
  return { code: e.code, nom: e.nom, dept: e.dept, lat: e.lat, lon: e.lon, tier: e.tier.id, joueur,
           x: p.x * MAP_W, y: p.y * MAP_H };
}

function territoiresVisibles(){
  const joueurs = new Map();
  joueurs.set(ID_MOI, { id: ID_MOI, pseudo: 'Toi', couleur: COULEUR_MOI, fonce: couleurFoncee(COULEUR_MOI), moi: true, nb: 0 });
  const liste = [];
  for(const e of collectionMap.values()){
    if(!METRO_DEPT_RE.test(e.dept) || e.lat == null) continue;
    liste.push(entreeCarte(e, ID_MOI));   // patch145""", 'entreeCarte + liste moi')

# ---------- 2. rendu complet : seulement ce qui est a l'ecran ----------
js = rempl(js, u"""      const possedees = new Map(liste.map(c => [c.code, c]));
      const parJoueur = new Map();""", u"""      // patch145 : la table ne change qu'avec les donnees, pas a chaque image
      if(CV.possedeesDe !== liste){ CV.possedeesDe = liste; CV.possedees = new Map(liste.map(c => [c.code, c])); }
      const possedees = CV.possedees;
      const vue = vueCarteUnites(12);
      const parJoueur = new Map();""", 'possedees')
js = rempl(js, u"""        for(const code in contours){
          const p = cheminCommuneCanvas(code, contours[code]);
          const c = possedees.get(code);""", u"""        for(const code in contours){
          // patch145 : une commune hors de l'ecran ne coute plus rien
          const b = boiteCommune(code, contours[code]);
          if(b[2] < vue[0] || b[0] > vue[2] || b[3] < vue[1] || b[1] > vue[3]) continue;
          const p = cheminCommuneCanvas(code, contours[code]);
          const c = possedees.get(code);""", 'boucle contours')
js = rempl(js, u"""        if(!pastilles.has(c.joueur)) pastilles.set(c.joueur, new Path2D());
        const pt = project(c.lat, c.lon);
        const x = pt.x * MAP_W, y = pt.y * MAP_H, r = RAYON_ZONE[c.tier] * ep;""", u"""        if(!pastilles.has(c.joueur)) pastilles.set(c.joueur, new Path2D());
        const x = c.x, y = c.y, r = RAYON_ZONE[c.tier] * ep;   // patch145""", 'pastilles')
js = rempl(js, u"""function dessinerMarqueursCanvas(ctx, liste, joueurs, k, legendairesSeules){
  const e = 1 / Math.max(1, mapZoom);
  for(const c of liste){
    if(c.tier !== 'legendaire' && (legendairesSeules || (c.tier !== 'rare' && c.tier !== 'epique'))) continue;
    const j = joueurs.get(c.joueur);
    if(!j) continue;
    const p = project(c.lat, c.lon);
    const x = p.x * MAP_W, y = p.y * MAP_H;""", u"""function dessinerMarqueursCanvas(ctx, liste, joueurs, k, legendairesSeules){
  const e = 1 / Math.max(1, mapZoom);
  const vue = vueCarteUnites(12);   // patch145
  for(const c of liste){
    if(c.tier !== 'legendaire' && (legendairesSeules || (c.tier !== 'rare' && c.tier !== 'epique'))) continue;
    const x = c.x, y = c.y;
    if(x < vue[0] || x > vue[2] || y < vue[1] || y > vue[3]) continue;
    const j = joueurs.get(c.joueur);
    if(!j) continue;""", 'marqueurs')

# ---------- 4. conquete depuis la carte ----------
js = rempl(js, u"""    if(r.conquise){
      await loadMyCollection();
      await loadOthersPossessions();
      fermerPanneau();
    }
    loadPackStatus();
    loadObjectifs();
    renderMapOverlay();
    if(!r.conquise && panneauCommune === code) ouvrirAttaque(code);""", u"""    if(r.conquise){
      // patch145 : la commune change de couleur tout de suite ; le
      // rechargement complet passe 8 s apres le dernier assaut, sans bloquer
      conquerirSurPlace(code);
      fermerPanneau();
      combatRafraichirPlusTard(true);
    }
    loadPackStatus();
    loadObjectifs();
    renderMapOverlay();
    if(!r.conquise && panneauCommune === code) ouvrirAttaque(code);""", 'lancerAssaut')
js = rempl(js, u"""async function lancerAssaut(code){""", u"""// patch145 : la commune prise passe dans ma collection sans attendre le serveur
function conquerirSurPlace(code){
  const c = othersMap.get(code);
  if(!c) return;
  othersMap.delete(code);
  const maintenant = Date.now();
  collectionMap.set(code, {
    code: c.code, nom: c.nom, dept: c.dept, pop: c.pop, lat: c.lat, lon: c.lon, tier: c.tier,
    rank: c.rank, tierSize: c.tierSize,
    acquiredAt: maintenant, bouclierDebut: 0, bouclierJusqua: 0, conquiseLe: maintenant,
    etiquette: '', photo: '', photoAuteur: '', photoLicence: '', photoSource: ''
  });
  if(c.tier && session[c.tier.id] !== undefined){ session[c.tier.id]++; session.total++; }
}

async function lancerAssaut(code){""", 'conquerirSurPlace')

ecrire('app.js', js)

# ---------- 5. fenetres plus hautes que l'ecran ----------
css = lire('style.css')
assert 'patch145' not in css
css = css.rstrip('\n') + u"""

/* ---------- patch145 : fenetre plus haute que l'ecran (LeoLesel) ----------
   Centree dans un fond fixe, une fenetre trop haute debordait par le haut :
   la croix sortait de l'ecran et on ne pouvait plus y revenir. Le fond
   defile ; la marge automatique ne centre que quand la fenetre tient. */
.fenetre-fond{ overflow-y:auto; overscroll-behavior:contain; align-items:flex-start; }
.fenetre-fond > .fenetre{ margin:auto; flex-shrink:0; }
"""
ecrire('style.css', css)
print(u'patch145 applique')
