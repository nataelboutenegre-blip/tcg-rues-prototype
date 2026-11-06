# patch362 (6/11/2026) : l'énergie des quêtes du Front passe de 50 à 80 par jour
# (s2-109, décision de Nataël). Les trois endroits du jeu qui affichaient 50.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch362' not in s, 'patch362 déjà appliqué'
s = rep(s, "<span class=\"obj-plafond\">⚡ ${ej} / 50 d'énergie de quêtes</span>", "<span class=\"obj-plafond\">⚡ ${ej} / 80 d'énergie de quêtes</span>")   # patch362
s = rep(s, "  const sous = (front ? `${ej} / 50 d’énergie gagnée`", "  const sous = (front ? `${ej} / 80 d’énergie gagnée`")   # patch362
s = rep(s, "<li>Les quêtes du jour : +5 chacune, jusqu'à 50 par jour.</li>", "<li>Les quêtes du jour : +5 chacune (+10 pour les plus dures), jusqu'à 80 par jour.</li>")   # patch362
F.write_text(s, encoding='utf-8')
print('patch362 appliqué')
