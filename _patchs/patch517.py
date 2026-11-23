# patch517 : QG › Guide — comment marche le siège, la défense, l'énergie (idée de Nataël, 23/11).
# Un 5e volet « Guide » à côté de Mon front / Attaquer / Défendre / Bâtiments. Texte fixe, chiffres de la saison 3
# au 23/11 (s3-58 : nuit, proximité graduée, rempart). Chaque bloc se replie.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

BAT = '<button type="button" class="volet" data-volet="batiments" role="tab" aria-selected="false">Bâtiments</button><!-- patch379 -->'
GUIDE_BTN = '\n        <button type="button" class="volet" data-volet="guide" role="tab" aria-selected="false">Guide</button><!-- patch517 -->'
rep('index.html', BAT, BAT + GUIDE_BTN, n=2)   # Attaquer et Défendre
rep('index.html', '<button type="button" class="volet actif" data-volet="batiments" role="tab" aria-selected="true">Bâtiments</button>',
    '<button type="button" class="volet actif" data-volet="batiments" role="tab" aria-selected="true">Bâtiments</button>' + GUIDE_BTN)
rep('index.html', '      <div class="tab onglet-fusionne" data-tab="batiments" aria-hidden="true"><!-- patch379 -->',
    '      <div class="tab onglet-fusionne" data-tab="guide" aria-hidden="true"></div><!-- patch517 -->\n      <div class="tab onglet-fusionne" data-tab="batiments" aria-hidden="true"><!-- patch379 -->')

