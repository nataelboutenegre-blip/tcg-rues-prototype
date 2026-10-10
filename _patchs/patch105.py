# -*- coding: utf-8 -*-
u"""
patch105 — saison 2 : le guide en bulles et la page d'accueil
(CACHÉS tant que SAISON2 = false). Aucun SQL.

Guide : 6 bulles (les deux modes, paquets Terra, collection, le Front et son
énergie, attaque et garnison, chaque jour). Le guide bascule tout seul de
mode quand une bulle parle de l'autre. Il se lance une fois pour TOUS les
joueurs au premier passage en saison 2 (clé terrafront-guide-s2-vu), pas
seulement pour les nouveaux.

Page d'accueil : accroche, chiffres, « Comment ça marche » en 4 étapes
(Collectionne, Conquiers, Défends, Joue chaque jour) et les 5 raretés.
La version saison 1 reste affichée tant que SAISON2 = false.
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

# ---------- page d'accueil ----------------------------------------------------
html = lire('index.html')
assert 's2-seul' not in html, u'patch105 deja applique'

html = rempl(html, u"""        <h1 class="lp-h1">Ta ville n'appartient qu'à <em>une seule personne</em>.</h1>
        <p class="lp-accroche">TerraFront est un jeu de collection sur la carte de France. Chaque commune du pays est une carte unique — et une seule personne peut la posséder à la fois.</p>
        <p class="lp-precis">Ouvre des paquets, colore ton territoire, prends celles des autres. Gratuit, dans le navigateur, sans rien installer.</p>""",
u"""        <h1 class="lp-h1 s1-seul">Ta ville n'appartient qu'à <em>une seule personne</em>.</h1>
        <p class="lp-accroche s1-seul">TerraFront est un jeu de collection sur la carte de France. Chaque commune du pays est une carte unique — et une seule personne peut la posséder à la fois.</p>
        <p class="lp-precis s1-seul">Ouvre des paquets, colore ton territoire, prends celles des autres. Gratuit, dans le navigateur, sans rien installer.</p>
        <h1 class="lp-h1 s2-seul">Collectionne la France. <em>Conquiers-la.</em></h1>
        <p class="lp-accroche s2-seul">Les 35 000 communes du pays sont des cartes. Complète ta propre France en <b>Terra</b>, et dispute la carte aux autres joueurs en <b>Front</b>, où chaque commune n'a qu'un seul propriétaire.</p>
        <p class="lp-precis s2-seul">Ouvre des paquets, échange tes doublons, prends les villes des autres. Gratuit, dans le navigateur, sans rien installer.</p>""", 'hero')

html = rempl(html, u"""        <div class="lp-chiffres">
          <div class="lp-chiffre"><b>35 000</b><small>COMMUNES</small></div>""", u"""        <div class="lp-chiffres s2-seul">
          <div class="lp-chiffre"><b>35 000</b><small>COMMUNES</small></div>
          <div class="lp-chiffre"><b>2</b><small>MODES DE JEU</small></div>
          <div class="lp-chiffre"><b>4</b><small>SEMAINES PAR SAISON</small></div>
        </div>
        <div class="lp-chiffres s1-seul">
          <div class="lp-chiffre"><b>35 000</b><small>COMMUNES</small></div>""", 'chiffres')

html = rempl(html, u"""      <h2 class="lp-h2">Comment ça marche</h2>
      <p class="lp-sous">Trois gestes, et c'est tout le jeu.</p>
      <div class="lp-etapes">""", u"""      <h2 class="lp-h2">Comment ça marche</h2>
      <p class="lp-sous s2-seul">Deux modes, un seul compte.</p>
      <div class="lp-etapes lp-etapes-4 s2-seul">
        <div class="lp-etape">
          <span class="lp-num">1</span>
          <b>Collectionne</b>
          <p>En Terra, un paquet gratuit toutes les 20 minutes complète ta propre France. Tes doublons s'échangent, se revendent ou partent en contrat.</p>
        </div>
        <div class="lp-etape">
          <span class="lp-num">2</span>
          <b>Conquiers</b>
          <p>En Front, chaque commune n'a qu'un propriétaire. Attaque avec ton énergie : trois victoires d'affilée et elle est à toi.</p>
        </div>
        <div class="lp-etape">
          <span class="lp-num">3</span>
          <b>Défends</b>
          <p>Mets tes communes clés en garnison : elles se défendent toutes seules pendant que tu n'es pas là.</p>
        </div>
        <div class="lp-etape">
          <span class="lp-num">4</span>
          <b>Joue chaque jour</b>
          <p>Quêtes, Commune du jour et duels Radar rapportent des points et de l'énergie.</p>
        </div>
      </div>
      <p class="lp-sous s1-seul">Trois gestes, et c'est tout le jeu.</p>
      <div class="lp-etapes s1-seul">""", 'etapes')

html = rempl(html, u"""      <div class="lp-rares">
        <div class="lp-rar" style="--c:#7E8BA0">""", u"""      <div class="lp-rares lp-rares-5 s2-seul">
        <div class="lp-rar" style="--c:#7E8BA0">
          <span class="lp-rar-pastille"></span><b>Commune</b>
          <small>moins de 450 hab.</small>
          <p>Les villages. La moitié de la carte.</p>
        </div>
        <div class="lp-rar" style="--c:#22A06B">
          <span class="lp-rar-pastille"></span><b>Peu commune</b>
          <small>à partir de 450</small>
          <p>Les bourgs. La matière de ton territoire.</p>
        </div>
        <div class="lp-rar" style="--c:#2F7CF6">
          <span class="lp-rar-pastille"></span><b>Rare</b>
          <small>à partir de 2 300</small>
          <p>Les petites villes, 3 406 dans tout le pays.</p>
        </div>
        <div class="lp-rar" style="--c:#9B5CF6">
          <span class="lp-rar-pastille"></span><b>Épique</b>
          <small>à partir de 8 000</small>
          <p>Les villes moyennes, 1 015 en tout.</p>
        </div>
        <div class="lp-rar" style="--c:#F0B429">
          <span class="lp-rar-pastille"></span><b>Légendaire</b>
          <small>à partir de 30 000</small>
          <p>Les grandes villes : 302 dans toute la France.</p>
        </div>
      </div>
      <div class="lp-rares s1-seul">
        <div class="lp-rar" style="--c:#7E8BA0">""", 'raretes')
ecrire('index.html', html)

# ---------- guide en bulles ---------------------------------------------------
js = lire('app.js')
js = rempl(js, u"""const CLE_GUIDE = 'terrafront-guide-vu';""",
           u"""// patch105 : la saison 2 a son propre guide, montre une fois a tous
