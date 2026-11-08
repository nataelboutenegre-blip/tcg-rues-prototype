# patch384 (8/11/2026) : déplacer une Fonderie (s2-122), idée de Maroli, règles validées par Nataël.
#
# Comme les forteresses (patch374) :
#   - fonderie_deplacer_prix lingots (10) ; 6 h de chantier sans production ;
#   - pas pendant un assaut sur sa commune ; un déplacement ne s'annule pas ;
#   - même bâtiment : compté une seule fois au score.
# Où : Combat › Bâtiments (« Déplacer » sur chaque Fonderie prête, puis la commune),
# et la fiche d'une de ses communes (« Déplacer une Fonderie ici », puis laquelle).
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:80]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch384' not in s, 'patch384 déjà appliqué'

# ---------- Combat › Bâtiments : la liste des Fonderies ----------
s = rep(s, """    ${F ? mesFonderies().map(x => ligne(ICONE_FONDERIE, x, btPretDans(x) <= 0 ? `Produit ${B.production} lingots par jour` : 'En construction', 'fonderie')).join('')""",
"""    ${F ? mesFonderies().map(x => x.deplacee && btPretDans(x) > 0   /* patch384 : en route, ne produit rien, ne s'annule pas */
        ? ligne(ICONE_FONDERIE, x, 'En déplacement · ne produit rien pendant le chantier')
        : btPretDans(x) <= 0 ? fdLigneActive(x, `Produit ${B.production} lingots par jour`)
        : ligne(ICONE_FONDERIE, x, 'En construction', 'fonderie')).join('')""")
s = rep(s, """  const ftc = document.getElementById('ftDepCherche');   // patch374""",
"""  const fdc = document.getElementById('fdDepCherche');   // patch384
  if(fdc) fdc.addEventListener('input', (e) => {
    fdDepRecherche = e.target.value;
    const z = document.getElementById('fdDepChoix'); if(z) z.innerHTML = fdDepChoixHtml();
  });
  const ftc = document.getElementById('ftDepCherche');   // patch374""")
