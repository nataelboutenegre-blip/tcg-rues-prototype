# patch332 (3/11/2026) : saison 3, la Suisse — la recherche et la saisie des cantons,
# éteintes comme patch330 (rien ne change tant que SUISSE vaut false).
# - un nom de canton se tape comme un nom de département (« Vaud », « Valais ») ;
#   « Jura » reste le département 39, le canton se tape « canton du Jura » ou « JU » ;
#   « canton de … » ne cherche que parmi les cantons ;
# - Combat : « VD », « vaud » filtrent le canton comme « 74 » filtre la Haute-Savoie ;
# - une recherche « ge » ne ramène plus toutes les communes d'un canton dont le
#   code contient la lettre (un code de canton se tape en entier) ;
# - boutique : le paquet département propose les cantons à part, sous « Suisse ».
import pathlib

F = pathlib.Path('app.js')
s = F.read_text(encoding='utf-8')

def rep(avant, apres, n=1):
    global s
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    s = s.replace(avant, apres)

# 1. codeDepartement : les cantons, « canton de … », et « Jura » sans surprise
rep("""  const t = nu(texte || '');
  if(t.length < 3) return null;
  const codes = Object.keys(DEPT_NAMES);""", """  let t = nu(texte || '');
  // patch330 (saison 3) : « canton de Vaud », « canton du Jura » -> seulement les cantons
  let cantonsSeuls = false;
  if(SUISSE){ const m = t.match(/^canton(?:des|du|de|d)?(.{3,})$/); if(m){ t = m[1]; cantonsSeuls = true; } }
  if(t.length < 3) return null;
  const codes = Object.keys(DEPT_NAMES).filter(c => !cantonsSeuls || estCanton(c));""")
rep("""  const exact = codes.find(c => noms(c).includes(t));
  if(exact) return exact;""", """  // « Jura » : le département 39 passe avant le canton (les clés numériques viennent d'abord)
  const exact = codes.find(c => noms(c).includes(t));
  if(exact) return exact;""")

# 2. une recherche courte ne ramène plus tout un canton par son code
rep("""      || (String(dept).length > 2 ? String(dept).toLowerCase().startsWith(recherche) : String(dept).toLowerCase().includes(recherche))""",
    """      || (String(dept).length > 2 ? String(dept).toLowerCase().startsWith(recherche)
          : estCanton(dept) ? String(dept).toLowerCase() === recherche   // patch332 : un code de canton se tape en entier
          : String(dept).toLowerCase().includes(recherche))""")

# 3. Combat : le canton filtre comme un département
rep("""      if(/^(\\d{2,3}|2a|2b)$/i.test(d)){ deps.push(d.toUpperCase()); continue; }""",
    """      if(/^(\\d{2,3}|2a|2b)$/i.test(d) || (SUISSE && estCanton(d.toUpperCase()))){ deps.push(d.toUpperCase()); continue; }   // patch332""")

# 4. Boutique : les cantons à part dans le paquet département
rep("""      ? `<select class="bq-dep" id="bqDep" aria-label="Département"><option value="">Choisis un département</option>${
          deps.map(d => `<option value="${d}">${d} · ${echapperTexte(DEPT_NAMES[d])}</option>`).join('')}</select>` : '';""",
    """      ? `<select class="bq-dep" id="bqDep" aria-label="Département"><option value="">Choisis un département${SUISSE ? ' ou un canton' : ''}</option>${
          (SUISSE   // patch332 : les cantons à part, sous « Suisse »
            ? '<optgroup label="France">' + deps.filter(d => !estCanton(d)).map(d => `<option value="${d}">${d} · ${echapperTexte(DEPT_NAMES[d])}</option>`).join('')
              + '</optgroup><optgroup label="Suisse">' + deps.filter(estCanton).map(d => `<option value="${d}">${d} · ${echapperTexte(DEPT_NAMES[d])}</option>`).join('') + '</optgroup>'
            : deps.map(d => `<option value="${d}">${d} · ${echapperTexte(DEPT_NAMES[d])}</option>`).join(''))}</select>` : '';""")

# 5. la cloche : le champ dit qu'on peut chercher un canton
rep("""placeholder="Nom ou numéro du département" autocomplete="off" value="${echapperTexte(NC.depQ || '')}" aria-label="Chercher un département">""",
    """placeholder="${SUISSE ? 'Département ou canton' : 'Nom ou numéro du département'}" autocomplete="off" value="${echapperTexte(NC.depQ || '')}" aria-label="Chercher un département">""")

F.write_text(s, encoding='utf-8')
print('patch332 appliqué')
