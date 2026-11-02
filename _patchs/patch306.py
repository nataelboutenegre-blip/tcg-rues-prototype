# patch306 : « Premiers pas » pour les nouveaux joueurs (s2-74)
# Une carte en haut du Tirage (Terra et Front), pour les comptes de moins de 14 jours :
#   1. ouvrir son premier paquet      → bouton « Ouvrir » (le paquet gratuit)
#   2. gagner sa première attaque     → « Attaquer » : passe au Front et ouvre l'attaque
#                                        sur une cible facile près de ses communes
#   3. rejoindre un clan ou le créer  → « Voir les clans »
#   4. construire sa Fonderie         → « Comment ? » (Défendre › Bâtiments)
# Les étapes sont cochées par le serveur. Les 4 faites : « Récupérer » (1 paquet Terra
# en plus et 10 lingots). Sans s2-74, rien ne s'affiche et rien ne casse.
import json, pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

# ---------------------------------------------------------------- index.html
f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
assert 'patch306' not in s
s = rep(s, """      <button type="button" class="obj-bandeau" id="objBandeau" hidden aria-haspopup="dialog"></button><!-- patch284 -->
""", """      <button type="button" class="obj-bandeau" id="objBandeau" hidden aria-haspopup="dialog"></button><!-- patch284 -->
      <div class="pp" id="premiersPas" hidden></div><!-- patch306 -->
""")
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- app.js
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch306' not in s

