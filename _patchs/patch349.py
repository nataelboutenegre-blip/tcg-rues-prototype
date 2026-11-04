# patch349 (5/11/2026) : la carte cassée après un changement d'onglet en plein
# écran (vidéo d'un joueur, 5/11).
# Cause : en plein écran (téléphone), passer à un autre onglet cachait d'abord
# la carte, puis la sortait du plein écran. recadrerCarte mesurait alors un
# cadre de 0 px : division par zéro, position de la carte en NaN, zoom gardé.
# De retour sur Territoire, la carte restait zoomée sans plein écran, dessinée
# sans son repère (France énorme et coupée, communes une à une au lieu des
# départements), et même « Réduire » ne la réparait plus avant un rechargement.
# - On sort du plein écran AVANT de cacher la carte (onglets et bouton Règles).
# - De retour sur Territoire avec un zoom de plein écran, la carte reprend le
#   plein écran, au même endroit.
# - recadrerCarte ne mesure plus une carte cachée (elle revient alors à toute la France).
# - clampMapPan répare une position invalide (NaN) au lieu de la garder.
import pathlib, json

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')

# 1. onglets : sortir du plein écran tant que la carte est encore visible
s = rep(s, """  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));""",
"""  tab.addEventListener('click', () => {
    // patch349 : avant de cacher la carte (cachée, elle se recadrait sur 0 px)
    if(tab.dataset.tab !== 'territoire') quitterPleinEcran();
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));""")
s = rep(s, """    if(tab.dataset.tab !== 'territoire') quitterPleinEcran();   // patch117
    if(tab.dataset.tab === 'territoire') sizeMapWrap(window.__mapAspectRatio);""",
"""    if(tab.dataset.tab === 'territoire'){
      sizeMapWrap(window.__mapAspectRatio);
      // patch349 : laissée zoomée en plein écran, la carte y revient au même endroit
      if(!carteEnPleinEcran() && mapZoom > PLEIN_ECRAN_SEUIL && pleinEcranPossible()) entrerPleinEcran();
    }""")

# 2. bouton Règles (quand l'onglet Règles n'est pas dans la barre)
s = rep(s, """  loadTauxTirage();
  // l'onglet Regles n'est plus dans la barre : on l'ouvre a la main
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));""",
"""  loadTauxTirage();
  quitterPleinEcran();   // patch349 : avant de cacher la carte
  // l'onglet Regles n'est plus dans la barre : on l'ouvre a la main
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));""")

# 3. recadrerCarte ne mesure pas une carte cachée
s = rep(s, """function recadrerCarte(changer){
  const wrap = document.getElementById('mapWrap');
  if(!wrap) return;
  const ech = echelleCarte() * mapZoom;""",
"""function recadrerCarte(changer){
  const wrap = document.getElementById('mapWrap');
  if(!wrap) return;
  // patch349 : carte cachée (0 px) : rien à mesurer, on repart de toute la France
  if(!wrap.clientWidth || !wrap.clientHeight){
    changer(wrap);
    mapZoom = MAP_ZOOM_MIN; mapPanX = 0; mapPanY = 0;
    return;
  }
  const ech = echelleCarte() * mapZoom;""")

# 4. une position invalide est réparée
s = rep(s, """function clampMapPan(){
  const wrap = document.getElementById('mapWrap');
  if(!wrap) return;""",
"""function clampMapPan(){
  const wrap = document.getElementById('mapWrap');
  if(!wrap) return;
  // patch349 : une position invalide (NaN) bloquait la carte jusqu'au rechargement
  if(!Number.isFinite(mapZoom) || !Number.isFinite(mapPanX) || !Number.isFinite(mapPanY)){
    mapZoom = MAP_ZOOM_MIN; mapPanX = 0; mapPanY = 0;
  }""")

F.write_text(s, encoding='utf-8')

# ======================================================= data/nouveautes.json
F = pathlib.Path('data/nouveautes.json'); d = json.loads(F.read_text(encoding='utf-8'))
ligne = "🗺 Carte : passer à un autre onglet pendant que la carte était en plein écran la cassait (zoomée, décalée, communes une par une) jusqu’au rechargement. Corrigé : en revenant sur Territoire, tu la retrouves en plein écran, là où tu l’avais laissée (défaut signalé par Oshannir)"
if d and d[0].get('date') == '2026-11-05':
    d[0]['nouveautes'].insert(0, ligne)
else:
    d.insert(0, {'date': '2026-11-05', 'nouveautes': [ligne]})
F.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch349 ok')