s = rep(s, """// ---------- patch374 : déplacer une forteresse (s2-116) ----------""",
"""// ---------- patch384 : déplacer une Fonderie (s2-122) ----------
var fdDepOuvert = null, fdDepRecherche = '';
const fdDepPrix = () => Number(btReglage('fonderie_deplacer_prix', 10)) || 0;
function fdLigneActive(x, sousActif){
  const assaut = btSousAssaut(x.code), ouvert = fdDepOuvert === x.code;
  const sous = assaut ? 'Assaut en cours : pas de déplacement' : sousActif;
  return `<div class="btl"><span class="btl-ic">${ICONE_FONDERIE}</span>
      <span class="btl-t"><button type="button" class="btl-nom" data-voir-carte="${echapperTexte(x.code)}">${echapperTexte(x.nom)} (${echapperTexte(x.dept)})</button><small>${sous}</small></span>
      <button type="button" class="gl-r bt-fortifier ft-dep-b${ouvert ? ' on' : ''}" data-fd-dep="${echapperTexte(x.code)}" ${assaut ? 'disabled' : ''}>${ouvert ? 'Fermer' : 'Déplacer'}</button></div>`
    + (ouvert && !assaut ? fdDepHtml() : '');
}
function fdDepHtml(){
  const prix = fdDepPrix(), n = lingotsActuels();
  if(n < prix) return `<p class="cr-manque">Il te faut ${prix} lingots pour la déplacer (tu en as ${n}).</p>`;
  return `<div class="cr-dem ft-dem">
    <p class="cr-txt">Elle part d’ici et se reconstruit là où tu veux : <b>${prix} lingots</b>, <b>${btReglage('construction_h', 6)} h de chantier</b> pendant lesquelles elle ne produit rien. Un déplacement ne s’annule pas.</p>
    <input type="search" class="bourse-search gn-cherche" id="fdDepCherche" placeholder="Choisis la commune où l’installer…" autocomplete="off" value="${echapperTexte(fdDepRecherche)}">
    <div class="gn-choix" id="fdDepChoix">${fdDepChoixHtml()}</div></div>`;
}
function fdDepChoixHtml(){
  const q = sansAccents(fdDepRecherche.trim().toLowerCase());
  const deja = new Set(mesFonderies().map(x => x.code));
  const ici = collectionMap.get(fdDepOuvert);
  const rang = (t) => TIERS.findIndex(x => x.id === t.id);
  const mes = [...collectionMap.values()].filter(c => !deja.has(c.code)
    && (!q || sansAccents(c.nom.toLowerCase()).includes(q) || c.dept === q.toUpperCase()));
  if(!mes.length) return `<p class="gl-vide">${collectionMap.size > 1 ? 'Aucune de tes communes ne correspond.' : 'Il te faut une autre commune.'}</p>`;
  const km = (c) => ici && ici.lat != null && c.lat != null ? kmEntre(ici.lat, ici.lon, c.lat, c.lon) : null;
  const L = mes.map(c => ({ c, km: km(c) }));
  L.sort((a, b) => rang(a.c.tier) - rang(b.c.tier) || (a.km == null) - (b.km == null) || (a.km || 0) - (b.km || 0));
  const prix = fdDepPrix();
  return L.slice(0, 6).map(({ c, km }) => {
    const a = btArme === c.code + '|fddep';
    return `<div class="gl gn-ligne"><i class="gl-c ${c.tier.id}"></i><div class="gl-t"><b>${echapperTexte(c.nom)}</b>
      <span>${c.tier.label} · ${echapperTexte(c.dept)}${km != null ? ' · à ' + Math.round(km) + ' km' : ''}</span></div>
      <button class="gl-r bt-fortifier${a ? ' arme' : ''}" data-fd-dep-ici="${echapperTexte(c.code)}">${a ? `Confirmer · ${prix} lingots` : 'Ici'}</button></div>`;
  }).join('') + (mes.length > 6 ? `<p class="gl-vide">+ ${mes.length - 6} autre${mes.length - 6 > 1 ? 's' : ''} : affine la recherche.</p>` : '');
}
async function fonderieDeplacer(depuis, vers){
  const { error } = await sb.rpc('fonderie_deplacer', { p_depuis: depuis, p_vers: vers });
  if(error) notifier({ type: 'erreur', titre: 'Déplacer la Fonderie', texte: messageLisible(error.message) });
  else {
    const c = collectionMap.get(vers);
    notifier({ type: 'succes', titre: 'Fonderie en route', texte: `${c ? c.nom + ' : p' : 'P'}rête dans ${btReglage('construction_h', 6)} h. D’ici là, elle ne produit rien.` });
  }
  fdDepOuvert = null; fdDepRecherche = '';
  await chargerBatiments();
  if(panneauCommune === vers && collectionMap.get(vers)){ const a = panneauAncre; ouvrirPanneau(vers, a ? a.x : 40, a ? a.y : 40); }
}

// ---------- patch374 : déplacer une forteresse (s2-116) ----------""")
s = rep(s, """      const fd = e.target.closest('[data-ft-dep]');   // patch374 : déplacer une forteresse""",
"""      const fdd = e.target.closest('[data-fd-dep]');   // patch384 : déplacer une Fonderie
      if(fdd){ fdDepOuvert = fdDepOuvert === fdd.dataset.fdDep ? null : fdd.dataset.fdDep; fdDepRecherche = ''; btArme = null; renderBatimentsBloc(); return; }
      const fdi = e.target.closest('[data-fd-dep-ici]');
      if(fdi){
        const k = fdi.dataset.fdDepIci + '|fddep';
        if(btArme !== k){ btArme = k; const z = document.getElementById('fdDepChoix'); if(z) z.innerHTML = fdDepChoixHtml(); return; }
        btArme = null; fdi.disabled = true; fonderieDeplacer(fdDepOuvert, fdi.dataset.fdDepIci); return;
      }
      const fd = e.target.closest('[data-ft-dep]');   // patch374 : déplacer une forteresse""")

# ---------- la fiche d'une commune ----------
s = rep(s, """    const prete = btPretDans(ici) <= 0;
    const pr = prochainLingotMs();""", """    const prete = btPretDans(ici) <= 0, route = ici.deplacee && !prete;   // patch384
    const pr = prochainLingotMs();""")
