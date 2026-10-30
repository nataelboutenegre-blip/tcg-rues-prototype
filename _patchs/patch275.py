# patch275 : idées d'Arkhannou (aperçu validé le 30/10 : « parfait ! »)
#  1. le blason du clan à côté des pseudos : classement (podium, liste, ligne repliée), légende « Joueurs » de la carte, journal
#  2. Terra › Échange : une pastille « Toutes » (toutes raretés mêlées ; un choix d'un côté resserre l'autre sur sa rareté)
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:90])
    return s.replace(a, b)

# ---------------- app.js ----------------
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch275' not in s

# --- 1. blasons : fonctions, juste après blasonHtml ---
a = """function blasonHtml(tag, couleur, petit){
  const bl = BLASONS.get(tag);   // patch253"""
s = rep(s, a, """// patch275 : le blason du clan à côté d'un pseudo (idée d'Arkhannou). Pas de clan = rien.
function blasonPseudo(id, estMoi, grand){
  if(!CLANS || !clansCarte.size || !id) return '';
  const k = clansCarte.get(estMoi || id === ID_MOI ? monUidClan : id);
  if(!k) return '';
  const bl = BLASONS.get(k.tag), t = echapperTexte('Clan ' + k.tag);
  return bl && bl.blason
    ? `<span class="bl-nom${grand ? ' grand' : ''}" role="img" aria-label="${t}" title="${t}"><svg viewBox="0 0 100 120" aria-hidden="true">${blasonSVG(bl.blason)}</svg></span>`
    : `<span class="bl-nom bl-nom-ecu${grand ? ' grand' : ''}" role="img" aria-label="${t}" title="${t}" style="--clan:${echapperTexte(k.couleur || '#E07A2E')}"></span>`;
}
// le nom puis son blason ; sans blason, le nom reste exactement comme avant
function pseudoBlason(nomHtml, id, estMoi, grand){
  const b = blasonPseudo(id, estMoi, grand);
  return b ? `<span class="nom-txt">${nomHtml}</span>${b}` : nomHtml;
}
// le journal ne connaît que des pseudos : on retrouve le joueur par ses communes sur la carte
var pseudosClan = { cle: '', map: new Map() };
function blasonParPseudo(p){
  if(!CLANS || !clansCarte.size || !p) return '';
  const cle = othersMap.size + '|' + clansCarteVersion;
  if(pseudosClan.cle !== cle){
    const m = new Map();
    for(const e of othersMap.values()) if(e.pseudo && !m.has(e.pseudo)) m.set(e.pseudo, e.joueurId);
    pseudosClan = { cle, map: m };
  }
  const id = pseudosClan.map.get(p);
  return id ? blasonPseudo(id) : '';
}
function majBlasonsJournal(){
  document.querySelectorAll('.jr-qui[data-jr-pseudo]').forEach(el => {
    const ancien = el.querySelector('.bl-nom');
    if(ancien) ancien.remove();
    const b = blasonParPseudo(el.dataset.jrPseudo);
    if(b) el.insertAdjacentHTML('afterbegin', b);
  });
}
function majBlasonsNoms(){
  try{
    if(classementMode !== 'clans' && classementDonnees && classementDonnees.length) renderClassement();
    majBlasonsJournal();
  }catch(e){ /* les blasons ne sont qu'un ornement */ }
}
""" + a)

# recharger les blasons des noms quand les clans arrivent
a = """    clansCarteVersion++;
    const moi = monUidClan ? clansCarte.get(monUidClan) : null;"""
s = rep(s, a, """    clansCarteVersion++;
    setTimeout(majBlasonsNoms, 0);   // patch275
    const moi = monUidClan ? clansCarte.get(monUidClan) : null;""")

# quand la carte des autres arrive, le journal peut retrouver les pseudos
a = """      bouclierJusqua: row.bouclier_jusqua ? new Date(row.bouclier_jusqua).getTime() : 0
    });
  }
  renderMapOverlay();
}"""
s = rep(s, a, """      bouclierJusqua: row.bouclier_jusqua ? new Date(row.bouclier_jusqua).getTime() : 0
    });
  }
  renderMapOverlay();
  majBlasonsJournal();   // patch275
}""")

# classement : podium et liste (pas le palmarès d'une saison finie)
a = "${l.est_moi ? 'Toi' : echapperTexte(l.pseudo)}${pointEnLigne(l.joueur_id)}"
s = rep(s, a, "${blClassement(l.est_moi ? 'Toi' : echapperTexte(l.pseudo), l, true)}${pointEnLigne(l.joueur_id)}")
a = "${l.est_moi ? '<b>Toi</b>' : echapperTexte(l.pseudo)}${pointEnLigne(l.joueur_id)}"
s = rep(s, a, "${blClassement(l.est_moi ? '<b>Toi</b>' : echapperTexte(l.pseudo), l)}${pointEnLigne(l.joueur_id)}", 2)
a = """           <span class="cl-pseudo"><b>Toi</b></span>"""
s = rep(s, a, """           <span class="cl-pseudo">${blClassement('<b>Toi</b>', moi)}</span>""")
a = "function renderClassement(){\n"
s = rep(s, a, "function blClassement(nom, l, grand){ return classementMode === 'palmares' ? nom : pseudoBlason(nom, l.joueur_id, l.est_moi, grand); }   // patch275\n" + a)

