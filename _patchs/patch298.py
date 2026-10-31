# patch298 : le Marché (31/10), aperçu validé par Nataël (« C'est parfait ! »)
# En Terra, Bourse, Échange et Contrat deviennent un seul onglet « Marché » (à la place de
# « Contrat » dans la barre du bas ; Bourse et Échange quittent le menu Plus).
# Volets : Mes doublons · Bourse · Échange · Contrat. « Mes doublons » s'ouvre depuis la barre :
# résumé (combien, valeur au jeu), À faire (échanges reçus, contrats possibles, communes qui
# te manquent en vente, tes annonces), puis une ligne par rareté (Contrat, Vendre, Bourse, Échanger).
# Rien ne change dans les règles ni dans les écrans Bourse, Échange et Contrat.
import json, pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

VOLETS = """      <div class="volets mdb-volets" role="tablist" aria-label="Marché"><!-- patch298 -->
        <button type="button" class="volet{d}" data-volet="doublons" role="tab" aria-selected="{ds}">Mes doublons</button>
        <button type="button" class="volet{b}" data-volet="bourse" role="tab" aria-selected="{bs}">Bourse</button>
        <button type="button" class="volet{e}" data-volet="echange" role="tab" aria-selected="{es}">Échange<span class="volet-badge" data-badge-echange hidden></span></button>
        <button type="button" class="volet{c}" data-volet="contrat" role="tab" aria-selected="{cs}">Contrat</button>
      </div>
"""
def volets(actif):
    v = {}
    for k in 'dbec':
        on = k == actif
        v[k] = ' actif' if on else ''
        v[k + 's'] = 'true' if on else 'false'
    return VOLETS.format(**v)

# ---------------------------------------------------------------- index.html
f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
assert 'patch298' not in s
s = rep(s, """      <div class="tab" data-tab="contrat">
        <div class="icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M6 3.5h8.5L19 8v12.5H6z"/>
            <path d="M14 3.5V8h5"/>
            <path d="M9 12.5h6M9 16h4"/>
          </svg>
        </div>
        Contrat
      </div>""", """      <div class="tab" data-tab="contrat"><!-- patch298 : l'onglet Contrat devient le Marché -->
        <div class="icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3.5 9.5h17l-1.8-5H5.3z"/>
            <path d="M5 9.5v10h14v-10"/>
            <path d="M9.5 19.5v-5h5v5"/>
          </svg>
        </div>
        Marché
        <span class="tab-badge" id="marcheBadge" hidden></span>
      </div>""")
