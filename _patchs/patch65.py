# -*- coding: utf-8 -*-
u"""
patch65 — Combat et Defense ne font plus qu'un onglet, et la Defense
s'ouvre sur un resume de ce qui s'est passe pendant l'absence.

POURQUOI
  1. La barre du bas du telephone n'a que quatre places (mesure du
     2 octobre). Combat et Defense en prenaient deux pour un seul sujet.
     Fusionnes, ils liberent une place : Collection y entre.
  2. Le badge « 22 » sur Defense ne disait pas ce qui s'etait passe. Le
     joueur qui revient doit lire toute la liste pour comprendre s'il a
     perdu quelque chose. Valide par Natael le 3 octobre (« reveil
     lisible »), prevu pour la saison 2, avance ici.

CE QUE LE JOUEUR VOIT
  - Un seul onglet « Combat », avec deux volets en haut : « Attaquer » et
    « Defendre ». Le badge des communes attaquees passe sur Combat, et se
    repete sur le volet Defendre.
  - Telephone : Tirage · Territoire · Collection · Combat · Plus.
  - En ouvrant Defendre, un encadre « Depuis ta derniere visite » :
    communes perdues (et par qui), attaques repoussees, sieges en cours,
    et en alerte celles qui ne sont plus qu'a une victoire d'etre prises.
    « Tout est calme » sinon.

D'OU VIENNENT LES CHIFFRES
  - Communes perdues : journal(p_mode 'moi', p_type 'conquete'), lignes ou
    le joueur est la cible, posterieures a la derniere visite.
  - Attaques repoussees et sieges : sieges_contre_moi(), deja charge par
    l'onglet. Une attaque est « repoussee » quand la serie de l'attaquant
    est retombee a zero depuis la derniere visite. Cette fonction ne garde
    que les dernieres 24 h : le resume ne remonte donc jamais plus loin.
  - Derniere visite : memorisee dans le navigateur (localStorage
    'tf-defense-vu'). Un autre appareil a sa propre derniere visite.

CE QUI NE CHANGE PAS
  - Les deux panneaux, leur contenu, leurs fonctions. L'onglet Defense
    existe toujours dans la page (cache), pour que les liens
    ?onglet=defense des notifications et le bouton « Bouclier » des fiches
    continuent de marcher.
  - Les notifications push : les filtrer (« seulement a 2 victoires sur
    une rare ou une legendaire ») se fait dans la fonction Edge, pas ici.
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

def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

VOLETS = u"""
      <div class="volets" role="tablist" aria-label="Combat">
        <button type="button" class="volet%s" data-volet="combat" role="tab" aria-selected="%s">Attaquer</button>
        <button type="button" class="volet%s" data-volet="defense" role="tab" aria-selected="%s">Défendre<span class="volet-badge" data-badge-defense hidden></span></button>
      </div>"""


# =========================================================================
#  index.html
# =========================================================================
html = lire('index.html')

# le badge passe de Defense a Combat ; l'onglet Defense reste, cache
html = rempl(html,
u"""          </svg>
        </div>
        Combat
      </div>

      <div class="tab" data-tab="defense">""",
u"""          </svg>
        </div>
        Combat
        <span class="tab-badge" id="combatBadge" hidden></span>
      </div>

      <div class="tab onglet-fusionne" data-tab="defense" aria-hidden="true">""",
u'badge sur Combat, Defense cache')

html = rempl(html,
u"""        Défense
        <span class="tab-badge" id="combatBadge" hidden></span>
      </div>""",
u"""        Défense
      </div>""",
u'ancien badge de Defense')

html = rempl(html,
u"""    <section class="tab-panel" id="panel-combat">
      <h1>Combat</h1>""",
u"""    <section class="tab-panel" id="panel-combat">
      <h1>Combat</h1>""" + VOLETS % (u' actif', u'true', u'', u'false'),
u'volets dans Attaquer')

html = rempl(html,
u"""    <section class="tab-panel" id="panel-defense">
      <h1>Défense</h1>""",
u"""    <section class="tab-panel" id="panel-defense">
      <h1>Combat</h1>""" + VOLETS % (u'', u'false', u' actif', u'true') + u"""
      <div class="reveil" id="reveilDefense" hidden></div>""",
u'volets et reveil dans Defendre')

ecrire('index.html', html)


# =========================================================================
#  app.js
# =========================================================================
js = lire('app.js')

js = rempl(js,
u"""const ONGLETS_BARRE = ['tirage', 'territoire', 'combat', 'defense'];""",
u"""// Combat et Defense ne font plus qu'un onglet (patch65) : la place liberee
// revient a Collection. L'onglet Defense reste dans la page, cache, et
// n'apparait ni dans la barre ni dans le menu.
const ONGLETS_BARRE = ['tirage', 'territoire', 'collection', 'combat'];
const ONGLETS_FUSIONNES = ['defense'];""",
u'barre du telephone')

js = rempl(js,
u"""  .filter((id) => ONGLETS_BARRE.indexOf(id) < 0);""",
u"""  .filter((id) => ONGLETS_BARRE.indexOf(id) < 0 && ONGLETS_FUSIONNES.indexOf(id) < 0);""",
u'menu Plus sans Defense')

js = rempl(js,
u"""// La pastille des attaques suit l'onglet Defense : sur la barre, ou sur "Plus" s'il est dans le menu
function majBadgePlus(){
  const source = document.getElementById('combatBadge');
  const cible = document.getElementById('plusBadge');
  if(!source || !cible) return;
  const dansLeMenu = surTelephone() && ONGLETS_MENU.includes('defense');""",
u"""// La pastille des attaques suit l'onglet Combat : sur la barre, ou sur "Plus" s'il est dans le menu
function majBadgePlus(){
  const source = document.getElementById('combatBadge');
  const cible = document.getElementById('plusBadge');
  if(!source || !cible) return;
  const dansLeMenu = surTelephone() && ONGLETS_MENU.includes('combat');""",
u'pastille Plus')

# onglet Defense actif => Combat allume ; et le reveil se calcule apres les sieges
js = rempl(js,
u"""    tab.classList.add('active');
    majBadgePlus();""",
u"""    tab.classList.add('active');
    // Defense est un volet de Combat : c'est Combat qui s'allume
    if(ONGLETS_FUSIONNES.indexOf(tab.dataset.tab) >= 0){
      const combat = document.querySelector('.tab[data-tab="combat"]');
      if(combat) combat.classList.add('active');
    }
    majBadgePlus();""",
u'Combat allume sur le volet Defendre')

js = rempl(js,
u"""    if(tab.dataset.tab === 'defense'){ loadMenaces(); loadCombat(); renderIntensite('defense'); }""",
u"""    if(tab.dataset.tab === 'defense'){ loadMenaces().then(loadReveil); loadCombat(); renderIntensite('defense'); }""",
u'reveil a l\'ouverture de Defendre')

# la pastille se repete sur le volet Defendre
js = rempl(js,
u"""    badge.title = enDanger.length > 1 ? `${enDanger.length} communes attaquées` : 'Une commune attaquée';
  }""",
u"""    badge.title = enDanger.length > 1 ? `${enDanger.length} communes attaquées` : 'Une commune attaquée';
  }
  document.querySelectorAll('[data-badge-defense]').forEach(b => {
    b.hidden = enDanger.length === 0;
    b.textContent = enDanger.length;
  });""",
u'pastille du volet Defendre')

js = rempl(js,
u"""// ---------- Navigation par onglets ----------""",
u"""// ---------- Volets Attaquer / Defendre ----------
document.addEventListener('click', (e) => {
  const v = e.target.closest('.volet[data-volet]');
  if(!v || v.classList.contains('actif')) return;
  const tab = document.querySelector(`.tab[data-tab="${v.dataset.volet}"]`);
  if(tab) tab.click();
});

// ---------- Le reveil : ce qui s'est passe depuis la derniere visite ----------
// La derniere visite est gardee dans ce navigateur. On la remet a maintenant
// des l'ouverture : la prochaine fois, le resume repartira d'ici.
async function loadReveil(){
  const bloc = document.getElementById('reveilDefense');
  if(!bloc) return;
  const maintenant = Date.now();
  const limite = maintenant - 24 * 3600 * 1000;   // sieges_contre_moi ne garde que 24 h
  let vu = 0;
  try { vu = Number(localStorage.getItem('tf-defense-vu')) || 0; } catch(e){}
  try { localStorage.setItem('tf-defense-vu', String(maintenant)); } catch(e){}
  const depuis = Math.max(vu, limite);

  let pertes = [];
  try {
    const { data, error } = await sb.rpc('journal', { p_mode: 'moi', p_type: 'conquete', p_limite: 50 });
    if(!error) pertes = (data || []).filter(e => e.je_suis_cible && new Date(e.cree_le).getTime() > depuis);
  } catch(e){}

  const repoussees = menaces.filter(m => m.victoires_consecutives === 0 && new Date(m.dernier_round).getTime() > depuis);
  const enCours = menaces.filter(m => m.victoires_consecutives > 0);
  const urgentes = enCours.filter(m => {
    const c = collectionMap.get(m.commune_code);
    const protegee = c && c.bouclierJusqua > maintenant;
    return m.victoires_consecutives >= 2 && !protegee;
  });

  const quand = vu <= limite ? 'ces dernières 24 h'
    : (maintenant - vu < 60000 ? 'à l\u2019instant' : `il y a ${formatDuree(maintenant - vu)}`);
  const nb = (n, un, plusieurs) => `<b>${n}</b><span>${n > 1 ? plusieurs : un}</span>`;
  const noms = (liste, f) => liste.slice(0, 3).map(f).join(', ') + (liste.length > 3 ? ` et ${liste.length - 3} autre${liste.length > 4 ? 's' : ''}` : '');

  if(pertes.length === 0 && repoussees.length === 0 && enCours.length === 0){
    bloc.className = 'reveil calme';
    bloc.innerHTML = `<p class="reveil-calme"><b>Tout est calme</b> depuis ta dernière visite (${quand}).</p>`;
    bloc.hidden = false;
    return;
  }
  bloc.className = 'reveil' + (urgentes.length ? ' alerte' : '');
  bloc.innerHTML = `
    <div class="reveil-tete"><b>Depuis ta dernière visite</b><span>${quand}</span></div>
    <div class="reveil-chiffres">
      <div class="rc perte${pertes.length ? '' : ' zero'}">${nb(pertes.length, 'commune perdue', 'communes perdues')}</div>
      <div class="rc ok${repoussees.length ? '' : ' zero'}">${nb(repoussees.length, 'attaque repoussée', 'attaques repoussées')}</div>
      <div class="rc encours${enCours.length ? '' : ' zero'}">${nb(enCours.length, 'siège en cours', 'sièges en cours')}</div>
    </div>
    ${urgentes.length ? `<p class="reveil-ligne urgent">À une victoire d'être prise : ${noms(urgentes, m => '<b>' + echapperTexte(m.nom) + '</b>')}. Pose un bouclier ou défends-la.</p>` : ''}
    ${pertes.length ? `<p class="reveil-ligne">Perdue${pertes.length > 1 ? 's' : ''} : ${noms(pertes, e => '<b>' + echapperTexte(e.commune_nom || 'une commune') + '</b> (prise par ' + echapperTexte(e.acteur_pseudo || 'un joueur') + ')')}.</p>` : ''}`;
  bloc.hidden = false;
}

// ---------- Navigation par onglets ----------""",
u'volets et reveil')

