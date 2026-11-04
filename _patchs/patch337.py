# patch337 (4/11/2026) : les défenses ne reviennent plus quand la série de
# l'attaquant retombe à zéro (s2-94, signalé par H34VEN). Les règles le disent ;
# une ligne dans la cloche.
import pathlib, json

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('index.html'); s = F.read_text(encoding='utf-8')
s = rep(s, """Une défense utilisée revient <b>24 h</b> après ta dernière défense, jusqu'à deux : une attaque laissée en plan peut toujours être repoussée. Si la série de l'attaquant retombe à zéro, tu les récupères toutes pour sa prochaine attaque.</li><!-- patch334 -->""",
"""Une défense utilisée revient <b>24 h</b> après ta dernière défense, jusqu'à deux : une attaque laissée en plan peut toujours être repoussée. Faire retomber la série de l'attaquant à zéro ne rend pas tes défenses.</li><!-- patch334, patch337 -->""")
F.write_text(s, encoding='utf-8')

F = pathlib.Path('data/nouveautes.json'); d = json.loads(F.read_text(encoding='utf-8'))
assert d[0]['date'] == '2026-11-04'
d[0]['nouveautes'].insert(0, "🛡 Défense : faire retomber la série d’un attaquant à zéro ne rend plus tes deux défenses ; elles reviennent seulement 24 h après ta dernière défense (défaut signalé par H34VEN)")
F.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch337 appliqué')
