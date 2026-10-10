# -*- coding: utf-8 -*-
u"""
patch du JOUR J — ouvre la saison 2 côté jeu : SAISON2 = true,
EPIQUE_VISIBLE = true. À appliquer JUSTE APRÈS jour-j-4-ouverture.sql
(sinon les écrans de Terra afficheraient « Terra n'est pas encore ouvert »).
Puis : python3 maj-version.py, commit, push.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = ICI
while not os.path.exists(os.path.join(BASE, 'app.js')) and BASE != os.path.dirname(BASE):
    BASE = os.path.dirname(BASE)
p = os.path.join(BASE, 'app.js')
with io.open(p, encoding='utf-8') as f: js = f.read()
for avant, apres in [(u"const SAISON2 = false;", u"const SAISON2 = true;"),
                     (u"const EPIQUE_VISIBLE = false;", u"const EPIQUE_VISIBLE = true;")]:
    if apres in js: print(u'deja fait :', apres); continue
    assert js.count(avant) == 1, avant
    js = js.replace(avant, apres)
with io.open(p, 'w', encoding='utf-8') as f: f.write(js)
print(u'saison 2 ouverte cote jeu')
