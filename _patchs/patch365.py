# patch365 (7/11/2026) : le bonus de débutant (s2-111, « piste 1 », accord de Nataël).
#
# Un compte de moins de 7 jours qui n'a encore rien conquis a au moins 85 %
# par assaut, même en prudent et même loin de ses communes. Jamais contre une
# commune en garnison ; une Forteresse garde son effet. Le bonus s'arrête à
# la première conquête. Le serveur décide (debutant_etat, apercu_attaque,
# attaquer) ; le jeu l'explique :
#   - Premiers pas : une ligne « Bonus de débutant · encore X jours » ;
#   - Combat › Attaquer : un bandeau qui dit ce que fait le bonus, et qu'après
#     tout redevient normal ;
#   - fiche d'attaque : le bonus, ou « pas de bonus ici » sur une garnison ;
#   - fiche guidée : le bonus, et elle s'ouvre aussi SANS paquet du Front
#     (pot vide), une fois par session, en arrivant sur Territoire ou Combat ;
#   - la cible proposée évite les garnisons et les Forteresses ;
#   - la première conquête annonce la fin du bonus ;
#   - Premiers pas, étape 1 : « Tourne la roue du Front » quand le pot est vide
#     (s2-111 la coche avec un tour de roue) ;
#   - règles : une phrase sur le bonus.
# Sans s2-111 (debutant_etat absent), rien ne s'affiche.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch365' not in s, 'patch365 déjà appliqué'

# --- l'état du bonus
s = rep(s, """// ---------- patch306 : Premiers pas (s2-74) ----------""",
"""// ---------- patch365 : le bonus de débutant (s2-111) ----------
// Compte de moins de 7 jours sans conquête : au moins 85 % par assaut, même
// à distance ; jamais contre une garnison. Le serveur décide, le jeu explique.
var DEBUTANT = null, DEBUTANT_FINI = false, PP_GARNIS = new Set(), ppVerifLu = 0;
const ICONE_DEBUTANT = '<svg class="db-ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8l2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.6l-5.4 2.9 1.1-6.1-4.5-4.2 6.1-.8z" fill="currentColor"/></svg>';
async function chargerDebutant(){
  if(!SAISON2) return;
  try{
    const { data: ss } = await sb.auth.getSession();
    const cree = ss && ss.session && ss.session.user ? Date.parse(ss.session.user.created_at) : 0;
    if(!cree || Date.now() - cree > 8 * 864e5){ DEBUTANT = null; return; }   // les anciens : aucun appel
    const { data, error } = await sb.rpc('debutant_etat');
    DEBUTANT = !error && data && data.actif ? { fin: Date.parse(data.fin_le) || 0, chances: Number(data.chances) || 85 } : null;
  }catch(e){ DEBUTANT = null; }
  debutantAfficher();
  setTimeout(pcSansPaquet, 1500);
}
function debutantActif(){ return !!(DEBUTANT && DEBUTANT.fin > Date.now()); }
function debutantReste(){
  if(!debutantActif()) return '';
  const ms = DEBUTANT.fin - Date.now();
  if(ms < 864e5) return 'encore ' + formatDuree(ms);
  const j = Math.ceil(ms / 864e5);
  return `encore ${j} jour${j > 1 ? 's' : ''}`;
}
function debutantAfficher(){
  const pan = document.getElementById('panel-combat');
  if(pan){
    let b = document.getElementById('debutantCombat');
    if(!b && debutantActif()){
      b = document.createElement('div');
      b.id = 'debutantCombat'; b.className = 'db-bandeau'; b.setAttribute('role', 'status');
      const sub = pan.querySelector(':scope > .sub') || pan.querySelector('.volets');
      if(sub) sub.insertAdjacentElement('afterend', b);
    }
    if(b){
      b.hidden = !debutantActif();
      if(debutantActif()) b.innerHTML = `${ICONE_DEBUTANT}<span><b>Bonus de débutant</b> · ${debutantReste()}<br>Au moins <b>${DEBUTANT.chances} %</b> par assaut, même en prudent et même loin de chez toi. Pas contre une commune en garnison. Il s’arrête à ta première conquête : ensuite, tes chances redeviennent normales.</span>`;
    }
  }
  renderPremiersPas();
}

// ---------- patch306 : Premiers pas (s2-74) ----------""")

