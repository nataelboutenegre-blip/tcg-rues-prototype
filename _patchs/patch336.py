# patch336 (4/11/2026) : les nouveaux commencent au Front, et leur première
# conquête est guidée (aperçu validé « parfait »).
# Lecture du 4/11 : les nouveaux qui conquièrent une commune dans leurs 24
# premières heures reviennent à 86 % le lendemain, les autres à 16 %.
# - Un compte neuf arrive en mode Front ; l'accueil parle du Front et son
#   bouton ouvre directement le paquet gratuit du Front (le guide en 6 bulles
#   n'est plus lancé, il reste dans « Revoir le guide »).
# - Après un paquet du Front, tant que « Premiers pas » n'a pas d'attaque
#   gagnée : une fiche propose la cible la plus facile (celle de Premiers pas),
#   avec les vraies chances (apercu_attaque), l'énergie, les 3 victoires et le
#   délai. « Lancer l'assaut » ouvre le panneau d'attaque sur la carte.
# - Un encart suit la série (x / 3, prochain assaut) sur Territoire et Combat,
#   jusqu'à la première conquête.
# - Première conquête : on fête, puis on propose 3 clans qui recrutent (ceux
#   qui ont des communes près des siennes d'abord) ; « Postuler » ouvre le clan
#   dans l'onglet Clan. Déjà en clan : on propose la Fonderie.
# - Étapes notées dans accueil_etapes : pc_accueil, pc_vu, pc_lancer,
#   pc_autre, pc_plustard, pc_abandon, pc_fete, pc_clan.
import pathlib

def ouvrir(nom):
    return pathlib.Path(nom), pathlib.Path(nom).read_text(encoding='utf-8')

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

# ===================================================================== index
F, s = ouvrir('index.html')
s = rep(s, """    <p class="acc-accroche">Les 35 000 communes de France sont des cartes à collectionner.<br>Une commune n'appartient qu'à un seul joueur à la fois.</p>
    <div class="acc-etapes">
      <div class="acc-etape"><span class="acc-num">1</span><div><b>Ouvre des paquets</b><span>5 vraies communes à chaque fois. Plus une ville est peuplée, plus elle est rare.</span></div></div>
      <div class="acc-etape"><span class="acc-num">2</span><div><b>Construis ton territoire</b><span>Tes communes s'affichent sur la carte de France et se rejoignent quand elles sont voisines.</span></div></div>
      <div class="acc-etape"><span class="acc-num">3</span><div><b>Attaque et défends</b><span>Prends les communes des autres joueurs — d'autant plus facilement qu'elles sont près de chez toi — et protège les tiennes.</span></div></div>
    </div>""",
"""    <p class="acc-accroche">Les 35 000 communes de France, une seule carte pour tous les joueurs. Chaque commune n'appartient qu'à un seul joueur.</p>
    <div class="acc-etapes">
      <div class="acc-etape"><span class="acc-num">1</span><div><b>Ouvre ton premier paquet</b><span>5 vraies communes, à toi sur la carte.</span></div></div>
      <div class="acc-etape"><span class="acc-num">2</span><div><b>Prends ta première commune</b><span>3 victoires et elle est à toi. Plus elle est près des tiennes, plus c'est facile.</span></div></div>
      <div class="acc-etape"><span class="acc-num">3</span><div><b>Rejoins un clan</b><span>À plusieurs, on ne s'attaque pas et on s'échange des communes.</span></div></div>
    </div>""")
s = rep(s, """      <span>Tu commences avec <b>100 TerraPoints</b> et <b>3 paquets gratuits</b>. Un nouveau paquet arrive toutes les 20 minutes.</span>""",
"""      <span>Tes paquets du Front sont <b>gratuits</b> : un nouveau toutes les <b>20 minutes</b>.</span>""")
s = rep(s, """      <button id="accueilPasser">Passer</button>
    </div>
  </div>
</div>""", """      <button id="accueilPasser">Passer</button>
    </div>
    <p class="acc-terra">Ta collection Terra t'attend aussi, en haut de l'écran.</p>
  </div>
</div>
<!-- patch336 : la première conquête guidée -->
<div class="pc-voile" id="pcVoile" hidden><div class="pc-boite" id="pcBoite" role="dialog" aria-modal="true" aria-label="Ta première conquête"></div></div>
<div class="pc-suivi" id="pcSuivi" hidden></div>""")
F.write_text(s, encoding='utf-8')

