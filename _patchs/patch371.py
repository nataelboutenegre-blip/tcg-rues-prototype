# patch371 (7/11/2026) : le Radar de détection et le déménagement du Centre (s2-115).
#
# Décisions de Nataël (7/11, 22 h 39) : le Radar ne voit pas les Banques ; le
# joueur repéré est prévenu ; le déménagement du Centre en même temps.
#   - Radar : 30 lingots, une Fonderie, 6 h, un seul ; 3 styles en pixel art
#     (Parabole, Radôme, Pylône) ; visible de tous ; voit les Centres des autres
#     (hors clan) à moins de 50 km, même secrets. Ce qu'il voit : sur la carte,
#     dans Défendre › Bâtiments, dans « Les autres » et la fiche du Radar.
#   - Le repéré : une ligne dans la cloche, une alerte dans Défendre (Centre).
#   - Déménager : dans Défendre (Centre : « Déménager », choix de la commune) et
#     sur la fiche d'une de ses communes (« Déménager le Centre ici »). 20 lingots
#     de sa poche, 6 h ; la bombe suit, en pause pendant le chantier. Chaque
#     commune proposée dit combien de Radars la verraient.
#   - Règles, classement (+80), légende, nouveautés.
import json, pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:80]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch371' not in s, 'patch371 déjà appliqué'

# ---------- icône, tracé de carte, réglages ----------
s = rep(s, "const bqReglage = (cle, defaut) => (BATIMENTS && BATIMENTS.banque_reglages && BATIMENTS.banque_reglages[cle] != null) ? BATIMENTS.banque_reglages[cle] : defaut;",
"""const bqReglage = (cle, defaut) => (BATIMENTS && BATIMENTS.banque_reglages && BATIMENTS.banque_reglages[cle] != null) ? BATIMENTS.banque_reglages[cle] : defaut;
// patch371 : le Radar (s2-115)
const rdReglage = (cle, defaut) => (BATIMENTS && BATIMENTS.radar_reglages && BATIMENTS.radar_reglages[cle] != null) ? BATIMENTS.radar_reglages[cle] : defaut;
const ICONE_RADAR = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" d="M12 21a9 9 0 1 1 9-9M12 17a5 5 0 1 1 5-5M12 12l5.5-5.5"/><circle cx="12" cy="12" r="1.6" fill="currentColor"/></svg>';
if(BT_TRACES) BT_TRACES.radar = [new Path2D('M12 21a9 9 0 1 1 9-9M12 17a5 5 0 1 1 5-5M12 12l5.5-5.5'), new Path2D('M13.6 12a1.6 1.6 0 1 1-3.2 0a1.6 1.6 0 1 1 3.2 0')];""")

# ---------- la scène d'assaut : un Radar pris ----------
s = rep(s, """        + (SAISON2 && (BATIMENTS_CARTE.get(String(cible.code)) || {}).centre ? `<span class="as-mon as-bt">${ICONE_CENTRE}Centre de recherche détruit : sa bombe est perdue</span>` : '')   // patch260""",
"""        + (SAISON2 && (BATIMENTS_CARTE.get(String(cible.code)) || {}).centre ? `<span class="as-mon as-bt">${ICONE_CENTRE}Centre de recherche détruit : sa bombe est perdue</span>` : '')   // patch260
        + (SAISON2 && (BATIMENTS_CARTE.get(String(cible.code)) || {}).radar ? `<span class="as-mon as-bt">${ICONE_RADAR}Radar détruit</span>` : '')   // patch371""")

# ---------- la fiche d'une commune des autres ----------
s = rep(s, """      if(bt.forteresse) t.push(bt.forteresse.pret ? 'Forteresse' : 'Forteresse en construction');
      lignes.push(['Bâtiment', t.join(' + ')]);""",
"""      if(bt.forteresse) t.push(bt.forteresse.pret ? 'Forteresse' : 'Forteresse en construction');
      if(bt.radar) t.push(bt.radar.pret ? 'Radar' : 'Radar en construction');   // patch371
      if(bt.centre) t.push(bt.centre.radar ? 'Centre de recherche (vu par ton Radar)' : 'Centre de recherche dévoilé');
      if(t.length) lignes.push(['Bâtiment', t.join(' + ')]);""")
s = rep(s, "if(bt && ['fonderie', 'forteresse', 'centre', 'banque'].some(t => bt[t])) return 'batiment';   // patch354",
           "if(bt && ['fonderie', 'forteresse', 'centre', 'banque', 'radar'].some(t => bt[t])) return 'batiment';   // patch354, patch371")

# ---------- chargement : les Centres vus par mon Radar ----------
s = rep(s, """    const carte = new Map();
    for(const b of (v.data || [])){
      const k = String(b.commune_code);
      const e = carte.get(k) || {};
      e[b.type] = { moi: b.joueur_id === window.__monId, pret: !!b.pret };""",
"""    const carte = new Map();
    const vusRadar = new Set(((BATIMENTS.radar && BATIMENTS.radar.voit) || []).map(x => String(x.code)));   // patch371
    for(const b of (v.data || [])){
      const k = String(b.commune_code);
      const e = carte.get(k) || {};
      e[b.type] = { moi: b.joueur_id === window.__monId, pret: !!b.pret, radar: b.type === 'centre' && vusRadar.has(k) };""")

# ---------- la carte ----------
s = rep(s, "    const types = ['fonderie', 'forteresse', 'centre', 'banque'].filter(t => bt[t] && BT_TRACES[t]);   // patch260, patch354",
           "    const types = ['fonderie', 'forteresse', 'centre', 'banque', 'radar'].filter(t => bt[t] && BT_TRACES[t]);   // patch260, patch354, patch371")
