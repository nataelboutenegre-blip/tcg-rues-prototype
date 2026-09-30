# -*- coding: utf-8 -*-
u"""
patch47 — On ne construit un onglet que lorsqu'on l'ouvre.

LE PROBLEME
  A la connexion, le jeu fabrique le contenu HTML de plusieurs onglets que
  le joueur n'a pas ouverts et n'ouvrira peut-etre jamais. Chez Oshannir,
  cela fait 19 591 elements pour la Collection, 7 463 pour la Bourse et
  2 538 pour la Defense — 29 592 elements construits avant le moindre clic,
  alors que l'onglet affiche au demarrage est le Tirage.

LE PRINCIPE
  Cinq fonctions de rendu commencent desormais par une question : mon
  panneau est-il a l'ecran ? Si non, elles notent qu'il y a du travail en
  attente et s'arretent la. Quand le joueur ouvre l'onglet, le travail en
  attente est execute avant qu'il ne voie quoi que ce soit.

  Les donnees, elles, continuent d'etre chargees comme avant : seule la
  fabrication du HTML est repoussee. Rien ne devient plus lent a l'usage,
  et rien n'arrive plus tard qu'avant.

LE PIEGE EVITE
  renderMenaces() ne fait pas que dessiner une liste : c'est elle qui pose
  la pastille rouge sur l'onglet Defense. Repousser la fonction entiere
  aurait supprime l'alerte « on t'attaque » pour tout joueur qui n'ouvre
  pas l'onglet — exactement ceux a qui elle sert. La garde est donc placee
  APRES la pastille, pas avant.
"""
import io, os

BASE = os.path.dirname(os.path.abspath(__file__))

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


js = lire('app.js')

# --- 1. le mecanisme -------------------------------------------------------
js = rempl(js,
u"""function renderCollection(){""",
u"""// ---------- Rendu differe des onglets fermes ----------
// Fabriquer le HTML d'un onglet qu'on ne regarde pas coute exactement aussi
// cher que celui qu'on regarde. On note le travail et on le fait a
// l'ouverture, juste avant que le panneau devienne visible.
const RENDUS_EN_ATTENTE = new Map();   // nom d'onglet -> Set de fonctions

function panneauOuvert(onglet){
  const p = document.getElementById('panel-' + onglet);
  return !!p && p.classList.contains('active');
}

// true => l'appelant doit s'arreter, le rendu se fera a l'ouverture
function rendreALOuverture(onglet, fn){
  if(panneauOuvert(onglet)) return false;
  if(!RENDUS_EN_ATTENTE.has(onglet)) RENDUS_EN_ATTENTE.set(onglet, new Set());
  RENDUS_EN_ATTENTE.get(onglet).add(fn);
  return true;
}

function faireLesRendusEnAttente(onglet){
  const attente = RENDUS_EN_ATTENTE.get(onglet);
  if(!attente || attente.size === 0) return;
  RENDUS_EN_ATTENTE.delete(onglet);
  for(const fn of attente){
    try { fn(); }
    catch(e){ console.error('rendu differe (' + onglet + ')', e); }
  }
}

function renderCollection(){
  if(rendreALOuverture('collection', renderCollection)) return;""",
u'mecanisme de rendu differe + garde sur renderCollection')

# --- 2. les autres gardes --------------------------------------------------
js = rempl(js,
u"""function renderSellableGrid(){""",
u"""function renderSellableGrid(){
  if(rendreALOuverture('bourse', renderSellableGrid)) return;""",
u'garde sur renderSellableGrid')

js = rempl(js,
u"""function renderBoucliers(){""",
u"""function renderBoucliers(){
  if(rendreALOuverture('defense', renderBoucliers)) return;""",
u'garde sur renderBoucliers')

js = rempl(js,
u"""function renderCombatGrid(){""",
u"""function renderCombatGrid(){
  if(rendreALOuverture('combat', renderCombatGrid)) return;""",
u'garde sur renderCombatGrid')

# renderMenaces : la pastille rouge d'abord, la garde ensuite
js = rempl(js,
u"""    badge.title = enDanger.length > 1 ? `${enDanger.length} communes attaquées` : 'Une commune attaquée';
  }
  const bloc = document.getElementById('combatMenaces');""",
u"""    badge.title = enDanger.length > 1 ? `${enDanger.length} communes attaquées` : 'Une commune attaquée';
  }
  // la pastille est posee, elle : elle previent le joueur qui n'ouvre pas
  // l'onglet, c'est precisement a lui qu'elle sert
  if(rendreALOuverture('defense', renderMenaces)) return;
  const bloc = document.getElementById('combatMenaces');""",
u'garde sur renderMenaces, apres la pastille')

# --- 3. executer le travail en attente a l'ouverture -----------------------
js = rempl(js,
u"""    document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
    if(tab.dataset.tab === 'territoire') sizeMapWrap(window.__mapAspectRatio);""",
u"""    document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
    // le panneau vient de devenir visible : on rattrape ce qu'on avait
    // repousse, avant que le joueur ne voie un onglet vide
    faireLesRendusEnAttente(tab.dataset.tab);
    if(tab.dataset.tab === 'territoire') sizeMapWrap(window.__mapAspectRatio);""",
u'rattrapage a l ouverture d un onglet')

ecrire('app.js', js)
print(u'patch47 applique.')
