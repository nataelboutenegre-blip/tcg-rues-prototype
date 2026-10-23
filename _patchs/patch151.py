# -*- coding: utf-8 -*-
u"""
patch151 — Terra : un paquet gratuit toutes les 30 minutes (au lieu de 20).
Le Front reste à 20 minutes. Réserve de 3 inchangée.
Le serveur décide (_sql/s2-25-terra-30min.sql, à lancer dans Supabase) ;
ce patch aligne le compte à rebours affiché et les textes Terra.
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
assert 'MIN_PAQUET_TERRA' not in js, u'patch151 deja applique'
js = rempl(js, u"""function liveJetons(){
  if(!packStatusCache) return 0;
  const elapsedMin = (Date.now() - packStatusFetchedAt) / 60000;
  return Math.min(3, packStatusCache.jetons_actuels + elapsedMin / 20);
}""", u"""// patch151 : Terra recharge un paquet en 30 min, le Front en 20 (le serveur fait foi)
const MIN_PAQUET_TERRA = 30, MIN_PAQUET_FRONT = 20;
function minParPaquet(){ return enTerra() ? MIN_PAQUET_TERRA : MIN_PAQUET_FRONT; }
function liveJetons(){
  if(!packStatusCache) return 0;
  const elapsedMin = (Date.now() - packStatusFetchedAt) / 60000;
  return Math.min(3, packStatusCache.jetons_actuels + elapsedMin / minParPaquet());
}""", 'liveJetons')
js = rempl(js, u"const minutes = Math.ceil((1 - (live % 1)) * 20);",
               u"const minutes = Math.ceil((1 - (live % 1)) * minParPaquet());", 'minutes')
js = rempl(js, u"texte: 'Un paquet gratuit toutes les 20 minutes, 3 en réserve, 5 communes à chaque fois.",
               u"texte: 'Un paquet gratuit toutes les 30 minutes, 3 en réserve, 5 communes à chaque fois.", 'guide s2')
ecrire('app.js', js)

h = lire('index.html')
h = rempl(h, u"<p>En Terra, un paquet gratuit toutes les 20 minutes complète ta propre France.",
             u"<p>En Terra, un paquet gratuit toutes les 30 minutes complète ta propre France.", 'accueil site s2')
h = rempl(h, u"""<div class="chiffre-bloc"><b>20 min</b><span>pour recharger un paquet gratuit (3 en réserve)</span></div><div class="chiffre-bloc"><b>200 pts</b>""",
             u"""<div class="chiffre-bloc"><b>30 min</b><span>pour recharger un paquet gratuit (3 en réserve)</span></div><div class="chiffre-bloc"><b>200 pts</b>""", 'regles terra')
ecrire('index.html', h)
print(u'patch151 applique. Lancer : python3 maj-version.py')