s = rep(s, "ctx.save(); ctx.shadowColor = t === 'centre' ? 'rgba(255,90,82,.7)' : 'rgba(255,150,60,.75)'; ctx.shadowBlur = 10;",
           "ctx.save(); ctx.shadowColor = t === 'centre' ? 'rgba(255,90,82,.7)' : t === 'radar' ? 'rgba(110,195,240,.75)' : 'rgba(255,150,60,.75)'; ctx.shadowBlur = 10;")
s = rep(s, "ctx.lineWidth = 2.6 * e; ctx.strokeStyle = bt[t].moi ? '#F0B429' : t === 'centre' ? '#FF6B63' : '#FFB347';",
           "ctx.lineWidth = 2.6 * e; ctx.strokeStyle = bt[t].moi ? '#F0B429' : t === 'centre' ? '#FF6B63' : t === 'radar' ? '#6EC3F0' : '#FFB347';   // patch371")

# ---------- noms, remboursement ----------
s = rep(s, "  if(type === 'banque') return Number(bqReglage('prix', 20)) || 0;   // patch354",
           "  if(type === 'banque') return Number(bqReglage('prix', 20)) || 0;   // patch354\n  if(type === 'radar') return Number(rdReglage('prix', 30)) || 0;   // patch371")
s = rep(s, "const btNom = (type) => type === 'fonderie' ? 'Fonderie' : type === 'centre' ? 'Centre de recherche' : type === 'banque' ? 'Banque' : 'Forteresse';   // patch354",
           "const btNom = (type) => type === 'fonderie' ? 'Fonderie' : type === 'centre' ? 'Centre de recherche' : type === 'banque' ? 'Banque' : type === 'radar' ? 'Radar' : 'Forteresse';   // patch354, patch371")
s = rep(s, "const r = btRembourse(type, code), a = btArme === code + '|annuler-' + type, le = type === 'centre' ? 'le' : 'la';",
           "const r = btRembourse(type, code), a = btArme === code + '|annuler-' + type, le = type === 'centre' || type === 'radar' ? 'le' : 'la';   // patch371")
s = rep(s, "notifier({ type: 'succes', titre: `${nom} annulé${type === 'centre' ? '' : 'e'}`,",
           "notifier({ type: 'succes', titre: `${nom} annulé${type === 'centre' || type === 'radar' ? '' : 'e'}`,")

# ---------- la fiche de ma commune : ce qui est construit ici ----------
s = rep(s, """  const ce = B.centre && B.centre.code === code ? B.centre : null;   // patch260
  if(ce){
    const P = B.preparation, pret = btPretDans(ce) <= 0, niv = bombeEtat().niv;""",
"""  const rd = B.radar && B.radar.code === code ? B.radar : null;   // patch371 : le Radar
  if(rd){
    const pret = btPretDans(rd) <= 0, nv = (rd.voit || []).length, po = rdReglage('portee_km', 50);
    html += `<div class="bt bt-radar">
      <div class="bt-haut">${ICONE_RADAR}Radar <b>${pret ? (nv ? nv + ' Centre' + (nv > 1 ? 's' : '') + ' en vue' : 'rien en vue') : 'prêt dans ' + formatDuree(btPretDans(rd))}</b></div>
      <p class="bt-txt">Il voit les Centres de recherche à moins de <b>${po} km</b>, même secrets : ils apparaissent sur ta carte, et leur propriétaire est prévenu. Visible de tous : si on te prend ${echapperHtml(c.nom)}, il est détruit. Le détail est dans Défendre.</p>
      ${pret ? '' : btAnnulerHtml(code, 'radar')}
    </div>`;
  }
  const ce = B.centre && B.centre.code === code ? B.centre : null;   // patch260
  if(ce){
    const P = B.preparation, pret = btPretDans(ce) <= 0, niv = bombeEtat().niv;""")
s = rep(s, """      <p class="bt-txt">${ce.devoile ? '<b>Dévoilé</b> : tout le monde le voit sur la carte.' : 'Secret : les autres ne le voient pas sur la carte.'} Si on te prend ${echapperHtml(c.nom)}, il est détruit${P ? ' et ta bombe est perdue' : ''}. Tout se gère dans Défendre.</p>
      ${pret ? '' : btAnnulerHtml(code, 'centre')}""",
"""      <p class="bt-txt">${!pret && P ? '<b>Déménagement en cours</b> : ta bombe est en pause jusqu’à la fin du chantier. ' : ''}${ce.devoile ? '<b>Dévoilé</b> : tout le monde le voit sur la carte.' : (B.repere_par || []).length ? `<b>Repéré</b> par ${(B.repere_par || []).length === 1 ? 'un Radar' : (B.repere_par || []).length + ' Radars'} : son propriétaire le voit sur sa carte.` : 'Secret : les autres ne le voient pas sur la carte.'} Si on te prend ${echapperHtml(c.nom)}, il est détruit${P ? ' et ta bombe est perdue' : ''}. Tout se gère dans Défendre.</p>
      ${pret || P ? '' : btAnnulerHtml(code, 'centre')}""")

