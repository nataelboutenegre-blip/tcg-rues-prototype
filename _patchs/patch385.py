# patch385 : la case « Relance » de la roue du Front offre 2 tours (s2-123, demande de Nataël 8/11).
# Textes seulement : « 2 tours offerts » dans les chances de la roue et sur l'annonce du gain.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
s = rep(s, """  if(Number(k.relance)) return 'Un tour offert';   // patch351""",
           """  if(Number(k.relance)) return Number(k.relance) > 1 ? `${Number(k.relance)} tours offerts` : 'Un tour offert';   // patch351, patch385""")
s = rep(s, """  if(offert) parts.push('Tour offert');""",
           """  const nOff = Number(d.tours_offerts) || 1;   // patch385 : la Relance peut offrir plusieurs tours
  if(offert) parts.push(nOff > 1 ? `${nOff} tours offerts` : 'Tour offert');""")
s = rep(s, """  else if(offert) note = 'Ton tour est rendu : il ne compte pas dans la journée';   // patch351""",
           """  else if(offert) note = nOff > 1 ? `Ton tour est rendu et tu en gagnes ${nOff - 1 > 1 ? nOff - 1 : 'un'} de plus : relance la roue !` : 'Ton tour est rendu : il ne compte pas dans la journée';   // patch351, patch385""")
F.write_text(s, encoding='utf-8')
print('patch385 ok')
