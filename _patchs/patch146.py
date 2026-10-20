# -*- coding: utf-8 -*-
u"""
patch146 — les paquets et tout le jeu ralentissaient le soir (20 octobre).

Mesuré dans Supabase (Query Performance) : 80 % du temps de la base passait
dans UNE requête, le chargement du territoire des autres joueurs
(possessions, ~29 000 lignes, par pages de 1 000). Chaque page était
demandée avec un décalage (.range) : pour servir la 28e page, la base
relisait et jetait les 27 000 lignes précédentes, avec leurs jointures. Le
coût d'un chargement complet grandissait donc comme le carré du nombre de
communes possédées. Moyenne 1,9 s par page, jusqu'à 7 s aux heures de
pointe : le processeur de la base saturait, et tout le reste attendait
(tirer_carte : ouverture des paquets lente).

Les pages s'enchaînent maintenant par la clé (« les 1 000 codes après
celui-ci ») : chaque page coûte la même chose, où qu'elle soit. Pour garder
le parallélisme, la liste est coupée en 5 tranches de codes chargées en
même temps. Mesuré sur la vraie base : la page à 27 000 passe de 501 ms à
153 ms, le chargement complet (28 044 lignes) prend 1,15 s, lignes
identiques.

Même fonction pour toutes les listes paginées : territoire des autres, ma
collection, cibles du Combat.
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
assert 'patch146' not in js, u'patch146 deja applique'

js = rempl(js, u"""// Supabase plafonne chaque requete a 1000 lignes : on demande par tranches
async function toutesLesLignes(construireRequete, cle = 'commune_code'){
  // patch122 : 6 paquets de 1 000 a la fois au lieu d'un seul. Tries sur une
  // cle unique, pour qu'une ligne ne puisse pas sauter d'un paquet a l'autre.
  const TAILLE = 1000, EN_PARALLELE = 6;
  let tout = [], page = 0;
  for(;;){
    const lot = [];
    for(let k = 0; k < EN_PARALLELE; k++){
      const debut = (page + k) * TAILLE;
      lot.push(construireRequete().order(cle, { ascending: true }).range(debut, debut + TAILLE - 1));
    }
    const reponses = await Promise.all(lot);
    for(const { data, error } of reponses){
      if(error) return { data: null, error };
      tout = tout.concat(data || []);
      if(!data || data.length < TAILLE) return { data: tout, error: null };
    }
    page += EN_PARALLELE;
  }
}""", u"""// Supabase plafonne chaque requete a 1000 lignes : on demande par tranches
// patch146 : chaque page commence APRES le dernier code de la precedente.
// Avec un decalage (.range), la base relisait toutes les lignes deja
// envoyees pour servir la page suivante (27 000 pour la 28e) : 80 % du temps
// de la base le 20 octobre, et les paquets qui s'ouvraient lentement.
// Cinq tranches de codes chargees en meme temps gardent le parallelisme.
const TRANCHES_DE_CODES = [null, '2', '4', '6', '8', null];
async function toutesLesLignes(construireRequete, cle = 'commune_code'){
  const TAILLE = 1000;
  const tranche = async (de, a) => {
    const lignes = [];
    let apres = null;
    for(;;){
      let q = construireRequete();
      if(de !== null) q = q.gte(cle, de);
      if(a !== null) q = q.lt(cle, a);
      if(apres !== null) q = q.gt(cle, apres);
      const { data, error } = await q.order(cle, { ascending: true }).limit(TAILLE);
      if(error) return { data: null, error };
      const page = data || [];
      for(const ligne of page) lignes.push(ligne);
      if(page.length < TAILLE) return { data: lignes, error: null };
      apres = page[page.length - 1][cle];
    }
  };
  const reponses = await Promise.all(TRANCHES_DE_CODES.slice(0, -1)
    .map((de, i) => tranche(de, TRANCHES_DE_CODES[i + 1])));
  const tout = [];
  for(const { data, error } of reponses){
    if(error) return { data: null, error };
    for(const ligne of data) tout.push(ligne);
  }
  return { data: tout, error: null };
}""", 'toutesLesLignes')

ecrire('app.js', js)
print(u'patch146 applique')