# ---------- la fiche de ma commune : ce qu'on peut y construire ----------
s = rep(s, """  return boutons.length ? `<p class="pc-titre-bt">Bâtiments</p><div class="pc-actions pc-actions-bt">${boutons.join('')}</div>` : '';
}
async function batimentConstruire(code, type, style){""",
"""  if(B.radars_ouverts && !B.radar){   // patch371 : le Radar
    const pr = rdReglage('prix', 30), nl = lingotsActuels();
    const bloque = !nF ? 'Il te faut d’abord une Fonderie' : nl < pr ? `Il te faut ${pr} lingots (tu en as ${nl})` : '';
    boutons.push(`<button class="pc-action bt-action${arme('radar') ? ' arme' : ''}" data-pc="bt-construire" data-bt="radar" ${bloque ? 'disabled' : ''}>${ICONE_RADAR}<span>${arme('radar') ? `Confirmer : ${pr} lingots` : 'Construire le Radar ici'}<small>${bloque || `Prêt dans ${h} h · un seul · <b class="bt-plus">voit les Centres de recherche à moins de ${rdReglage('portee_km', 50)} km, même secrets</b> · visible de tous`}</small></span><span class="prix">${pr} ${ICONE_LINGOT}</span></button>`);
  }
  if(B.bombes_ouvertes && B.centre && B.centre.code !== code && btPretDans(B.centre) <= 0){   // patch371 : déménager le Centre ici
    const net = crDemenagerPrix(), nl = lingotsActuels(), n = rdRadarsAutour(code);
    const bloque = btSousAssaut(B.centre.code) ? 'Ton Centre est attaqué : pas de déménagement pendant l’assaut' : nl < net ? `Il te faut ${net} lingots (tu en as ${nl})` : '';
    boutons.push(`<button class="pc-action bt-action${arme('demenager') ? ' arme' : ''}" data-pc="bt-demenager" ${bloque ? 'disabled' : ''}>${ICONE_CENTRE}<span>${arme('demenager') ? `Confirmer : déménager le Centre de ${echapperHtml(B.centre.nom)} ici` : 'Déménager le Centre ici'}<small>${bloque || `Prêt dans ${h} h · ${B.preparation ? 'ta bombe suit, en pause pendant le chantier · ' : ''}<b class="bt-plus">${n ? n + ' Radar' + (n > 1 ? 's' : '') + ' le verrai' + (n > 1 ? 'ent' : 't') + ' ici' : 'aucun Radar ne le voit ici'}</b>`}</small></span><span class="prix">${net} ${ICONE_LINGOT}</span></button>`);
  }
  return boutons.length ? `<p class="pc-titre-bt">Bâtiments</p><div class="pc-actions pc-actions-bt">${boutons.join('')}</div>` : '';
}
// patch371 : déménager son Centre (s2-115) : l'ancien rend 20, le nouveau coûte 40
const crDemenagerPrix = () => Math.max(0, Number(btReglage('centre_prix', 40)) - Number(rdReglage('centre_rendu', 20)));
// les Radars des autres (hors clan) qui verraient un Centre posé sur cette commune
function rdRadarsAutour(code){
  const c = collectionMap.get(code) || othersMap.get(code);
  if(!c || c.lat == null) return 0;
  const po = Number(rdReglage('portee_km', 50)) || 50;
  let n = 0;
  for(const [k, e] of BATIMENTS_CARTE){
    if(!e.radar || e.radar.moi || !e.radar.pret) continue;
    const o = othersMap.get(k);
    if(!o || o.lat == null || (o.joueurId && clanMembres.has(o.joueurId))) continue;
    if(kmEntre(c.lat, c.lon, o.lat, o.lon) <= po) n++;
  }
  return n;
}
async function centreDemenager(code){
  const { error } = await sb.rpc('centre_demenager', { p_code: code });
  if(error) notifier({ type: 'erreur', titre: 'Déménager le Centre', texte: messageLisible(error.message) });
  else {
    const c = collectionMap.get(code);
    notifier({ type: 'succes', titre: 'Centre en déménagement', texte: `${c ? c.nom + ' : p' : 'P'}rêt dans ${btReglage('construction_h', 6)} h.${BATIMENTS && BATIMENTS.preparation ? ' Ta bombe est en pause jusque-là.' : ''}` });
  }
  crDemOuvert = false; crDemRecherche = '';
  await chargerBatiments();
  if(panneauCommune === code && collectionMap.get(code)){ const a = panneauAncre; ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40); }
}
async function batimentConstruire(code, type, style){""")

s = rep(s, """  if(quoi === 'bt-construire'){   // patch243 : deux temps, comme le retrait de garnison""",
"""  if(quoi === 'bt-demenager'){   // patch371 : en deux temps
    if(btArme !== code + '|demenager'){ btArme = code + '|demenager'; const a = panneauAncre; ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40); return; }
    btArme = null;
    b.disabled = true;
    centreDemenager(code);
    return;
  }
  if(quoi === 'bt-construire'){   // patch243 : deux temps, comme le retrait de garnison""")

# ---------- Défendre : le Centre (repéré, déménager) et le Radar ----------
s = rep(s, """  } else if(btPretDans(ce) > 0){
    corps = `<div class="cr">${tete('En construction : prêt dans ' + formatDuree(btPretDans(ce)), badge)}${btAnnulerHtml(ce.code, 'centre')}</div>`;   // patch305""",
"""  } else if(btPretDans(ce) > 0){
    corps = P   // patch371 : un déménagement, la bombe attend
      ? `<div class="cr">${tete('Déménagement : prêt dans ' + formatDuree(btPretDans(ce)), badge)}<p class="cr-txt">Ta bombe est <b>en pause</b> pendant le chantier : elle reprendra à ${formatDuree(bombeEtat().ec * 1000 + btPretDans(ce))} de préparation.</p></div>`
      : `<div class="cr">${tete('En construction : prêt dans ' + formatDuree(btPretDans(ce)), badge)}${btAnnulerHtml(ce.code, 'centre')}</div>`;   // patch305""")
