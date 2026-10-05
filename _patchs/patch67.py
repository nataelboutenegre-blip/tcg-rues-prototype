# -*- coding: utf-8 -*-
u"""
patch67 — Les Succes passent dans le Profil, en volet.

POURQUOI
  Liberer une place dans le menu avant l'arrivee du QG (Commune du jour +
  Radar). Demande de Natael le 4 octobre au soir : « mettre les succes
  dans le profil pour liberer un onglet ».

CE QUE LE JOUEUR VOIT
  - L'onglet Succes disparait de la colonne (ordinateur) et du menu Plus
    (telephone).
  - Profil s'ouvre avec deux volets en haut : « Profil » et « Succes »,
    comme Attaquer / Defendre dans Combat.

CE QUI NE CHANGE PAS
  Le contenu des deux panneaux et leurs fonctions. L'onglet Succes existe
  toujours dans la page, cache : tout ce qui y menait y mene encore.
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

def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

def volets(actif):
    def v(id_, nom):
        a = id_ == actif
        return (u'<button type="button" class="volet%s" data-volet="%s" role="tab" aria-selected="%s">%s</button>'
                % (' actif' if a else '', id_, 'true' if a else 'false', nom))
    return (u'\n      <div class="volets" role="tablist" aria-label="Profil">\n        '
            + v('profil', u'Profil') + u'\n        ' + v('succes', u'Succès') + u'\n      </div>')


# ---------------- index.html ----------------
html = lire('index.html')

html = rempl(html,
u"""      <div class="tab" data-tab="succes">""",
u"""      <div class="tab onglet-fusionne" data-tab="succes" aria-hidden="true">""", 'onglet succes cache')

html = rempl(html,
u"""    <section class="tab-panel" id="panel-succes">
      <h1>Succès</h1>""",
u"""    <section class="tab-panel" id="panel-succes">
      <h1>Profil</h1>""" + volets('succes'), 'panneau succes')

html = rempl(html,
u"""    <section class="tab-panel" id="panel-profil">
      <h1>Profil</h1>""",
u"""    <section class="tab-panel" id="panel-profil">
      <h1>Profil</h1>""" + volets('profil'), 'panneau profil')

ecrire('index.html', html)


# ---------------- app.js ----------------
js = lire('app.js')

js = rempl(js,
u"""const ONGLETS_FUSIONNES = ['defense'];""",
u"""const ONGLETS_FUSIONNES = ['defense', 'succes'];
// l'onglet qui s'allume quand on ouvre un volet fusionne
const ONGLET_PARENT = { defense: 'combat', succes: 'profil' };""", 'liste fusion')

js = rempl(js,
u"""    if(ONGLETS_FUSIONNES.indexOf(tab.dataset.tab) >= 0){
      const combat = document.querySelector('.tab[data-tab="combat"]');
      if(combat) combat.classList.add('active');""",
u"""    if(ONGLETS_FUSIONNES.indexOf(tab.dataset.tab) >= 0){
      const parent = document.querySelector(`.tab[data-tab="${ONGLET_PARENT[tab.dataset.tab]}"]`);
      if(parent) parent.classList.add('active');""", 'onglet parent')

ecrire('app.js', js)

print(u'patch67 applique : index.html, app.js')
