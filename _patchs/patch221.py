# -*- coding: utf-8 -*-
u"""
patch221 — les règles du jeu à jour (saison 2), demandé par Nataël le 27/10.

Chaque chiffre vérifié dans le code ou le SQL avant d'être écrit.
- Sommaire + 3 sections neuves : Collections et vitrine, Clans et amis, Outre-mer.
- Terra : outre-mer dans le pot (≈ 1 carte sur 270), Ma France France|Outre-mer,
  Boutique en points (garanti, département, collection ; 3 par jour), Aurore.
- Bourse/échange : Mes alertes (10 communes), cartes payées en points non
  échangeables, contrat = métropole.
- Front : épiques et outre-mer dans les paquets, récolte des légendaires,
  le calcul du classement (cartes, victoires, départements, régions), astuce
  de recherche.
- Quêtes : la réserve (5 sur 11, 20 pts, +50), quêtes Front à jour (35/jour),
  récompenses à réclamer avant minuit, Rafale et Plus ou moins.
- Saison : les 5 communes gardées, le versement en Terra (> 45 %).
Rien d'autre que du texte (index.html).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a); assert c == n, ('MATCH', a[:70], 'trouve', c, 'attendu', n); return s.replace(a, b)

CHEVRON = '<svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 9l6 6 6-6"/></svg>'
def section(id_, icone, titre, sous, corps):
    return (u'        <details class="regle" id="%s">\n          <summary>\n'
            u'            <span class="regle-icone"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">%s</svg></span>\n'
            u'            <h2>%s<small>%s</small></h2>\n            %s\n          </summary>\n'
            u'          <div class="regle-corps">\n%s          </div>\n        </details>\n') % (id_, icone, titre, sous, CHEVRON, corps)
def p(*lignes): return ''.join(u'            <p>%s</p>\n' % l for l in lignes)

h = lire('index.html')
assert 'id="s2-outremer"' not in h

# --- intro et sommaire ------------------------------------------------------
h = rep(h, u"""<h3>Accomplis</h3><p>Quêtes du jour, Commune du jour et Radar rapportent des points Terra et de l'énergie.</p>""",
           u"""<h3>Accomplis</h3><p>Les quêtes du jour et les mini-jeux du QG rapportent des points Terra et de l'énergie.</p>""")
h = rep(h, u"""          <a href="#s2-terra">Terra</a>
          <a href="#s2-echanges">Bourse, échange, contrat</a>
          <a href="#s2-front">Front</a>
          <a href="#s2-defense">Défense et garnison</a>
""", u"""          <a href="#s2-terra">Terra</a>
          <a href="#s2-collections">Collections et vitrine</a>
          <a href="#s2-echanges">Bourse, échange, contrat</a>
          <a href="#s2-front">Front</a>
          <a href="#s2-defense">Défense et garnison</a>
          <a href="#s2-clans">Clans et amis</a>
          <a href="#s2-outremer">Outre-mer</a>
""")

# --- Terra -------------------------------------------------------------------
h = rep(h, u"""            <p>Toutes les communes de France ont <b>la même chance</b> de sortir : environ une carte sur deux est commune, une sur cent est légendaire. Une carte que tu as déjà devient un <b>doublon</b>.</p>
            <p>Ta collection se regarde en cartes ou sur <b>Ma France</b>, une carte zoomable où tes communes apparaissent avec leur rareté.</p>
            <p>Tu gardes toujours <b>au moins un exemplaire</b> de chaque commune : seuls les doublons se vendent, s'échangent ou partent en contrat.</p>
""", p(u"""Toutes les communes ont <b>la même chance</b> de sortir : environ une carte sur deux est commune, une sur cent est légendaire. Les 129 communes d'<b>outre-mer</b> sont dans le même pot : environ une carte sur 270. Une carte que tu as déjà devient un <b>doublon</b>.""",
       u"""Ta collection se regarde en cartes ou sur <b>Ma France</b>, une carte zoomable où tes communes apparaissent avec leur rareté. Le bouton <b>France | Outre-mer</b> passe aux 5 territoires d'outre-mer.""",
       u"""Tu gardes toujours <b>au moins un exemplaire</b> de chaque commune : seuls les doublons se vendent, s'échangent ou partent en contrat.""",
       u"""<b>Boutique</b> (en points Terra) : le paquet <b>garanti</b> (4 communes au hasard + 1 rare, épique ou légendaire), le paquet d'un <b>département</b> (5 communes différentes du département choisi) et les paquets de <b>collection</b>. 3 paquets de Boutique par jour au plus ; ils ne comptent pas pour les quêtes.""",
       u"""<b>Aurore</b> : 233 communes existent aussi en version Aurore. Quand l'une d'elles sort d'un paquet, elle a <b>1 chance sur 3</b> d'être une Aurore. Un exemplaire Aurore reste toujours dans ta collection : il ne se vend pas et ne s'échange pas."""))

