# patch375 (8/11/2026) : déplacer la Banque, et les Radars voient les Banques (s2-117).
#
# Demande de Nataël (8/11, 13 h 32), qui remplace sa décision du 7/11.
#   - Banque : « Déplacer la Banque » dans Défendre (choix de la commune) et
#     « Déplacer la Banque ici » sur la fiche d'une de ses communes ; 10 lingots,
#     6 h, le contenu suit, pas de dépôt ni d'intérêts pendant le chantier (le
#     retrait reste possible), pas pendant un assaut, ne s'annule pas.
#   - Repérée : alerte dans Défendre, ligne dans la cloche, état « Repérée ».
#   - Radar : voit aussi les Banques (Défendre, carte, fiche, « Les autres »,
#     infos) ; prendre la commune d'une Banque repérée : la scène le dit.
#   - Textes : règles, infos des bâtiments.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:80]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch375' not in s, 'patch375 déjà appliqué'

# ---------- la carte : les Banques vues par mon Radar ----------
s = rep(s, "    const vusRadar = new Set(((BATIMENTS.radar && BATIMENTS.radar.voit) || []).map(x => String(x.code)));   // patch371",
           "    const vusRadar = new Set(((BATIMENTS.radar && BATIMENTS.radar.voit) || []).concat((BATIMENTS.radar && BATIMENTS.radar.voit_banques) || []).map(x => String(x.code)));   // patch371, patch375 : les Banques aussi")
s = rep(s, "radar: b.type === 'centre' && vusRadar.has(k) };",
           "radar: (b.type === 'centre' || b.type === 'banque') && vusRadar.has(k) };")
# fiche d'une commune des autres
s = rep(s, "      if(bt.centre) t.push(bt.centre.radar ? 'Centre de recherche (vu par ton Radar)' : 'Centre de recherche dévoilé');",
           """      if(bt.centre) t.push(bt.centre.radar ? 'Centre de recherche (vu par ton Radar)' : 'Centre de recherche dévoilé');
      if(bt.banque) t.push(bt.banque.pret ? 'Banque (vue par ton Radar)' : 'Banque en chantier (vue par ton Radar)');   // patch375""")
# la scène de conquête
s = rep(s, "        + (SAISON2 && (BATIMENTS_CARTE.get(String(cible.code)) || {}).radar ? `<span class=\"as-mon as-bt\">${ICONE_RADAR}Radar détruit</span>` : '')   // patch371",
           """        + (SAISON2 && (BATIMENTS_CARTE.get(String(cible.code)) || {}).radar ? `<span class="as-mon as-bt">${ICONE_RADAR}Radar détruit</span>` : '')   // patch371
        + (SAISON2 && (BATIMENTS_CARTE.get(String(cible.code)) || {}).banque ? `<span class="as-mon as-bt">${ICONE_BANQUE}Banque détruite : tu pilles la moitié de son contenu</span>` : '')   // patch375""")

# ---------- le Radar : ce qu'il voit ----------
s = rep(s, "    const pret = btPretDans(rd) <= 0, nv = (rd.voit || []).length, po = rdReglage('portee_km', 50);",
           "    const pret = btPretDans(rd) <= 0, nv = (rd.voit || []).length + (rd.voit_banques || []).length, po = rdReglage('portee_km', 50);   // patch375")
s = rep(s, "${pret ? (nv ? nv + ' Centre' + (nv > 1 ? 's' : '') + ' en vue' : 'rien en vue') : 'prêt dans ' + formatDuree(btPretDans(rd))}",
           "${pret ? (nv ? nv + ' bâtiment' + (nv > 1 ? 's' : '') + ' en vue' : 'rien en vue') : 'prêt dans ' + formatDuree(btPretDans(rd))}")
s = rep(s, "      <p class=\"bt-txt\">Il voit les Centres de recherche à moins de <b>${po} km</b>, même secrets : ils apparaissent sur ta carte, et leur propriétaire est prévenu.",
           "      <p class=\"bt-txt\">Il voit les Centres de recherche et les Banques à moins de <b>${po} km</b>, même secrets : ils apparaissent sur ta carte, et leur propriétaire est prévenu.")