s = rep(s, """  return `<div class="btl-titre">Centre de recherche <em>${ce ? 1 : 0} / 1</em></div>${corps}`;
}""",
"""  return `<div class="btl-titre">Centre de recherche <em>${ce ? 1 : 0} / 1</em></div>${corps}${ce && btPretDans(ce) <= 0 ? crRepereHtml() + crDemenagerHtml(ce) : ''}`;   // patch371
}
// patch371 : qui voit mon Centre
function crRepereHtml(){
  const L = (BATIMENTS && BATIMENTS.repere_par) || [];
  if(!L.length) return '';
  const qui = L.slice(0, 3).map(x => `<b>${echapperHtml(x.pseudo || 'un joueur')}</b> (${String(x.km).replace('.', ',')} km)`).join(', ');
  return `<p class="cr-alerte rd-alerte">${ICONE_RADAR}<span>${L.length === 1 ? 'Le Radar de ' + qui + ' voit ton centre' : L.length + ' Radars voient ton centre : ' + qui}. Il apparaît sur ${L.length === 1 ? 'sa' : 'leur'} carte : déménage-le pour disparaître de ${L.length === 1 ? 'son' : 'leur'} écran.</span></p>`;
}
// patch371 : déménager, depuis Défendre
var crDemOuvert = false, crDemRecherche = '';
function crDemenagerHtml(ce){
  const net = crDemenagerPrix(), n = lingotsActuels(), P = BATIMENTS.preparation;
  const bloque = btSousAssaut(ce.code) ? 'Ton centre est attaqué : pas de déménagement pendant l’assaut.' : n < net ? `Il te faut ${net} lingots pour déménager (tu en as ${n}).` : '';
  if(!crDemOuvert) return `<button type="button" class="cr-dem-b" data-cr-dem ${bloque ? 'disabled' : ''}>${ICONE_CENTRE}Déménager le centre · ${net} ${ICONE_LINGOT}</button>${bloque ? `<p class="cr-manque">${bloque}</p>` : ''}`;
  return `<div class="cr-dem">
    <p class="cr-txt">Ton centre actuel te rend <b>${rdReglage('centre_rendu', 20)} lingots</b>, le nouveau en coûte ${btReglage('centre_prix', 40)} : <b>${net} de ta poche</b>. ${btReglage('construction_h', 6)} h de chantier${P ? ' ; ta bombe suit, <b>en pause</b> pendant le chantier' : ''}.${ce.devoile ? ' Il reste dévoilé à sa nouvelle adresse.' : ''}</p>
    <input type="search" class="bourse-search gn-cherche" id="crDemCherche" placeholder="Choisis la commune où le déménager…" autocomplete="off" value="${echapperTexte(crDemRecherche)}">
    <div class="gn-choix" id="crDemChoix">${crDemChoixHtml(ce)}</div>
    <button type="button" class="cr-dem-x" data-cr-dem>Fermer</button></div>`;
}
function crDemChoixHtml(ce){
  const q = sansAccents(crDemRecherche.trim().toLowerCase());
  const ici = collectionMap.get(ce.code);
  const mes = [...collectionMap.values()].filter(c => c.code !== ce.code
    && (!q || sansAccents(c.nom.toLowerCase()).includes(q) || c.dept === q.toUpperCase()));
  if(!mes.length) return `<p class="gl-vide">${collectionMap.size > 1 ? 'Aucune de tes communes ne correspond.' : 'Il te faut une autre commune.'}</p>`;
  const L = mes.map(c => ({ c, km: ici && ici.lat != null && c.lat != null ? kmEntre(ici.lat, ici.lon, c.lat, c.lon) : null, r: rdRadarsAutour(c.code) }));
  L.sort((a, b) => a.r - b.r || (a.km == null) - (b.km == null) || (a.km || 0) - (b.km || 0));
  const net = crDemenagerPrix();
  return L.slice(0, 6).map(({ c, km, r }) => {
    const a = btArme === c.code + '|demenager';
    return `<div class="gl gn-ligne"><i class="gl-c ${c.tier.id}"></i><div class="gl-t"><b>${echapperTexte(c.nom)}</b>
      <span>${echapperTexte(c.dept)}${km != null ? ' · à ' + Math.round(km) + ' km' : ''} · <em class="${r ? 'rd-vu' : 'rd-ok'}">${r ? r + ' Radar' + (r > 1 ? 's' : '') + ' le verrai' + (r > 1 ? 'ent' : 't') : 'aucun Radar'}</em></span></div>
      <button class="gl-r bt-fortifier${a ? ' arme' : ''}" data-cr-dem-ici="${echapperTexte(c.code)}">${a ? `Confirmer · ${net} lingots` : 'Ici'}</button></div>`;
  }).join('') + (mes.length > 6 ? `<p class="gl-vide">+ ${mes.length - 6} autre${mes.length - 6 > 1 ? 's' : ''} : affine la recherche (les moins exposées aux Radars d’abord).</p>` : '');
}
// patch371 : Défendre, le Radar
function radarHtml(){
  const B = BATIMENTS;
  if(!B || !B.radars_ouverts) return '';
  const r = B.radar, prix = rdReglage('prix', 30), po = rdReglage('portee_km', 50);
  let corps;
  if(!r){
    corps = `<p class="gl-vide">${prix} lingots, une Fonderie demandée. Ouvre une de tes communes sur la carte et choisis « Construire le Radar ici ». Il voit les Centres de recherche à moins de ${po} km, même secrets (pas les Banques), et leur propriétaire est prévenu. Il est visible de tous.</p>`;
  } else {
    const pret = btPretDans(r) <= 0, a = btArme === r.code + '|annuler-radar';
    const fin = pret ? '<span class="btl-etat ok">Actif</span>'
      : btSousAssaut(r.code) ? `<span class="btl-etat cours">prêt dans ${formatDuree(btPretDans(r))}</span>`
      : `<button type="button" class="gl-r bt-ann${a ? ' arme' : ''}" data-bt-annuler="${echapperTexte(r.code)}" data-bt-type="radar">${a ? 'Confirmer ?' : 'Annuler'}</button>`;
    const sous = pret ? `Voit à ${po} km autour` : `Prêt dans ${formatDuree(btPretDans(r))} · ${prix} lingots rendus si tu annules`;
    const V = r.voit || [];
    corps = `<div class="btl"><span class="btl-ic rd-ic">${ICONE_RADAR}</span><span class="btl-t"><button type="button" class="btl-nom" data-voir-carte="${echapperTexte(r.code)}">${echapperTexte(r.nom)} (${echapperTexte(r.dept)})</button><small>${sous}</small></span>${fin}</div>`
      + (!pret ? '' : V.length ? `<div class="rd-liste">${V.map(x => `<div class="rd-l"><span class="rd-km">${String(x.km).replace('.', ',')} km</span><span class="rd-t"><button type="button" class="btl-nom" data-voir-carte="${echapperTexte(x.code)}">Centre de ${echapperTexte(x.nom)} (${echapperTexte(x.dept)})</button><small>${echapperHtml(x.pseudo || 'un joueur')} · ${x.bombe ? '<b class="rd-rouge">bombe en préparation</b>' : 'pas de bombe en préparation'}${x.pret === false ? ' · en construction' : ''}</small></span></div>`).join('')}</div>`
        : `<p class="gl-vide">Aucun Centre de recherche à moins de ${po} km pour l’instant. Dès qu’un joueur en construit un dans ta zone, il apparaît ici et sur ta carte.</p>`);
  }
  return `<div class="btl-titre">Radar <em>${r ? 1 : 0} / 1</em></div>${corps}`;
}""")
s = rep(s, "    ${centreHtml()}\n", "    ${centreHtml()}\n    ${radarHtml()}\n")
s = rep(s, """      const fo = e.target.closest('[data-bt-fortifier]');
      if(!fo) return;""",
"""      if(e.target.closest('[data-cr-dem]')){ crDemOuvert = !crDemOuvert; crDemRecherche = ''; btArme = null; renderBatimentsBloc(); return; }   // patch371
      const dm = e.target.closest('[data-cr-dem-ici]');
      if(dm){
        const k = dm.dataset.crDemIci + '|demenager';
        if(btArme !== k){ btArme = k; const z = document.getElementById('crDemChoix'); if(z && BATIMENTS && BATIMENTS.centre) z.innerHTML = crDemChoixHtml(BATIMENTS.centre); return; }
        btArme = null; dm.disabled = true; centreDemenager(dm.dataset.crDemIci); return;
      }
      const fo = e.target.closest('[data-bt-fortifier]');
      if(!fo) return;""")
