# -*- coding: utf-8 -*-
u"""
patch191 — des menus ranges (apercu valide le 26 octobre, « Ensemble »
renomme « Joueurs ») :
 - les onglets sont groupes : Jouer / Marche (Terra) ou Mes cartes (Front) /
   Joueurs / Moi, avec un titre de groupe sur PC ;
 - sur PC, le nom de chaque onglet sous son icone ;
 - Monuments devient un volet de Collection (Terra) : Mes cartes / Ma France /
   Collections / Monuments ;
 - les Regles descendent en bas du rail, a cote du Discord ;
 - telephone : la barre du bas ne change pas (Front : Combat avant QG) ; le
   menu « Plus » reprend les memes groupes, en tuiles.
Aucun SQL.
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
assert 'ONGLETS_GROUPES' not in js, u'patch191 deja applique'

js = rempl(js, u"""const ONGLETS_FUSIONNES = ['defense', 'succes', 'cdj', 'radar', 'rafale', 'boutiqueeuros', 'personnaliser'];""",
u"""const ONGLETS_FUSIONNES = ['defense', 'succes', 'cdj', 'radar', 'rafale', 'boutiqueeuros', 'personnaliser', 'monuments'];   // patch191 : monuments""", 'fusionnes')
js = rempl(js, u"""boutiqueeuros: 'boutique', personnaliser: 'profil' };""",
u"""boutiqueeuros: 'boutique', personnaliser: 'profil', monuments: 'collection' };""", 'parent')
js = rempl(js, u"""           propres: ['tirage', 'collection', 'qg', 'contrat', 'monuments', 'bourse', 'echange', 'boutique'] },
  front: { nom: 'Front', barre: ['tirage', 'territoire', 'qg', 'combat'],""",
u"""           propres: ['tirage', 'collection', 'qg', 'contrat', 'bourse', 'echange', 'boutique'] },   // patch191 : monuments dans Collection
  front: { nom: 'Front', barre: ['tirage', 'territoire', 'combat', 'qg'],""", 'modes')
js = rempl(js, u"""const ONGLETS_COMMUNS = CLANS ? ['profil', 'communaute', 'clan'] : ['profil', 'communaute'];""",
u"""const ONGLETS_COMMUNS = CLANS ? ['profil', 'communaute', 'clan'] : ['profil', 'communaute'];
// patch191 : les onglets ranges en groupes (rail PC et menu Plus)
const ONGLETS_GROUPES = {
  terra: [['Jouer', ['tirage', 'collection', 'qg']], ['Marché', ['contrat', 'bourse', 'echange', 'boutique']],
          ['Joueurs', ['communaute', 'clan']], ['Moi', ['profil']]],
  front: [['Jouer', ['tirage', 'territoire', 'combat', 'qg']], ['Mes cartes', ['collection', 'boutique']],
          ['Joueurs', ['communaute', 'clan']], ['Moi', ['profil']]],
};
function groupesDuMode(){
  return ONGLETS_GROUPES[modeJeu].map(([t, ids]) => [t, ids.filter(id => CLANS || id !== 'clan')]);
}
function rangerGroupes(){
  const rangee = document.getElementById('tabsRow');
  if(!rangee) return;
  const mon = rangee.querySelector('.tab[data-tab="monuments"]');
  if(mon) mon.classList.add('onglet-fusionne');
  rangee.querySelectorAll('.tab-groupe').forEach(el => el.remove());
  let n = 0;
  groupesDuMode().forEach(([titre, ids], i) => {
    const h = document.createElement('div');
    h.className = 'tab-groupe' + (i ? '' : ' premier');
    h.textContent = titre;
    h.setAttribute('aria-hidden', 'true');
    h.style.setProperty('--ordre-pc', n++);
    rangee.appendChild(h);
    ids.forEach(id => { const t = rangee.querySelector(`.tab[data-tab="${id}"]`); if(t) t.style.setProperty('--ordre-pc', n++); });
  });
  // les Regles descendent en bas du rail, a cote du Discord (une seule fois)
  const regles = document.getElementById('reglesBtn');
  const pied = document.querySelector('.sidebar-footer');
  if(regles && pied && regles.parentElement !== pied) pied.insertBefore(regles, pied.firstChild);
}""", 'groupes')
js = rempl(js, u"""  majBascule();
  // l'onglet ouvert n'existe pas dans ce mode : retour au Tirage""", u"""  majBascule();
  rangerGroupes();   // patch191
  // l'onglet ouvert n'existe pas dans ce mode : retour au Tirage""", 'appliquerMode')

