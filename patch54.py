# -*- coding: utf-8 -*-
u"""
patch54 — Les « … » a la place du pourcentage de reussite (signale par Oshannir).

CE QU'IL VOYAIT
  Dans Combat, le bouton Attaquer affiche le cout et la chance de reussite.
  Chez lui, une carte sur deux affichait « … » a la place du pourcentage,
  et un rechargement force n'y changeait rien.

CE QUE C'ETAIT
  Reproduit sur le banc avec 900 cibles : les 400 premieres cartes ont leur
  pourcentage, toutes les suivantes affichent « … ». Exactement 400, et pas
  une de plus.

  La cause est une limite que j'avais posee moi-meme. Le serveur refuse de
  calculer plus de 400 communes d'un coup — c'est une protection, elle est
  bonne. Le navigateur, lui, envoyait « les 400 premieres » une fois pour
  toutes, au chargement de l'onglet. Un joueur avec moins de 400 cibles ne
  voyait jamais rien ; Oshannir en a davantage, donc tout ce qui venait
  apres etait condamne au tiret. Et ce n'etait pas qu'une question de
  nombre : des que la liste etait filtree, triee par proximite ou reduite
  aux combats en cours, les 400 envoyees n'etaient meme plus celles que le
  joueur avait sous les yeux.

CE QUE JE FAIS
  On ne demande plus « les 400 premieres de la liste » mais « celles qui
  sont a l'ecran et dont on ignore encore la chance ». Le cache se remplit
  au fur et a mesure du defilement, par paquets, sans jamais depasser la
  limite du serveur et sans jamais redemander deux fois la meme commune.

  Quand la reponse arrive, seul le texte des boutons concernes change : la
  grille n'est pas redessinee, donc le joueur ne perd pas sa place.

  Changer d'intensite vide le cache — les chances ne sont plus les memes —
  et le remplit a nouveau pour ce qui est affiche.

DEUXIEME CORRECTION, DANS LE MEME FICHIER
  La liste des cibles s'arretait silencieusement a 1 000 lignes : c'est la
  limite de l'API, et elle n'avait pas ete paginee ici alors qu'elle l'est
  deja pour la carte. Tant qu'il y a moins de 1 000 communes rares et
  legendaires detenues par les autres joueurs, personne ne s'en apercoit.
  Au-dela, des cibles deviennent invisibles sans message. On reutilise la
  pagination qui existe deja.
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

# ---------------------------------------------------------------------------
#  1. La liste des cibles ne s'arrete plus a 1 000
# ---------------------------------------------------------------------------
js = rempl(js,
u"""  const champsCible = 'communes!inner(nom,departement,tier,latitude,longitude), joueurs(pseudo)';
  let { data: cibles, error } = await sb
    .from('possessions')
    .select('commune_code, joueur_id, acquired_at, bouclier_jusqua, ' + champsCible)
    .neq('joueur_id', uid)
    .in('communes.tier', ['rare','legendaire']);
  if(error){
    ({ data: cibles, error } = await sb.from('possessions').select('commune_code, joueur_id, acquired_at, ' + champsCible)
      .neq('joueur_id', uid).in('communes.tier', ['rare','legendaire']));
  }""",
u"""  const champsCible = 'communes!inner(nom,departement,tier,latitude,longitude), joueurs(pseudo)';
  // Sans pagination, l'API s'arrete a 1 000 lignes et des cibles disparaissent
  // sans message. Meme precaution que pour les possessions des autres joueurs.
  let { data: cibles, error } = await toutesLesLignes(() => sb
    .from('possessions')
    .select('commune_code, joueur_id, acquired_at, bouclier_jusqua, ' + champsCible)
    .neq('joueur_id', uid)
    .in('communes.tier', ['rare','legendaire']));
  if(error){
    ({ data: cibles, error } = await toutesLesLignes(() => sb
      .from('possessions').select('commune_code, joueur_id, acquired_at, ' + champsCible)
      .neq('joueur_id', uid).in('communes.tier', ['rare','legendaire'])));
  }""",
u'pagination des cibles de combat')


# ---------------------------------------------------------------------------
#  2. Les chances suivent ce qui est affiche
# ---------------------------------------------------------------------------
ANCIEN = u"""// Les vraies chances et le vrai coût, calculés par le serveur pour toutes
// les cibles affichées. Avant ce patch, l'onglet Combat montrait le taux
// nominal de l'intensité, le même pour toute la France : deux écrans
// donnaient deux nombres pour la même commune.
//
// Un seul appel, gardé en mémoire. La requête coûte environ 900 ms pour
// 200 cibles : acceptable au chargement, hors de question à chaque frappe
// dans la recherche. Les filtres relisent ce cache.
let chancesCibles = new Map();
let chancesPour = null;     // l'intensité pour laquelle le cache est valable

