# -*- coding: utf-8 -*-
u"""
patch76 — Radar : mode entraînement (maquette validée le 6 octobre).

- QG : bouton « S'entraîner » à côté de « Lancer un duel » (pastille
  « Nouveau » jusqu'au premier essai).
- Réglages : communes (Grandes villes 50 000+, Toutes 15 000+, Une région
  5 000+) et chrono (15 s ou sans chrono). Derniers réglages retenus.
- Partie : 5 communes au hasard, mêmes règles de distance que le duel
  (plafond 1 000 km, 1 000 km si le temps est écoulé). En mode région, la
  carte est zoomée sur la région et montre ses départements.
- Fin : le résumé des duels (carte, manches), avec le record personnel
  par réglage, gardé sur l'appareil. Rejouer / Réglages / QG.
- Rien côté serveur : pas d'Elo, pas de base. Les communes viennent de
  data/radar-entrainement.json, fabriqué ici depuis data/communes.json
  (métropole, 5 000 habitants et plus, sans les arrondissements, comme
  le Radar classé).
"""
import io, os, json, re

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

# ---------------------------------------------------------------------
# 0. Les communes de l'entraînement
# ---------------------------------------------------------------------
metro = re.compile(r'^(0[1-9]|[1-8][0-9]|9[0-5]|2A|2B)$')
toutes = json.loads(lire('data/communes.json'))
liste = [[c[0], c[1], c[2], round(c[4], 4), round(c[5], 4)] for c in toutes
         if metro.match(c[1]) and c[2] >= 5000 and 'rrondissement' not in c[0] and c[4] and c[5]]
ecrire('data/radar-entrainement.json', json.dumps(liste, ensure_ascii=False, separators=(',', ':')))
print(u'radar-entrainement.json : %d communes' % len(liste))

# ---------------------------------------------------------------------
# 1. index.html
# ---------------------------------------------------------------------
h = lire('index.html')
h = rempl(h,
u'''<button type="button" class="qg-btn plein" id="qgLancer">Lancer un duel</button>''',
u'''<button type="button" class="qg-btn plein" id="qgLancer">Lancer un duel</button><button type="button" class="qg-btn" id="qgEntr">S'entraîner</button>''',
'bouton QG')
h = rempl(h,
u'''      <div class="rd-ecran" id="rdFin" hidden></div>''',
u'''      <div class="rd-ecran" id="rdEntr" hidden></div>
      <div class="rd-ecran" id="rdFin" hidden></div>''', 'ecran entrainement')
ecrire('index.html', h)

# ---------------------------------------------------------------------
# 2. app.js
# ---------------------------------------------------------------------
js = lire('app.js')

js = rempl(js,
u'''function radarMontrer(id){
  for(const x of ['rdVs', 'rdManche', 'rdFin']) document.getElementById(x).hidden = x !== id;''',
u'''function radarMontrer(id){
  for(const x of ['rdVs', 'rdManche', 'rdEntr', 'rdFin']) document.getElementById(x).hidden = x !== id;''', 'radarMontrer')

# un duel remet le mode classé
js = rempl(js,
u'''document.getElementById('qgLancer').addEventListener('click', async (ev) => {
  const b = ev.currentTarget;
  b.disabled = true;''',
u'''document.getElementById('qgLancer').addEventListener('click', async (ev) => {
  const b = ev.currentTarget;
  b.disabled = true;
  radarModeEntr = false; clearInterval(radarChrono);''', 'duel mode')
js = rempl(js,
u'''async function radarSuite(){
  if(!radarPartie) return;''',
u'''async function radarSuite(){
  if(!radarPartie) return;
  radarModeEntr = false;''', 'radarSuite mode')