s = s.rstrip('\n') + r"""

// ---------- patch306 : Premiers pas (s2-74) ----------
// Les nouveaux qui combattent le 1er jour reviennent ; les autres presque jamais.
// La carte les mène à leur première attaque. Le serveur coche les étapes.
let PREMIERS_PAS = null, ppMinuteur = null;
async function chargerPremiersPas(){
  if(!SAISON2) return;
  try{
    const { data, error } = await sb.rpc('premiers_pas');
    PREMIERS_PAS = !error && data && data.eligible ? data : null;
  }catch(e){ PREMIERS_PAS = null; }
  renderPremiersPas();
}
// après une action qui peut cocher une étape : relire un peu plus tard (une seule fois)
function ppRelire(delai){
  if(!PREMIERS_PAS) return;
  clearTimeout(ppMinuteur);
  ppMinuteur = setTimeout(chargerPremiersPas, delai || 1500);
}
// une cible facile : la commune d'un autre joueur la plus proche des miennes, plutôt commune
function ppCible(){
  const maintenant = Date.now();
  const miennes = [...collectionMap.values()].filter(m => m.lat != null && m.lon != null && !estOutremerCode(m.code));
  const rangT = (t) => ({ commun: 0, peucommun: 1, rare: 2, epique: 3, legendaire: 4 })[t && t.id] ?? 2;
  let meilleure = null, score = Infinity;
  for(const c of othersMap.values()){
    if(c.lat == null || c.lon == null || estOutremerCode(c.code)) continue;
    if(clanMembres.has(c.joueurId) || c.bouclierJusqua > maintenant) continue;
    let d = 300;
    for(const m of miennes){
      if(Math.abs(m.lat - c.lat) > 1.5) continue;
      const x = distanceKm(c.lat, c.lon, m.lat, m.lon);
      if(x < d) d = x;
    }
    const sc = d + rangT(c.tier) * 15;
    if(sc < score){ score = sc; meilleure = c; }
  }
  return meilleure;
}
function renderPremiersPas(){
  const el = document.getElementById('premiersPas');
  if(!el) return;
  const P = PREMIERS_PAS;
  el.hidden = !P;
  if(!P) return;
  const cible = P.attaque ? null : ppCible();
  const etapes = [
    ['paquet', 'Ouvre ton premier paquet', '5 vraies communes, à leur place sur la carte', 'Ouvrir'],
    ['attaque', 'Gagne ta première attaque', cible ? `Une cible facile près de chez toi : ${echapperHtml(cible.nom)} (${echapperHtml(cible.dept)})` : 'Choisis une commune proche dans l’onglet Combat', 'Attaquer'],
    ['clan', 'Rejoins un clan ou crée le tien', 'Les membres ne s’attaquent pas entre eux, et s’échangent des communes', 'Voir les clans'],
    ['fonderie', 'Construis ta Fonderie', `Gratuite : ${(BATIMENTS && BATIMENTS.production) || 10} lingots par jour pour tes bâtiments`, 'Comment ?'],
  ];
  const faites = etapes.filter(e => P[e[0]]).length;
  const premiere = etapes.findIndex(e => !P[e[0]]);
  const R = P.recompense || { paquets: 1, lingots: 10 };
  const lots = `${R.paquets} paquet Terra en plus et ${R.lingots} lingots`;
  el.innerHTML = `<div class="pp-haut"><span class="pp-t">Premiers pas</span><span class="pp-n">${faites} / 4</span></div>
    <p class="pp-sous">${faites === 4 ? 'Bravo, tout est fait : ta récompense t’attend.' : 'Fais ces 4 choses pour bien démarrer ta conquête.'}</p>
    <div class="pp-seg">${etapes.map(e => `<i class="${P[e[0]] ? 'on' : ''}"></i>`).join('')}</div>
    ${etapes.map((e, i) => `<div class="pp-e${P[e[0]] ? ' fait' : i === premiere ? ' cours' : ''}"><span class="pp-c">${P[e[0]] ? '✓' : i + 1}</span>
      <span class="pp-l"><b>${e[1]}</b><small>${e[2]}</small></span>
      ${P[e[0]] ? '<span></span>' : `<button type="button" class="pp-go${i === premiere ? ' fort' : ''}" data-pp="${e[0]}">${e[3]}</button>`}</div>`).join('')}
    ${faites === 4
      ? `<button type="button" class="pp-reclamer" data-pp="reclamer">🎁 Récupérer : ${lots}</button>`
      : `<div class="pp-recomp"><span class="gift">🎁</span><span>Les 4 faites : <b>${lots}</b></span></div>`}`;
}
async function ppAction(quoi, bouton){
  if(quoi === 'paquet'){
    const b = document.getElementById('openFreeBtn');
    if(b && !b.disabled) b.click();
    else { if(b) b.scrollIntoView({ behavior: 'smooth', block: 'center' }); notifier({ type: 'info', titre: 'Paquet', texte: 'Ton prochain paquet gratuit arrive bientôt : le compte à rebours est juste en dessous.' }); }
    return;
  }
  if(quoi === 'attaque'){
    ncAller('front', 'territoire', () => {
      const c = ppCible();
      if(!c){ ncAller('front', 'combat'); return; }
      voirCommuneSurCarte(c);
      setTimeout(() => { try{ ouvrirAttaque(c.code); }catch(e){} }, 450);
    });
    return;
  }
  if(quoi === 'clan'){ ncAller(null, 'clan'); return; }
  if(quoi === 'fonderie'){ ncAller('front', 'defense'); return; }
  if(quoi === 'reclamer'){
    bouton.disabled = true;
    const { data, error } = await sb.rpc('premiers_pas_reclamer');
    if(error){ bouton.disabled = false; notifier({ type: 'erreur', titre: 'Premiers pas', texte: messageLisible(error.message) }); return; }
    notifier({ type: 'succes', titre: 'Premiers pas terminés !', texte: `+${(data && data.paquets) || 1} paquet Terra et +${(data && data.lingots) || 10} lingots. Bonne conquête !` });
    PREMIERS_PAS = null; renderPremiersPas();
    loadPackStatus();
    if(typeof chargerBatiments === 'function') chargerBatiments();
  }
}
document.getElementById('premiersPas')?.addEventListener('click', (e) => {
  const b = e.target.closest('[data-pp]');
  if(b) ppAction(b.dataset.pp, b);
});
"""

# chargement au démarrage, avec les quêtes
s = rep(s, """  parrainDeclare.then(parrainageDuJour);
  loadObjectifs();
""", """  parrainDeclare.then(parrainageDuJour);
  loadObjectifs();
  chargerPremiersPas();   // patch306
""")
# retour sur le Tirage : la carte se met à jour (et la cible proposée aussi)
s = rep(s, """    if(tab.dataset.tab === 'tirage'){ loadPackStatus(); loadObjectifs(); }""",
           """    if(tab.dataset.tab === 'tirage'){ loadPackStatus(); loadObjectifs(); ppRelire(300); }   // patch306""")
# après un paquet (les cartes arrivent juste après le paiement)
s = rep(s, """async function loadPackStatus(){
  if(enTerra()) return loadPackStatusTerra();""",
"""async function loadPackStatus(){
  if(PREMIERS_PAS && !PREMIERS_PAS.paquet) ppRelire(4000);   // patch306
  if(enTerra()) return loadPackStatusTerra();""")
# après une victoire
s = rep(s, """    mettreEnSceneAssaut(cibleVue, r);
    if(r.conquise){""",
"""    mettreEnSceneAssaut(cibleVue, r);
    if((r.gagne || r.conquise) && PREMIERS_PAS && !PREMIERS_PAS.attaque) ppRelire(800);   // patch306
    if(r.conquise){""")