# légende « Joueurs » de la carte
a = """<span class="leg-pseudo">${j.moi ? '<b>Toi</b>' : echapperHtml(j.pseudo)}</span>"""
s = rep(s, a, """<span class="leg-pseudo">${pseudoBlason(j.moi ? '<b>Toi</b>' : echapperHtml(j.pseudo), j.id, j.moi)}</span>""")

# journal : le blason devant le pseudo
a = "  const moi = (p) => p ? `<b>${echapperTexte(p)}</b>` : 'un joueur';"
s = rep(s, a, "  const moi = (p) => p ? `<span class=\"jr-qui\" data-jr-pseudo=\"${echapperTexte(p)}\">${blasonParPseudo(p)}<b>${echapperTexte(p)}</b></span>` : 'un joueur';   // patch275 : + blason")

# --- 2. Échange Terra : « Toutes » ---
a = "let echangeCibles = [];\n"
s = rep(s, a, a + """// patch275 : « Toutes » (Terra seulement, idée d'Arkhannou). L'échange reste à rareté égale :
// un choix d'un côté resserre l'autre côté sur sa rareté.
function echToutes(){ return echangeTier === 'tout'; }
function echTierImpose(cote){
  if(!echToutes()) return echangeTier;
  if(cote === 'mien') return echangeCible && echangeCible.tier ? echangeCible.tier : null;
  const m = echangeMien && terraCollection.get(echangeMien);
  return m ? m.tier.id : null;
}
function echTierOk(id, cote){ const t = echTierImpose(cote); return !t || id === t; }
function echTierEffectif(){
  if(!echToutes()) return echangeTier;
  const m = echangeMien && terraCollection.get(echangeMien);
  return m ? m.tier.id : ((echangeCible && echangeCible.tier) || 'commun');
}
function rangTier(id){ return TIERS.findIndex(t => t.id === id); }
function echRarHtml(id){ return echToutes() && id ? `<em class="ech-rar ${id}">${tierInfo(id).label}</em> · ` : ''; }
function echNoteRarete(cote){
  if(!echToutes()) return '';
  if(cote === 'mien' && echangeMien) return '';   // les deux côtés choisis : une seule note, sous « Tu reçois »
  const t = echTierImpose(cote);
  if(!t) return '';
  const lab = { commun: 'communes', peucommun: 'peu communes', rare: 'rares', epique: 'épiques', legendaire: 'légendaires' }[t] || t;
  return `<p class="ech-note-rar"><span>Un échange se fait à rareté égale : on ne te montre plus que les <b class="ech-rar ${t}">${lab}</b>.</span><button type="button" data-ech-revoir="${cote}">Tout revoir</button></p>`;
}
function echPillToutes(){
  const terra = marcheTerra();
  const p = document.querySelector('#echTiers [data-tier="tout"]');
  if(p) p.hidden = !terra;
  if(!terra && echToutes()){
    echangeTier = 'commun'; echangeMien = null; echangeCible = null;
    document.querySelectorAll('#echTiers .filter-pill').forEach(x => x.classList.toggle('active', x.dataset.tier === 'commun'));
  }
}
""")

a = """function renderEchangeMien(){
  const zone = document.getElementById('echMien');
  if(!zone) return;
"""
s = rep(s, a, a + "  echPillToutes();   // patch275\n")

# mes doublons (Terra)
a = "    .filter(c => c.tier.id === echangeTier && echangeablesTerra(c) > 0);"
s = rep(s, a, "    .filter(c => echTierOk(c.tier.id, 'mien') && echangeablesTerra(c) > 0);   // patch275")
a = """    .filter(c => correspondUnTerme(c.nom, c.dept, rechercheM))
    .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));
  if(!miennes.length){
    zone.innerHTML = rechercheM"""
s = rep(s, a, """    .filter(c => correspondUnTerme(c.nom, c.dept, rechercheM))
    .sort((a, b) => (echToutes() ? rangTier(a.tier.id) - rangTier(b.tier.id) : 0) || a.nom.localeCompare(b.nom, 'fr'));
  if(!miennes.length){
    zone.innerHTML = echNoteRarete('mien') + (rechercheM""")
a = """         : '<p class="collection-empty">Tu n\\'as aucun doublon de cette rareté.</p>');
    echangeMien = null;"""