s = rep(s, """: `<b>En construction</b> : prête dans ${formatDuree(btPretDans(ici))}.`}""",
           """: route ? `<b>En déplacement</b> : prête dans ${formatDuree(btPretDans(ici))}, elle ne produit rien d’ici là.` : `<b>En construction</b> : prête dans ${formatDuree(btPretDans(ici))}.`}${prete ? ` Tu peux la déplacer pour ${fdDepPrix()} lingots : Combat › Bâtiments, ou « Déplacer une Fonderie ici » sur une autre de tes communes.` : ''}""")
s = rep(s, """      ${prete ? '' : btAnnulerHtml(code, 'fonderie')}""", """      ${prete || route ? '' : btAnnulerHtml(code, 'fonderie')}""")
s = rep(s, """  if(!mesForteresses().some(x => x.code === code)){
    const nb = mesForteresses().length, maxF = btReglage('forteresse_max', 3)""",
"""  const fdPretes = mesFonderies().filter(x => btPretDans(x) <= 0 && x.code !== code);   // patch384 : en déplacer une ici
  if(fdPretes.length && !mesFonderies().some(x => x.code === code)){
    const pd = fdDepPrix(), nl = lingotsActuels(), ici = collectionMap.get(code);
    const bloque = nl < pd ? `Il te faut ${pd} lingots (tu en as ${nl})` : '';
    if(!arme('fddep') || bloque){
      boutons.push(`<button class="pc-action bt-action" data-pc="bt-fd-dep" ${bloque ? 'disabled' : ''}>${ICONE_FONDERIE}<span>Déplacer une Fonderie ici<small>${bloque || `Prête dans ${h} h · ne produit rien pendant le chantier · ne s’annule pas`}</small></span><span class="prix">${pd} ${ICONE_LINGOT}</span></button>`);
    } else {
      for(const x of fdPretes){
        const o = collectionMap.get(x.code), kmTxt = o && ici && o.lat != null && ici.lat != null ? kmEntre(ici.lat, ici.lon, o.lat, o.lon) : null;
        const assaut = btSousAssaut(x.code);
        boutons.push(`<button class="pc-action bt-action ft-dep-de" data-pc="bt-fd-dep-de" data-depuis="${echapperTexte(x.code)}" ${assaut ? 'disabled' : ''}>${ICONE_FONDERIE}<span>Prendre celle ${/^[aeiouyhâàéèêîïôû]/i.test(x.nom) ? 'd’' : 'de '}${echapperHtml(x.nom)}<small>${assaut ? 'Assaut en cours : elle ne bouge pas' : `${echapperHtml(x.dept)}${kmTxt != null ? ' · à ' + Math.round(kmTxt) + ' km' : ''} · prête ici dans ${h} h`}</small></span><span class="prix">${pd} ${ICONE_LINGOT}</span></button>`);
      }
    }
  }
  if(!mesForteresses().some(x => x.code === code)){
    const nb = mesForteresses().length, maxF = btReglage('forteresse_max', 3)""")
s = rep(s, """  if(quoi === 'bt-ft-dep'){""", """  if(quoi === 'bt-fd-dep'){ btArme = code + '|fddep'; const a = panneauAncre; ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40); return; }   // patch384 : laquelle ?
  if(quoi === 'bt-fd-dep-de'){ btArme = null; b.disabled = true; fonderieDeplacer(b.dataset.depuis, code); return; }
  if(quoi === 'bt-ft-dep'){""")
F.write_text(s, encoding='utf-8')

# ---------- règles ----------
H = pathlib.Path('index.html'); h = H.read_text(encoding='utf-8')
assert 'patch384' not in h
h = rep(h, """réserve jusqu'à 45. Les <b>combats</b>""",
"""réserve jusqu'à 45. Une Fonderie prête se <b>déplace</b> sur une autre de tes communes pour <b>10 lingots</b> (Combat › Bâtiments, ou la fiche de la commune) : 6 h de chantier sans production, pas pendant un assaut, et ça ne s'annule pas.<!-- patch384 --> Les <b>combats</b>""")
H.write_text(h, encoding='utf-8')
print('patch384 ok')
