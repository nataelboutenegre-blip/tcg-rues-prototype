# -*- coding: utf-8 -*-
u"""
patch63 — La fenetre de mise en vente annonce le plancher.

POURQUOI
  bourse-plancher.sql refuse desormais un prix inferieur a ce que le jeu
  paie pour la carte (5 / 20 / 100 / 1 000). Sans ce patch, un joueur qui
  propose 500 pour une legendaire recoit l'exception PostgreSQL brute :
  « Prix minimum pour cette rarete : 1000 points. » Ca marche, mais ca se
  voit.

CE QUE LA FENETRE DISAIT
  « Ton prix » avec un champ vide, min="1", et dessous : « Le jeu te la
  rachete 1 000 pts si tu preferes vendre tout de suite. » Le chiffre du
  rachat etait deja affiche — il se trouve que c'est exactement le
  plancher. Il ne change donc pas de valeur, il change de role : il
  n'informe plus, il contraint.

CE QU'ELLE DIT MAINTENANT
  Le champ demarre sur le plancher au lieu d'etre vide, son min le reprend,
  et la phrase d'aide dit les deux choses d'un coup : c'est le minimum, et
  c'est aussi ce que le jeu paie. Un joueur qui veut juste s'en debarrasser
  valide sans rien taper.

  Le message d'erreur nomme le chiffre plutot que de dire « superieur a 0 »,
  qui etait vrai avant et ne l'est plus.
"""
import io, os

BASE = os.path.dirname(os.path.abspath(__file__))

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


js = lire('app.js')

js = rempl(js,
u"""function demanderPrix({ nom, rachat }){
  return new Promise((resolve) => {""",
u"""function demanderPrix({ nom, rachat }){
  // Le plancher de la Bourse, c'est le prix de rachat du jeu : en dessous,
  // vendre a un joueur n'avait aucun sens pour un vendeur de bonne foi, il
  // avait toujours mieux a faire en vendant au jeu. Voir bourse-plancher.sql.
  const plancher = Number(rachat) || 1;
  const plancherTxt = plancher.toLocaleString('fr-FR');
  return new Promise((resolve) => {""",
u'le plancher calcule dans la fenetre')

js = rempl(js,
u"""          <span class="prix-saisie"><input type="number" inputmode="numeric" min="1" step="1" id="prixValeur" required><em>pts</em></span>
        </label>
        <p class="prix-aide">Le jeu te la rachète ${Number(rachat).toLocaleString('fr-FR')} pts si tu préfères vendre tout de suite.</p>""",
u"""          <span class="prix-saisie"><input type="number" inputmode="numeric" min="${plancher}" step="1" id="prixValeur" value="${plancher}" required><em>pts</em></span>
        </label>
        <p class="prix-aide">Minimum ${plancherTxt} pts — c’est aussi ce que le jeu te la rachète si tu préfères vendre tout de suite.</p>""",
u'le champ demarre au plancher')

js = rempl(js,
u"""      const prix = parseInt(champ.value, 10);
      if(!prix || prix <= 0){
        document.getElementById('prixErreur').textContent = 'Indique un prix supérieur à 0.';
        champ.focus();
        return;
      }""",
u"""      const prix = parseInt(champ.value, 10);
      if(!prix || prix < plancher){
        document.getElementById('prixErreur').textContent =
          'Le prix minimum pour cette rareté est de ' + plancherTxt + ' pts.';
        champ.focus();
        return;
      }""",
u'le message d erreur nomme le plancher')

ecrire('app.js', js)
print(u'patch63 applique.')