s = rep(s, """  const champ = document.getElementById('btCherche');
  if(champ) champ.addEventListener('input', (e) => {""",
"""  const crc = document.getElementById('crDemCherche');   // patch371
  if(crc) crc.addEventListener('input', (e) => {
    crDemRecherche = e.target.value;
    const z = document.getElementById('crDemChoix'); if(z && BATIMENTS && BATIMENTS.centre) z.innerHTML = crDemChoixHtml(BATIMENTS.centre);
  });
  const champ = document.getElementById('btCherche');
  if(champ) champ.addEventListener('input', (e) => {""")

# ---------- l'écran Bâtiments, les fiches, les styles ----------
s = rep(s, "var BT_STYLES_DEFAUT = { fonderie: ['brique', 'acier'], forteresse: ['chateau', 'bastion', 'tour'], banque: ['classique', 'coffre'], centre: ['labo', 'bunker'] };",
           "var BT_STYLES_DEFAUT = { fonderie: ['brique', 'acier'], forteresse: ['chateau', 'bastion', 'tour'], banque: ['classique', 'coffre'], centre: ['labo', 'bunker'], radar: ['parabole', 'dome', 'pylone'] };   // patch371")
s = rep(s, "labo: 'Laboratoire', bunker: 'Bunker' };", "labo: 'Laboratoire', bunker: 'Bunker', parabole: 'Parabole', dome: 'Radôme', pylone: 'Pylône' };")
s = rep(s, "const btFem = (type) => type !== 'centre';   // la Fonderie, la Forteresse, la Banque ; le Centre",
           "const btFem = (type) => type !== 'centre' && type !== 'radar';   // la Fonderie, la Forteresse, la Banque ; le Centre, le Radar (patch371)")
s = rep(s, "  if(BATIMENTS.centre) l.push(Object.assign({}, BATIMENTS.centre, { type: 'centre' }));\n  return l;",
           "  if(BATIMENTS.centre) l.push(Object.assign({}, BATIMENTS.centre, { type: 'centre' }));\n  if(BATIMENTS.radar) l.push(Object.assign({}, BATIMENTS.radar, { type: 'radar' }));   // patch371\n  return l;")
s = rep(s, "  if(type === 'banque') return `Une épargne : jusqu’à ${bqReglage('reserve', 60)} lingots, +${bqReglage('interet', 10)}\u00a0% par nuit. Secrète`;",
           "  if(type === 'banque') return `Une épargne : jusqu’à ${bqReglage('reserve', 60)} lingots, +${bqReglage('interet', 10)}\u00a0% par nuit. Secrète`;\n  if(type === 'radar') return `Voit les Centres de recherche à moins de ${rdReglage('portee_km', 50)} km, même secrets`;   // patch371")
