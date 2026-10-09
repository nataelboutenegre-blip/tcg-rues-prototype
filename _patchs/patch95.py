# -*- coding: utf-8 -*-
u"""
patch95 — Combat : les communes et peu communes dans la liste (saison 1).
Demande du 9 octobre au soir. Aucun SQL.

- Deux filtres de plus : « Peu commun » et « Commun ».
- Ces cibles (environ 25 000) ne sont PAS chargées à l'ouverture de
  l'onglet, pour qu'il reste rapide : elles arrivent quand on choisit leur
  filtre, ou quand « Près de mon territoire » est allumé sur « Toutes ».
  Une fois chargées, elles restent (y compris après une attaque).
- Les combats en cours sur une commune ou une peu commune apparaissent
  toujours, même sans avoir chargé leur palier.
- Texte du haut et message « rien à proximité » mis à jour.
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
assert 'combatBasCharges' not in js, u'patch95 deja applique'

# 1. etat + chargement a la demande ----------------------------------------------
js = rempl(js, u"let combatProximite = false;\n", u"""let combatProximite = false;
// patch95 : communs et peu communs, charges a la demande (environ 25 000
// cibles : les charger a chaque ouverture ralentirait tout l'onglet)
const COMBAT_TIERS_BAS = ['commun', 'peucommun'];
let combatBasCharges = new Set();
let combatBasChargement = false;
const tiersCombat = () => ['rare', 'epique', 'legendaire'].concat([...combatBasCharges]);
function combatBasVoulus(){
  if(COMBAT_TIERS_BAS.indexOf(combatFilterTier) >= 0) return [combatFilterTier];
  if(combatProximite && combatFilterTier === 'tous') return COMBAT_TIERS_BAS.slice();
  return [];
}
async function assurerCiblesBas(){
  const manquants = combatBasVoulus().filter(t => !combatBasCharges.has(t));
  if(!manquants.length || combatBasChargement) return;
  combatBasChargement = true;
  renderCombatGrid();
  try{
    const { data: userData } = await sb.auth.getUser();
    const uid = userData.user.id;
    const { data, error } = await toutesLesLignes(() => sb
      .from('possessions')
      .select('commune_code, joueur_id, acquired_at, bouclier_jusqua, communes!inner(nom,departement,tier,latitude,longitude), joueurs(pseudo)')
      .neq('joueur_id', uid)
      .in('communes.tier', manquants));
    if(error) throw error;
    manquants.forEach(t => combatBasCharges.add(t));
    const deja = new Set(combatCibles.map(c => c.commune_code));
    combatCibles = combatCibles.concat((data || []).filter(c => !deja.has(c.commune_code)));
    calculerDistancesCibles();
  }catch(e){
    console.error('TERRAFRONT cibles communes', e);
  }
  combatBasChargement = false;
  renderCombatGrid();
  demanderChances();
  // le filtre a pu changer pendant le chargement
  if(combatBasVoulus().some(t => !combatBasCharges.has(t))) assurerCiblesBas();
}
""", 'etat')

# 2. loadCombat : paliers deja charges + combats en cours -----------------------
js = rempl(js, u"""    .neq('joueur_id', uid)
    .in('communes.tier', ['rare','epique','legendaire']));""", u"""    .neq('joueur_id', uid)
    .in('communes.tier', tiersCombat()));""", 'load 1')
js = rempl(js, u"""      .neq('joueur_id', uid).in('communes.tier', ['rare','epique','legendaire'])));""",
           u"""      .neq('joueur_id', uid).in('communes.tier', tiersCombat())));""", 'load 2')
js = rempl(js, u"""  combatCibles = cibles || [];
  calculerDistancesCibles();
  loadMenaces();""", u"""  combatCibles = cibles || [];
  // un combat en cours sur une commune ou une peu commune doit rester visible
  // meme si son palier n'est pas charge
  const horsListe = (mesSieges || []).map(s => s.commune_code)
    .filter(code => !combatCibles.some(c => c.commune_code === code));
  if(horsListe.length){
    const { data: enPlus } = await sb.from('possessions')
      .select('commune_code, joueur_id, acquired_at, bouclier_jusqua, ' + champsCible)
      .neq('joueur_id', uid).in('commune_code', horsListe.slice(0, 200));
    if(enPlus) combatCibles = combatCibles.concat(enPlus);
  }
  calculerDistancesCibles();
  loadMenaces();""", 'sieges')

# 3. affichage -------------------------------------------------------------------
js = rempl(js, u"""  let cibles = combatCibles;
  if(combatFilterTier !== 'tous'){""", u"""  if(combatBasChargement && combatBasVoulus().some(t => !combatBasCharges.has(t))){
    grid.innerHTML = '<p class="collection-empty">Chargement des communes et peu communes…</p>';
    return;
  }
  let cibles = combatCibles;
  if(combatFilterTier !== 'tous'){""", 'chargement')
js = rempl(js, u"""      msg = `Aucune commune rare ou légendaire à moins de ${combatRayonKm} km de ton territoire.`;""",
           u"""      msg = `Aucune cible à moins de ${combatRayonKm} km de ton territoire.`;""", 'msg prox')

# 4. declencheurs ----------------------------------------------------------------
js = rempl(js, u"""  document.getElementById('combatRayons').hidden = !combatProximite;
  renderCombatGrid();
});""", u"""  document.getElementById('combatRayons').hidden = !combatProximite;
  renderCombatGrid();
  assurerCiblesBas();
});""", 'prox')
js = rempl(js, u"""  combatFilterTier = pill.dataset.tier;
  renderCombatGrid();
});""", u"""  combatFilterTier = pill.dataset.tier;
  renderCombatGrid();
  assurerCiblesBas();
});""", 'filtre')
ecrire('app.js', js)

html = lire('index.html')
html = rempl(html, u"""        <button class="filter-pill" data-tier="rare"><span class="pill-point" style="background:#2F7CF6"></span>Rare</button>
      </div>
      <input type="text" id="combatSearch\"""", u"""        <button class="filter-pill" data-tier="rare"><span class="pill-point" style="background:#2F7CF6"></span>Rare</button>
        <button class="filter-pill" data-tier="peucommun"><span class="pill-point" style="background:#22A06B"></span>Peu commun</button>
        <button class="filter-pill" data-tier="commun"><span class="pill-point" style="background:#7E8BA0"></span>Commun</button>
      </div>
      <input type="text" id="combatSearch\"""", 'pilules')
