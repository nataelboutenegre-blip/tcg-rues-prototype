# patch418 (11/11/2026) : les règles de la saison 3 (le siège, la Suisse, la zone de départ, les petits cantons)
# Les textes sont dans index.html dès maintenant mais cachés : chacun apparaît tout seul quand sa nouveauté s'allume
#   data-s3="siege"  : body.siege-on (siege_actif(), patch405 ; ?siege=test)
#   data-s3="suisse" : body.suisse-on (SUISSE, patch330 ; ?suisse=test)
#   data-s3="zone"   : body.zone-on (zone_depart_etat().ouvert, patch348)
#   data-s2="des"    : les textes des dés (rounds, engagements, 2 défenses…), cachés quand le siège s'allume
# Aujourd'hui (tout éteint), la page est la même qu'avant, sauf une phrase : le calque Clans « Contour ou Plein » (patch413).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:80]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
H, A, C = 'index.html', 'app.js', 'style.css'
if 'data-s3="siege"' in open(H, encoding='utf-8').read(): sys.exit('déjà appliqué')

# ---------- l'essentiel ----------
rep(H, """<p>En Front, chaque commune n'a qu'un propriétaire. Attaque avec ton énergie, défends-toi à la main ou avec tes garnisons.</p><!-- patch340 -->""",
"""<p>En Front, chaque commune n'a qu'un propriétaire. <span data-s2="des">Attaque avec ton énergie, défends-toi à la main ou avec tes garnisons.</span><span data-s3="siege">Assiège-la avec ton énergie ; renforce tes communes ou pose une garnison pour tenir.</span></p><!-- patch340, patch418 -->""")

# ---------- le sommaire ----------
rep(H, """          <a href="#s2-front">Front</a>
          <a href="#s2-defense">Défense et garnison</a>""",
"""          <a href="#s2-front">Front</a>
          <a href="#s3-siege" data-s3="siege">Le siège</a>
          <a href="#s2-defense">Défense et garnison</a>""")
rep(H, """          <a href="#s2-outremer">Outre-mer</a>
          <a href="#s2-quetes">Quêtes et mini-jeux</a>""",
"""          <a href="#s2-outremer">Outre-mer</a>
          <a href="#s3-suisse" data-s3="suisse">Suisse</a>
          <a href="#s2-quetes">Quêtes et mini-jeux</a>""")

# ---------- Front : les dés cachés avec le siège ----------
rep(H, """<div class="chiffre-bloc"><b>3</b><span>victoires pour conquérir</span></div></div>""",
"""<div class="chiffre-bloc" data-s2="des"><b>3</b><span>victoires pour conquérir</span></div><div class="chiffre-bloc" data-s3="siege"><b>2</b><span>énergie pour poser un siège</span></div></div>""")
for debut in ("""            <p>Avant chaque assaut, choisis ton engagement""",
              """            <p><b>Bonus de débutant</b> : pendant tes 7 premiers jours""",
              """            <p><b>Série noire</b> : après 2 assauts perdus""",
              """            <p>Gagne <b>3 rounds</b> pour prendre la commune"""):
    rep(H, debut, debut.replace('<p>', '<p data-s2="des">', 1))
rep(H, """            <p data-s2="des">Gagne <b>3 rounds</b> pour prendre la commune""",
"""            <p data-s3="siege">Pour prendre une commune, tu l'<b>assièges</b> : tout est expliqué juste en dessous, dans <a href="#s3-siege" class="rg-lien">Le siège</a>.</p>
            <p data-s2="des">Gagne <b>3 rounds</b> pour prendre la commune""")

# la zone de départ, après les paquets du Front
rep(H, """Les chances de chaque case sont affichées sous la roue.</p><!-- patch343 -->""",
"""Les chances de chaque case sont affichées sous la roue.</p><!-- patch343 -->
            <p data-s3="zone"><b>Zone de départ</b> : une fois par saison, avant ton premier paquet du Front, choisis une des <b>13 régions</b> ou la <b>Suisse</b> : tes <b>3 premiers paquets</b> du Front (15 cartes) y tombent, puis le tirage reprend partout. Le choix est définitif. Les chances de rareté restent celles de toute la France. Une zone se ferme aux nouveaux venus quand les <b>trois quarts</b> de ses communes sont prises ; si elle se vide avant tes 3 paquets, le tirage reprend partout, sans perdre de carte.</p><!-- patch418 -->""")

