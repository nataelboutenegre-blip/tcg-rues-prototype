# patch416 (11/11/2026) : calque Clans « Plein » sans le contour du clan (Cairnan217, #bugs 16 h 28 : « la vision clan
# plein a aussi les contours »). En « Plein », le gros trait du clan (bord sombre + couleur du clan) était encore tracé
# autour du territoire, par-dessus le remplissage. Il ne reste que le remplissage et le trait fin entre les membres ;
# « Contour » ne change pas. Trois endroits : de près, de loin (départements), outre-mer.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
if 'patch416' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')
rep(A, """        if(CLANS && CALQUES.clans && j.clan){   // patch212""",
"""        if(CLANS && CALQUES.clans && j.clan && !pleinD){   // patch212 ; patch416 : pas en « Plein »""")
rep(A, """      if(parClan) for(const { couleur, chemin } of parClan.values()){
        const dehors = new Path2D();
        dehors.rect(-MAP_W, -MAP_H, MAP_W * 3, MAP_H * 3);""",
"""      if(parClan && !clanPlein()) for(const { couleur, chemin } of parClan.values()){   // patch416 : pas en « Plein »
        const dehors = new Path2D();
        dehors.rect(-MAP_W, -MAP_H, MAP_W * 3, MAP_H * 3);""")
rep(A, """  if(parClan) for(const { couleur, chemin } of parClan.values()){
    const dehors = new Path2D();
    dehors.rect(-larg, -haut, larg * 3, haut * 3);""",
"""  if(parClan && !clanPlein()) for(const { couleur, chemin } of parClan.values()){   // patch416 : pas en « Plein »
    const dehors = new Path2D();
    dehors.rect(-larg, -haut, larg * 3, haut * 3);""")
print('patch416 OK')
