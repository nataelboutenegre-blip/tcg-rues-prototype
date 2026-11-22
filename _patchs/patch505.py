# patch505 : des animaux héraldiques dans les motifs, gratuits (demande d'ASMFCB, 22/11 23 h 55 ; Nataël « rajoute-les
# dans les motifs gratuits »). Nouvel onglet « Animaux » dans la bibliothèque de formes : lion, aigle, griffon, dragon,
# sanglier, ours, loup, cerf, dauphin, coq, cygne, corbeau, licorne, salamandre, abeille, pégase.
# Dessins : game-icons.net (Lorc, Delapouite et autres), licence CC BY 3.0 (usage commercial permis, crédit obligatoire :
# mentionné sous l'onglet et dans les mentions légales). Conversion : _patchs/patch505-animaux-source.py (512 -> 100).
# Va avec s3-56 (les 16 formes dans motif_formes, pack null).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
ICI = os.path.dirname(os.path.abspath(__file__))
an = json.load(open(os.path.join(ICI, 'patch505-animaux.json'), encoding='utf-8'))
p = os.path.join(R, 'motifs-formes.json'); fs = json.load(open(p, encoding='utf-8'))
ids = {f['id'] for f in fs}
for a in an:
    if a['id'] not in ids: fs.append({k: a[k] for k in ('id', 'nom', 'cat', 'pack', 'type', 'd')})
json.dump(fs, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':')); print('motifs-formes.json : ok')
A = 'app.js'
rep(A, "const MOT_CATS = ['Formes', 'Lignes', 'Symboles', 'Héraldique', 'Nature', 'Cartographe', 'Lettres'];",
       "const MOT_CATS = ['Formes', 'Lignes', 'Symboles', 'Animaux', 'Héraldique', 'Nature', 'Cartographe', 'Lettres'];   // patch505 : Animaux")
rep(A, "    : 'Gratuit pour tous.';\n  g.innerHTML = `<div class=\"mot-grille\">",
       "    : 'Gratuit pour tous.' + (ME.cat === 'Animaux' ? ' <small class=\"mot-credit\">Dessins : game-icons.net (Lorc, Delapouite et autres), licence CC BY 3.0.</small>' : '');   // patch505\n  g.innerHTML = `<div class=\"mot-grille\">")
rep('mentions-legales.html', "<p>Les polices Big Shoulders Display et Instrument Sans",
    "<p>Les animaux des motifs de territoire sont des dessins de <a href=\"https://game-icons.net\" rel=\"noopener\">game-icons.net</a> (Lorc, Delapouite et autres auteurs), sous licence <a href=\"https://creativecommons.org/licenses/by/3.0/\" rel=\"noopener\">CC BY 3.0</a>, mis à l'échelle pour le jeu.</p>\n<p>Les polices Big Shoulders Display et Instrument Sans")
p = os.path.join(R, 'style.css'); t = open(p, encoding='utf-8').read()
M = '/* patch505 : le crédit des animaux */'
if M not in t:
    open(p, 'w', encoding='utf-8').write(t.rstrip('\n') + '\n\n' + M + '\n.mot-credit{ display:block; margin-top:4px; font-size:.72rem; opacity:.7; }\n'); print('style.css : ok')
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = max((x for x in d if x.get('date') in ('2026-11-22', '2026-11-23')), key=lambda x: x['date'])
l = "🦁 Motifs : un onglet « Animaux » gratuit, avec 16 figures de l'héraldique (lion, aigle, griffon, dragon, sanglier, ours, loup, cerf, dauphin, coq, cygne, corbeau, licorne, salamandre, abeille, pégase). Idée d'ASMFCB."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
