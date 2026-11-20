# patch479 : la carte se recharge en entier toutes les 15 minutes (signalé par D.C.A, 20/11 : des communes
# affichées libres alors que le serveur en compte 0). Entre deux, seuls les changements arrivent (patch329) ;
# un changement manqué (grosse opération serveur qui se termine en retard) laissait une commune « libre » à tort
# jusqu'au prochain lancement du jeu.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
rep(A, "  othersMap = m;\n  CARTE.id = Number(data.id) || 0; CARTE.uid = uid; CARTE.dispo = true;\n  return true;",
       "  othersMap = m;\n  CARTE.id = Number(data.id) || 0; CARTE.uid = uid; CARTE.dispo = true;\n  CARTE.toutLe = Date.now();   // patch479\n  return true;")
rep(A, """  const p = (CARTE.id != null && CARTE.uid === uid) ? carteDelta(rendre) : carteToutCharger(uid);""",
"""  // patch479 : tout recharger au moins toutes les 15 minutes, au cas où un changement aurait été manqué
  const p = (CARTE.id != null && CARTE.uid === uid && Date.now() - (CARTE.toutLe || 0) < 15 * 60000) ? carteDelta(rendre)
    : carteToutCharger(uid).then(ok => { if(ok && rendre && CARTE.id != null){ renderMapOverlay(); majBlasonsJournal(); carteMesPlusTard(); } return ok; });""")
print('patch479 : fini')