s = rep(s, "<b class=\"bt-plus\">voit les Centres de recherche à moins de ${rdReglage('portee_km', 50)} km, même secrets</b>",
           "<b class=\"bt-plus\">voit les Centres de recherche et les Banques à moins de ${rdReglage('portee_km', 50)} km, même secrets</b>")
s = rep(s, "Il voit les Centres de recherche à moins de ${po} km, même secrets (pas les Banques), et leur propriétaire est prévenu. Il est visible de tous.</p>`;",
           "Il voit les Centres de recherche et les Banques à moins de ${po} km, même secrets, et leur propriétaire est prévenu. Il est visible de tous.</p>`;")
s = rep(s, """    const V = r.voit || [];""", """    const V = r.voit || [], VB = r.voit_banques || [];   // patch375""")
s = rep(s, """      + (!pret ? '' : V.length ? `<div class="rd-liste">${V.map(""", """      + (!pret ? '' : (V.length || VB.length) ? `<div class="rd-liste">${V.map(""")
s = rep(s, """${x.pret === false ? ' · en construction' : ''}</small></span></div>`).join('')}</div>`
        : `<p class="gl-vide">Aucun Centre de recherche à moins de ${po} km pour l’instant. Dès qu’un joueur en construit un dans ta zone, il apparaît ici et sur ta carte.</p>`);""",
"""${x.pret === false ? ' · en construction' : ''}</small></span></div>`).join('')}${VB.map(x => `<div class="rd-l"><span class="rd-km">${String(x.km).replace('.', ',')} km</span><span class="rd-t"><button type="button" class="btl-nom" data-voir-carte="${echapperTexte(x.code)}">Banque de ${echapperTexte(x.nom)} (${echapperTexte(x.dept)})</button><small>${echapperHtml(x.pseudo || 'un joueur')} · <b class="rd-or">prends sa commune : tu pilles la moitié de son contenu</b>${x.pret === false ? ' · en chantier' : ''}</small></span></div>`).join('')}</div>`
        : `<p class="gl-vide">Aucun Centre de recherche ni aucune Banque à moins de ${po} km pour l’instant. Dès qu’un joueur en construit un dans ta zone, il apparaît ici et sur ta carte.</p>`);""")
# état, effet, fiche du bâtiment, « Les autres »
s = rep(s, "  if(b.type === 'radar'){ const n = (b.voit || []).length; return n ? { t: `${n} Centre${n > 1 ? 's' : ''} en vue`, c: 'rouge' } : { t: 'Rien en vue', c: 'ok' }; }   // patch371",
           "  if(b.type === 'radar'){ const n = (b.voit || []).length + (b.voit_banques || []).length; return n ? { t: `${n} bâtiment${n > 1 ? 's' : ''} en vue`, c: 'rouge' } : { t: 'Rien en vue', c: 'ok' }; }   // patch371, patch375")
s = rep(s, "  if(b.type === 'banque') return { t: `Secrète · ${Math.floor(Number(b.contenu) || 0)} lingots`, c: 'or' };",
           "  if(b.type === 'banque') return bqReperee().length ? { t: `Repérée par un Radar · ${Math.floor(Number(b.contenu) || 0)} lingots`, c: 'rouge' } : { t: `Secrète · ${Math.floor(Number(b.contenu) || 0)} lingots`, c: 'or' };   // patch375")
s = rep(s, "  if(type === 'banque') return `Une épargne : jusqu’à ${bqReglage('reserve', 60)} lingots, +${bqReglage('interet', 10)}\u00a0% par nuit. Secrète`;",
           "  if(type === 'banque') return moi ? `Une épargne : jusqu’à ${bqReglage('reserve', 60)} lingots, +${bqReglage('interet', 10)}\u00a0% par nuit. Secrète, sauf pour les Radars` : 'Son épargne. Prendre sa commune pille la moitié de son contenu';   // patch375")
s = rep(s, "  if(type === 'radar') return `Voit les Centres de recherche à moins de ${rdReglage('portee_km', 50)} km, même secrets`;   // patch371",
           "  if(type === 'radar') return `Voit les Centres de recherche et les Banques à moins de ${rdReglage('portee_km', 50)} km, même secrets`;   // patch371, patch375")
