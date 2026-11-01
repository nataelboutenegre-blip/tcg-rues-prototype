# patch301 : défense réussie avec la réserve pleine (1/11) — demande de Nataël (« oui au pire »)
# Après une défense, la notification dit « Réserve pleine : pas de lingot. » quand la réserve
# est au plafond, comme la fin d'un assaut gagné (patch300). Avant, elle ne disait rien.
import json, pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch301' not in s
s = rep(s, """        lgTexte = g > 0 ? ` +${g} lingot${g > 1 ? 's' : ''} (${n} / ${p} aujourd’hui).` : n >= p ? ` Plafond du jour atteint (${p} / ${p} lingots).` : '';""",
           """        lgTexte = g > 0 ? ` +${g} lingot${g > 1 ? 's' : ''} (${n} / ${p} aujourd’hui).` : n >= p ? ` Plafond du jour atteint (${p} / ${p} lingots).`
          : BATIMENTS && lingotsActuels() >= (Number(BATIMENTS.max) || 30) ? ' Réserve pleine : pas de lingot.' : '';   // patch301""")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('data/nouveautes.json'); d = json.loads(f.read_text(encoding='utf-8'))
e = next(x for x in d if x['date'] == '2026-11-01')
e['correctifs'].insert(0, 'Après une défense réussie avec la réserve de lingots pleine, la notification le dit')
f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch301 appliqué')
