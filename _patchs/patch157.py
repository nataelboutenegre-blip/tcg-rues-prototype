# -*- coding: utf-8 -*-
u"""
patch157 — la Collection Terra s'arretait a 1000 cartes (25 octobre).
Supabase plafonne chaque reponse a 1000 lignes, y compris les fonctions :
terra_collection_moi et terra_bloques_moi passent par toutesLesLignes
(pages par code de commune, comme les possessions du Front).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)
js = lire('app.js')
assert 'patch157' not in js, u'patch157 deja applique'
js = rempl(js, u"""  const { data, error } = await sb.rpc('terra_collection_moi');""",
u"""  // patch157 : par pages, sinon la collection s'arrete a 1000 cartes
  const { data, error } = await toutesLesLignes(() => sb.rpc('terra_collection_moi'), 'code');""", 'collection')
js = rempl(js, u"""    const { data: bl, error: eb } = await sb.rpc('terra_bloques_moi');""",
u"""    const { data: bl, error: eb } = await toutesLesLignes(() => sb.rpc('terra_bloques_moi'), 'code');""", 'bloques')
ecrire('app.js', js)
print(u'patch157 applique. Lancer : python3 maj-version.py')