s = rep(s, "<b>${x.type === 'centre' ? (x.radar ? 'Centre repéré' : 'Centre dévoilé') : btNom(x.type)} · ",
           "<b>${x.type === 'centre' ? (x.radar ? 'Centre repéré' : 'Centre dévoilé') : x.type === 'banque' ? 'Banque repérée' : btNom(x.type)} · ")
s = rep(s, "<h3>${type === 'centre' && !moi ? (x.radar ? 'Centre repéré' : 'Centre dévoilé') : btNom(type)}</h3>",
           "<h3>${type === 'centre' && !moi ? (x.radar ? 'Centre repéré' : 'Centre dévoilé') : type === 'banque' && !moi ? 'Banque repérée' : btNom(type)}</h3>")
s = rep(s, "    ${moi && type === 'radar' && (x.voit || []).length ? `<div class=\"btf-l\"><span>En vue</span><span>${x.voit.map(v => `Centre de ${echapperHtml(v.nom)} (${echapperHtml(v.dept)}) · ${echapperHtml(v.pseudo || 'un joueur')} · ${String(v.km).replace('.', ',')} km`).join('<br>')}</span></div>` : ''}",
           "    ${moi && type === 'radar' && ((x.voit || []).length || (x.voit_banques || []).length) ? `<div class=\"btf-l\"><span>En vue</span><span>${(x.voit || []).map(v => `Centre de ${echapperHtml(v.nom)} (${echapperHtml(v.dept)}) · ${echapperHtml(v.pseudo || 'un joueur')} · ${String(v.km).replace('.', ',')} km`).concat((x.voit_banques || []).map(v => `Banque de ${echapperHtml(v.nom)} (${echapperHtml(v.dept)}) · ${echapperHtml(v.pseudo || 'un joueur')} · ${String(v.km).replace('.', ',')} km`)).join('<br>')}</span></div>` : ''}")
s = rep(s, "    ${moi && type === 'centre' && (BATIMENTS.repere_par || []).length ? ",
           "    ${moi && type === 'banque' && bqReperee().length ? `<div class=\"btf-l\"><span>Repérée</span><span class=\"bte-e rouge\">par ${bqReperee().map(v => 'le Radar de ' + echapperHtml(v.pseudo || 'un joueur')).join(', ')}</span></div>` : ''}\n    ${moi && type === 'centre' && (BATIMENTS.repere_par || []).length ? ")
s = rep(s, "  const types = [['', 'Tous'], ['fonderie', 'Fonderies'], ['forteresse', 'Forteresses'], ['radar', 'Radars'], ['centre', 'Centres']];   // patch371",
           "  const types = [['', 'Tous'], ['fonderie', 'Fonderies'], ['forteresse', 'Forteresses'], ['radar', 'Radars'], ['centre', 'Centres'], ['banque', 'Banques']];   // patch371, patch375")

# ---------- la cloche : ma Banque repérée ----------
s = rep(s, """  if(SAISON2 && BATIMENTS && Array.isArray(BATIMENTS.repere_par)){   // patch371 : un Radar voit mon Centre""",
"""  if(SAISON2 && BATIMENTS && Array.isArray(BATIMENTS.banque_reperee_par)){   // patch375 : un Radar voit ma Banque
    for(const x of BATIMENTS.banque_reperee_par){
      items.push({ cle: `radarbq|${x.id}|${BATIMENTS.banque ? BATIMENTS.banque.code : ''}`, sec: 'afaire', c: 'danger', i: '📡', mode: 'front',
        t: `Le <b>Radar de ${echapperTexte(x.pseudo || 'un joueur')}</b> voit ta Banque`,
        s: `Son Radar est à ${echapperTexte(x.nom || '')} (${echapperTexte(x.dept || '')}), à ${String(x.km).replace('.', ',')} km de ta Banque`,
        a: 'Déplacer', aller: () => ncAller('front', 'defense') });
    }
  }
  if(SAISON2 && BATIMENTS && Array.isArray(BATIMENTS.repere_par)){   // patch371 : un Radar voit mon Centre""")