s = rep(s, "  if(b.type === 'banque') return { t: `Secrète · ${Math.floor(Number(b.contenu) || 0)} lingots`, c: 'or' };",
           "  if(b.type === 'banque') return { t: `Secrète · ${Math.floor(Number(b.contenu) || 0)} lingots`, c: 'or' };\n  if(b.type === 'radar'){ const n = (b.voit || []).length; return n ? { t: `${n} Centre${n > 1 ? 's' : ''} en vue`, c: 'rouge' } : { t: 'Rien en vue', c: 'ok' }; }   // patch371")
s = rep(s, "  const types = [['', 'Tous'], ['fonderie', 'Fonderies'], ['forteresse', 'Forteresses'], ['centre', 'Centres']];",
           "  const types = [['', 'Tous'], ['fonderie', 'Fonderies'], ['forteresse', 'Forteresses'], ['radar', 'Radars'], ['centre', 'Centres']];   // patch371")
s = rep(s, "<span>Les Banques sont secrètes : elles n’apparaissent jamais ici. Un Centre n’y apparaît qu’une fois dévoilé.</span>",
           "<span>Les Banques sont secrètes : elles n’apparaissent jamais ici. Un Centre n’y apparaît qu’une fois dévoilé, ou repéré par ton Radar.</span>")
s = rep(s, """      <span class="bte-t"><b>${x.type === 'centre' ? 'Centre dévoilé' : btNom(x.type)} · ${echapperHtml(btStyleNom(btStyleDe(x.type, x.style)))}</b>
        <small>${echapperHtml(x.pseudo || 'un joueur')} · ${echapperHtml(x.nom || x.code)}${x.dept ? ' (' + echapperHtml(x.dept) + ')' : ''}${x.type === 'centre' ? ` · <span class="bte-rouge">${x.centre === 'preparation' ? 'bombe en préparation' : 'a lancé sa bombe'}</span>` : ''}${x.pret === false ? ' · en construction' : ''}</small></span>""",
"""      <span class="bte-t"><b>${x.type === 'centre' ? (x.radar ? 'Centre repéré' : 'Centre dévoilé') : btNom(x.type)} · ${echapperHtml(btStyleNom(btStyleDe(x.type, x.style)))}</b>
        <small>${echapperHtml(x.pseudo || 'un joueur')} · ${echapperHtml(x.nom || x.code)}${x.dept ? ' (' + echapperHtml(x.dept) + ')' : ''}${x.type === 'centre' ? ` · <span class="bte-rouge">${x.centre === 'preparation' ? 'bombe en préparation' : x.centre === 'lancee' ? 'a lancé sa bombe' : 'pas de bombe'}</span>${x.radar ? ' · vu par ton Radar' : ''}` : ''}${x.pret === false ? ' · en construction' : ''}</small></span>""")   # patch371
s = rep(s, """    <div class="btf-titre"><h3>${type === 'centre' && !moi ? 'Centre dévoilé' : btNom(type)}</h3>""",
"""    <div class="btf-titre"><h3>${type === 'centre' && !moi ? (x.radar ? 'Centre repéré' : 'Centre dévoilé') : btNom(type)}</h3>""")
s = rep(s, """    ${!moi && x.pret === false ? '<div class="btf-l"><span>État</span><span>En construction</span></div>' : ''}""",
"""    ${!moi && x.pret === false ? '<div class="btf-l"><span>État</span><span>En construction</span></div>' : ''}
    ${moi && type === 'radar' && (x.voit || []).length ? `<div class="btf-l"><span>En vue</span><span>${x.voit.map(v => `Centre de ${echapperHtml(v.nom)} (${echapperHtml(v.dept)}) · ${echapperHtml(v.pseudo || 'un joueur')} · ${String(v.km).replace('.', ',')} km`).join('<br>')}</span></div>` : ''}
    ${moi && type === 'centre' && (BATIMENTS.repere_par || []).length ? `<div class="btf-l"><span>Repéré</span><span class="bte-e rouge">par ${BATIMENTS.repere_par.map(v => 'le Radar de ' + echapperHtml(v.pseudo || 'un joueur')).join(', ')}</span></div>` : ''}""")   # patch371
s = rep(s, "          : type === 'centre' ? btReglage('centre_prix', 40) : bqReglage('prix', 20);",
           "          : type === 'centre' ? btReglage('centre_prix', 40) : type === 'radar' ? rdReglage('prix', 30) : bqReglage('prix', 20);   // patch371")

# ---------- légende ----------
s = rep(s, "${['fonderie', 'forteresse', 'banque', 'centre'].map(k =>   /* patch357 */ `<button type=\"button\" class=\"leg-bt-info${btBulleCle === k ? ' on' : ''}\" data-bt-info=\"${k}\" aria-expanded=\"${btBulleCle === k}\"><span class=\"leg-bt${k === 'centre' ? ' leg-centre' : ''}\">${k === 'fonderie' ? ICONE_FONDERIE : k === 'forteresse' ? ICONE_FORTERESSE : k === 'banque' ? ICONE_BANQUE : ICONE_CENTRE}</span>",
           "${['fonderie', 'forteresse', 'banque', 'radar', 'centre'].map(k =>   /* patch357, patch371 */ `<button type=\"button\" class=\"leg-bt-info${btBulleCle === k ? ' on' : ''}\" data-bt-info=\"${k}\" aria-expanded=\"${btBulleCle === k}\"><span class=\"leg-bt${k === 'centre' ? ' leg-centre' : k === 'radar' ? ' leg-radar' : ''}\">${k === 'fonderie' ? ICONE_FONDERIE : k === 'forteresse' ? ICONE_FORTERESSE : k === 'banque' ? ICONE_BANQUE : k === 'radar' ? ICONE_RADAR : ICONE_CENTRE}</span>")
