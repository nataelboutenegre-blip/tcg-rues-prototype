# -*- coding: utf-8 -*-
u"""
patch90 — Terra côté jeu : Tirage et Collection (saison 2, CACHÉ tant que
SAISON2 = false). Aperçu « terra-apercu.png » validé le 9 octobre.

En mode Terra (SAISON2 = true et mode Terra choisi) :
- Tirage : statut lu par terra_statut() (paquets gratuits Terra, achats du
  jour, solde) ; ouvrir un paquet appelle terra_ouvrir_paquet(), qui paie et
  tire en une fois ; la révélation est celle du jeu ; pas de compteur de
  communes libres (pas de pot en Terra) ; paquet teinté vert ; sous le
  paquet, le bilan « N nouvelles, N doublons » avec une étiquette par carte.
- Collection : la collection Terra (terra_collection_moi), compteur sur
  34 739, progression par rareté, pastille ×N sur les doublons, filtre
  Doublons, recherche, affichage par 120 ; « Vendre… » ouvre une feuille par
  rareté (commune et peu commune cochées par défaut) qui appelle
  terra_vendre_doublons().
- On ne change pas de mode pendant l'ouverture d'un paquet.

Le mode Front et la saison 1 ne changent pas. Serveur : s2-4-terra.sql et
s2-5-terra-jeu.sql (fermés tant que terra_ouverte() est faux).
"""
import io, os

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)

js = lire('app.js')
assert 'enTerra' not in js, u'patch90 deja applique'

# --- etat Terra, a cote du bloc SAISON2 --------------------------------------
js = rempl(js, u"let energieTimer = null;\n",
           u"""let energieTimer = null;
// patch90 : Terra
const enTerra = () => SAISON2 && modeJeu === 'terra';
const TERRA_REVENTE = { commun: 5, peucommun: 20, rare: 100, epique: 300, legendaire: 600 };
let terraPaquet = null;            // reponse de terra_ouvrir_paquet, en attente de revelation
let terraCollection = new Map();   // code -> carte de la collection Terra
let terraCharge = false;
let terraFiltre = 'tous';
let terraRecherche = '';
let terraLimite = 120;
let terraDernier = null;           // le dernier paquet ouvert, pour le bilan
""", 'etat Terra')

# --- statut des paquets -------------------------------------------------------
js = rempl(js, u"async function loadPackStatus(){\n  const { data, error } = await sb.rpc('statut_paquets');",
           u"""async function loadPackStatusTerra(){
  const { data, error } = await sb.rpc('terra_statut');
  if(error){ console.error(error); return; }
  const s = data && data[0];
  if(!s) return;
  // meme forme que statut_paquets : renderPackStatus sert aux deux modes
  packStatusCache = { jetons_actuels: Number(s.jetons), paquets_achetes_jour: s.achetes_jour,
    paquets_achetes_date: new Date().toISOString().slice(0, 10), solde: s.solde };
  packStatusFetchedAt = Date.now();
  majBascule();
  renderPackStatus();
  if(!packStatusInterval) packStatusInterval = setInterval(renderPackStatus, 5000);
}

async function loadPackStatus(){
  if(enTerra()) return loadPackStatusTerra();
  const { data, error } = await sb.rpc('statut_paquets');""", 'loadPackStatus')

# --- payer et tirer ------------------------------------------------------------
js = rempl(js, u"async function payerPaquet(type){\n",
           u"""async function payerPaquet(type){
  if(enTerra()){
    // Terra : le serveur paie et tire les 5 cartes en un seul appel
    const { data, error } = await sb.rpc('terra_ouvrir_paquet', { p_paye: type === 'achete' });
    terraPaquet = error ? null : (data || []);
    viderBilanTerra();
    return error;
  }
""", 'payerPaquet')
js = rempl(js, u"async function tirerCartesDuPaquet(nbCartes){\n  const draws = [];\n",
           u"""async function tirerCartesDuPaquet(nbCartes){
  if(enTerra()) return tirerPaquetTerra();
  const draws = [];
""", 'tirerCartesDuPaquet')
js = rempl(js, u"function paquetSansCarte(zone){",
           u"""function tirerPaquetTerra(){
  const rows = terraPaquet || [];
  terraPaquet = null;
  const draws = rows.map(row => ({
    code: row.code, nom: row.nom, dept: row.departement, pop: row.population,
    lat: row.latitude, lon: row.longitude, tier: TIERS.find(t => t.id === row.tier),
    rank: row.rang, tierSize: row.palier_total,
    terraNouvelle: !!row.nouvelle, terraExemplaires: Number(row.exemplaires) || 1,
  }));
  terraDernier = draws;
  return draws;
}

function paquetSansCarte(zone){""", 'tirerPaquetTerra')
js = rempl(js, u"function potRetirer(n){\n",
           u"function potRetirer(n){\n  if(enTerra()) return;   // pas de pot en Terra\n", 'potRetirer')

