# -*- coding: utf-8 -*-
u"""
patch202 — skins et collections (dos + skin) dans la boutique en euros
(prix « pour moi » calculé par le serveur), bloc « Skins de carte » et
« Choisir les cartes » dans Profil › Personnaliser.
SQL : _boutique-euros/14-skins-packs-boutique.sql (à passer avant de pousser).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)

BLOC_JS = r'''// ---------- patch202 : skins et collections dans la boutique, skins dans Personnaliser ----------
// une carte pour montrer un skin : ma plus belle carte Terra avec photo, sinon Paris
function carteExemple(){
  let best = null;
  try{
    if(typeof terraCollection !== 'undefined' && terraCollection)
      for(const e of terraCollection.values()){
        if(!e.photo) continue;
        if(!best || RANG_TIER[e.tier.id] > RANG_TIER[best.tier.id]) best = e;
      }
  }catch(err){}
  return best || { code: '75056', nom: 'Paris', dept: '75', tier: TIERS[0], rank: 1, tierSize: 302, photo: '' };
}
function skinVignetteHtml(k){
  if(!k) return '';
  return `<div class="sk-vig" aria-hidden="true"><div class="sk-vig-echelle">${miniTerra({ ...carteExemple(), skin: k, exemplaires: 1, aurore: 0 })}</div></div>`;
}
const bqePrixMoi = (a) => a.prix_moi != null ? Number(a.prix_moi) : Number(a.prix_centimes);
function bqePrixHtml(a){
  const moi = bqePrixMoi(a), plein = Number(a.prix_centimes);
  return (moi < plein ? `<s>${euros(plein)}</s> ` : '') + euros(moi);
}

// Profil › Personnaliser : mes skins et les cartes qui les portent
function blocSkinsHtml(){
  const liste = mesSkins || [];
  if(!liste.length) return `<div class="gr-titre">Skins de carte <span>0 possédé</span></div>
    <p class="gr-dc-vide">Un skin habille les cartes de ton choix (photo, fond, textes). Ils sont dans la boutique.</p>`;
  const lignes = mesSkinsCartes ? [...mesSkinsCartes.entries()].sort((a, b) => a[1].nom.localeCompare(b[1].nom, 'fr')) : [];
  return `<div class="gr-titre">Skins de carte <span>${liste.length} possédé${liste.length > 1 ? 's' : ''} · ${lignes.length} carte${lignes.length > 1 ? 's' : ''} habillée${lignes.length > 1 ? 's' : ''}</span></div>
    ${lignes.length ? `<div class="gr-dc-liste">${lignes.map(([cle, r]) => {
      const [source] = cle.split('|'); const k = skinCle(r.skin);
      return `<div class="gr-dc-ligne gr-sk-ligne"><i class="sk-pastille sk-p-${k}" aria-hidden="true"></i>
        <div class="gr-dc-nom"><b>${echapperTexte(r.nom)}</b><span>${source === 'front' ? 'Front' : 'Terra'} · ${echapperTexte(SKIN_NOMS[k] || '')}</span></div>
        <button type="button" class="bq-btn secondaire" data-gr-sk-retirer="${echapperTexte(cle)}">Retirer</button></div>`;
    }).join('')}</div>` : '<p class="gr-dc-vide">Aucune carte n\'a de skin pour l\'instant.</p>'}
    <div class="gr-dc-bas"><button type="button" class="bq-btn secondaire" data-gr-sk-choisir>Choisir les cartes</button>
      <small>Terra et Front. Une carte vendue, échangée ou prise perd ton skin ; le skin reste à toi.</small></div>`;
}
document.getElementById('grCorps').addEventListener('click', async (e) => {
  const r = e.target.closest('[data-gr-sk-retirer]');
  if(r){
    r.disabled = true;
    const [source, code] = r.dataset.grSkRetirer.split('|');
    const { error } = await sb.rpc('skin_cartes_definir', { p_source: source, p_codes: [code], p_skin: null });
    if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); r.disabled = false; return; }
    mesSkinsCartes.delete(r.dataset.grSkRetirer);
    skinGl.rafraichir();
    renderGardeRobe();
    return;
  }
  if(e.target.closest('[data-gr-sk-choisir]')) ouvrirChoixSkinCartes();
});
async function ouvrirChoixSkinCartes(){
  const liste = await chargerMesSkins();
  if(!liste.length) return;
  if(!terraCharge) await chargerCollectionTerra();
  let skin = liste[0].id;
  let source = modeJeu === 'front' ? 'front' : 'terra';
  let choix = new Set(), recherche = '';
  const rangTier = (t) => TIERS.findIndex(x => x.id === t.id);
  const cartesDe = (s) => [...(s === 'front' ? collectionMap.values() : terraCollection.values())]
    .filter(c => !c.perdue)
    .sort((a, b) => rangTier(a.tier) - rangTier(b.tier) || a.nom.localeCompare(b.nom, 'fr'));
  const fermer = ouvrirFenetre(`
    <div class="fenetre vt-choix dc-fenetre sk-fenetre" role="dialog" aria-modal="true" aria-labelledby="skTitre">
      <h2 id="skTitre">Poser un skin sur des cartes</h2>
      <p class="vt-aide">Choisis un skin, puis touche les cartes qui le porteront.</p>
      <div class="sk-rangee" id="skSkins" role="group" aria-label="Le skin"></div>
      <div class="dc-sources" role="group" aria-label="Mode">
        <button type="button" data-sk-source="terra">Terra</button><button type="button" data-sk-source="front">Front</button>
      </div>
      <p class="vt-compte" id="skCompte"></p>
      <input type="search" id="skRecherche" class="bourse-search" placeholder="Rechercher une commune ou un département…" autocomplete="off">
      <div class="vt-grille" id="skGrille"></div>
      <p class="prix-erreur" id="skErreur" role="alert"></p>
      <div class="prix-boutons">
        <button type="button" class="open-btn secondary" data-sk="annuler">Annuler</button>
        <button type="button" class="open-btn" data-sk="ok">Enregistrer</button>
      </div>
    </div>`);
  const boite = document.querySelector('#fenetre .sk-fenetre');
  if(!boite) return;
  const dessiner = () => {
    boite.querySelector('#skSkins').innerHTML = liste.map(o => { const k = skinCle(o.id);
      return `<button type="button" class="sk-opt${o.id === skin ? ' on' : ''}" data-sk-skin="${echapperTexte(o.id)}" aria-pressed="${o.id === skin}"><i class="sk-pastille sk-p-${k}" aria-hidden="true"></i>${echapperTexte(SKIN_NOMS[k] || o.nom)}</button>`; }).join('');
    boite.querySelectorAll('[data-sk-source]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.skSource === source)));
    boite.querySelector('#skCompte').innerHTML = `<b>${choix.size}</b> carte${choix.size > 1 ? 's' : ''} choisie${choix.size > 1 ? 's' : ''}`;
    const q = recherche.trim().toLowerCase();
    const dep = q ? codeDepartement(q) : null;
    const qs = sansAccents(recherche.trim());
    const cartes = cartesDe(source).filter(c => !q || correspondRecherche(c.nom, c.dept, qs) || c.dept === dep).slice(0, 150);
    boite.querySelector('#skGrille').innerHTML = cartes.map(c => `<button type="button" class="vt-carte${choix.has(c.code) ? ' pris' : ''}" data-sk-code="${echapperTexte(c.code)}" aria-pressed="${choix.has(c.code)}">
        ${miniVitrine({ ...c, aurore: source === 'front' ? (AURORE && AURORE[c.code] ? 1 : 0) : c.aurore })}${choix.has(c.code) ? '<span class="vt-num">✓</span>' : ''}</button>`).join('')
      || '<p class="collection-empty">Aucune carte ne correspond.</p>';
  };
  dessiner();
  boite.querySelector('#skRecherche').addEventListener('input', (e) => { recherche = e.target.value; dessiner(); });
  boite.addEventListener('click', async (e) => {
    const d = e.target.closest('[data-sk-skin]');
    if(d){ skin = d.dataset.skSkin; dessiner(); return; }
    const s = e.target.closest('[data-sk-source]');
    if(s){ if(s.dataset.skSource !== source){ source = s.dataset.skSource; choix = new Set(); } dessiner(); return; }
    const c = e.target.closest('[data-sk-code]');
    if(c){ const k = c.dataset.skCode; if(choix.has(k)) choix.delete(k); else choix.add(k); dessiner(); return; }
    const b = e.target.closest('[data-sk]');
    if(!b) return;
    if(b.dataset.sk === 'annuler'){ fermer(null); return; }
    if(!choix.size){ boite.querySelector('#skErreur').textContent = 'Touche au moins une carte.'; return; }
    b.disabled = true; b.textContent = 'Enregistrement…';
    const { error } = await sb.rpc('skin_cartes_definir', { p_source: source, p_codes: [...choix], p_skin: skin });
    if(error){ boite.querySelector('#skErreur').textContent = messageLisible(error.message); b.disabled = false; b.textContent = 'Enregistrer'; return; }
    fermer(null);
    await chargerMesSkinsCartes(true);
    renderGardeRobe();
    notifier({ type: 'succes', titre: 'Skin posé', texte: `${choix.size} carte${choix.size > 1 ? 's' : ''} ${choix.size > 1 ? 'portent' : 'porte'} maintenant le skin ${SKIN_NOMS[skinCle(skin)] || ''}.` });
  });
}

'''
BLOC_CSS = r'''
/* ---------- patch202 : skins et collections dans la boutique ---------- */
.sk-vig{ width: 94px; height: 141px; margin: 0 auto 4px; position: relative; }
.sk-vig-echelle{ width: 150px; position: absolute; left: 0; top: 0; transform: scale(.6267); transform-origin: 0 0; }
.sk-vig .mini{ width: 150px; content-visibility: visible; }
.bqe-col-vig{ display: flex; justify-content: center; align-items: flex-end; gap: 6px; margin: 0 auto 4px; }
.bqe-col-vig .bq-dos-apercu, .bqe-col-vig .sk-vig{ margin: 0; }
.bqe-col-vig .bq-dos-apercu{ width: 64px; height: 89.5px; }
.bqe-col-vig .bq-dos-echelle{ transform: scale(.34); }
.bqe-col-vig .sk-vig{ width: 60px; height: 90px; }
.bqe-col-vig .sk-vig-echelle{ transform: scale(.4); }
.bqe-prix s, .bqe-gros-prix s{ opacity: .6; font-weight: 600; margin-right: 4px; }
.bqe-grand .sk-vig, .bqe-grand .bqe-col-vig{ margin: 0; }
.gr-sk-ligne{ grid-template-columns: 22px minmax(0, 1fr) auto; }
.gr-sk-ligne .sk-pastille{ width: 18px; height: 18px; }
'''
REMPL = [("replace(/^(Paquet|Dos) (OG )?/, '')", "replace(/^(Paquet|Dos|Skin|Collection) (OG )?/, '')"), ("function bqeVignette(a){ return a.type === 'dos' ? dosApercuHtml(a.id) : habVignette(habCle(a.id)); }", 'function bqeVignette(a){\n  if(a.type === \'skin\') return skinVignetteHtml(skinCle(a.id));   // patch202\n  if(a.type === \'collection\'){ const c = a.contenu || [];\n    return `<div class="bqe-col-vig">${dosApercuHtml(c.find(x => x.startsWith(\'dos-\')))}${skinVignetteHtml(skinCle(c.find(x => x.startsWith(\'skin-\'))))}</div>`; }\n  return a.type === \'dos\' ? dosApercuHtml(a.id) : habVignette(habCle(a.id));\n}'), ('`<span class="bq-btn bqe-prix">${euros(a.prix_centimes)}</span>`', '`<span class="bq-btn bqe-prix">${bqePrixHtml(a)}</span>`'), ("const arts = (cat.articles || []).filter(a => a.type === 'dos' || a.type === 'habillage');", "const arts = (cat.articles || []).filter(a => ['dos', 'habillage', 'skin', 'collection'].includes(a.type));"), ("const dos = arts.filter(a => !a.reserve_og && a.type === 'dos');", "const dos = arts.filter(a => !a.reserve_og && a.type === 'dos');\n  const skins = arts.filter(a => a.type === 'skin'), cols = arts.filter(a => a.type === 'collection');   // patch202"), ("    + (cat.og ? section('Réservé aux OG', 'pour les joueurs de la saison 1', og, true) : '')", "    + (cat.og ? section('Réservé aux OG', 'pour les joueurs de la saison 1', og, true) : '')\n    + section('Collections', 'le dos et le skin ensemble, moins cher', cols)"), ("    + section('Dos de cartes', '', dos)", "    + section('Dos de cartes', '', dos)\n    + section('Skins de carte', 'à poser sur les cartes de ton choix', skins)"), ('const nom = bqeNomCourt(a), prix = euros(a.prix_centimes);', 'const nom = bqeNomCourt(a), prix = euros(bqePrixMoi(a));'), ("const quoi = a.type === 'habillage' ? `<b>l'habillage ${echapperTexte(nom)}</b> sur tous tes paquets` : `<b>le dos ${echapperTexte(nom)}</b> sur toutes tes cartes`;", "const quoi = a.type === 'habillage' ? `<b>l'habillage ${echapperTexte(nom)}</b> sur tous tes paquets`\n    : a.type === 'skin' ? `<b>le skin ${echapperTexte(nom)}</b>, à poser sur autant de tes cartes que tu veux (Terra et Front)`\n    : a.type === 'collection' ? `<b>le dos et le skin ${echapperTexte(nom)}</b>${bqePrixMoi(a) < Number(a.prix_centimes) ? ' (tu en as déjà une partie : tu ne paies que ce qui te manque)' : ''}`\n    : `<b>le dos ${echapperTexte(nom)}</b> sur toutes tes cartes`;"), ('Number(cat.plafond_restant) < Number(a.prix_centimes);', 'Number(cat.plafond_restant) < bqePrixMoi(a);'), ("const grand = a.type === 'dos' ? dosApercuHtml(a.id) :", "const grand = a.type === 'dos' ? dosApercuHtml(a.id) : a.type === 'skin' || a.type === 'collection' ? bqeVignette(a) :"), ("${a.type === 'dos' ? 'Dos de carte' : 'Habillage de paquet'}", "${{ dos: 'Dos de carte', skin: 'Skin de carte', collection: 'Collection · dos + skin' }[a.type] || 'Habillage de paquet'}"), ('  if(SAISON2) await chargerMesDosCartes(true);   // patch200', '  if(SAISON2) await Promise.all([chargerMesDosCartes(true), chargerMesSkins(true), chargerMesSkinsCartes(true)]);   // patch200-202'), ("      ${SAISON2 ? blocDosCartesHtml() : ''}", "      ${SAISON2 ? blocDosCartesHtml() + blocSkinsHtml() : ''}"), ('// ---------- patch179 : la carte en grand, inclinable et retournable ----------', '__BLOC__// ---------- patch179 : la carte en grand, inclinable et retournable ----------')]

js = lire('app.js')
assert 'patch202' not in js
for avant, apres in REMPL:
    assert js.count(avant) == 1, avant[:60]
    js = js.replace(avant, apres.replace('__BLOC__', BLOC_JS))
ecrire('app.js', js)
css = lire('style.css')
assert 'patch202' not in css
ecrire('style.css', css.rstrip('\n') + '\n' + BLOC_CSS)
print(u'patch202 applique. Lancer : python3 maj-version.py')
