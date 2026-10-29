# patch264 : le journal disait « une rare » pour une épique (signalé par Nataël le 29/10)
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch264' not in s
s = rep(s, "  else texte = `${acteur} ${a} tiré ${e.tier === 'legendaire' ? 'une légendaire' : 'une rare'} : ${commune}`;",
           "  else texte = `${acteur} ${a} tiré ${({ legendaire: 'une légendaire', epique: 'une épique', rare: 'une rare', peucommun: 'une peu commune' })[e.tier] || 'une carte'} : ${commune}`;   // patch264 : l'épique était annoncée « rare »")
f.write_text(s, encoding='utf-8')
print('patch264 ok')
