# patch486 : l'Atelier devient le 3e onglet de la boutique (idée de Nataël, aperçu validé le 22/11 à 10 h 46).
# « Mes cartes » : ma composition, ce qui est à moi, ce qui se gagne en jouant (avec ma progression),
# ce qui est en vente. « Mon territoire » : ma couleur sur la carte (l'éditeur de motifs viendra ici).
# Dans la fiche d'une carte Terra, l'atelier de la carte se replie sur une ligne (on l'ouvre en la touchant).
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A, H, C = 'app.js', 'index.html', 'style.css'
VOL = '<button type="button" class="volet{} vol-atelier" data-volet="atelierbq" role="tab" aria-selected="{}" hidden>Atelier</button>'

# ---------- index.html : 3 volets, l'onglet caché et son panneau ----------
rep(H, """        <button type="button" class="volet actif" data-volet="boutique" role="tab" aria-selected="true">Avec mes TP</button>
        <button type="button" class="volet" data-volet="boutiqueeuros" role="tab" aria-selected="false">Objets TerraFront</button>
      </div>""", """        <button type="button" class="volet actif" data-volet="boutique" role="tab" aria-selected="true">Avec mes TP</button>
        <button type="button" class="volet" data-volet="boutiqueeuros" role="tab" aria-selected="false">Objets</button>
        """ + VOL.format('', 'false') + """
      </div>""")
rep(H, """        <button type="button" class="volet" data-volet="boutique" role="tab" aria-selected="false">Avec mes TP</button>
        <button type="button" class="volet actif" data-volet="boutiqueeuros" role="tab" aria-selected="true">Objets TerraFront</button>
      </div>""", """        <button type="button" class="volet" data-volet="boutique" role="tab" aria-selected="false">Avec mes TP</button>
        <button type="button" class="volet actif" data-volet="boutiqueeuros" role="tab" aria-selected="true">Objets</button>
        """ + VOL.format('', 'false') + """
      </div>""")
rep(H, """      <div id="bqeCorps"><p class="collection-empty">Chargement…</p></div>
    </section>""", """      <div id="bqeCorps"><p class="collection-empty">Chargement…</p></div>
    </section>

    <section class="tab-panel" id="panel-atelierbq"><!-- patch486 -->
      <h1>Boutique</h1>
      <div class="volets" role="tablist" aria-label="Boutique">
        <button type="button" class="volet" data-volet="boutique" role="tab" aria-selected="false">Avec mes TP</button>
        <button type="button" class="volet" data-volet="boutiqueeuros" role="tab" aria-selected="false">Objets</button>
        """ + VOL.format(' actif', 'true').replace(' hidden>', '>') + """
      </div>
      <div class="atb-seg" role="tablist" aria-label="Atelier">
        <button type="button" class="on" data-atb-vue="cartes" role="tab" aria-selected="true">Mes cartes</button>
        <button type="button" data-atb-vue="territoire" role="tab" aria-selected="false">Mon territoire</button>
      </div>
      <div id="atbCorps"><p class="collection-empty">Chargement…</p></div>
    </section>""")
rep(H, """      <div class="tab onglet-fusionne" data-tab="boutiqueeuros" aria-hidden="true"><div class="icon"></div>Boutique</div>""",
       """      <div class="tab onglet-fusionne" data-tab="boutiqueeuros" aria-hidden="true"><div class="icon"></div>Boutique</div>
      <div class="tab onglet-fusionne" data-tab="atelierbq" aria-hidden="true"><div class="icon"></div>Atelier</div>""")

# ---------- app.js ----------
rep(A, """const ONGLETS_FUSIONNES = ['defense', 'batiments', 'succes', 'cdj', 'radar', 'rafale', 'boutiqueeuros', 'personnaliser',""",
       """const ONGLETS_FUSIONNES = ['defense', 'batiments', 'succes', 'cdj', 'radar', 'rafale', 'boutiqueeuros', 'atelierbq', 'personnaliser',""")
rep(A, """const ONGLET_PARENT = { defense: 'combat', batiments: 'combat', succes: 'profil', cdj: 'qg', radar: 'qg', rafale: 'qg', boutiqueeuros: 'boutique',""",
       """const ONGLET_PARENT = { defense: 'combat', batiments: 'combat', succes: 'profil', cdj: 'qg', radar: 'qg', rafale: 'qg', boutiqueeuros: 'boutique', atelierbq: 'boutique',""")