# chrono : à zéro, on envoie selon le mode ; en duel, l'affichage reprend sa forme
js = rempl(js,
u'''  const el = document.getElementById('rdChrono');
  el.textContent = r;
  el.classList.toggle('court', r <= 5);
  // a zero, on envoie ce qu'on a (le point pose, ou rien)
  if(r === 0 && !radarRevele && !radarEnvoi) radarViser();''',
u'''  const el = document.getElementById('rdChrono');
  el.classList.remove('libre');
  el.textContent = r;
  el.classList.toggle('court', r <= 5);
  // a zero, on envoie ce qu'on a (le point pose, ou rien)
  if(r === 0 && !radarRevele && !radarEnvoi){ if(radarModeEntr) entrViser(); else radarViser(); }''', 'radarTic')

js = rempl(js,
u'''document.getElementById('rdValider').addEventListener('click', () => {
  if(!radarRevele){ if(radarPin) radarViser(); return; }
  if(radarPartie.fini) radarResultat(); else radarSuite();
});''',
u'''document.getElementById('rdValider').addEventListener('click', () => {
  if(radarModeEntr){
    if(!radarRevele){ if(radarPin) entrViser(); return; }
    if(entr.coups.length >= ENTR_MANCHES) entrFin(); else entrManche();
    return;
  }
  if(!radarRevele){ if(radarPin) radarViser(); return; }
  if(radarPartie.fini) radarResultat(); else radarSuite();
});''', 'valider')

# la carte de la manche : vue zoomée sur la région à l'entraînement
js = rempl(js,
u'''  const contour = FRANCE_OUTLINE || cdjContour;
  svg.setAttribute('viewBox', `0 0 ${cdjBornes.w.toFixed(2)} ${cdjBornes.h.toFixed(2)}`);
  const ray = cdjBornes.w / 80;
  let h = '';
  for(const a of contour) h += `<path class="cdj-fr" d="M${a.map(([lo, la]) => cdjPx(lo, la).join(',')).join('L')}Z"/>`;
  if(manche){
    const [cx, cy] = cdjPx(+manche.lon, +manche.lat);''',
u'''  const contour = FRANCE_OUTLINE || cdjContour;
  const vue = radarModeEntr && entr.vue ? entr.vue : null;
  svg.setAttribute('viewBox', vue ? `${vue.x} ${vue.y} ${vue.w} ${vue.h}` : `0 0 ${cdjBornes.w.toFixed(2)} ${cdjBornes.h.toFixed(2)}`);
  svg.classList.toggle('rd-zoom', !!vue);
  const ray = (vue ? vue.w : cdjBornes.w) / 80;
  let h = '';
  for(const a of contour) h += `<path class="cdj-fr" d="M${a.map(([lo, la]) => cdjPx(lo, la).join(',')).join('L')}Z"/>`;
  if(vue && entr.depsPath) h += `<path class="rd-dep" d="${entr.depsPath}"/>`;
  if(manche){
    const [cx, cy] = cdjPx(+manche.lon, +manche.lat);''', 'radarDessiner vue')

# le résumé : en-tête et boutons de l'entraînement, vue zoomée
js = rempl(js,
u'''  let tete;
  if(adv){
    const mot = p.resultat === 'victoire' ? 'Victoire' : p.resultat === 'defaite' ? 'Défaite' : 'Égalité';''',
u'''  let tete;
  if(p.entr){
    const e = p.entr;
    tete = `<span class="rd-etiq">Entraînement · ${echapperTexte(e.label)}</span>
      <div class="rd-entr-total"><h2>${fmt(p.total_km)} km</h2>${e.nouveau ? '<span class="rd-record-ok">Nouveau record !</span>' : ''}</div>
      <p class="qg-petit">${e.avant == null ? 'Premier record pour ce réglage.' : (e.nouveau ? `Ancien record : ${fmt(e.avant)} km` : `Ton record : ${fmt(e.avant)} km`)} · ${e.chrono ? '15 secondes' : 'sans chrono'}</p>`;
  } else if(adv){
    const mot = p.resultat === 'victoire' ? 'Victoire' : p.resultat === 'defaite' ? 'Défaite' : 'Égalité';''', 'resume tete')