# ===================================================================== style
F, s = ouvrir('style.css')
s += """
/* patch336 : la première conquête guidée */
.acc-terra{ position:relative; text-align:center; font-size:.76rem; color:#7F91AB; margin:10px 0 0; }
.pc-voile{ position:fixed; inset:0; z-index:65; background:rgba(5,12,24,.72); display:flex; align-items:flex-end; justify-content:center; opacity:0; transition:opacity .18s; }
.pc-voile[hidden]{ display:none; }
.pc-voile.ouvert{ opacity:1; }
.pc-boite{ position:relative; width:min(460px,100%); max-height:92vh; overflow:auto; background:var(--nuit-2); color:#fff; text-align:left;
  border:1px solid rgba(240,180,41,.45); border-bottom:0; border-radius:22px 22px 0 0; padding:10px 18px calc(18px + env(safe-area-inset-bottom));
  box-shadow:0 -20px 40px rgba(0,0,0,.5); transform:translateY(24px); transition:transform .22s cubic-bezier(.2,.8,.3,1.1); }
.pc-voile.ouvert .pc-boite{ transform:none; }
.pc-boite.fete{ border-color:rgba(43,212,139,.5); overflow-x:hidden; }
.pc-poignee{ width:42px; height:5px; border-radius:9px; background:rgba(169,188,212,.35); margin:0 auto 12px; }
.pc-kicker{ font-size:.7rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:#FFB27A; }
.pc-titre{ font:900 1.7rem/1 var(--titre); margin:4px 0 12px; }
.pc-cible{ display:flex; gap:12px; align-items:center; background:rgba(10,22,40,.5); border:1px solid rgba(169,188,212,.18); border-radius:14px; padding:12px; }
.pc-vign{ width:50px; height:50px; border-radius:10px; flex:none; display:grid; place-items:center; font:900 1.15rem var(--titre); color:#fff; background:var(--c, #7E8BA0); }
.pc-cible b{ display:block; font-size:1rem; }
.pc-cible small{ display:block; font-size:.76rem; color:var(--brume); margin-top:2px; line-height:1.35; }
.pc-chip{ display:inline-block; font-size:.66rem; font-weight:700; padding:2px 8px; border-radius:99px; background:rgba(126,139,160,.25); color:#C9D3E0; margin-right:5px; }
.pc-chiffres{ display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:12px 0; }
.pc-chiffres div{ background:rgba(10,22,40,.45); border-radius:12px; padding:10px 6px; text-align:center; }
.pc-chiffres b{ display:block; font:900 1.6rem/1 var(--titre); }
.pc-chiffres b.ok{ color:#2BD48B; } .pc-chiffres b.moyen{ color:#F0B429; } .pc-chiffres b.dur{ color:#E5484D; }
.pc-chiffres span{ display:block; font-size:.7rem; color:var(--brume); margin-top:4px; }
.pc-txt{ font-size:.8rem; color:var(--brume); line-height:1.45; margin:0 0 14px; }
.pc-txt b{ color:#fff; }
.pc-go{ display:block; width:100%; font:800 1.3rem/1 var(--titre); letter-spacing:.02em; background:var(--c-legendaire); color:var(--encre); border:0; border-radius:13px; padding:14px; box-shadow:0 5px 0 #B7791F; cursor:pointer; }
.pc-go:active{ transform:translateY(4px); box-shadow:0 1px 0 #B7791F; }
.pc-sec{ display:flex; justify-content:space-between; gap:12px; margin-top:12px; }
.pc-sec button{ background:none; border:0; padding:4px 0; color:var(--brume); font:inherit; font-size:.8rem; text-decoration:underline; cursor:pointer; }
.pc-eclat{ position:absolute; left:50%; top:-150px; width:420px; height:420px; margin-left:-210px; background:radial-gradient(circle, rgba(43,212,139,.22), transparent 65%); pointer-events:none; }
.pc-bravo{ position:relative; font:900 2.1rem/1 var(--titre); text-align:center; margin:6px 0 6px; }
.pc-sous{ position:relative; text-align:center; color:var(--brume); font-size:.9rem; margin:0 0 12px; }
.pc-sous b{ color:#fff; }
.pc-gains{ position:relative; display:flex; justify-content:center; flex-wrap:wrap; gap:7px; margin-bottom:14px; }
.pc-gains span{ font-size:.75rem; font-weight:700; padding:5px 10px; border-radius:99px; background:rgba(240,180,41,.13); border:1px solid rgba(240,180,41,.35); color:#FFD98A; }
.pc-pp{ position:relative; display:flex; align-items:center; gap:10px; font-size:.75rem; color:var(--brume); margin-bottom:14px; }
.pc-pp .seg{ flex:1; display:grid; grid-template-columns:repeat(4,1fr); gap:4px; }
.pc-pp .seg i{ height:5px; border-radius:3px; background:rgba(169,188,212,.18); }
.pc-pp .seg i.on{ background:#2BD48B; }
.pc-pp b{ color:#fff; }
.pc-sep{ position:relative; border-top:1px solid rgba(169,188,212,.14); margin:0 -18px 12px; }
.pc-st{ position:relative; font:900 1.3rem/1 var(--titre); margin:0 0 4px; }
.pc-ss{ position:relative; font-size:.78rem; color:var(--brume); margin:0 0 8px; line-height:1.4; }
.pc-clan{ position:relative; display:flex; align-items:center; gap:10px; padding:9px 0; border-top:1px solid rgba(169,188,212,.1); }
.pc-clan .qui{ min-width:0; flex:1; }
.pc-clan b{ display:block; font-size:.88rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.pc-clan small{ display:block; font-size:.72rem; color:var(--brume); }
.pc-clan small .rec{ color:#5BE3A6; font-weight:700; }
.pc-postuler{ flex:none; font:inherit; font-size:.76rem; font-weight:700; padding:7px 12px; border-radius:99px; border:0; background:#E8833A; color:#fff; cursor:pointer; }
.pc-vide{ font-size:.78rem; color:var(--brume); margin:6px 0 0; }
.pc-suivi{ position:fixed; z-index:39; left:12px; right:12px; bottom:calc(78px + env(safe-area-inset-bottom)); background:var(--nuit-2); color:#fff;
  border:1px solid rgba(232,131,58,.55); border-radius:16px; padding:11px 14px 12px; box-shadow:0 10px 30px rgba(0,0,0,.5); text-align:left; }
.pc-suivi[hidden]{ display:none; }
.pc-suivi .pc-s-h{ display:flex; justify-content:space-between; align-items:center; gap:8px; }
.pc-suivi .pc-s-h .pc-kicker{ font-size:.66rem; }
.pc-suivi .pc-s-x{ background:none; border:0; color:#7F91AB; font-size:1rem; padding:0 2px; cursor:pointer; line-height:1; }
.pc-suivi .pc-s-nom{ font-weight:700; font-size:.95rem; margin-top:2px; }
.pc-suivi .pc-s-pts{ display:flex; gap:6px; margin:8px 0 4px; }
.pc-suivi .pc-s-pts i{ flex:1; height:8px; border-radius:9px; background:rgba(169,188,212,.2); }
.pc-suivi .pc-s-pts i.on{ background:#2BD48B; }
.pc-suivi .pc-s-l{ display:flex; justify-content:space-between; align-items:center; gap:10px; margin-top:6px; padding:0; border:0; background:none; }
.pc-suivi .pc-s-l > span{ font-size:.8rem; color:var(--brume); }
.pc-suivi .pc-s-l > span b{ color:#fff; }
.pc-assaut{ flex:none; font:800 .95rem/1 var(--titre); letter-spacing:.03em; border-radius:11px; padding:10px 14px; border:0; background:var(--c-legendaire); color:var(--encre); cursor:pointer; white-space:nowrap; }
.pc-assaut:disabled{ background:var(--nuit-3); color:#9FB0C8; border:1px solid rgba(169,188,212,.25); cursor:default; }
.pc-suivi .pc-s-note{ font-size:.7rem; color:#8FA2BC; margin:7px 0 0; line-height:1.4; }
@media (min-width: 721px){
  .pc-voile{ align-items:center; padding:16px; }
  .pc-boite{ border-bottom:1px solid rgba(240,180,41,.45); border-radius:20px; padding-bottom:18px; }
  .pc-poignee{ display:none; }
  .pc-suivi{ left:auto; right:22px; bottom:22px; width:360px; }
}
"""
F.write_text(s, encoding='utf-8')

