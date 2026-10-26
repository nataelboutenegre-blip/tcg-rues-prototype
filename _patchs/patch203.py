# -*- coding: utf-8 -*-
u"""
patch203 — skins : 1) une carte Aurore garde son apparence Aurore (pas de
skin dessus : il cachait le fond Aurore et retombait sur le dessin) ;
2) le choix de la vitrine montre les skins de mes cartes, et ma vitrine du
profil se recharge quand je change un skin ou un dos. Aucun SQL.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)

js = lire('app.js')
assert 'patch203' not in js
def rempl(avant, apres, n=1):
    global js
    assert js.count(avant) == n, (js.count(avant), avant[:70])
    js = js.replace(avant, apres)

# 1. le moteur ne pose jamais de skin sur une carte Aurore
rempl(u"""  function skinDe(mini){
    if(mini.dataset.skin) return mini.dataset.skin;""",
u"""  function skinDe(mini){
    if(mini.classList.contains('aurore')) return null;   // patch203 : l'Aurore garde son apparence
    if(mini.dataset.skin) return mini.dataset.skin;""")

# la fiche d'une carte Aurore : pas de choix de skin, une phrase à la place
rempl(u"""  if(!el.isConnected || !liste.length) return;   // aucun skin : rien à choisir
  el.hidden = false;
  const mini = boite.querySelector('.c3d .mini');""",
u"""  if(!el.isConnected || !liste.length) return;   // aucun skin : rien à choisir
  el.hidden = false;
  const mini = boite.querySelector('.c3d .mini');
  if(mini && mini.classList.contains('aurore')){   // patch203
    el.querySelector('.sk-rangee').innerHTML = '<p class="dc-aide">Une carte Aurore garde son apparence Aurore : elle ne prend pas de skin.</p>';
    el.querySelector('.sk-etat').textContent = '';
    return;
  }""")

# « Choisir les cartes » des skins : sans les cartes Aurore
rempl(u"""    .filter(c => !c.perdue)
    .sort((a, b) => rangTier(a.tier) - rangTier(b.tier) || a.nom.localeCompare(b.nom, 'fr'));
  const fermer = ouvrirFenetre(`
    <div class="fenetre vt-choix dc-fenetre sk-fenetre\"""",
u"""    .filter(c => !c.perdue && !(s === 'front' ? (AURORE && AURORE[c.code]) : c.aurore > 0))   // patch203 : pas d'Aurore
    .sort((a, b) => rangTier(a.tier) - rangTier(b.tier) || a.nom.localeCompare(b.nom, 'fr'));
  const fermer = ouvrirFenetre(`
    <div class="fenetre vt-choix dc-fenetre sk-fenetre\"""")

# 2. le choix de la vitrine montre mes skins
i = js.index('async function ouvrirChoixVitrine(')
j = js.index('\n}\n', i)
corps = js[i:j]
assert corps.count('${miniVitrine(c)}') == 2
corps = corps.replace('${miniVitrine(c)}', "${miniVitrine({ ...c, skin: skinDeMaCarte(front ? 'front' : 'terra', c.code) })}")
js = js[:i] + corps + js[j:]

# ma vitrine du profil se recharge après un changement de skin ou de dos
rempl(u"""    if(val) mesSkinsCartes.set(source + '|' + code, { skin: val, nom: '' }); else mesSkinsCartes.delete(source + '|' + code);""",
u"""    if(val) mesSkinsCartes.set(source + '|' + code, { skin: val, nom: '' }); else mesSkinsCartes.delete(source + '|' + code);
    rafraichirPanneauProfil();   // patch203 : ma vitrine suit""")
rempl(u"""    else mesDosCartes.delete(source + '|' + code);
    el._dessiner();""",
u"""    else mesDosCartes.delete(source + '|' + code);
    rafraichirPanneauProfil();   // patch203
    el._dessiner();""")
rempl(u"""    mesSkinsCartes.delete(r.dataset.grSkRetirer);
    skinGl.rafraichir();""",
u"""    mesSkinsCartes.delete(r.dataset.grSkRetirer);
    rafraichirPanneauProfil();   // patch203
    skinGl.rafraichir();""")
rempl(u"""    await chargerMesSkinsCartes(true);
    renderGardeRobe();
    notifier({ type: 'succes', titre: 'Skin posé',""",
u"""    await chargerMesSkinsCartes(true);
    rafraichirPanneauProfil();   // patch203
    renderGardeRobe();
    notifier({ type: 'succes', titre: 'Skin posé',""")
ecrire('app.js', js)
print(u'patch203 applique. Lancer : python3 maj-version.py')