# classement : les victoires
rep(H, """<tr><td>Victoire (conquête, défense, garnison qui repousse), 10 par jour, 2 par jour contre un même joueur</td>""",
"""<tr><td><span data-s2="des">Victoire (conquête, défense, garnison qui repousse)</span><span data-s3="siege">Victoire (conquête, défense réussie d'un siège)</span>, 10 par jour, 2 par jour contre un même joueur</td>""")
rep(H, """<p>Par département, seul le palier le plus haut compte (métropole).""",
"""<p>Par département, seul le palier le plus haut compte (métropole<span data-s3="suisse"> et cantons suisses</span>).""")

# bâtiments : Forteresse, bombe, rébellion
rep(H, """: <b>−15 %</b> aux chances des attaquants sur elle, et <b>+5 %</b> à tes attaques à moins de 20 km.""",
""": <span data-s2="des"><b>−15 %</b> aux chances des attaquants sur elle, et <b>+5 %</b> à tes attaques à moins de 20 km.</span><span data-s3="siege">sa résistance est <b>× 1,5</b> et tout siège contre elle est long ; tes sièges à moins de 20 km font <b>× 1,1</b> de dégâts.</span>""")
rep(H, """et pendant 24 h tout le monde y attaque à +15 %.""",
"""et pendant 24 h tout le monde y <span data-s2="des">attaque à +15 %</span><span data-s3="siege">fait +15 % de dégâts</span>.""")
rep(H, """<b>3 lingots par point</b>, de −1 % à <b>−15 %</b> de défense, pendant <b>24 h</b>, pour toi seul.""",
"""<b>3 lingots par point</b>, de −1 % à <b>−15 %</b> de <span data-s2="des">défense</span><span data-s3="siege">résistance</span>, pendant <b>24 h</b>, pour toi seul.""")