rep(A, """    if(tab.dataset.tab === 'boutiqueeuros') loadBoutiqueEuros();   // patch175""",
       """    if(tab.dataset.tab === 'boutiqueeuros') loadBoutiqueEuros();   // patch175
    if(tab.dataset.tab === 'atelierbq') atbOuvrir();   // patch486""")
# le volet « Atelier » n'apparaît que si l'atelier est ouvert
rep(A, """    try{ if(gardeRobe && document.getElementById('grCorps')) renderGardeRobe(); }catch(e){}""",
       """    try{ if(gardeRobe && document.getElementById('grCorps')) renderGardeRobe(); }catch(e){}
    atbMajVolets();   // patch486""")
rep(A, """  const v = document.getElementById('bqVolets');
  if(v) v.hidden = !bqeAcces;""", """  const v = document.getElementById('bqVolets');
  if(v) v.hidden = !bqeAcces && !(ATL.lu && ATL.ouvert);   // patch486 : l'atelier suffit à montrer les volets
  atbMajVolets();""")
rep(A, """// ---------- l'écran de l'atelier ----------""", """// ---------- patch486 : l'onglet Atelier de la boutique ----------
let atbVue = 'cartes';
function atbMajVolets(){
  const ok = !!(ATL.lu && ATL.ouvert);
  document.querySelectorAll('.vol-atelier').forEach(b => { b.hidden = !ok; });
  const v = document.getElementById('bqVolets');
  if(v && ok) v.hidden = false;
}
async function atbOuvrir(){
  try{ if(ATL.pret) await ATL.pret; }catch(e){}
  try{ if(bqeAcces === null) await bqeVerifierAcces(); }catch(e){}
  atbRendre();
}
function atbBarre(v, total){
  const p = total ? Math.max(0, Math.min(100, Math.round(100 * v / total))) : 0;
  return `<div class="atb-barre"><i style="width:${p}%"></i></div>`;
}
function atbRendre(){
  const corps = document.getElementById('atbCorps');
  if(!corps) return;
  document.querySelectorAll('[data-atb-vue]').forEach(b => { const on = b.dataset.atbVue === atbVue; b.classList.toggle('on', on); b.setAttribute('aria-selected', String(on)); });
  if(atbVue === 'territoire'){
    corps.innerHTML = `<div class="atb-bloc atb-terr">${blocCouleur()}
      <p class="atb-note">Bientôt ici : <b>ton motif de territoire</b>, à composer toi-même (formes, lignes, symboles, couleurs).</p></div>`;
    return;
  }
  if(!ATL.lu || !ATL.ouvert){ corps.innerHTML = '<p class="collection-empty">L’atelier n’est pas encore ouvert.</p>'; return; }
  const P = ATL.progres || {}, S = ATL.seuils || {};
  const toutes = ATL_TOUTES_FAMILLES.flatMap(f => f.options.map(o => ({ ...o, fam: f.lib }))).filter(o => o.src !== 'inclus');
  const amoi = toutes.filter(o => atlPossede(o.id));
  const gagner = toutes.filter(o => !atlPossede(o.id) && (o.src === 'gagner' || o.src === 'pass'));
  const vente = toutes.filter(o => !atlPossede(o.id) && o.src === 'boutique');
  const progres = (o) => {
    if(o.id === 'encre') return [P.quetes, S.encre || 50, 'quêtes du jour réclamées'];
    if(o.id === 'lueur') return [P.serie, S.lueur || 7, 'jours de suite'];
    if(o.id === 'nuit') return [P.serie, S.nuit || 14, 'jours de suite'];
    if(o.id === 'postale') return [P.communes, S.postale || 200, 'communes Terra'];
    if(o.id === 'etat') return [P.departements, S.etat || 1, 'département fini'];
    if(o.id === 'tricolore') return [P.departements, S.tricolore || 3, 'départements finis'];
    return null;
  };
  const carte = (() => {
    try{
      const e = atlCartesEssai().slice().sort((a, b) => TIERS.findIndex(t => t.id === b.tier.id) - TIERS.findIndex(t => t.id === a.tier.id))[0];
      return e ? miniTerra({ ...e, exemplaires: 1, atelier: atlMienne(1) }) : '';
    }catch(x){ return ''; }
  })();
  const ligneGagner = (o) => {
    if(o.src === 'pass') return `<div class="atb-l"><b>${o.nom}</b><small>${echapperTexte(o.comment || 'Pass de saison')}, pass complet</small><span class="atb-v pass">Pass</span></div>`;
    const pr = progres(o);
    const fait = pr && pr[0] != null ? Math.min(pr[0], pr[1]) : null;
    return `<div class="atb-l"><b>${o.nom}</b><small>${echapperTexte(o.comment || '')}${fait != null ? ` · ${fmtNombre(fait)} / ${fmtNombre(pr[1])}` : ''}</small>`
      + (fait != null ? atbBarre(fait, pr[1]) : '') + `${fait != null && pr[1] - fait <= Math.max(1, Math.ceil(pr[1] * 0.2)) ? '<span class="atb-v proche">Bientôt</span>' : ''}</div>`;
  };
  corps.innerHTML = `
    <div class="atb-bloc atb-tete"><div class="atb-mini">${carte}</div><div>
      <p>Ta composition : <b>${echapperTexte(atlVide(ATL.moi) ? 'aucun effet' : atlResume(ATL.moi))}</b>${ATL.moi && ATL.moi.mode === 'choisies' ? ', sur les cartes que tu as choisies.' : ', sur toutes tes cartes Terra.'}</p>
      <button type="button" class="atb-btn" data-atb="ouvrir">Ouvrir l’atelier</button></div></div>
    <div class="atb-bloc"><div class="atb-h">À toi <small>${amoi.length} sur ${toutes.length}</small></div>
      ${amoi.length ? `<div class="atb-chips">${amoi.map(o => `<span class="atb-chip">${o.nom}</span>`).join('')}</div>` : '<p class="atb-note">Rien encore : joue pour gagner tes premiers éléments.</p>'}</div>
    ${gagner.length ? `<div class="atb-bloc"><div class="atb-h">À gagner en jouant</div>${gagner.map(ligneGagner).join('')}</div>` : ''}
    ${vente.length ? `<div class="atb-bloc"><div class="atb-h">En vente</div>${vente.map(o => `<div class="atb-l"><b>${o.nom}</b><small>${echapperTexte(o.fam)}</small>
      <span class="atb-v"><button type="button" class="atb-acheter" data-atb-acheter="${echapperTexte(o.id)}">${atlPrix(o)}</button></span></div>`).join('')}</div>` : ''}
    <p class="atb-note">Chaque élément s’obtient une seule fois et sert ensuite sur toutes tes cartes Terra. Jamais sur le Front.</p>`;
}
document.getElementById('panel-atelierbq').addEventListener('click', async (e) => {
  const vue = e.target.closest('[data-atb-vue]');
  if(vue){ atbVue = vue.dataset.atbVue; atbRendre(); return; }
  if(e.target.closest('[data-atb="ouvrir"]')){ atlOuvrir(); return; }
  const ach = e.target.closest('[data-atb-acheter]');
  if(ach){
    const o = ATL_TOUTES_FAMILLES.flatMap(f => f.options).find(x => x.id === ach.dataset.atbAcheter);
    try{ await bqeVerifierAcces(); }catch(err){}
    const art = o && atlArticle(o);
    if(!bqeAcces || !art){ notifier({ type: 'erreur', titre: 'Indisponible', texte: 'Cet élément n’est pas en vente pour le moment.' }); return; }
    bqeOuvrirFiche(art.id, 'atelier');
    return;
  }
  const pc = e.target.closest('[data-pf="couleur"]');   // ma couleur, comme dans le profil
  if(pc){ await choisirCouleur(pc.dataset.couleur); atbRendre(); return; }
  const dr = e.target.closest('[data-pf="dore"]');
  if(dr){
    try{ localStorage.setItem(CLE_DORE, dr.checked ? '1' : '0'); }catch(err){}
    appliquerCouleurMoi();
    try{ renderMapOverlay(); }catch(err){}
  }
});

// ---------- l'écran de l'atelier ----------""")
# la fiche d'une carte : l'atelier replié sur une ligne
rep(A, """  return `<div class="dc-choix atl-fc" data-atl-fc="${echapperTexte(code)}">${atlFicheInterieur(code)}</div>`;""",
       """  return `<div class="dc-choix atl-fc replie" data-atl-fc="${echapperTexte(code)}">${atlFicheInterieur(code)}</div>`;   // patch486 : replié""")
