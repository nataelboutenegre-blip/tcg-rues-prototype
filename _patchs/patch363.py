# patch363 (6/11/2026) : règles du jeu à jour avec s2-108 et s2-109
# (quête Plus ou moins : partie du jour ou duel classé ; 80 énergie de quêtes par jour).
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('index.html'); s = F.read_text(encoding='utf-8')
assert 'patch363' not in s, 'patch363 déjà appliqué'
s = rep(s, "7 sur 10 au Plus ou moins du jour. Au plus <b>50 énergie de quêtes par jour</b> ; elle peut faire dépasser le maximum, jusqu'à 100.</p><!-- lot 8/11 -->",
           "7 sur 10 au Plus ou moins (partie du jour ou duel classé). Au plus <b>80 énergie de quêtes par jour</b> ; elle peut faire dépasser le maximum, jusqu'à 100.</p><!-- lot 8/11, patch363 -->")
F.write_text(s, encoding='utf-8')
print('patch363 appliqué')