# --- Collections et vitrine (nouvelle, après Terra) ---------------------------
h = rep(h, u"""        <details class="regle" id="s2-echanges">""",
  section('s2-collections', '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/>',
    u'Collections et vitrine', u'Albums, monuments, vitrine',
    p(u"""<b>Collections</b> : des albums thématiques (fromages, eaux minérales, vins, préfectures, plus beaux villages…). Complète-en un pour <b>réclamer sa récompense</b>, une seule fois : des points Terra et un dos de carte exclusif. Toutes tes cartes comptent, d'où qu'elles viennent. Chaque collection a son paquet en Boutique : 5 communes de la collection que tu n'as <b>pas encore</b>.""",
      u"""<b>Monuments</b> : l'album des monuments de France. Un monument est trouvé dès que sa commune est dans ta collection Terra.""",
      u"""<b>Vitrine</b> : jusqu'à <b>20 cartes</b> à montrer sur ton profil, une vitrine Terra et une vitrine Front. Touche une carte puis une autre pour échanger leurs places ; une place vide envoie la carte au bout.""")) + u"""        <details class="regle" id="s2-echanges">""")

# --- Bourse, échange, contrat --------------------------------------------------
h = rep(h, u"""La commune reçue est une commune que tu n'as <b>pas encore</b>.</p>
""", u"""La commune reçue est une commune de métropole que tu n'as <b>pas encore</b>.</p>
""" + p(u"""<b>Mes alertes</b> (dans Échange) : note jusqu'à <b>10 communes</b> que tu cherches. Tu vois qui les a en doublon, quels joueurs cherchent tes propres doublons, et les communes les plus recherchées. Une commune obtenue sort toute seule de ta liste.""",
        u"""Les cartes payées en points (paquet acheté, Boutique) <b>ne s'échangent pas</b> et ne vont pas à la Bourse : elles se revendent au jeu ou partent en contrat, en premier."""))

# --- Front ----------------------------------------------------------------------
h = rep(h, u"""            <p>En Front, les paquets sont <b>gratuits uniquement</b> (1 toutes les 20 min, 3 en réserve) et rien ne s'achète.</p>
""", p(u"""En Front, les paquets sont <b>gratuits uniquement</b> (1 toutes les 20 min, 3 en réserve) et rien ne s'achète. Toutes les raretés peuvent en sortir, <b>épiques</b> comprises, et parfois une commune d'<b>outre-mer</b> encore libre."""))
h = rep(h, u"""et reprendre plusieurs fois la même commune au même joueur rapporte de moins en moins.</p>
          </div>
        </details>
        <details class="regle" id="s2-defense">""",
u"""et reprendre plusieurs fois la même commune au même joueur rapporte de moins en moins.</p>
""" + p(u"""<b>Légendaires</b> : chaque légendaire que tu tiens depuis au moins 24 h rapporte <b>+2 énergie</b> par jour (10 au plus), à récolter à la main dans Combat. Ce qui n'est pas récolté dans la journée est perdu. L'énergie récoltée peut dépasser 40, jusqu'à 60.""",
        u"""<b>Le classement du Front</b> additionne tes cartes, tes victoires et tes territoires :""") +
u"""            <div class="tableau-defile">
              <table class="tableau">
                <thead><tr><th>Ce qui compte</th><th>Points</th></tr></thead>
                <tbody>
                  <tr><td>Chaque commune tenue</td><td class="chiffre or">1 · 3 · 12 · 25 · 60</td></tr>
                  <tr><td>Victoire (conquête, défense, garnison qui repousse), 10 par jour, 2 par jour contre un même joueur</td><td class="chiffre or">+10</td></tr>
                  <tr><td>Département dominé (le plus de communes, seul, et au moins 10 %)</td><td class="chiffre or">+100</td></tr>
                  <tr><td>Département contrôlé (au moins 50 %), à la place de dominé</td><td class="chiffre or">+300</td></tr>
                  <tr><td>Région : plus de la moitié de ses départements dominés ou contrôlés</td><td class="chiffre or">+600</td></tr>
                </tbody>
              </table>
            </div>
""" + p(u"""Points des communes, de commune à légendaire. Une victoire ne compte qu'une fois par commune et par type, et reste acquise même si tu reperds la commune.""",
        u"""Astuce : dans Combat comme dans Échange, sépare tes critères par une virgule. « Arkhannou, 63 » montre les communes d'Arkhannou dans le Puy-de-Dôme.""") +
u"""          </div>
        </details>
        <details class="regle" id="s2-defense">""")

