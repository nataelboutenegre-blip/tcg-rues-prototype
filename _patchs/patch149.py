# -*- coding: utf-8 -*-
u"""
patch149 — exclure un joueur (ou un département) dans les recherches du
Combat et de l'Échange (idée d'Arkhannou, 22 octobre).

Tout ce qui suit un « / » est exclu :
  25 /Maroli            le Doubs, sauf les communes de Maroli
  25 /Maroli /Oshannir  plusieurs exclusions
  Doubs, Jura /Maroli   les virgules combinent toujours plusieurs termes
  /Maroli               tout, sauf Maroli
Une exclusion qui est un numéro ou un nom de département retire ce
département ; sinon elle retire les joueurs dont le pseudo la contient et
les communes dont le nom la contient.

Combat : les virgules marchent maintenant aussi (« Doubs, Jura »), comme
dans l'Échange. Une recherche faite seulement d'exclusions ne charge pas
les communes et peu communes (comme un champ vide).

Échange : le serveur renvoie 120 communes au plus ; les exclusions sont
appliquées ensuite, dans le navigateur (pas de SQL à passer). Si la liste
était coupée et que des exclusions ont retiré des communes, une ligne
conseille d'ajouter un département.
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
assert 'separerExclusions' not in js, u'patch149 deja applique'

# --- outils communs, juste apres correspondUnTerme (patch142)
js = rempl(js, u"""function correspondUnTerme(nom, dept, recherche){
  const termes = String(recherche || '').split(/[,;]/).map(t => t.trim()).filter(Boolean);
  if(!termes.length) return true;
  return termes.some(t => correspondRecherche(nom, dept, t));
}
""", u"""function correspondUnTerme(nom, dept, recherche){
  const termes = String(recherche || '').split(/[,;]/).map(t => t.trim()).filter(Boolean);
  if(!termes.length) return true;
  return termes.some(t => correspondRecherche(nom, dept, t));
}

// patch149 : « 25 /Maroli » -> le Doubs sauf Maroli. Tout ce qui suit un / est exclu.
function separerExclusions(texte){
  const morceaux = String(texte || '').split('/');
  const exclus = morceaux.slice(1).join(',').split(/[,;]/)
    .map(t => sansAccents(t.trim())).filter(Boolean);
  return { recherche: morceaux[0].trim(), exclus };
}
// un departement (numero ou nom) retire ce departement ; sinon le pseudo ou le nom qui le contient
function estExclu(nom, dept, pseudo, exclus){
  if(!exclus.length) return false;
  const p = sansAccents(pseudo || ''), n = sansAccents(nom || ''), d = String(dept || '').toUpperCase();
  return exclus.some(t => {
    const brut = /^\\d$/.test(t) ? '0' + t : t.toUpperCase();
    const code = DEPT_NAMES[brut] ? brut : codeDepartement(t);
    if(code) return d === code || p === t;
    return (p && p.includes(t)) || n.includes(t);
  });
}
""", 'outils')

# --- Combat : la liste chargee est complete, on filtre ici
js = rempl(js, u"""  // patch125 : une recherche reduit la liste, on peut tout charger
  const champ = document.getElementById('combatSearch');
  if(combatFilterTier === 'tous' && champ && champ.value.trim()) return COMBAT_TIERS_BAS.slice();""",
u"""  // patch125 : une recherche reduit la liste, on peut tout charger
  // (patch149 : des exclusions seules ne reduisent rien, comme un champ vide)
  const champ = document.getElementById('combatSearch');
  if(combatFilterTier === 'tous' && champ && separerExclusions(champ.value).recherche) return COMBAT_TIERS_BAS.slice();""", 'combatBasVoulus')

js = rempl(js, u"""  const searchEl = document.getElementById('combatSearch');
  const searchText = sansAccents(searchEl ? searchEl.value.trim() : '');
  majAideCombat(searchText);""", u"""  const searchEl = document.getElementById('combatSearch');
  const { recherche: rechercheCombat, exclus: exclusCombat } = separerExclusions(searchEl ? searchEl.value : '');
  const searchText = sansAccents(rechercheCombat);
  majAideCombat(searchText);""", 'combat lecture')

js = rempl(js, u"""  if(searchText){
    // patch126 : le pseudo du proprietaire compte aussi
    cibles = cibles.filter(c => correspondRecherche(c.communes.nom, c.communes.departement, searchText)
      || (c.joueurs && c.joueurs.pseudo && sansAccents(c.joueurs.pseudo).includes(searchText)));
  }""", u"""  if(searchText){
    // patch126 : le pseudo du proprietaire compte aussi ; patch149 : plusieurs termes, separes par des virgules
    const termes = searchText.split(/[,;]/).map(t => t.trim()).filter(Boolean);
    cibles = cibles.filter(c => termes.some(t => correspondRecherche(c.communes.nom, c.communes.departement, t)
      || (c.joueurs && c.joueurs.pseudo && sansAccents(c.joueurs.pseudo).includes(t))));
  }
  if(exclusCombat.length){
    cibles = cibles.filter(c => !estExclu(c.communes.nom, c.communes.departement, c.joueurs && c.joueurs.pseudo, exclusCombat));
  }""", 'combat filtre')

# --- Echange : le serveur ne recoit que la partie avant le /, on retire les exclus ensuite
js = rempl(js, u"""let echangeRecherche = '';""", u"""let echangeRecherche = '';
let echangeCoupee = false;   // patch149 : le serveur a renvoye son maximum et des exclusions ont retire des communes""", 'echange variable')