const CLE_GUIDE = SAISON2 ? 'terrafront-guide-s2-vu' : 'terrafront-guide-vu';""", 'cle')
js = rempl(js, u"""let guideIndex = -1;
let guideCibleActuelle = null;""", u"""const ETAPES_GUIDE_S2 = [
  { cible: '#modeBascule', titre: 'Deux modes',
    texte: 'Terra, c\\'est ta collection à toi : ta propre France, à compléter. Front, c\\'est la carte partagée : chaque commune n\\'a qu\\'un propriétaire, et se prend au combat.' },
  { mode: 'terra', cible: '#packZone .paquet, #openFreeBtn', titre: 'Ouvre tes paquets Terra',
    texte: 'Un paquet gratuit toutes les 20 minutes, 3 en réserve, 5 communes à chaque fois. Celles que tu as déjà deviennent des doublons.' },
  { mode: 'terra', cible: '.tab[data-tab="collection"]', titre: 'Ta collection',
    texte: 'Ta France se remplit ici, en cartes ou sur la carte. Tes doublons se revendent, s\\'échangent avec les autres joueurs ou partent en contrat.' },
  { mode: 'front', cible: '#modeBascule [data-mode="front"]', titre: 'Le Front',
    texte: 'Ici, l\\'énergie remplace les points : 40 au maximum, +1 toutes les 10 minutes. Elle sert à attaquer et à défendre.' },
  { mode: 'front', cible: '.tab[data-tab="combat"]', titre: 'Attaque et défends',
    texte: 'Trois victoires d\\'affilée prennent une commune. Mets tes communes clés en garnison : elles se défendent seules pendant ton absence.' },
  { cible: '.tab[data-tab="qg"]', titre: 'Chaque jour',
    texte: 'Les quêtes, la Commune du jour et le Radar rapportent des points Terra et de l\\'énergie. Une saison du Front dure 4 semaines.' },
];
if(SAISON2) ETAPES_GUIDE.splice(0, ETAPES_GUIDE.length, ...ETAPES_GUIDE_S2);

let guideIndex = -1;
let guideCibleActuelle = null;""", 'etapes')
js = rempl(js, u"""  if(guideCibleActuelle) guideCibleActuelle.classList.remove('guide-cible');
  const cible = trouverCibleGuide(etape.cible);""", u"""  if(guideCibleActuelle) guideCibleActuelle.classList.remove('guide-cible');
  // saison 2 : la bulle parle d'un mode, on y passe
  if(etape.mode && SAISON2 && modeJeu !== etape.mode){
    const b = document.querySelector('#modeBascule [data-mode="' + etape.mode + '"]');
    if(b) b.click();
  }
  const cible = trouverCibleGuide(etape.cible);""", 'mode')
# lancement automatique pour les anciens joueurs au premier passage en saison 2
js = rempl(js, u"""function initModes(){
  // patch104 : les regles de la saison 2 remplacent celles de la saison 1
  document.body.classList.toggle('saison-2-regles', SAISON2);""", u"""function initModes(){
  // patch104 : les regles de la saison 2 remplacent celles de la saison 1
  document.body.classList.toggle('saison-2-regles', SAISON2);
  // patch105 : le guide de la saison 2, une fois, pour les joueurs deja la
  if(SAISON2 && accueilDejaVu() && !guideDejaVu() && !document.getElementById('modeBascule')){
    setTimeout(() => { if(guideIndex < 0) demarrerGuide(); }, 1500);
  }""", 'auto')
# la page d'accueil suit la saison des le chargement
js = rempl(js, u"""const SAISON2 = false;""", u"""const SAISON2 = false;
document.documentElement.classList.toggle('saison-2', SAISON2);""", 'html classe')
ecrire('app.js', js)

css = lire('style.css')
assert '.s2-seul' not in css
css += u"""
/* patch105 : accueil de la saison 2 */
.s2-seul{ display:none !important; }
html.saison-2 .s1-seul{ display:none !important; }
html.saison-2 .lp-hero .s2-seul{ display:block !important; }
html.saison-2 .lp-chiffres.s2-seul, html.saison-2 .lp-etapes.s2-seul, html.saison-2 .lp-rares.s2-seul{ display:grid !important; }
html.saison-2 .lp-chiffres.s2-seul{ display:flex !important; }
html.saison-2 .lp-sous.s2-seul{ display:block !important; }
.lp-etapes-4{ grid-template-columns:repeat(4,1fr); }
.lp-rares-5{ grid-template-columns:repeat(5,1fr); }
@media (max-width: 900px){ .lp-etapes-4{ grid-template-columns:1fr 1fr; } .lp-rares-5{ grid-template-columns:1fr 1fr; } }
@media (max-width: 560px){ .lp-etapes-4, .lp-rares-5{ grid-template-columns:1fr; } }
"""
ecrire('style.css', css)
print(u'patch105 applique')
