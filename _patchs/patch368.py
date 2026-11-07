# patch368 (7/11/2026) : « corse » vise la Corse-du-Sud ET la Haute-Corse.
#
# Signalé par Nataël : dans Combat, la recherche « corse » ne montrait que les
# 6 cibles du 2A, alors que la carte en montre plus de 200 en Haute-Corse.
# Cause : codeDepartement() prenait un début de nom unique (« corse » ->
# Corse-du-Sud) sans voir que le mot se lit aussi dans Haute-Corse.
# Correctif :
#   - codeDepartement() ne choisit plus un département quand le mot se lit
#     dans plusieurs noms (il rend null, comme pour « seine » ou « alpes ») ;
#   - codesDepartements() rend alors tous ces départements (« corse » -> 2A, 2B) ;
#   - Combat, Échange (le serveur ne connaît que les numéros), exclusions
#     « /corse » et exclusions du contrat s'en servent.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch368' not in s, 'patch368 déjà appliqué'

s = rep(s, """  const exact = codes.find(c => noms(c).includes(t));
  if(exact) return exact;
  const debuts = codes.filter(c => noms(c).some(x => x.startsWith(t)));
  return debuts.length === 1 ? debuts[0] : null;
}""",
"""  const exact = codes.find(c => noms(c).includes(t));
  if(exact) return exact;
  const debuts = codes.filter(c => noms(c).some(x => x.startsWith(t)));
  // patch368 : « corse » commence Corse-du-Sud mais se lit aussi dans Haute-Corse : pas un seul département
  const dedans = codes.filter(c => noms(c).some(x => x.includes(t)));
  if(debuts.length === 1 && dedans.length > 1){ codeDepartement.plusieurs = dedans; return null; }
  return debuts.length === 1 ? debuts[0] : null;
}
// patch368 : tous les départements visés par un mot (« corse » -> 2A et 2B), [] si aucun
function codesDepartements(texte){
  codeDepartement.plusieurs = null;
  const un = codeDepartement(texte);
  const plusieurs = codeDepartement.plusieurs || [];
  codeDepartement.plusieurs = null;
  return un ? [un] : plusieurs;
}""")

# estExclu : « /corse » retire les deux
s = rep(s, """    const code = DEPT_NAMES[brut] ? brut : codeDepartement(t);
    if(code) return d === code || p === t;""",
"""    const codes = DEPT_NAMES[brut] ? [brut] : codesDepartements(t);   // patch368
    if(codes.length) return codes.includes(d) || p === t;""")

# contrat : « corse » exclut les deux départements
s = rep(s, """document.getElementById('ctExclAjouter').addEventListener('click', () => {
  const champ = document.getElementById('ctExclDept');
  const saisi = (champ.value || '').trim();
  if(!saisi) return;""",
"""document.getElementById('ctExclAjouter').addEventListener('click', async () => {
  const champ = document.getElementById('ctExclDept');
  const saisi = (champ.value || '').trim();
  if(!saisi) return;
  { const ks = codesDepartements(saisi);   // patch368 : « corse » = 2A et 2B
    if(ks.length > 1){ champ.value = ''; for(const k of ks) await exclureDuContrat({ p_departement: k }); return; } }""")

# Combat
s = rep(s, """      const d = codeDepartement(t) || t;
      if(/^(\\d{2,3}|2a|2b)$/i.test(d)""",
"""      const ds = codesDepartements(t);   // patch368 : « corse » = 2A et 2B
      if(ds.length > 1){ deps.push(...ds); continue; }
      const d = ds[0] || t;
      if(/^(\\d{2,3}|2a|2b)$/i.test(d)""")

# Échange : le serveur ne connaît que les numéros
s = rep(s, """    .map(t => codeDepartement(t) || t).join(', ');""",
"""    .flatMap(t => { const ds = codesDepartements(t); return ds.length ? ds : [t]; }).join(', ');   // patch368""")

F.write_text(s, encoding='utf-8')
print('patch368 appliqué')
