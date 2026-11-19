# patch472 : l'alerte « Un tour de roue t'attend » suit les vrais tours de roue, plus les paquets gratuits.
# Signalé par Oshannir le 19/11 : depuis que la roue a ses propres jetons (jetons_propres), les jetons de paquets
# ne se dépensent plus quand la carte est pleine ; l'alerte revenait alors qu'il avait déjà tourné.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
rep(A, "let dispoPrecedente = null;   // pour reperer le moment ou un jeton se recharge",
       "let dispoPrecedente = null;   // pour reperer le moment ou un jeton se recharge\n"
       "let roueToursPrecedents = null;   // patch472 : idem pour les tours de roue (la roue a ses propres jetons)")
rep(A, """  if(dispoPrecedente !== null && dispo > dispoPrecedente && !paquetEnCours && roueRemplace() && !roueTourne && ROUE.tours_jour < ROUE.par_jour){   // patch343, patch445
    notifier({
      type: 'succes',
      titre: 'Un tour de roue t\\'attend',
      texte: dispo > 1 ? `Tu en as ${dispo} en réserve. Touche ici pour tourner la roue du Front.` : 'Touche ici pour tourner la roue du Front.',""",
"""  // patch472 : on compte les tours de roue eux-mêmes, pas les paquets gratuits (qui ne se dépensent plus quand la roue les remplace)
  const toursRoue = roueRemplace() ? Math.floor(roueJetons()) + Math.max(0, Number(ROUE.offerts) || 0) + roueSoirReste() : null;
  const roueJouable = toursRoue !== null && (roueSoirReste() > 0 || Number(ROUE.offerts) > 0 || Number(ROUE.tours_jour) < Number(ROUE.par_jour));
  if(toursRoue !== null && roueToursPrecedents !== null && toursRoue > roueToursPrecedents && !paquetEnCours && !roueTourne && roueJouable){   // patch343, patch445, patch472
    notifier({
      type: 'succes',
      titre: 'Un tour de roue t\\'attend',
      texte: toursRoue > 1 ? `Tu en as ${toursRoue} en réserve. Touche ici pour tourner la roue du Front.` : 'Touche ici pour tourner la roue du Front.',""")
rep(A, "  dispoPrecedente = dispo;\n  majPaquetPret(dispo);",
       "  dispoPrecedente = dispo;\n  roueToursPrecedents = toursRoue;   // patch472\n  majPaquetPret(dispo);")
rep(A, "    dispoPrecedente = null;   // pas de fausse notification « paquet gratuit »",
       "    dispoPrecedente = null;   // pas de fausse notification « paquet gratuit »\n    roueToursPrecedents = null;   // patch472")
print('patch472 : fini')