s = rep(s, """      <div class="tab" data-tab="bourse">""", """      <div class="tab onglet-fusionne" data-tab="bourse" aria-hidden="true"><!-- patch298 : volet du Marché -->""")
s = rep(s, """      <div class="tab" data-tab="echange">""", """      <div class="tab onglet-fusionne" data-tab="echange" aria-hidden="true"><!-- patch298 : volet du Marché -->""")
s = rep(s, """    <section class="tab-panel" id="panel-bourse">
      <h1>Bourse</h1>
""", """    <section class="tab-panel" id="panel-bourse">
      <h1>Marché</h1>
""" + volets('b'))
s = rep(s, """    <section class="tab-panel" id="panel-echange">
      <h1>Échange</h1>
""", """    <section class="tab-panel" id="panel-echange">
      <h1>Marché</h1>
""" + volets('e'))
s = rep(s, """    <section class="tab-panel" id="panel-contrat">
      <h1>Contrat</h1>
""", """    <section class="tab-panel" id="panel-contrat">
      <h1>Marché</h1>
""" + volets('c') + """      <div id="mesDoublons" class="mdb" aria-live="polite"></div>
""")
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- style.css
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch298' not in s
s += """
/* patch298 : le Marché (Mes doublons · Bourse · Échange · Contrat) */
.volets.mdb-volets{ display:flex; width:100%; max-width:560px; box-sizing:border-box; }
.mdb-volets .volet{ flex:1 1 auto; padding-left:6px; padding-right:6px; white-space:nowrap; display:inline-flex; align-items:center; justify-content:center; gap:5px; }
@media (max-width:720px){ .mdb-volets .volet{ font-size:.8rem; padding-left:3px; padding-right:3px; } .mdb-volets .volet-badge{ min-width:16px; height:16px; font-size:.62rem; padding:0 4px; } }
#panel-contrat.vue-doublons > :not(h1):not(.volets):not(#mesDoublons){ display:none !important; }
#panel-contrat:not(.vue-doublons) > #mesDoublons{ display:none; }
.mdb{ max-width:560px; }
.mdb-sub{ color:var(--brume); font-size:.9rem; margin:0 0 12px; }
.mdb-resume{ border-radius:16px; padding:14px 14px 12px; border:1px solid rgba(240,180,41,.35); background:linear-gradient(135deg, rgba(240,180,41,.13), rgba(22,44,75,.6) 60%); margin-bottom:4px; }
.mdb-l1{ display:flex; align-items:baseline; justify-content:space-between; gap:8px; flex-wrap:wrap; }
.mdb-n{ font-family:var(--titre); font-weight:900; font-size:2.3rem; line-height:1; color:#fff; }
.mdb-n small{ font-family:var(--texte); font-size:.85rem; font-weight:600; color:#C9D3E3; margin-left:4px; }
.mdb-v{ text-align:right; font-size:.74rem; color:#C9D3E3; }
.mdb-v b{ display:block; font-family:var(--titre); font-weight:900; font-size:1.35rem; color:#FFE08A; }
.mdb-barre{ display:flex; height:9px; border-radius:5px; overflow:hidden; margin:12px 0 8px; gap:2px; background:rgba(169,188,212,.1); }
.mdb-barre i{ display:block; height:100%; }
.mdb-leg{ display:flex; flex-wrap:wrap; gap:4px 12px; font-size:.74rem; color:#C9D3E3; }
.mdb-leg span{ display:inline-flex; align-items:center; gap:5px; }
.mdb-leg span::before{ content:''; width:8px; height:8px; border-radius:50%; background:var(--c); }
.mdb-h{ font-size:.7rem; letter-spacing:.1em; text-transform:uppercase; color:#C8D5E6; font-weight:700; margin:16px 2px 8px; }
.mdb-grille{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.mdb-t{ border-radius:14px; border:1px solid rgba(169,188,212,.16); background:rgba(169,188,212,.06); padding:11px 12px; text-align:left; color:#fff; font:inherit; cursor:pointer; display:flex; flex-direction:column; gap:4px; min-width:0; box-sizing:border-box; }
.mdb-t:hover{ border-color:rgba(169,188,212,.34); }
.mdb-t:focus-visible{ outline:2px solid #F0B429; outline-offset:2px; }
.mdb-k{ display:flex; align-items:center; gap:6px; font-size:.66rem; font-weight:700; text-transform:uppercase; letter-spacing:.07em; color:var(--brume); }
.mdb-k svg{ width:13px; height:13px; flex:none; }
.mdb-g{ font-family:var(--titre); font-weight:900; font-size:1.55rem; line-height:1.05; }
.mdb-p{ font-size:.76rem; color:#C9D3E3; line-height:1.35; }
.mdb-a{ margin-top:auto; padding-top:6px; font-size:.78rem; font-weight:700; color:#FFE08A; }
.mdb-t.urgent{ border-color:rgba(229,72,77,.55); background:linear-gradient(180deg, rgba(229,72,77,.14), rgba(169,188,212,.04)); }
.mdb-t.urgent .mdb-k{ color:#FF8A8E; }
.mdb-t.or .mdb-k{ color:#FFE08A; }
.mdb-t.vert .mdb-k{ color:#7CF0B5; }
.mdb-t.calme .mdb-g{ color:#8EA2BF; }
.mdb-rar{ border-radius:14px; border:1px solid rgba(169,188,212,.16); overflow:hidden; }
.mdb-ligne{ padding:10px 12px; border-top:1px solid rgba(169,188,212,.1); }
.mdb-ligne:first-child{ border-top:none; }
.mdb-lh{ display:flex; align-items:center; gap:8px; }
.mdb-lh .pt{ width:10px; height:10px; border-radius:50%; background:var(--c); flex:none; }
.mdb-lh b{ font-size:.92rem; color:#fff; }
.mdb-lh .n{ margin-left:auto; font-family:var(--titre); font-weight:800; font-size:1.2rem; color:#fff; }
.mdb-li{ font-size:.74rem; color:#A9BCD4; margin:3px 0 8px 18px; }
.mdb-li em{ font-style:normal; color:#7CF0B5; }
.mdb-acts{ display:flex; gap:5px; margin-left:18px; flex-wrap:wrap; }
.mdb-act{ font:inherit; font-size:.74rem; font-weight:600; color:#E6ECF5; background:rgba(169,188,212,.08); border:1px solid rgba(169,188,212,.22); border-radius:8px; padding:6px 9px; cursor:pointer; }
.mdb-act:hover:not(:disabled){ border-color:rgba(169,188,212,.45); }
.mdb-act.plein{ background:var(--c-legendaire); border-color:var(--c-legendaire); color:var(--encre); font-weight:700; }
.mdb-act:disabled{ opacity:.38; cursor:default; }
.mdb-note{ font-size:.74rem; color:#8EA2BF; line-height:1.45; margin:10px 2px 0; }
.mdb-note b{ color:#C9D3E3; }
.mdb-vide{ border:1px dashed rgba(169,188,212,.3); border-radius:14px; padding:16px 14px; color:#A9BCD4; font-size:.86rem; line-height:1.5; }
"""
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- app.js
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch298' not in s
# Bourse et Échange : des volets du Marché (l'onglet Contrat s'allume)
s = rep(s, "const ONGLETS_FUSIONNES = ['defense', 'succes', 'cdj', 'radar', 'rafale', 'boutiqueeuros', 'personnaliser', 'monuments', 'pass'];",
           "const ONGLETS_FUSIONNES = ['defense', 'succes', 'cdj', 'radar', 'rafale', 'boutiqueeuros', 'personnaliser', 'monuments', 'pass', 'bourse', 'echange'];   // patch298 : bourse, echange")