async function chargerChancesCibles(){
  // le serveur refuse au-delà de 400 ; on n'envoie de toute façon que ce
  // qui est affichable
  const codes = combatCibles.slice(0, 400).map(c => c.commune_code);
  const voulue = intensiteChoisie;
  if(!codes.length){
    chancesCibles = new Map();
    chancesPour = voulue;
    return;
  }
  try{
    const { data, error } = await sb.rpc('apercu_attaques',
      { p_codes: codes, p_intensite: voulue });
    if(error) throw error;
    const m = new Map();
    for(const r of (data || [])){
      m.set(r.commune_code, { chances: r.chances, cout: r.cout });
    }
    chancesCibles = m;
    chancesPour = voulue;
  }catch(e){
    // Le serveur n'a pas répondu. On n'invente pas un pourcentage : les
    // cartes afficheront un tiret. Un faux nombre serait pire que pas de
    // nombre du tout — c'est exactement ce qui a produit ce bug.
    console.warn('TERRAFRONT chances groupées indisponibles', e);
    chancesCibles = new Map();
    chancesPour = null;
  }
  renderCombatGrid();
}"""

NOUVEAU = u"""// Les vraies chances et le vrai coût, calculés par le serveur. L'onglet
// Combat montrait auparavant le taux nominal de l'intensité, le même pour
// toute la France : deux écrans donnaient deux nombres pour la même commune.
//
// On ne demande pas la liste entière : le serveur refuse au-delà de 400
// communes d'un coup, et c'est une bonne protection. On demande donc ce qui
// est À L'ÉCRAN et qu'on ne connaît pas encore, au fur et à mesure du
// défilement. Le cache ne se vide jamais tout seul : une commune déjà
// calculée n'est plus redemandée, y compris après un filtre ou une recherche.
//
// La version précédente envoyait « les 400 premières cibles » une fois pour
// toutes, au chargement. Un joueur qui en avait davantage voyait « … » sur
// tout le reste de la liste, et un filtre suffisait à ce que les 400 envoyées
// ne soient plus celles affichées.
let chancesCibles = new Map();     // code -> { chances, cout }
let chancesPour = null;            // l'intensité à laquelle ce cache correspond
let chancesTimer = null;
let chancesEnVol = false;
const CHANCES_MAX = 400;           // la limite du serveur, à ne pas dépasser

function oublierChances(){
  chancesCibles = new Map();
  chancesPour = intensiteChoisie;
}

// Ce qu'on demande : les premières cibles de la liste AFFICHÉE dont on ignore
// encore la chance. combatAffichees est la liste après filtre, recherche, tri
// par proximité et combats en cours — donc exactement l'ordre dans lequel le
// joueur va les rencontrer. On en prend un plein chargement d'avance, ce qui
// évite une requête à chaque lot de soixante cartes.
let combatAffichees = [];

function chancesManquantes(){
  const vus = new Set(), out = [];
  for(const c of combatAffichees){
    const code = c.commune_code;
    if(!code || chancesCibles.has(code) || vus.has(code)) continue;
    vus.add(code); out.push(code);
    if(out.length >= CHANCES_MAX) break;
  }
  return out;
}

// Ce qui déclenche une demande : une carte RÉELLEMENT à l'écran sans chiffre.
// La distinction compte — on demande loin devant, mais on ne relance que
// quand le joueur a rattrapé ce qu'on avait pris d'avance.
function chancesIncompletes(){
  const grid = document.getElementById('combatGrid');
  if(!grid) return false;
  for(const b of grid.querySelectorAll('.cible-attaquer[data-code]')){
    if(!chancesCibles.has(b.dataset.code)) return true;
  }
  return false;
}