js = rempl(js, u"""  const { data, error } = await sb.rpc(marcheTerra() ? 'terra_cibles_echange' : 'cibles_echange', {
    p_tier: echangeTier, p_recherche: criteresEchange(echangeRecherche)
  });""", u"""  const { recherche: rechercheEch, exclus: exclusEch } = separerExclusions(echangeRecherche);
  const { data, error } = await sb.rpc(marcheTerra() ? 'terra_cibles_echange' : 'cibles_echange', {
    p_tier: echangeTier, p_recherche: criteresEchange(rechercheEch)
  });""", 'echange appel')

js = rempl(js, u"""  echangeCibles = data || [];
  await chargerSieges(echangeCibles.map(c => c.commune_code));
  renderEchangeCibles();""", u"""  const recues = data || [];
  echangeCibles = exclusEch.length ? recues.filter(c => !estExclu(c.nom, c.departement, c.pseudo, exclusEch)) : recues;
  // le serveur s'arrete a 120 : apres des exclusions, d'autres communes peuvent exister plus loin
  echangeCoupee = recues.length >= 120 && echangeCibles.length < recues.length;
  await chargerSieges(echangeCibles.map(c => c.commune_code));
  renderEchangeCibles();""", 'echange filtre')

js = rempl(js, u"""  if(echangeCibles.length === 0){
    zone.innerHTML = '<p class="collection-empty">Aucune commune disponible de cette rareté.</p>';""",
u"""  if(echangeCibles.length === 0){
    zone.innerHTML = echangeCoupee
      ? '<p class="collection-empty">Rien dans les 120 premières communes une fois les exclusions retirées : ajoute un département pour chercher plus loin.</p>'
      : '<p class="collection-empty">Aucune commune disponible de cette rareté.</p>';""", 'echange vide')

js = rempl(js, u"""      <small>${echapperTexte(c.departement)} · ${echapperTexte(c.pseudo || 'un joueur')}</small>${tagSiege(siegesConnus.get(c.commune_code))}
    </button>`).join('');
  majResumeEchange();""", u"""      <small>${echapperTexte(c.departement)} · ${echapperTexte(c.pseudo || 'un joueur')}</small>${tagSiege(siegesConnus.get(c.commune_code))}
    </button>`).join('')
    + (echangeCoupee ? '<p class="ech-astuce">Liste limitée aux 120 premières communes : ajoute un département pour voir les autres.</p>' : '');
  majResumeEchange();""", 'echange coupee')

ecrire('app.js', js)

h = lire('index.html')
h = rempl(h, u"""<input type="text" id="combatSearch" class="bourse-search" placeholder="Rechercher une commune ou un département…">""",
             u"""<input type="text" id="combatSearch" class="bourse-search" placeholder="Commune, département ou joueur · /pseudo pour exclure">""", 'placeholder combat')
h = rempl(h, u"""<p class="ech-astuce">Combine avec des virgules : <b>16, 17, Maroli</b></p>""",
             u"""<p class="ech-astuce">Combine avec des virgules : <b>16, 17, Maroli</b> · exclus avec / : <b>25 /Maroli</b></p>""", 'astuce echange')
ecrire('index.html', h)
print(u'patch149 applique. Lancer : python3 maj-version.py')