# ---------- ma Banque : fiche, Défendre, déplacer ----------
s = rep(s, """function banqueGestionHtml(){
  const B = BATIMENTS; if(!B || !B.banque || !bqEpargne()) return '';
  const bq = B.banque, pret = btPretDans(bq) <= 0;""",
"""// patch375 : la Banque repérée par des Radars, et la déplacer (s2-117)
const bqReperee = () => (BATIMENTS && BATIMENTS.banque_reperee_par) || [];
const bqDepPrix = () => Number(bqReglage('deplacer_prix', 10)) || 0;
var bqDepOuvert = false, bqDepRecherche = '';
function bqSecretTexte(){
  const L = bqReperee();
  return L.length ? `<b>Repérée</b> par ${L.length === 1 ? 'le Radar de ' + echapperHtml(L[0].pseudo || 'un joueur') : L.length + ' Radars'} : ${L.length === 1 ? 'il la voit' : 'ils la voient'} sur ${L.length === 1 ? 'sa' : 'leur'} carte. Déplace-la pour disparaître de ${L.length === 1 ? 'son' : 'leur'} écran.`
    : `Secrète : seuls les Radars des autres à moins de ${rdReglage('portee_km', 50)} km la voient.`;
}
function bqRepereHtml(){
  const L = bqReperee();
  if(!L.length) return '';
  const qui = L.slice(0, 3).map(x => `<b>${echapperHtml(x.pseudo || 'un joueur')}</b> (${String(x.km).replace('.', ',')} km)`).join(', ');
  return `<p class="cr-alerte rd-alerte">${ICONE_RADAR}<span>${L.length === 1 ? 'Le Radar de ' + qui + ' voit ta Banque. S’il prend sa commune' : L.length + ' Radars voient ta Banque : ' + qui + '. Si l’un d’eux prend sa commune'}, il pille la moitié de son contenu : déplace-la pour disparaître de ${L.length === 1 ? 'son' : 'leur'} écran.</span></p>`;
}
function bqDepHtml(bq){
  if(btPretDans(bq) > 0) return '';
  const prix = bqDepPrix(), n = lingotsActuels();
  const bloque = btSousAssaut(bq.code) ? 'Ta Banque est attaquée : pas de déplacement pendant l’assaut.' : n < prix ? `Il te faut ${prix} lingots pour la déplacer (tu en as ${n}).` : '';
  if(!bqDepOuvert) return `<button type="button" class="cr-dem-b bq-dem-b" data-bq-dep ${bloque ? 'disabled' : ''}>${ICONE_BANQUE}Déplacer la Banque · ${prix} ${ICONE_LINGOT}</button>${bloque ? `<p class="cr-manque">${bloque}</p>` : ''}`;
  return `<div class="cr-dem">
    <p class="cr-txt"><b>${prix} lingots</b>, <b>${btReglage('construction_h', 6)} h de chantier</b> : son contenu la suit. Pendant le chantier, ni dépôt ni intérêts (tu peux retirer). Un déplacement ne s’annule pas.${bqReperee().length ? ' Les Radars qui la voient ici la perdent de vue.' : ''}</p>
    <input type="search" class="bourse-search gn-cherche" id="bqDepCherche" placeholder="Choisis la commune où la cacher…" autocomplete="off" value="${echapperTexte(bqDepRecherche)}">
    <div class="gn-choix" id="bqDepChoix">${bqDepChoixHtml(bq)}</div>
    <button type="button" class="cr-dem-x" data-bq-dep>Fermer</button></div>`;
}
// les Radars des autres (hors clan) qui verraient une Banque posée ici : même calcul que pour le Centre
function bqDepChoixHtml(bq){
  const q = sansAccents(bqDepRecherche.trim().toLowerCase());
  const ici = collectionMap.get(bq.code);
  const mes = [...collectionMap.values()].filter(c => c.code !== bq.code
    && (!q || sansAccents(c.nom.toLowerCase()).includes(q) || c.dept === q.toUpperCase()));
  if(!mes.length) return `<p class="gl-vide">${collectionMap.size > 1 ? 'Aucune de tes communes ne correspond.' : 'Il te faut une autre commune.'}</p>`;
  const L = mes.map(c => ({ c, km: ici && ici.lat != null && c.lat != null ? kmEntre(ici.lat, ici.lon, c.lat, c.lon) : null, r: rdRadarsAutour(c.code) }));
  L.sort((a, b) => a.r - b.r || (a.km == null) - (b.km == null) || (a.km || 0) - (b.km || 0));
  const prix = bqDepPrix();
  return L.slice(0, 6).map(({ c, km, r }) => {
    const a = btArme === c.code + '|bqdep';
    return `<div class="gl gn-ligne"><i class="gl-c ${c.tier.id}"></i><div class="gl-t"><b>${echapperTexte(c.nom)}</b>
      <span>${echapperTexte(c.dept)}${km != null ? ' · à ' + Math.round(km) + ' km' : ''} · <em class="${r ? 'rd-vu' : 'rd-ok'}">${r ? r + ' Radar' + (r > 1 ? 's' : '') + ' la verrai' + (r > 1 ? 'ent' : 't') : 'aucun Radar'}</em></span></div>
      <button class="gl-r bt-fortifier${a ? ' arme' : ''}" data-bq-dep-ici="${echapperTexte(c.code)}">${a ? `Confirmer · ${prix} lingots` : 'Ici'}</button></div>`;
  }).join('') + (mes.length > 6 ? `<p class="gl-vide">+ ${mes.length - 6} autre${mes.length - 6 > 1 ? 's' : ''} : affine la recherche (les moins exposées aux Radars d’abord).</p>` : '');
}
async function banqueDeplacer(code){
  const { error } = await sb.rpc('banque_deplacer', { p_vers: code });
  if(error) notifier({ type: 'erreur', titre: 'Déplacer la Banque', texte: messageLisible(error.message) });
  else {
    const c = collectionMap.get(code);
    notifier({ type: 'succes', titre: 'Banque en route', texte: `${c ? c.nom + ' : p' : 'P'}rête dans ${btReglage('construction_h', 6)} h, avec son contenu. D’ici là, ni dépôt ni intérêts.` });
  }
  bqDepOuvert = false; bqDepRecherche = '';
  await chargerBatiments();
  if(panneauCommune === code && collectionMap.get(code)){ const a = panneauAncre; ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40); }
}

function banqueGestionHtml(){
  const B = BATIMENTS; if(!B || !B.banque || !bqEpargne()) return '';
  const bq = B.banque, pret = btPretDans(bq) <= 0, route = !!bq.deplacee && !pret;   // patch375""")