# Monuments : un volet de Collection
js = rempl(js, u"""function selecteurVueTerra(){
  return `<div class="mf-vue" role="tablist" aria-label="Affichage de la collection">
    <button role="tab" data-tcv="cartes" class="${terraVue === 'cartes' ? 'on' : ''}" aria-selected="${terraVue === 'cartes'}">Mes cartes</button>
    <button role="tab" data-tcv="france" class="${terraVue === 'france' ? 'on' : ''}" aria-selected="${terraVue === 'france'}">Ma France</button>
    <button role="tab" data-tcv="collections" class="${terraVue === 'collections' ? 'on' : ''}" aria-selected="${terraVue === 'collections'}">Collections</button></div>`;
}""", u"""function selecteurVueTerra(actif){
  const a = actif || terraVue;   // patch191 : 'monuments' depuis l'onglet Monuments
  const b = (id, nom) => `<button role="tab" data-tcv="${id}" class="${a === id ? 'on' : ''}" aria-selected="${a === id}">${nom}</button>`;
  return `<div class="mf-vue" role="tablist" aria-label="Affichage de la collection">
    ${b('cartes', 'Mes cartes')}${b('france', 'Ma France')}${b('collections', 'Collections')}${SAISON2 ? b('monuments', 'Monuments') : ''}</div>`;
}
// patch191 : l'onglet Monuments porte le meme selecteur, Monuments allume
function vuesMonuments(){
  const panneau = document.getElementById('panel-monuments');
  if(!panneau || !enTerra()) return;
  let z = document.getElementById('monVues');
  if(!z){
    z = document.createElement('div');
    z.id = 'monVues';
    const titre = panneau.querySelector('h1');
    if(titre) titre.insertAdjacentElement('afterend', z); else panneau.prepend(z);
    z.addEventListener('click', (e) => {
      const v = e.target.closest('[data-tcv]');
      if(!v || v.dataset.tcv === 'monuments') return;
      terraVue = v.dataset.tcv;
      const t = document.querySelector('.tab[data-tab="collection"]');
      if(t) t.click();
    });
  }
  z.innerHTML = selecteurVueTerra('monuments');
}""", 'selecteur')
js = rempl(js, u"""  const v = e.target.closest('[data-tcv]');
  if(v){ if(terraVue !== v.dataset.tcv){ terraVue = v.dataset.tcv; renderCollectionTerra(); } return; }""",
u"""  const v = e.target.closest('[data-tcv]');
  if(v && v.dataset.tcv === 'monuments'){ const t = document.querySelector('.tab[data-tab="monuments"]'); if(t) t.click(); return; }   // patch191
  if(v){ if(terraVue !== v.dataset.tcv){ terraVue = v.dataset.tcv; renderCollectionTerra(); } return; }""", 'clic vue')
js = rempl(js, u"""    if(tab.dataset.tab === 'monuments') loadMonuments();""",
u"""    if(tab.dataset.tab === 'monuments'){ vuesMonuments(); loadMonuments(); }   // patch191""", 'onglet monuments')

