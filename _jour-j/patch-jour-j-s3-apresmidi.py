# Saison 3, jour J, l'après-midi : la cloche des trois nouveautés de clan (à lancer après s3-jj-7-clans-artillerie.sql).
# Ensuite : python3 maj-version.py, commit de app.js + index.html + version.json + data/nouveautes.json, push.
import json, os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
p = os.path.join(R, 'data', 'nouveautes.json')
d = json.load(open(p, encoding='utf-8'))
e = next((x for x in d if x.get('date') == '2026-11-22'), None)
assert e, 'la cloche du 22/11 (patch-jour-j-s3.py) doit être faite avant'
lignes = [
    "📯 Les clans s'organisent : le chef ou un bras droit pose jusqu'à 3 cibles (viseur rouge sur la carte, et dans Mon front) et lance un appel à l'assaut qui prévient tout le clan.",
    "⚡ La Centrale du clan : financée par les dons des membres (onglet Clan), elle donne 8 énergie par jour à chacun.",
    "💥 Nouveau bâtiment, l'Artillerie (20 lingots) : tes sièges à moins de 50 km d'elle n'ont plus le malus de distance. Secrète tant qu'elle ne tire pas.",
]
if lignes[0] in e['nouveautes']:
    print('déjà fait')
else:
    e['nouveautes'] = lignes + e['nouveautes']
    s = json.dumps(d, indent=2, ensure_ascii=False)
    assert json.loads(s) == d
    open(p, 'w', encoding='utf-8').write(s + '\n')
    print('cloche : ok')
print('Ensuite : python3 maj-version.py, vérifier VERSION_JEU = version.json, commit, push.')