# ---------- Le siège (nouvelle section, après Front) ----------
rep(H, """        <details class="regle" id="s2-defense">""",
"""        <details class="regle" id="s3-siege" data-s3="siege">
          <summary>
            <span class="regle-icone"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h16"/><path d="M6 20V9l3-2 3 2 3-2 3 2v11"/><path d="M10 20v-4h4v4"/></svg></span>
            <h2>Le siège<small>Prendre une commune avec ton énergie</small></h2>
            <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 9l6 6 6-6"/></svg>
          </summary>
          <div class="regle-corps"><div class="chiffres"><div class="chiffre-bloc"><b>2</b><span>énergie pour poser un siège</span></div><div class="chiffre-bloc"><b>10</b><span>points de dégâts par énergie</span></div><div class="chiffre-bloc"><b>24 h</b><span>sans vague : le siège tombe</span></div></div>
            <p><b>Assiéger</b> : depuis la fiche d'une commune ou Combat › Attaquer, pose un siège (<b>2 énergie</b>), puis envoie des <b>vagues</b> : tu choisis l'énergie de chaque vague, 60 au plus. Chaque énergie fait <b>10 points de dégâts</b> (entre 8 et 12, au hasard). Quand ta jauge atteint la <b>résistance</b> de la commune, elle est à toi. Le propriétaire est prévenu dès que tu poses le siège.</p>
            <div class="tableau-defile">
              <table class="tableau">
                <thead><tr><th>Rareté</th><th>Résistance</th><th>Énergie, environ</th><th>Siège long : au moins</th></tr></thead>
                <tbody>
                  <tr><td><span class="rarete commun">Commune</span></td><td class="chiffre">55</td><td class="chiffre">8</td><td class="chiffre">1 h</td></tr>
                  <tr><td><span class="rarete peucommun">Peu commune</span></td><td class="chiffre">55</td><td class="chiffre">8</td><td class="chiffre">1 h 30</td></tr>
                  <tr><td><span class="rarete rare">Rare</span></td><td class="chiffre">65</td><td class="chiffre">9</td><td class="chiffre">2 h</td></tr>
                  <tr><td><span class="rarete epique">Épique</span></td><td class="chiffre">125</td><td class="chiffre">15</td><td class="chiffre">6 h</td></tr>
                  <tr><td><span class="rarete legendaire">Légendaire</span></td><td class="chiffre">250</td><td class="chiffre">27</td><td class="chiffre">15 h</td></tr>
                </tbody>
              </table>
            </div>
            <p><b>Éclair ou long</b> : tant que personne ne se défend, le siège est <b>éclair</b> : ta jauge monte aussi vite que tu envoies (une épique demande quand même <b>1 h</b>). Il devient <b>long</b>, et le reste, dès que le propriétaire renforce, ou si la commune a une garnison ou un bâtiment visible ; une légendaire est toujours un siège long. Un siège long ne peut pas aller plus vite que la durée du tableau (10 % tout de suite) : l'énergie en trop <b>attend</b> et part toute seule, au fil du temps.</p>
            <p><b>Places</b> : tu peux mener <b>8 sièges longs</b> à la fois, plus 1 par type de bâtiment prêt (12 au plus). Les sièges éclair sont illimités. Un siège éclair qui devient long continue, même sans place libre.</p>
            <p><b>Tes dégâts</b> : <b>× 0,8</b> sans commune à toi à moins de 20 km, <b>× 1,1</b> avec deux ou plus ; <b>× 1,1</b> avec une de tes Forteresses à moins de 20 km ; <b>× 1,15</b> dans la zone d'une bombe (24 h). <b>Bonus de débutant</b> : pendant tes 7 premiers jours, et jusqu'à ta première conquête, <b>× 1,5</b> (pas contre une épique, une légendaire ou une commune en garnison).</p>
            <p><b>La résistance</b> : <b>× 1,5</b> sur une Forteresse ; une rébellion que tu finances la baisse jusqu'à <b>−15 %</b> face à toi seul.</p>
            <p><b>Plusieurs assiégeants</b> : c'est une course, le premier qui remplit sa jauge prend la commune ; les autres récupèrent l'énergie qui attendait. Une commune prise est <b>protégée 3 h</b> contre les nouveaux sièges.</p>
            <p><b>Fin du siège</b> : sans vague de ta part pendant <b>24 h</b>, ton siège tombe. Tu peux aussi l'<b>abandonner</b> : l'énergie qui attendait t'est rendue. Une conquête rapporte <b>+10</b> au classement, comme une défense réussie.</p>
            <p>Sur la fiche d'un siège, « Comment c'est calculé ? » montre le détail des dégâts et de la résistance de la commune visée.</p>
          </div>
        </details><!-- patch418 -->
        <details class="regle" id="s2-defense">""")

# ---------- Défense : siège ----------
for debut in ("""            <p><b>Défendre</b> : quand un joueur gagne un round contre toi""",
              """            <p><b>Course à la commune</b> : quand un joueur prend une commune""",
              """            <p><b>Garnison</b> : jusqu'à <b>5 communes</b>, où tu déposes de l'énergie""",
              """            <p>Retirer une garnison rend les trois quarts de son énergie."""):
    rep(H, debut, debut.replace('<p>', '<p data-s2="des">', 1))
rep(H, """            <p data-s2="des"><b>Défendre</b> : quand un joueur gagne un round contre toi""",
"""            <p data-s3="siege"><b>Renforcer</b> : quand une de tes communes est assiégée, la cloche te prévient et Défendre la montre avec la jauge de l'attaquant. Chaque énergie que tu mets fait <b>reculer</b> sa jauge de 10 points, <b>+20 %</b> parce que tu es chez toi (12 en moyenne). Renforcer rend le siège long : il ne peut plus aller plus vite que sa durée minimale. Tu peux aussi <b>laisser filer</b> une commune qui ne t'intéresse pas.</p>
            <p data-s3="siege"><b>Défense réussie</b> : quand le siège finit sans conquête (24 h sans vague ou abandon) et que tu as renforcé, ou que ta garnison a encaissé : <b>+10</b> au classement, <b>10 TP</b>, et elle compte pour la quête de défense du jour.</p>
            <p data-s3="siege"><b>Garnison</b> : jusqu'à <b>5 communes</b>, où tu déposes de l'énergie (10 au plus par commune). Elle devient un <b>bouclier</b> de <b>10 points par énergie</b> (100 au plus), que l'attaquant doit briser avant de faire monter sa jauge, et elle rend tout siège long. L'énergie entamée est perdue ; retirer une garnison rend les trois quarts de ce qui reste. Une bombe détruit les garnisons de sa zone. L'attaquant voit qu'une commune est en garnison, pas combien elle contient.</p>
            <p data-s2="des"><b>Défendre</b> : quand un joueur gagne un round contre toi""")

