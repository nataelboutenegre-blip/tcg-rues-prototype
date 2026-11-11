# patch413 (11/11/2026) : calque Clans, « Contour | Plein » (idée de Cairnan217)
# Avant : le calque Clans entourait le territoire de chaque clan de sa couleur ; chaque joueur gardait la sienne.
# Maintenant, un choix sous « Couleurs » quand le calque Clans est allumé : « Contour » (comme avant) ou « Plein » :
# tout le territoire d'un clan prend la couleur du clan ; un trait sombre sépare ses membres, mes communes gardent
# un liseré jaune pour que je m'y retrouve. Les joueurs sans clan gardent leur couleur.
# Pas en mode Couleurs « Raretés » (la rareté reste la couleur) : le choix n'y apparaît pas.
# Le choix est retenu (CALQUES.clanVue, localStorage terrafront-calques). Vaut aussi en outre-mer et de loin (départements).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, C = 'app.js', 'style.css'
if 'patch413' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

# 1. le réglage retenu
rep(A, """raretes: true, passage: false, clans: false, batiments: true, couleur: 'joueurs' };   // patch294 : couleur""",
"""raretes: true, passage: false, clans: false, batiments: true, couleur: 'joueurs', clanVue: 'contour' };   // patch294 : couleur ; patch413 : clanVue""")
rep(A, """function enregistrerCalques(){""",
"""// patch413 : calque Clans en « Plein » (pas avec les couleurs de rareté)
function clanPlein(){
  return CLANS && CALQUES.clans && CALQUES.clanVue === 'plein' && CALQUES.couleur !== 'raretes';
}
function enregistrerCalques(){""")

# 2. allumer ou éteindre Clans montre ou cache le choix
rep(A, """    enregistrerCalques();
    if(id === 'passage' && CALQUES.passage){""",
"""    enregistrerCalques();
    if(id === 'clans') couleursRendre();   // patch413 : « Clans : Contour | Plein » apparaît avec le calque
    if(id === 'passage' && CALQUES.passage){""")

# 3. le choix, sous « Couleurs »
rep(A, """    z.addEventListener('click', (e) => {
      const b = e.target.closest('[data-couleur]');
      if(!b || b.dataset.couleur === CALQUES.couleur) return;""",
"""    z.addEventListener('click', (e) => {
      const v = e.target.closest('[data-clanvue]');   // patch413
      if(v){
        if(v.dataset.clanvue === CALQUES.clanVue) return;
        CALQUES.clanVue = v.dataset.clanvue;
        enregistrerCalques();
        couleursRendre();
        CV.donneesSignature = '';
        demanderDessin();
        if(typeof frontZone !== 'undefined' && frontZone === 'outremer' && typeof OMF !== 'undefined') for(const d of OMF.tuiles.keys()) omfDessiner(d);
        return;
      }
      const b = e.target.closest('[data-couleur]');
      if(!b || b.dataset.couleur === CALQUES.couleur) return;""")
rep(A, """    ${r ? `<span class="mc-leg">${['commun', 'peucommun', 'rare', 'epique', 'legendaire'].map(t => `<span><i style="background:${COULEURS_FILTRE[t]}"></i>${LIB[t]}</span>`).join('')}</span>` : ''}`;""",
"""    ${r ? `<span class="mc-leg">${['commun', 'peucommun', 'rare', 'epique', 'legendaire'].map(t => `<span><i style="background:${COULEURS_FILTRE[t]}"></i>${LIB[t]}</span>`).join('')}</span>` : ''}
    ${CLANS && CALQUES.clans && !r ? `<span class="mc-clans"><span class="mc-lib">Clans :</span><span class="mc-seg" role="group" aria-label="Territoire des clans">
      <button type="button" data-clanvue="contour" aria-pressed="${CALQUES.clanVue !== 'plein'}" class="${CALQUES.clanVue !== 'plein' ? 'on' : ''}">Contour</button>
      <button type="button" data-clanvue="plein" aria-pressed="${CALQUES.clanVue === 'plein'}" class="${CALQUES.clanVue === 'plein' ? 'on' : ''}">Plein</button></span></span>` : ''}`;   // patch413""")

