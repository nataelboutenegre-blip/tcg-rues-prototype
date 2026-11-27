# patch558 (27/11) : chercher une commune sur les cartes (idée de Saaslil).
# Front : en tête du menu ☰ (loupe sur le bouton). Terra › Ma France : une loupe sous les boutons de zoom.
# Serveur : _sql/s3-89-carte-chercher.sql (carte_chercher).
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
rep('app.js', """<button data-mf="centre" aria-label="Recentrer">⌂</button></div>""",
    """<button data-mf="centre" aria-label="Recentrer">⌂</button><button data-mf="chercher" aria-label="Chercher une commune"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg></button></div>""")
ajouter('app.js', 'patch558-chercher.js', 'patch558 : chercher une commune sur les cartes')
ajouter('style.css', 'patch558.css', 'patch558 : chercher une commune sur les cartes')
p = os.path.join(R, 'data/nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
assert d[0]['date'] in ('2026-11-26', '2026-11-27')
c = "Chercher une commune sur les cartes : en haut du menu 🔍☰ de la carte du Front, et avec la loupe sur Terra › Ma France. La carte se centre dessus. Idée de Saaslil."
if c not in d[0].setdefault('nouveautes', []): d[0]['nouveautes'].insert(0, c)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('nouveautes : ok')