s = rep(s, """    pied: 'Pour en construire un : 2 Fonderies et 40 lingots.' },""",
"""    pied: 'Pour en construire un : 2 Fonderies et 40 lingots. Son propriétaire peut le déménager (20 lingots, 6 h).' },
  radar: { titre: 'Radar', role: 'Il trouve les Centres de recherche cachés autour de lui.',   // patch371
    li: ['Coûte <b>30 lingots</b>, un seul par joueur, il faut une Fonderie.', 'Voit les <b>Centres de recherche</b> à moins de <b>50 km</b>, même secrets (pas les Banques).',
         'Le joueur repéré est <b>prévenu</b> : il peut déménager son Centre.', 'Visible de tous. Disparaît si on prend sa commune.'],
    pied: 'Se construit en 6 h sur une de tes communes.' },""")
s = rep(s, "  const ic = k === 'fonderie' ? ICONE_FONDERIE : k === 'forteresse' ? ICONE_FORTERESSE : k === 'banque' ? ICONE_BANQUE : ICONE_CENTRE;   // patch356",
           "  const ic = k === 'fonderie' ? ICONE_FONDERIE : k === 'forteresse' ? ICONE_FORTERESSE : k === 'banque' ? ICONE_BANQUE : k === 'radar' ? ICONE_RADAR : ICONE_CENTRE;   // patch356, patch371")
s = rep(s, """  btBulle.innerHTML = `<h4><span class="leg-bt${k === 'centre' ? ' leg-centre' : ''}">${ic}</span>""",
"""  btBulle.innerHTML = `<h4><span class="leg-bt${k === 'centre' ? ' leg-centre' : k === 'radar' ? ' leg-radar' : ''}">${ic}</span>""")

# ---------- la cloche ----------
s = rep(s, """  if(p.jeu.echange && Array.isArray(d.ech)){
    for(const e of d.ech.filter(x => x.sens === 'recu')){""",
"""  if(SAISON2 && BATIMENTS && Array.isArray(BATIMENTS.repere_par)){   // patch371 : un Radar voit mon Centre
    for(const x of BATIMENTS.repere_par){
      items.push({ cle: `radar|${x.id}|${BATIMENTS.centre ? BATIMENTS.centre.code : ''}`, sec: 'afaire', c: 'danger', i: '📡', mode: 'front',
        t: `Le <b>Radar de ${echapperTexte(x.pseudo || 'un joueur')}</b> voit ton Centre de recherche`,
        s: `Son Radar est à ${echapperTexte(x.nom || '')} (${echapperTexte(x.dept || '')}), à ${String(x.km).replace('.', ',')} km de ton centre`,
        a: 'Déménager', aller: () => ncAller('front', 'defense') });
    }
  }
  if(p.jeu.echange && Array.isArray(d.ech)){
    for(const e of d.ech.filter(x => x.sens === 'recu')){""")

# ---------- le classement ----------
s = rep(s, "Chaque bâtiment terminé : Fonderie <b>+50</b> · Forteresse <b>+80</b> · Centre de recherche <b>+150</b> · Banque <b>+80</b>. Acquis même s’il est détruit, jusqu’au maximum de chaque type (2 Fonderies, 5 Forteresses, 1 Centre, 1 Banque : <b>730</b> au plus).",
           "Chaque bâtiment terminé : Fonderie <b>+50</b> · Forteresse <b>+80</b> · Centre de recherche <b>+150</b> · Banque <b>+80</b> · Radar <b>+80</b>. Acquis même s’il est détruit, jusqu’au maximum de chaque type (2 Fonderies, 5 Forteresses, 1 Centre, 1 Banque, 1 Radar : <b>810</b> au plus).")
s = rep(s, "  else { notifier({ type: 'succes', titre: nom + ' en construction', texte: `Prête dans ${btReglage('construction_h', 6)} h.` }); ppRelire(800); }   // patch306",
           "  else { notifier({ type: 'succes', titre: nom + ' en construction', texte: `${btFem(type) ? 'Prête' : 'Prêt'} dans ${btReglage('construction_h', 6)} h.` }); ppRelire(800); }   // patch306, patch371")
F.write_text(s, encoding='utf-8')

# retouches après l'aperçu : « Repéré » au lieu de « Secret », « pas de bombe » sans rouge
s = rep(s, """  const badge = ce && ce.devoile ? '<span class="cr-secret cr-devoile">Dévoilé</span>' : '<span class="cr-secret">Secret</span>';""",
"""  const badge = ce && ce.devoile ? '<span class="cr-secret cr-devoile">Dévoilé</span>'
    : ((B.repere_par || []).length ? '<span class="cr-secret cr-devoile">Repéré</span>' : '<span class="cr-secret">Secret</span>');   // patch371""")
s = rep(s, "  return b.devoile ? { t: 'Dévoilé : bombe en préparation', c: 'rouge' } : { t: 'Secret', c: 'or' };",
           "  return b.devoile ? { t: 'Dévoilé : bombe en préparation', c: 'rouge' }\n    : (BATIMENTS && (BATIMENTS.repere_par || []).length) ? { t: 'Repéré par un Radar', c: 'rouge' } : { t: 'Secret', c: 'or' };   // patch371")
s = rep(s, "${x.type === 'centre' ? ` · <span class=\"bte-rouge\">${x.centre === 'preparation' ? 'bombe en préparation' : x.centre === 'lancee' ? 'a lancé sa bombe' : 'pas de bombe'}</span>${x.radar ? ' · vu par ton Radar' : ''}` : ''}",
           "${x.type === 'centre' ? (x.centre === 'calme' ? ' · pas de bombe' : ` · <span class=\"bte-rouge\">${x.centre === 'preparation' ? 'bombe en préparation' : 'a lancé sa bombe'}</span>`) + (x.radar ? ' · vu par ton Radar' : '') : ''}")
F.write_text(s, encoding='utf-8')

