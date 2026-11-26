# patch544 : Espagne (test) : le Portugal entier en voisin grisé, le Maroc et l'Algérie près de Ceuta et Melilla ;
# contours des provinces refaits avec mapshaper (frontières communes identiques, trous des condominios comblés).
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "const lire = (f) => fetch('data/' + f + '?v=1', { cache: 'force-cache' })", "const lire = (f) => fetch('data/' + f + (f === 'voisins.json' ? '?v=2' : '?v=1'), { cache: 'force-cache' })")
rep('app.js', "// patch331 : le fond de la saison 3 (Suisse, lacs, frontière, voisins)\nlet FOND_S3 = null;", "// patch331 : le fond de la saison 3 (Suisse, lacs, frontière, voisins ; patch544 : voisins.json en v2)\nlet FOND_S3 = null;")
rep('app.js', "data/contours-provinces-es.json?v=1", "data/contours-provinces-es.json?v=2", n=2)
