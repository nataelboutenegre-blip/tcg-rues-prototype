# -*- coding: utf-8 -*-
"""
patch42 — Les chiffres des paliers viennent de la base.

Les comptes (29 318 / 4 392 / 981 / 48) et les seuils (2 000 / 10 000 /
100 000) etaient ecrits en dur a DEUX endroits : le bloc « Toutes les
communes ne se valent pas » de la page d'accueil, et le tableau de
l'onglet Regles. Trois sources pour un meme chiffre avec la base : elles
finiront par diverger, c'est ce qui a mis la barre du bas sur deux lignes
ce matin.

Tout vient maintenant de totaux_paliers(). Les valeurs qui restent dans
le HTML servent de repli : si l'appel echoue, ou si la fonction n'existe
pas encore en base, l'affichage reste celui d'aujourd'hui au lieu de
montrer des trous.

CONSEQUENCE SUR L'ORDRE DES OPERATIONS
  Ce correctif peut partir AVANT la bascule des paliers : tant que
  totaux_paliers() n'existe pas, le repli affiche les valeurs actuelles,
  qui sont justes. Des que la bascule est passee, tout se met a jour tout
  seul, sans deuxieme deploiement. Il n'y a donc aucun moment ou les
  regles mentent.
"""
import io, os, re

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


# ===========================================================================
#  index.html — on marque les endroits a remplir
# ===========================================================================
html = lire('index.html')

# --- le bloc de la page d'accueil ------------------------------------------
html = rempl(html,
u"""          <span class="lp-rar-pastille"></span><b>Commune</b>
          <small>moins de 2 000 hab.</small>
          <p>Les villages. La masse, et 84 % de la carte.</p>""",
u"""          <span class="lp-rar-pastille"></span><b>Commune</b>
          <small data-lp-seuil="commun">moins de 2 000 hab.</small>
          <p>Les villages. La masse, et <span data-lp-pct="commun">84</span> % de la carte.</p>""",
u'accueil : commun')

html = rempl(html,
u"""          <span class="lp-rar-pastille"></span><b>Peu commune</b>
          <small>à partir de 2 000</small>""",
u"""          <span class="lp-rar-pastille"></span><b>Peu commune</b>
          <small data-lp-seuil="peucommun">à partir de 2 000</small>""",
u'accueil : peu commune')

html = rempl(html,
u"""          <span class="lp-rar-pastille"></span><b>Rare</b>
          <small>à partir de 10 000</small>
          <p>Convoitées, et 981 seulement dans tout le pays.</p>""",
u"""          <span class="lp-rar-pastille"></span><b>Rare</b>
          <small data-lp-seuil="rare">à partir de 10 000</small>
          <p>Convoitées, et <span data-lp-n="rare">981</span> seulement dans tout le pays.</p>""",
u'accueil : rare')

html = rempl(html,
u"""          <span class="lp-rar-pastille"></span><b>Légendaire</b>
          <small>à partir de 100 000</small>
          <p>48 dans toute la France, et presque toutes déjà prises.</p>""",
u"""          <span class="lp-rar-pastille"></span><b>Légendaire</b>
          <small data-lp-seuil="legendaire">à partir de 100 000</small>
          <p><span data-lp-n="legendaire">48</span> dans toute la France, et presque toutes déjà prises.</p>""",
u'accueil : legendaire')

# --- la colonne Population du tableau des Regles ---------------------------
for tier, pop in [('legendaire', u'100 000 et plus'),
                  ('rare',       u'10 000 à 99 999'),
                  ('peucommun',  u'2 000 à 9 999'),
                  ('commun',     u'Moins de 2 000')]:
    html = rempl(html,
        u'<td>%s</td>' % pop,
        u'<td data-pop="%s">%s</td>' % (tier, pop),
        u'regles : population %s' % tier)

ecrire('index.html', html)


# ===========================================================================
#  app.js
# ===========================================================================
js = lire('app.js')

