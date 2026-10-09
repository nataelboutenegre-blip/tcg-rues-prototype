# -*- coding: utf-8 -*-
u"""
patch89 — Navigation Terra / Front (saison 2), CACHÉE tant que SAISON2 = false
(aperçu « navigation.png » validé le 9 octobre).

Avec SAISON2 = false (saison 1) : rien ne change. Aucune des nouvelles
fonctions ne tourne, le sélecteur n'existe pas dans la page.

Avec SAISON2 = true (au lancement de la saison 2) :
- un sélecteur Terra / Front en haut de la page, avec la ressource de chaque
  mode (points pour Terra, énergie pour Front), mémorisé dans le navigateur ;
- une couleur par mode : vert (Terra), rouge (Front), sur le sélecteur et
  l'onglet actif ;
- la barre du téléphone s'adapte : Terra = Tirage, Collection, QG, Contrat ;
  Front = Tirage, Territoire, QG, Combat ; Plus en 5e place ;
- les onglets d'un mode n'apparaissent pas dans l'autre (ni barre, ni menu,
  ni colonne de l'ordinateur) ; Profil et Communauté sont communs ;
- le menu Plus est rangé en deux parties : le mode, puis le commun ;
- si l'onglet ouvert n'existe pas dans le mode choisi, on revient au Tirage.

Le contenu des onglets n'est PAS encore séparé par mode (le Tirage de Terra
tire encore dans le pot commun, etc.) : c'est l'objet des patchs suivants.
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
assert 'SAISON2' not in js, u'patch89 deja applique'

js = rempl(js, u"const ONGLETS_BARRE = ['tirage', 'territoire', 'qg', 'combat'];",
           u"let ONGLETS_BARRE = ['tirage', 'territoire', 'qg', 'combat'];", 'ONGLETS_BARRE')
js = rempl(js, u"const ONGLETS_MENU = Array.prototype.map",
           u"let ONGLETS_MENU = Array.prototype.map", 'ONGLETS_MENU')

js = rempl(js, u"const ONGLET_PARENT = { defense: 'combat', succes: 'profil', cdj: 'qg', radar: 'qg' };\n",
           u"""const ONGLET_PARENT = { defense: 'combat', succes: 'profil', cdj: 'qg', radar: 'qg' };

