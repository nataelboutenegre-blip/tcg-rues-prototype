# -*- coding: utf-8 -*-
u"""
patch61 — « haute savoie » doit marcher comme « haute-savoie ».

CE QUE J'AI MESURE EN VERIFIANT LE CHAMP DES EXCLUSIONS
  Il accepte le numero (16), le nom exact (Charente), un debut sans
  ambiguite (corse) et les accents (rhone comme rhône). Il refuse en
  revanche les noms composes ecrits AVEC DES ESPACES :

      charente maritime · haute savoie · corse du sud · val d oise

  et « 2a » en minuscules, alors que « 2A » passe.

  Personne ne tape forcement les traits d'union, et personne ne tape
  l'apostrophe de Val-d'Oise.

OU EST LA CORRECTION
  Dans codeDepartement, pas dans le champ des exclusions. Cette fonction
  sert aussi aux recherches du Combat, de l'Echange, de la Bourse et de la
  Collection : le defaut y etait identique et depuis plus longtemps. Le
  corriger a sa source le corrige partout.

  Les separateurs cessent de decider : espaces, traits d'union et
  apostrophes sont retires des deux cotes avant comparaison. « hautesavoie »
  trouve aussi la Haute-Savoie, ce qui ne gene personne.

  Et dans le champ des exclusions, « 2a » est mis en majuscules avant d'etre
  compare aux numeros — la Corse est le seul departement dont le numero
  contient une lettre.
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

js = rempl(js,
u"""function codeDepartement(texte){
  const t = sansAccents(texte || '');
  if(t.length < 3) return null;
  const codes = Object.keys(DEPT_NAMES);
  const exact = codes.find(c => sansAccents(DEPT_NAMES[c]) === t);
  if(exact) return exact;
  const debuts = codes.filter(c => sansAccents(DEPT_NAMES[c]).startsWith(t));
  return debuts.length === 1 ? debuts[0] : null;
}""",
u"""function codeDepartement(texte){
  // Les separateurs ne doivent pas decider du resultat : « haute savoie »,
  // « haute-savoie » et « hautesavoie » visent la meme chose, et personne ne
  // tape l'apostrophe de Val-d'Oise. On les retire des deux cotes.
  const nu = (s) => sansAccents(s).replace(/[\\s'\\u2019-]+/g, '');
  const t = nu(texte || '');
  if(t.length < 3) return null;
  const codes = Object.keys(DEPT_NAMES);
  const exact = codes.find(c => nu(DEPT_NAMES[c]) === t);
  if(exact) return exact;
  const debuts = codes.filter(c => nu(DEPT_NAMES[c]).startsWith(t));
  return debuts.length === 1 ? debuts[0] : null;
}""",
u'les separateurs ne decident plus')

js = rempl(js,
u"""  // « charente » devient « 16 » : le meme utilitaire que les recherches
  const code = codeDepartement(saisi) || saisi;""",
u"""  // « charente » devient « 16 » : le meme utilitaire que les recherches.
  // A defaut, la saisie est prise pour un numero — en majuscules, la Corse
  // etant le seul departement dont le numero contient une lettre.
  const code = codeDepartement(saisi) || saisi.toUpperCase();""",
u'2a accepte comme 2A')

ecrire('app.js', js)
print(u'patch61 applique.')
