# -*- coding: utf-8 -*-
u"""
patch112 — Terra : les collections thématiques.

Dans Collection (Terra), un troisième onglet « Collections » à côté de
« Mes cartes » et « Ma France » : Fromages, Eaux minérales, Vins,
Préfectures, Plus beaux villages.

- Chaque collection : sa progression, sa récompense (points + dos de carte),
  la liste de ses communes (possédées en couleur, manquantes en gris).
- « Paquet » : 5 communes de la collection qui te manquent, jamais de
  doublon. Même ouverture que les paquets de boutique (onglet Tirage),
  même limite de 3 par jour.
- Collection complète : bouton « Réclamer » (points + dos de carte, qui
  apparaît ensuite dans la boutique pour le mettre sur ses cartes).
- 5 nouveaux dos de carte (récompenses, pas en vente).

À passer AVANT : _sql/s2-19-collections.sql. Caché tant que SAISON2 = false.
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
assert 'renderCollectionsTerra' not in js, u'patch112 deja applique'

# l'onglet dans le sélecteur de vue
js = rempl(js, u"""    <button role="tab" data-tcv="france" class="${terraVue === 'france' ? 'on' : ''}" aria-selected="${terraVue === 'france'}">Ma France</button></div>`;""",
u"""    <button role="tab" data-tcv="france" class="${terraVue === 'france' ? 'on' : ''}" aria-selected="${terraVue === 'france'}">Ma France</button>
    <button role="tab" data-tcv="collections" class="${terraVue === 'collections' ? 'on' : ''}" aria-selected="${terraVue === 'collections'}">Collections</button></div>`;""",
    'selecteur')
js = rempl(js, u"  if(terraVue === 'france') return renderMaFranceTerra(el, totalFrance);",
           u"  if(terraVue === 'france') return renderMaFranceTerra(el, totalFrance);\n"
           u"  if(terraVue === 'collections') return renderCollectionsTerra(el);   // patch112",
           'vue collections')
# les clics de la vue Collections passent par le même écouteur
js = rempl(js, u"""function clicCollectionTerra(e){
  const v = e.target.closest('[data-tcv]');""",
u"""function clicCollectionTerra(e){
  if(clicCollections(e)) return;   // patch112
  const v = e.target.closest('[data-tcv]');""", 'clic')

# le paiement : un paquet de collection passe par la boutique
js = rempl(js, u"""  if(boutiqueAchat){
    // patch107 : paquet de la boutique, paye et tire en un seul appel
    const achat = boutiqueAchat;
    boutiqueAchat = null;""",
u"""  if(boutiqueAchat && boutiqueAchat.collection){
    // patch112 : paquet d'une collection thematique
    const achat = boutiqueAchat;
    boutiqueAchat = null;
    const { data, error } = await sb.rpc('boutique_ouvrir_collection', { p_collection: achat.collection });
    terraPaquet = error ? null : (data || []);
    boutiqueOuvert = !error;
    colCache = null;
    viderBilanTerra();
    return error;
  }
  if(boutiqueAchat){
    // patch107 : paquet de la boutique, paye et tire en un seul appel
    const achat = boutiqueAchat;
    boutiqueAchat = null;""", 'payer')

js += u"""

// ---------- patch112 : les collections thematiques (Terra) ----------
let colCache = null;          // reponse de collections_moi()
let colOuverte = null;        // id de la collection depliee
const colDetails = new Map(); // id -> lignes de collection_detail()

async function chargerCollections(){
  const { data, error } = await sb.rpc('collections_moi');
  if(error){ console.error(error); return false; }
  colCache = data || [];
  return true;
}

async function renderCollectionsTerra(el){
  if(!colCache){
    el.innerHTML = `<div class="coll-ligne-titre"><h1>Collection</h1></div>${selecteurVueTerra()}<p class="collection-empty">Chargement des collections…</p>`;
    const ok = await chargerCollections();
    if(terraVue !== 'collections') return;
    if(!ok){ el.querySelector('.collection-empty').textContent = 'Les collections ne sont pas disponibles pour le moment.'; return; }
  }
  const finies = colCache.filter(c => c.reclamee).length;
  el.innerHTML = `
    <div class="coll-ligne-titre"><h1>Collection</h1><span class="coll-compteur"><b>${finies}</b> / ${colCache.length} terminées</span></div>
    ${selecteurVueTerra()}
    <p class="col-intro">Complète une collection pour gagner des points et un dos de carte. Le paquet d'une collection ne donne que des communes qui te manquent.</p>
    <div class="col-liste">${colCache.map(carteCollection).join('')}</div>`;
  if(colOuverte && colDetails.has(colOuverte)) afficherDetailCollection(colOuverte);
}

function carteCollection(c){
  const total = Number(c.total) || 0, n = Number(c.possedees) || 0;
  const manque = Math.max(0, total - n);
  const pct = total ? Math.round(100 * n / total) : 0;
  const prix = manque ? Math.ceil(c.prix * Math.min(5, manque) / 5) : 0;
  const court = packStatusCache && Number(packStatusCache.solde) < prix;
  let action;
  if(c.reclamee) action = `<span class="col-finie">✓ Terminée</span>`;
  else if(!manque) action = `<button class="col-btn or" data-col-reclamer="${c.id}">Réclamer ${fmtNombre(c.recompense)} pts</button>`;
  else action = `<button class="bq-btn col-paquet" data-col-paquet="${c.id}" data-prix="${prix}"${court ? ' data-court="1"' : ''}>${bqPrix(prix)}</button>`;
  return `<div class="col-carte${c.reclamee ? ' finie' : ''}${!manque && !c.reclamee ? ' prete' : ''}" data-col="${c.id}">
      <div class="col-tete">
        <span class="col-emoji" aria-hidden="true">${c.emoji}</span>
        <div class="col-titre"><b>${echapperTexte(c.nom)}</b><span>${echapperTexte(c.description)}</span></div>
        ${dosApercuHtml(c.dos).replace('bq-dos-apercu', 'bq-dos-apercu col-dos')}
      </div>
      <div class="col-prog" role="progressbar" aria-valuemin="0" aria-valuemax="${total}" aria-valuenow="${n}"><i style="width:${pct}%"></i></div>
      <div class="col-chiffres"><span><b>${fmtNombre(n)}</b> / ${fmtNombre(total)} communes</span>
        <span class="col-rec">${c.reclamee ? 'Récompense reçue' : `Récompense : <b>${fmtNombre(c.recompense)} pts</b> + dos « ${echapperTexte(c.dos_nom || '')} »`}</span></div>
      <div class="col-actions">
        <button class="col-btn" data-col-voir="${c.id}" aria-expanded="${colOuverte === c.id}">${colOuverte === c.id ? 'Masquer' : 'Voir les communes'}</button>
        ${action}
      </div>
      <div class="col-detail" id="colDetail-${c.id}"${colOuverte === c.id ? '' : ' hidden'}></div>
    </div>`;
}

async function afficherDetailCollection(id){
  const zone = document.getElementById('colDetail-' + id);
  if(!zone) return;
  zone.hidden = false;
  if(!colDetails.has(id)){
    zone.innerHTML = '<p class="collection-empty">Chargement…</p>';
    const { data, error } = await sb.rpc('collection_detail', { p_collection: id });
    if(error){ zone.innerHTML = `<p class="collection-empty">${echapperTexte(messageLisible(error.message))}</p>`; return; }
    colDetails.set(id, data || []);
  }
  const lignes = colDetails.get(id);
  const z = document.getElementById('colDetail-' + id);
  if(!z) return;
  z.innerHTML = `<div class="col-communes">${lignes.map(r => {
    const t = TIERS.find(x => x.id === r.tier);
    return `<span class="col-commune ${r.possedee ? 'a ' + r.tier : 'manque'}${r.aurore > 0 ? ' aurore-chip' : ''}" title="${echapperTexte(r.nom)} (${r.departement})${t ? ' — ' + t.label : ''}${r.possedee ? '' : ' — à trouver'}">
        <b>${echapperTexte(r.nom)}</b><i>${echapperTexte(r.departement)}</i></span>`;
  }).join('')}</div>`;
}

function clicCollections(e){
  const voir = e.target.closest('[data-col-voir]');
  if(voir){
    const id = voir.dataset.colVoir;
    const zone = document.getElementById('colDetail-' + id);
    if(colOuverte === id){ colOuverte = null; if(zone) zone.hidden = true; voir.textContent = 'Voir les communes'; voir.setAttribute('aria-expanded', 'false'); }
    else {
      document.querySelectorAll('.col-detail').forEach(d => { d.hidden = true; });
      document.querySelectorAll('[data-col-voir]').forEach(b => { b.textContent = 'Voir les communes'; b.setAttribute('aria-expanded', 'false'); });
      colOuverte = id; voir.textContent = 'Masquer'; voir.setAttribute('aria-expanded', 'true');
      afficherDetailCollection(id);
    }
    return true;
  }
  const paq = e.target.closest('[data-col-paquet]');
  if(paq){
    if(!bqConfirmer(paq)) return true;
    paq.disabled = true;
    acheterPaquetCollection(paq.dataset.colPaquet).finally(() => { paq.disabled = false; });
    return true;
  }
  const rec = e.target.closest('[data-col-reclamer]');
  if(rec){
    rec.disabled = true;
    reclamerCollection(rec.dataset.colReclamer).finally(() => { rec.disabled = false; });
    return true;
  }
  return false;
}

async function acheterPaquetCollection(id){
  if(paquetEnCours){
    notifier({ type: 'erreur', titre: 'Un paquet t\\'attend déjà', texte: 'Ouvre d\\'abord celui qui est sur la table.' });
    return;
  }
  const c = (colCache || []).find(x => x.id === id);
  boutiqueAchat = { collection: id };
  boutiqueOuvert = false;
  const tirage = document.querySelector('.tab[data-tab="tirage"]');
  if(tirage) tirage.click();
  await openPack('achete');
  boutiqueAchat = null;
  colDetails.delete(id);
  terraCharge = false;
  if(!boutiqueOuvert) return;
  const bande = document.querySelector('#packZone .paquet .paquet-bande');
  if(bande && c) bande.textContent = c.nom;
  const titre = document.querySelector('#packZone .paquet .paquet-titre');
  if(titre) titre.textContent = 'Collection';
}

async function reclamerCollection(id){
  const { data, error } = await sb.rpc('collection_reclamer', { p_collection: id });
  if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); return; }
  const r = data && data[0];
  if(r && packStatusCache){ packStatusCache.solde = r.solde; majBascule(); }
  colCache = null;
  boutiqueCache = null;
  notifier({ type: 'succes', titre: 'Collection terminée !',
             texte: r ? `+${fmtNombre(r.points)} points et le dos « ${r.dos_nom} ». Mets-le sur tes cartes depuis la Boutique.` : '' });
  const el = document.getElementById('terraColl');
  if(el && terraVue === 'collections') renderCollectionsTerra(el);
}
"""
ecrire('app.js', js)

css = lire('style.css')
assert 'patch112' not in css, u'patch112 deja applique (css)'
css += u"""
/* ---------- patch112 : collections thématiques ---------- */
.col-intro{ color: var(--brume); font-size: .85rem; margin: 12px 0 14px; }
.col-liste{ display:grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); align-items:start; }
.col-carte{ background: rgba(19,35,59,.85); border: 1px solid rgba(169,188,212,.16); border-radius: 14px; padding: 14px; }
.col-carte.prete{ border-color: var(--c-legendaire); box-shadow: 0 0 18px rgba(240,180,41,.25); }
.col-carte.finie{ border-color: rgba(53,185,126,.5); }
.col-tete{ display:flex; align-items:center; gap: 12px; }
.col-emoji{ font-size: 1.9rem; line-height:1; width: 44px; height: 44px; display:flex; align-items:center; justify-content:center;
  border-radius: 12px; background: rgba(169,188,212,.1); flex-shrink:0; }
.col-titre{ flex:1; min-width:0; display:flex; flex-direction:column; }
.col-titre b{ font-family: var(--titre); font-weight: 800; font-size: 1.3rem; line-height: 1.05; color:#fff; }
.col-titre span{ font-size: .76rem; color: var(--brume); }
.bq-dos-apercu.col-dos{ width: 34px; height: 47.6px; margin:0; flex-shrink:0; border-radius: 4px; overflow:hidden; }
.bq-dos-apercu.col-dos .bq-dos-echelle{ transform: scale(.181); }
.col-prog{ height: 8px; border-radius: 99px; background: rgba(169,188,212,.14); margin: 12px 0 8px; overflow:hidden; }
.col-prog i{ display:block; height:100%; border-radius: inherit; background: linear-gradient(90deg, var(--c-peucommun), #6EE0A8); }
.col-carte.prete .col-prog i, .col-carte.finie .col-prog i{ background: linear-gradient(90deg, #C9952A, var(--c-legendaire)); }
.col-chiffres{ display:flex; flex-wrap:wrap; justify-content:space-between; gap: 4px 12px; font-size: .78rem; color: var(--brume); }
.col-chiffres b{ color:#fff; }
.col-actions{ display:flex; gap: 8px; margin-top: 12px; }
.col-actions > *{ flex:1; }
.col-btn{ font: inherit; font-size: .85rem; font-weight: 600; padding: 9px 10px; border-radius: 10px; cursor:pointer;
  background: transparent; color:#fff; border: 0; box-shadow: inset 0 0 0 1.5px rgba(169,188,212,.35); }
.col-btn.or{ background: var(--c-legendaire); color: var(--encre); box-shadow:none; }
.col-actions .bq-btn{ margin:0; }
.col-finie{ text-align:center; padding: 9px 0; font-size: .85rem; font-weight: 600; color: var(--c-peucommun); }
.col-detail{ margin-top: 12px; border-top: 1px solid rgba(169,188,212,.14); padding-top: 12px; }
.col-communes{ display:flex; flex-wrap:wrap; gap: 6px; max-height: 320px; overflow-y:auto; }
.col-commune{ display:inline-flex; align-items:baseline; gap: 5px; padding: 4px 9px; border-radius: 99px; font-size: .76rem; color:#fff; }
.col-commune i{ font-style: normal; opacity: .7; font-size: .68rem; }
.col-commune.manque{ color: rgba(169,188,212,.55); box-shadow: inset 0 0 0 1px rgba(169,188,212,.25); }
.col-commune.a.commun{ background: var(--c-commun); }
.col-commune.a.peucommun{ background: var(--c-peucommun); }
.col-commune.a.rare{ background: var(--c-rare); }
.col-commune.a.epique{ background: var(--c-epique); }
.col-commune.a.legendaire{ background: var(--c-legendaire); color: var(--encre); }
.col-commune.aurore-chip{ box-shadow: 0 0 0 1.5px #7FF2D0, 0 0 8px rgba(127,242,208,.5); }
@media (max-width: 560px){ .col-liste{ grid-template-columns: 1fr; } }

/* les 5 dos de récompense */
body[data-dos="fromages"], .bq-dos-apercu[data-dos="fromages"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #FFF1C9 0%, #F2D68F 55%, #C99B48 100%);
  --dos-liseret: rgba(140,90,30,0.6); --dos-embleme: #FFF6DC; --dos-or: #A86A22; --dos-anneau: rgba(201,155,72,0.9);
}
body[data-dos="source"], .bq-dos-apercu[data-dos="source"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #5FD0E8 0%, #1F8FB8 55%, #0D4F72 100%);
  --dos-liseret: rgba(232,246,252,0.65); --dos-embleme: #0D4F72; --dos-or: #E8F6FC; --dos-anneau: rgba(13,79,114,0.9);
}
body[data-dos="grand-cru"], .bq-dos-apercu[data-dos="grand-cru"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #8E2A47 0%, #5E1530 55%, #330816 100%);
  --dos-liseret: rgba(232,190,110,0.6); --dos-embleme: #3D0B1C; --dos-or: #E8BE6E; --dos-anneau: rgba(51,8,22,0.9);
}
body[data-dos="republique"], .bq-dos-apercu[data-dos="republique"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #2B4A9A 0%, #1A2E66 55%, #0C1638 100%);
  --dos-liseret: rgba(255,255,255,0.7); --dos-embleme: #0C1638; --dos-or: #FFFFFF; --dos-anneau: rgba(224,82,82,0.95);
}
body[data-dos="village"], .bq-dos-apercu[data-dos="village"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #CDB9E0 0%, #9C83B8 55%, #5E4A7A 100%);
  --dos-liseret: rgba(244,232,210,0.7); --dos-embleme: #4A3A63; --dos-or: #F4E8D2; --dos-anneau: rgba(94,74,122,0.9);
}
"""
ecrire('style.css', css)
print(u'patch112 applique')