s = rep(s, """<small>Secrète · ${pret ? `${bqReglage('interet', 10)} % par nuit` : 'prête dans ' + formatDuree(btPretDans(bq))}</small></span>""",
           """<small>${bqReperee().length ? '<b class="rd-rouge">Repérée</b>' : 'Secrète'} · ${pret ? `${bqReglage('interet', 10)} % par nuit` : (route ? 'en route, prête dans ' : 'prête dans ') + formatDuree(btPretDans(bq))}</small></span>""")
s = rep(s, """    <div class="bq-ligne"><span>Retirer</span>${bouton('retrait', Math.min(5, dedans), '5')}${bouton('retrait', Math.min(10, dedans), '10')}${bouton('retrait', dedans, `Tout (${dedans})`)}</div>` : ''}
  </div>`;""",
"""    <div class="bq-ligne"><span>Retirer</span>${bouton('retrait', Math.min(5, dedans), '5')}${bouton('retrait', Math.min(10, dedans), '10')}${bouton('retrait', dedans, `Tout (${dedans})`)}</div>` : ''}
    ${route ? `<p class="bq-nuit">Déplacement en cours : ni dépôt ni intérêts jusqu’à la fin du chantier.</p>
    <div class="bq-ligne"><span>Retirer</span>${bouton('retrait', Math.min(5, dedans), '5')}${bouton('retrait', Math.min(10, dedans), '10')}${bouton('retrait', dedans, `Tout (${dedans})`)}</div>` : ''}
  </div>${bqRepereHtml()}${bqDepHtml(bq)}`;   // patch375""")