// ---------- patch89 : saison 2, deux modes ----------
// SAISON2 = false : la saison 1 tourne comme avant, rien de ce bloc ne
// s'execute. Le passer a true au lancement de la saison 2.
const SAISON2 = false;
const ONGLETS_MODE = {
  terra: { nom: 'Terra', barre: ['tirage', 'collection', 'qg', 'contrat'],
           propres: ['tirage', 'collection', 'qg', 'contrat', 'monuments', 'bourse', 'echange'] },
  front: { nom: 'Front', barre: ['tirage', 'territoire', 'qg', 'combat'],
           propres: ['tirage', 'territoire', 'qg', 'combat', 'collection'] },
};
const ONGLETS_COMMUNS = ['profil', 'communaute'];
let modeJeu = (() => {
  try { return localStorage.getItem('tf-mode') === 'front' ? 'front' : 'terra'; }
  catch(e){ return 'terra'; }
})();
let energieTimer = null;
""", 'bloc SAISON2')

# le menu Plus : en saison 2, rangé par mode puis commun
js = rempl(js, u"""  const entrees = ONGLETS_MENU.map(id => {
    const tab = document.querySelector(`.tab[data-tab="${id}"]`);""",
           u"""  const entree = (id) => {
    const tab = document.querySelector(`.tab[data-tab="${id}"]`);""", 'menu entree 1')
js = rempl(js, u"""    return `<button class="fp-item" data-aller="${id}">${icone}${nom}${nb}</button>`;
  }).join('');
  liste.innerHTML = entrees + `""",
           u"""    return `<button class="fp-item" data-aller="${id}">${icone}${nom}${nb}</button>`;
  };
  let entrees;
  if(SAISON2){
    const propres = ONGLETS_MENU.filter(id => ONGLETS_COMMUNS.indexOf(id) < 0);
    const communs = ONGLETS_MENU.filter(id => ONGLETS_COMMUNS.indexOf(id) >= 0);
    entrees = (propres.length ? `<p class="fp-titre">${ONGLETS_MODE[modeJeu].nom}</p>` + propres.map(entree).join('') : '')
      + `<p class="fp-titre">Commun</p>` + communs.map(entree).join('');
  } else {
    entrees = ONGLETS_MENU.map(entree).join('');
  }
  liste.innerHTML = entrees + `""", 'menu entree 2')

# les fonctions du mode, juste avant le menu Plus
js = rempl(js, u"function construireMenuPlus(){",
           u"""// patch89 : le selecteur Terra / Front et la barre qui suit le mode
const ICONE_ENERGIE = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M13.2 2.5 5.5 13.2h5.3l-1 8.3 7.7-10.7h-5.3z"/></svg>';
function initModes(){
  if(!SAISON2 || document.getElementById('modeBascule')) { appliquerMode(); return; }
  const el = document.createElement('div');
  el.className = 'mode-bascule';
  el.id = 'modeBascule';
  el.setAttribute('role', 'tablist');
  el.setAttribute('aria-label', 'Mode de jeu');
  el.innerHTML = `
    <button class="terra" data-mode="terra" role="tab"><span class="mb-nom">Terra</span><span class="mb-res"><b id="mbPoints">—</b>points</span></button>
    <button class="front" data-mode="front" role="tab"><span class="mb-nom">Front</span><span class="mb-res">${ICONE_ENERGIE}<b id="mbEnergie">—</b>/ 40 énergie</span></button>`;
  const entete = document.querySelector('.content .entete-mobile');
  entete.insertAdjacentElement('afterend', el);
  el.addEventListener('click', (e) => {
    const b = e.target.closest('[data-mode]');
    if(!b || b.dataset.mode === modeJeu) return;
    modeJeu = b.dataset.mode;
    try { localStorage.setItem('tf-mode', modeJeu); } catch(err){}
    appliquerMode();
  });
  appliquerMode();
  majEnergie();
  if(!energieTimer) energieTimer = setInterval(majEnergie, 60000);
}

function appliquerMode(){
  if(!SAISON2) return;
  const m = ONGLETS_MODE[modeJeu];
  const visibles = m.propres.concat(ONGLETS_COMMUNS);
  ONGLETS_BARRE = m.barre.slice();
  ONGLETS_MENU = visibles.filter(id => ONGLETS_BARRE.indexOf(id) < 0);
  document.body.classList.toggle('mode-terra', modeJeu === 'terra');
  document.body.classList.toggle('mode-front', modeJeu === 'front');
  for(const tab of document.querySelectorAll('.tab[data-tab]')){
    const id = tab.dataset.tab;
    if(ONGLETS_FUSIONNES.indexOf(id) >= 0) continue;
    tab.classList.toggle('hors-mode', visibles.indexOf(id) < 0);
    tab.classList.toggle('dans-le-menu', ONGLETS_BARRE.indexOf(id) < 0);
    const i = ONGLETS_BARRE.indexOf(id);
    if(i >= 0) tab.style.setProperty('--ordre-tel', i); else tab.style.removeProperty('--ordre-tel');
  }
  const bascule = document.getElementById('modeBascule');
  if(bascule) bascule.querySelectorAll('[data-mode]').forEach(b => {
    const on = b.dataset.mode === modeJeu;
    b.classList.toggle('on', on);
    b.setAttribute('aria-selected', String(on));
  });
  majBascule();
  // l'onglet ouvert n'existe pas dans ce mode : retour au Tirage
  const actif = document.querySelector('.tab.active[data-tab]');
  const idActif = actif ? actif.dataset.tab : null;
  const parent = idActif && ONGLET_PARENT[idActif] ? ONGLET_PARENT[idActif] : idActif;
  if(!parent || visibles.indexOf(parent) < 0){
    const tirage = document.querySelector('.tab[data-tab="tirage"]');
    if(tirage) tirage.click();
  }
  majBadgePlus();
}

function majBascule(){
  if(!SAISON2) return;
  const el = document.getElementById('mbPoints');
  if(el && packStatusCache && packStatusCache.solde != null) el.textContent = fmtNombre(Number(packStatusCache.solde));
}

async function majEnergie(){
  if(!SAISON2) return;
  const { data, error } = await sb.rpc('front_energie');
  if(error || !data || !data[0]) return;
  const el = document.getElementById('mbEnergie');
  if(el) el.textContent = data[0].energie;
}

function construireMenuPlus(){""", 'fonctions mode')

# les points suivent le solde
js = rempl(js, u"  packStatusCache = data[0];\n  packStatusFetchedAt = Date.now();\n",
           u"  packStatusCache = data[0];\n  packStatusFetchedAt = Date.now();\n  majBascule();\n", 'solde -> bascule')
js = rempl(js, u"  ['soldeValue', 'soldeValueCombat', 'soldeValueDefense'].forEach(id => {\n    const el = document.getElementById(id);\n    if(el) el.textContent = row.solde;\n  });",
           u"  ['soldeValue', 'soldeValueCombat', 'soldeValueDefense'].forEach(id => {\n    const el = document.getElementById(id);\n    if(el) el.textContent = row.solde;\n  });\n  if(SAISON2){ const mb = document.getElementById('mbPoints'); if(mb) mb.textContent = fmtNombre(Number(row.solde)); }",
           'rafraichirSoldes')

# le selecteur se pose au demarrage du jeu (showGame tourne deux fois : initModes ne cree qu'une fois)
js = rempl(js, u"  chargerRadar();\n  verifierVersion();\n",
           u"  chargerRadar();\n  verifierVersion();\n  if(SAISON2) initModes();\n", 'showGame')

ecrire('app.js', js)

# =============================================================================
css = lire('style.css')
assert 'mode-bascule' not in css, u'patch89 deja applique (css)'
css += u'''
/* =====================================================================
   patch89 — Saison 2 : selecteur Terra / Front (n'existe qu'avec SAISON2)
   ===================================================================== */
.mode-bascule{ display:grid; grid-template-columns:1fr 1fr; gap:4px; padding:4px; margin:0 0 16px;
  width:100%; max-width:440px; min-width:0; align-self:flex-start;
  background:rgba(169,188,212,.08); border:1px solid rgba(169,188,212,.16); border-radius:14px; }
.mode-bascule button{ display:flex; flex-direction:column; align-items:flex-start; gap:1px; padding:8px 12px; border:none;
  border-radius:10px; background:none; color:var(--brume); font:inherit; text-align:left; cursor:pointer; min-width:0; }
.mode-bascule button:focus-visible{ outline:2px solid var(--c-legendaire); outline-offset:2px; }
.mode-bascule .mb-nom{ font-family:var(--titre); font-weight:800; font-size:1.05rem; letter-spacing:.03em; text-transform:uppercase; }
.mode-bascule .mb-res{ font-size:.74rem; display:flex; align-items:center; gap:4px; font-variant-numeric:tabular-nums; white-space:nowrap; }
.mode-bascule .mb-res b{ font-weight:600; }
.mode-bascule .mb-res svg{ width:12px; height:12px; flex:none; }
.mode-bascule button.terra.on{ background:linear-gradient(160deg,#1E5A44,#143B2E); color:#E8F6EE; box-shadow:inset 0 0 0 1px rgba(53,185,126,.55); }
.mode-bascule button.terra.on .mb-nom{ color:#5FD39D; }
.mode-bascule button.front.on{ background:linear-gradient(160deg,#5A1E26,#3B141A); color:#FBE9EA; box-shadow:inset 0 0 0 1px rgba(229,72,77,.6); }
.mode-bascule button.front.on .mb-nom{ color:#FF8A8E; }
.tab.hors-mode{ display:none !important; }
body.mode-terra .tab.active, body.mode-terra .tab.active .icon{ color:#5FD39D; }
body.mode-front .tab.active, body.mode-front .tab.active .icon{ color:#FF8A8E; }
.fp-titre{ margin:8px 12px 2px; font-size:.68rem; letter-spacing:.08em; text-transform:uppercase; color: var(--brume); }
@media (max-width: 720px){
  body.mode-terra .tabs-row .tab, body.mode-front .tabs-row .tab{ order: var(--ordre-tel, 20); }
  body.mode-terra .tabs-row .tab-plus, body.mode-front .tabs-row .tab-plus{ order: 10; }
}
'''
ecrire('style.css', css)
print(u'patch89 : OK')
