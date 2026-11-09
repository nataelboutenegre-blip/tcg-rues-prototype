# patch392 (9/11/2026) : le bonus de débutant ne joue plus sur une épique ni une légendaire (s2-131).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
# la fiche d'attaque : les puces
rep(A, """function atkPuces(code, a){
  const p = [];
  const deb = debutantActif();
  if(attaqueEnGarnison) p.push(['moins', ICONES_PC.bouclier, 'Garnison']);
  if(deb) p.push(attaqueEnGarnison ? ['neutre', ICONE_DEBUTANT, 'Sans bonus de débutant'] : ['plus', ICONE_DEBUTANT, 'Bonus de débutant']);""",
"""// patch392 : le bonus de débutant ne joue ni sur une épique ni sur une légendaire (s2-131)
function debHautRang(code){ const c = othersMap.get(code); const t = c && c.tier && c.tier.id; return t === 'epique' || t === 'legendaire'; }
function debutantIci(code){ return debutantActif() && !attaqueEnGarnison && !debHautRang(code); }
function atkPuces(code, a){
  const p = [];
  const deb = debutantActif(), debOk = debutantIci(code);
  if(attaqueEnGarnison) p.push(['moins', ICONES_PC.bouclier, 'Garnison']);
  if(deb) p.push(debOk ? ['plus', ICONE_DEBUTANT, 'Bonus de débutant'] : ['neutre', ICONE_DEBUTANT, 'Sans bonus de débutant']);""")
rep(A, "if(a.a_distance) p.push([deb && !attaqueEnGarnison ? 'neutre' : 'moins', ICONE_REPERE, 'À distance']);",
       "if(a.a_distance) p.push([debOk ? 'neutre' : 'moins', ICONE_REPERE, 'À distance']);")
# la fiche d'attaque : le détail
rep(A, """    ${debutantActif() ? (attaqueEnGarnison
      ? `<div class="db-badge non">${ICONE_DEBUTANT}<span><b>Pas de bonus de débutant ici :</b> il ne joue jamais contre une commune en garnison.</span></div>`
      : `<div class="db-badge">""",
"""    ${debutantActif() ? (attaqueEnGarnison
      ? `<div class="db-badge non">${ICONE_DEBUTANT}<span><b>Pas de bonus de débutant ici :</b> il ne joue jamais contre une commune en garnison.</span></div>`
      : debHautRang(code)
      ? `<div class="db-badge non">${ICONE_DEBUTANT}<span><b>Pas de bonus de débutant ici :</b> il ne joue pas contre une épique ou une légendaire. Tes chances sont les chances normales.</span></div>`
      : `<div class="db-badge">""")
rep(A, "<div class=\"pc-prox ${a.a_distance && !(debutantActif() && !attaqueEnGarnison) ? 'loin' : ''}\">",
       "<div class=\"pc-prox ${a.a_distance && !debutantIci(code) ? 'loin' : ''}\">")
rep(A, "? (debutantActif() && !attaqueEnGarnison ? 'Aucune de tes communes à moins de 20 km : <b>attaque à distance</b>, sans effet avec ton bonus de débutant.'",
       "? (debutantIci(code) ? 'Aucune de tes communes à moins de 20 km : <b>attaque à distance</b>, sans effet avec ton bonus de débutant.'")
# le bandeau de l'onglet Combat et les Premiers pas
rep(A, "même en prudent et même loin de chez toi. Pas contre une commune en garnison. Il s’arrête",
       "même en prudent et même loin de chez toi. Pas contre une commune en garnison, ni contre une épique ou une légendaire. Il s’arrête")
rep(A, "même loin de chez toi (sauf contre une garnison), jusqu’à ta première conquête.",
       "même loin de chez toi (sauf contre une garnison, une épique ou une légendaire), jusqu’à ta première conquête.")
# la cible proposée aux nouveaux : jamais une épique ni une légendaire
rep(A, """    if(PP_GARNIS.has(String(c.code))) continue;   // patch365 : jamais une garnison""",
"""    if(PP_GARNIS.has(String(c.code))) continue;   // patch365 : jamais une garnison
    if(rangT(c.tier) >= 3) continue;   // patch392 : ni une épique ni une légendaire (pas de bonus de débutant)""")
rep(A, "au moins ${DEBUTANT.chances}\\u00a0% par assaut, même en prudent. Il s’arrête à ta première conquête, puis tout redevient normal.",
       "au moins ${DEBUTANT.chances}\\u00a0% par assaut, même en prudent (sauf contre une garnison, une épique ou une légendaire). Il s’arrête à ta première conquête, puis tout redevient normal.")
# les règles
rep('index.html', "Une Forteresse garde son effet ; <b>aucun bonus contre une commune en garnison</b>.",
    "Une Forteresse garde son effet ; <b>aucun bonus contre une commune en garnison, ni contre une épique ou une légendaire</b> (chances normales).")
print('patch392 ok')