ecrire('app.js', js)


# =========================================================================
#  style.css
# =========================================================================
css = lire('style.css')
assert u'.volets{' not in css, u'patch65 deja applique'
css += u"""

/* =====================================================================
   patch65 — Combat et Defense fusionnes, et le reveil de la Defense
   ===================================================================== */
.tab.onglet-fusionne{ display:none !important; }

.volets{ display:inline-flex; gap:4px; padding:4px; margin: 2px 0 16px;
  background: var(--nuit-2); border:1px solid rgba(169,188,212,0.16); border-radius:12px; }
.volet{ font: inherit; font-weight:600; font-size:.92rem; color: var(--brume); background:transparent; cursor:pointer;
  border:none; border-radius:9px; padding:8px 18px; display:inline-flex; align-items:center; gap:8px; }
.volet:hover{ color:#fff; }
.volet.actif{ background: var(--c-legendaire); color: var(--encre); cursor:default; }
.volet:focus-visible{ outline:2px solid var(--c-legendaire); outline-offset:2px; }
.volet-badge{ min-width:20px; height:20px; padding:0 6px; border-radius:10px; background: var(--c-rouge); color:#fff;
  font-size:.72rem; font-weight:700; display:inline-flex; align-items:center; justify-content:center; }
.volet-badge[hidden]{ display:none; }

.reveil{ background: var(--nuit-2); border:1px solid rgba(169,188,212,0.16); border-radius:14px;
  padding:14px 16px; margin: 0 0 18px; display:flex; flex-direction:column; gap:10px; }
.reveil[hidden]{ display:none; }
.reveil.alerte{ border-color: rgba(229,72,77,0.55); box-shadow: inset 3px 0 0 var(--c-rouge); }
.reveil-tete{ display:flex; flex-wrap:wrap; align-items:baseline; justify-content:space-between; gap:4px 12px; }
.reveil-tete b{ font-family: var(--titre); font-weight:900; font-size:1.25rem; letter-spacing:.01em; }
.reveil-tete span{ font-size:.8rem; color:#7F91AB; }
.reveil-chiffres{ display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:8px; }
.rc{ border-radius:10px; padding:10px 12px; background: rgba(169,188,212,0.07); display:flex; flex-direction:column; gap:2px; min-width:0; }
.rc b{ font-family: var(--titre); font-weight:900; font-size:1.8rem; line-height:1; font-variant-numeric: tabular-nums; }
.rc span{ font-size:.78rem; color: var(--brume); }
.rc.perte b{ color: var(--c-rouge); }
.rc.ok b{ color: var(--c-peucommun); }
.rc.encours b{ color: var(--c-legendaire); }
.rc.zero b{ color:#5E6F88; }
.reveil-ligne{ margin:0; font-size:.86rem; color: var(--brume); line-height:1.45; }
.reveil-ligne b{ color:#fff; }
.reveil-ligne.urgent{ color:#FFB4B6; }
.reveil.calme{ border-color: rgba(34,160,107,0.4); }
.reveil-calme{ margin:0; color: var(--brume); font-size:.9rem; }
.reveil-calme b{ color: var(--c-peucommun); }

@media (max-width: 560px){
  .volets{ display:flex; }
  .volet{ flex:1; justify-content:center; padding:8px 10px; }
  .rc{ padding:8px 9px; }
  .rc b{ font-size:1.5rem; }
  .rc span{ font-size:.7rem; }
}
"""
ecrire('style.css', css)

print(u'patch65 applique : index.html, app.js, style.css')