html = rempl(html, u"""<div class="sub">3 victoires d'affilée pour conquérir une commune rare ou légendaire, une défaite remet ta série à zéro. Avant d'attaquer, choisis ton engagement : plus tu paies, plus tu as de chances. Un round toutes les 10 min sur une rare, toutes les 3 h sur une légendaire.</div>""",
           u"""<div class="sub">3 victoires d'affilée pour conquérir une commune, une défaite remet ta série à zéro. Avant d'attaquer, choisis ton engagement : plus tu paies, plus tu as de chances. Un round toutes les 2 min sur une commune, 5 min sur une peu commune, 10 min sur une rare, 3 h sur une légendaire. Les communes et peu communes s'affichent avec leur filtre ou « Près de mon territoire ».</div>""",
           'texte')
ecrire('index.html', html)

css = lire('style.css')
css = rempl(css, u"""  .cible.legendaire .cible-rarete{ background: var(--c-legendaire); color: var(--encre); }
""", u"""  .cible.legendaire .cible-rarete{ background: var(--c-legendaire); color: var(--encre); }
  /* patch95 : communs et peu communs dans Combat */
  .cible.peucommun{ background: linear-gradient(160deg, #7FE0B4, var(--c-peucommun) 45%, #16734C); }
  .cible.commun{ background: linear-gradient(160deg, #C3CBD8, var(--c-commun) 45%, #4E5A6E); }
  .cible.peucommun .cible-rarete{ background: var(--c-peucommun); }
  .cible.commun .cible-rarete{ background: var(--c-commun); }
""", 'css')
ecrire('style.css', css)
print(u'patch95 applique')