GUIDE = '''
    <section class="tab-panel" id="panel-guide"><!-- patch517 : le guide du Front -->
      <h1>Combat</h1>
      <div class="volets" role="tablist" aria-label="Combat">
        <button type="button" class="volet" data-volet="monfront" role="tab" aria-selected="false">Mon front</button>
        <button type="button" class="volet" data-volet="combat" role="tab" aria-selected="false">Attaquer</button>
        <button type="button" class="volet" data-volet="defense" role="tab" aria-selected="false">Défendre<span class="volet-badge" data-badge-defense hidden></span></button>
        <button type="button" class="volet" data-volet="batiments" role="tab" aria-selected="false">Bâtiments</button>
        <button type="button" class="volet actif" data-volet="guide" role="tab" aria-selected="true">Guide</button>
      </div>
      <div class="sub">Tout le Front en 5 minutes. Les chiffres exacts d'une commune sont sur sa fiche de siège, sous « Comment c'est calculé ? ».</div>
      <div class="gd">
        <details class="gd-b" open>
          <summary><span class="gd-i">⚔️</span><span><b>Prendre une commune : le siège</b><small>Poser, envoyer des vagues, remplir la jauge</small></span></summary>
          <ol class="gd-etapes">
            <li><b>Pose ton siège.</b> Touche une commune sur la carte ou dans Attaquer, puis « Assiéger ». Poser coûte <b>2 ⚡</b>, en plus de ta première vague.</li>
            <li><b>Envoie des vagues d'énergie.</b> Chaque ⚡ fait environ <b>10 points de dégâts</b> (entre 8 et 12 au hasard), jusqu'à 60 ⚡ par vague.</li>
            <li><b>Remplis la jauge.</b> Quand les dégâts atteignent la <b>résistance</b> de la commune, elle est à toi.</li>
          </ol>
          <div class="gd-tab">
            <div><span>Commune, peu commune</span><b>55</b></div><div><span>Rare</span><b>65</b></div>
            <div><span>Épique</span><b>125</b></div><div><span>Légendaire</span><b>250</b></div>
          </div>
          <p class="gd-p">Résistance de base. Il faut donc environ <b>6 ⚡</b> pour une commune et <b>25 ⚡</b> pour une légendaire, plus les 2 ⚡ de la pose, avant les bonus et malus ci-dessous. Le chiffre « ≈ N ⚡ » de chaque cible en tient compte.</p>
        </details>
        <details class="gd-b">
          <summary><span class="gd-i">⏱️</span><span><b>Éclair ou long</b><small>Le temps qu'il faut au moins</small></span></summary>
          <p class="gd-p"><b>Éclair</b> : tant que personne ne défend, la commune peut tomber vite, mais pas avant un délai minimum : <b>5 min</b> (commune), <b>10 min</b> (peu commune), <b>20 min</b> (rare), <b>1 h</b> (épique).</p>
          <p class="gd-p"><b>Long</b> : dès que le propriétaire défend, ou s'il y a une garnison, un bâtiment visible, ou que c'est une légendaire, le siège devient long. La jauge ne peut alors avancer qu'à un certain rythme : au mieux <b>1 h</b> (commune), <b>1 h 30</b> (peu commune), <b>2 h</b> (rare), <b>6 h</b> (épique), <b>15 h</b> (légendaire). L'énergie en trop attend dans le siège et part toute seule toutes les 5 minutes. Tu as <b>8 places</b> de sièges longs.</p>
          <p class="gd-p">Un siège sans nouvelle vague pendant <b>24 h</b> s'arrête. Une commune qui vient d'être prise est protégée <b>3 h</b>.</p>
        </details>
        <details class="gd-b">
          <summary><span class="gd-i">📍</span><span><b>Ce qui change tes dégâts</b><small>Tes communes autour de la cible</small></span></summary>
          <div class="gd-tab">
            <div><span>Aucune commune à toi à 20 km</span><b class="gd-m">−20 %</b></div>
            <div><span>1 ou 2</span><b class="gd-m">−10 %</b></div>
            <div><span>3 à 5</span><b>normal</b></div>
            <div><span>6 ou plus</span><b class="gd-p2">+10 %</b></div>
          </div>
          <p class="gd-p">L'<b>Artillerie</b> évite le −20 % quand tu n'as rien autour. Une <b>bombe</b> sur la zone donne +15 %, une <b>Forteresse</b> à toi tout près +10 %. Attaquer depuis ton territoire coûte donc moins cher que de sauter loin.</p>
        </details>
        <details class="gd-b">
          <summary><span class="gd-i">🏰</span><span><b>Ce qui rend une commune plus dure</b><small>Forteresse, rempart, garnison</small></span></summary>
          <p class="gd-p"><b>Forteresse</b> sur la commune : résistance ×1,5.</p>
          <p class="gd-p"><b>Rempart</b> : une commune entourée par son propriétaire résiste mieux, <b>+5 %</b> par commune à lui à moins de 10 km au-delà de 3, jusqu'à <b>+50 %</b>. Le cœur d'un territoire est plus dur que sa frontière.</p>
          <p class="gd-p"><b>Garnison</b> : un bouclier d'énergie à percer avant que la jauge bouge (1 ⚡ de garnison arrête 10 points de dégâts).</p>
        </details>
        <details class="gd-b">
          <summary><span class="gd-i">🛡️</span><span><b>Défendre ta commune</b><small>Repousser la jauge de l'attaquant</small></span></summary>
          <ol class="gd-etapes">
            <li><b>Tu es prévenu</b> quand un siège commence, puis quand la jauge passe les deux tiers (« en danger »). Ton clan aussi.</li>
            <li><b>Renforce</b> dans Défendre : chaque ⚡ fait reculer la jauge d'environ <b>12 points</b> (×1,2 pour le défenseur). « Tout repousser » met d'un coup ce qu'il faut pour la ramener à 0.</li>
            <li><b>Ton siège devient long</b> dès ta première défense : l'attaquant ne peut plus finir en quelques minutes.</li>
          </ol>
          <p class="gd-p">Un allié de ton clan peut aussi renforcer, jusqu'à 60 ⚡ par siège. Une <b>garnison</b> posée à l'avance protège sans que tu sois là.</p>
        </details>
        <details class="gd-b">
          <summary><span class="gd-i">🌙</span><span><b>La nuit, le Front dort</b><small>De 0 h à 7 h, heure de Paris</small></span></summary>
          <p class="gd-p">Pas de nouveau siège ni de vague, et aucune commune ne tombe. L'énergie déjà en attente dans un siège part à 7 h. Renforcer reste possible.</p>
        </details>
        <details class="gd-b">
          <summary><span class="gd-i">⚡</span><span><b>Trouver de l'énergie</b><small>Où la gagner</small></span></summary>
          <ul class="gd-l">
            <li><b>Recharge</b> : 1 ⚡ toutes les 7 minutes, jusqu'à 120.</li>
            <li><b>Roue du Front</b> : un jeton toutes les 20 minutes, 50 tours par jour, plus la soirée de 21 h à 23 h.</li>
            <li><b>Quêtes du jour</b> : jusqu'à 100 ⚡ par jour.</li>
            <li><b>Mess</b> : ta ration, et les jeux de l'Arcade.</li>
            <li><b>Récoltes</b> et paquets du Front.</li>
          </ul>
        </details>
      </div>
    </section>
'''
rep('index.html', '\n    <section class="tab-panel" id="panel-defense">', GUIDE + '\n    <section class="tab-panel" id="panel-defense">')

