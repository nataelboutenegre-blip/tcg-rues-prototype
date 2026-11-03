# patch324 (3/11/2026) : « Premiers pas » mène au Front + mesure de l'accueil (s2-86)
# A. L'étape 1 devient « Ouvre ton premier paquet du Front » : le bouton passe en
#    mode Front, relit les paquets, puis montre le paquet prêt (ou ouvre le
#    paquet gratuit). Avant, le bouton cliquait un bouton souvent grisé quand
#    un paquet prêt était affiché, et ouvrait du Terra en mode Terra.
# C. onbMarque(etape) : la première fois qu'un nouveau (compte < 14 jours)
#    passe une étape de l'accueil, le jeu le note (accueil_etape, s2-86).
#    Silencieux : si la fonction n'existe pas encore, rien ne s'affiche.
import pathlib

F = pathlib.Path('app.js')
s = F.read_text(encoding='utf-8')

def rep(avant, apres, n=1):
    global s
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    s = s.replace(avant, apres)

# ---------- A. Premiers pas : l'étape 1 au Front ----------
rep("""    ['paquet', 'Ouvre ton premier paquet', '5 vraies communes, à leur place sur la carte', 'Ouvrir'],""",
    """    ['paquet', 'Ouvre ton premier paquet du Front', '5 communes rien qu’à toi sur la carte partagée', 'Ouvrir'],   // patch324""")

rep("""async function ppAction(quoi, bouton){
  if(quoi === 'paquet'){
    const b = document.getElementById('openFreeBtn');
    if(b && !b.disabled) b.click();
    else { if(b) b.scrollIntoView({ behavior: 'smooth', block: 'center' }); notifier({ type: 'info', titre: 'Paquet', texte: 'Ton prochain paquet gratuit arrive bientôt : le compte à rebours est juste en dessous.' }); }
    return;
  }""",
    """async function ppAction(quoi, bouton){
  onbMarque('pp_' + quoi);   // patch324
  if(quoi === 'paquet'){
    // patch324 : le premier paquet du Front (s2-86 ne coche plus l'étape avec du Terra)
    if(paquetEnCours){ notifier({ type: 'info', titre: 'Un paquet est en cours', texte: 'Retourne d’abord tes cartes, puis reviens ici.' }); return; }
    ncAller('front', 'tirage', async () => {
      try{ await loadPackStatus(); }catch(e){}
      const pret = document.querySelector('#packZone .paquet[data-pret]');
      const b = document.getElementById('openFreeBtn');
      if(pret){
        pret.scrollIntoView({ behavior: 'smooth', block: 'center' });
        appelerPaquet(pret);
        notifier({ type: 'info', titre: 'Ton paquet du Front', texte: 'Touche le paquet pour l’ouvrir : ces 5 communes seront à toi sur la carte.' });
      } else if(b && !b.disabled) b.click();
      else { if(b) b.scrollIntoView({ behavior: 'smooth', block: 'center' }); notifier({ type: 'info', titre: 'Paquet du Front', texte: 'Ton prochain paquet gratuit arrive bientôt : le compte à rebours est juste en dessous.' }); }
    });
    return;
  }""")

# la carte affichée : une fois
rep("""  const P = PREMIERS_PAS;
  el.hidden = !P;
  if(!P) return;
""", """  const P = PREMIERS_PAS;
  el.hidden = !P;
  if(!P) return;
  onbMarque('pp_vu');   // patch324
""")

# ---------- C. la mesure de l'accueil ----------
rep("""// ---------- patch306 : Premiers pas (s2-74) ----------""",
    """// ---------- patch324 : mesure de l'accueil (s2-86) ----------
// La première fois qu'un nouveau (compte de moins de 14 jours) passe une étape,
// le serveur la note. Une fois par appareil (mémoire locale), sans rien afficher.
var ONB = { actif: false, uid: null, faits: new Set(), envoyes: new Set() };
function onbDemarrer(session_){
  try{
    const u = session_ && session_.user;
    ONB.uid = u ? u.id : null;
    ONB.envoyes = new Set();
    ONB.actif = !!(u && u.created_at && Date.now() - Date.parse(u.created_at) < 14 * 864e5);
    ONB.faits = new Set(JSON.parse(localStorage.getItem('tf-onb-' + ONB.uid) || '[]'));
  }catch(e){ ONB.faits = new Set(); }
}
function onbAppareil(){
  let a = 'ordi';
  try{ if(window.matchMedia('(pointer: coarse)').matches) a = 'mobile'; }catch(e){}
  try{ if(window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) a += '-appli'; }catch(e){}
  return a + '-' + modeJeu;
}
function onbMarque(etape, detail){
  const o = window.ONB;
  if(!o || !o.actif || o.faits.has(etape) || o.envoyes.has(etape)) return;
  o.envoyes.add(etape);
  try{
    sb.rpc('accueil_etape', { p_etape: etape, p_detail: detail || null }).then(({ error }) => {
      if(error) return;
      o.faits.add(etape);
      try{ localStorage.setItem('tf-onb-' + o.uid, JSON.stringify([...o.faits])); }catch(e){}
    }, () => {});
  }catch(e){}
}

// ---------- patch306 : Premiers pas (s2-74) ----------""")

