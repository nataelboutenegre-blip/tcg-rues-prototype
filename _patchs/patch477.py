# patch477 : une attaque lancée depuis la carte apparaît tout de suite dans Combat (signalé par ASMFCB, 20/11).
# Avant : Combat ne se rechargeait qu'une fois par minute, et l'assaut depuis la carte ne le prévenait pas.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
rep(A, """    pcApresAssaut(code, r);   // patch336
    chancesPerimer(code, r.conquise);   // patch446 : le % de la grille suit""",
"""    pcApresAssaut(code, r);   // patch336
    chancesPerimer(code, r.conquise);   // patch446 : le % de la grille suit
    combatChargeLe = 0;   // patch477 : Combat se relira en y allant
    if(!r.conquise) combatRafraichirPlusTard(false);""")
rep(A, "      if(!combatRafraichTimer && Date.now() - combatChargeLe > 60000) loadCombat();",
       "      if(combatChargeLe === 0 || (!combatRafraichTimer && Date.now() - combatChargeLe > 60000)) loadCombat();   // patch477")
print('patch477 : fini')
