# patch538 : notification téléphone « Commune perdue » (Bonjean, s3-77) ; Recensement limité à 25 000 habitants.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "  ['perdue', 'Commune perdue', 'Un joueur t’a pris une commune', false],",
              "  ['perdue', 'Commune perdue', 'Un joueur t’a pris une commune · sur le téléphone, une alerte au plus toutes les 15 min', true],   // patch538")
rep('app.js', "                    tel: { attaque: true, paquet: true, defense: true, clan: true }, seuil: 'commun',",
              "                    tel: { attaque: true, perdue: true, paquet: true, defense: true, clan: true }, seuil: 'commun',")
rep('app.js', "Des communes de 3 000 à 60 000 habitants.", "Des communes de 3 000 à 25 000 habitants.")