# entrée dans le jeu
rep("""async function showGame(session_){
  if(cdjInvite) quitterInviteCdj();""",
    """async function showGame(session_){
  onbDemarrer(session_); onbMarque('arrive');   // patch324
  if(cdjInvite) quitterInviteCdj();""")
rep("""  dmFin(true);   // patch225 : on arrive dans le jeu
""", """  dmFin(true);   // patch225 : on arrive dans le jeu
  onbMarque('jeu', onbAppareil());   // patch324
""")

# l'écran d'accueil
rep("""  voile.hidden = false;
  requestAnimationFrame(() => voile.classList.add('ouvert'));
  const go = document.getElementById('accueilGo');""",
    """  voile.hidden = false;
  onbMarque('accueil_vu');   // patch324
  requestAnimationFrame(() => voile.classList.add('ouvert'));
  const go = document.getElementById('accueilGo');""")
rep("""document.getElementById('accueilGo').addEventListener('click', () => {
  fermerAccueil(true);""", """document.getElementById('accueilGo').addEventListener('click', () => {
  onbMarque('accueil_ouvrir');   // patch324
  fermerAccueil(true);""")
rep("""document.getElementById('accueilPasser').addEventListener('click', () => {
  fermerAccueil(false);""", """document.getElementById('accueilPasser').addEventListener('click', () => {
  onbMarque('accueil_passer');   // patch324
  fermerAccueil(false);""")
rep("""document.getElementById('accueilRegles').addEventListener('click', () => {
  fermerAccueil(false);""", """document.getElementById('accueilRegles').addEventListener('click', () => {
  onbMarque('accueil_regles');   // patch324
  fermerAccueil(false);""")

# le guide
rep("""  const etape = ETAPES_GUIDE[guideIndex];
  if(!etape){ fermerGuide(); return; }""", """  const etape = ETAPES_GUIDE[guideIndex];
  if(!etape){ fermerGuide(); return; }
  onbMarque('guide_' + (guideIndex + 1));   // patch324""")
rep("""  if(guideCibleActuelle){ guideCibleActuelle.classList.remove('guide-cible'); guideCibleActuelle = null; }
  if(voile) voile.hidden = true;
  if(bulle) bulle.hidden = true;
  guideIndex = -1;""", """  if(guideCibleActuelle){ guideCibleActuelle.classList.remove('guide-cible'); guideCibleActuelle = null; }
  if(voile) voile.hidden = true;
  if(bulle) bulle.hidden = true;
  if(guideIndex >= 0) onbMarque(guideIndex >= ETAPES_GUIDE.length ? 'guide_fini' : 'guide_passe');   // patch324
  guideIndex = -1;""")

# changement de mode
rep("""    modeJeu = b.dataset.mode;
    try { localStorage.setItem('tf-mode', modeJeu); } catch(err){}
    appliquerMode();""", """    modeJeu = b.dataset.mode;
    try { localStorage.setItem('tf-mode', modeJeu); } catch(err){}
    onbMarque('mode_' + modeJeu);   // patch324
    appliquerMode();""")

# paquet payé (bouton, puis paquet prêt), cartes révélées
rep("""  // le paquet en cours n'est pas encore ouvert : pas question d'en relancer un avant d'avoir retourne les cartes
  paquetEnCours = true;
  await loadPackStatus();
  afficherPaquetATirer(type, 5);""", """  // le paquet en cours n'est pas encore ouvert : pas question d'en relancer un avant d'avoir retourne les cartes
  paquetEnCours = true;
  onbMarque('paquet_' + (enTerra() ? 'terra' : 'front'));   // patch324
  await loadPackStatus();
  afficherPaquetATirer(type, 5);""")
rep("""    delete pack.dataset.pret;
    loadPackStatus();
    return tirerCartesDuPaquet(5);""", """    delete pack.dataset.pret;
    onbMarque('paquet_' + (enTerra() ? 'terra' : 'front'));   // patch324
    loadPackStatus();
    return tirerCartesDuPaquet(5);""")
rep("""function revealCards(draws){
  const zone = document.getElementById('packZone');""", """function revealCards(draws){
  if(draws && draws.length) onbMarque('cartes_' + (enTerra() ? 'terra' : 'front'));   // patch324
  const zone = document.getElementById('packZone');""")

F.write_text(s, encoding='utf-8')
print('patch324 appliqué')