s = rep(s, "  chargerPremiersPas();   // patch306\n",
           "  chargerPremiersPas();   // patch306\n  chargerDebutant();   // patch365\n")

# --- la cible proposée : ni garnison ni Forteresse, les n meilleures
s = rep(s, "function ppCible(exclues){   // patch336 : exclues = codes déjà proposés",
           "function ppCibles(exclues, n){   // patch336 : exclues = codes déjà proposés ; patch365 : les n meilleures")
s = rep(s, """  let meilleure = null, score = Infinity;
  for(const c of othersMap.values()){""", """  const tous = [];
  for(const c of othersMap.values()){""")
s = rep(s, """    if(exclues && exclues.has(c.code)) continue;
    let d = 300;""", """    if(exclues && exclues.has(c.code)) continue;
    if(PP_GARNIS.has(String(c.code))) continue;   // patch365 : jamais une garnison
    if(typeof BATIMENTS_CARTE !== 'undefined' && BATIMENTS_CARTE && BATIMENTS_CARTE.get && (BATIMENTS_CARTE.get(String(c.code)) || {}).forteresse) continue;   // ni une Forteresse
    let d = 300;""")
s = rep(s, """    const sc = d + rangT(c.tier) * 15;
    if(sc < score){ score = sc; meilleure = c; }
  }
  return meilleure;
}""", """    const sc = d + rangT(c.tier) * 15;
    tous.push([sc, c]);
  }
  return tous.sort((a, b) => a[0] - b[0]).slice(0, n || 1).map(x => x[1]);
}
function ppCible(exclues){ return ppCibles(exclues, 1)[0] || null; }
// patch365 : on demande au serveur lesquelles des meilleures cibles sont en garnison
async function ppGarnisVerifier(exclues){
  const liste = ppCibles(exclues, 15);
  if(!liste.length) return liste;
  try{
    const { data, error } = await sb.rpc('garnisons_visibles', { p_codes: liste.map(c => String(c.code)) });
    if(!error && Array.isArray(data)) data.forEach(g => PP_GARNIS.add(String(g.commune_code)));
  }catch(e){}
  ppVerifLu = Date.now();
  return liste;
}
async function ppCibleSure(exclues){
  const liste = await ppGarnisVerifier(exclues);
  return liste.find(c => !PP_GARNIS.has(String(c.code))) || null;
}""")

# --- Premiers pas : le bonus, la roue à l'étape 1
s = rep(s, """  const cible = P.attaque ? null : ppCible();
  const etapes = [
    ['paquet', 'Ouvre ton premier paquet du Front', '5 communes rien qu’à toi sur la carte partagée', 'Ouvrir'],   // patch324
    ['attaque', 'Gagne ta première attaque', cible ? `Une cible facile près de chez toi : ${echapperHtml(cible.nom)} (${echapperHtml(cible.dept)})` : 'Choisis une commune proche dans l’onglet Combat', 'Attaquer'],""",
"""  const cible = P.attaque ? null : ppCible();
  if(cible && Date.now() - ppVerifLu > 60000){ ppVerifLu = Date.now(); ppGarnisVerifier().then(() => { if(PP_GARNIS.has(String(cible.code))) renderPremiersPas(); }); }   // patch365
  const parRoue = !P.paquet && typeof roueActive === 'function' && roueActive();   // patch365 : pot vide
  const deb = debutantActif();
  const etapes = [
    parRoue ? ['paquet', 'Tourne la roue du Front', 'Plus aucune commune libre en ce moment : la roue te donne de l’énergie pour attaquer', 'Tourner']
            : ['paquet', 'Ouvre ton premier paquet du Front', '5 communes rien qu’à toi sur la carte partagée', 'Ouvrir'],   // patch324
    ['attaque', 'Gagne ta première attaque', cible ? `Une cible facile${deb ? '' : ' près de chez toi'} : ${echapperHtml(cible.nom)} (${echapperHtml(cible.dept)})${deb ? ` · <b>${DEBUTANT.chances} %</b> avec ton bonus` : ''}` : 'Choisis une commune proche dans l’onglet Combat', 'Attaquer'],""")
