# patch415 (11/11/2026) : mentions légales, les sources de la Suisse (saison 3)
# swisstopo demande de citer la source (« © swisstopo ») ; Wikidata (CC0) et Natural Earth (domaine public) par
# correction. Les photos des communes viennent aussi de Wikimedia Commons (avant : « photos de monuments » seulement).
# Page statique : visible dès la mise en ligne (pas d'interrupteur). À mettre en ligne au plus tard le jour J.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
M = 'mentions-legales.html'
if 'swisstopo' in open(M, encoding='utf-8').read(): sys.exit('déjà appliqué')
rep(M, """<p>Les photos de monuments proviennent de Wikimedia Commons : leur auteur et leur licence sont indiqués sous chaque photo.</p>""",
"""<p>Les communes suisses (noms officiels, populations, contours) et les lacs proviennent de swissBOUNDARIES3D et de swissTLMRegio : © swisstopo. Leurs noms en français proviennent de Wikidata. Les contours des pays voisins proviennent de Natural Earth (domaine public).</p>
<p>Les photos des communes et des monuments proviennent de Wikimedia Commons : leur auteur et leur licence sont indiqués sous chaque photo.</p>""")
print('patch415 OK')
