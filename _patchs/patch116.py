# -*- coding: utf-8 -*-
u"""
patch116 — la vitrine de profil (saison 2).

Chaque joueur expose jusqu'à 5 cartes de sa collection Terra sur sa fiche
de profil, visibles par tous. On la remplit depuis l'onglet Profil ou depuis
sa propre fiche (« Modifier »). Une carte Aurore s'y montre en Aurore.
Une carte vendue disparaît d'elle-même de la vitrine.
Caché tant que SAISON2 = false.
À passer AVANT : _sql/s2-20-vitrine.sql.
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
assert 'blocVitrine' not in js, u'patch116 deja applique'

# 1. la fiche d'un joueur charge sa vitrine en meme temps que son profil
js = rempl(js, u"""  if(!joueurId) return;
  const { data, error } = await sb.rpc('profil_joueur', { p_joueur: joueurId });
  if(error || !data){
    // profil-joueur.sql""", u"""  if(!joueurId) return;
  const [{ data, error }, vitrine] = await Promise.all([
    sb.rpc('profil_joueur', { p_joueur: joueurId }), chargerVitrine(joueurId)]);
  if(error || !data){
    // profil-joueur.sql""", 'fiche chargement')
js = rempl(js, u"""  profilEnCours = data;
  rendreProfil();""", u"""  profilEnCours = data;
  profilEnCours.vitrine = vitrine;
  rendreProfil();""", 'fiche donnees')
js = rempl(js, u"""
        <h3>Territoire</h3>""", u"""
        ${blocVitrine(p.vitrine || [], moi)}

        <h3>Territoire</h3>""", 'fiche bloc')

# 2. l'onglet Profil montre aussi ma vitrine
js = rempl(js, u"""    profilPanneau = data;
  }""", u"""    profilPanneau = data;
    profilPanneau.vitrine = await chargerVitrine(id);
  }""", 'panneau chargement')
js = rempl(js, u"""    ${blocsProfil(p)}
    <div class="pf-boutons">""", u"""    ${blocVitrine(p.vitrine || [], true)}
    ${blocsProfil(p)}
    <div class="pf-boutons">""", 'panneau bloc')
js = rempl(js, u"""  if(e.target.closest('[data-pf="supprimer"]')) ouvrirSuppressionCompte();
});""", u"""  if(e.target.closest('[data-pf="supprimer"]')) ouvrirSuppressionCompte();
  const vt = (profilPanneau || {}).vitrine || [];
  if(e.target.closest('[data-pr="vitrine"]')) ouvrirChoixVitrine(vt, 'panneau');
  if(e.target.closest('[data-vt-voir]')) ouvrirGrandeVitrine(vt, true, (profilPanneau || {}).pseudo, (v) => {
    if(v === 'modifier') setTimeout(() => ouvrirChoixVitrine(vt, 'panneau'), 200);
  });
});""", 'panneau clic')

js += u"""

// ---------- patch116 : la vitrine de profil ----------
// 5 cartes de la collection Terra, choisies par le joueur, visibles par tous
// sur sa fiche. Le serveur ne renvoie que les cartes encore possedees.
async function chargerVitrine(id){
  if(!SAISON2 || !id) return [];
  const { data, error } = await sb.rpc('terra_vitrine', { p_joueur: id });
  if(error){ console.error(error); return []; }
  return (data || []).map(r => ({ code: r.code, nom: r.nom, dept: r.departement,
    tier: TIERS.find(t => t.id === r.tier) || TIERS[TIERS.length - 1], pop: r.population,
    exemplaires: 1, rank: r.rang, tierSize: r.palier_total, aurore: r.aurore ? 1 : 0 }));
}

// cinq cartes cote a cote : un nom de plus de 8 lettres passe en plus petit
function miniVitrine(c){
  return miniTerra({ ...c, exemplaires: 1 }).replace('class="mini-nom', 'class="mini-nom' + (c.nom.length > 8 ? ' vt-l' : ''));
}

const VITRINE_MAX = 20;    // places de la grande vitrine
const VITRINE_FICHE = 5;   // cartes montrees sur la fiche

// Sur la fiche : les 5 premieres. Au-dela, la 5e case montre « +N » et
// invite a ouvrir la grande vitrine.
function blocVitrine(cartes, moi){
  if(!SAISON2 || (!cartes.length && !moi)) return '';
  const cases = [];
  const reste = cartes.length - (VITRINE_FICHE - 1);
  for(let i = 0; i < VITRINE_FICHE; i++){
    const c = cartes[i];
    const plus = i === VITRINE_FICHE - 1 && cartes.length > VITRINE_FICHE;
    cases.push(c ? `<div class="vt-case${plus ? ' vt-a-plus' : ''}">${miniVitrine(c)}${plus ? `<span class="vt-plus">+${reste}</span>` : ''}</div>`
      : `<div class="vt-case vide">${moi ? '<button type="button" class="vt-ajout" data-pr="vitrine" aria-label="Ajouter une carte à ma vitrine">+</button>' : ''}</div>`);
  }
  const lien = cartes.length
    ? `<button type="button" class="vt-modifier" data-vt-voir>Tout voir <span>${cartes.length}/${VITRINE_MAX}</span> ›</button>`
    : (moi ? '<button type="button" class="vt-modifier" data-pr="vitrine">Remplir</button>' : '');
  return `<div class="vt-bloc">
      <div class="vt-titre"><h3>Vitrine</h3>${lien}</div>
      <div class="vt-etagere${cartes.length ? ' cliquable' : ''}"${cartes.length ? ' data-vt-voir' : ''}>${cases.join('')}</div>
      ${moi && !cartes.length ? `<p class="vt-aide">Expose jusqu'à ${VITRINE_MAX} cartes de ta collection : tout le monde les verra sur ton profil.</p>` : ''}
    </div>`;
}

// La grande vitrine : toutes les cartes exposees, en grand. Pour moi, les
// places libres restent visibles, pour donner envie de les remplir.
function ouvrirGrandeVitrine(cartes, moi, pseudo, apres){
  const vides = moi ? VITRINE_MAX - cartes.length : 0;
  const fermer = ouvrirFenetre(`
    <div class="fenetre vt-grande" role="dialog" aria-modal="true" aria-labelledby="vtgTitre">
      <button class="pr-fermer" data-vtg="fermer" aria-label="Fermer">✕</button>
      <p class="vt-surtitre">Vitrine</p>
      <h2 id="vtgTitre">${echapperTexte(pseudo || '')}</h2>
      <p class="vt-compte"><b>${cartes.length}</b> carte${cartes.length > 1 ? 's' : ''} exposée${cartes.length > 1 ? 's' : ''}${moi ? ` sur ${VITRINE_MAX}` : ''}</p>
      <div class="vt-mur">
        ${cartes.map((c, i) => `<div class="vt-place"><span class="vt-rang">${i + 1}</span>${miniTerra({ ...c, exemplaires: 1 })}</div>`).join('')}
        ${Array.from({ length: vides }, () => '<button type="button" class="vt-case vide" data-vtg="modifier" aria-label="Ajouter une carte"><span>+</span></button>').join('')}
      </div>
      ${moi ? '<div class="prix-boutons"><button type="button" class="open-btn" data-vtg="modifier">Modifier ma vitrine</button></div>' : ''}
    </div>`, (v) => { if(apres) apres(v); });
  document.querySelector('#fenetre .vt-grande').addEventListener('click', (e) => {
    const b = e.target.closest('[data-vtg]');
    if(b) fermer(b.dataset.vtg);
  });
}

// depuis une fiche : on ferme la fiche, on ouvre la grande vitrine ou le
// choix, et on revient sur la fiche ensuite
document.getElementById('fenetre').addEventListener('click', (e) => {
  if(!profilEnCours) return;
  const voir = e.target.closest('[data-vt-voir]');
  const modif = e.target.closest('[data-pr="vitrine"]');
  if(!voir && !(modif && profilEnCours.est_moi)) return;
  const p = profilEnCours;
  const cartes = p.vitrine || [];
  if(fermerProfil) fermerProfil(null);
  setTimeout(() => {
    if(modif){ ouvrirChoixVitrine(cartes, 'fiche'); return; }
    ouvrirGrandeVitrine(cartes, !!p.est_moi, p.pseudo, (v) => {
      if(v === 'modifier') setTimeout(() => ouvrirChoixVitrine(cartes, 'fiche'), 200);
      else setTimeout(() => { profilEnCours = p; rendreProfil(); }, 200);
    });
  }, 200);
});

async function ouvrirChoixVitrine(actuelle, retour){
  if(!terraCharge) await chargerCollectionTerra();
  let choix = actuelle.map(c => c.code).filter(code => terraCollection.has(code));
  let recherche = '';
  const rangTier = (t) => TIERS.findIndex(x => x.id === t.id);
  const toutes = [...terraCollection.values()].sort((a, b) =>
    (b.aurore > 0) - (a.aurore > 0) || rangTier(a.tier) - rangTier(b.tier) || a.nom.localeCompare(b.nom, 'fr'));
  const fermer = ouvrirFenetre(`
    <div class="fenetre vt-choix" role="dialog" aria-modal="true" aria-labelledby="vtTitre">
      <h2 id="vtTitre">Ma vitrine</h2>
      <p class="vt-aide">Choisis jusqu'à ${VITRINE_MAX} cartes, dans l'ordre où tu veux les montrer : les ${VITRINE_FICHE} premières s'affichent sur ton profil. Touche une carte de la vitrine pour la retirer.</p>
      <p class="vt-compte" id="vtCompte"></p>
      <div class="vt-etagere vt-bande" id="vtApercu"></div>
      <input type="search" id="vtRecherche" class="bourse-search" placeholder="Rechercher une commune ou un département…" autocomplete="off">
      <div class="vt-grille" id="vtGrille"></div>
      <p class="prix-erreur" id="vtErreur" role="alert"></p>
      <div class="prix-boutons">
        <button type="button" class="open-btn secondary" data-vt="annuler">Annuler</button>
        <button type="button" class="open-btn" data-vt="ok">Enregistrer</button>
      </div>
    </div>`);
  const boite = document.querySelector('#fenetre .vt-choix');
  const erreur = document.getElementById('vtErreur');
  const dessiner = () => {
    const cases = [];
    for(let i = 0; i < VITRINE_MAX; i++){
      const c = choix[i] && terraCollection.get(choix[i]);
      cases.push(c ? `<button type="button" class="vt-case" data-vt-retirer="${echapperTexte(c.code)}" aria-label="Retirer ${echapperTexte(c.nom)}">${miniVitrine(c)}</button>`
                   : `<div class="vt-case vide"><span>${i + 1}</span></div>`);
    }
    const bande = document.getElementById('vtApercu');
    const defil = bande.scrollLeft;
    bande.innerHTML = cases.join('');
    bande.scrollLeft = defil;
    document.getElementById('vtCompte').innerHTML = `<b>${choix.length}</b> / ${VITRINE_MAX}`;
    const q = recherche.trim().toLowerCase();
    const dep = q ? codeDepartement(q) : null;
    const liste = toutes.filter(c => !q || c.nom.toLowerCase().includes(q) || c.dept === dep || c.dept.toLowerCase() === q).slice(0, 150);
    document.getElementById('vtGrille').innerHTML = liste.map(c => {
      const n = choix.indexOf(c.code);
      return `<button type="button" class="vt-carte${n >= 0 ? ' pris' : ''}" data-vt-code="${echapperTexte(c.code)}">
        ${miniVitrine(c)}${n >= 0 ? `<span class="vt-num">${n + 1}</span>` : ''}</button>`;
    }).join('') || '<p class="collection-empty">Aucune carte ne correspond.</p>';
  };
  dessiner();
  document.getElementById('vtRecherche').addEventListener('input', (e) => { recherche = e.target.value; dessiner(); });
  boite.addEventListener('click', async (e) => {
    const r = e.target.closest('[data-vt-retirer]');
    if(r){ choix = choix.filter(x => x !== r.dataset.vtRetirer); erreur.textContent = ''; dessiner(); return; }
    const c = e.target.closest('[data-vt-code]');
    if(c){
      const code = c.dataset.vtCode;
      if(choix.includes(code)) choix = choix.filter(x => x !== code);
      else if(choix.length >= VITRINE_MAX){ erreur.textContent = 'La vitrine est pleine : retire une carte d\\'abord.'; return; }
      else choix.push(code);
      erreur.textContent = '';
      dessiner();
      // la derniere carte ajoutee reste en vue dans la bande
      const bande = document.getElementById('vtApercu');
      const cible = bande.children[Math.max(0, choix.length - 1)];
      if(cible) bande.scrollLeft = Math.max(0, cible.offsetLeft - bande.clientWidth + cible.offsetWidth + 10);
      return;
    }
    const b = e.target.closest('[data-vt]');
    if(!b) return;
    if(b.dataset.vt === 'annuler'){ fermer(null); return; }
    b.disabled = true; b.textContent = 'Enregistrement…';
    const { error } = await sb.rpc('terra_vitrine_definir', { p_codes: choix });
    if(error){ erreur.textContent = messageLisible(error.message); b.disabled = false; b.textContent = 'Enregistrer'; return; }
    fermer(null);
    notifier({ type: 'info', titre: 'Vitrine enregistrée',
               texte: choix.length ? 'Tout le monde peut la voir sur ton profil.' : 'Ta vitrine est vide.' });
    rafraichirPanneauProfil();
    if(retour === 'fiche') setTimeout(() => ouvrirProfil(window.__monId || null), 200);
  });
}
"""
ecrire('app.js', js)

css = lire('style.css')
assert 'vt-etagere' not in css
css += u"""
/* patch116 : la vitrine de profil */
.vt-bloc{ margin:0 0 20px; }
.vt-titre{ display:flex; align-items:baseline; justify-content:space-between; }
.vt-modifier{ font:inherit; font-size:.76rem; font-weight:600; color:var(--c-legendaire); background:none; border:0; padding:0 0 9px; cursor:pointer; }
.vt-modifier span{ color:var(--brume); font-weight:500; }
.vt-etagere.cliquable{ cursor:pointer; }
.vt-a-plus .mini{ filter:brightness(.28) saturate(.6) blur(1px); }
.vt-plus{ position:absolute; inset:0; display:grid; place-items:center; z-index:6; font-family:var(--titre); font-weight:900; font-size:1.5rem; color:#fff; text-shadow:0 2px 8px rgba(0,0,0,.6); }
/* la grande vitrine */
.fenetre.vt-grande{ position:relative; width:min(620px, 100%); max-height:90vh; overflow-y:auto; text-align:center;
  background:
    radial-gradient(80% 40% at 50% 0%, rgba(240,180,41,.16), transparent 70%),
    linear-gradient(180deg, var(--nuit-3, #16294A), var(--nuit, #0B1830) 60%); }
.vt-surtitre{ font-size:.7rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--c-legendaire); margin:0 0 4px; }
.fenetre.vt-grande h2{ text-transform:uppercase; letter-spacing:.02em; margin:0; }
.vt-compte{ font-size:.82rem; color:var(--brume); margin:6px 0 14px; }
.vt-compte b{ color:#fff; }
.vt-mur{ display:grid; grid-template-columns:repeat(auto-fill, minmax(86px, 1fr)); gap:14px 10px; text-align:left; margin-bottom:6px; }
.vt-place{ position:relative; }
.vt-place .mini{ content-visibility:visible; box-shadow:0 10px 18px rgba(0,0,0,.5); }
.vt-rang{ position:absolute; top:-7px; left:-5px; z-index:7; min-width:20px; height:20px; padding:0 5px; border-radius:999px;
  background:var(--c-legendaire); color:var(--encre); font-family:var(--titre); font-weight:900; font-size:.78rem; line-height:20px; text-align:center;
  box-shadow:0 2px 6px rgba(0,0,0,.45); }
.vt-mur .vt-case.vide{ cursor:pointer; color:rgba(169,188,212,.45); font-size:1.5rem; }
.vt-mur .vt-case.vide:hover{ border-color:var(--c-legendaire); color:var(--c-legendaire); }
.vt-mur .vt-case.vide span{ font-family:inherit; font-weight:400; font-size:1.5rem; color:inherit; }
/* la bande des 20 places, dans le choix */
.vt-etagere.vt-bande{ display:flex; overflow-x:auto; scrollbar-width:thin; padding:12px 10px 14px; }
.vt-bande > .vt-case{ flex:0 0 66px; width:66px; min-width:0; }
.vt-bande > .vt-case .mini{ width:100%; }
.vt-etagere{
  display:grid; grid-template-columns:repeat(5, minmax(0, 1fr)); gap:7px;
  padding:14px 10px 16px; border-radius:14px;
  background:
    radial-gradient(90% 70% at 50% 0%, rgba(240,180,41,.13), transparent 70%),
    linear-gradient(180deg, var(--nuit-3, #16294A), var(--nuit, #0B1830));
  box-shadow: inset 0 1px 0 rgba(255,255,255,.06), inset 0 -3px 0 rgba(240,180,41,.25);
}
.vt-case{ position:relative; display:block; min-width:0; padding:0; border:0; background:none; font:inherit; color:inherit; text-align:left; }
.vt-case .mini, .vt-carte .mini{ content-visibility:visible; box-shadow:0 6px 12px rgba(0,0,0,.45); }
.vt-case.vide{ aspect-ratio:2 / 3; border-radius:10px; border:1.5px dashed rgba(169,188,212,.22); display:grid; place-items:center; }
.vt-case.vide span{ font-family:var(--titre); font-weight:900; font-size:1.1rem; color:rgba(169,188,212,.3); }
.vt-ajout{ width:100%; height:100%; border:0; background:none; color:rgba(169,188,212,.55); font-size:1.6rem; cursor:pointer; }
.vt-ajout:hover{ color:var(--c-legendaire); }
.vt-aide{ font-size:.78rem; color:var(--brume); margin:8px 0 0; line-height:1.4; }
/* cinq cartes sur la largeur d'une fiche : on resserre le texte */
.vt-etagere .mini-art, .vt-grille .mini-art{ margin:3px 3px 0; }
.vt-etagere .mini-dept, .vt-grille .mini-dept{ font-size:1.05rem; }
.vt-etagere .mini-infos, .vt-grille .mini-infos{ padding:3px 4px; }
.vt-etagere .mini-nom, .vt-grille .mini-nom{ font-size:.7rem; overflow-wrap:normal; hyphens:auto; -webkit-hyphens:auto; }
.vt-etagere .mini-nom.vt-l, .vt-grille .mini-nom.vt-l{ font-size:.6rem; overflow-wrap:anywhere; }
.vt-etagere .mini-num{ display:none; }
.vt-etagere .mini-rarete, .vt-grille .mini-rarete{ font-size:.5rem; }
.vt-grille .mini-num{ font-size:.5rem; }
.vt-grille .mini-total{ display:none; }
.fenetre.vt-choix{ width:min(560px, 100%); max-height:90vh; overflow-y:auto; text-align:left; }
.vt-choix .vt-etagere{ margin:4px 0 14px; }
.vt-choix .vt-compte{ text-align:left; margin:8px 0 0; }
.vt-choix .bourse-search{ width:100%; margin-bottom:12px; }
.fenetre .vt-grille{ display:grid; grid-template-columns:repeat(auto-fill, minmax(70px, 1fr)); gap:7px; max-height:46vh; overflow-y:auto; padding:4px 2px 6px; }
.vt-carte{ position:relative; padding:0; border:0; background:none; cursor:pointer; border-radius:10px; }
.vt-carte.pris .mini{ outline:2px solid var(--c-legendaire); outline-offset:2px; opacity:.55; }
.vt-num{
  position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); z-index:5;
  width:30px; height:30px; border-radius:50%; display:grid; place-items:center;
  background:var(--c-legendaire); color:var(--encre); font-family:var(--titre); font-weight:900; font-size:1.05rem;
  box-shadow:0 4px 10px rgba(0,0,0,.45);
}
"""
ecrire('style.css', css)
print(u'patch116 applique')
