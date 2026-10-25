# -*- coding: utf-8 -*-
u"""
patch163 — Contrat : les doublons proposes s'arretaient a 1000 par rarete
(plafond de Supabase par reponse). Depuis les cartes versees le 25 octobre,
les gros joueurs Terra le depassent. Lecture par pages (toutesLesLignes),
comme la collection (patch157). Vaut pour Terra et pour le Front.
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
assert 'patch163' not in js, u'patch163 deja applique'
js = rempl(js, u"""    const res = await Promise.all(CONTRATS.map(c =>
      sb.rpc(terra ? 'terra_contrat_candidates' : 'contrat_candidates', { p_tier: c.de })));""",
u"""    // patch163 : par pages, sinon la liste s'arrete a 1000 doublons
    const res = await Promise.all(CONTRATS.map(c => toutesLesLignes(() =>
      sb.rpc(terra ? 'terra_contrat_candidates' : 'contrat_candidates', { p_tier: c.de }), 'commune_code')));""", 'contrat')
ecrire('app.js', js)
print(u'patch163 applique. Lancer : python3 maj-version.py')