# --- Clans et amis + Outre-mer (nouvelles, après Défense) ----------------------
h = rep(h, u"""        <details class="regle" id="s2-quetes">""",
  section('s2-clans', '<circle cx="9" cy="8" r="3"/><path d="M3.5 19c.8-3 3-4.5 5.5-4.5s4.7 1.5 5.5 4.5"/><circle cx="17" cy="9" r="2.3"/><path d="M15.5 14.6c2.4.2 4.2 1.6 4.9 4.4"/>',
    u'Clans et amis', u'Jouer à plusieurs',
    p(u"""<b>Clan</b> : jusqu'à <b>6 joueurs</b>. Le chef invite par pseudo, le joueur accepte. Entre membres d'un même clan, <b>pas d'attaque</b>.""",
      u"""<b>Échanges de clan</b> (Front) : une commune contre une commune de <b>même rareté</b>, entre membres du clan depuis au moins 48 h. 2 échanges par jour au plus ; pas une commune prise il y a moins de 24 h, en garnison ou échangée il y a moins de 48 h. Une proposition attend 24 h.""",
      u"""Sur la carte, le calque <b>Clans</b> entoure le territoire de chaque clan de sa couleur. Le classement des clans fait la <b>moyenne</b> de leurs membres actifs (jeu ouvert dans les 7 derniers jours) ; il faut 3 membres pour être classé. Après avoir quitté un clan, il faut attendre 48 h pour en rejoindre un autre.""",
      u"""<b>Inviter des amis</b> (Profil) : ton lien d'invitation donne à ton ami <b>1 paquet Terra</b> et <b>10 énergie</b> dès son arrivée. Quand il a joué 3 jours, tu reçois <b>10 énergie</b> (5 amis par saison au plus), et des badges ; à 5 amis, le titre « Le Parrain ».""")) +
  section('s2-outremer', '<path d="M3 18c3-1.5 6-1.5 9 0s6 1.5 9 0"/><path d="M12 16V8"/><path d="M12 8c-2-2-5-2-7 0M12 8c2-2 5-2 7 0M12 8c-1-2.5-3.5-3.5-6-3M12 8c1-2.5 3.5-3.5 6-3"/>',
    u'Outre-mer', u'Guadeloupe, Martinique, Guyane, La Réunion, Mayotte',
    p(u"""Les <b>129 communes</b> de ces 5 départements forment un <b>set à part</b>, avec leurs propres raretés : 5 légendaires (une par territoire), 6 épiques, 15 rares, 40 peu communes et 63 communes. Leur numéro, par exemple <b>n° 3 / 129</b>, est leur rang parmi elles, de la plus peuplée à la moins peuplée. On les reconnaît à leur carte « lagon » et au badge <b>★ Outre-mer</b>.""",
      u"""<b>Terra</b> : elles sont dans le même pot que la métropole (environ une carte sur 270) et comptent dans ta collection et tes défis de collection. Ma France a son bouton <b>Outre-mer</b>. Les contrats et la quête « Complète un département » restent en métropole.""",
      u"""<b>Front</b> : chaque carte d'un paquet Front a une petite chance d'être une commune d'outre-mer encore libre. Elles s'attaquent et se défendent comme les autres, et tenir des communes voisines aide aussi. Elles rapportent les points de leur rareté au classement, mais <b>aucun bonus de département ni de région</b>. La carte du Front a son bouton <b>Outre-mer</b>.""")) +
  u"""        <details class="regle" id="s2-quetes">""")