# le menu Plus : les memes groupes, en tuiles
js = rempl(js, u"""    return `<button class="fp-item" data-aller="${id}">${icone}${nom}${nb}</button>`;
  };
  let entrees;
  if(SAISON2){""", u"""    return `<button class="fp-item fp-tuile" data-aller="${id}">${icone}<span>${nom}</span>${nb}</button>`;
  };
  let entrees;
  if(SAISON2){   // patch191 : les groupes du rail
    entrees = groupesDuMode().map(([t, ids]) => [t, ids.filter(id => ONGLETS_MENU.indexOf(id) >= 0)])
      .filter(([, ids]) => ids.length)
      .map(([t, ids]) => `<p class="fp-titre">${t}</p><div class="fp-grille">${ids.map(entree).join('')}</div>`).join('');
  } else if(false){""", 'menu plus')
ecrire('app.js', js)

css = lire('style.css')
assert 'patch191' not in css, u'patch191 deja applique (css)'
css += u"""

/* ---------- patch191 : des menus ranges ---------- */
.tab-groupe{ display:none; }
@media (min-width: 721px){
  body.mode-terra .tabs-row .tab, body.mode-front .tabs-row .tab,
  body.mode-terra .tabs-row .tab-groupe, body.mode-front .tabs-row .tab-groupe{ order: var(--ordre-pc, 99); }
  body.mode-terra .tab-groupe, body.mode-front .tab-groupe{
    display:block; font-size:.62rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:#6F84A3;
    padding:10px 12px 3px; margin-top:4px; border-top:1px solid rgba(169,188,212,.12); }
  body.mode-terra .tab-groupe.premier, body.mode-front .tab-groupe.premier{ border-top:0; margin-top:0; padding-top:2px; }
}
@media (min-width: 721px) and (hover: hover){
  .app-shell{ padding-left: 84px; }
  .sidebar{ width: 84px; }
  body.mode-terra .tab-groupe, body.mode-front .tab-groupe{ width:68px; padding:9px 0 2px; text-align:center; font-size:.55rem; letter-spacing:.12em; }
  .sidebar:hover .tab-groupe, .sidebar:focus-within .tab-groupe{ text-align:left; padding-left:12px; width:auto; }
  /* le nom sous l'icone, rail ferme comme ouvert */
  .tab:not([data-tab="tirage"]), .sidebar:hover .tab:not([data-tab="tirage"]), .sidebar:focus-within .tab:not([data-tab="tirage"]){
    flex-direction:column; align-items:center; justify-content:center; gap:3px; width:68px;
    padding:7px 2px 6px; font-size:.62rem; font-weight:600; line-height:1.1; white-space:normal; text-align:center; }
  .tab .tab-badge, .sidebar:hover .tab .tab-badge, .sidebar:focus-within .tab .tab-badge{ position:absolute; left:auto; right:10px; top:2px; margin:0; }
  .tab[data-tab="tirage"]{ margin-left:6px; }
  /* les Regles en bas, a cote du Discord */
  .sidebar-footer .regles-btn{ width:44px; height:36px; margin:0 0 6px 12px; }
  .sidebar:hover .sidebar-footer .regles-btn, .sidebar:focus-within .sidebar-footer .regles-btn{ margin-left:0; }
}
/* le menu Plus du telephone : des tuiles par groupe */
.fp-grille{ display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:6px; padding:0 6px; }
.fp-item.fp-tuile{ position:relative; flex-direction:column; justify-content:center; gap:5px; padding:10px 2px 8px; font-size:.72rem; font-weight:600;
  text-align:center; background: rgba(169,188,212,.06); }
.fp-item.fp-tuile svg{ width:22px; height:22px; }
.fp-item.fp-tuile span{ overflow-wrap:anywhere; line-height:1.1; }
.fp-item.fp-tuile .fp-badge{ position:absolute; top:4px; right:6px; margin:0; }
#monVues{ margin: 2px 0 10px; }
"""
ecrire('style.css', css)
print(u'patch191 applique. Lancer : python3 maj-version.py')