# ===================================================================== app.js
F, s = ouvrir('app.js')

# 1. un compte neuf arrive au Front
s = rep(s, """  voile.hidden = false;
  onbMarque('accueil_vu');   // patch324""",
"""  // patch336 : un compte neuf commence au Front
  if(!force && SAISON2 && modeJeu !== 'front'){
    const b = document.querySelector('#modeBascule [data-mode="front"]');
    if(b) b.click();
  }
  voile.hidden = false;
  onbMarque('accueil_vu');   // patch324""")

# 2. « Ouvrir mon premier paquet » : le paquet du Front, sans le guide
s = rep(s, """  onbMarque('accueil_ouvrir');   // patch324
  fermerAccueil(true);
  if(!guideDejaVu()) setTimeout(demarrerGuide, 280);""",
"""  onbMarque('accueil_ouvrir');   // patch324
  if(SAISON2){   // patch336 : droit au paquet du Front ; le guide reste dans les règles
    fermerAccueil(false);
    marquerGuideVu();
    onbMarque('pc_accueil');
    ppOuvrirPaquetFront();
    return;
  }
  fermerAccueil(true);
  if(!guideDejaVu()) setTimeout(demarrerGuide, 280);""")

# 3. Premiers pas : le paquet du Front devient une fonction, la cible peut en écarter
s = rep(s, """  if(quoi === 'paquet'){
    // patch324 : le premier paquet du Front (s2-86 ne coche plus l'étape avec du Terra)
    if(paquetEnCours){ notifier({ type: 'info', titre: 'Un paquet est en cours', texte: 'Retourne d’abord tes cartes, puis reviens ici.' }); return; }
    ncAller('front', 'tirage', async () => {""",
"""  if(quoi === 'paquet'){ ppOuvrirPaquetFront(); return; }   // patch336 : partagé avec l'accueil
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
// patch324 / patch336 : le premier paquet du Front (s2-86 ne coche plus l'étape avec du Terra)
function ppOuvrirPaquetFront(){
  {
    if(paquetEnCours){ notifier({ type: 'info', titre: 'Un paquet est en cours', texte: 'Retourne d’abord tes cartes, puis reviens ici.' }); return; }
    ncAller('front', 'tirage', async () => {""")