# --- chaque carte retournee ----------------------------------------------------------
js = rempl(js, u"""    collectionMap.set(draw.code, draw);
    annoncerMonument(draw.code, draw.nom);
    session[draw.tier.id]++;
    session.total++;
    renderStats();
    renderCollection();
    renderMapOverlay();
    pendingFlips--;
    if(pendingFlips <= 0){
      paquetEnCours = false;""",
           u"""    if(enTerra()) terraCarteRetournee(draw); else collectionMap.set(draw.code, draw);
    annoncerMonument(draw.code, draw.nom);
    session[draw.tier.id]++;
    session.total++;
    renderStats();
    if(!enTerra()){ renderCollection(); renderMapOverlay(); }
    pendingFlips--;
    if(pendingFlips <= 0){
      paquetEnCours = false;
      if(enTerra()) afficherBilanTerra();""", 'surCarteRetournee')

# --- on ne change pas de mode pendant une ouverture --------------------------------
js = rempl(js, u"    if(!b || b.dataset.mode === modeJeu) return;\n",
           u"    if(!b || b.dataset.mode === modeJeu) return;\n    if(paquetEnCours){ notifier({ type: 'info', titre: 'Un paquet est en cours', texte: 'Retourne tes cartes avant de changer de mode.' }); return; }\n",
           'bascule pendant paquet')

