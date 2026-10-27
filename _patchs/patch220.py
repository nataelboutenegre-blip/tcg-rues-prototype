# -*- coding: utf-8 -*-
u"""
patch220 — l'outre-mer sur la carte du Front (v2). Validé sur aperçu le 27/10.

1. Carte du Front : bouton France | Outre-mer. En outre-mer, le cadre de la
   carte montre les 5 DOM (DA lagon) colorés par propriétaire (moi en or),
   clans en liseré si le calque Clans est actif, boucliers en pointillés.
   Toucher une commune tenue ouvre LE panneau du Front existant (Attaquer,
   garnison, favori…) : aucune logique de combat en double. Commune libre :
   une bulle « elle peut sortir d'un paquet Front ». Seul le calque Clans
   reste visible en outre-mer.
2. « Voir sur la carte » (fiche, conquête, contrat) d'une commune d'outre-mer :
   ouvre la vue outre-mer, territoire agrandi, commune entourée — au lieu de
   projeter Saint-Denis hors de la carte de France.
3. Panneau : « Rang outre-mer » au lieu de « Rang national » pour un DOM.
4. Les tuiles se redessinent quand les possessions changent et à l'ouverture
   de l'onglet.

Côté base : s2-37 (chance DOM 1,5 % par carte Front, épiques au tirage Front).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a); assert c == n, ('MATCH', a[:70], 'trouve', c, 'attendu', n); return s.replace(a, b)

BLOC = r'''// ---------- patch220 : l'outre-mer sur la carte du Front ----------
// Même cadre que la carte de France : le bouton France | Outre-mer remplace la
// carte par les 5 territoires. Toucher une commune tenue ouvre LE panneau du
// Front (attaquer, défendre, garnison…) : aucune logique de combat en double.

function installerZoneFront(){
  const outils = document.querySelector('#panel-territoire .map-outils');
  const wrap = document.getElementById('mapWrap');
  if(!outils || !wrap || document.getElementById('frontZone')) return;
  outils.insertAdjacentHTML('afterbegin', '<div class="mf-zone france" id="frontZone" role="group" aria-label="Quelle carte"></div>');
  wrap.insertAdjacentHTML('beforeend', '<div class="omf" id="mapOutremer" hidden></div>');
  const om = document.getElementById('mapOutremer');
  // la carte de France écoute ces gestes sur tout le cadre : ici, ils restent à nous
  for(const t of ['wheel', 'mousedown', 'touchstart', 'pointerdown', 'gesturestart', 'dblclick'])
    om.addEventListener(t, (e) => e.stopPropagation(), { passive: true });
  om.addEventListener('click', clicOutremerFront);
  // le calque Clans se voit aussi en outre-mer : on redessine après son changement
  const calques = document.getElementById('mapCalques');
  if(calques) calques.addEventListener('click', () => setTimeout(() => { if(frontZone === 'outremer') for(const d of OMF.tuiles.keys()) omfDessiner(d); }, 0));
  document.getElementById('frontZone').addEventListener('click', (e) => {
    const b = e.target.closest('[data-fz]');
    if(b && b.dataset.fz !== frontZone) basculerZoneFront(b.dataset.fz);
  });
  majZoneFront();
}

function majZoneFront(){
  const z = document.getElementById('frontZone');
  if(!z) return;
  z.className = 'mf-zone ' + frontZone;
  z.innerHTML = [['france', 'France'], ['outremer', 'Outre-mer']].map(([id, nom]) =>
    `<button data-fz="${id}" class="${frontZone === id ? 'on' : ''}" aria-pressed="${frontZone === id}">${nom}</button>`).join('');
}

function basculerZoneFront(z, focus){
  frontZone = z;
  OMF.focus = focus || null;
  OMF.bulle = null;
  fermerPanneau();
  const wrap = document.getElementById('mapWrap');
  const om = document.getElementById('mapOutremer');
  wrap.classList.toggle('outremer', z === 'outremer');
  document.getElementById('panel-territoire').classList.toggle('outremer', z === 'outremer');
  om.hidden = z !== 'outremer';
  majZoneFront();
  if(z === 'outremer') renderOutremerFront();
  else { sizeMapWrap(window.__mapAspectRatio); demanderDessin(); }
}

function renderOutremerFront(){
  const om = document.getElementById('mapOutremer');
  if(!om || om.hidden) return;
  const focus = OM_TERR.find(t => t.dep === OMF.focus);
  const tuile = (t) => {
    return `<div class="om-tuile${focus ? ' grande' : ''}" data-omdep="${t.dep}">
      <span class="om-nom">${t.nom}</span>
      <span class="om-nb">${omfCompte(t)}</span>
      <span class="om-code" aria-hidden="true">${t.dep}</span>
      ${focus ? '' : `<button class="om-agrandir" data-omfocus="${t.dep}" aria-label="Agrandir ${t.nom}">⤢</button>`}
      <canvas aria-label="${t.nom} : touche une commune pour l'attaquer ou la défendre"></canvas>
      <div class="mf-bulle om-bulle" hidden></div>
    </div>`;
  };
  om.innerHTML = `
    ${focus ? `<button class="om-retour" data-omfocus="">← Les 5 territoires</button>` : ''}
    <div class="om-grille${focus ? ' focus' : ''}">${(focus ? [focus] : OM_TERR).map(tuile).join('')}</div>
    <div class="mf-leg omf-leg"><span><i style="background:${COULEUR_MOI}"></i>Moi</span><span><i class="omf-autres"></i>Autres joueurs</span>`
      + `<span><i class="om-vide"></i>Libre</span><span><i class="omf-bouclier"></i>Bouclier</span></div>
    <p class="omf-note">Les communes d'outre-mer sortent rarement des paquets Front. Elles rapportent les points de leur rareté, sans bonus de département.</p>`;
  OMF.tuiles.clear();
  for(const div of om.querySelectorAll('.om-tuile')){
    const dep = div.dataset.omdep;
    OMF.tuiles.set(dep, { div, cv: div.querySelector('canvas'), chemins: [] });
    chargerContours(dep).then(() => omfDessiner(dep));
  }
}

function omfDessiner(dep){
  const tu = OMF.tuiles.get(dep);
  const contours = CONTOURS.get(dep);
  if(!tu || !document.body.contains(tu.cv)) return;
  const cv = tu.cv, larg = cv.clientWidth;
  if(larg < 40) return;
  const grand = tu.div.classList.contains('grande');
  const haut = Math.round(grand ? Math.min(larg * 0.9, window.innerHeight * 0.66) : larg * 1.05);
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  cv.width = Math.round(larg * dpr); cv.height = Math.round(haut * dpr); cv.style.height = haut + 'px';
  const ctx = cv.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, larg, haut);
  for(let i = 8; i >= 1; i--){
    ctx.strokeStyle = `rgba(44,198,201,${(0.04 + i * 0.012).toFixed(3)})`;
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.ellipse(larg / 2, haut / 2 + 20, larg * 0.075 * i, haut * 0.07 * i, 0, 0, Math.PI * 2); ctx.stroke();
  }
  if(!contours || contours === 'erreur'){ tu.chemins = []; return; }
  const P = omProjection(contours, larg, haut, grand ? 18 : 10, grand ? 40 : 46);
  tu.chemins = [];
  const maintenant = Date.now();
  const clans = (typeof CALQUES !== 'undefined' && CALQUES.clans && typeof clansCarte !== 'undefined') ? clansCarte : null;
  for(const code in contours){
    const p = new Path2D();
    for(const anneau of contours[code]){
      anneau.forEach(([lon, lat], i) => { const [x, y] = P(lon, lat); i ? p.lineTo(x, y) : p.moveTo(x, y); });
      p.closePath();
    }
    tu.chemins.push([code, p]);
    const mienne = collectionMap.get(code), autre = mienne ? null : othersMap.get(code);
    const c = mienne || autre;
    ctx.fillStyle = mienne ? COULEUR_MOI : autre ? colorForPlayer(autre.joueurId) : '#14454E';
    ctx.fill(p);
    ctx.strokeStyle = c ? 'rgba(4,20,30,.9)' : 'rgba(44,198,201,.38)';
    ctx.lineWidth = grand ? 1.1 : 0.8;
    ctx.stroke(p);
    const clan = clans && c && clans.get(mienne ? window.__monId : autre.joueurId);
    if(clan){ ctx.strokeStyle = clan.couleur; ctx.lineWidth = grand ? 2.6 : 1.8; ctx.stroke(p); }
    if(c && c.bouclierJusqua > maintenant){
      ctx.save(); ctx.setLineDash([3, 3]); ctx.strokeStyle = '#fff'; ctx.lineWidth = grand ? 1.6 : 1.1; ctx.stroke(p); ctx.restore();
    }
  }
  if(OMF.bulle && OMF.bulle.dep === dep){
    const c = tu.chemins.find(([code]) => code === OMF.bulle.code);
    if(c){ ctx.strokeStyle = '#fff'; ctx.lineWidth = 2.4; ctx.stroke(c[1]); }
  }
}

function clicOutremerFront(e){
  const f = e.target.closest('[data-omfocus]');
  if(f){ OMF.focus = f.dataset.omfocus || null; fermerPanneau(); renderOutremerFront(); return; }
  const cv = e.target.closest('.om-tuile canvas');
  if(!cv) return;
  const dep = cv.parentElement.dataset.omdep;
  const tu = OMF.tuiles.get(dep);
  const r = cv.getBoundingClientRect(), px = e.clientX - r.left, py = e.clientY - r.top;
  const ctx = cv.getContext('2d'), dpr = cv.width / cv.clientWidth;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const trouve = tu.chemins.find(([, p]) => ctx.isPointInPath(p, px * dpr, py * dpr));
  const avant = OMF.bulle && OMF.bulle.dep;
  OMF.bulle = trouve ? { dep, code: trouve[0] } : null;
  for(const [d, t] of OMF.tuiles) t.div.querySelector('.om-bulle').hidden = true;
  if(avant && avant !== dep) omfDessiner(avant);
  omfDessiner(dep);
  if(!trouve){ fermerPanneau(); return; }
  if(collectionMap.has(trouve[0]) || othersMap.has(trouve[0])){
    const w = document.getElementById('mapWrap').getBoundingClientRect();
    ouvrirPanneau(trouve[0], e.clientX - w.left, e.clientY - w.top);
  } else {
    fermerPanneau();
    const b = tu.div.querySelector('.om-bulle');
    b.hidden = false;
    b.innerHTML = `<i class="mf-pastille vide"></i><div><b>Commune libre</b><span>Personne ne la tient : elle peut sortir d'un paquet Front.</span></div>`;
  }
}

// « 12 / 24 tenues · 4 à toi »
function omfCompte(t){
  let a = 0, moi = 0;
  for(const code of collectionMap.keys()) if(code.startsWith(t.dep)){ a++; moi++; }
  for(const code of othersMap.keys()) if(code.startsWith(t.dep)) a++;
  return `${a} / ${t.n} tenues${moi ? ` · <b>${moi} à toi</b>` : ''}`;
}

// les possessions ont bougé, ou l'onglet vient de s'ouvrir : on redessine sans tout reconstruire
function omfRafraichir(){
  const om = document.getElementById('mapOutremer');
  if(frontZone !== 'outremer' || !om || om.hidden) return;
  for(const [dep, tu] of OMF.tuiles){
    const t = OM_TERR.find(x => x.dep === dep), nb = tu.div.querySelector('.om-nb');
    if(t && nb) nb.innerHTML = omfCompte(t);
    omfDessiner(dep);
  }
}

// « Voir sur la carte » d'une commune d'outre-mer : son territoire, en grand, commune entourée
function montrerSurOutremerFront(code){
  const dep = String(code).slice(0, 3);
  basculerZoneFront('outremer', dep);
  OMF.bulle = { dep, code };
  omfRafraichir();
  const om = document.getElementById('mapOutremer');
  if(om && om.scrollIntoView) om.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

installerZoneFront();
'''
CSS = r'''/* patch220 — l'outre-mer sur la carte du Front */
#panel-territoire .map-outils{ flex-wrap:wrap; gap:8px; }
#panel-territoire .map-outils .mf-zone{ margin:0; }
.map-wrap.outremer{ height:auto !important; background:#0C1A31; padding:10px; overflow:visible; }
.map-wrap.outremer #mapTransform, .map-wrap.outremer #mapCanvas, .map-wrap.outremer #mapInfobulle,
.map-wrap.outremer .map-reduire, .map-wrap.outremer #mapLegende{ display:none !important; }
.omf[hidden]{ display:none; }
.omf .om-grille{ max-width:none; }
.omf-leg .omf-autres{ background:linear-gradient(90deg,#E5484D 0 33%,#8E7CF6 33% 66%,#2EC4B6 66%); }
.omf-leg .omf-bouclier{ background:none; box-shadow:inset 0 0 0 1.5px #fff; border:1px dashed #0C1A31; }
.omf-note{ margin:8px 0 0; font-size:.72rem; color:var(--brume); }
.om-nb b{ color:#F0B429; }
/* en outre-mer, seuls les clans ont un sens parmi les calques de la carte de France */
#panel-territoire.outremer #toggleOthersBtn, #panel-territoire.outremer .map-calques button:not([data-calque="clans"]),
#panel-territoire.outremer .map-note{ display:none !important; }
'''

js = lire('app.js')
assert 'patch219' in js, 'patch219 doit passer avant'
assert 'patch220' not in js

# 0. l'état de la vue outre-mer du Front, en tête (aucune zone morte)
js = rep(js, r"""const OM = { focus: null, tuiles: new Map(), bulle: null };""",
  r"""const OM = { focus: null, tuiles: new Map(), bulle: null };
