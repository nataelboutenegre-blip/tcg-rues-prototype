# patch234 : règles — les paliers de territoire (s2-43, barème ×2)
import pathlib
f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:60], s.count(a)); s = s.replace(a, b)
rep('''                  <tr><td>Département dominé (le plus de communes, seul, et au moins 10 %)</td><td class="chiffre or">+100</td></tr>
                  <tr><td>Département contrôlé (au moins 50 %), à la place de dominé</td><td class="chiffre or">+300</td></tr>
                  <tr><td>Région : plus de la moitié de ses départements dominés ou contrôlés</td><td class="chiffre or">+600</td></tr>''',
'''                  <tr><td>Département à 5 % (seul en tête, au moins 5 communes)</td><td class="chiffre or">+100</td></tr>
                  <tr><td>Département à 10 % (seul en tête)</td><td class="chiffre or">+200</td></tr>
                  <tr><td>Département à 25 % (seul en tête)</td><td class="chiffre or">+300</td></tr>
                  <tr><td>Département à 50 %</td><td class="chiffre or">+600</td></tr>
                  <tr><td>Département à 75 %</td><td class="chiffre or">+900</td></tr>
                  <tr><td>Département entier (100 %)</td><td class="chiffre or">+1 400</td></tr>
                  <tr><td>Région : plus de la moitié de ses départements à 10 % ou plus</td><td class="chiffre or">+1 200</td></tr>''')
rep('''<p>Points des communes, de commune à légendaire.''',
'''<p>Par département, seul le palier le plus haut compte (métropole). Points des communes, de commune à légendaire.''')
f.write_text(s, encoding='utf-8'); print('patch234 ok')
