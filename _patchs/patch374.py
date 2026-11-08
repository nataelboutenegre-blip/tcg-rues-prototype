# patch374 (8/11/2026) : déplacer une Forteresse (s2-116), demande de Nataël.
#
# Une Forteresse active peut aller sur une autre de ses communes :
#   - forteresse_deplacer_prix lingots (10 par défaut, la moitié de sa construction) ;
#   - 6 h de chantier à la nouvelle adresse, sans aucun effet pendant ce temps ;
#   - pas pendant un assaut sur sa commune ; un déplacement ne s'annule pas ;
#   - elle reste comptée une seule fois au score (même bâtiment).
# Où : Défendre › Bâtiments (« Déplacer » sur chaque forteresse active, puis la
# commune), et sur la fiche d'une de ses communes (« Déplacer une forteresse
# ici », puis laquelle).
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:80]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch374' not in s, 'patch374 déjà appliqué'

# ---------- Défendre : la liste des forteresses ----------
s = rep(s, """    ${forts.map(x => ligne(ICONE_FORTERESSE, x, btPretDans(x) <= 0 ? `−${btReglage('forteresse_defense', 15)} % aux attaquants · +${btReglage('forteresse_appui', 5)} % autour` : 'En construction', 'forteresse')).join('')}""",
"""    ${forts.map(x => x.deplacee && btPretDans(x) > 0   /* patch374 : en route, sans effet, ne s'annule pas */
        ? ligne(ICONE_FORTERESSE, x, `En déplacement · sans effet pendant le chantier`)
        : btPretDans(x) <= 0 ? ftLigneActive(x)
        : ligne(ICONE_FORTERESSE, x, 'En construction', 'forteresse')).join('')}""")
s = rep(s, """  const crc = document.getElementById('crDemCherche');   // patch371""",
"""  const ftc = document.getElementById('ftDepCherche');   // patch374
  if(ftc) ftc.addEventListener('input', (e) => {
    ftDepRecherche = e.target.value;
    const z = document.getElementById('ftDepChoix'); if(z) z.innerHTML = ftDepChoixHtml();
  });
  const crc = document.getElementById('crDemCherche');   // patch371""")