let frontZone = 'france';           // patch220 : carte du Front, 'france' | 'outremer'
const OMF = { tuiles: new Map(), focus: null, bulle: null };""")

# 1. le bloc de la vue outre-mer du Front
js = rep(js, r"""// ---------- Attaquer depuis le panneau ----------""",
  BLOC + "\n" + r"""// ---------- Attaquer depuis le panneau ----------""")

# 2. rafraîchir les tuiles : possessions qui bougent, onglet qui s'ouvre
js = rep(js, r"""  if(rendreALOuverture('territoire', renderMapOverlay)) return;
""", r"""  if(rendreALOuverture('territoire', renderMapOverlay)) return;
  omfRafraichir();   // patch220
""")
js = rep(js, r"""  if(!parent.clientWidth) return;
""", r"""  if(!parent.clientWidth) return;
  if(frontZone === 'outremer') omfRafraichir();   // patch220
""")

# 3. « Voir sur la carte » d'une commune d'outre-mer
js = rep(js, r"""function voirCommuneSurCarte(entry){
""", r"""function voirCommuneSurCarte(entry){
  if(estOutremerCode(entry.code)){   // patch220 : la vue outre-mer, pas la carte de France
    if(fermerFiche) fermerFiche(null);
    const ong = document.querySelector('.tab[data-tab="territoire"]');
    if(ong) ong.click();
    requestAnimationFrame(() => requestAnimationFrame(() => montrerSurOutremerFront(entry.code)));
    return;
  }
""")
js = rep(js, r"""        setTimeout(() => centrerSurCommune(cible.lat, cible.lon), 250);""",
  r"""        setTimeout(() => estOutremerCode(cible.code) ? montrerSurOutremerFront(cible.code) : centrerSurCommune(cible.lat, cible.lon), 250);   // patch220""")

# 4. panneau : le rang d'un DOM se compte en outre-mer
js = rep(js, r"""  if(mienne && c.rank) lignes.push(['Rang national', nbFr(c.rank) + '<sup>e</sup>']);""",
  r"""  if(mienne && c.rank) lignes.push([estOutremerCode(code) ? 'Rang outre-mer' : 'Rang national', nbFr(c.rank) + '<sup>e</sup>']);   // patch220""")
ecrire('app.js', js)

css = lire('style.css')
assert 'patch220' not in css
ecrire('style.css', css.rstrip('\n') + '\n\n' + CSS)
print('patch220 OK')
