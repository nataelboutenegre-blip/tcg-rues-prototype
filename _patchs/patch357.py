# patch357 (6/11/2026) : légende de la carte, les icônes orange ensemble
# (Fonderie, Forteresse, Banque), puis le Centre dévoilé (bleu).
# Demande de Nataël. Rien d'autre ne change, aucun SQL.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch357' not in s, 'patch357 déjà appliqué'
s = rep(s, "${['fonderie', 'forteresse', 'centre', 'banque'].map(k =>",
           "${['fonderie', 'forteresse', 'banque', 'centre'].map(k =>   /* patch357 */")
F.write_text(s, encoding='utf-8')
print('patch357 appliqué')