# 4. de loin (départements) : la couleur du clan
rep(A, """        ctx.globalAlpha = opaciteJoueur(info.joueur, info.force);
        ctx.fillStyle = j.couleur;
        const cd = cheminDeptCanvas(dep, CONTOURS_DEPTS[dep]);""",
"""        const pleinD = j.clan && clanPlein();   // patch413 : de loin, la couleur du clan, assez franche pour se lire
        ctx.globalAlpha = opaciteJoueur(info.joueur, pleinD ? Math.max(info.force, 0.72) : info.force);
        ctx.fillStyle = pleinD ? j.clanCouleur : j.couleur;
        const cd = cheminDeptCanvas(dep, CONTOURS_DEPTS[dep]);""")

# 5. de près : chaque membre peint de la couleur de son clan, un trait entre membres, mon liseré jaune
rep(A, """      // patch411 : échange en cours, mes communes d'une autre rareté voilées, les bonnes entourées
""", """      // patch413 : calque Clans « Plein »
      if(parClan && clanPlein()){
        const bordsP = bordsTerritoires(deps, possedees);
        for(const id of ordre([...parJoueur.keys()])){
          const j = joueurs.get(id), p = parJoueur.get(id);
          if(!j || !j.clan) continue;
          ctx.globalAlpha = opaciteJoueur(id, 0.92);
          ctx.fillStyle = j.clanCouleur; ctx.fill(p);
          if(interieur > 0){ ctx.globalAlpha = opaciteJoueur(id, 0.45 * interieur); ctx.strokeStyle = '#07111F'; ctx.lineWidth = trait(0.7); ctx.stroke(p); }
          const bord = bordsP.get(id);
          if(bord){
            ctx.save(); ctx.clip(p);
            ctx.globalAlpha = opaciteJoueur(id, 1);
            ctx.strokeStyle = '#07111F'; ctx.lineWidth = trait(j.moi ? 5.4 : 2.6); ctx.stroke(bord);
            if(j.moi){ ctx.strokeStyle = COULEUR_MOI; ctx.lineWidth = trait(3); ctx.stroke(bord); }
            ctx.restore();
          }
        }
        ctx.globalAlpha = 1;
      }
      // patch411 : échange en cours, mes communes d'une autre rareté voilées, les bonnes entourées
""")

# 6. outre-mer
rep(A, """    const c = mienne || autre;
    ctx.fillStyle = mienne ? COULEUR_MOI : autre ? colorForPlayer(autre.joueurId) : '#14454E';
    ctx.fill(p);
    ctx.strokeStyle = c ? 'rgba(4,20,30,.9)' : 'rgba(44,198,201,.38)';
    ctx.lineWidth = grand ? 1.1 : 0.8;
    ctx.stroke(p);
    const clan = clans && c && clans.get(mienne ? window.__monId : autre.joueurId);
""", """    const c = mienne || autre;
    const clan = clans && c && clans.get(mienne ? window.__monId : autre.joueurId);   // patch413 : avant le fond, pour « Plein »
    const plein = clan && clanPlein();
    ctx.fillStyle = plein ? clan.couleur : mienne ? COULEUR_MOI : autre ? colorForPlayer(autre.joueurId) : '#14454E';
    ctx.fill(p);
    ctx.strokeStyle = c ? 'rgba(4,20,30,.9)' : 'rgba(44,198,201,.38)';
    ctx.lineWidth = grand ? 1.1 : 0.8;
    ctx.stroke(p);
    if(plein && mienne){ ctx.save(); ctx.clip(p); ctx.strokeStyle = COULEUR_MOI; ctx.lineWidth = grand ? 3.4 : 2.4; ctx.stroke(p); ctx.restore(); }
""")

open(C, 'a', encoding='utf-8').write("""
/* patch413 : « Clans : Contour | Plein » */
.mc-clans{ display:inline-flex; align-items:center; gap:10px; }
""")
print('patch413 OK')