rep('app.js', "const ONGLETS_FUSIONNES = ['defense', 'batiments',", "const ONGLETS_FUSIONNES = ['defense', 'batiments', 'guide',")   # patch517
rep('app.js', "const ONGLET_PARENT = { defense: 'combat', batiments: 'combat',", "const ONGLET_PARENT = { defense: 'combat', batiments: 'combat', guide: 'combat',")
rep('app.js', "const ONGLETS_CONNUS = ['tirage', 'collection', 'territoire', 'bourse', 'combat', 'defense', 'batiments',",
              "const ONGLETS_CONNUS = ['tirage', 'collection', 'territoire', 'bourse', 'combat', 'defense', 'batiments', 'guide',")
rep('style.css', "#panel-combat .volets, #panel-defense .volets, #panel-batiments .volets{",
                 "#panel-combat .volets, #panel-defense .volets, #panel-batiments .volets, #panel-guide .volets{")
# patch517 : le panneau Guide suit les mêmes règles de volets que les trois autres (5 volets tiennent sur téléphone)
_p = os.path.join(R, 'style.css'); _t = open(_p, encoding='utf-8').read()
_t2 = _t.replace('#panel-batiments .volet{', '#panel-batiments .volet, #panel-guide .volet{').replace('#panel-batiments .volet-badge{', '#panel-batiments .volet-badge, #panel-guide .volet-badge{')
_t2 = _t2.replace('#panel-combat .volet, #panel-defense .volet{ white-space:nowrap; }', '#panel-combat .volet, #panel-defense .volet, #panel-guide .volet{ white-space:nowrap; }')
if '#panel-guide .volet{' not in _t: open(_p, 'w', encoding='utf-8').write(_t2); print('style.css (volets) : ok')
rep('style.css', ".bth{",
""".gd{ display:flex; flex-direction:column; gap:10px; }   /* patch517 : le guide */
.gd-b{ border:1px solid rgba(255,255,255,.1); border-radius:14px; background:rgba(255,255,255,.03); }
.gd-b > summary{ display:flex; align-items:center; gap:12px; padding:12px 14px; cursor:pointer; list-style:none; }
.gd-b > summary::-webkit-details-marker{ display:none; }
.gd-b > summary::after{ content:'›'; margin-left:auto; font-size:1.2rem; color:var(--brume); transition:transform .2s; }
.gd-b[open] > summary::after{ transform:rotate(90deg); }
.gd-b > summary > span:nth-child(2){ display:flex; flex-direction:column; gap:2px; }
.gd-b > summary small{ font-size:.76rem; color:var(--brume); font-weight:500; }
.gd-i{ font-size:1.3rem; width:28px; text-align:center; }
.gd-b > :not(summary){ margin-left:14px; margin-right:14px; }
.gd-b > :last-child{ margin-bottom:14px; }
.gd-p{ font-size:.86rem; line-height:1.5; margin:0 0 8px; color:var(--texte, #e8e6f0); }
.gd-etapes, .gd-l{ margin:0 0 10px; padding-left:20px; font-size:.86rem; line-height:1.5; display:flex; flex-direction:column; gap:6px; }
.gd-tab{ display:grid; grid-template-columns:1fr 1fr; gap:6px; margin:0 0 10px; }
.gd-tab > div{ display:flex; justify-content:space-between; align-items:center; gap:8px; padding:8px 10px; border-radius:10px; background:rgba(255,255,255,.05); font-size:.8rem; }
.gd-tab span{ color:var(--brume); }
.gd-tab b{ font-family:var(--titre, 'Big Shoulders Display'), Impact, sans-serif; font-size:1rem; white-space:nowrap; }
.gd-m{ color:#FF6369; } .gd-p2{ color:#3DD68C; }
.bth{""")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-23': d.insert(0, {'date': '2026-11-23', 'nouveautes': []})
e = d[0]; e.setdefault('nouveautes', [])
l = "📖 QG › Guide : tout le Front en 5 minutes. Le siège, l'éclair et le long, ce qui change tes dégâts, la défense, la nuit et où trouver de l'énergie."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
