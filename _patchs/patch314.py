# patch314 : garnison retirée près du plafond d'énergie (s2-81)
# H34VEN (2/11) : deux garnisons pleines retirées, aucune énergie reçue. Le remboursement
# ne fait jamais dépasser 60 d'énergie : un joueur à 58 qui retire 10 ne reçoit que 2.
# Le bouton annonçait pourtant « +7 » et la notification aussi. Désormais le bouton
# prévient avant (« +2 seulement : plafond de 60 ») et la notification dit ce qui a
# vraiment été reçu (s2-81 renvoie le gain réel).
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch314' not in s
s = rep(s, """  const armee = gnRetraitArme === code;
  return `<div class="gn">""", """  const armee = gnRetraitArme === code;
  // patch314 : le remboursement ne fait pas dépasser 60 d'énergie
  const rendu = Math.floor(g.energie * 3 / 4);
  const dispo = energieEtat ? Math.floor(Number(energieEtat.energie) || 0) : 0;
  const recu = Math.max(0, Math.min(rendu, 60 - dispo));
  return `<div class="gn">""")
s = rep(s, """${armee ? `Confirmer (+${Math.floor(g.energie * 3 / 4)})` : 'Retirer'}</button>
    </div></div>`;""", """${armee ? `Confirmer (+${recu})` : 'Retirer'}</button>
    </div>${armee && recu < rendu ? `<p class="gn-txt gn-plafond">Tu as déjà ${dispo} d’énergie : tu ne récupérerais que ${recu} sur ${rendu}, l’énergie ne dépasse pas 60.</p>` : ''}</div>`;""")
s = rep(s, """  if(n === 'retirer') notifier({ type: 'info', titre: 'Garnison retirée', texte: `${r ? r.rendue : 0} énergie te revient.` });""",
           """  if(n === 'retirer') notifier({ type: 'info', titre: 'Garnison retirée', texte: r && Number(r.rendue) > 0 ? `+${r.rendue} énergie.` : 'Aucune énergie rendue : tu étais déjà au plafond de 60.' });   // patch314""")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch314' not in s
s = s.rstrip('\n') + """

/* patch314 : garnison retirée près du plafond */
.gn-plafond{ color:#FFB27A !important; margin-top:6px; }
"""
f.write_text(s, encoding='utf-8')
print('patch314 appliqué')