# --- en changeant de mode : statut et collection du mode ----------------------------
js = rempl(js, u"""  if(!parent || visibles.indexOf(parent) < 0){
    const tirage = document.querySelector('.tab[data-tab="tirage"]');
    if(tirage) tirage.click();
  }
  majBadgePlus();
}""",
           u"""  if(!parent || visibles.indexOf(parent) < 0){
    const tirage = document.querySelector('.tab[data-tab="tirage"]');
    if(tirage) tirage.click();
  }
  majBadgePlus();
  // patch90 : le statut des paquets et la collection suivent le mode
  if(packStatusCache) loadPackStatus();
  viderBilanTerra();
  const ouvert = document.querySelector('.tab.active[data-tab]');
  if(ouvert && ouvert.dataset.tab === 'collection' && enTerra()) ouvrirCollectionTerra();
}

// ---------- patch90 : Terra, bilan du paquet et collection ----------
function viderBilanTerra(){
  const el = document.getElementById('terraBilan');
  if(el) el.remove();
}

function terraCarteRetournee(draw){
  const e = terraCollection.get(draw.code);
  if(e) e.exemplaires = draw.terraExemplaires;
  else terraCollection.set(draw.code, { code: draw.code, nom: draw.nom, dept: draw.dept, tier: draw.tier,
    pop: draw.pop, exemplaires: draw.terraExemplaires, rank: draw.rank, tierSize: draw.tierSize });
}

function miniTerra(e){
  const nom = echapperTexte(e.nom);
  return `<div class="mini ${e.tier.id}" title="${nom} (${e.dept}) — ${e.tier.label}${e.exemplaires > 1 ? ' — ' + e.exemplaires + ' exemplaires' : ''}">
    <div class="mini-int">
      ${e.exemplaires > 1 ? `<span class="mini-ex">×${e.exemplaires}</span>` : ''}
      <div class="mini-art">${miniArtSvg(e.code, e.tier.id)}<span class="mini-dept">${echapperTexte(e.dept)}</span></div>
      <div class="mini-infos">
        <p class="mini-nom ${e.nom.length > 14 ? 'long' : ''}">${nom}</p>
        ${e.rank ? `<span class="mini-num">n° ${Number(e.rank).toLocaleString('fr-FR')}<span class="mini-total"> / ${Number(e.tierSize).toLocaleString('fr-FR')}</span></span>` : ''}
        <span class="mini-rarete">${e.tier.label}</span>
      </div>
      <div class="mini-lisere"><span></span><span></span><span></span></div>
    </div>
  </div>`;
}

function afficherBilanTerra(){
  viderBilanTerra();
  const draws = terraDernier;
  if(!draws || !draws.length) return;
  const nouv = draws.filter(d => d.terraNouvelle).length;
  const dbl = draws.length - nouv;
  const zone = document.getElementById('packZone');
  if(!zone) return;
  const el = document.createElement('div');
  el.id = 'terraBilan';
  el.className = 'tt-bilan-bloc';
  el.innerHTML = `<p class="tt-bilan">Dernier paquet : <b>${nouv} nouvelle${nouv > 1 ? 's' : ''}</b>, ${dbl} doublon${dbl > 1 ? 's' : ''}</p>
    <div class="tt-res">${trierPourRevelation(draws).map(d => `<div class="tt-c"><span class="tt-tag ${d.terraNouvelle ? 'neuf' : 'dbl'}">${d.terraNouvelle ? 'NOUVELLE' : 'DOUBLON'}</span>${miniTerra({ code: d.code, nom: d.nom, dept: d.dept, tier: d.tier, exemplaires: d.terraExemplaires, rank: d.rank, tierSize: d.tierSize })}</div>`).join('')}</div>`;
  zone.insertAdjacentElement('afterend', el);
}

async function chargerCollectionTerra(){
  const { data, error } = await sb.rpc('terra_collection_moi');
  if(error){ console.error(error); return false; }
  terraCollection = new Map();
  for(const r of data || []){
    const tier = TIERS.find(t => t.id === r.tier);
    if(!tier) continue;
    terraCollection.set(r.code, { code: r.code, nom: r.nom, dept: r.departement, tier, pop: r.population,
      exemplaires: Number(r.exemplaires) || 1, rank: r.rang, tierSize: r.palier_total });
  }
  terraCharge = true;
  return true;
}

async function ouvrirCollectionTerra(){
  const panneau = document.getElementById('panel-collection');
  if(!panneau) return;
  let el = document.getElementById('terraColl');
  if(!el){
    el = document.createElement('div');
    el.id = 'terraColl';
    panneau.prepend(el);
    el.addEventListener('click', clicCollectionTerra);
    el.addEventListener('input', (e) => {
      if(e.target.id !== 'tcRecherche') return;
      terraRecherche = e.target.value;
      terraLimite = 120;
      renderGrilleTerra();
    });
  }
  if(!terraCharge) el.innerHTML = '<p class="collection-empty">Chargement de ta collection…</p>';
  await Promise.all([terraCharge ? null : chargerCollectionTerra(), chargerTotauxPaliers()]);
  renderCollectionTerra();
}

function doublonsTerra(){
  const parTier = {};
  for(const e of terraCollection.values()){
    if(e.exemplaires < 2) continue;
    parTier[e.tier.id] = (parTier[e.tier.id] || 0) + e.exemplaires - 1;
  }
  return parTier;
}

function renderCollectionTerra(){
  const el = document.getElementById('terraColl');
  if(!el) return;
  const parTier = {};
  for(const e of terraCollection.values()) parTier[e.tier.id] = (parTier[e.tier.id] || 0) + 1;
  const tot = totauxPaliers || {};
  const totalFrance = Object.values(tot).reduce((s, l) => s + Number(l.total || 0), 0) || 34739;
  const dbl = doublonsTerra();
  const nbDbl = Object.values(dbl).reduce((s, n) => s + n, 0);
  const gainMax = Object.entries(dbl).reduce((s, [t, n]) => s + n * (TERRA_REVENTE[t] || 0), 0);
  const ordre = TIERS.filter(t => tot[t.id] || parTier[t.id]);
  el.innerHTML = `
    <div class="coll-ligne-titre"><h1>Collection</h1><span class="coll-compteur"><b>${fmtNombre(terraCollection.size)}</b> / ${fmtNombre(totalFrance)} communes</span></div>
    <div class="tc-prog" style="grid-template-columns:repeat(${Math.max(1, ordre.length)},1fr)">${ordre.map(t => {
      const n = parTier[t.id] || 0, total = tot[t.id] ? Number(tot[t.id].total) : 0;
      return `<div style="--c:${COULEURS_FILTRE[t.id]};--p:${total ? (100 * n / total).toFixed(1) : 0}%"><b>${fmtNombre(n)}</b><span>${t.label}${total ? ' · ' + fmtNombre(total) : ''}</span><i></i></div>`;
    }).join('')}</div>
    ${nbDbl ? `<div class="tc-vente"><span aria-hidden="true">🔁</span><span><b>${fmtNombre(nbDbl)} doublon${nbDbl > 1 ? 's' : ''}</b> · jusqu'à ${fmtNombre(gainMax)} pts</span><button data-tc="vendre">Vendre…</button></div>` : ''}
    <div class="coll-filtres">
      <button class="coll-filtre ${terraFiltre === 'tous' ? 'actif' : ''}" data-tcf="tous">Toutes <span class="nb">${fmtNombre(terraCollection.size)}</span></button>
      <button class="coll-filtre ${terraFiltre === 'doublons' ? 'actif' : ''}" data-tcf="doublons">Doublons <span class="nb">${fmtNombre(nbDbl)}</span></button>
      ${ordre.filter(t => parTier[t.id]).map(t => `<button class="coll-filtre ${terraFiltre === t.id ? 'actif' : ''}" data-tcf="${t.id}"><span class="point" style="background:${COULEURS_FILTRE[t.id]}"></span>${t.label} <span class="nb">${fmtNombre(parTier[t.id])}</span></button>`).join('')}
    </div>
    <input type="text" id="tcRecherche" class="bourse-search coll-recherche" placeholder="Rechercher une commune ou un département…" value="${echapperTexte(terraRecherche)}">
    <div class="coll-grille" id="tcGrille"></div>
    <div class="tc-plus-zone" id="tcPlus"></div>`;
  renderGrilleTerra();
}

function renderGrilleTerra(){
  const grille = document.getElementById('tcGrille');
  if(!grille) return;
  const liste = [...terraCollection.values()]
    .filter(e => terraFiltre === 'tous' || (terraFiltre === 'doublons' ? e.exemplaires > 1 : e.tier.id === terraFiltre))
    .filter(e => correspondRecherche(e.nom, e.dept, sansAccents(terraRecherche.trim())))
    .sort((a, b) => RANG_TIER[b.tier.id] - RANG_TIER[a.tier.id] || (b.pop || 0) - (a.pop || 0));
  grille.innerHTML = liste.length
    ? liste.slice(0, terraLimite).map(miniTerra).join('')
    : `<p class="collection-empty">${terraCollection.size ? 'Aucune commune ne correspond.' : 'Ta collection Terra est vide : ouvre un paquet dans l’onglet Tirage.'}</p>`;
  const plus = document.getElementById('tcPlus');
  if(plus) plus.innerHTML = liste.length > terraLimite
    ? `<button class="open-btn secondary" data-tc="plus">Afficher plus (${fmtNombre(liste.length - terraLimite)} de plus)</button>` : '';
}

function clicCollectionTerra(e){
  const f = e.target.closest('[data-tcf]');
  if(f){ terraFiltre = f.dataset.tcf; terraLimite = 120; renderCollectionTerra(); return; }
  const b = e.target.closest('[data-tc]');
  if(!b) return;
  if(b.dataset.tc === 'plus'){ terraLimite += 240; renderGrilleTerra(); }
  if(b.dataset.tc === 'vendre') ouvrirVenteTerra();
}

function ouvrirVenteTerra(){
  const dbl = doublonsTerra();
  const lignes = TIERS.slice().reverse().filter(t => dbl[t.id]);
  if(!lignes.length) return;
  const voile = document.createElement('div');
  voile.className = 'tc-voile';
  const f = document.createElement('div');
  f.className = 'tc-feuille';
  f.setAttribute('role', 'dialog');
  f.setAttribute('aria-modal', 'true');
  f.setAttribute('aria-labelledby', 'tcVenteTitre');
  f.innerHTML = `<h3 id="tcVenteTitre">Vendre mes doublons</h3><p>On garde toujours un exemplaire de chaque commune.</p>
    ${lignes.map(t => `<label class="tc-ligne"><input type="checkbox" value="${t.id}" ${t.id === 'commun' || t.id === 'peucommun' ? 'checked' : ''}>
      <i class="pt" style="background:${COULEURS_FILTRE[t.id]}"></i>${t.label} <em>× ${fmtNombre(dbl[t.id])} · ${TERRA_REVENTE[t.id]} pts</em><b>+${fmtNombre(dbl[t.id] * TERRA_REVENTE[t.id])}</b></label>`).join('')}
    <button class="tc-ok" id="tcVenteOk"></button>
    <button class="tc-annuler" id="tcVenteNon">Annuler</button>`;
  document.body.append(voile, f);
  const fermer = () => { voile.remove(); f.remove(); };
  const majBouton = () => {
    const choix = [...f.querySelectorAll('input:checked')].map(i => i.value);
    const n = choix.reduce((s, t) => s + dbl[t], 0);
    const g = choix.reduce((s, t) => s + dbl[t] * TERRA_REVENTE[t], 0);
    const ok = f.querySelector('#tcVenteOk');
    ok.disabled = n === 0;
    ok.textContent = n ? `Vendre ${fmtNombre(n)} doublon${n > 1 ? 's' : ''} · +${fmtNombre(g)} points` : 'Coche au moins une rareté';
    return choix;
  };
  majBouton();
  f.addEventListener('change', majBouton);
  voile.addEventListener('click', fermer);
  f.querySelector('#tcVenteNon').addEventListener('click', fermer);
  f.querySelector('#tcVenteOk').addEventListener('click', async (ev) => {
    const choix = majBouton();
    if(!choix.length) return;
    ev.target.disabled = true;
    const { data, error } = await sb.rpc('terra_vendre_doublons', { p_tiers: choix });
    fermer();
    if(error){ notifier({ type: 'erreur', titre: 'Vente impossible', texte: messageLisible(error.message) }); return; }
    const r = data && data[0];
    for(const e of terraCollection.values()) if(choix.includes(e.tier.id) && e.exemplaires > 1) e.exemplaires = 1;
    if(r && packStatusCache){ packStatusCache.solde = r.solde; majBascule(); }
    notifier({ type: 'succes', titre: 'Doublons vendus', texte: r ? `${fmtNombre(r.vendus)} doublon${r.vendus > 1 ? 's' : ''} · +${fmtNombre(r.gain)} points` : '' });
    renderCollectionTerra();
  });
}""", 'fonctions Terra')

