# -*- coding: utf-8 -*-
u"""
patch148 — Rafale sur téléphone : le clavier reste ouvert entre deux communes
(signalé par Arkhannou le 22 octobre).

Il fallait retoucher le champ après chaque commune : le clavier se fermait.
Deux causes, aucune dans notre code : toucher le bouton OK lui donnait le
focus (le champ le perdait), et sur certains téléphones la touche Entrée
envoyait le formulaire puis refermait le clavier.
- Entrée est maintenant traitée directement dans le champ, sans passer par
  l'envoi du formulaire (sauf pendant une saisie en cours de composition,
  où le formulaire reste la voie de secours).
- Le bouton OK ne prend plus le focus quand on le touche.
- Après chaque envoi, le champ reprend le focus s'il l'a perdu.
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
assert 'rafaleSoumettre' not in js, u'patch148 deja applique'

js = rempl(js, u"""document.getElementById('rfForm').addEventListener('submit', (e) => {
  e.preventDefault();
  const champ = document.getElementById('rfChamp');
  const brut = champ.value.trim();
  champ.value = '';
  if(!brut || !rafalePartie || Date.now() > rafaleFin) return;
  rafaleFile.push(brut);
  rafaleEnvoyer();
});""", u"""// Sur telephone, le clavier doit rester ouvert d'une commune a l'autre (patch148) :
// Entree est traitee dans le champ (l'envoi du formulaire refermait le clavier sur
// certains telephones), OK ne prend pas le focus, et le champ le reprend apres l'envoi.
function rafaleSoumettre(){
  const champ = document.getElementById('rfChamp');
  const brut = champ.value.trim();
  champ.value = '';
  if(!champ.disabled && document.activeElement !== champ) champ.focus({ preventScroll: true });
  if(!brut || !rafalePartie || Date.now() > rafaleFin) return;
  rafaleFile.push(brut);
  rafaleEnvoyer();
}
document.getElementById('rfForm').addEventListener('submit', (e) => {
  e.preventDefault();
  rafaleSoumettre();
});
document.getElementById('rfChamp').addEventListener('keydown', (e) => {
  // pendant une composition (clavier Android qui souligne le mot), on laisse le formulaire faire
  if(e.key !== 'Enter' || e.isComposing || e.keyCode === 229) return;
  e.preventDefault();
  rafaleSoumettre();
});
['pointerdown', 'mousedown'].forEach(t => document.querySelector('#rfForm button[type="submit"]')
  .addEventListener(t, (e) => e.preventDefault()));""", 'rafale submit')

ecrire('app.js', js)
print(u'patch148 applique. Lancer : python3 maj-version.py')