js = rempl(js,
u'''        <div class="qg-actions"><button type="button" class="qg-btn plein" id="rdRetour">Retour au QG</button>${partage ? '<button type="button" class="qg-btn" id="rdCopier">Copier pour Discord</button>' : ''}</div></div>
    </div>`;''',
u'''        <div class="qg-actions">${p.entr
          ? '<button type="button" class="qg-btn plein" id="rdRejouer">Rejouer</button><button type="button" class="qg-btn" id="rdReglages">Réglages</button><button type="button" class="qg-btn" id="rdRetour">QG</button>'
          : `<button type="button" class="qg-btn plein" id="rdRetour">Retour au QG</button>${partage ? '<button type="button" class="qg-btn" id="rdCopier">Copier pour Discord</button>' : ''}`}</div></div>
    </div>`;
  if(p.entr){
    document.getElementById('rdRejouer').onclick = () => entrCommencer();
    document.getElementById('rdReglages').onclick = () => entrAfficherReglages();
  }''', 'resume boutons')
js = rempl(js,
u'''  const contour = FRANCE_OUTLINE || cdjContour;
  svg.setAttribute('viewBox', `0 0 ${cdjBornes.w.toFixed(2)} ${cdjBornes.h.toFixed(2)}`);
  const ray = cdjBornes.w / 80;
  let h = '';
  for(const a of contour) h += `<path class="cdj-fr" d="M${a.map(([lo, la]) => cdjPx(lo, la).join(',')).join('L')}Z"/>`;
  // la manche choisie en dernier''',
u'''  const contour = FRANCE_OUTLINE || cdjContour;
  const vue = p.vue || null;
  svg.setAttribute('viewBox', vue ? `${vue.x} ${vue.y} ${vue.w} ${vue.h}` : `0 0 ${cdjBornes.w.toFixed(2)} ${cdjBornes.h.toFixed(2)}`);
  const ray = (vue ? vue.w : cdjBornes.w) / 80;
  let h = '';
  for(const a of contour) h += `<path class="cdj-fr" d="M${a.map(([lo, la]) => cdjPx(lo, la).join(',')).join('L')}Z"/>`;
  if(vue && p.depsPath) h += `<path class="rd-dep" d="${p.depsPath}"/>`;
  // la manche choisie en dernier''', 'resume vue')

# en revenant au QG, un chrono d'entraînement en cours s'arrête
js = rempl(js,
u'''async function ouvrirQG(){
  renderQG();''',
u'''async function ouvrirQG(){
  if(radarModeEntr) clearInterval(radarChrono);
  majBoutonEntr();
  renderQG();''', 'ouvrirQG')

