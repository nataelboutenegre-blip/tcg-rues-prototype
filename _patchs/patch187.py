# -*- coding: utf-8 -*-
u"""
patch187 — Tirage : en passant de Terra a Front (ou l'inverse), les cartes
tirees dans l'autre mode ne restent plus affichees. La zone du paquet est
videe (sauf paquet en cours, ou le changement de mode est deja refuse), puis
le paquet gratuit du nouveau mode s'affiche s'il y en a un. Plus de fausse
notification « Un paquet gratuit t'attend » au changement de mode.
Aucun SQL.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
js = lire('app.js')
assert 'patch187' not in js, u'patch187 deja applique'
avant = u"""  // patch90 : le statut des paquets et la collection suivent le mode
  loadPackStatus();"""
apres = u"""  // patch187 : les cartes tirees dans l'autre mode ne restent pas a l'ecran
  if(!paquetEnCours){
    const zoneP = document.getElementById('packZone');
    if(zoneP) zoneP.innerHTML = '';
    dispoPrecedente = null;   // pas de fausse notification « paquet gratuit »
  }
  // patch90 : le statut des paquets et la collection suivent le mode
  loadPackStatus();"""
assert js.count(avant) == 1, u'appliquerMode : %d occurrences (attendu 1)' % js.count(avant)
ecrire('app.js', js.replace(avant, apres))
print(u'patch187 applique. Lancer : python3 maj-version.py')
