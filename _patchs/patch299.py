# patch299 : énergie du Front, réserve 50 (31/10) — va avec _sql/s2-71-energie-50.sql
# La bascule Terra/Front affichait « / 40 énergie » en dur : elle suit maintenant le maximum
# renvoyé par le serveur (front_energie). Règles et aide passent à 50.
import json, pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch299' not in s
s = rep(s, """<b id="mbEnergie">—</b>/ 40 énergie</span>""",
           """<b id="mbEnergie">—</b>/ <span id="mbMax">50</span> énergie</span>""")
s = rep(s, """  energieEtat = { energie: Number(data[0].energie), maximum: Number(data[0].maximum) || 40, prochaine_dans: data[0].prochaine_dans, lu: Date.now() };""",
           """  energieEtat = { energie: Number(data[0].energie), maximum: Number(data[0].maximum) || 40, prochaine_dans: data[0].prochaine_dans, lu: Date.now() };
  const mx = document.getElementById('mbMax'); if(mx) mx.textContent = energieEtat.maximum;   // patch299 : le maximum du serveur""")
s = rep(s, "texte: 'Ici, l\\'énergie remplace les TerraPoints : 40 au maximum, +1 toutes les 10 minutes. Elle sert à attaquer et à défendre.' },",
           "texte: 'Ici, l\\'énergie remplace les TerraPoints : 50 au maximum, +1 toutes les 10 minutes. Elle sert à attaquer et à défendre.' },   // patch299")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
assert 'patch299' not in s
s = rep(s, """<div class="chiffre-bloc"><b>40</b><span>énergie au maximum</span></div>""",
           """<div class="chiffre-bloc"><b>50</b><span>énergie au maximum</span></div><!-- patch299 -->""")
s = rep(s, "elle peut faire dépasser les 40, jusqu'à 60.</p>", "elle peut faire dépasser les 50, jusqu'à 60.</p>")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('data/nouveautes.json'); d = json.loads(f.read_text(encoding='utf-8'))
e = next(x for x in d if x['date'] == '2026-10-31')
e['nouveautes'].insert(0, '⚡ Front : la réserve d’énergie passe de 40 à 50 (toujours +1 toutes les 10 minutes)')
f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch299 appliqué')