rep(A, """document.getElementById('pfCorps').addEventListener('click', (e) => {""", """// patch486 : l'atelier d'une carte s'ouvre en touchant sa ligne
document.addEventListener('click', (e) => {
  const t = e.target.closest('.atl-fc .dc-tete');
  if(!t) return;
  const b = t.closest('.atl-fc');
  b.classList.toggle('replie');
});
document.getElementById('pfCorps').addEventListener('click', (e) => {""")

# le choix du dos de la fiche : le premier .dc-choix pouvait être l'atelier de la carte (rangée jamais remplie)
rep(A, """  remplirChoixDos(boite.querySelector('.dc-choix'), (cle) => majDosC3d(c3d, cle, true));""",
       """  remplirChoixDos(boite.querySelector('.dc-choix[data-dc-src]'), (cle) => majDosC3d(c3d, cle, true));   // patch486""")

# ---------- style.css ----------
rep(C, """/* patch484 : passer le flambeau */""", """/* patch486 : l'onglet Atelier de la boutique */
.atb-seg{ display:flex; width:100%; box-sizing:border-box; background:rgba(23,44,75,.9); border-radius:14px; padding:4px; gap:4px; margin:12px 0 14px; }
.atb-seg button{ flex:1 1 0; white-space:nowrap; font:inherit; font-weight:600; font-size:.95rem; color:#A9BCD4; background:none; border:0; border-radius:10px; padding:9px 6px; cursor:pointer; }
.atb-seg button.on{ background:#F1F5F9; color:#0F1F38; }
.atb-bloc{ background:rgba(23,44,75,.9); border:1px solid #284268; border-radius:16px; padding:14px; margin-bottom:12px; }
.atb-tete{ display:flex; gap:14px; align-items:center; }
.atb-mini{ flex:none; width:84px; } .atb-mini .mini{ width:84px; }
.atb-tete p{ margin:0 0 10px; color:#A9BCD4; font-size:.92rem; line-height:1.4; } .atb-tete p b{ color:#F1F5F9; }
.atb-btn{ font:inherit; font-weight:700; font-size:.95rem; background:#F0B429; color:#1A1404; border:0; border-radius:12px; padding:10px 16px; cursor:pointer; }
.atb-h{ display:flex; justify-content:space-between; align-items:baseline; margin:0 0 10px; font-weight:700; }
.atb-h small{ font-weight:500; color:#A9BCD4; font-size:.82rem; }
.atb-chips{ display:flex; flex-wrap:wrap; gap:6px; }
.atb-chip{ font-size:.85rem; font-weight:600; background:rgba(74,222,128,.1); color:#8EE3B8; border:1px solid rgba(74,222,128,.3); border-radius:999px; padding:4px 10px; }
.atb-l{ display:grid; grid-template-columns:1fr auto; gap:2px 10px; padding:10px 0; border-top:1px solid rgba(169,188,212,.12); align-items:center; }
.atb-h + .atb-l{ border-top:0; padding-top:2px; }
.atb-l > b{ grid-column:1; } .atb-l > small{ grid-column:1; color:#A9BCD4; font-size:.82rem; }
.atb-l .atb-v{ grid-row:1 / 4; grid-column:2; font-size:.85rem; font-weight:700; color:#F0B429; text-align:right; }
.atb-l .atb-v.pass{ color:#C4B5FD; } .atb-l .atb-v.proche{ color:#8EE3B8; }
.atb-barre{ grid-column:1; height:5px; border-radius:3px; background:rgba(169,188,212,.15); overflow:hidden; margin-top:4px; }
.atb-barre i{ display:block; height:100%; background:#8EE3B8; border-radius:3px; }
.atb-acheter{ font:inherit; font-size:.85rem; font-weight:700; color:#1A1404; background:#F0B429; border:0; border-radius:10px; padding:7px 12px; cursor:pointer; }
.atb-note{ font-size:.82rem; color:#A9BCD4; margin:10px 0 0; line-height:1.45; }
.atb-terr .pf-bloc{ background:none; border:0; padding:0; margin:0; }
/* la fiche d'une carte : l'atelier replié sur une ligne */
.atl-fc .dc-tete{ cursor:pointer; }
.atl-fc.replie > :not(.dc-tete){ display:none !important; }
.atl-fc .dc-tete::after{ content:'›'; margin-left:8px; color:#A9BCD4; transition:transform .15s; display:inline-block; }
.atl-fc:not(.replie) .dc-tete::after{ transform:rotate(90deg); }
/* patch484 : passer le flambeau */""")
print('patch486 : fini')
