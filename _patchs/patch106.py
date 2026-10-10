# -*- coding: utf-8 -*-
u"""
patch106 — saison à durée fixe : la jauge du Tirage affiche la date de fin.
SQL : _sql/s2-14-saison-4-semaines.sql (sans effet en saison 1).

Quand la saison a une date de fin fixée (saison 2) et que le compte à rebours
n'est pas encore lancé, le bloc « communes libres » du Tirage dit
« Fin de saison dans N jours · le 7 novembre » et la jauge avance avec le
temps (sur 28 jours). Sans date (saison 1), rien ne change.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)

js = lire('app.js')
assert 'DUREE_SAISON_JOURS' not in js, u'patch106 deja applique'
js = rempl(js, u"""  document.getElementById('potNombre').textContent = libres.toLocaleString('fr-FR');
  document.getElementById('potSeuil').textContent = seuil > 0
    ? `La fin de saison s'enclenche à ${seuil.toLocaleString('fr-FR')}` : '';
  const pct = total > seuil ? Math.max(0, Math.min(100, (total - libres) / (total - seuil) * 100)) : 100;""",
u"""  document.getElementById('potNombre').textContent = libres.toLocaleString('fr-FR');
  document.getElementById('potSeuil').textContent = seuil > 0
    ? `La fin de saison s'enclenche à ${seuil.toLocaleString('fr-FR')}` : '';
  let pct = total > seuil ? Math.max(0, Math.min(100, (total - libres) / (total - seuil) * 100)) : 100;
  // patch106 : saison a duree fixe (saison 2) : la date de fin, et le temps qui passe
  if(s.fin_prevue && s.etat === 'en_cours'){
    const fin = new Date(s.fin_prevue).getTime();
    const jours = Math.max(0, Math.ceil((fin - Date.now()) / 86400000));
    const date = new Date(fin).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });
    document.getElementById('potSeuil').textContent = `Fin de saison dans ${jours} jour${jours > 1 ? 's' : ''} · le ${date}`;
    pct = Math.max(0, Math.min(100, 100 - (fin - Date.now()) / (DUREE_SAISON_JOURS * 86400000) * 100));
  }""", 'pot')
js = rempl(js, u"""let potLibres = null;""", u"""let potLibres = null;
const DUREE_SAISON_JOURS = 28;   // doit rester aligne avec jour-j-4-ouverture.sql""", 'const')
ecrire('app.js', js)
print(u'patch106 applique')
