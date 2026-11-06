# patch358 (6/11/2026) : trois retouches.
#
# 1. « Depuis ta dernière visite » (Défendre) : le numéro du département à
#    côté de chaque commune nommée (« À une victoire d'être prise » et
#    « Perdue »). Idée d'Arkhannou.
# 2. Tirage : le bandeau « Commune du jour » ne prend plus toute la largeur
#    sur ordinateur ; il s'aligne sur les autres bandeaux (620 px au plus).
# 3. Tirage, pot vide : un ancien voyait « Réserve d'accueil active · Les 0
#    dernières communes libres… ». Quand il n'y a plus aucune commune libre,
#    tout le monde voit maintenant « Plus aucune commune libre ».
# Rien d'autre ne change, aucun SQL.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch358' not in s, 'patch358 déjà appliqué'

# 1. le département dans le réveil
s = rep(s, "  const noms = (liste, f) => liste.slice(0, 3).map(f).join(', ') + (liste.length > 3 ? ` et ${liste.length - 3} autre${liste.length > 4 ? 's' : ''}` : '');\n\n  if(pertes.length === 0 && repoussees.length === 0 && enCours.length === 0){",
           "  const noms = (liste, f) => liste.slice(0, 3).map(f).join(', ') + (liste.length > 3 ? ` et ${liste.length - 3} autre${liste.length > 4 ? 's' : ''}` : '');\n"
           "  // patch358 : le numéro du département à côté du nom (idée d'Arkhannou)\n"
           "  const dep = (code) => {\n"
           "    const c = code && (collectionMap.get(code) || othersMap.get(code));\n"
           "    const d = (c && c.dept) || (code ? (String(code).startsWith('97') ? String(code).slice(0, 3) : String(code).slice(0, 2)) : '');\n"
           "    return d ? ` <span class=\"reveil-dep\">(${echapperTexte(d)})</span>` : '';\n"
           "  };\n\n"
           "  if(pertes.length === 0 && repoussees.length === 0 && enCours.length === 0){")
s = rep(s, "${noms(urgentes, m => '<b>' + echapperTexte(m.nom) + '</b>')}",
           "${noms(urgentes, m => '<b>' + echapperTexte(m.nom) + '</b>' + dep(m.commune_code))}")
s = rep(s, "${noms(pertes, e => '<b>' + echapperTexte(e.commune_nom || 'une commune') + '</b> (prise par ' + echapperTexte(e.acteur_pseudo || 'un joueur') + ')')}",
           "${noms(pertes, e => '<b>' + echapperTexte(e.commune_nom || 'une commune') + '</b>' + dep(e.commune_code) + ' (prise par ' + echapperTexte(e.acteur_pseudo || 'un joueur') + ')')}")

# 3. pot vide : le message « plus aucune commune libre » passe avant celui de la réserve
s = rep(s, "    if(bloque){\n      cas = 'bloque';\n      html = `<span class=\"ra-ic\">🛡️</span><span class=\"ra-t\">Réserve d'accueil active</span>",
           "    if(libres === 0 && roueActive()){   // patch358 : pot vide, avant la réserve (plus de « Les 0 dernières communes »)\n"
           "      cas = 'bloque';\n"
           "      html = `<span class=\"ra-ic\">🛡️</span><span class=\"ra-t\">Plus aucune commune libre</span>\n"
           "        <p class=\"ra-x\">Le pot du Front est vide. En attendant, <b>la roue du Front remplace tes paquets</b>. Pour gagner du terrain, attaque !</p>`;\n"
           "    } else if(bloque){\n      cas = 'bloque';\n      html = `<span class=\"ra-ic\">🛡️</span><span class=\"ra-t\">Réserve d'accueil active</span>")
F.write_text(s, encoding='utf-8')

# 2. le bandeau de la Commune du jour
C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch358' not in c
c += "\n/* patch358 : le bandeau de la Commune du jour s'aligne sur les autres bandeaux du Tirage ; le département dans le réveil */\n" \
     "#panel-tirage .cdj-carte{ max-width:620px; }\n" \
     ".reveil-dep{ color: var(--brume); font-weight:500; }\n"
C.write_text(c, encoding='utf-8')
print('patch358 appliqué')
