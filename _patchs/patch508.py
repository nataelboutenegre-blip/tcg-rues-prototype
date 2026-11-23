# patch508 : sur Android (Chrome 135 et plus, « edge-to-edge »), quand la page défile, le bas de l'écran passe sous la
# barre de navigation du téléphone : la barre d'onglets du jeu était à moitié cachée sur Tirage (page qui défile) et
# pas sur Territoire (page fixe). Signalé par Arkhannou (vidéo du 23/11, 2 h 20).
# Correctif : viewport-fit=cover. Le jeu déclare gérer lui-même les bords : env(safe-area-inset-bottom) vaut alors la
# hauteur de la barre du téléphone, et la barre d'onglets (déjà prévue pour, .tabs-row) reste au-dessus.
# Les autres env(safe-area-inset-*) déjà présents dans style.css (feuilles, carte plein écran, éditeurs) s'activent aussi.
# En paysage sur iPhone, les côtés (encoche) sont protégés par une marge.
# Retour arrière : retirer « , viewport-fit=cover » de la balise viewport d'index.html.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('index.html', '<meta name="viewport" content="width=device-width, initial-scale=1">',
                  '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">')
p = os.path.join(R, 'style.css'); t = open(p, encoding='utf-8').read()
M = '/* patch508 : viewport-fit=cover, les côtés en paysage (encoche) */'
if M not in t:
    t = t.rstrip('\n') + '\n\n' + M + '\n@media (orientation: landscape){ body{ padding-left: env(safe-area-inset-left, 0px); padding-right: env(safe-area-inset-right, 0px); } }\n'
    open(p, 'w', encoding='utf-8').write(t); print('style.css : ok')
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = d[0]; e.setdefault('correctifs', [])
l = "Android : la barre d'onglets ne passe plus à moitié sous la barre du téléphone quand la page défile (Tirage notamment). Signalé par Arkhannou."
if l not in e['correctifs']: e['correctifs'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