s = rep(s, "const ONGLET_PARENT = { defense: 'combat', succes: 'profil', cdj: 'qg', radar: 'qg', rafale: 'qg', boutiqueeuros: 'boutique', personnaliser: 'profil', monuments: 'collection', pass: 'qg' };",
           "const ONGLET_PARENT = { defense: 'combat', succes: 'profil', cdj: 'qg', radar: 'qg', rafale: 'qg', boutiqueeuros: 'boutique', personnaliser: 'profil', monuments: 'collection', pass: 'qg', bourse: 'contrat', echange: 'contrat' };   // patch298")
s = rep(s, "           propres: ['tirage', 'collection', 'qg', 'contrat', 'bourse', 'echange', 'boutique'] },   // patch191 : monuments dans Collection",
           "           propres: ['tirage', 'collection', 'qg', 'contrat', 'boutique'] },   // patch191 : monuments dans Collection   // patch298 : bourse et echange dans le Marché")
s = rep(s, "  terra: [['Jouer', ['tirage', 'collection', 'qg']], ['Marché', ['contrat', 'bourse', 'echange', 'boutique']],",
           "  terra: [['Jouer', ['tirage', 'collection', 'qg']], ['Marché', ['contrat', 'boutique']],   // patch298")
# l'onglet ouvre Mes doublons
s = rep(s, "    if(tab.dataset.tab === 'contrat') loadContratEtExclusions();",
           "    if(tab.dataset.tab === 'contrat') loadContratEtExclusions();\n    if(tab.dataset.tab === 'contrat') mdbEntrer();   // patch298")
# les contrats connus : Mes doublons se redessine avec le vrai nombre
s = rep(s, "  if(ctTerra()){ await loadContrat(); return; }",
           "  if(ctTerra()){ await loadContrat(); mdbApres(); return; }   // patch298")
# la pastille des échanges suit aussi sur le Marché
s = rep(s, """  const badge = document.getElementById('echangeBadge');
  if(!badge) return;
  badge.hidden = recues + nouv === 0;""", """  const mb = document.getElementById('marcheBadge');   // patch298
  if(mb){ mb.hidden = recues + nouv === 0; mb.textContent = recues + nouv; }
  document.querySelectorAll('[data-badge-echange]').forEach(x => { x.hidden = recues === 0; x.textContent = recues; });
  if(mdbActif()) mdbRendre();
  const badge = document.getElementById('echangeBadge');
  if(!badge) return;
  badge.hidden = recues + nouv === 0;""")
