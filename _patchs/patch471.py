# patch471 : le nom d'une commune ne se coupe plus au milieu d'un mot sur les petites cartes (« Châteaubour / g »).
# Vu par Nataël le 19/11 sur une carte à skin. Un nom dont un mot fait 11 lettres ou plus passe dans la taille « long »
# (comme les noms de plus de 14 caractères) ; s'il ne tient toujours pas, le navigateur coupe à une syllabe, avec un tiret.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
rep(A, "function hashTexte(str){", "// patch471 : un nom à mettre en petit sur une petite carte (trop long, ou un mot trop long pour une ligne)\n"
    "function nomLong(n){ n = String(n || ''); return n.length > 14 || n.split(/[\\s\\-'’]/).some(m => m.length >= 11); }\n"
    "function hashTexte(str){")
rep(A, """<p class="mini-nom ${(nom || '').length > 14 ? 'long' : ''}">""", """<p class="mini-nom ${nomLong(nom) ? 'long' : ''}">""")
rep(A, """<p class="mini-nom ${entry.nom.length > 14 ? 'long' : ''}">""", """<p class="mini-nom ${nomLong(entry.nom) ? 'long' : ''}">""")
rep(A, """<p class="mini-nom ${e.nom.length > 14 ? 'long' : ''}">""", """<p class="mini-nom ${nomLong(e.nom) ? 'long' : ''}">""")
S = 'style.css'
rep(S, "    margin:0; overflow-wrap:anywhere;\n    display:-webkit-box; -webkit-line-clamp:2;",
       "    margin:0; overflow-wrap:break-word; -webkit-hyphens:auto; hyphens:auto;   /* patch471 : coupe à une syllabe, pas n'importe où */\n    display:-webkit-box; -webkit-line-clamp:2;")
print('patch471 : fini')