s = rep(s, a, """         : (echToutes() && !echTierImpose('mien') ? '<p class="collection-empty">Tu n\\'as aucun doublon échangeable.</p>' : '<p class="collection-empty">Tu n\\'as aucun doublon de cette rareté.</p>')));
    echangeMien = null;""")
a = """    <button class="ech-item ${echangeTier} ${echangeMien === c.code ? 'choisi' : ''}" data-mien="${echapperTexte(c.code)}">
      <b>${echapperTexte(c.nom)}</b>
      <small>${echapperTexte(c.dept)} · ${c.libres}"""
s = rep(s, a, """    <button class="ech-item ${c.tier.id} ${echangeMien === c.code ? 'choisi' : ''}" data-mien="${echapperTexte(c.code)}">
      <b>${echapperTexte(c.nom)}</b>
      <small>${echRarHtml(c.tier.id)}${echapperTexte(c.dept)} · ${c.libres}""")
a = "  if([...terraCollection.values()].some(c => c.tier.id === echangeTier && achetesTerra(c) > 0))"
s = rep(s, a, "  { const n = echNoteRarete('mien'); if(n) zone.insertAdjacentHTML('afterbegin', n); }   // patch275\n  if([...terraCollection.values()].some(c => echTierOk(c.tier.id, 'mien') && achetesTerra(c) > 0))")

# les communes des autres : une demande par rareté en « Toutes »
a = """  const { data, error } = await sb.rpc(marcheTerra() ? 'terra_cibles_echange' : 'cibles_echange', {
    p_tier: echangeTier, p_recherche: criteresEchange(rechercheEch)
  });"""
s = rep(s, a, """  echPillToutes();   // patch275
  const tiersDemandes = echToutes() ? TIERS.map(t => t.id).filter(id => id !== 'epique' || EPIQUE_VISIBLE) : [echangeTier];
  const reps = await Promise.all(tiersDemandes.map(t => sb.rpc(marcheTerra() ? 'terra_cibles_echange' : 'cibles_echange', {
    p_tier: t, p_recherche: criteresEchange(rechercheEch)
  }).then(r => ({ t, data: r.data, error: r.error }))));
  const error = (reps.find(r => r.error) || {}).error || null;
  const data = error ? null : reps.flatMap(r => (r.data || []).map(c => Object.assign({}, c, { tier: r.t })));
  const coupees = reps.some(r => (r.data || []).length >= 120);""")
a = "  echangeCoupee = recues.length >= 120 && echangeCibles.length < recues.length;"
s = rep(s, a, "  echangeCoupee = coupees && echangeCibles.length < recues.length;   // patch275 : par rareté")

a = """  if(echangeCibles.length === 0){
    zone.innerHTML = echangeCoupee"""
s = rep(s, a, """  const visibles = echangeCibles.filter(c => !c.tier || echTierOk(c.tier, 'cible'));   // patch275
  if(visibles.length === 0){
    zone.innerHTML = echNoteRarete('cible') + (echangeCoupee""")
a = """      : '<p class="collection-empty">Aucune commune disponible de cette rareté.</p>';
    echangeCible = null;"""
s = rep(s, a, """      : (echToutes() && !echTierImpose('cible') ? '<p class="collection-empty">Aucune commune disponible.</p>' : '<p class="collection-empty">Aucune commune disponible de cette rareté.</p>'));
    echangeCible = null;""")
a = """  if(echangeCible && !echangeCibles.some(c => cleCible(c) === cleCible(echangeCible))) echangeCible = null;

  zone.innerHTML = echangeCibles.map(c => `
    <button class="ech-item ${echangeTier} ${echangeCible"""
s = rep(s, a, """  if(echangeCible && !visibles.some(c => cleCible(c) === cleCible(echangeCible))) echangeCible = null;

  zone.innerHTML = echNoteRarete('cible') + visibles.map(c => `
    <button class="ech-item ${c.tier || echangeTier} ${echangeCible""")
a = "      <small>${echapperTexte(c.departement)} · ${echapperTexte(c.pseudo || 'un joueur')}</small>"
s = rep(s, a, "      <small>${echRarHtml(c.tier)}${echapperTexte(c.departement)} · ${echapperTexte(c.pseudo || 'un joueur')}</small>")

a = "  const commission = COMMISSION_ECHANGE[echangeTier] || 1;"
s = rep(s, a, "  const commission = COMMISSION_ECHANGE[echTierEffectif()] || 1;   // patch275")

