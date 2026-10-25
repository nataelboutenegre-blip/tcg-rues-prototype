# -*- coding: utf-8 -*-
u"""
patch161 — le paquet gratuit deja pose sur l'ecran ne prenait pas le dos OG
(signale par Nataël le 25 octobre). Il est dessine a l'arrivee, souvent
avant que la Boutique dise quel dos est equipe, et restait tel quel.
appliquerDos redessine le paquet gratuit en attente quand le dos change.
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
assert 'patch161' not in js, u'patch161 deja applique'
js = rempl(js, u"""function appliquerDos(id){
  document.body.dataset.dos = dosCle(id);
}""", u"""function appliquerDos(id){
  const avant = document.body.dataset.dos;
  document.body.dataset.dos = dosCle(id);
  // patch161 : le paquet gratuit qui attend sur l'ecran suit le nouveau dos
  if(avant !== document.body.dataset.dos && !paquetEnCours){
    const zone = document.getElementById('packZone');
    if(zone && zone.querySelector('.paquet[data-pret]')){ zone.innerHTML = ''; afficherPaquetPret('gratuit'); }
  }
}""", 'dos')
ecrire('app.js', js)
print(u'patch161 applique. Lancer : python3 maj-version.py')
