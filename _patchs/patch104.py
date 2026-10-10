# -*- coding: utf-8 -*-
u"""
patch104 — les Règles de la saison 2 (CACHÉES tant que SAISON2 = false).
Aucun SQL.

En saison 2, l'onglet Règles montre un bloc #reglesS2 (l'essentiel en 4
étapes, un sommaire, 8 sections) à la place des règles de la saison 1.
La carte des notifications et « Revoir le guide » restent en haut.
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

def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)

CHEVRON = u'<svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 9l6 6 6-6"/></svg>'
ICONES = {
  'modes':  u'<path d="M4 12h16M12 4v16"/><circle cx="12" cy="12" r="8.5"/>',
  'cartes': u'<rect x="5" y="3" width="14" height="18" rx="2.5"/><path d="M9 8h6M9 12h6"/>',
  'terra':  u'<rect x="4" y="3" width="16" height="18" rx="2.5"/><path d="M4 13l6-4v12"/>',
  'echanges': u'<path d="M7 7h11l-3-3M17 17H6l3 3"/>',
  'front':  u'<path d="M6.5 17.5L17 7M17 7h-4M17 7v4M17.5 17.5L7 7M7 7h4M7 7v4"/>',
  'defense': u'<path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/>',
  'quetes': u'<path d="M5 4h14v16l-7-4-7 4z"/>',
  'saison': u'<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3 2"/>',
}

def section(id_, icone, titre, sous_titre, corps, ouvert=False):
    return u'''
        <details class="regle" id="%s"%s>
          <summary>
            <span class="regle-icone"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">%s</svg></span>
            <h2>%s<small>%s</small></h2>
            %s
          </summary>
          <div class="regle-corps">%s
          </div>
        </details>''' % (id_, u' open' if ouvert else u'', ICONES[icone], titre, sous_titre, CHEVRON, corps)

def chiffres(*blocs):
    return u'<div class="chiffres">' + u''.join(u'<div class="chiffre-bloc"><b>%s</b><span>%s</span></div>' % b for b in blocs) + u'</div>'

S2 = u'''
      <div class="regles-s2" id="reglesS2">
        <section class="essentiel" aria-label="L'essentiel">
          <div class="etape"><div class="etape-num">1</div><h3>Deux modes</h3><p>En haut de l'écran : <b>Terra</b>, ta collection à toi, et <b>Front</b>, la conquête de la carte avec tous les joueurs.</p></div>
          <div class="etape"><div class="etape-num">2</div><h3>Collectionne</h3><p>En Terra, chaque paquet complète ta propre France. Les doublons se revendent, s'échangent ou partent en contrat.</p></div>
          <div class="etape"><div class="etape-num">3</div><h3>Conquiers</h3><p>En Front, chaque commune n'a qu'un propriétaire. Attaque avec ton énergie, défends avec tes garnisons.</p></div>
          <div class="etape"><div class="etape-num">4</div><h3>Accomplis</h3><p>Quêtes du jour, Commune du jour et Radar rapportent des points Terra et de l'énergie.</p></div>
        </section>

        <nav class="sommaire" aria-label="Sommaire">
          <a href="#s2-modes">Terra et Front</a>
          <a href="#s2-cartes">Raretés</a>
          <a href="#s2-terra">Terra</a>
          <a href="#s2-echanges">Bourse, échange, contrat</a>
          <a href="#s2-front">Front</a>
          <a href="#s2-defense">Défense et garnison</a>
          <a href="#s2-quetes">Quêtes et mini-jeux</a>
          <a href="#s2-saison">La saison</a>
        </nav>
''' + section('s2-modes', 'modes', u'Terra et Front', u'Deux façons de jouer, un seul compte', u'''
            <p><b>Terra</b> est ta collection personnelle : tu as ta propre copie de la France, et une commune peut être dans la collection de tous les joueurs à la fois. Elle ne se remet jamais à zéro.</p>
            <p><b>Front</b> est la carte partagée : chaque commune n'appartient qu'à <b>un seul joueur</b>, et se prend au combat. Le Front repart à chaque saison.</p>
            <p>Les deux sont liés : ce que tu gagnes en Front (conquêtes, défenses) rapporte des <b>points Terra</b>. L'inverse n'existe pas : Terra ne donne aucune force en Front.</p>''', True) + section('s2-cartes', 'cartes', u'Raretés', u'Cinq paliers, selon la population', u'''
            <div class="tableau-defile">
              <table class="tableau">
                <thead><tr><th>Rareté</th><th>Population</th><th>Communes</th><th>Revente d'un doublon</th></tr></thead>
                <tbody>
                  <tr><td><span class="rarete legendaire">Légendaire</span></td><td>30 000 et plus</td><td class="chiffre">302</td><td class="chiffre or">600 pts</td></tr>
                  <tr><td><span class="rarete epique">Épique</span></td><td>8 000 à 29 999</td><td class="chiffre">1 015</td><td class="chiffre or">300 pts</td></tr>
                  <tr><td><span class="rarete rare">Rare</span></td><td>2 300 à 7 999</td><td class="chiffre">3 406</td><td class="chiffre or">100 pts</td></tr>
                  <tr><td><span class="rarete peucommun">Peu commun</span></td><td>450 à 2 299</td><td class="chiffre">12 841</td><td class="chiffre or">20 pts</td></tr>
                  <tr><td><span class="rarete commun">Commun</span></td><td>Moins de 450</td><td class="chiffre">17 183</td><td class="chiffre or">5 pts</td></tr>
                </tbody>
              </table>
            </div>
            <p>Le numéro d'une carte, par exemple <b>n° 9 / 302</b>, est son rang parmi les communes de sa rareté, de la plus peuplée à la moins peuplée.</p>''') + section('s2-terra', 'terra', u'Terra', u'Paquets, collection, doublons', chiffres((u'5', u'cartes par paquet'), (u'20 min', u'pour recharger un paquet gratuit (3 en réserve)'), (u'200 pts', u'le paquet acheté, 5 par jour')) + u'''
            <p>Toutes les communes de France ont <b>la même chance</b> de sortir : environ une carte sur deux est commune, une sur cent est légendaire. Une carte que tu as déjà devient un <b>doublon</b>.</p>
            <p>Ta collection se regarde en cartes ou sur <b>Ma France</b>, une carte zoomable où tes communes apparaissent avec leur rareté.</p>
            <p>Tu gardes toujours <b>au moins un exemplaire</b> de chaque commune : seuls les doublons se vendent, s'échangent ou partent en contrat.</p>''') + section('s2-echanges', 'echanges', u'Bourse, échange, contrat', u'Que faire de tes doublons', u'''
            <p><b>Vendre au jeu</b> : au prix de revente du tableau des raretés, tout de suite.</p>
            <p><b>Bourse</b> : mets un doublon en vente au prix que tu veux, au moins le prix de revente. Il quitte ta collection le temps de l'annonce ; « Retirer » le rend.</p>
            <p><b>Échange</b> : un de tes doublons contre un doublon d'un autre joueur, de la même rareté. Chacun paie une petite commission ; l'autre joueur a 48 h pour répondre.</p>
            <p><b>Contrat</b> : <b>10 doublons</b> communs donnent une commune peu commune, 10 doublons peu communs donnent une rare. La commune reçue est une commune que tu n'as <b>pas encore</b>.</p>''') + section('s2-front', 'front', u'Front', u'Énergie et combat', chiffres((u'40', u'énergie au maximum'), (u'10 min', u'pour recharger 1 énergie'), (u'3', u'victoires d\'affilée pour conquérir')) + u'''
            <p>Avant chaque assaut, choisis ton engagement : <b>prudent</b> (1 énergie, 35 %), <b>normal</b> (2 énergie, 50 %) ou <b>offensif</b> (3 énergie, 65 %). Avoir des communes autour de la cible augmente tes chances.</p>
            <p>Gagne <b>3 rounds d'affilée</b> pour prendre la commune ; une défaite remet ta série à zéro. Entre deux assauts sur la même commune : 2 min (commune), 5 min (peu commune), 10 min (rare), 1 h (épique), 3 h (légendaire). Une commune prise est protégée 3 h.</p>
            <p>En Front, les paquets sont <b>gratuits uniquement</b> (1 toutes les 20 min, 3 en réserve) et rien ne s'achète.</p>
            <div class="tableau-defile">
              <table class="tableau">
                <thead><tr><th>Conquête d'une…</th><th>Points Terra</th></tr></thead>
                <tbody>
                  <tr><td><span class="rarete commun">Commune</span></td><td class="chiffre or">+5</td></tr>
                  <tr><td><span class="rarete peucommun">Peu commune</span></td><td class="chiffre or">+10</td></tr>
                  <tr><td><span class="rarete rare">Rare</span></td><td class="chiffre or">+25</td></tr>
                  <tr><td><span class="rarete epique">Épique</span></td><td class="chiffre or">+50</td></tr>
                  <tr><td><span class="rarete legendaire">Légendaire</span></td><td class="chiffre or">+100</td></tr>
                </tbody>
              </table>
            </div>
            <p>Une défense réussie rapporte <b>+10</b>. Au plus <b>250 points Terra par jour</b> venant du Front. Reprendre une commune perdue depuis moins de 24 h ne rapporte rien, et reprendre plusieurs fois la même commune au même joueur rapporte de moins en moins.</p>''') + section('s2-defense', 'defense', u'Défense et garnison', u'Protéger ton territoire', u'''
            <p><b>Défendre</b> : quand un joueur gagne un round contre toi, tu peux tenter une défense pour <b>1 énergie</b>, une fois par attaque. Réussie, l'attaquant perd une victoire.</p>
            <p><b>Garnison</b> : jusqu'à <b>3 communes</b>, où tu déposes de l'énergie (10 au maximum par commune). Quand un attaquant gagne un round, la garnison tente seule une défense : <b>1 chance sur 2</b>, 1 énergie par tentative. Réussie, la victoire ne compte pas.</p>
            <p>Retirer une garnison rend la moitié de son énergie. Une défense que tu réussis toi-même sur une commune en garnison y remet <b>3 énergie</b>. L'attaquant voit qu'une commune est en garnison, pas combien elle contient.</p>
            <p>Dans Défendre, <b>Mes départements</b> fait passer en tête les communes attaquées des départements que tu choisis.</p>''') + section('s2-quetes', 'quetes', u'Quêtes et mini-jeux', u'Chaque jour', u'''
            <p><b>Quêtes Terra</b> (points) : ouvrir 2 paquets Terra (30), ajouter 3 nouvelles communes (40), vendre ou échanger un doublon (30). Et des défis permanents : 100, 500, 2 000 communes, un département complet, une première épique.</p>
            <p><b>Quêtes Front</b> (énergie) : réussir une défense, mettre une garnison, ouvrir un paquet Terra, trouver la Commune du jour, gagner un duel Radar (+5 chacune), conquérir une commune (50 pts et +3). Au plus <b>20 énergie de quêtes par jour</b> ; elle peut faire dépasser les 40, jusqu'à 60.</p>
            <p><b>Commune du jour</b> : 50 pts trouvée en un essai, puis 40, 30, 20, 15 et 10. <b>Radar</b> : 20 pts par victoire en duel classé, 5 victoires payées par jour.</p>''') + section('s2-saison', 'saison', u'La saison', u'Le Front repart toutes les 4 semaines', u'''
            <p>Une saison de Front dure <b>4 semaines</b>. Un compte à rebours s'affiche les 5 derniers jours.</p>
            <p>À la fin, le classement du Front est figé dans le <b>Palmarès</b> (onglet Communauté), puis les communes du Front retournent au pot pour la saison suivante.</p>
            <p>Ta <b>collection Terra</b>, elle, ne se remet jamais à zéro.</p>''') + u'''
      </div>
'''

html = lire('index.html')
assert 'id="reglesS2"' not in html, u'patch104 deja applique'
html = rempl(html, u"""        <button class="regles-guide" id="revoirGuide">Revoir le guide de démarrage</button>
""", u"""        <button class="regles-guide" id="revoirGuide">Revoir le guide de démarrage</button>
""" + S2, 'insertion')
ecrire('index.html', html)

js = lire('app.js')
assert 'saison-2-regles' not in js
js = rempl(js, u"""function initModes(){
  if(!SAISON2 || document.getElementById('modeBascule')) { appliquerMode(); return; }""", u"""function initModes(){
  // patch104 : les regles de la saison 2 remplacent celles de la saison 1
  document.body.classList.toggle('saison-2-regles', SAISON2);
  if(!SAISON2 || document.getElementById('modeBascule')) { appliquerMode(); return; }""", 'classe')
ecrire('app.js', js)

css = lire('style.css')
assert '.regles-s2' not in css
css += u"""
/* patch104 : regles de la saison 2 */
#panel-regles .regles-s2{ display:none; }
body.saison-2-regles #panel-regles .regles-s2{ display:block; }
body.saison-2-regles #panel-regles .regles > .essentiel,
body.saison-2-regles #panel-regles .regles > .sommaire,
body.saison-2-regles #panel-regles .regles > details.regle{ display:none; }
"""
ecrire('style.css', css)
print(u'patch104 applique')