# le mode entraînement lui-même, à la fin du fichier
js = rempl(js, u'''\ninitAuth();''', u'''
// ----- l'entrainement Radar (patch76) : tout se joue dans le navigateur -----
const ENTR_MANCHES = 5, ENTR_SECONDES = 15, ENTR_PENALITE = 1000;
const ENTR_REGIONS = {
  'Auvergne-Rhône-Alpes': ['01','03','07','15','26','38','42','43','63','69','73','74'],
  'Bourgogne-Franche-Comté': ['21','25','39','58','70','71','89','90'],
  'Bretagne': ['22','29','35','56'],
  'Centre-Val de Loire': ['18','28','36','37','41','45'],
  'Corse': ['2A','2B'],
  'Grand Est': ['08','10','51','52','54','55','57','67','68','88'],
  'Hauts-de-France': ['02','59','60','62','80'],
  'Île-de-France': ['75','77','78','91','92','93','94','95'],
  'Normandie': ['14','27','50','61','76'],
  'Nouvelle-Aquitaine': ['16','17','19','23','24','33','40','47','64','79','86','87'],
  'Occitanie': ['09','11','12','30','31','32','34','46','48','65','66','81','82'],
  'Pays de la Loire': ['44','49','53','72','85'],
  "Provence-Alpes-Côte d'Azur": ['04','05','06','13','83','84'],
};
const ENTR_NIVEAUX = {
  grandes: { nom: 'Grandes villes', aide: '50 000 hab. et plus', min: 50000 },
  toutes:  { nom: 'Toutes', aide: '15 000 hab. et plus', min: 15000 },
  region:  { nom: 'Une région', aide: '5 000 hab. et plus', min: 5000 },
};
let radarModeEntr = false;
let entr = { niveau: 'toutes', region: 'Île-de-France', chrono: true, communes: [], coups: [], vue: null, depsPath: '', derniers: [] };
let entrListe = null, entrListeEnCours = null, entrDeps = null;

function entrLireLocal(cle, defaut){ try { const v = localStorage.getItem(cle); return v ? JSON.parse(v) : defaut; } catch(e){ return defaut; } }
function entrEcrireLocal(cle, v){ try { localStorage.setItem(cle, JSON.stringify(v)); } catch(e){} }
{
  const r = entrLireLocal('tf-radar-entr-reglages', null);
  if(r && ENTR_NIVEAUX[r.niveau]) entr.niveau = r.niveau;
  if(r && ENTR_REGIONS[r.region]) entr.region = r.region;
  if(r && typeof r.chrono === 'boolean') entr.chrono = r.chrono;
}
function majBoutonEntr(){
  const b = document.getElementById('qgEntr');
  if(b) b.classList.toggle('neuf', !entrLireLocal('tf-radar-entr-vu', false));
}
majBoutonEntr();

function entrCharger(){
  if(entrListe) return Promise.resolve(entrListe);
  if(!entrListeEnCours){
    entrListeEnCours = fetch('data/radar-entrainement.json', { cache: 'force-cache' })
      .then(r => { if(!r.ok) throw new Error('liste'); return r.json(); })
      .then(l => (entrListe = l.map(([nom, dept, pop, lat, lon]) => ({ nom, dept, pop, lat, lon }))))
      .catch(err => { entrListeEnCours = null; throw err; });
  }
  return entrListeEnCours;
}
function entrChargerDeps(){
  if(entrDeps) return Promise.resolve(entrDeps);
  return fetch('contours-departements.json', { cache: 'force-cache' }).then(r => r.json()).then(d => (entrDeps = d)).catch(() => null);
}
function entrPool(niveau = entr.niveau, region = entr.region){
  if(!entrListe) return [];
  const min = ENTR_NIVEAUX[niveau].min;
  const deps = niveau === 'region' ? new Set(ENTR_REGIONS[region]) : null;
  return entrListe.filter(c => c.pop >= min && (!deps || deps.has(c.dept)));
}
function entrCle(){ return `${entr.niveau}|${entr.niveau === 'region' ? entr.region : ''}|${entr.chrono ? '15' : 'libre'}`; }
function entrLabel(){ return entr.niveau === 'region' ? entr.region : ENTR_NIVEAUX[entr.niveau].nom; }
function entrRecord(){ const r = entrLireLocal('tf-radar-records', {}); return r[entrCle()] == null ? null : Number(r[entrCle()]); }

document.getElementById('qgEntr').addEventListener('click', () => {
  entrEcrireLocal('tf-radar-entr-vu', true); majBoutonEntr();
  const t = document.querySelector('.tab[data-tab="radar"]'); if(t) t.click();
  entrAfficherReglages();
});

async function entrAfficherReglages(){
  radarModeEntr = false; clearInterval(radarChrono);
  radarMontrer('rdEntr');
  const ecran = document.getElementById('rdEntr');
  const rendre = () => {
    const pret = !!entrListe;
    const n = pret ? entrPool().length : 0;
    const rec = entrRecord();
    ecran.innerHTML = `<div class="rd-bloc rd-entr">
      <span class="rd-etiq">Entraînement</span>
      <p class="qg-petit">Sans classement ni Elo : joue autant que tu veux pour apprendre la carte.</p>
      <div><p class="rd-label">Communes</p>
        <div class="rd-seg trois">${Object.entries(ENTR_NIVEAUX).map(([k, v]) =>
          `<button type="button" data-niveau="${k}" class="${entr.niveau === k ? 'actif' : ''}" aria-pressed="${entr.niveau === k}"><b>${v.nom}</b><span>${pret && k !== 'region' ? `${entrPool(k).length} communes` : v.aide}</span></button>`).join('')}</div>
        ${entr.niveau === 'region' ? `<select id="rdEntrRegion" class="rd-select" aria-label="Région">${Object.keys(ENTR_REGIONS).map(r =>
          `<option value="${echapperTexte(r)}" ${r === entr.region ? 'selected' : ''}>${echapperTexte(r)}${pret ? ` · ${entrPool('region', r).length} communes` : ''}</option>`).join('')}</select>` : ''}
      </div>
      <div><p class="rd-label">Chrono</p>
        <div class="rd-seg deux">
          <button type="button" data-chrono="1" class="${entr.chrono ? 'actif' : ''}" aria-pressed="${entr.chrono}"><b>15 secondes</b><span>comme en duel</span></button>
          <button type="button" data-chrono="0" class="${!entr.chrono ? 'actif' : ''}" aria-pressed="${!entr.chrono}"><b>Sans chrono</b><span>prends ton temps</span></button>
        </div></div>
      <div class="rd-record"><span>Ton record ici</span><b>${rec == null ? '—' : `${Number(rec).toLocaleString('fr-FR')} km`}</b></div>
      <div class="qg-actions"><button type="button" class="qg-btn plein" id="rdEntrGo" ${pret && n >= ENTR_MANCHES ? '' : 'disabled'}>${pret ? 'Commencer' : 'Chargement…'}</button><button type="button" class="qg-btn" id="rdEntrRetour">Retour</button></div>
    </div>`;
    const garder = () => entrEcrireLocal('tf-radar-entr-reglages', { niveau: entr.niveau, region: entr.region, chrono: entr.chrono });
    ecran.querySelectorAll('[data-niveau]').forEach(b => b.onclick = () => { entr.niveau = b.dataset.niveau; garder(); rendre(); });
    ecran.querySelectorAll('[data-chrono]').forEach(b => b.onclick = () => { entr.chrono = b.dataset.chrono === '1'; garder(); rendre(); });
    const sel = document.getElementById('rdEntrRegion');
    if(sel) sel.onchange = () => { entr.region = sel.value; garder(); rendre(); };
    document.getElementById('rdEntrGo').onclick = () => entrCommencer();
    document.getElementById('rdEntrRetour').onclick = () => { const t = document.querySelector('.tab[data-tab="qg"]'); if(t) t.click(); };
  };
  rendre();
  if(!entrListe){
    try { await Promise.all([entrCharger(), loadOutline()]); rendre(); }
    catch(e){ notifier({ type: 'erreur', titre: 'Radar', texte: 'Impossible de charger les communes. Recharge la page.' }); }
  }
}

async function entrCommencer(){
  const pool = entrPool();
  if(pool.length < ENTR_MANCHES) return;
  // 5 communes au hasard, en évitant celles de la partie précédente quand c'est possible
  const dispo = pool.length >= ENTR_MANCHES * 3 ? pool.filter(c => !entr.derniers.includes(c.nom + c.dept)) : pool.slice();
  const choix = [];
  while(choix.length < ENTR_MANCHES && dispo.length){ choix.push(dispo.splice(Math.floor(Math.random() * dispo.length), 1)[0]); }
  entr.communes = choix; entr.coups = []; entr.derniers = choix.map(c => c.nom + c.dept);
  entr.vue = null; entr.depsPath = '';
  if(entr.niveau === 'region'){
    // le cadre : les communes de la région, avec une marge
    radarAssurerBornes();
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    for(const c of pool){ const [x, y] = cdjPx(c.lon, c.lat).map(Number); x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
    let w = x1 - x0, h = y1 - y0; const m = Math.max(w, h) * 0.12 + 0.15;
    if(w < h * 0.6){ x0 -= (h * 0.6 - w) / 2; w = h * 0.6; }
    if(h < w * 0.6){ y0 -= (w * 0.6 - h) / 2; h = w * 0.6; }
    entr.vue = { x: +(x0 - m).toFixed(3), y: +(y0 - m).toFixed(3), w: +(w + 2 * m).toFixed(3), h: +(h + 2 * m).toFixed(3) };
    const deps = await entrChargerDeps();
    if(deps){
      let d = '';
      for(const code of ENTR_REGIONS[entr.region]){
        for(const poly of (deps[code] || [])){
          const anneau = typeof poly[0][0] === 'number' ? poly : poly[0];
          d += 'M' + anneau.map(([lo, la]) => cdjPx(lo, la).join(',')).join('L') + 'Z';
        }
      }
      entr.depsPath = d;
    }
  }
  radarModeEntr = true;
  entrManche();
}

function entrManche(){
  const n = entr.coups.length, c = entr.communes[n];
  radarPin = null; radarRevele = false; radarEnvoi = false;
  radarMontrer('rdManche');
  document.getElementById('rdNum').textContent = `Commune ${n + 1} sur ${ENTR_MANCHES} · entraînement`;
  document.getElementById('rdNom').textContent = c.nom;
  document.getElementById('rdPoints').innerHTML = Array.from({ length: ENTR_MANCHES }, (_, i) =>
    `<i class="${i < n ? 'fait' : i === n ? 'encours' : ''}"></i>`).join('');
  document.getElementById('rdVerdict').innerHTML = '<span>Clique sur la carte, puis valide.</span>';
  const v = document.getElementById('rdValider');
  v.disabled = true; v.textContent = 'Valider';
  radarDessiner();
  clearInterval(radarChrono);
  const el = document.getElementById('rdChrono');
  if(entr.chrono){
    radarFin = Date.now() + ENTR_SECONDES * 1000;
    radarChrono = setInterval(radarTic, 200);
    radarTic();
  } else {
    el.classList.remove('court'); el.classList.add('libre');
    el.innerHTML = '∞<small>sans chrono</small>';
  }
}

function entrKm(lat1, lon1, lat2, lon2){
  const r = (x) => x * Math.PI / 180;
  const h = Math.sin(r(lat2 - lat1) / 2) ** 2 + Math.cos(r(lat1)) * Math.cos(r(lat2)) * Math.sin(r(lon2 - lon1) / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}

function entrViser(){
  if(radarRevele || !radarModeEntr) return;
  clearInterval(radarChrono);
  const c = entr.communes[entr.coups.length], p = radarPin;
  const moi = p ? { lon: p[0], lat: p[1], km: Math.min(ENTR_PENALITE, Math.round(entrKm(p[1], p[0], c.lat, c.lon))) }
                : { lon: null, lat: null, km: ENTR_PENALITE };
  const m = { nom: c.nom, dept: c.dept, lat: c.lat, lon: c.lon, moi, lui: null };
  entr.coups.push(m);
  radarRevele = true;
  document.getElementById('rdVerdict').innerHTML =
    `<b>${p ? '' : 'Temps écoulé · '}${moi.km.toLocaleString('fr-FR')} km</b><span>${echapperTexte(c.nom)} (${echapperTexte(c.dept)})</span>`;
  const v = document.getElementById('rdValider');
  v.disabled = false;
  v.textContent = entr.coups.length >= ENTR_MANCHES ? 'Voir le résultat' : 'Commune suivante';
  radarDessiner(m);
}

function entrFin(){
  clearInterval(radarChrono);
  radarModeEntr = false;
  const total = entr.coups.reduce((s, m) => s + m.moi.km, 0);
  const records = entrLireLocal('tf-radar-records', {});
  const avant = records[entrCle()] == null ? null : Number(records[entrCle()]);
  const nouveau = avant == null || total < avant;
  if(nouveau){ records[entrCle()] = total; entrEcrireLocal('tf-radar-records', records); }
  radarAfficherResume({
    jouees: entr.coups, total_km: total, adversaire: null, resultat: null, regle_le: null,
    entr: { label: entrLabel(), avant, nouveau: nouveau && avant != null, chrono: entr.chrono },
    vue: entr.vue, depsPath: entr.depsPath,
  }, true);
}

initAuth();''', 'entrainement')

