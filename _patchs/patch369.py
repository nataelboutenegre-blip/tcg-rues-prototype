# patch369 (7/11/2026) : chercher par région (idée validée par Nataël).
#
# « bretagne » -> 22, 29, 35, 56 ; « grand est », « occitanie », « idf »,
# « paca », « nouvelle-aquitaine »… Partout où l'on cherche une commune ou un
# département :
#   - correspondRecherche() (Collection, Vitrine, decks, skins, Combat par nom…)
#     accepte aussi une région ;
#   - codesDepartements() rend les départements de la région quand le mot ne
#     vise aucun département : Combat, Échange (le serveur ne connaît que les
#     numéros), exclusions « /bretagne » et exclusions du contrat.
# Un département passe toujours avant une région : « loire » reste le 42,
# « corse » le 2A et le 2B. Une région se tape en entier, avec un alias
# (idf, paca) ou par un début d'au moins 5 lettres sans ambiguïté
# (« bourgogne », « auvergne », « provence »).
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch369' not in s, 'patch369 déjà appliqué'
assert 'function codesDepartements' in s, 'patch368 manquant'

s = rep(s, """// patch368 : tous les départements visés par un mot (« corse » -> 2A et 2B), [] si aucun
function codesDepartements(texte){
  codeDepartement.plusieurs = null;
  const un = codeDepartement(texte);
  const plusieurs = codeDepartement.plusieurs || [];
  codeDepartement.plusieurs = null;
  return un ? [un] : plusieurs;
}""",
"""// patch368 : tous les départements visés par un mot (« corse » -> 2A et 2B), [] si aucun
// patch369 : à défaut d'un département, ceux d'une région (« bretagne » -> 22, 29, 35, 56)
function codesDepartements(texte){
  codeDepartement.plusieurs = null;
  const un = codeDepartement(texte);
  const plusieurs = codeDepartement.plusieurs || [];
  codeDepartement.plusieurs = null;
  return un ? [un] : plusieurs.length ? plusieurs : departementsRegion(texte);
}
// patch369 : les départements d'une région tapée en entier, par un alias ou par
// un début d'au moins 5 lettres sans ambiguïté ; [] sinon
const REGIONS_ALIAS = { paca: "Provence-Alpes-Côte d'Azur", idf: 'Île-de-France' };
const REGIONS_CACHE = new Map();
function departementsRegion(texte){
  const nu = (x) => sansAccents(x).replace(/[\\s'\\u2019-]+/g, '');
  const t = nu(texte || '');
  if(REGIONS_CACHE.has(t)) return REGIONS_CACHE.get(t);
  let r = [];
  if(t.length >= 3){
    const noms = [...new Set(Object.values(DEP_REGION))];
    let nom = REGIONS_ALIAS[t] || noms.find(n => nu(n) === t);
    if(!nom && t.length >= 5){ const d = noms.filter(n => nu(n).startsWith(t)); if(d.length === 1) nom = d[0]; }
    if(nom) r = Object.keys(DEP_REGION).filter(c => DEP_REGION[c] === nom);
  }
  REGIONS_CACHE.set(t, r);
  return r;
}""")

s = rep(s, """      || sansAccents(DEPT_NAMES[dept] || '').includes(recherche);
}""",
"""      || sansAccents(DEPT_NAMES[dept] || '').includes(recherche)
      || departementsRegion(recherche).includes(String(dept).toUpperCase());   // patch369 : une région
}""")

# contrat : plusieurs départements d'un coup, une seule relecture à la fin
s = rep(s, """  { const ks = codesDepartements(saisi);   // patch368 : « corse » = 2A et 2B
    if(ks.length > 1){ champ.value = ''; for(const k of ks) await exclureDuContrat({ p_departement: k }); return; } }""",
"""  { const ks = codesDepartements(saisi);   // patch368 : « corse » = 2A et 2B ; patch369 : une région
    if(ks.length > 1){
      champ.value = ''; direErreurExclusion('');
      for(const k of ks){
        const { error } = await sb.rpc('exclure_du_contrat', { p_departement: k });
        if(error){ direErreurExclusion(messageLisible(error.message)); break; }
      }
      await chargerExclusions(); renderExclusions(); await loadContrat();
      return;
    } }""")

s = rep(s, """      const ds = codesDepartements(t);   // patch368 : « corse » = 2A et 2B""",
"""      const ds = codesDepartements(t);   // patch368 : « corse » = 2A et 2B ; patch369 : une région""")

F.write_text(s, encoding='utf-8')

H = pathlib.Path('index.html'); h = H.read_text(encoding='utf-8')
assert 'patch369' not in h
h = rep(h, """<li><b>Combats en cours</b> affiche les cibles où tu as déjà 1 ou 2 victoires.""",
"""<li>La recherche accepte une commune, un département, un pseudo ou une région (« bretagne », « grand est », « idf », « paca »), séparés par des virgules.</li><!-- patch369 -->
              <li><b>Combats en cours</b> affiche les cibles où tu as déjà 1 ou 2 victoires.""")
H.write_text(h, encoding='utf-8')
print('patch369 appliqué')
