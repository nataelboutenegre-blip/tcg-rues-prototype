# patch548 : la carte du Territoire allégée. Barre « France/Outre-mer · ☰ · 🎨 Mon territoire » au-dessus de la carte ;
# options d'affichage dans un panneau du bas ; couleur + motif ouverts depuis la carte ; Profil : un lien au lieu du nuancier en double.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
D = os.path.dirname(os.path.abspath(__file__))
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
def ajouter(f, src, marque):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if marque in t: print(f'{f} : déjà ajouté'); return
    open(p, 'a', encoding='utf-8').write(open(os.path.join(D, src), encoding='utf-8').read()); print(f'{f} : ajouté')
rep('app.js', "    ${blocParrainage(p.parrainage)}\n    ${blocCouleur()}\n", "    ${blocParrainage(p.parrainage)}\n    ${blocTerrLien()}\n")   # patch548
ajouter('app.js', 'patch548-carte.js', 'patch548 : la carte du Territoire allégée')
ajouter('style.css', 'patch548.css', 'patch548 : la carte du Territoire allégée')
p = os.path.join(R, 'data/nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
assert d[0]['date'] == '2026-11-26'
n1 = "🗺️ Carte du Territoire plus dégagée : les options d'affichage passent derrière le bouton ☰, et le nouveau bouton « 🎨 Mon territoire » ouvre directement ta couleur et ton motif."
if n1 not in d[0]['nouveautes']: d[0]['nouveautes'].append(n1)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('nouveautes : ok')