s = rep(s, """    <p class="pp-sous">${faites === 4 ? 'Bravo, tout est fait : ta récompense t’attend.' : 'Fais ces 4 choses pour bien démarrer ta conquête.'}</p>""",
"""    <p class="pp-sous">${faites === 4 ? 'Bravo, tout est fait : ta récompense t’attend.' : 'Fais ces 4 choses pour bien démarrer ta conquête.'}</p>
    ${deb ? `<div class="db-pp">${ICONE_DEBUTANT}<span><b>Bonus de débutant</b> · ${debutantReste()} : au moins ${DEBUTANT.chances} % par assaut, même loin de chez toi (sauf contre une garnison), jusqu’à ta première conquête. Ensuite, retour à la normale.</span></div>` : ''}""")

s = rep(s, """  if(quoi === 'paquet'){ ppOuvrirPaquetFront(); return; }   // patch336 : partagé avec l'accueil
  if(quoi === 'attaque'){
    ncAller('front', 'territoire', () => {
      const c = ppCible();""", """  if(quoi === 'paquet' && typeof roueActive === 'function' && roueActive()){   // patch365 : pot vide, la roue
    ncAller('front', 'tirage', () => { const r = document.getElementById('roueFront'); if(r) r.scrollIntoView({ behavior: 'smooth', block: 'center' }); });
    return;
  }
  if(quoi === 'paquet'){ ppOuvrirPaquetFront(); return; }   // patch336 : partagé avec l'accueil
  if(quoi === 'attaque'){
    ncAller('front', 'territoire', async () => {
      const c = await ppCibleSure();   // patch365""")

# --- la roue : l'étape 1 se coche, et l'étape change de texte quand la roue s'ouvre
s = rep(s, """  roueLu = Date.now();
  renderRoue();
}""", """  roueLu = Date.now();
  renderRoue();
  if(PREMIERS_PAS) renderPremiersPas();   // patch365
}""")
s = rep(s, """  roueGainMontrer(data);
  renderRoueInfos();""", """  roueGainMontrer(data);
  renderRoueInfos();
  if(PREMIERS_PAS && !PREMIERS_PAS.paquet) ppRelire(1500);   // patch365 : étape 1 par la roue""")

# --- la fiche guidée : aussi sans paquet, une cible sûre, le bonus
s = rep(s, """async function pcProposer(){
  if(paquetEnCours || NC.ouvert) return;
  const c = ppCible(PC.exclues);
  if(!c) return;
  PC.info = c;
  onbMarque('pc_vu');
  pcOuvrir(pcFicheHtml(c, null));""", """async function pcProposer(){
  if(paquetEnCours || NC.ouvert) return;
  const c = await ppCibleSure(PC.exclues);   // patch365 : ni garnison ni Forteresse
  if(!c || paquetEnCours || NC.ouvert) return;
  PC.info = c;
  onbMarque('pc_vu');
  try{ sessionStorage.setItem('tf-pc-sp', '1'); }catch(e){}   // patch365
  pcOuvrir(pcFicheHtml(c, null));""")
s = rep(s, """function pcFicheHtml(c, a){""", """// patch365 : la fiche guidée s'ouvre aussi sans paquet du Front (pot vide), une fois par session
function pcSansPaquet(){
  if(!SAISON2 || !debutantActif() || modeJeu !== 'front') return;
  try{ if(sessionStorage.getItem('tf-pc-sp')) return; }catch(e){}
  const t = document.querySelector('.tab.active[data-tab]');
  if(!t || !['territoire', 'combat'].includes(t.dataset.tab)) return;
  pcApresPaquet();
}
function pcFicheHtml(c, a){""")
s = rep(s, """      ${proche ? `<small>${km <= 20 ? `À ${km} km de ${echapperHtml(proche.entry.nom)}, ta commune` : `À ${km} km de ta commune la plus proche : une attaque à distance`}</small>` : ''}</div></div>""",
"""      ${proche ? `<small>${km <= 20 ? `À ${km} km de ${echapperHtml(proche.entry.nom)}, ta commune` : `À ${km} km de ta commune la plus proche : une attaque à distance${debutantActif() ? ', sans effet avec ton bonus' : ''}`}</small>` : ''}</div></div>""")
s = rep(s, """    <p class="pc-txt">Une défaite ne te fait <b>rien perdre</b> : ta série reste où elle en est.${delai ? ` Entre deux assauts sur cette commune : <b>${formatDuree(delai)}</b>.` : ''}</p>""",
"""    ${debutantActif() ? `<div class="db-pp">${ICONE_DEBUTANT}<span><b>Bonus de débutant</b> · ${debutantReste()} : au moins ${DEBUTANT.chances} % par assaut, même en prudent. Il s’arrête à ta première conquête, puis tout redevient normal.</span></div>` : ''}
    <p class="pc-txt">Une défaite ne te fait <b>rien perdre</b> : ta série reste où elle en est.${delai ? ` Entre deux assauts sur cette commune : <b>${formatDuree(delai)}</b>.` : ''}</p>""")