a = """document.getElementById('echMien').addEventListener('click', (e) => {
  const b = e.target.closest('[data-mien]');
  if(!b) return;
  echangeMien = echangeMien === b.dataset.mien ? null : b.dataset.mien;
  renderEchangeMien();
});"""
s = rep(s, a, """function echRevoir(e){   // patch275 : « Tout revoir » défait le choix de l'autre côté
  const rv = e.target.closest('[data-ech-revoir]');
  if(!rv) return false;
  if(rv.dataset.echRevoir === 'mien') echangeCible = null; else echangeMien = null;
  renderEchangeMien(); renderEchangeCibles();
  return true;
}
document.getElementById('echMien').addEventListener('click', (e) => {
  if(echRevoir(e)) return;
  const b = e.target.closest('[data-mien]');
  if(!b) return;
  echangeMien = echangeMien === b.dataset.mien ? null : b.dataset.mien;
  renderEchangeMien();
  if(echToutes()) renderEchangeCibles();   // patch275
});""")
a = """  const c = echangeCibles.find(x => cleCible(x) === b.dataset.cible);
  echangeCible = (echangeCible && cleCible(echangeCible) === b.dataset.cible) ? null : c;
  renderEchangeCibles();
});"""
s = rep(s, a, """  const c = echangeCibles.find(x => cleCible(x) === b.dataset.cible);
  echangeCible = (echangeCible && cleCible(echangeCible) === b.dataset.cible) ? null : c;
  renderEchangeCibles();
  if(echToutes()) renderEchangeMien();   // patch275
});""")
a = """document.getElementById('echCibles').addEventListener('click', (e) => {
  const b = e.target.closest('[data-cible]');"""
s = rep(s, a, """document.getElementById('echCibles').addEventListener('click', (e) => {
  if(echRevoir(e)) return;   // patch275
  const b = e.target.closest('[data-cible]');""")
f.write_text(s, encoding='utf-8')

# ---------------- index.html ----------------
f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
assert 'patch275' not in s and 'data-tier="tout"' not in s
a = """        <div class="bourse-filters" id="echTiers">
          <button class="filter-pill active" data-tier="commun">"""
s = rep(s, a, """        <div class="bourse-filters" id="echTiers">
          <button class="filter-pill" data-tier="tout" hidden><span class="pill-point pill-toutes"></span>Toutes</button><!-- patch275 -->
          <button class="filter-pill active" data-tier="commun">""")
f.write_text(s, encoding='utf-8')

# ---------------- style.css ----------------
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch275' not in s
s = s.rstrip('\n') + """

/* patch275 : blason du clan à côté des pseudos (classement, légende, journal) */
.bl-nom{ display:inline-block; flex:none; width:14px; height:17px; margin-left:5px; vertical-align:-3px; }
.bl-nom.grand{ width:18px; height:22px; vertical-align:-5px; }
.bl-nom svg{ width:100%; height:100%; display:block; filter:drop-shadow(0 1px 2px rgba(0,0,0,.4)); }
.bl-nom-ecu{ background: var(--clan); clip-path: polygon(50% 0, 100% 15%, 100% 55%, 50% 100%, 0 55%, 0 15%); }
.cl-pseudo:has(> .bl-nom), .leg-pseudo:has(> .bl-nom){ display:flex; align-items:center; }
.cl-marche .cl-pseudo:has(> .bl-nom){ justify-content:center; width:100%; }
.cl-podium > .cl-marche{ min-width:0; }   /* un long pseudo ne doit pas élargir sa marche */
.nom-txt{ min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.jr-qui{ white-space:nowrap; }
.jr-qui .bl-nom{ margin:0 4px 0 0; }

/* patch275 : Terra › Échange, « Toutes » */
.pill-point.pill-toutes{ background: conic-gradient(var(--c-commun) 0 20%, var(--c-peucommun) 0 40%, var(--c-rare) 0 60%, var(--c-epique) 0 80%, var(--c-legendaire) 0); }
.ech-rar{ font-style:normal; font-weight:600; }
.ech-rar.commun{ color:#A9B4C6; }
.ech-rar.peucommun{ color:#3DCB8E; }
.ech-rar.rare{ color:#5C9BFF; }
.ech-rar.epique{ color:#B38BFA; }
.ech-rar.legendaire{ color: var(--c-legendaire); }
.ech-note-rar{ flex-basis:100%; display:flex; align-items:center; gap:10px; margin:0 0 4px; padding:7px 10px;
  font-size:.8rem; line-height:1.4; color:#D5DEEA; background: rgba(47,124,246,.1); border:1px solid rgba(47,124,246,.35); border-radius:10px; }
.ech-note-rar button{ margin-left:auto; padding:4px 2px; background:none; border:none; font:inherit; font-weight:600; color: var(--c-legendaire); cursor:pointer; white-space:nowrap; }
.ech-note-rar button:focus-visible{ outline:2px solid var(--c-legendaire); outline-offset:2px; border-radius:4px; }
"""
f.write_text(s, encoding='utf-8')
print('patch275 appliqué')
