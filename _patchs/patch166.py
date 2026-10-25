# -*- coding: utf-8 -*-
u"""
patch166 — cartes blanches, sans dessin, dans « Ma vitrine » (Maroli,
25 octobre, telephone). Le dessin d'une mini-carte est un degrade SVG avec un
identifiant tire du code de la commune : la meme carte affichee dans la
Collection (onglet cache) et dans la vitrine avait deux fois le meme id ;
le navigateur prend le premier, qui est dans un bloc cache, et ne peint rien.
Chaque dessin recoit maintenant un identifiant unique (le gabarit reste en
cache, l'id change a chaque affichage).
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
assert 'patch166' not in js, u'patch166 deja applique'
js = rempl(js, u"""function miniArtSvg(code, tierId){
  const cle = code + '|' + tierId;
  if(miniArtCache.has(cle)) return miniArtCache.get(cle);""", u"""// patch166 : un id unique par affichage (gabarit en cache, id a la sortie)
let miniArtNumero = 0;
function miniArtSvg(code, tierId){
  const cle = code + '|' + tierId;
  const gabarit = miniArtCache.get(cle) || miniArtGabarit(code, tierId, cle);
  return gabarit.split('__MGID__').join('mg' + (++miniArtNumero).toString(36));
}
function miniArtGabarit(code, tierId, cle){""", 'entree')
js = rempl(js, u"""  const id = 'mg' + hashTexte(cle).toString(36);
  const { d, cx, cy } = courbesDeNiveau(hashTexte(String(code)), 160, 100, 6, 36);""", u"""  const id = '__MGID__';
  const { d, cx, cy } = courbesDeNiveau(hashTexte(String(code)), 160, 100, 6, 36);""", 'id')
ecrire('app.js', js)
print(u'patch166 applique. Lancer : python3 maj-version.py')