# --- la fiche d'attaque
s = rep(s, """    ${attaqueEnGarnison ? `<div class="gn-badge">${ICONES_PC.bouclier}<span><b>Commune en garnison.</b> Une victoire sur deux est annulée par sa défense : la chance affichée en tient déjà compte.</span></div>` : ''}""",
"""    ${attaqueEnGarnison ? `<div class="gn-badge">${ICONES_PC.bouclier}<span><b>Commune en garnison.</b> Une victoire sur deux est annulée par sa défense : la chance affichée en tient déjà compte.</span></div>` : ''}
    ${debutantActif() ? (attaqueEnGarnison
      ? `<div class="db-badge non">${ICONE_DEBUTANT}<span><b>Pas de bonus de débutant ici :</b> il ne joue jamais contre une commune en garnison.</span></div>`
      : `<div class="db-badge">${ICONE_DEBUTANT}<span><b>Bonus de débutant</b> · ${debutantReste()} : ${a.chances} % ici, même en prudent et même loin de chez toi. Il s’arrête à ta première conquête.</span></div>`) : ''}""")
s = rep(s, """        ? 'Aucune de tes communes à moins de 20 km : <b>attaque à distance</b>, tes chances baissent.'""",
"""        ? (debutantActif() && !attaqueEnGarnison ? 'Aucune de tes communes à moins de 20 km : <b>attaque à distance</b>, sans effet avec ton bonus de débutant.' : 'Aucune de tes communes à moins de 20 km : <b>attaque à distance</b>, tes chances baissent.')   // patch365""")

# --- la première conquête met fin au bonus
s = rep(s, """    mettreEnSceneAssaut(cibleVue, r);
    pcApresAssaut(code, r);   // patch336""", """    mettreEnSceneAssaut(cibleVue, r);
    if(r.conquise && debutantActif()){   // patch365 : le bonus de débutant s'arrête
      const guidee = pcLire(PC_CIBLE) === code && !pcLire(PC_FETE);
      DEBUTANT_FINI = true; DEBUTANT = null; debutantAfficher();
      if(!guidee) setTimeout(() => notifier({ type: 'succes', titre: 'Première conquête : bonus terminé', texte: 'Bravo ! Désormais tes chances dépendent de ton engagement (35, 50 ou 65 %) et de tes communes autour.' }), 2500);
    }
    pcApresAssaut(code, r);   // patch336""")
s = rep(s, """    <div class="pc-gains"><span>+${PC_TP[info.tier] || 5} TP</span><span>+10 au classement</span></div>""",
"""    <div class="pc-gains"><span>+${PC_TP[info.tier] || 5} TP</span><span>+10 au classement</span></div>
    ${DEBUTANT_FINI ? '<p class="pc-db">Ton bonus de débutant s’arrête ici : désormais, tes chances dépendent de ton engagement (35, 50 ou 65 %) et de tes communes autour.</p>' : ''}""")

# --- en arrivant sur Territoire ou Combat : la fiche guidée sans paquet
s = rep(s, """    if(tab.dataset.tab === 'combat') mfoEntrer();   // patch288""",
"""    if(tab.dataset.tab === 'combat') mfoEntrer();   // patch288
    if(SAISON2 && (tab.dataset.tab === 'territoire' || tab.dataset.tab === 'combat')) setTimeout(pcSansPaquet, 900);   // patch365""")