# --- l'onglet Collection en mode Terra ------------------------------------------------
js = rempl(js, u"    if(tab.dataset.tab === 'monuments') loadMonuments();\n",
           u"    if(tab.dataset.tab === 'monuments') loadMonuments();\n    if(tab.dataset.tab === 'collection' && enTerra()) ouvrirCollectionTerra();\n",
           'onglet collection')

ecrire('app.js', js)

# =============================================================================
css = lire('style.css')
assert 'tc-prog' not in css, u'patch90 deja applique (css)'
css += u'''
/* =====================================================================
   patch90 — Terra : Tirage et Collection (n'apparait qu'en mode Terra)
   ===================================================================== */
body.mode-terra #potLibres{ display:none !important; }
body.mode-terra .paquet .paquet-motif{ filter: hue-rotate(-62deg) saturate(1.05); }
#terraColl{ display:none; width:100%; min-width:0; }
body.mode-terra #terraColl{ display:block; }
body.mode-terra #panel-collection > :not(#terraColl){ display:none !important; }
.mini-ex{ position:absolute; top:5px; right:5px; z-index:4; background:#0F1F38; color:#fff; font-weight:700; font-size:.66rem;
  padding:2px 6px; border-radius:999px; box-shadow:0 0 0 1.5px rgba(255,255,255,.85); font-variant-numeric:tabular-nums; }
.tc-prog{ display:grid; grid-template-columns:repeat(5,1fr); gap:6px; width:100%; margin:4px 0 12px; }
.tc-prog div{ background:rgba(169,188,212,.07); border:1px solid rgba(169,188,212,.14); border-radius:10px; padding:7px 6px 8px; min-width:0; }
.tc-prog b{ display:block; color:#fff; font-size:.82rem; font-variant-numeric:tabular-nums; white-space:nowrap; }
.tc-prog span{ display:block; color:var(--brume); font-size:.6rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.tc-prog i{ display:block; height:4px; border-radius:2px; margin-top:6px; background:rgba(169,188,212,.18); overflow:hidden; }
.tc-prog i::after{ content:''; display:block; height:100%; width:var(--p); min-width:2px; background:var(--c); }
.tc-vente{ display:flex; align-items:center; gap:10px; width:100%; margin:0 0 12px; padding:10px 12px; border-radius:12px;
  background:linear-gradient(160deg,rgba(53,185,126,.16),rgba(53,185,126,.06)); border:1px solid rgba(53,185,126,.4); color:#E8F6EE; font-size:.84rem; }
.tc-vente b{ color:#5FD39D; }
.tc-vente button{ margin-left:auto; border:none; border-radius:999px; padding:7px 12px; background:#35B97E; color:#0B2A1D; font:inherit; font-weight:700; font-size:.78rem; cursor:pointer; }
#terraColl .coll-grille{ width:100%; }
.tc-plus-zone{ display:flex; justify-content:center; margin:14px 0 4px; }
.tc-voile{ position:fixed; inset:0; background:rgba(5,12,24,.6); z-index:79; }
.tc-feuille{ position:fixed; left:0; right:0; bottom:0; z-index:80; max-width:520px; margin:0 auto; background:#122743;
  border-top:1px solid rgba(169,188,212,.2); border-radius:18px 18px 0 0; padding:14px 16px calc(22px + env(safe-area-inset-bottom));
  box-shadow:0 -14px 40px rgba(0,0,0,.55); color:#fff; }
.tc-feuille h3{ margin:4px 0 4px; font-family:var(--titre); font-size:1.4rem; }
.tc-feuille p{ margin:0 0 12px; color:var(--brume); font-size:.8rem; }
.tc-ligne{ display:flex; align-items:center; gap:10px; padding:10px 4px; border-bottom:1px solid rgba(169,188,212,.1); font-size:.88rem; cursor:pointer; }
.tc-ligne input{ accent-color:#35B97E; width:18px; height:18px; }
.tc-ligne em{ font-style:normal; color:var(--brume); font-size:.78rem; }
.tc-ligne b{ margin-left:auto; color:#5FD39D; }
.tc-ligne .pt{ width:9px; height:9px; border-radius:50%; flex:none; }
.tc-ok{ width:100%; margin-top:14px; border:none; border-radius:12px; padding:13px; background:#35B97E; color:#0B2A1D; font:inherit; font-weight:800; font-size:.95rem; cursor:pointer; }
.tc-ok:disabled{ opacity:.5; cursor:default; }
.tc-annuler{ width:100%; margin-top:8px; border:none; background:none; color:var(--brume); font:inherit; font-size:.85rem; padding:8px; cursor:pointer; }
.tt-bilan-bloc{ width:100%; min-width:0; max-width:620px; }
.tt-bilan{ width:100%; margin:18px 0 0; font-size:.82rem; color:var(--brume); }
.tt-bilan b{ color:#fff; }
.tt-res{ display:grid; grid-template-columns:repeat(5,1fr); gap:6px; width:100%; margin-top:14px; padding-top:4px; }
.tt-c{ position:relative; min-width:0; }
.tt-c .mini{ width:100%; }
.tt-c .mini-num{ display:none; }
.tt-tag{ position:absolute; left:50%; transform:translateX(-50%); top:-9px; z-index:5; white-space:nowrap; font-size:.58rem; font-weight:800;
  letter-spacing:.04em; padding:2px 7px; border-radius:999px; }
.tt-tag.neuf{ background:#35B97E; color:#0B2A1D; }
.tt-tag.dbl{ background:#1F3A60; color:#C7D6EA; box-shadow:0 0 0 1px rgba(169,188,212,.3); }
'''
ecrire('style.css', css)
print(u'patch90 : OK')