ecrire('app.js', js)

# ---------------------------------------------------------------------
# 3. style.css
# ---------------------------------------------------------------------
css = lire('style.css')
MARQUE = u'/* ---------- Radar : entraînement (patch76) ---------- */'
assert MARQUE not in css, u'patch76 déjà passé'
css = css.rstrip('\n') + u'\n\n' + MARQUE + u'''
#qgEntr{ position:relative; }
#qgEntr.neuf::after{ content:'Nouveau'; position:absolute; top:-9px; right:-8px; background: var(--c-peucommun); color:#fff;
  font-size:10px; font-weight:700; padding:2px 6px; border-radius:999px; text-transform:uppercase; letter-spacing:.04em; }
.rd-etiq{ align-self:flex-start; display:inline-block; font-size:11px; font-weight:700; letter-spacing:.1em; text-transform:uppercase;
  color: var(--c-legendaire); background: rgba(240,180,41,.12); border:1px solid rgba(240,180,41,.35); padding:3px 9px; border-radius:999px; }
.rd-entr{ max-width:640px; }
.rd-label{ margin:0 0 8px; font-size:12px; letter-spacing:.08em; text-transform:uppercase; color: var(--brume); font-weight:700; }
.rd-seg{ display:grid; gap:8px; }
.rd-seg.trois{ grid-template-columns:repeat(3, 1fr); }
.rd-seg.deux{ grid-template-columns:1fr 1fr; }
.rd-seg button{ font:inherit; color:#fff; background: var(--nuit); border:1px solid rgba(169,188,212,.25); border-radius:12px;
  padding:10px 9px; text-align:left; cursor:pointer; min-width:0; }
.rd-seg button:hover{ border-color: rgba(169,188,212,.6); }
.rd-seg button b{ display:block; font-family: var(--titre); font-size:19px; font-weight:800; text-transform:uppercase; line-height:1.05; }
.rd-seg button span{ display:block; font-size:12px; color: var(--brume); margin-top:3px; }
.rd-seg button.actif{ border-color: var(--c-legendaire); background: rgba(240,180,41,.12); box-shadow: inset 0 0 0 1px var(--c-legendaire); }
.rd-select{ width:100%; margin-top:8px; font:inherit; font-size:15px; color:#fff; background: var(--nuit);
  border:1px solid var(--c-legendaire); border-radius:10px; padding:10px 12px; }
.rd-record{ display:flex; justify-content:space-between; align-items:center; background: rgba(255,255,255,.04); border-radius:10px;
  padding:10px 12px; font-size:14px; color: var(--brume); }
.rd-record b{ font-family: var(--titre); font-size:24px; color:#fff; }
.rd-chrono.libre{ font-size:30px; line-height:1; text-align:right; }
.rd-chrono.libre small{ display:block; font-family: var(--texte); font-size:12px; font-weight:400; color: var(--brume); }
.rd-dep{ fill:#22416B; stroke: rgba(169,188,212,.55); stroke-width:.8; vector-effect: non-scaling-stroke; }
svg.rd-zoom .cdj-fr{ fill:#172D4C; }
.rd-entr-total{ display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }
.rd-entr-total h2{ margin:0; }
.rd-record-ok{ background: var(--c-peucommun); color:#fff; font-family: var(--titre); font-weight:800; font-size:20px;
  text-transform:uppercase; padding:4px 12px; border-radius:999px; }
@media (max-width: 380px){ .rd-seg button b{ font-size:16px; } }
'''
ecrire('style.css', css)
print(u'patch76 : OK')