s = rep(s, """      else { if(b) b.scrollIntoView({ behavior: 'smooth', block: 'center' }); notifier({ type: 'info', titre: 'Paquet du Front', texte: 'Ton prochain paquet gratuit arrive bientôt : le compte à rebours est juste en dessous.' }); }
    });
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
}""",
"""      else { if(b) b.scrollIntoView({ behavior: 'smooth', block: 'center' }); notifier({ type: 'info', titre: 'Paquet du Front', texte: 'Ton prochain paquet gratuit arrive bientôt : le compte à rebours est juste en dessous.' }); }
    });
  }
}""")
s = rep(s, """function ppCible(){
  const maintenant = Date.now();""", """function ppCible(exclues){   // patch336 : exclues = codes déjà proposés
  const maintenant = Date.now();""")
s = rep(s, """    if(clanMembres.has(c.joueurId) || c.bouclierJusqua > maintenant) continue;
    let d = 300;""", """    if(clanMembres.has(c.joueurId) || c.bouclierJusqua > maintenant) continue;
    if(exclues && exclues.has(c.code)) continue;
    let d = 300;""")

# 4. fin d'un paquet du Front : la fiche « première conquête »
s = rep(s, """      loadPackStatus().then(proposerPaquetSuivant);
    }
  };
}""", """      loadPackStatus().then(proposerPaquetSuivant);
      if(!enTerra()) pcApresPaquet();   // patch336
    }
  };
}""")

# 5. après un assaut (carte et Combat)
s = rep(s, """    mettreEnSceneAssaut(cibleVue, r);
""", """    mettreEnSceneAssaut(cibleVue, r);
    pcApresAssaut(code, r);   // patch336
""")
s = rep(s, """        mettreEnSceneAssaut(cibleVueCombat, result);
""", """        mettreEnSceneAssaut(cibleVueCombat, result);
        pcApresAssaut(code, result);   // patch336
""")

