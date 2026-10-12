# -*- coding: utf-8 -*-
u"""
patch118 — carte en plein écran : la moitié basse restait sans couleurs.

Vu par Nataël sur iPhone juste après patch117 : en plein écran, seules les
communes du haut de l'écran étaient coloriées. Le calcul des départements
« à l'écran » (ceux dont on charge les contours des communes) prenait la
hauteur du cadre pour la hauteur de la carte. Les deux étaient égales tant
que le cadre avait les proportions de la France ; en plein écran le cadre
est bien plus haut, les départements du bas étaient crus hors de l'écran
et leurs contours jamais chargés. On prend désormais la vraie hauteur de la
carte (largeur / proportions), et la hauteur du cadre pour savoir ce qui
est à l'écran.
"""
import io, os

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

js = lire('app.js')
assert 'patch118' not in js, u'patch118 deja applique'
avant = u"""  const w = wrap.clientWidth, h = wrap.clientHeight;
  const vus = new Set();
  const ajouter = (c) => {
    if(c.lat == null) return;
    const p = project(c.lat, c.lon);
    const x = p.x * w * mapZoom + mapPanX, y = p.y * h * mapZoom + mapPanY;"""
apres = u"""  const w = wrap.clientWidth, h = wrap.clientHeight;
  // patch118 : hauteur de la CARTE (et non du cadre, plus haut en plein ecran)
  const hc = MAP_H * (w / MAP_W);
  const vus = new Set();
  const ajouter = (c) => {
    if(c.lat == null) return;
    const p = project(c.lat, c.lon);
    const x = p.x * w * mapZoom + mapPanX, y = p.y * hc * mapZoom + mapPanY;"""
assert js.count(avant) == 1, u'departementsVisibles introuvable'
js = js.replace(avant, apres)
ecrire('app.js', js)
print(u'patch118 applique')