# ---------- Clans : calque Plein (déjà en ligne, patch413) ----------
rep(H, """<p>Sur la carte, le calque <b>Clans</b> entoure le territoire de chaque clan de sa couleur.""",
"""<p>Sur la carte, le calque <b>Clans</b> entoure le territoire de chaque clan de sa couleur, ou le remplit (<b>Contour</b> ou <b>Plein</b>, sous « Couleurs »).""")

# ---------- La Suisse (nouvelle section, après Outre-mer) ----------
rep(H, """        <details class="regle" id="s2-quetes">""",
"""        <details class="regle" id="s3-suisse" data-s3="suisse">
          <summary>
            <span class="regle-icone"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M12 8v8M8 12h8"/></svg></span>
            <h2>Suisse<small>26 cantons, 2 110 communes</small></h2>
            <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 9l6 6 6-6"/></svg>
          </summary>
          <div class="regle-corps">
            <p>Les <b>2 110 communes</b> de Suisse rejoignent la carte. Leurs <b>26 cantons</b> (GE, VD, ZH…) jouent le rôle des départements, et forment ensemble la région <b>Suisse</b>. Mêmes seuils de population qu'en France pour la rareté ; leur numéro, par exemple <b>n° 1 / 27</b> pour Zurich, est leur rang parmi les communes suisses. Les grandes villes gardent leur nom français (Genève, Bâle, Zurich…), les autres leur nom officiel.</p>
            <p><b>Front</b> : elles sortent des paquets du Front et s'assiègent comme les autres. La frontière ne compte pas pour la proximité : une commune française à moins de 20 km d'une commune suisse compte comme voisine. Chaque canton rapporte les mêmes paliers qu'un département ; un canton de <b>moins de 20 communes</b> rapporte au prorata (Bâle-Ville, 3 communes : 1 400 × 3 / 20 = <b>210</b> s'il est entier). Région Suisse : seul en tête avec 10 % ou plus dans plus de la moitié des cantons (<b>14 sur 26</b>) : <b>+1 200</b>.</p>
            <p><b>Terra</b> : au Tirage, choisis <b>France</b> ou <b>Suisse</b> : mêmes jetons et même prix. Dans un paquet suisse, la rareté est tirée avec les chances d'un paquet France, puis une commune suisse de cette rareté. Ta collection a son choix France | Suisse ; Ma France reste française.</p>
            <p>Pas encore de Suisse dans les mini-jeux (Commune du jour, Radar, Rafale, Plus ou moins), dans les contrats, ni dans la quête « Complète un département ».</p>
          </div>
        </details><!-- patch418 -->
        <details class="regle" id="s2-quetes">""")

# ---------- les interrupteurs ----------
open(C, 'a', encoding='utf-8').write("""
/* patch418 : règles de la saison 3, chacune visible quand sa nouveauté s'allume */
#panel-regles [data-s3]{ display:none !important; }
body.siege-on #panel-regles [data-s3="siege"], body.suisse-on #panel-regles [data-s3="suisse"],
body.zone-on #panel-regles [data-s3="zone"]{ display:revert !important; }
body.siege-on #panel-regles [data-s2="des"]{ display:none !important; }
#panel-regles .rg-lien{ color:#FFB27A; font-weight:700; }
""")
rep(A, """    ZD = !error && data ? data : null;   // s3-6 pas lancé : rien""",
"""    ZD = !error && data ? data : null;   // s3-6 pas lancé : rien
    document.body.classList.toggle('zone-on', !!(ZD && ZD.ouvert));   // patch418 : la règle de la zone de départ""")
open(A, 'a', encoding='utf-8').write("""
// ---------- patch418 : la règle de la Suisse s'affiche avec la Suisse ; le lien « Le siège » ouvre sa section ----------
document.body.classList.toggle('suisse-on', !!SUISSE);
document.addEventListener('click', (e) => {
  const a = e.target.closest('#panel-regles .rg-lien');
  if(!a) return;
  const d = document.querySelector(a.getAttribute('href'));
  if(d && d.tagName === 'DETAILS') d.open = true;
});
""")
print('patch418 OK')