# --- Quêtes et mini-jeux -------------------------------------------------------
h = rep(h, u"""            <p><b>Quêtes Terra</b> (points) : ouvrir 2 paquets Terra (30), ajouter 3 nouvelles communes (40), vendre ou échanger un doublon (30). Et des défis permanents : 100, 500, 2 000 communes, un département complet, une première épique.</p>
            <p><b>Quêtes Front</b> (énergie) : réussir une défense, mettre une garnison, ouvrir un paquet Terra, trouver la Commune du jour, gagner un duel Radar (+5 chacune), conquérir une commune (50 pts et +3). Au plus <b>20 énergie de quêtes par jour</b> ; elle peut faire dépasser les 40, jusqu'à 60.</p>
            <p><b>Commune du jour</b> : 50 pts trouvée en un essai, puis 40, 30, 20, 15 et 10. <b>Radar</b> : 20 pts par victoire en duel classé, 5 victoires payées par jour.</p>
""", p(u"""<b>Quêtes Terra</b> (points) : chaque jour, <b>5 quêtes</b> tirées dans une réserve de 11, les mêmes pour tout le monde : <b>20 pts</b> chacune, et <b>+50</b> quand les 5 sont faites. Et des défis permanents : 100, 500 et 2 000 communes (200, 400 et 600 pts), un département complet (300), une première épique (200).""",
       u"""<b>Quêtes Front</b> (énergie, +5 chacune) : réussir une défense, mettre une garnison, ouvrir un paquet Terra, trouver la Commune du jour, jouer à Plus ou moins, gagner un duel Radar, gagner un duel Rafale, conquérir 3 communes, conquérir dans 2 départements, garder une commune prise la veille. Conquérir une commune : 50 pts et +3. Au plus <b>35 énergie de quêtes par jour</b> ; elle peut faire dépasser les 40, jusqu'à 60.""",
       u"""<b>Réclame tes récompenses</b> à la main, avant <b>minuit</b> (heure de Paris) : une quête du jour non réclamée est perdue.""",
       u"""Mini-jeux du <b>QG</b>. <b>Commune du jour</b> : 50 pts trouvée en un essai, puis 40, 30, 20, 15 et 10. <b>Radar</b> et <b>Rafale</b> (une lettre, 30 secondes, le plus de communes possible) : 20 pts par victoire en duel classé, 5 victoires payées par jour pour chacun. <b>Plus ou moins</b> (laquelle a le plus d'habitants ?) : le jeu du jour, 10 duels à 5 pts la bonne réponse, et des duels classés à 20 pts la victoire, 5 par jour."""))

# --- La saison -----------------------------------------------------------------
h = rep(h, u"""            <p>À la fin, le classement du Front est figé dans le <b>Palmarès</b> (onglet Communauté), puis les communes du Front retournent au pot pour la saison suivante.</p>
            <p>Ta <b>collection Terra</b>, elle, ne se remet jamais à zéro.</p>
""", p(u"""Marque d'une <b>★</b> les <b>5 communes</b> que tu veux garder : elles restent à toi la saison suivante. Si tu en marques moins, le jeu complète avec tes communes les plus rares (une seule légendaire).""",
       u"""À la fin, le classement du Front est figé dans le <b>Palmarès</b> (onglet Communauté), puis les autres communes du Front retournent au pot pour la saison suivante.""",
       u"""Ta <b>collection Terra</b>, elle, ne se remet jamais à zéro. Elle reçoit en plus tes 5 communes gardées, et toutes tes communes d'un département que tu tiens à <b>plus de 45 %</b>."""))

ecrire('index.html', h)
print('patch221 OK')