# --- retouches après l'aperçu : 85 % insécable, bandeau avant le long texte, « à distance » sans rouge
s = rep(s, "${deb ? ` · <b>${DEBUTANT.chances} %</b> avec ton bonus` : ''}", "${deb ? ` · ${DEBUTANT.chances}\\u00a0% avec ton bonus` : ''}")
s = rep(s, "au moins ${DEBUTANT.chances} % par assaut, même loin de chez toi (sauf contre une garnison)", "au moins ${DEBUTANT.chances}\\u00a0% par assaut, même loin de chez toi (sauf contre une garnison)")
s = rep(s, "au moins ${DEBUTANT.chances} % par assaut, même en prudent. Il s’arrête", "au moins ${DEBUTANT.chances}\\u00a0% par assaut, même en prudent. Il s’arrête")
s = rep(s, "Au moins <b>${DEBUTANT.chances} %</b> par assaut", "Au moins <b>${DEBUTANT.chances}\\u00a0%</b> par assaut")
s = rep(s, ": ${a.chances} % ici, même en prudent", ": ${a.chances}\\u00a0% ici, même en prudent")
s = rep(s, "      if(sub) sub.insertAdjacentElement('afterend', b);", "      if(sub) sub.insertAdjacentElement(sub.classList.contains('sub') ? 'beforebegin' : 'afterend', b);")
s = rep(s, """    <div class="pc-prox ${a.a_distance ? 'loin' : ''}">""", """    <div class="pc-prox ${a.a_distance && !(debutantActif() && !attaqueEnGarnison) ? 'loin' : ''}">""")

# --- patch365, ajout du 7/11 (12 h 14, accord de Nataël) : un nouveau sans commune
# choisit sa première cible près de chez lui (ce sera sa base pour la suite).
s = rep(s, """function pcSansPaquet(){""", """function pcSansCommune(){ return ![...collectionMap.values()].some(m => !m.perdue); }
function pcSansPaquet(){""")
s = rep(s, """    <button type="button" class="pc-go" data-pc-act="lancer" data-pc-code="${echapperTexte(c.code)}">Lancer l'assaut</button>
    <div class="pc-sec"><button type="button" data-pc-act="autre">Une autre cible</button><button type="button" data-pc-act="plustard">Plus tard</button></div>`;""",
"""    ${pcSansCommune() ? '<div class="pc-base"><b>Tu n’as pas encore de commune.</b> Choisis ta première cible près de chez toi : ce sera ta base pour la suite.</div>' : ''}
    <button type="button" class="pc-go" data-pc-act="lancer" data-pc-code="${echapperTexte(c.code)}">${pcSansCommune() ? 'Attaquer ' + echapperHtml(c.nom) : 'Lancer l\\'assaut'}</button>
    ${pcSansCommune() ? '<button type="button" class="pc-carte" data-pc-act="carte">Choisir sur la carte, près de chez moi</button>' : ''}
    <div class="pc-sec"><button type="button" data-pc-act="autre">Une autre cible</button><button type="button" data-pc-act="plustard">Plus tard</button></div>`;""")
s = rep(s, """  if(a === 'autre'){ if(PC.info) PC.exclues.add(PC.info.code); onbMarque('pc_autre'); return pcProposer(); }""",
"""  if(a === 'autre'){ if(PC.info) PC.exclues.add(PC.info.code); onbMarque('pc_autre'); return pcProposer(); }
  if(a === 'carte'){   // patch365 : sans commune, il choisit sa cible près de chez lui
    onbMarque('pc_carte'); pcFermer();
    ncAller('front', 'territoire', () => { const m = document.getElementById('mapWrap'); if(m) m.scrollIntoView({ behavior: 'smooth', block: 'center' }); notifier({ type: 'info', titre: 'Choisis ta première cible', texte: `Touche la commune d’un autre joueur près de chez toi, puis « Attaquer »${debutantActif() ? ` : ${DEBUTANT.chances}\\u00a0% avec ton bonus de débutant` : ''}.` }); });
    return;
  }""")
s = rep(s, """    const { data, error } = await sb.rpc('attaquer', { p_commune_code: code, p_intensite: intensiteChoisie });""",
"""    if(debutantActif() && pcSansCommune() && !pcLire(PC_CIBLE) && !pcLire(PC_FETE)) pcEcrire(PC_CIBLE, code);   // patch365 : la cible choisie sur la carte est suivie et fêtée
    const { data, error } = await sb.rpc('attaquer', { p_commune_code: code, p_intensite: intensiteChoisie });""")
