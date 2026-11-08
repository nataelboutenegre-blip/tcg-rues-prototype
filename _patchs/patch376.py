# patch376 (8/11/2026) : la mallette de la bombe et les communes à tiret (signalé
# par Oshannir) : pas de touche « - », et « SAINTJEAN » ne trouvait pas Saint-Jean.
#   - une touche « - » sur la 3e rangée (⌫ et VALIDER un peu plus étroits) ;
#   - au clavier de l'ordinateur, « - », l'espace et l'apostrophe tapent un tiret ;
#   - côté serveur (s2-118), tirets et espaces ne comptent plus dans la recherche,
#     et les communes à portée passent devant.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:80]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch376' not in s, 'patch376 déjà appliqué'
s = rep(s, "  const R = ['AZERTYUIOP', 'QSDFGHJKLM', 'WXCVBN'];",
           "  const R = ['AZERTYUIOP', 'QSDFGHJKLM', 'WXCVBN-'];   // patch376 : le tiret")
s = rep(s, "  else if(/^[a-zà-ÿ]$/i.test(e.key)){ const l = mlNorm(e.key).toUpperCase(); if(l){ e.preventDefault(); mlAppuyer(l); } }",
           """  else if(/^[a-zà-ÿ]$/i.test(e.key)){ const l = mlNorm(e.key).toUpperCase(); if(l){ e.preventDefault(); mlAppuyer(l); } }
  else if(e.key === '-' || e.key === ' ' || e.key === "'" || e.key === '’'){ e.preventDefault(); mlAppuyer('-'); }   // patch376""")
s = rep(s, "  else if(ML.requete.length < 24) ML.requete += k;",
           "  else if(k === '-' && (!ML.requete || ML.requete.endsWith('-'))) return;   // patch376 : pas de tiret en tête ni doublé\n  else if(ML.requete.length < 28) ML.requete += k;")
F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch376' not in c
c = rep(c, ".ml-k.ml-eff{ grid-column:span 3; font-size:15px; }",
           ".ml-k.ml-eff{ grid-column:span 2; font-size:15px; }   /* patch376 : 3 avant, place pour le tiret */")
c = rep(c, ".ml-k.ml-ok{ grid-column:span 5; color:#2A1A06; font-size:11px; letter-spacing:.12em; font-weight:600;",
           ".ml-k.ml-ok{ grid-column:span 4; color:#2A1A06; font-size:10.5px; letter-spacing:.04em; font-weight:600;   /* patch376 : 5 avant */")
C.write_text(c, encoding='utf-8')
print('patch376 ok')
