# patch254 : le pass de saison « Brumes d'automne » (avec s2-53)
#  - une carte « Pass de saison » en tête du QG (niveau, XP, récompenses à réclamer)
#  - un volet « Pass de saison » (onglet fusionné au QG) : en-tête, piste des 20 niveaux, réclamer, débloquer
#  - l'achat passe par la fiche de la boutique en euros (type « pass »)
#  - les titres du pass dans le choix du titre
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)

# ---------------------------------------------------------------- index.html
f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
s = rep(s, """      <div class="tab onglet-fusionne" data-tab="cdj" aria-hidden="true">""",
"""      <div class="tab onglet-fusionne" data-tab="pass" aria-hidden="true"><div class="icon"></div>Pass de saison</div>
      <div class="tab onglet-fusionne" data-tab="cdj" aria-hidden="true">""")
s = rep(s, """      <div class="qg-grille">
        <div class="qg-jeux">
        <div class="qg-carte" id="qgCdj">""",
"""      <div class="qg-grille">
        <div class="qg-jeux">
        <div class="qg-carte ps-qg" id="qgPass" hidden></div>
        <div class="qg-carte" id="qgCdj">""")
s = rep(s, """    <section class="tab-panel" id="panel-boutiqueeuros">""",
"""    <section class="tab-panel" id="panel-pass">
      <div class="volets" role="tablist" aria-label="QG">
        <button type="button" class="volet" data-volet="qg" role="tab" aria-selected="false">QG</button>
        <button type="button" class="volet actif" data-volet="pass" role="tab" aria-selected="true">Pass de saison</button>
      </div>
      <div id="passCorps"><p class="collection-empty">Chargement…</p></div>
    </section>

    <section class="tab-panel" id="panel-boutiqueeuros">""")
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- app.js
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
s = rep(s, "const ONGLETS_FUSIONNES = ['defense', 'succes', 'cdj', 'radar', 'rafale', 'boutiqueeuros', 'personnaliser', 'monuments'];",
           "const ONGLETS_FUSIONNES = ['defense', 'succes', 'cdj', 'radar', 'rafale', 'boutiqueeuros', 'personnaliser', 'monuments', 'pass'];   // patch254 : pass")
s = rep(s, "personnaliser: 'profil', monuments: 'collection' };",
           "personnaliser: 'profil', monuments: 'collection', pass: 'qg' };")
s = rep(s, "    if(tab.dataset.tab === 'qg') ouvrirQG();\n",
           "    if(tab.dataset.tab === 'qg') ouvrirQG();\n    if(tab.dataset.tab === 'pass') chargerPass();   // patch254\n")
s = rep(s, "  chargerPom();   // patch160\n", "  chargerPom();   // patch160\n  chargerPass();   // patch254\n")

# titres
s = rep(s, "const TITRES = { parrain: 'Le Parrain' };",
"""const TITRES = { parrain: 'Le Parrain',
  // patch254 : les titres du pass « Brumes d'automne »
  'pass-s2-mecene': 'Mécène d’automne', 'pass-s2-recrue': 'Recrue d’automne', 'pass-s2-vignes': 'Seigneur des vignes',
  'pass-s2-brumes': 'Gardien des brumes', 'pass-s2-legende': 'Légende de la saison 2', 'pass-s2-veteran': 'Vétéran de la saison 2' };""")
s = rep(s, "t === 'parrain' ? '5 amis invités et actifs' : '']));",
           "t === 'parrain' ? '5 amis invités et actifs' : t.startsWith('pass-') ? 'Pass de saison' : '']));")

# la fiche d'achat sait vendre un pass
s = rep(s, "  const quoi = a.type === 'habillage' ? `<b>l'habillage ${echapperTexte(nom)}</b> sur tous tes paquets`",
           "  const quoi = a.type === 'pass' ? `<b>le ${echapperTexte(nom)}</b> : ses 10 récompenses, dont tout de suite celles des niveaux que tu as déjà atteints`   // patch254\n    : a.type === 'habillage' ? `<b>l'habillage ${echapperTexte(nom)}</b> sur tous tes paquets`")
s = rep(s, "{ dos: 'Dos de carte', skin: 'Skin de carte', collection: 'Collection · dos + skin' }[a.type]",
           "{ dos: 'Dos de carte', skin: 'Skin de carte', collection: 'Collection · dos + skin', pass: 'Pass de saison' }[a.type]")