s = rep(s, """    ['attaque', 'Gagne ta première attaque', cible ? `Une cible facile${deb ? '' : ' près de chez toi'} : ${echapperHtml(cible.nom)} (${echapperHtml(cible.dept)})${deb ? ` · ${DEBUTANT.chances}\\u00a0% avec ton bonus` : ''}` : 'Choisis une commune proche dans l’onglet Combat', 'Attaquer'],""",
"""    ['attaque', 'Gagne ta première attaque', deb && pcSansCommune() ? `Choisis une commune près de chez toi : ${DEBUTANT.chances}\\u00a0% avec ton bonus` : cible ? `Une cible facile${deb ? '' : ' près de chez toi'} : ${echapperHtml(cible.nom)} (${echapperHtml(cible.dept)})${deb ? ` · ${DEBUTANT.chances}\\u00a0% avec ton bonus` : ''}` : 'Choisis une commune proche dans l’onglet Combat', 'Attaquer'],""")
s = rep(s, """  if(quoi === 'attaque'){
    ncAller('front', 'territoire', async () => {""", """  if(quoi === 'attaque' && debutantActif() && pcSansCommune()){ ncAller('front', 'territoire', () => setTimeout(pcProposer, 300)); return; }   // patch365 : la fiche avec « Choisir sur la carte »
  if(quoi === 'attaque'){
    ncAller('front', 'territoire', async () => {""")

F.write_text(s, encoding='utf-8')

# --- styles
C = pathlib.Path('style.css'); css = C.read_text(encoding='utf-8')
assert 'patch365' not in css
css += """
/* patch365 : le bonus de débutant */
.db-ic{ width:18px; height:18px; flex:none; color:#F0B429; }
.db-bandeau{ display:flex; align-items:flex-start; gap:10px; margin:10px 0 12px; padding:11px 13px; border-radius:12px;
  background:rgba(240,180,41,.1); border:1px solid rgba(240,180,41,.45); color:#F1F5F9; font-size:.84rem; line-height:1.45; text-align:left; }
.db-bandeau[hidden]{ display:none; }
.db-bandeau b{ color:#FFD36B; }
.db-pp{ display:flex; align-items:flex-start; gap:8px; margin:0 0 10px; padding:9px 11px; border-radius:10px;
  background:rgba(240,180,41,.1); border:1px solid rgba(240,180,41,.4); font-size:.78rem; line-height:1.4; color:#F1F5F9; text-align:left; }
.db-pp b{ color:#FFD36B; }
.db-badge{ display:flex; align-items:flex-start; gap:8px; margin-top:10px; padding:9px 10px; border-radius:10px;
  background:rgba(240,180,41,.1); border:1px solid rgba(240,180,41,.4); font-size:.8rem; line-height:1.4; }
.db-badge b{ color:#FFD36B; }
.db-badge.non{ background:rgba(169,188,212,.08); border-color:rgba(169,188,212,.3); }
.db-badge.non .db-ic{ color:#A9BCD4; }
.db-badge.non b{ color:#fff; }
.pc-db{ margin:10px 0 0; font-size:.82rem; line-height:1.4; color:#FFD9B8; text-align:center; }
.pc-base{ margin:0 0 12px; padding:10px 12px; border-radius:10px; background:rgba(47,124,246,.12); border:1px solid rgba(110,170,255,.4); font-size:.82rem; line-height:1.4; color:#F1F5F9; text-align:left; }
.pc-base b{ color:#fff; }
.pc-carte{ display:block; width:100%; margin-top:10px; padding:12px; border-radius:13px; border:1px solid rgba(240,180,41,.7); background:transparent; color:#FFD36B; font-family:inherit; font-weight:700; font-size:.95rem; line-height:1.2; cursor:pointer; }
"""
C.write_text(css, encoding='utf-8')

# --- règles
H = pathlib.Path('index.html'); h = H.read_text(encoding='utf-8')
assert 'patch365' not in h
h = rep(h, """une, rien ne change ; <b>deux ou plus, +5 %</b>.</p><!-- lot 8/11 -->""",
"""une, rien ne change ; <b>deux ou plus, +5 %</b>.</p><!-- lot 8/11 -->
            <p><b>Bonus de débutant</b> : pendant tes 7 premiers jours, et jusqu'à ta première conquête, chaque assaut a <b>au moins 85 %</b> de chances, même en prudent et même à distance. Une Forteresse garde son effet ; <b>aucun bonus contre une commune en garnison</b>. Ensuite, tout redevient normal.</p><!-- patch365 -->""")
H.write_text(h, encoding='utf-8')
print('patch365 appliqué')