js = rempl(js,
u"""let tauxEnCours = false;

async function loadTauxTirage(){""",
u"""let tauxEnCours = false;
let totauxPaliers = null;      // { tier: { total, pop_min, pop_max } }
let totauxDemandes = false;

// Les comptes et les seuils viennent de la base. Le HTML garde les valeurs
// actuelles en repli : si l'appel echoue, ou si totaux_paliers() n'existe
// pas encore, l'affichage reste juste au lieu de montrer des trous.
async function chargerTotauxPaliers(){
  if(totauxPaliers || totauxDemandes) return totauxPaliers;
  totauxDemandes = true;
  try{
    const { data, error } = await sb.rpc('totaux_paliers');
    if(error || !Array.isArray(data) || !data.length) return null;
    const m = {};
    for(const l of data) m[l.tier] = l;
    totauxPaliers = m;
  }catch(e){
    console.warn('TERRAFRONT totaux_paliers indisponible', e);
  }finally{
    totauxDemandes = false;
  }
  return totauxPaliers;
}

// « 50 000 et plus », « 5 000 a 49 999 », « Moins de 1 000 » : les bornes se
// deduisent des paliers voisins, donc un seul chiffre a changer en base
// suffit a corriger les quatre lignes.
function libellePopulation(id, m){
  const ordre = ['commun', 'peucommun', 'rare', 'legendaire'];
  const i = ordre.indexOf(id);
  if(i < 0 || !m[id]) return null;
  const bas = Number(m[id].pop_min);
  const suivant = m[ordre[i + 1]];
  if(!suivant) return fmtNombre(bas) + ' et plus';
  const haut = Number(suivant.pop_min) - 1;
  if(i === 0) return 'Moins de ' + fmtNombre(Number(suivant.pop_min));
  return fmtNombre(bas) + ' à ' + fmtNombre(haut);
}

async function majChiffresPaliers(){
  const m = await chargerTotauxPaliers();
  if(!m) return;
  const grand = Object.values(m).reduce((s, l) => s + Number(l.total || 0), 0);

  for(const id of ['commun', 'peucommun', 'rare', 'legendaire']){
    if(!m[id]) continue;
    const n = Number(m[id].total) || 0;
    const pop = libellePopulation(id, m);

    const cptRegles = document.querySelector('#panel-regles [data-total="' + id + '"]');
    if(cptRegles) cptRegles.textContent = fmtNombre(n);
    const popRegles = document.querySelector('#panel-regles [data-pop="' + id + '"]');
    if(popRegles && pop) popRegles.textContent = pop;

    const seuil = document.querySelector('[data-lp-seuil="' + id + '"]');
    if(seuil && m[id]){
      const suivant = { commun: 'peucommun', peucommun: 'rare',
                        rare: 'legendaire' }[id];
      seuil.textContent = suivant && m[suivant]
        ? (id === 'commun'
            ? 'moins de ' + fmtNombre(Number(m[suivant].pop_min)) + ' hab.'
            : 'à partir de ' + fmtNombre(Number(m[id].pop_min)))
        : 'à partir de ' + fmtNombre(Number(m[id].pop_min));
    }
    const nAccueil = document.querySelector('[data-lp-n="' + id + '"]');
    if(nAccueil) nAccueil.textContent = fmtNombre(n);
    const pctAccueil = document.querySelector('[data-lp-pct="' + id + '"]');
    if(pctAccueil && grand > 0) pctAccueil.textContent = Math.round(100 * n / grand);
  }
}

async function loadTauxTirage(){""",
u'chargement des totaux')

# La jauge se calcule sur le total : il doit etre a jour avant.
js = rempl(js,
u"""  if(tauxEnCours) return;
  tauxEnCours = true;
  try{
    const { data, error } = await sb.rpc('taux_actuels');""",
u"""  if(tauxEnCours) return;
  tauxEnCours = true;
  try{
    // la jauge se calcule sur le total du palier : il doit etre a jour avant
    await majChiffresPaliers();
    const { data, error } = await sb.rpc('taux_actuels');""",
u'totaux avant les taux')

# La page d'accueil s'affiche avant toute connexion : elle a ses propres
# chiffres a remplir, et loadTauxTirage() ne tourne que dans l'onglet Regles.
# initAuth() est la derniere ligne du fichier, donc tout est initialise.
js = rempl(js,
u"""  page.hidden = false;
  window.scrollTo(0, 0);
  dessinerCarteLanding();""",
u"""  page.hidden = false;
  window.scrollTo(0, 0);
  dessinerCarteLanding();
  majChiffresPaliers();""",
u'chiffres de la page d\'accueil')

ecrire('app.js', js)

print(u'patch42 applique.')