s = rep(s, "      : `<p class=\"cr-txt cr-dim\">Encore secret ${formatDuree(Math.max(0, dv * 3600 - ec) * 1000)} : ensuite, ton centre apparaît sur la carte.</p>`;",
           "      : `<p class=\"cr-txt cr-dim\">${(B.repere_par || []).length ? 'Caché aux autres joueurs encore' : 'Encore secret'} ${formatDuree(Math.max(0, dv * 3600 - ec) * 1000)} : ensuite, ton centre apparaît sur la carte${(B.repere_par || []).length ? ' de tout le monde' : ''}.</p>`;   // patch371")
F.write_text(s, encoding='utf-8')

# ---------- styles ----------
C = pathlib.Path('style.css'); css = C.read_text(encoding='utf-8')
assert 'patch371' not in css
css += """
/* patch371 : le Radar et le déménagement du Centre */
.leg-bt.leg-radar{ border-color:#6EC3F0; color:#9ED8F6; background:#0E2233; }
.bt-radar .bt-haut svg{ color:#6EC3F0; }
.rd-ic{ color:#6EC3F0; }
.rd-liste{ display:grid; gap:6px; margin:8px 0 4px; }
.rd-l{ display:flex; align-items:center; gap:10px; padding:8px 10px; border-radius:10px; background:rgba(110,195,240,.07); border:1px solid rgba(110,195,240,.28); }
.rd-km{ flex:none; min-width:52px; font-weight:700; font-size:.78rem; color:#9ED8F6; font-variant-numeric:tabular-nums; }
.rd-t{ min-width:0; } .rd-t small{ display:block; font-size:.72rem; color:#A9BCD4; margin-top:2px; }
.rd-rouge{ color:#FF8A82; font-weight:600; }
.rd-alerte{ display:flex; align-items:flex-start; gap:8px; }
.rd-alerte svg{ flex:none; width:18px; height:18px; color:#FF8A82; margin-top:1px; }
.cr-dem-b{ display:flex; align-items:center; justify-content:center; gap:8px; width:100%; margin-top:10px; padding:10px 12px; border-radius:10px;
  background:rgba(156,194,255,.1); border:1px solid rgba(156,194,255,.45); color:#D6E5FF; font:inherit; font-weight:600; font-size:.84rem; cursor:pointer; }
.cr-dem-b svg{ width:17px; height:17px; }
.cr-dem-b:disabled{ opacity:.5; cursor:default; }
.cr-dem{ margin-top:10px; padding:10px; border-radius:12px; background:rgba(156,194,255,.06); border:1px solid rgba(156,194,255,.3); }
.cr-dem .cr-txt{ margin-top:0; }
.cr-dem .gn-cherche{ margin-top:10px; }
.cr-dem-x{ display:block; margin:8px auto 0; background:none; border:0; color:#A9BCD4; font:inherit; font-size:.8rem; text-decoration:underline; cursor:pointer; }
.rd-ok{ font-style:normal; color:#7FE3B4; } .rd-vu{ font-style:normal; color:#FF8A82; }
"""
C.write_text(css, encoding='utf-8')

# ---------- règles ----------
H = pathlib.Path('index.html'); h = H.read_text(encoding='utf-8')
assert 'patch371' not in h
h = rep(h, "<tr><td>Bâtiment terminé, acquis même s'il est détruit, jusqu'au maximum de chaque type : Fonderie · Forteresse · Centre de recherche · Banque</td><td class=\"chiffre or\">+50 · +80 · +150 · +80</td></tr>",
           "<tr><td>Bâtiment terminé, acquis même s'il est détruit, jusqu'au maximum de chaque type : Fonderie · Forteresse · Centre de recherche · Banque · Radar</td><td class=\"chiffre or\">+50 · +80 · +150 · +80 · +80</td></tr><!-- patch371 -->")
h = rep(h, "Pas de bombe à moins de 30 km d'une zone encore active.</p><!-- patch370 -->",
           "Pas de bombe à moins de 30 km d'une zone encore active. Tu peux <b>déménager ton centre</b> sur une autre de tes communes (Défendre › Bâtiments) : l'ancien te rend 20 lingots, le nouveau en coûte 40, 6 h de chantier ; ta bombe suit, en pause pendant le chantier, et un centre dévoilé le reste.</p><!-- patch370, patch371 -->\n"
           "            <p><b>Radar</b> : avec une Fonderie, construis un <b>Radar</b> (30 lingots, un seul). Il voit les <b>Centres de recherche</b> des autres joueurs à moins de <b>50 km</b>, même secrets (pas les Banques, ni ceux de ton clan) : ils apparaissent sur ta carte et dans Défendre, et leur propriétaire est prévenu. Le Radar est visible de tous ; si on prend sa commune, il est détruit.</p><!-- patch371 -->")
H.write_text(h, encoding='utf-8')

# ---------- nouveautés ----------
N = pathlib.Path('data/nouveautes.json'); L = json.loads(N.read_text(encoding='utf-8'))
assert L[0]['date'] == '2026-11-07' and not any('Radar' in x for x in L[0]['nouveautes'])
L[0]['nouveautes'][1:1] = [
  "📡 Radar (30 lingots, une Fonderie) : il voit les Centres de recherche à moins de 50 km, même secrets, et les montre sur ta carte. Le joueur repéré est prévenu. Visible de tous, +80 au classement",
  "🧪 Déménager son Centre de recherche (idée d’Arkhannou) : 20 lingots, 6 h de chantier ; la bombe suit, en pause pendant le chantier. Défendre › Bâtiments, ou « Déménager le Centre ici » sur une de tes communes",
]
N.write_text(json.dumps(L, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch371 appliqué')