# Défendre : clics et recherche
s = rep(s, """      if(bqb){ bqb.disabled = true; banqueMouvement(bqb.dataset.bq, Number(bqb.dataset.bqN) || 0); return; }""",
"""      if(bqb){ bqb.disabled = true; banqueMouvement(bqb.dataset.bq, Number(bqb.dataset.bqN) || 0); return; }
      if(e.target.closest('[data-bq-dep]')){ bqDepOuvert = !bqDepOuvert; bqDepRecherche = ''; btArme = null; renderBatimentsBloc(); return; }   // patch375
      const bqi = e.target.closest('[data-bq-dep-ici]');
      if(bqi){
        const k = bqi.dataset.bqDepIci + '|bqdep';
        if(btArme !== k){ btArme = k; const z = document.getElementById('bqDepChoix'); if(z && BATIMENTS && BATIMENTS.banque) z.innerHTML = bqDepChoixHtml(BATIMENTS.banque); return; }
        btArme = null; bqi.disabled = true; banqueDeplacer(bqi.dataset.bqDepIci); return;
      }""")
s = rep(s, """  const ftc = document.getElementById('ftDepCherche');   // patch374""",
"""  const bqc = document.getElementById('bqDepCherche');   // patch375
  if(bqc) bqc.addEventListener('input', (e) => {
    bqDepRecherche = e.target.value;
    const z = document.getElementById('bqDepChoix'); if(z && BATIMENTS && BATIMENTS.banque) z.innerHTML = bqDepChoixHtml(BATIMENTS.banque);
  });
  const ftc = document.getElementById('ftDepCherche');   // patch374""")
# fiche de ma Banque
s = rep(s, """    const pret = btPretDans(bq) <= 0, res = Number(bqReglage('reserve', 60)) || 60, dedans = Math.min(res, Number(bq.contenu) || 0);
    html += `<div class="bt bt-banque">
      <div class="bt-haut">${ICONE_BANQUE}Banque <b>${pret ? `${dedans} / ${res} ${ICONE_LINGOT}` : 'prête dans ' + formatDuree(btPretDans(bq))}</b></div>""",
"""    const pret = btPretDans(bq) <= 0, res = Number(bqReglage('reserve', 60)) || 60, dedans = Math.min(res, Number(bq.contenu) || 0);
    const route = !!bq.deplacee && !pret;   // patch375
    html += `<div class="bt bt-banque">
      <div class="bt-haut">${ICONE_BANQUE}Banque <b>${pret ? `${dedans} / ${res} ${ICONE_LINGOT}` : (route ? `en route · ${dedans} ${ICONE_LINGOT} · ` : '') + 'prête dans ' + formatDuree(btPretDans(bq))}</b></div>""")
s = rep(s, """(jusqu’à ${res}). Pour les dépenser, retire-les. Secrète : les autres ne la voient pas sur la carte.` : `Ce qui dépasse""",
           """(jusqu’à ${res}). Pour les dépenser, retire-les. ${route ? '<b>Déplacement en cours</b> : ni dépôt ni intérêts avant la fin du chantier. ' : ''}${bqSecretTexte()}` : `Ce qui dépasse""")
s = rep(s, """      ${pret ? '' : btAnnulerHtml(code, 'banque')}
    </div>`;""",
"""      ${pret || route ? '' : btAnnulerHtml(code, 'banque')}
    </div>`;""")
# fiche d'une autre de mes communes : « Déplacer la Banque ici »
s = rep(s, "<b class=\"bt-plus\">${bqEpargne() ? `épargne jusqu’à ${bqReglage('reserve', 60)}, +${bqReglage('interet', 10)} % par nuit` : `+${bqReglage('reserve', 60)} lingots de réserve`}</b> · secrète : les autres ne la voient pas sur la carte`}",
           "<b class=\"bt-plus\">${bqEpargne() ? `épargne jusqu’à ${bqReglage('reserve', 60)}, +${bqReglage('interet', 10)} % par nuit` : `+${bqReglage('reserve', 60)} lingots de réserve`}</b> · secrète, sauf pour les Radars`}")