s = rep(s, """function btChoixHtml(){
  const q = sansAccents(btRecherche.trim().toLowerCase());""",
"""// ---------- patch374 : déplacer une forteresse (s2-116) ----------
var ftDepOuvert = null, ftDepRecherche = '';
const ftDepPrix = () => Number(btReglage('forteresse_deplacer_prix', 10)) || 0;
function ftLigneActive(x){
  const assaut = btSousAssaut(x.code), ouvert = ftDepOuvert === x.code;
  const sous = assaut ? 'Assaut en cours : pas de déplacement' : `Active · −${btReglage('forteresse_defense', 15)} % aux attaquants · +${btReglage('forteresse_appui', 5)} % autour`;
  return `<div class="btl"><span class="btl-ic">${ICONE_FORTERESSE}</span>
      <span class="btl-t"><button type="button" class="btl-nom" data-voir-carte="${echapperTexte(x.code)}">${echapperTexte(x.nom)} (${echapperTexte(x.dept)})</button><small>${sous}</small></span>
      <button type="button" class="gl-r bt-fortifier ft-dep-b${ouvert ? ' on' : ''}" data-ft-dep="${echapperTexte(x.code)}" ${assaut ? 'disabled' : ''}>${ouvert ? 'Fermer' : 'Déplacer'}</button></div>`
    + (ouvert && !assaut ? ftDepHtml() : '');
}
function ftDepHtml(){
  const prix = ftDepPrix(), n = lingotsActuels();
  if(n < prix) return `<p class="cr-manque">Il te faut ${prix} lingots pour la déplacer (tu en as ${n}).</p>`;
  return `<div class="cr-dem ft-dem">
    <p class="cr-txt">Elle part d’ici et se reconstruit là où tu veux : <b>${prix} lingots</b>, <b>${btReglage('construction_h', 6)} h de chantier</b> pendant lesquelles elle ne protège rien. Un déplacement ne s’annule pas.</p>
    <input type="search" class="bourse-search gn-cherche" id="ftDepCherche" placeholder="Choisis la commune où l’installer…" autocomplete="off" value="${echapperTexte(ftDepRecherche)}">
    <div class="gn-choix" id="ftDepChoix">${ftDepChoixHtml()}</div></div>`;
}
function ftDepChoixHtml(){
  const q = sansAccents(ftDepRecherche.trim().toLowerCase());
  const deja = new Set(mesForteresses().map(x => x.code));
  const ici = collectionMap.get(ftDepOuvert);
  const rang = (t) => TIERS.findIndex(x => x.id === t.id);
  const mes = [...collectionMap.values()].filter(c => !deja.has(c.code)
    && (!q || sansAccents(c.nom.toLowerCase()).includes(q) || c.dept === q.toUpperCase()));
  if(!mes.length) return `<p class="gl-vide">${collectionMap.size > 1 ? 'Aucune de tes communes ne correspond.' : 'Il te faut une autre commune.'}</p>`;
  const km = (c) => ici && ici.lat != null && c.lat != null ? kmEntre(ici.lat, ici.lon, c.lat, c.lon) : null;
  const L = mes.map(c => ({ c, km: km(c) }));
  L.sort((a, b) => rang(a.c.tier) - rang(b.c.tier) || (a.km == null) - (b.km == null) || (a.km || 0) - (b.km || 0));
  const prix = ftDepPrix();
  return L.slice(0, 6).map(({ c, km }) => {
    const a = btArme === c.code + '|ftdep';
    return `<div class="gl gn-ligne"><i class="gl-c ${c.tier.id}"></i><div class="gl-t"><b>${echapperTexte(c.nom)}</b>
      <span>${c.tier.label} · ${echapperTexte(c.dept)}${km != null ? ' · à ' + Math.round(km) + ' km' : ''}</span></div>
      <button class="gl-r bt-fortifier${a ? ' arme' : ''}" data-ft-dep-ici="${echapperTexte(c.code)}">${a ? `Confirmer · ${prix} lingots` : 'Ici'}</button></div>`;
  }).join('') + (mes.length > 6 ? `<p class="gl-vide">+ ${mes.length - 6} autre${mes.length - 6 > 1 ? 's' : ''} : affine la recherche.</p>` : '');
}
async function forteresseDeplacer(depuis, vers){
  const { error } = await sb.rpc('forteresse_deplacer', { p_depuis: depuis, p_vers: vers });
  if(error) notifier({ type: 'erreur', titre: 'Déplacer la forteresse', texte: messageLisible(error.message) });
  else {
    const c = collectionMap.get(vers);
    notifier({ type: 'succes', titre: 'Forteresse en route', texte: `${c ? c.nom + ' : p' : 'P'}rête dans ${btReglage('construction_h', 6)} h. D’ici là, elle ne protège rien.` });
  }
  ftDepOuvert = null; ftDepRecherche = '';
  await chargerBatiments();
  if(panneauCommune === vers && collectionMap.get(vers)){ const a = panneauAncre; ouvrirPanneau(vers, a ? a.x : 40, a ? a.y : 40); }
}

function btChoixHtml(){
  const q = sansAccents(btRecherche.trim().toLowerCase());""")
s = rep(s, """      const fo = e.target.closest('[data-bt-fortifier]');
      if(!fo) return;""",
"""      const fd = e.target.closest('[data-ft-dep]');   // patch374 : déplacer une forteresse
      if(fd){ ftDepOuvert = ftDepOuvert === fd.dataset.ftDep ? null : fd.dataset.ftDep; ftDepRecherche = ''; btArme = null; renderBatimentsBloc(); return; }
      const fi = e.target.closest('[data-ft-dep-ici]');
      if(fi){
        const k = fi.dataset.ftDepIci + '|ftdep';
        if(btArme !== k){ btArme = k; const z = document.getElementById('ftDepChoix'); if(z) z.innerHTML = ftDepChoixHtml(); return; }
        btArme = null; fi.disabled = true; forteresseDeplacer(ftDepOuvert, fi.dataset.ftDepIci); return;
      }
      const fo = e.target.closest('[data-bt-fortifier]');
      if(!fo) return;""")

# ---------- la fiche d'une commune ----------
s = rep(s, """  const fort = mesForteresses().find(x => x.code === code);
  if(fort){
    const prete = btPretDans(fort) <= 0;
    html += `<div class="bt bt-fort">
      <div class="bt-haut">${ICONE_FORTERESSE}Forteresse <b>${prete ? 'active' : 'prête dans ' + formatDuree(btPretDans(fort))}</b></div>
      <p class="bt-txt"><b>−${btReglage('forteresse_defense', 15)} %</b> aux chances des attaquants ici, et <b>+${btReglage('forteresse_appui', 5)} %</b> à tes attaques à moins de ${btReglage('rayon_km', 20)} km.</p>
      ${prete ? '' : btAnnulerHtml(code, 'forteresse')}
    </div>`;""",
"""  const fort = mesForteresses().find(x => x.code === code);
  if(fort){
    const prete = btPretDans(fort) <= 0, route = fort.deplacee && !prete;   // patch374
    html += `<div class="bt bt-fort">
      <div class="bt-haut">${ICONE_FORTERESSE}Forteresse <b>${prete ? 'active' : (route ? 'en route · ' : '') + 'prête dans ' + formatDuree(btPretDans(fort))}</b></div>
      <p class="bt-txt">${route ? '<b>Déplacement en cours</b> : elle ne protège rien avant la fin du chantier. ' : ''}<b>−${btReglage('forteresse_defense', 15)} %</b> aux chances des attaquants ici, et <b>+${btReglage('forteresse_appui', 5)} %</b> à tes attaques à moins de ${btReglage('rayon_km', 20)} km.${prete ? ` Tu peux la déplacer pour ${ftDepPrix()} lingots : Défendre › Bâtiments, ou « Déplacer une forteresse ici » sur une autre de tes communes.` : ''}</p>
      ${prete || route ? '' : btAnnulerHtml(code, 'forteresse')}
    </div>`;""")