# la vente des doublons : préchoisir la rareté, et Mes doublons suit
s = rep(s, "function ouvrirVenteTerra(){\n  const dbl = doublonsTerra();",
           "function ouvrirVenteTerra(pre){   // patch298 : pre = la rareté cochée seule\n  const dbl = doublonsTerra();")
s = rep(s, """<input type="checkbox" value="${t.id}" ${t.id === 'commun' || t.id === 'peucommun' ? 'checked' : ''}>""",
           """<input type="checkbox" value="${t.id}" ${(pre ? t.id === pre : (t.id === 'commun' || t.id === 'peucommun')) ? 'checked' : ''}>""")
s = rep(s, """    notifier({ type: 'succes', titre: 'Doublons vendus', texte: r ? `${fmtNombre(r.vendus)} doublon${r.vendus > 1 ? 's' : ''} · +${fmtNombre(r.gain)} TP` : '' });
    renderCollectionTerra();""", """    notifier({ type: 'succes', titre: 'Doublons vendus', texte: r ? `${fmtNombre(r.vendus)} doublon${r.vendus > 1 ? 's' : ''} · +${fmtNombre(r.gain)} TP` : '' });
    renderCollectionTerra();
    if(mdbActif()) mdbRendre();   // patch298""")
s = rep(s, "texte: 'Elles t’attendent dans l’onglet Échange.' });", "texte: 'Elles t’attendent dans le Marché, volet Échange.' });   // patch298")