s = rep(s, "function bqeGrandApercu(a){\n",
           "function bqeGrandApercu(a){\n  if(a.type === 'pass') return `<div class=\"ps-fiche-apercu\">${passFeuilles(14)}<b>${echapperTexte(a.nom || 'Pass de saison')}</b><span>20 niveaux · 10 récompenses du pass</span></div>`;   // patch254\n")

MOTEUR = r"""
// ---------- patch254 : le pass de saison ----------
let passEtat = null;
const PS_QUETES_JOUR = 13;   // 5 quêtes Terra + le bonus + 7 quêtes Front
const PS_ICO = {
  tp:   '<svg viewBox="0 0 56 56" aria-hidden="true"><circle cx="28" cy="28" r="20" fill="#E8B931" stroke="#7A5410" stroke-width="2.5"/><text x="28" y="34" text-anchor="middle" font-family="Big Shoulders Display, Impact" font-weight="900" font-size="17" fill="#5A3A06">TP</text></svg>',
  energie: '<svg viewBox="0 0 56 56" aria-hidden="true"><path d="M31 6L14 31h11l-3 19 18-27H29z" fill="#7DD3FC" stroke="#0B3A5A" stroke-width="2.2" stroke-linejoin="round"/></svg>',
  titre:'<svg viewBox="0 0 56 56" aria-hidden="true"><rect x="6" y="18" width="44" height="20" rx="10" fill="#1F3A60" stroke="#F2C9A0" stroke-width="2"/><text x="28" y="32" text-anchor="middle" font-family="Instrument Sans, sans-serif" font-weight="700" font-size="9.5" fill="#F2C9A0">TITRE</text></svg>',
  dos:  '<svg viewBox="0 0 56 56" aria-hidden="true"><rect x="15" y="6" width="26" height="44" rx="4" fill="#3A2A1E" stroke="#0B1830" stroke-width="2"/><rect x="18.5" y="9.5" width="19" height="37" rx="2.5" fill="none" stroke="#E8B931" stroke-width="1.5"/><path d="M28 18c4 4 4 9 0 14c-4-5-4-10 0-14z" fill="#E8B931"/></svg>',
  habillage: '<svg viewBox="0 0 56 56" aria-hidden="true"><path d="M12 14h32v34a3 3 0 0 1-3 3H15a3 3 0 0 1-3-3z" fill="#8E2C48" stroke="#0B1830" stroke-width="2"/><path d="M12 14l4-7h24l4 7z" fill="#D97B3A" stroke="#0B1830" stroke-width="2" stroke-linejoin="round"/><path d="M22 30c3-5 9-5 12 0c-3 5-9 5-12 0z" fill="#D97B3A"/></svg>',
  skin: '<svg viewBox="0 0 56 56" aria-hidden="true"><rect x="13" y="6" width="30" height="44" rx="4" fill="#EEF1F5" stroke="#0B1830" stroke-width="2"/><rect x="16" y="9" width="24" height="20" rx="2" fill="#5E7A8C"/><path d="M16 24c5-6 10 2 14-3s7 0 10-2v10H16z" fill="#C8D3DC" opacity=".85"/><rect x="17" y="33" width="16" height="3" rx="1.5" fill="#0B1830"/><rect x="17" y="39" width="10" height="2.5" rx="1.2" fill="#8E9AAF"/></svg>',
};
const PS_TYPE = { tp: 'TerraPoints', energie: 'Énergie', titre: 'Titre', dos: 'Dos de carte', habillage: 'Habillage de paquet', skin: 'Skin de carte' };
const PS_CADENAS = '<svg class="ps-cadenas" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>';
function passFeuilles(n){
  const f = [];
  for(let i = 0; i < n; i++){
    const x = (i * 97) % 1000, y = (i * 53) % 220, r = (i * 37) % 360, c = ['#D97B3A', '#8E2C48', '#E8B931', '#A0522D'][i % 4], k = .6 + (i % 5) * .15;
    f.push(`<path transform="translate(${x} ${y}) rotate(${r}) scale(${k})" d="M0 -10C7 -6 8 4 0 10C-8 4 -7 -6 0 -10Z" fill="${c}" opacity=".55"/>`);
  }
  return `<svg class="ps-feuilles" viewBox="0 0 1000 220" preserveAspectRatio="none" aria-hidden="true">${f.join('')}</svg>`;
}
async function chargerPass(){
  try{
    const { data, error } = await sb.rpc('pass_etat');
    passEtat = error ? null : data;
  }catch(e){ passEtat = null; }
  renderPassQG();
  renderPass();
}
const psEtatRecompense = (r, e) => r.recu ? 'recu' : r.niveau > e.niveau ? 'loin' : (r.payant && !e.possede) ? 'pass' : !r.dispo ? 'bientot' : 'pret';
function psJours(e){ return Math.max(0, Math.ceil((new Date(e.fin) - Date.now()) / 86400000)); }
function renderPassQG(){
  const el = document.getElementById('qgPass');
  if(!el) return;
  const e = passEtat;
  if(!e || !e.recompenses){ el.hidden = true; return; }
  el.hidden = false;
  const prets = e.recompenses.filter(r => psEtatRecompense(r, e) === 'pret').length;
  const pct = e.niveau >= e.niveaux ? 100 : Math.round(100 * e.dans_niveau / e.xp_niveau);
  el.innerHTML = `<div class="qg-tete">
      <span class="ps-qg-n">${e.niveau}</span>
      <div class="qg-titre"><h2>Pass de saison · ${echapperTexte(e.nom)}</h2><p>Niveau ${e.niveau} sur ${e.niveaux} · ${e.actif ? `encore ${psJours(e)} jour${psJours(e) > 1 ? 's' : ''}` : 'saison terminée'}</p></div>
      ${prets ? `<span class="qg-etiquette or">${prets} à réclamer</span>` : ''}
    </div>
    <div class="ps-jauge"><i style="width:${pct}%"></i></div>
    <div class="qg-actions"><button type="button" class="qg-btn plein" id="qgPassBtn">Voir le pass</button><span class="qg-petit">Tes quêtes du jour font avancer le pass.</span></div>`;
}
function renderPass(){
  const el = document.getElementById('passCorps');
  if(!el) return;
  const e = passEtat;
  if(!e || !e.recompenses){
    el.innerHTML = '<p class="collection-empty">Le pass de saison arrive bientôt : tes quêtes du jour le feront avancer.</p>';
    return;
  }
  const jours = psJours(e);
  const pct = e.niveau >= e.niveaux ? 100 : Math.round(100 * e.dans_niveau / e.xp_niveau);
  const jourXp = Number(e.jour_quetes || 0) + Number(e.jour_actions || 0);
  const jourMax = PS_QUETES_JOUR * e.xp_quete + e.plafond_actions;
  const nb = (n) => Number(n || 0).toLocaleString('fr-FR');
  const prix = e.prix ? euros(e.prix) : '';
  const prets = e.recompenses.filter(r => psEtatRecompense(r, e) === 'pret').length;
  const nPass = e.recompenses.filter(r => r.payant).length;
  const atteintesPass = e.recompenses.filter(r => r.payant && r.niveau <= e.niveau).length;
  const achat = e.possede
    ? `<div class="ps-achat ok"><b class="t">Pass débloqué ✓</b><p>Les ${nPass} récompenses du pass sont à toi, au fil des niveaux. Merci pour ton soutien !</p></div>`
    : e.en_vente && e.actif
      ? `<div class="ps-achat"><b class="t">Pass complet · ${prix}</b><p>Débloque les ${nPass} récompenses du pass.${atteintesPass ? ` Tu reçois tout de suite ${atteintesPass > 1 ? `les ${atteintesPass}` : 'celle'} que tu as déjà atteinte${atteintesPass > 1 ? 's' : ''}.` : ''} Achat unique, gardé à vie.</p><button type="button" class="ps-btn" data-ps-acheter>Débloquer le pass</button></div>`
      : `<div class="ps-achat"><b class="t">Pass complet</b><p>${e.actif ? 'Bientôt en vente.' : 'La saison est terminée.'}</p></div>`;
  const cases = e.recompenses.map(r => {
    const st = psEtatRecompense(r, e);
    const etat = st === 'recu' ? '<span class="ps-etat ok">✓ Reçu</span>'
      : st === 'pret' ? `<button type="button" class="ps-etat recl" data-ps-reclamer="${r.niveau}">Réclamer</button>`
      : st === 'pass' ? '<span class="ps-etat">Avec le pass</span>'
      : st === 'bientot' ? '<span class="ps-etat">Bientôt</span>'
      : `<span class="ps-etat">Niveau ${r.niveau}</span>`;
    const nom = r.type === 'titre' ? r.nom.replace(/^Titre /, '') : r.nom;
    return `<div class="ps-niv ${r.niveau <= e.niveau ? 'atteint' : ''} ${r.niveau === e.niveau + 1 ? 'courant' : ''}"><div class="ps-num">${r.niveau}</div>
      <div class="ps-case ${r.payant ? 'pass' : ''} ${st === 'pret' || st === 'recu' ? '' : 'ferme'}">${r.payant ? '<span class="ps-etiq">PASS</span>' : ''}
        ${r.payant && !e.possede ? PS_CADENAS : ''}
        <div class="ps-ico">${PS_ICO[r.type] || ''}</div><div class="ps-nom">${echapperTexte(nom)}</div><div class="ps-type">${PS_TYPE[r.type] || ''}</div>${etat}</div></div>`;
  }).join('');
  el.innerHTML = `<div class="ps-tete">${passFeuilles(26)}
      <div>
        <div class="ps-surtitre">Pass de la saison ${echapperTexte(nomSaison(e.saison).replace('Saison ', ''))} · jusqu’au ${new Date(e.fin).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })}</div>
        <h1 class="ps-h1">${echapperTexte(e.nom)}</h1>
        <div class="ps-niveau"><div class="ps-pastille">${e.niveau}</div>
          <div class="ps-barre"><div class="l"><span>Niveau ${e.niveau} sur ${e.niveaux}</span><span>${e.niveau >= e.niveaux ? '<b>Pass terminé</b>' : `<b>${nb(e.dans_niveau)}</b> / ${nb(e.xp_niveau)} XP`}</span></div>
            <div class="ps-jauge"><i style="width:${pct}%"></i></div>
            <div class="ps-jour">${e.actif ? `Aujourd’hui : ${nb(jourXp)} XP sur ${nb(jourMax)} possibles · encore ${jours} jour${jours > 1 ? 's' : ''}` : 'Saison terminée : réclame tes récompenses avant qu’elles disparaissent.'}</div></div></div>
      </div>${achat}</div>
    <div class="ps-piste-titre"><h2>Les ${e.niveaux} niveaux</h2>${prets > 1 ? `<button type="button" class="qg-btn plein" data-ps-tout>Tout réclamer (${prets})</button>` : '<span>Niveaux impairs : pour tous · niveaux pairs : pass</span>'}</div>
    <div class="ps-piste" id="psPiste">${cases}</div>
    <div class="ps-lignes">
      <div class="ps-bloc"><h3>Gagner de l’XP</h3><ul>
        <li>Chaque quête du jour réclamée <b>+${e.xp_quete} XP</b></li>
        <li>Conquête ou défense réussie <b>+30 XP</b></li>
        <li>Duel classé, Commune du jour <b>+20 XP</b></li>
        <li>Paquet Terra ouvert <b>+10 XP</b></li>
        <li>Plafond des actions <b>${nb(e.plafond_actions)} XP / jour</b></li></ul></div>
      <div class="ps-bloc"><h3>Le rythme</h3><p>${nb(e.xp_niveau)} XP par niveau. Les quêtes du jour comptent plus que le temps passé : impossible de tout finir en 3 jours. Les récompenses « bientôt » arrivent pendant la saison, avant que tu atteignes leur niveau.</p></div>
      <div class="ps-bloc"><h3>Ce qui reste</h3><p>Tout ce que tu gagnes se garde à vie. Le pass payant ne donne que de l’apparence : rien qui fasse gagner au Front. Les titres se choisissent dans ton profil, les objets dans Profil › Personnaliser.</p></div>
    </div>`;
  // la piste s'ouvre sur le niveau en cours
  requestAnimationFrame(() => {
    const piste = document.getElementById('psPiste');
    const cible = piste && piste.querySelector('.ps-niv.courant');
    if(piste && cible && piste.offsetWidth) piste.scrollLeft = Math.max(0, cible.offsetLeft - piste.offsetLeft - piste.offsetWidth / 2 + 59);
  });
}
async function passReclamer(niveau, bouton){
  if(bouton) bouton.disabled = true;
  const { data, error } = await sb.rpc('pass_reclamer', { p_niveau: niveau == null ? null : Number(niveau) });
  if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); if(bouton) bouton.disabled = false; return; }
  const avant = passEtat;
  passEtat = data;
  const n = Number(data.reclamees || 0);
  const r = niveau != null && avant ? avant.recompenses.find(x => x.niveau === Number(niveau)) : null;
  notifier({ type: 'succes', titre: n > 1 ? `${n} récompenses récupérées` : 'Récompense récupérée',
             texte: r ? r.nom + (r.type === 'titre' ? ' : choisis-le dans ton profil.' : r.type === 'dos' || r.type === 'habillage' || r.type === 'skin' ? ' : dans Profil › Personnaliser.' : '') : '' });
  renderPassQG(); renderPass();
  if(typeof loadPackStatus === 'function') loadPackStatus();   // solde et énergie
  if(SAISON2 && typeof majEnergie === 'function') majEnergie();
}
async function passAcheter(){
  const e = passEtat;
  if(!e) return;
  if(!bqeCat){
    const { data, error } = await sb.rpc('euros_catalogue');
    if(error || !data){ notifier({ type: 'erreur', titre: 'Boutique indisponible', texte: 'Réessaie dans un instant.' }); return; }
    bqeCat = data;
  }
  if(bqeCat.peut_acheter === false){ notifier({ type: 'info', titre: 'Pas encore', texte: 'Les achats ne sont pas ouverts pour ton compte.' }); return; }
  bqeCat.articles = bqeCat.articles || [];
  if(!bqeCat.articles.find(x => x.id === e.article))
    bqeCat.articles.push({ id: e.article, type: 'pass', nom: 'Pass ' + e.nom, description: 'Les récompenses du pass de saison', prix_centimes: e.prix, possede: false });
  bqeOuvrirFiche(e.article);
}
document.addEventListener('click', (ev) => {
  const t = ev.target;
  if(t.closest('#qgPassBtn')){ const tab = document.querySelector('.tab[data-tab="pass"]'); if(tab) tab.click(); return; }
  const r = t.closest('[data-ps-reclamer]');
  if(r){ passReclamer(r.dataset.psReclamer, r); return; }
  const tout = t.closest('[data-ps-tout]');
  if(tout){ passReclamer(null, tout); return; }
  if(t.closest('[data-ps-acheter]')) passAcheter();
});
"""
s = rep(s, "function majBadgeQG(){\n", MOTEUR + "\nfunction majBadgeQG(){\n")
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- style.css
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
s += """
/* ---------- patch254 : le pass de saison ---------- */
.ps-feuilles{ position:absolute; inset:0; width:100%; height:100%; pointer-events:none; opacity:.5; }
.ps-tete{ position:relative; overflow:hidden; border-radius:18px; padding:22px 24px; display:grid; grid-template-columns:minmax(0,1fr) auto; gap:18px; align-items:end;
  background: radial-gradient(120% 140% at 0% 0%, rgba(217,123,58,.38), transparent 55%), radial-gradient(90% 120% at 100% 100%, rgba(142,44,72,.45), transparent 60%), var(--nuit);
  border:1px solid rgba(217,123,58,.35); margin-top:12px; }
.ps-tete > *:not(.ps-feuilles){ position:relative; }
.ps-surtitre{ color:#F2C9A0; font-size:.85rem; }
.ps-h1{ font-family:var(--titre); font-weight:900; font-size:2.6rem; line-height:.95; margin:4px 0 10px; }
.ps-niveau{ display:flex; align-items:center; gap:12px; }
.ps-pastille{ width:54px; height:54px; border-radius:50%; display:grid; place-items:center; font-family:var(--titre); font-weight:900; font-size:1.6rem; background:var(--nuit); border:3px solid var(--c-legendaire, #F0B429); flex:none; }
.ps-barre{ flex:1; min-width:180px; }
.ps-barre .l{ display:flex; justify-content:space-between; gap:10px; font-size:.82rem; color:var(--brume); margin-bottom:5px; }
.ps-barre .l b{ color:#fff; }
.ps-jauge{ height:10px; border-radius:6px; background:rgba(255,255,255,.1); overflow:hidden; }
.ps-jauge i{ display:block; height:100%; border-radius:6px; background:linear-gradient(90deg, #D97B3A, #F0B429); }
.ps-jour{ font-size:.78rem; color:var(--brume); margin-top:7px; }
.ps-achat{ background:rgba(11,24,48,.72); border:1px solid rgba(240,180,41,.45); border-radius:14px; padding:14px 16px; width:270px; }
.ps-achat.ok{ border-color:rgba(123,224,166,.45); }
.ps-achat b.t{ font-family:var(--titre); font-size:1.25rem; display:block; }
.ps-achat p{ margin:4px 0 10px; font-size:.8rem; color:var(--brume); line-height:1.4; }
.ps-achat.ok p{ margin-bottom:0; }
.ps-btn{ font-family:var(--titre); font-weight:800; font-size:1.1rem; border-radius:10px; padding:9px 16px; cursor:pointer; border:0; background:var(--c-legendaire, #F0B429); color:#1a0d02; width:100%; }
@media (max-width:760px){ .ps-tete{ grid-template-columns:1fr; padding:18px; } .ps-achat{ width:auto; } .ps-h1{ font-size:2.1rem; } }
.ps-piste-titre{ display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; margin:22px 2px 10px; }
.ps-piste-titre h2{ font-family:var(--titre); font-weight:800; font-size:1.3rem; margin:0; }
.ps-piste-titre span{ color:var(--brume); font-size:.8rem; }
.ps-piste{ display:flex; gap:10px; overflow-x:auto; padding:12px 2px 14px; scroll-snap-type:x proximity; }
.ps-niv{ flex:none; width:118px; scroll-snap-align:start; display:flex; flex-direction:column; gap:6px; }
.ps-num{ text-align:center; font-family:var(--titre); font-weight:800; font-size:1rem; color:var(--brume); }
.ps-niv.atteint .ps-num{ color:var(--c-legendaire, #F0B429); }
.ps-niv.courant .ps-num{ color:#fff; }
.ps-case{ border-radius:12px; padding:10px 8px 9px; min-height:128px; display:flex; flex-direction:column; align-items:center; gap:6px; text-align:center;
  background:var(--nuit-2); border:1.5px solid rgba(169,188,212,.14); position:relative; }
.ps-case.pass{ background:linear-gradient(180deg, rgba(142,44,72,.35), rgba(22,44,75,.9)); border-color:rgba(217,123,58,.4); }
.ps-ico{ width:56px; height:56px; display:grid; place-items:center; }
.ps-ico svg{ width:56px; height:56px; }
.ps-nom{ font-size:.76rem; line-height:1.2; font-weight:600; }
.ps-type{ font-size:.66rem; color:var(--brume); }
.ps-etat{ margin-top:auto; font-size:.7rem; }
.ps-etat.ok{ color:#7BE0A6; }
.ps-etat.recl{ background:var(--c-legendaire, #F0B429); color:#1a0d02; border:0; border-radius:7px; padding:3px 9px; font-weight:700; font-family:var(--titre); font-size:.85rem; cursor:pointer; }
.ps-case.ferme .ps-ico, .ps-case.ferme .ps-nom{ opacity:.55; }
.ps-cadenas{ position:absolute; top:6px; right:6px; width:18px; height:18px; color:#F2C9A0; }
.ps-etiq{ position:absolute; top:-8px; left:50%; transform:translateX(-50%); font-size:.6rem; font-weight:700; background:#D97B3A; color:#1a0d02; padding:1px 7px; border-radius:6px; white-space:nowrap; }
.ps-lignes{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:10px; }
@media (max-width:760px){ .ps-lignes{ grid-template-columns:1fr; } }
.ps-bloc{ background:var(--nuit); border:1px solid rgba(169,188,212,.14); border-radius:14px; padding:14px 16px; }
.ps-bloc h3{ font-family:var(--titre); font-weight:800; font-size:1.1rem; margin:0 0 8px; }
.ps-bloc ul{ margin:0; padding-left:0; list-style:none; font-size:.82rem; line-height:1.55; color:var(--brume); }
.ps-bloc li{ display:flex; justify-content:space-between; gap:10px; }
.ps-bloc li b{ color:#fff; white-space:nowrap; }
.ps-bloc p{ margin:0; font-size:.82rem; line-height:1.5; color:var(--brume); }
.qg-carte.ps-qg{ position:relative; overflow:hidden; border-color:rgba(217,123,58,.4);
  background: radial-gradient(120% 160% at 0% 0%, rgba(217,123,58,.22), transparent 60%), var(--nuit-2, #162C4B); }
.ps-qg-n{ width:38px; height:38px; border-radius:50%; display:grid; place-items:center; font-family:var(--titre); font-weight:900; font-size:1.2rem; border:2.5px solid var(--c-legendaire, #F0B429); flex:none; }
.qg-carte.ps-qg .ps-jauge{ height:8px; }
.ps-fiche-apercu{ position:relative; overflow:hidden; width:100%; min-height:150px; border-radius:14px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:4px;
  background: radial-gradient(120% 140% at 0% 0%, rgba(217,123,58,.45), transparent 55%), radial-gradient(90% 120% at 100% 100%, rgba(142,44,72,.55), transparent 60%), #0F1F38; }
.ps-fiche-apercu b{ position:relative; font-family:var(--titre); font-weight:900; font-size:1.7rem; }
.ps-fiche-apercu span{ position:relative; color:#F2C9A0; font-size:.8rem; }
"""
f.write_text(s, encoding='utf-8')
print('patch254 ok')
