# patch356 (6/11/2026) : légende de la carte (Territoire).
#
# 1. Sur ordinateur, les bâtiments de la légende sont l'un sous l'autre :
#    à trois sur une ligne, le « Centre dévoilé » dépassait sur le côté.
#    Rien ne change sur téléphone (légende sous la carte).
# 2. La Banque rejoint la légende (4e ligne), avec sa bulle d'explication.
#    Elle reste secrète sur la carte : seul son propriétaire y voit la sienne.
# Aperçu validé par Nataël le 6/11. Rien d'autre ne change, aucun SQL.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch356' not in s, 'patch356 déjà appliqué'

s = rep(s, "${['fonderie', 'forteresse', 'centre'].map(k => `<button type=\"button\" class=\"leg-bt-info${btBulleCle === k ? ' on' : ''}\" data-bt-info=\"${k}\" aria-expanded=\"${btBulleCle === k}\"><span class=\"leg-bt${k === 'centre' ? ' leg-centre' : ''}\">${k === 'fonderie' ? ICONE_FONDERIE : k === 'forteresse' ? ICONE_FORTERESSE : ICONE_CENTRE}</span>",
           "${['fonderie', 'forteresse', 'centre', 'banque'].map(k => `<button type=\"button\" class=\"leg-bt-info${btBulleCle === k ? ' on' : ''}\" data-bt-info=\"${k}\" aria-expanded=\"${btBulleCle === k}\"><span class=\"leg-bt${k === 'centre' ? ' leg-centre' : ''}\">${k === 'fonderie' ? ICONE_FONDERIE : k === 'forteresse' ? ICONE_FORTERESSE : k === 'banque' ? ICONE_BANQUE : ICONE_CENTRE}</span>")   # patch356

s = rep(s, "    pied: 'Pour en construire un : 2 Fonderies et 40 lingots.' },\n};",
           "    pied: 'Pour en construire un : 2 Fonderies et 40 lingots.' },\n"
           "  banque: { titre: 'Banque', role: 'Elle met tes lingots à l’abri, en plus de la réserve de tes Fonderies.',   // patch356\n"
           "    li: ['Coûte <b>20 lingots</b>, une seule par joueur, il faut une Fonderie.', '<b>+60 lingots</b> de réserve, à l’abri du pillage des Fonderies.',\n"
           "         '<b>Secrète</b> : toi seul la vois sur la carte.', 'Si on prend sa commune, elle disparaît et le joueur pille <b>la moitié</b> de son contenu. Une bombe lui en fait perdre 20 à 40 %.'],\n"
           "    pied: 'Se construit en 6 h sur une de tes communes.' },\n};")

s = rep(s, "  const ic = k === 'fonderie' ? ICONE_FONDERIE : k === 'forteresse' ? ICONE_FORTERESSE : ICONE_CENTRE;",
           "  const ic = k === 'fonderie' ? ICONE_FONDERIE : k === 'forteresse' ? ICONE_FORTERESSE : k === 'banque' ? ICONE_BANQUE : ICONE_CENTRE;   // patch356")

F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch356' not in c
c += "\n/* patch356 : sur ordinateur, les bâtiments de la légende l'un sous l'autre */\n" \
     "@media (min-width: 721px){\n  .leg-tailles.leg-batiments{ flex-direction:column; align-items:flex-start; gap:2px; }\n}\n"
C.write_text(c, encoding='utf-8')
print('patch356 appliqué')