# après une construction
s = rep(s, """  else notifier({ type: 'succes', titre: nom + ' en construction', texte: `Prête dans ${btReglage('construction_h', 6)} h.` });""",
"""  else { notifier({ type: 'succes', titre: nom + ' en construction', texte: `Prête dans ${btReglage('construction_h', 6)} h.` }); ppRelire(800); }   // patch306""")
# après une action de clan (créer, rejoindre)
s = rep(s, """  if(succes) notifier({ type: 'succes', titre: succes });
  clanCache = clanCache || { classement: [] };""",
"""  if(succes) notifier({ type: 'succes', titre: succes });
  ppRelire(800);   // patch306
  clanCache = clanCache || { classement: [] };""")
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- style.css
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch306' not in s
s = s.rstrip('\n') + """

/* patch306 : Premiers pas */
.pp{ background:linear-gradient(160deg,rgba(232,131,58,.16),rgba(15,31,56,.6) 55%); border:1px solid rgba(232,131,58,.45); border-radius:14px; padding:14px 14px 12px; color:#fff; margin:0 0 14px; text-align:left; }
.pp[hidden]{ display:none; }
.pp-haut{ display:flex; align-items:baseline; justify-content:space-between; gap:10px; }
.pp-t{ font-family:var(--titre); font-weight:900; font-size:1.05rem; letter-spacing:.01em; }
.pp-n{ font-size:.78rem; color:#FFB27A; font-weight:700; white-space:nowrap; }
.pp-sous{ font-size:.76rem; color:#A9BCD4; margin:3px 0 10px; }
.pp-seg{ display:grid; grid-template-columns:repeat(4,1fr); gap:4px; margin-bottom:10px; }
.pp-seg i{ height:5px; border-radius:3px; background:rgba(169,188,212,.18); }
.pp-seg i.on{ background:#2BD48B; }
.pp-e{ display:grid; grid-template-columns:26px minmax(0,1fr) auto; gap:10px; align-items:center; padding:8px 0; border-top:1px solid rgba(169,188,212,.1); }
.pp-c{ width:24px; height:24px; border-radius:50%; display:grid; place-items:center; font-size:.75rem; font-weight:800; border:1.5px solid rgba(169,188,212,.35); color:#A9BCD4; box-sizing:border-box; }
.pp-e.fait .pp-c{ background:#2BD48B; border-color:#2BD48B; color:#0F1F38; }
.pp-e.cours .pp-c{ border-color:#E8833A; color:#FFB27A; }
.pp-l b{ display:block; font-size:.86rem; }
.pp-l small{ display:block; font-size:.72rem; color:#A9BCD4; margin-top:2px; line-height:1.35; }
.pp-e.fait .pp-l b{ color:#A9BCD4; text-decoration:line-through; text-decoration-color:rgba(169,188,212,.5); }
.pp-go{ font:inherit; font-size:.74rem; font-weight:700; border-radius:999px; padding:7px 12px; border:1px solid rgba(232,131,58,.6); background:rgba(232,131,58,.18); color:#fff; white-space:nowrap; cursor:pointer; }
.pp-go.fort{ background:#E8833A; border-color:#E8833A; }
.pp-recomp{ display:flex; align-items:center; gap:10px; margin-top:8px; padding:9px 11px; border-radius:10px; background:rgba(10,22,40,.45); border:1px dashed rgba(255,178,122,.45); font-size:.78rem; color:#FFD9B8; }
.pp-recomp b{ color:#fff; }
.pp-recomp .gift{ font-size:1.1rem; }
.pp-reclamer{ display:block; width:100%; margin-top:10px; padding:11px 12px; border-radius:10px; border:0; background:#2BD48B; color:#0F1F38; font:inherit; font-weight:800; font-size:.88rem; cursor:pointer; }
.pp-reclamer:disabled{ opacity:.6; cursor:default; }
"""
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- nouveautés
f = pathlib.Path('data/nouveautes.json'); d = json.loads(f.read_text(encoding='utf-8'))
e = next((x for x in d if x['date'] == '2026-11-02'), None)
if e is None:
    e = {'date': '2026-11-02', 'nouveautes': [], 'correctifs': []}
    d.insert(0, e)
e['nouveautes'].insert(0, '🧭 Nouveaux joueurs : une carte « Premiers pas » (4 étapes, et 1 paquet Terra + 10 lingots à la clé)')
f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch306 appliqué')