s = rep(s, """  if(B.bombes_ouvertes && !B.centre){   // patch260 : le Centre de recherche""",
"""  const ftActives = mesForteresses().filter(x => btPretDans(x) <= 0 && x.code !== code);   // patch374 : en déplacer une ici
  if(ftActives.length && !mesForteresses().some(x => x.code === code)){
    const pd = ftDepPrix(), nl = lingotsActuels(), ici = collectionMap.get(code);
    const bloque = nl < pd ? `Il te faut ${pd} lingots (tu en as ${nl})` : '';
    if(!arme('ftdep') || bloque){
      boutons.push(`<button class="pc-action bt-action" data-pc="bt-ft-dep" ${bloque ? 'disabled' : ''}>${ICONE_FORTERESSE}<span>Déplacer une forteresse ici<small>${bloque || `Prête dans ${h} h · sans effet pendant le chantier · ne s’annule pas`}</small></span><span class="prix">${pd} ${ICONE_LINGOT}</span></button>`);
    } else {
      for(const x of ftActives){
        const o = collectionMap.get(x.code), kmTxt = o && ici && o.lat != null && ici.lat != null ? kmEntre(ici.lat, ici.lon, o.lat, o.lon) : null;
        const assaut = btSousAssaut(x.code);
        boutons.push(`<button class="pc-action bt-action ft-dep-de" data-pc="bt-ft-dep-de" data-depuis="${echapperTexte(x.code)}" ${assaut ? 'disabled' : ''}>${ICONE_FORTERESSE}<span>Prendre celle ${/^[aeiouyhâàéèêîïôû]/i.test(x.nom) ? 'd’' : 'de '}${echapperHtml(x.nom)}<small>${assaut ? 'Assaut en cours : elle ne bouge pas' : `${echapperHtml(x.dept)}${kmTxt != null ? ' · à ' + Math.round(kmTxt) + ' km' : ''} · prête ici dans ${h} h`}</small></span><span class="prix">${pd} ${ICONE_LINGOT}</span></button>`);
      }
    }
  }
  if(B.bombes_ouvertes && !B.centre){   // patch260 : le Centre de recherche""")
s = rep(s, """  if(quoi === 'bt-demenager'){   // patch371 : en deux temps""",
"""  if(quoi === 'bt-ft-dep'){ btArme = code + '|ftdep'; const a = panneauAncre; ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40); return; }   // patch374 : laquelle ?
  if(quoi === 'bt-ft-dep-de'){ btArme = null; b.disabled = true; forteresseDeplacer(b.dataset.depuis, code); return; }
  if(quoi === 'bt-demenager'){   // patch371 : en deux temps""")
F.write_text(s, encoding='utf-8')

# ---------- règles ----------
H = pathlib.Path('index.html'); h = H.read_text(encoding='utf-8')
assert 'patch374' not in h
h = rep(h, """Avec <b>20 lingots</b>, fais d'une commune une <b>Forteresse</b> (5 au plus) : <b>−15 %</b> aux chances des attaquants sur elle, et <b>+5 %</b> à tes attaques à moins de 20 km.""",
"""Avec <b>20 lingots</b>, fais d'une commune une <b>Forteresse</b> (5 au plus) : <b>−15 %</b> aux chances des attaquants sur elle, et <b>+5 %</b> à tes attaques à moins de 20 km. Une Forteresse active se <b>déplace</b> sur une autre de tes communes pour <b>10 lingots</b> (Défendre › Bâtiments, ou la fiche de la commune) : 6 h de chantier sans effet, pas pendant un assaut, et ça ne s'annule pas.<!-- patch374 -->""")
H.write_text(h, encoding='utf-8')
print('patch374 ok')