s += r"""

// ---------- patch298 : le Marché, « Mes doublons » ----------
// Bourse, Échange et Contrat sont des volets ; l'onglet Contrat (« Marché » dans la barre)
// ouvre Mes doublons. Un clic du joueur sur l'onglet → Mes doublons ; un clic venu du code
// (rappel de contrat, bouton Contrat de la Collection) → l'écran Contrat, comme avant.
// var et non const : l'onglet peut être ouvert par le code avant que cette ligne soit lue
var MDB = { vue: 'doublons', forcer: null, marcheLu: 0, chargement: false };
var MDB_ICO = {
  echange: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8h13l-3.5-3.5M17 8l-3.5 3.5"/><path d="M20 16H7l3.5-3.5M7 16l3.5 3.5"/></svg>',
  contrat: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3.5h8.5L19 8v12.5H6z"/><path d="M9 12.5h6M9 16h4"/></svg>',
  loupe: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="6"/><path d="m20 20-4.5-4.5"/></svg>',
  etiquette: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 12.6V5.2a1.7 1.7 0 0 1 1.7-1.7h7.4l7.9 7.9a1.7 1.7 0 0 1 0 2.4l-7.4 7.4a1.7 1.7 0 0 1-2.4 0z"/><circle cx="8.2" cy="8.2" r="1.5"/></svg>',
};
function mdbActif(){
  if(typeof MDB === 'undefined' || !MDB) return false;
  const p = document.getElementById('panel-contrat');
  return !!(SAISON2 && p && p.classList.contains('active') && MDB.vue === 'doublons' && document.getElementById('mesDoublons'));
}
function mdbAppliquer(){
  if(typeof MDB === 'undefined' || !MDB) return;
  const p = document.getElementById('panel-contrat');
  if(!p || !document.getElementById('mesDoublons')) return;
  const d = SAISON2 && MDB.vue === 'doublons';
  p.classList.toggle('vue-doublons', d);
  p.querySelectorAll('.volets .volet').forEach(v => {
    const on = v.dataset.volet === (d ? 'doublons' : 'contrat');
    v.classList.toggle('actif', on); v.setAttribute('aria-selected', String(on));
  });
}
async function mdbEntrer(){
  if(!SAISON2 || typeof MDB === 'undefined' || !MDB) return;
  mdbAppliquer();
  if(MDB.vue !== 'doublons') return;
  mdbRendre();
  if(MDB.chargement) return;
  MDB.chargement = true;
  try{
    const att = [];
    if(!terraCharge) att.push(chargerCollectionTerra());
    if(Date.now() - MDB.marcheLu > 120000) att.push(sb.rpc('terra_marche').then(({ data, error }) => {
      if(!error){ marcheTerraLignes = data || []; MDB.marcheLu = Date.now(); }
    }).catch(() => {}));
    if(!Array.isArray(echangesEnCours) || !echangesEnCours.length) att.push(chargerEchangesEnCours().catch(() => {}));
    await Promise.all(att);
  }finally{ MDB.chargement = false; }
  if(mdbActif()) mdbRendre();
}
function mdbApres(){ if(mdbActif()) mdbRendre(); }
// contrats possibles par rareté : la liste du serveur si on l'a (elle tient compte de tout), sinon les doublons
function mdbContrats(dbl){
  const r = {};
  for(const c of CONTRATS){
    const conn = Array.isArray(contratDispo[c.de]) ? contratDispo[c.de].length : null;
    const n = conn != null ? conn : (dbl[c.de] || 0);
    r[c.de] = { nb: Math.floor(n / c.n), reste: c.n - (n % c.n), vers: c.vers, n: c.n };
  }
  return r;
}
function mdbRendre(){
  const el = document.getElementById('mesDoublons');
  if(!el) return;
  if(!terraCharge){ el.innerHTML = '<p class="mdb-sub">Tes doublons : les vendre, les échanger, ou en faire des contrats.</p><p class="collection-empty">Chargement de ta collection…</p>'; return; }
  const dbl = doublonsTerra();
  const ech = {}, ach = {};
  for(const e of terraCollection.values()){
    const x = echangeablesTerra(e), a = achetesTerra(e);
    if(x) ech[e.tier.id] = (ech[e.tier.id] || 0) + x;
    if(a) ach[e.tier.id] = (ach[e.tier.id] || 0) + a;
  }
  const total = Object.values(dbl).reduce((s, n) => s + n, 0);
  const gain = Object.entries(dbl).reduce((s, [t, n]) => s + n * (TERRA_REVENTE[t] || 0), 0);
  const nbAch = Object.values(ach).reduce((s, n) => s + n, 0);
  const ordre = TIERS.filter(t => dbl[t.id]);                 // légendaire → commun
  const cts = mdbContrats(dbl);
  const nbCt = Object.values(cts).reduce((s, c) => s + c.nb, 0);
  const lab = (id, n) => { const t = TIERS.find(x => x.id === id); const l = t ? t.label.toLowerCase() : id; return n > 1 ? l + 's' : l; };   // 90 communs, 36 peu communs
  const labF = (id, n) => ({ peucommun: 'peu commune', rare: 'rare' }[id] || lab(id, 1)) + (n > 1 ? 's' : '');   // 3 rares nouvelles
  const recues = (echangesEnCours || []).filter(e => e.sens === 'recu');
  const exp = recues.map(e => new Date(e.expire_le).getTime() - Date.now()).filter(x => x > 0).sort((a, b) => a - b)[0];
  const lignes = Array.isArray(marcheTerraLignes) ? marcheTerraLignes : [];
  const pourMoi = lignes.filter(a => !a.mienne && !a.je_l_ai).length;
  const mes = lignes.filter(a => a.mienne).length;
  const marcheConnu = (MDB && MDB.marcheLu > 0) || lignes.length > 0;

  const tuile = (cls, vers, ico, k, g, p, a) => `<button type="button" class="mdb-t ${cls}" data-mdb="${vers}"><span class="mdb-k">${ico}${k}</span><span class="mdb-g">${g}</span><span class="mdb-p">${p}</span><span class="mdb-a">${a} →</span></button>`;
  const tuiles = [
    recues.length
      ? tuile('urgent', 'echange-cours', MDB_ICO.echange, `Échange${recues.length > 1 ? 's' : ''} reçu${recues.length > 1 ? 's' : ''}`, recues.length, exp ? `${recues.length > 1 ? 'Le premier expire' : 'Expire'} dans ${formatDuree(exp)}` : 'À regarder', 'Répondre')
      : tuile('calme', 'echange', MDB_ICO.echange, 'Échanges reçus', 0, 'Aucune proposition en attente', 'Proposer'),
    tuile(nbCt ? 'or' : 'calme', 'contrat', MDB_ICO.contrat, 'Contrats possibles', fmtNombre(nbCt), nbCt ? 'Que des communes que tu n’as pas encore' : 'Il faut 10 doublons communs ou peu communs', nbCt ? 'Signer' : 'Voir'),
    tuile(pourMoi ? 'vert' : 'calme', 'bourse', MDB_ICO.loupe, 'En vente pour toi', marcheConnu ? fmtNombre(pourMoi) : '…', !marcheConnu ? 'Chargement de la Bourse…' : pourMoi ? `Commune${pourMoi > 1 ? 's' : ''} qui te manque${pourMoi > 1 ? 'nt' : ''}, à la Bourse` : 'Rien qui te manque pour l’instant', 'Voir'),
    tuile('', 'bourse', MDB_ICO.etiquette, 'Tes annonces', marcheConnu ? fmtNombre(mes) : '…', !marcheConnu ? 'Chargement de la Bourse…' : mes ? `En vente à la Bourse` : 'Aucune commune en vente', mes ? 'Gérer' : 'Vendre'),
  ];

  const ligne = (t) => {
    const n = dbl[t.id], c = cts[t.id], x = ech[t.id] || 0;
    let info = `${fmtNombre(TERRA_REVENTE[t.id] || 0)} TP pièce au jeu`;
    let ctBtn = '';
    if(c){
      if(c.nb) info += ` · <em>${c.nb} contrat${c.nb > 1 ? 's' : ''} → ${c.nb} ${labF(c.vers, c.nb)} nouvelle${c.nb > 1 ? 's' : ''}</em>`;
      else info += ` · encore ${c.reste} pour un contrat`;
      ctBtn = `<button type="button" class="mdb-act${c.nb ? ' plein' : ''}" data-mdb="contrat"${c.nb ? '' : ' disabled'}>Contrat${c.nb ? '' : ` (${c.n - c.reste}/${c.n})`}</button>`;
    } else info += ' · Bourse à partir de ' + fmtNombre(TERRA_REVENTE[t.id] || 0) + ' TP';
    const vendre = `<button type="button" class="mdb-act" data-mdb="vendre" data-tier="${t.id}">${t.id === 'commun' ? `Tout vendre (${fmtNombre(n * (TERRA_REVENTE[t.id] || 0))} TP)` : 'Vendre'}</button>`;
    const bourse = `<button type="button" class="mdb-act" data-mdb="bourse-tier" data-tier="${t.id}"${x ? '' : ' disabled title="Achetées en TP : elles ne vont pas à la Bourse"'}>Bourse</button>`;
    const echg = `<button type="button" class="mdb-act" data-mdb="echange-tier" data-tier="${t.id}"${x ? '' : ' disabled title="Achetées en TP : elles ne s’échangent pas"'}>Échanger</button>`;
    return `<div class="mdb-ligne">
        <div class="mdb-lh"><span class="pt" style="--c:${COULEURS_FILTRE[t.id]}"></span><b>${t.label}${n > 1 ? 's' : ''}</b><span class="n">${fmtNombre(n)}</span></div>
        <div class="mdb-li">${info}</div>
        <div class="mdb-acts">${c && c.nb ? ctBtn + vendre : vendre}${t.id === 'commun' ? '' : bourse}${echg}${c && !c.nb ? ctBtn : ''}</div>
      </div>`;
  };

  el.innerHTML = `<p class="mdb-sub">Tes doublons : les vendre, les échanger, ou en faire des contrats. Tu gardes toujours un exemplaire de chaque commune.</p>
    ${total ? `<div class="mdb-resume">
      <div class="mdb-l1"><div class="mdb-n">${fmtNombre(total)}<small>doublon${total > 1 ? 's' : ''}</small></div>
        <div class="mdb-v">vendus au jeu<b>jusqu’à ${fmtNombre(gain)} TP</b></div></div>
      <div class="mdb-barre">${TIERS.slice().reverse().filter(t => dbl[t.id]).map(t => `<i style="flex:${dbl[t.id]};background:${COULEURS_FILTRE[t.id]}"></i>`).join('')}</div>
      <div class="mdb-leg">${TIERS.slice().reverse().filter(t => dbl[t.id]).map(t => `<span style="--c:${COULEURS_FILTRE[t.id]}">${fmtNombre(dbl[t.id])} ${lab(t.id, dbl[t.id])}</span>`).join('')}</div>
    </div>` : `<div class="mdb-vide">Pas encore de doublon : ils arrivent quand tu tires une commune que tu as déjà. Tu peux quand même acheter à la Bourse ou proposer un échange.</div>`}
    <div class="mdb-h">À faire</div>
    <div class="mdb-grille">${tuiles.join('')}</div>
    ${total ? `<div class="mdb-h">Par rareté</div><div class="mdb-rar">${ordre.map(ligne).join('')}</div>` : ''}
    ${nbAch ? `<p class="mdb-note"><b>${fmtNombre(nbAch)} de tes doublons viennent d’achats en TP.</b> Ils se vendent au jeu et comptent pour les contrats, mais ne vont ni à la Bourse ni à l’Échange.</p>` : ''}`;
}
function mdbVers(quoi, tier){
  const onglet = (id) => { const t = document.querySelector(`.tab[data-tab="${id}"]`); if(t) t.click(); };
  if(quoi === 'contrat'){ MDB.vue = 'contrat'; mdbAppliquer(); return; }
  if(quoi === 'vendre') return ouvrirVenteTerra(tier);
  if(quoi === 'echange-cours'){ echVue = 'cours'; return onglet('echange'); }
  if(quoi === 'echange'){ echVue = 'proposer'; return onglet('echange'); }
  if(quoi === 'echange-tier'){
    echVue = 'proposer'; echangeTier = tier; echangeMien = null; echangeCible = null;
    document.querySelectorAll('#echTiers .filter-pill').forEach(x => x.classList.toggle('active', x.dataset.tier === tier));
    return onglet('echange');
  }
  if(quoi === 'bourse-tier'){
    sellFilterTier = tier;
    document.querySelectorAll('#sellFilters .filter-pill').forEach(x => x.classList.toggle('active', x.dataset.tier === tier));
    onglet('bourse');
    setTimeout(() => { const g = document.getElementById('sellFilters'); if(g) g.scrollIntoView({ block: 'start', behavior: 'smooth' }); }, 350);
    return;
  }
  if(quoi === 'bourse') return onglet('bourse');
}
(function mdbInit(){
  if(!SAISON2) return;
  document.getElementById('mesDoublons')?.addEventListener('click', (e) => {
    const b = e.target.closest('[data-mdb]');
    if(b && !b.disabled) mdbVers(b.dataset.mdb, b.dataset.tier);
  });
  // les volets du Marché et l'onglet : en phase de capture, avant l'écouteur général des volets
  document.addEventListener('click', (e) => {
    const v = e.target.closest('.mdb-volets .volet[data-volet]');
    if(v){
      const ici = document.getElementById('panel-contrat')?.classList.contains('active');
      if(v.dataset.volet === 'doublons' || v.dataset.volet === 'contrat'){
        e.stopPropagation();
        MDB.vue = v.dataset.volet;
        if(ici){ mdbEntrer(); if(MDB.vue === 'contrat') mdbAppliquer(); }
        else { MDB.forcer = MDB.vue; const t = document.querySelector('.tab[data-tab="contrat"]'); if(t) t.click(); }
      }
      return;   // Bourse, Échange : l'écouteur général ouvre l'onglet
    }
    const t = e.target.closest('.tab[data-tab="contrat"]');
    if(t){ MDB.vue = MDB.forcer || (e.isTrusted ? 'doublons' : 'contrat'); MDB.forcer = null; }
  }, true);
  mdbAppliquer();
})();
"""
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- nouveautés
f = pathlib.Path('data/nouveautes.json'); d = json.loads(f.read_text(encoding='utf-8'))
e = next(x for x in d if x['date'] == '2026-10-31')
e['nouveautes'].insert(0, '🏪 Le Marché : Bourse, Échange et Contrat réunis, avec « Mes doublons » pour voir d’un coup ce que tu peux en faire')
f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch298 appliqué')