# 6. le module
s = rep(s, """// ---------- patch322 : le bandeau de la réserve d'accueil (s2-76) ----------""",
r"""// ---------- patch336 : la première conquête guidée ----------
// Les nouveaux qui conquièrent une commune dans leurs 24 premières heures
// reviennent à 86 % le lendemain, les autres à 16 % (lecture du 4/11). Après
// son paquet du Front, un compte neuf (Premiers pas) se voit proposer la
// cible la plus facile ; un encart suit sa série jusqu'à la conquête, qu'on
// fête avant de lui proposer un clan qui recrute.
var PC = { exclues: new Set(), info: null, siege: null, siegeCode: null, siegeLu: 0, cle: '' };
const PC_CIBLE = 'tf-pc-cible', PC_FETE = 'tf-pc-fete', PC_PLUSTARD = 'tf-pc-plustard';
const PC_TP = { commun: 5, peucommun: 10, rare: 25, epique: 50, legendaire: 100 };
const PC_COULEUR = { commun: '#7E8BA0', peucommun: '#22A06B', rare: '#2F7CF6', epique: '#9B5CF6', legendaire: '#F0B429' };
function pcLire(k){ try{ return localStorage.getItem(k); }catch(e){ return null; } }
function pcEcrire(k, v){ try{ if(v == null) localStorage.removeItem(k); else localStorage.setItem(k, String(v)); }catch(e){} }
function pcMinSec(ms){ const t = Math.max(0, Math.ceil(ms / 1000)); return t >= 3600 ? formatDuree(ms) : Math.floor(t / 60) + ':' + String(t % 60).padStart(2, '0'); }
function pcVoile(){ return document.getElementById('pcVoile'); }
function pcOuvrir(html, fete){
  const v = pcVoile(), b = document.getElementById('pcBoite');
  if(!v || !b) return;
  b.className = 'pc-boite' + (fete ? ' fete' : '');
  b.innerHTML = html;
  v.hidden = false;
  requestAnimationFrame(() => v.classList.add('ouvert'));
  pcMajSuivi();
}
function pcFermer(){
  const v = pcVoile();
  if(!v || v.hidden) return;
  v.classList.remove('ouvert');
  setTimeout(() => { v.hidden = true; pcMajSuivi(); }, 180);
}
// après un paquet du Front : la fiche, une fois, tant qu'aucune attaque n'est gagnée
async function pcApresPaquet(){
  if(!SAISON2 || pcLire(PC_FETE) || pcLire(PC_CIBLE)) return;
  if(Date.now() - (Number(pcLire(PC_PLUSTARD)) || 0) < 6 * 3600 * 1000) return;
  await chargerPremiersPas();
  if(!PREMIERS_PAS || PREMIERS_PAS.attaque) return;
  if(othersMap.size < 50){ try{ await loadOthersPossessions(); }catch(e){} }
  setTimeout(pcProposer, 600);
}
async function pcProposer(){
  if(paquetEnCours || NC.ouvert) return;
  const c = ppCible(PC.exclues);
  if(!c) return;
  PC.info = c;
  onbMarque('pc_vu');
  pcOuvrir(pcFicheHtml(c, null));
  try{
    const { data, error } = await sb.rpc('apercu_attaque', { p_commune_code: c.code, p_intensite: intensiteChoisie });
    if(!error && data && data[0] && PC.info === c && !pcVoile().hidden) document.getElementById('pcBoite').innerHTML = pcFicheHtml(c, data[0]);
  }catch(e){}
}
function pcFicheHtml(c, a){
  const t = c.tier && c.tier.id ? c.tier.id : 'commun';
  const proche = maCommuneLaPlusProche(c.lat, c.lon);
  const km = proche ? Math.max(1, Math.round(proche.km)) : null;
  const ch = a ? Number(a.chances) : null;
  const cl = ch == null ? '' : ch >= 50 ? 'ok' : ch >= 35 ? 'moyen' : 'dur';
  const delai = DELAI_ATTAQUE_MS[t] || 0;
  return `<div class="pc-poignee"></div>
    <div class="pc-kicker">Premiers pas · étape 2 sur 4</div>
    <div class="pc-titre">Prends ta première commune</div>
    <div class="pc-cible"><div class="pc-vign" style="--c:${PC_COULEUR[t] || '#7E8BA0'}">${echapperHtml(String(c.nom || '?')[0].toUpperCase())}</div><div>
      <b>${echapperHtml(c.nom)} (${echapperHtml(c.dept || '')})</b>
      <small><span class="pc-chip">${echapperHtml(c.tier && c.tier.label ? c.tier.label : LIBELLE_TIER[t] || '')}</span>tenue par ${echapperHtml(c.pseudo || 'un joueur')}</small>
      ${proche ? `<small>${km <= 20 ? `À ${km} km de ${echapperHtml(proche.entry.nom)}, ta commune` : `À ${km} km de ta commune la plus proche : une attaque à distance`}</small>` : ''}</div></div>
    <div class="pc-chiffres">
      <div><b class="${cl}">${ch == null ? '…' : ch + ' %'}</b><span>de chances par assaut</span></div>
      <div><b>${ENERGIE_INTENSITE[intensiteChoisie] || 2} ⚡</b><span>par assaut (${echapperHtml(intensite().label.toLowerCase())})</span></div>
      <div><b>3</b><span>victoires pour la prendre</span></div>
    </div>
    <p class="pc-txt">Une défaite ne te fait <b>rien perdre</b> : ta série reste où elle en est.${delai ? ` Entre deux assauts sur cette commune : <b>${formatDuree(delai)}</b>.` : ''}</p>
    <button type="button" class="pc-go" data-pc-act="lancer" data-pc-code="${echapperTexte(c.code)}">Lancer l'assaut</button>
    <div class="pc-sec"><button type="button" data-pc-act="autre">Une autre cible</button><button type="button" data-pc-act="plustard">Plus tard</button></div>`;
}
function pcLancer(code){
  pcEcrire(PC_CIBLE, code);
  PC.siegeLu = 0;
  onbMarque('pc_lancer');
  pcFermer();
  ncAller('front', 'territoire', () => {
    const c = othersMap.get(code);
    if(c) voirCommuneSurCarte(c);
    setTimeout(() => { try{ ouvrirAttaque(code); }catch(e){} }, 450);
  });
}
// l'encart qui suit la série, sur Territoire et Combat
async function pcLireSiege(code){
  PC.siegeLu = Date.now(); PC.siegeCode = code;
  try{
    if(!window.__monId){ const { data: u } = await sb.auth.getUser(); window.__monId = u && u.user ? u.user.id : null; }
    const { data } = await sb.from('sieges').select('victoires_consecutives, dernier_round')
      .eq('attacker_id', window.__monId).eq('commune_code', code).maybeSingle();
    PC.siege = data || null;
  }catch(e){ PC.siege = null; }
  PC.cle = '';
  pcMajSuivi();
}
function pcMajSuivi(){
  const el = document.getElementById('pcSuivi');
  if(!el) return;
  const code = pcLire(PC_CIBLE);
  const cacher = () => { if(!el.hidden){ el.hidden = true; PC.cle = ''; } };
  if(!SAISON2 || !code || pcLire(PC_FETE) || modeJeu !== 'front') return cacher();
  const t = document.querySelector('.tab.active[data-tab]');
  if(!t || !['territoire', 'combat'].includes(t.dataset.tab)) return cacher();
  const pan = document.getElementById('mapPanneau'), fen = document.getElementById('fenetre'), v = pcVoile();
  if((t.dataset.tab === 'territoire' && pan && !pan.hidden) || (fen && !fen.hidden) || (v && !v.hidden) || NC.ouvert) return cacher();
  const c = othersMap.get(code);
  if(!c){
    if(collectionMap.has(code)) return cacher();   // prise : la fête arrive par pcApresAssaut
    if(othersMap.size > 50){ pcEcrire(PC_CIBLE, null); return cacher(); }   // redevenue libre
    return cacher();
  }
  if(PC.siegeCode !== code || Date.now() - PC.siegeLu > 30000){ if(Date.now() - PC.siegeLu > 3000) pcLireSiege(code); }
  const v3 = Math.min(2, Number(PC.siege && PC.siege.victoires_consecutives) || 0);
  const dernier = PC.siege && PC.siege.dernier_round ? new Date(PC.siege.dernier_round).getTime() : 0;
  const attente = Math.max(0, dernier + (DELAI_ATTAQUE_MS[c.tier && c.tier.id] || 0) - Date.now());
  const cle = code + '|' + v3 + '|' + (attente > 0);
  if(cle !== PC.cle){
    PC.cle = cle;
    const reste = 3 - v3;
    el.innerHTML = `<div class="pc-s-h"><span class="pc-kicker">Ta première conquête</span><span style="font-size:.75rem;color:var(--brume)">${v3} / 3 <button type="button" class="pc-s-x" data-pc-act="abandon" aria-label="Ne plus suivre cette cible">✕</button></span></div>
      <div class="pc-s-nom">${echapperHtml(c.nom)} (${echapperHtml(c.dept || '')})</div>
      <div class="pc-s-pts">${[0, 1, 2].map(i => `<i class="${i < v3 ? 'on' : ''}"></i>`).join('')}</div>
      <div class="pc-s-l"><span>${v3 ? `Encore <b>${reste} victoire${reste > 1 ? 's' : ''}</b> et elle est à toi.` : '<b>3 victoires</b> et elle est à toi.'}</span>
        <button type="button" class="pc-assaut" data-pc-act="assaut" ${attente > 0 ? 'disabled' : ''}>${attente > 0 ? 'Assaut dans <span data-pc-compte>' + pcMinSec(attente) + '</span>' : 'Assaut'}</button></div>
      <p class="pc-s-note">${echapperHtml(c.pseudo || 'Son propriétaire')} peut tenter de se défendre : s'il réussit, tu perds une victoire, rien de plus.</p>`;
  } else if(attente > 0){
    const cpt = el.querySelector('[data-pc-compte]');
    if(cpt) cpt.textContent = pcMinSec(attente);
  }
  el.hidden = false;
}
setInterval(() => { try{ pcMajSuivi(); }catch(e){} }, 1000);
// après chaque assaut : la série change, et la première conquête se fête
function pcApresAssaut(code, r){
  if(!SAISON2 || !r || pcLire(PC_FETE) || !pcLire(PC_CIBLE)) return;
  const c = othersMap.get(code) || {};
  const info = { code, nom: c.nom || code, dept: c.dept || '', tier: c.tier && c.tier.id ? c.tier.id : 'commun' };
  if(r.conquise){
    pcEcrire(PC_FETE, '1');
    pcEcrire(PC_CIBLE, null);
    // on attend que la fenêtre de l'assaut soit refermée
    const debut = Date.now();
    const attendre = () => {
      const fen = document.getElementById('fenetre');
      if((fen && !fen.hidden) || paquetEnCours){ if(Date.now() - debut < 180000) setTimeout(attendre, 400); return; }
      setTimeout(() => pcFeter(info), 250);
    };
    setTimeout(attendre, 600);
  } else if(code === pcLire(PC_CIBLE)){
    PC.siege = { victoires_consecutives: Number(r.victoires_consecutives) || 0, dernier_round: new Date().toISOString() };
    PC.siegeCode = code; PC.siegeLu = Date.now(); PC.cle = '';
  }
}
async function pcFeter(info){
  onbMarque('pc_fete', info.tier);
  const enClan = clanMembres.size > 0 || !!(clanCache && clanCache.moi && clanCache.moi.clan);
  const entete = (P) => {
    const faites = P ? ['paquet', 'attaque', 'clan', 'fonderie'].filter(k => P[k]).length : null;
    return `<div class="pc-eclat"></div>
    <div class="pc-poignee"></div>
    <div class="pc-bravo">Première conquête !</div>
    <p class="pc-sous"><b>${echapperHtml(info.nom)}${info.dept ? ' (' + echapperHtml(info.dept) + ')' : ''}</b> est à toi.</p>
    <div class="pc-gains"><span>+${PC_TP[info.tier] || 5} TP</span><span>+10 au classement</span></div>
    ${faites == null ? '' : `<div class="pc-pp"><span>Premiers pas</span><div class="seg">${[0, 1, 2, 3].map(i => `<i class="${i < faites ? 'on' : ''}"></i>`).join('')}</div><b>${faites} / 4</b></div>`}
    <div class="pc-sep"></div>`;
  };
  const pied = (gauche) => `<div class="pc-sec">${gauche}<button type="button" data-pc-act="fermer">Plus tard</button></div>`;
  if(enClan){
    await chargerPremiersPas();
    pcOuvrir(entete(PREMIERS_PAS) + `<p class="pc-st">Et maintenant, ta Fonderie ?</p>
      <p class="pc-ss">Gratuite, elle produit ${(BATIMENTS && BATIMENTS.production) || 10} lingots par jour pour construire des Forteresses.</p>
      <button type="button" class="pc-go" data-pc-act="fonderie">Construire ma Fonderie</button>` + pied('<span></span>'), true);
    return;
  }
  pcOuvrir(entete(null) + `<p class="pc-st">Et maintenant, un clan ?</p><p class="pc-ss">Chargement des clans qui recrutent…</p>`, true);
  const [, cl, cf] = await Promise.all([
    chargerPremiersPas(),
    sb.rpc('clans_classement').then(r => r, () => ({ error: true })),
    sb.rpc('clans_en_formation').then(r => r, () => ({ error: true })),
    typeof chargerCandidatures === 'function' ? chargerCandidatures() : null,
    clansCarte.size ? null : loadClansCarte(),
  ]);
  const tous = [].concat(cl && !cl.error ? cl.data || [] : [], cf && !cf.error ? cf.data || [] : [])
    .filter(x => x && x.clan_id && (Number(x.membres) || 0) < 8 && !candFerme(x.clan_id));
  // les clans qui ont des communes près des miennes passent devant
  const miennes = [...collectionMap.values()].filter(m => m.lat != null && m.lon != null);
  const pres = new Map();
  for(const o of othersMap.values()){
    const k = clansCarte.get(o.joueurId);
    if(!k || o.lat == null) continue;
    for(const m of miennes){
      if(Math.abs(m.lat - o.lat) > 0.5) continue;
      if(distanceKm(o.lat, o.lon, m.lat, m.lon) <= 30){ pres.set(k.tag, (pres.get(k.tag) || 0) + 1); break; }
    }
  }
  tous.sort((a, b) => (pres.get(b.tag) || 0) - (pres.get(a.tag) || 0) || (Number(b.membres) || 0) - (Number(a.membres) || 0));
  const trois = tous.slice(0, 3);
  const lignes = trois.map(x => `<div class="pc-clan">${blasonHtml(x.tag, x.couleur, true)}<div class="qui"><b>${echapperHtml(x.nom)}</b>
      <small><span class="rec">Recrute</span> · ${Number(x.membres) || 0} membre${(Number(x.membres) || 0) > 1 ? 's' : ''}${pres.get(x.tag) ? ' · près de tes communes' : ''}</small></div>
      <button type="button" class="pc-postuler" data-pc-act="clan" data-pc-clan="${echapperTexte(x.clan_id)}">Postuler</button></div>`).join('');
  if(pcVoile().hidden) return;   // fermée pendant le chargement
  document.getElementById('pcBoite').innerHTML = entete(PREMIERS_PAS) + `<p class="pc-st">Et maintenant, un clan ?</p>
    <p class="pc-ss">Entre membres, on ne s'attaque pas et on s'échange des communes.${lignes ? ' Ces clans recrutent :' : ''}</p>
    ${lignes || '<p class="pc-vide">Aucun clan ne recrute en ce moment : tu peux créer le tien dans l’onglet Clan.</p>'}
    ` + pied('<button type="button" data-pc-act="clans">Voir tous les clans</button>');
}
document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-pc-act]');
  if(!b) return;
  const a = b.dataset.pcAct;
  if(a === 'lancer') return pcLancer(b.dataset.pcCode);
  if(a === 'autre'){ if(PC.info) PC.exclues.add(PC.info.code); onbMarque('pc_autre'); return pcProposer(); }
  if(a === 'plustard'){ pcEcrire(PC_PLUSTARD, Date.now()); onbMarque('pc_plustard'); return pcFermer(); }
  if(a === 'fermer') return pcFermer();
  if(a === 'abandon'){ pcEcrire(PC_CIBLE, null); onbMarque('pc_abandon'); PC.cle = ''; return pcMajSuivi(); }
  if(a === 'assaut'){
    const code = pcLire(PC_CIBLE), c = code ? othersMap.get(code) : null;
    if(!c) return;
    ncAller('front', 'territoire', () => { voirCommuneSurCarte(c); setTimeout(() => { try{ ouvrirAttaque(code); }catch(err){} }, 450); });
    return;
  }
  if(a === 'clan'){ onbMarque('pc_clan'); pcFermer(); clanAOuvrir = b.dataset.pcClan; ncAller(null, 'clan'); return; }
  if(a === 'clans'){ onbMarque('pc_clan'); pcFermer(); ncAller(null, 'clan'); return; }
  if(a === 'fonderie'){ pcFermer(); ncAller('front', 'defense'); return; }
});
pcVoile()?.addEventListener('click', (e) => { if(e.target === pcVoile()) pcFermer(); });

// ---------- patch322 : le bandeau de la réserve d'accueil (s2-76) ----------""")
F.write_text(s, encoding='utf-8')
print('patch336 appliqué')