// On ne redessine pas la grille : on remplace le texte des boutons concernés.
// Redessiner ferait remonter le joueur en haut de la liste au moment précis
// où il la parcourt.
function appliquerChances(){
  const grid = document.getElementById('combatGrid');
  if(!grid || chancesPour !== intensiteChoisie) return;
  for(const b of grid.querySelectorAll('.cible-attaquer[data-code]')){
    const v = chancesCibles.get(b.dataset.code);
    if(!v) continue;
    const pc = b.querySelector('i'), prix = b.querySelector('b');
    if(pc) pc.textContent = v.chances + ' %';
    if(prix) prix.textContent = v.cout + ' pts';
  }
}

// Groupé : l'arrivée d'un lot de soixante cartes ne doit déclencher qu'une
// requête, pas soixante.
function demanderChances(){
  clearTimeout(chancesTimer);
  chancesTimer = setTimeout(envoyerChances, 180);
}

async function envoyerChances(){
  if(chancesEnVol) return;              // la fin de la requête en cours relancera
  if(chancesPour !== intensiteChoisie) oublierChances();
  // rien d'incomplet à l'écran : l'avance prise au tour précédent suffit
  if(!chancesIncompletes()) return;
  const codes = chancesManquantes();
  if(!codes.length) return;
  const voulue = intensiteChoisie;
  chancesEnVol = true;
  try{
    const { data, error } = await sb.rpc('apercu_attaques',
      { p_codes: codes, p_intensite: voulue });
    if(error) throw error;
    // le joueur a pu changer d'intensité pendant la requête : la réponse ne
    // vaut plus rien
    if(voulue !== intensiteChoisie) return;
    for(const r of (data || [])){
      chancesCibles.set(r.commune_code, { chances: r.chances, cout: r.cout });
    }
    appliquerChances();
    // des cartes ont pu arriver pendant la requête
    if(chancesIncompletes()) demanderChances();
  }catch(e){
    // Le serveur n'a pas répondu. On n'invente pas un pourcentage : les
    // cartes gardent leur tiret, et on ne relance pas en boucle. Un faux
    // nombre serait pire que pas de nombre du tout.
    console.warn('TERRAFRONT chances indisponibles', e);
  }finally{
    chancesEnVol = false;
  }
}"""

js = rempl(js, ANCIEN, NOUVEAU, u'le chargement progressif des chances')

# --- les deux appels ---------------------------------------------------------
js = rempl(js,
u"""  combatSieges = new Map((mesSieges || []).map(s => [s.commune_code, s]));
  renderCombatGrid();
  chargerChancesCibles();
}""",
u"""  combatSieges = new Map((mesSieges || []).map(s => [s.commune_code, s]));
  renderCombatGrid();
  demanderChances();
}""",
u'appel au chargement de l\'onglet')

js = rempl(js,
u"""  renderMenaces();
  // les chances dépendent de l'intensité : le cache ne vaut plus
  chargerChancesCibles();
});""",
u"""  renderMenaces();
  // les chances dépendent de l'intensité : le cache ne vaut plus
  oublierChances();
  demanderChances();
});""",
u'appel au changement d\'intensite')

# --- la grille previent quand des cartes arrivent -----------------------------
js = rempl(js,
u"""  // la signature dit si c'est un nouveau filtrage ou un simple rafraichissement
  const signature = [combatFilterTier, searchText, combatProximite,
                     combatRayonKm, combatEnCours, cibles.length].join('|');
  afficherParLots(grid, cibles, carteCible, signature);
}""",
u"""  // la signature dit si c'est un nouveau filtrage ou un simple rafraichissement
  const signature = [combatFilterTier, searchText, combatProximite,
                     combatRayonKm, combatEnCours, cibles.length].join('|');
  combatAffichees = cibles;
  afficherParLots(grid, cibles, carteCible, signature);
  demanderChances();
}

// Les lots suivants sont ajoutés par afficherParLots, qui ne prévient
// personne. Plutôt que de lui ajouter un rappel — elle sert à cinq grilles
// qui n'en ont pas besoin — on surveille la grille : chaque arrivée de cartes
// redemande ce qui manque. Sans sous-arbre, donc le changement de texte des
// boutons ne se redéclenche pas lui-même.
(function surveillerGrilleCombat(){
  const grid = document.getElementById('combatGrid');
  if(!grid || !('MutationObserver' in window)) return;
  new MutationObserver(demanderChances).observe(grid, { childList: true });
})();""",
u'surveillance de la grille')

ecrire('app.js', js)
print(u'patch54 applique.')
