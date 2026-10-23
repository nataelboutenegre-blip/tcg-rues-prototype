# -*- coding: utf-8 -*-
u"""
patch153 — contrat : « Passer » pendant le défilé faisait disparaître la carte
gagnante (23 octobre, vidéo d'un joueur).

Cause : direct() remplaçait le défilé par la seule carte gagnante, centrée,
mais gardait le décalage du défilé (translateX de plusieurs milliers de
pixels) : la carte était posée hors de la piste, il ne restait que le halo.
Le premier contrat d'une session marchait parce qu'il allait jusqu'au bout.
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
assert 'patch153' not in js, u'patch153 deja applique'
js = rempl(js, u"""  const direct = () => {
    rail.style.transition = 'none';
    rail.style.justifyContent = 'center';""", u"""  const direct = () => {
    rail.style.transition = 'none';
    rail.style.transform = 'none';   // patch153 : sinon la carte reste decalee hors de la piste
    rail.style.justifyContent = 'center';""", 'direct')
ecrire('app.js', js)
print(u'patch153 applique. Lancer : python3 maj-version.py')