s = rep(s, """  if(B.radars_ouverts && !B.radar){   // patch371 : le Radar""",
"""  if(B.banque && B.banque.code !== code && btPretDans(B.banque) <= 0){   // patch375 : déplacer la Banque ici
    const pd = bqDepPrix(), nl = lingotsActuels(), n = rdRadarsAutour(code);
    const bloque = btSousAssaut(B.banque.code) ? 'Ta Banque est attaquée : pas de déplacement pendant l’assaut' : nl < pd ? `Il te faut ${pd} lingots (tu en as ${nl})` : '';
    boutons.push(`<button class="pc-action bt-action${arme('bqdep') ? ' arme' : ''}" data-pc="bt-bq-dep" ${bloque ? 'disabled' : ''}>${ICONE_BANQUE}<span>${arme('bqdep') ? `Confirmer : la Banque de ${echapperHtml(B.banque.nom)} vient ici` : 'Déplacer la Banque ici'}<small>${bloque || `Prête dans ${h} h · son contenu suit · <b class="bt-plus">${n ? n + ' Radar' + (n > 1 ? 's' : '') + ' la verrai' + (n > 1 ? 'ent' : 't') + ' ici' : 'aucun Radar ne la voit ici'}</b>`}</small></span><span class="prix">${pd} ${ICONE_LINGOT}</span></button>`);
  }
  if(B.radars_ouverts && !B.radar){   // patch371 : le Radar""")
s = rep(s, """  if(quoi === 'bt-ft-dep'){ btArme = code + '|ftdep';""",
"""  if(quoi === 'bt-bq-dep'){   // patch375 : en deux temps
    if(btArme !== code + '|bqdep'){ btArme = code + '|bqdep'; const a = panneauAncre; ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40); return; }
    btArme = null; b.disabled = true; banqueDeplacer(code); return;
  }
  if(quoi === 'bt-ft-dep'){ btArme = code + '|ftdep';""")

# ---------- infos des bâtiments ----------
s = rep(s, """  radar: { titre: 'Radar', role: 'Il trouve les Centres de recherche cachés autour de lui.',   // patch371
    li: ['Coûte <b>30 lingots</b>, un seul par joueur, il faut une Fonderie.', 'Voit les <b>Centres de recherche</b> à moins de <b>50 km</b>, même secrets (pas les Banques).',
         'Le joueur repéré est <b>prévenu</b> : il peut déménager son Centre.',""",
"""  radar: { titre: 'Radar', role: 'Il trouve les Centres de recherche et les Banques cachés autour de lui.',   // patch371, patch375
    li: ['Coûte <b>30 lingots</b>, un seul par joueur, il faut une Fonderie.', 'Voit les <b>Centres de recherche</b> et les <b>Banques</b> à moins de <b>50 km</b>, même secrets.',
         'Le joueur repéré est <b>prévenu</b> : il peut déménager son Centre ou déplacer sa Banque.',""")
s = rep(s, "         '<b>Secrète</b> : toi seul la vois sur la carte.', 'Si on prend sa commune",
           "         '<b>Secrète</b>, sauf pour les Radars des autres à moins de 50 km. Elle se déplace pour 10 lingots.', 'Si on prend sa commune")
F.write_text(s, encoding='utf-8')

# ---------- règles ----------
H = pathlib.Path('index.html'); h = H.read_text(encoding='utf-8')
assert 'patch375' not in h
h = rep(h, "Elle est <b>secrète</b> : les autres ne la voient pas sur la carte. Si on prend sa commune",
           "Elle est <b>secrète</b>, sauf pour les Radars des autres joueurs à moins de 50 km. Tu peux la <b>déplacer</b> sur une autre de tes communes pour 10 lingots (Défendre › Bâtiments, ou la fiche de la commune) : son contenu la suit ; 6 h de chantier sans dépôt ni intérêts, pas pendant un assaut, et ça ne s'annule pas.<!-- patch375 --> Si on prend sa commune")
h = rep(h, "Il voit les <b>Centres de recherche</b> des autres joueurs à moins de <b>50 km</b>, même secrets (pas les Banques, ni ceux de ton clan) : ils apparaissent sur ta carte et dans Défendre, et leur propriétaire est prévenu.",
           "Il voit les <b>Centres de recherche</b> et les <b>Banques</b> des autres joueurs à moins de <b>50 km</b>, même secrets (pas ceux de ton clan) : ils apparaissent sur ta carte et dans Défendre, et leur propriétaire est prévenu.<!-- patch375 -->")
H.write_text(h, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch375' not in c
c += """
/* patch375 : Banque repérée, déplacer la Banque */
.rd-or{ font-weight:600; color:#F0B429; }
.bq-dem-b{ margin-top:10px; }
"""
C.write_text(c, encoding='utf-8')
print('patch375 ok')
