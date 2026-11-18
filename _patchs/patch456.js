
// ---------- patch456 : saison 3 — l'Artillerie, la Centrale de clan, les ordres du chef (s3-27) ----------
// Tout dépend du serveur : tant que s3-27 n'est pas lancé, ou que ses interrupteurs sont éteints
// (config_jeu 'batiments'.artilleries_ouvertes, 'centrale_clan'.ouverte, 'ordres_chef'.ouverts), rien ne s'affiche.
var S3C = { centrale: null, ordres: null, lu: 0, charge: null, arme: null };
var ICONE_ARTILLERIE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round" d="M3.6 13.8 16.4 7l1.8 3.2L5.4 17M18.8 8l2.2-1.2M10.5 18.5h9.5"/><circle cx="7.6" cy="18" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>';
var ICONE_CENTRALE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round" d="M4.5 21c1.4-3.6 1.4-8.4 0-12h7c-1.4 3.6-1.4 8.4 0 12zM14 21v-8h6.5v8M2.5 21h19M6 6c0-1.6 1.2-2.6 2.6-2.4.6-1.2 2.6-1.2 3 .3"/><path fill="currentColor" d="M18.4 13.8l-2.6 3.7h1.7l-1 2.6 2.9-3.9h-1.7z"/></svg>';
var ICONE_CIBLE = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.6" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="4.3" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="1.4" fill="currentColor"/><path stroke="currentColor" stroke-width="1.8" stroke-linecap="round" d="M12 1.5v3.2M12 19.3v3.2M1.5 12h3.2M19.3 12h3.2"/></svg>';
if(typeof BT_TRACES !== 'undefined' && BT_TRACES){
  BT_TRACES.artillerie = [new Path2D('M3.6 13.8 16.4 7l1.8 3.2L5.4 17M18.8 8l2.2-1.2M10.5 18.5h9.5M10.6 18a3 3 0 1 1-6 0a3 3 0 1 1 6 0')];
  BT_TRACES.centrale = [new Path2D('M4.5 21c1.4-3.6 1.4-8.4 0-12h7c-1.4 3.6-1.4 8.4 0 12zM14 21v-8h6.5v8M2.5 21h19'), new Path2D('M18.4 13.8l-2.6 3.7h1.7l-1 2.6 2.9-3.9h-1.7z')];
}
function s3Art(){ return !!(BATIMENTS && BATIMENTS.artilleries_ouvertes); }
function s3ArtR(k, d){ const R = BATIMENTS && BATIMENTS.artillerie_reglages; return R && R[k] != null ? R[k] : d; }
function s3CentraleOk(){ const c = S3C.centrale; return !!(c && c.ouverte && c.clan); }
function s3OrdresOk(){ const o = S3C.ordres; return !!(o && o.ouverts && o.clan); }
function s3Ordre(code){ return s3OrdresOk() ? (S3C.ordres.ordres || []).find(o => String(o.code) === String(code)) || null : null; }
const s3Km = (x) => String(x).replace('.', ',');

// ---- chargement : l'état de la Centrale et des ordres de mon clan
async function s3Charger(force){
  if(!SAISON2 || !CLANS) return;
  if(S3C.charge) return S3C.charge;
  if(!force && Date.now() - S3C.lu < 60e3) return;
  S3C.charge = (async () => {
    try{
      const [c, o] = await Promise.all([sb.rpc('clan_centrale_etat'), sb.rpc('clan_ordres_etat')]);
      S3C.centrale = c && !c.error ? c.data : null;
      S3C.ordres = o && !o.error ? o.data : null;
      S3C.lu = Date.now();
      s3Rendre(false);
    }catch(e){}
    finally{ S3C.charge = null; }
  })();
  return S3C.charge;
}
setInterval(() => { if(document.visibilityState === 'visible') s3Charger(); }, 120e3);
function s3Rendre(fiche){
  const ce = S3C.centrale && S3C.centrale.centrale;   // la Centrale de mon clan compte comme « à moi » sur la carte
  if(ce && BATIMENTS_CARTE){ const e = BATIMENTS_CARTE.get(String(ce.code)); if(e && e.centrale) e.centrale.moi = true; }
  try{ if(typeof mfoRendre === 'function') mfoRendre(); }catch(e){}
  s3MajClan();
  try{ if(typeof demanderDessin === 'function' && canvasActif()){ CV.donneesSignature = null; demanderDessin(); } }catch(e){}
  if(fiche && panneauCommune){ const a = panneauAncre; try{ ouvrirPanneau(panneauCommune, a ? a.x : 40, a ? a.y : 40); }catch(e){} }
}

// ---- les ordres du chef : une ligne (Mon front et l'onglet Clan)
function s3OrdreLigne(o, O){
  const reste = Math.max(0, new Date(o.fin).getTime() - Date.now());
  const t = TIERS.find(x => x.id === o.tier);
  const n = Number(o.membres_siege) || 0;
  const sous = o.prise ? '<b class="s3o-prise">Prise par ton clan ✓</b>'
    : `${o.proprio ? 'tenue par ' + echapperHtml(o.proprio) : ''}${n ? ` · <b>${n}</b> du clan ${n > 1 ? 'l’assiègent' : 'l’assiège'}` : ' · personne du clan dessus'}`;
  const act = o.prise || o.a_moi ? '' : `<button type="button" class="mfo-btn mfo-rouge s3o-go" data-sg-ouvrir="${echapperTexte(o.code)}">${o.mon_siege ? 'Continuer' : 'Assiéger'}</button>`;
  const ar = S3C.arme === 'retirer-' + o.id;
  const chef = O.je_gere ? `<div class="s3o-chef">${o.prise ? '' : `<button type="button" class="s3o-mini" data-s3="appel" data-id="${o.id}" ${o.appel_dans > 0 ? 'disabled' : ''}>📯 ${o.appel_dans > 0 ? 'Nouvel appel dans ' + formatDuree(o.appel_dans * 1000) : 'Appel à l’assaut'}</button>`}<button type="button" class="s3o-mini sec${ar ? ' arme' : ''}" data-s3="retirer" data-id="${o.id}">${ar ? 'Confirmer : retirer' : 'Retirer'}</button></div>` : '';
  return `<div class="s3o-l${o.prise ? ' prise' : ''}"><span class="s3o-ic">${ICONE_CIBLE}</span><div class="s3o-t"><div class="s3o-tl"><button type="button" class="s3o-nom" data-voir-carte="${echapperTexte(o.code)}">${echapperHtml(o.nom)} <small>(${echapperHtml(o.dept)})</small></button>${t ? `<span class="s3o-tier ${o.tier}">${t.label}</span>` : ''}</div>
      <small>${sous}</small><small class="s3o-fin">posée par ${echapperHtml(o.pose_par || 'le chef')} · encore ${formatDuree(reste)}</small></div>${act}${chef}</div>`;
}
function s3MfoOrdres(){
  if(!s3OrdresOk()) return '';
  const O = S3C.ordres, L = O.ordres || [];
  if(!L.length && !O.je_gere) return '';
  return `<div class="mfo-t s3o-bloc"><div class="mfo-h"><span>${ICONE_CIBLE}Ordres du chef</span><span class="s3o-n">${L.length} / ${O.max}</span></div>
    ${L.map(o => s3OrdreLigne(o, O)).join('') || '<p class="mfo-p">Aucune cible. Touche une commune ennemie sur la carte, puis « Cible du clan » : tout ton clan la verra ici et sur sa carte.</p>'}</div>`;
}
// ---- la Centrale dans Mon front (sous l'énergie, comme la récolte)
function s3MfoCentrale(){
  if(!s3CentraleOk()) return '';
  const C = S3C.centrale, ce = C.centrale, I = `<span class="s3c-ic">${ICONE_CENTRALE}</span>`;
  if(!ce) return `<div class="mfo-rc s3c-rc"><span>${I}Centrale du clan : caisse ${C.caisse} / ${C.prix} ${ICONE_LINGOT}</span><button type="button" class="mfo-btn mfo-sec" data-s3="vers-clan">Donner ›</button></div>`;
  if(!ce.pret) return `<div class="mfo-rc s3c-rc"><span>${I}Centrale du clan : prête dans ${formatDuree(new Date(ce.pret_le).getTime() - Date.now())}</span></div>`;
  if(C.ramasse) return `<div class="mfo-rc s3c-rc"><span>${I}Centrale : +${C.ramasse_energie} ramassée aujourd’hui</span><span class="mfo-ok">✓ demain</span></div>`;
  if(C.ancien_dans > 0) return `<div class="mfo-rc s3c-rc"><span>${I}Centrale : ta part dans ${formatDuree(C.ancien_dans * 1000)}</span></div>`;
  return `<div class="mfo-rc s3c-rc"><span>${I}Centrale du clan</span><button type="button" class="mfo-btn mfo-or" data-s3="ramasser">Ramasser +${C.part} ⚡</button></div>`;
}
// ---- l'onglet Clan
function s3ClanBlocs(){ return `<div data-s3-clan>${s3ClanHtml()}</div>`; }
function s3MajClan(){ const el = document.querySelector('[data-s3-clan]'); if(el) el.innerHTML = s3ClanHtml(); }
function s3ClanHtml(){
  let h = '';
  if(s3CentraleOk()) h += s3CentraleHtml();
  if(s3OrdresOk()){
    const O = S3C.ordres, L = O.ordres || [];
    h += `<div class="s3-carte"><h3>${ICONE_CIBLE}Ordres du chef <small>${L.length} / ${O.max} cibles · ${O.duree_h} h chacune</small></h3>
      ${L.map(o => s3OrdreLigne(o, O)).join('') || `<p class="clan-note">${O.je_gere ? 'Aucune cible. Touche une commune ennemie sur la carte, puis « Cible du clan » : ton clan la verra sur sa carte et dans Mon front. Un appel à l’assaut prévient tout le monde.' : 'Aucune cible pour l’instant : le chef et les bras droits les posent sur la carte.'}</p>`}
      <p class="clan-note">Aucun bonus de combat : c’est pour s’organiser. Le premier qui remplit sa jauge prend la commune.</p></div>`;
  }
  return h;
}
function s3CentraleHtml(){
  const C = S3C.centrale, ce = C.centrale;
  let corps;
  if(ce){
    const reste = new Date(ce.pret_le).getTime() - Date.now();
    const action = !ce.pret ? `<p class="s3c-p">En construction : prête dans <b>${formatDuree(reste)}</b>.</p>`
      : C.ramasse ? `<p class="s3c-p s3c-ok">✓ Ta part est ramassée aujourd’hui (+${C.ramasse_energie} ⚡). La prochaine à minuit.</p>`
      : C.ancien_dans > 0 ? `<p class="s3c-p">Ta part arrive ${C.anciennete_h} h après ton entrée dans le clan : dans <b>${formatDuree(C.ancien_dans * 1000)}</b>.</p>`
      : `<button type="button" class="bq-btn s3c-ramasser" data-s3="ramasser">Ramasser ma part · +${C.part} ⚡</button>`;
    corps = `<p class="s3c-p">À <button type="button" class="btl-nom" data-voir-carte="${echapperTexte(ce.code)}">${echapperHtml(ce.nom)} (${echapperHtml(ce.dept)})</button>, posée par ${echapperHtml(ce.poseur || 'le chef')}. Chaque membre y ramasse <b>${C.part} ⚡ par jour</b>.</p>${action}
      <p class="clan-note">Visible de tous sur la carte. Si sa commune est prise ou bombardée, ou si ${echapperHtml(ce.poseur || 'celui qui l’a posée')} quitte le clan, elle est détruite.</p>`;
  } else {
    const pct = Math.min(100, Math.round(100 * C.caisse / Math.max(1, C.prix)));
    const manque = Math.max(0, C.prix - C.caisse), moi = Number(C.mes_lingots) || 0;
    const arme = S3C.arme && S3C.arme.startsWith('donner-') ? Number(S3C.arme.slice(7)) : 0;
    const bt = (n, txt, cl) => `<button type="button" class="s3c-don${cl ? ' ' + cl : ''}${arme === n ? ' arme' : ''}" data-s3="donner" data-n="${n}" ${moi < n || n < 1 ? 'disabled' : ''}>${arme === n ? `Confirmer : ${n}` : txt}</button>`;
    const dons = [5, 10].filter(n => n < manque).map(n => bt(n, '+' + n)).join('') + (manque > 0 ? bt(Math.min(manque, moi), moi >= manque ? `Compléter · ${manque}` : `Tout donner · ${moi}`, 'plein') : '');
    corps = `<p class="s3c-p">Chaque membre y ramassera <b>${C.part} ⚡ par jour</b>, chacun sa part. Prix : ${C.prix_actif} ${ICONE_LINGOT} par membre actif, payés par les dons du clan.</p>
      <div class="s3c-caisse"><div class="s3c-barre"><i style="width:${pct}%"></i></div><b>${C.caisse} / ${C.prix}</b>${ICONE_LINGOT}</div>
      ${manque > 0 ? `<div class="s3c-dons"><span>Donner <small>(tu as ${moi})</small></span>${dons}</div>${arme ? '<p class="s3c-p s3c-arme">Touche encore pour confirmer : les lingots donnés ne reviennent pas.</p>' : ''}`
        : `<p class="s3c-p s3c-ok">✓ La caisse est pleine. ${C.je_gere ? 'Ouvre une de tes communes sur la carte et choisis « Poser la Centrale du clan ici ».' : 'Le chef ou un bras droit peut maintenant la poser.'}</p>`}
      ${C.actifs < C.actifs_min ? `<p class="clan-note">Il faut ${C.actifs_min} membres actifs (joué dans les 7 derniers jours) pour la poser : ${C.actifs} aujourd’hui.</p>` : ''}
      ${(C.dons || []).length ? `<p class="clan-note">Derniers dons : ${(C.dons || []).slice(0, 5).map(d => `${echapperHtml(d.pseudo || '?')} <b>${d.lingots}</b>`).join(' · ')}</p>` : ''}`;
  }
  return `<div class="s3-carte s3c"><div class="s3c-tete"><span class="s3c-img">${btImg('centrale', 'turbine', 56)}</span><div><h3>Centrale du clan</h3><small>${ce ? (ce.pret ? 'En marche' : 'En construction') : 'À financer'}</small></div></div>${corps}</div>`;
}

// ---- la fiche d'une commune
function s3OrdreFiche(code, c, mienne, allie){
  const o = s3Ordre(code);
  if(!o || mienne) return '';
  const n = Number(o.membres_siege) || 0;
  return `<p class="s3o-bandeau">${ICONE_CIBLE}<span><b>Cible du clan</b> · posée par ${echapperHtml(o.pose_par || 'le chef')} · encore ${formatDuree(new Date(o.fin).getTime() - Date.now())}${n ? ` · ${n} du clan dessus` : ''}</span></p>`;
}
function s3ActionsFiche(code, c, mienne, allie){
  const out = [];
  const O = S3C.ordres;
  if(s3OrdresOk() && O.je_gere && !mienne && !allie && c.joueurId){
    const o = s3Ordre(code);
    if(o){
      const ar = S3C.arme === 'retirer-' + o.id;
      out.push(`<button class="pc-action s3o-pc" data-pc="s3-appel" data-id="${o.id}" ${o.appel_dans > 0 ? 'disabled' : ''}><span aria-hidden="true">📯</span>${o.appel_dans > 0 ? 'Nouvel appel dans ' + formatDuree(o.appel_dans * 1000) : 'Appel à l’assaut'}</button>`);
      out.push(`<button class="pc-action s3o-pc sec${ar ? ' arme' : ''}" data-pc="s3-retirer" data-id="${o.id}">${ICONE_CIBLE}${ar ? 'Confirmer : retirer la cible' : 'Retirer la cible'}</button>`);
    } else {
      const plein = (O.ordres || []).length >= O.max;
      out.push(`<button class="pc-action s3o-pc" data-pc="s3-ordre" ${plein ? 'disabled' : ''}>${ICONE_CIBLE}<span>Cible du clan<small>${plein ? `Déjà ${O.max} cibles : retires-en une` : `Ton clan la voit sur sa carte et dans Mon front · ${O.duree_h} h`}</small></span></button>`);
    }
  }
  const C = S3C.centrale;
  if(mienne && s3CentraleOk() && C.je_gere && !C.centrale && C.caisse >= C.prix && C.actifs >= C.actifs_min){
    const a = btArme === code + '|centrale';
    out.push(`<button class="pc-action bt-action s3c-pc${a ? ' arme' : ''}" data-pc="s3-centrale">${ICONE_CENTRALE}<span>${a ? `Confirmer : la Centrale à ${echapperHtml(c.nom)}` : 'Poser la Centrale du clan ici'}<small>Prête dans ${C.construction_h} h · ${C.prix} lingots de la caisse · visible de tous</small></span></button>`);
  }
  return out.length ? `<div class="pc-actions s3-pc">${out.join('')}</div>` : '';
}
function s3EtatFiche(code, c, mienne){
  let h = '';
  const A = BATIMENTS && BATIMENTS.artillerie;
  if(mienne && s3Art() && A && A.code === code){
    const pret = btPretDans(A) <= 0;
    const vis = A.devoilee ? `<b class="bt-rouge">Visible</b> jusqu’à ${new Date(A.devoile_jusqua).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })} : elle a tiré` : 'Secrète tant qu’elle ne tire pas';
    h += `<div class="bt bt-artillerie"><div class="bt-haut">${ICONE_ARTILLERIE}Artillerie <b>${pret ? `portée ${s3ArtR('portee_km', 50)} km` : (A.deplacee ? 'en route · ' : '') + 'prête dans ' + formatDuree(btPretDans(A))}</b></div>
      <p class="bt-txt">Tes sièges à moins de ${s3ArtR('portee_km', 50)} km d’ici n’ont plus le malus de distance (× ${s3Km(s3ArtR('malus', 0.8))}), contre ${s3ArtR('cout', 10)} % d’énergie en plus par vague. ${vis}. Si on te prend ${echapperHtml(c.nom)} ou qu’une bombe tombe ici, elle est détruite.</p>
      ${pret || A.deplacee ? '' : btAnnulerHtml(code, 'artillerie')}</div>`;
  }
  const ce = S3C.centrale && S3C.centrale.centrale;
  if(ce && ce.code === code){
    h += `<div class="bt bt-centrale"><div class="bt-haut">${ICONE_CENTRALE}Centrale du clan <b>${ce.pret ? `+${S3C.centrale.part} ⚡ par membre et par jour` : 'prête dans ' + formatDuree(new Date(ce.pret_le).getTime() - Date.now())}</b></div>
      <p class="bt-txt">Payée par la caisse du clan. Visible de tous : si on te prend ${echapperHtml(c.nom)} ou qu’une bombe tombe ici, elle est détruite.</p></div>`;
  }
  return h;
}
// dans « Bâtiments » de la fiche : construire ou déplacer l'Artillerie
function s3BoutonsBt(code, c){
  if(!s3Art()) return [];
  const A = BATIMENTS.artillerie, h = btReglage('construction_h', 6), nl = lingotsActuels();
  if(!A){
    const prix = s3ArtR('prix', 20), a = btArme === code + '|artillerie';
    const bloque = !mesFonderies().length ? 'Il te faut d’abord une Fonderie' : nl < prix ? `Il te faut ${prix} lingots (tu en as ${nl})` : '';
    return [`<button class="pc-action bt-action${a ? ' arme' : ''}" data-pc="bt-construire" data-bt="artillerie" ${bloque ? 'disabled' : ''}>${ICONE_ARTILLERIE}<span>${a ? `Confirmer : ${prix} lingots` : 'Construire l’Artillerie ici'}<small>${bloque || `Prête dans ${h} h · une seule · <b class="bt-plus">sièges sans malus de distance à ${s3ArtR('portee_km', 50)} km</b>`}</small></span><span class="prix">${prix} ${ICONE_LINGOT}</span></button>`];
  }
  if(A.code !== code && btPretDans(A) <= 0){
    const pd = s3ArtR('deplacer_prix', 10), a = btArme === code + '|artdep';
    const bloque = nl < pd ? `Il te faut ${pd} lingots (tu en as ${nl})` : '';
    return [`<button class="pc-action bt-action${a ? ' arme' : ''}" data-pc="s3-art-dep" ${bloque ? 'disabled' : ''}>${ICONE_ARTILLERIE}<span>${a ? `Confirmer : l’Artillerie de ${echapperHtml(A.nom)} vient ici` : 'Déplacer l’Artillerie ici'}<small>${bloque || `Prête dans ${h} h · sans effet pendant le chantier · ne s’annule pas`}</small></span><span class="prix">${pd} ${ICONE_LINGOT}</span></button>`];
  }
  return [];
}
function s3ClicPanneau(quoi, code, b){
  const rouvrir = () => { const a = panneauAncre; ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40); };
  if(quoi === 's3-ordre'){ b.disabled = true; s3Action('clan_ordre_poser', { p_code: code }, () => notifier({ type: 'succes', titre: 'Cible du clan', texte: 'Ton clan la voit sur sa carte et dans Mon front. Lance un appel à l’assaut pour prévenir tout le monde.' }), true); return true; }
  if(quoi === 's3-appel'){ b.disabled = true; s3Action('clan_ordre_appel', { p_id: Number(b.dataset.id) }, s3AppelFait, true); return true; }
  if(quoi === 's3-retirer'){
    const id = Number(b.dataset.id);
    if(S3C.arme !== 'retirer-' + id){ S3C.arme = 'retirer-' + id; rouvrir(); return true; }
    S3C.arme = null; b.disabled = true; s3Action('clan_ordre_retirer', { p_id: id }, null, true); return true;
  }
  if(quoi === 's3-centrale'){
    if(btArme !== code + '|centrale'){ btArme = code + '|centrale'; rouvrir(); return true; }
    btArme = null; b.disabled = true;
    s3Action('clan_centrale_construire', { p_code: code }, () => { notifier({ type: 'succes', titre: 'Centrale du clan en construction', texte: `Prête dans ${btReglage('construction_h', 6)} h : chaque membre pourra y ramasser sa part.` }); chargerBatiments(); }, true);
    return true;
  }
  if(quoi === 's3-art-dep'){
    if(btArme !== code + '|artdep'){ btArme = code + '|artdep'; rouvrir(); return true; }
    btArme = null; b.disabled = true;
    const A = BATIMENTS && BATIMENTS.artillerie;
    if(!A){ rouvrir(); return true; }
    sb.rpc('artillerie_deplacer', { p_depuis: A.code, p_vers: code }).then(async ({ error }) => {
      if(error) notifier({ type: 'erreur', titre: 'Artillerie', texte: messageLisible(error.message) });
      else notifier({ type: 'succes', titre: 'Artillerie en route', texte: `Prête dans ${btReglage('construction_h', 6)} h.` });
      await chargerBatiments();
      if(panneauCommune === code) rouvrir();
    });
    return true;
  }
  return false;
}
function s3AppelFait(d){
  const n = Number(d && d.prevenus) || 0;
  notifier({ type: 'succes', titre: 'Appel à l’assaut', texte: n ? `${n} membre${n > 1 ? 's' : ''} prévenu${n > 1 ? 's' : ''} sur ${n > 1 ? 'leur' : 'son'} téléphone.` : 'Aucun membre n’a les notifications : préviens-les sur le Discord.' });
}
async function s3Action(fn, args, ok, fiche){
  const { data, error } = await sb.rpc(fn, args);
  if(error){ notifier({ type: 'erreur', titre: fn.includes('ordre') ? 'Ordres du chef' : 'Centrale du clan', texte: messageLisible(error.message) }); s3Rendre(fiche); return null; }
  if(data && typeof data === 'object'){ if(fn.startsWith('clan_centrale')) S3C.centrale = data; else S3C.ordres = data; }
  S3C.lu = Date.now();
  if(ok) ok(data);
  s3Rendre(fiche);
  return data;
}
document.addEventListener('click', (ev) => {
  const b = ev.target.closest('[data-s3]');
  if(!b || b.disabled) return;
  const q = b.dataset.s3, id = Number(b.dataset.id) || 0;
  if(q === 'vers-clan'){ const t = document.querySelector('.tab[data-tab="clan"]'); if(t) t.click(); return; }
  if(q === 'ramasser'){
    b.disabled = true;
    s3Action('clan_centrale_ramasser', {}, (d) => {
      notifier({ type: 'succes', titre: 'Centrale du clan', texte: d.gagne < d.part ? `+${d.gagne} ⚡ (réserve au maximum, ${d.plafond})` : `+${d.gagne} ⚡ ramassées. Ta part revient demain.` });
      if(typeof majEnergie === 'function') majEnergie();
    });
    return;
  }
  if(q === 'donner'){
    const n = Number(b.dataset.n) || 0;
    if(S3C.arme !== 'donner-' + n){ S3C.arme = 'donner-' + n; s3MajClan(); return; }
    S3C.arme = null; b.disabled = true;
    s3Action('clan_centrale_donner', { p_lingots: n }, (d) => {
      notifier({ type: 'succes', titre: 'Centrale du clan', texte: `${d.donne} lingot${d.donne > 1 ? 's' : ''} dans la caisse : ${d.caisse} / ${d.prix}.` });
      chargerBatiments();
    });
    return;
  }
  if(q === 'appel'){ b.disabled = true; s3Action('clan_ordre_appel', { p_id: id }, s3AppelFait); return; }
  if(q === 'retirer'){
    if(S3C.arme !== 'retirer-' + id){ S3C.arme = 'retirer-' + id; s3Rendre(false); return; }
    S3C.arme = null; b.disabled = true; s3Action('clan_ordre_retirer', { p_id: id }); return;
  }
});

// ---- QG › Bâtiments : le bloc de l'Artillerie
function s3ArtillerieHtml(){
  if(!s3Art()) return '';
  const A = BATIMENTS.artillerie, prix = s3ArtR('prix', 20), po = s3ArtR('portee_km', 50);
  let corps;
  if(!A) corps = `<p class="gl-vide">${prix} lingots, une Fonderie demandée. Ouvre une de tes communes sur la carte et choisis « Construire l’Artillerie ici ». Tes sièges à moins de ${po} km n’ont plus le malus de distance (× ${s3Km(s3ArtR('malus', 0.8))} quand tu n’as aucune commune à moins de 20 km), contre ${s3ArtR('cout', 10)} % d’énergie en plus par vague. Secrète tant qu’elle ne tire pas.</p>`;
  else {
    const pret = btPretDans(A) <= 0, a = btArme === A.code + '|annuler-artillerie';
    const fin = pret ? (A.devoilee ? '<span class="btl-etat rouge">Visible</span>' : '<span class="btl-etat ok">Secrète</span>')
      : A.deplacee ? `<span class="btl-etat cours">en route · ${formatDuree(btPretDans(A))}</span>`
      : `<button type="button" class="gl-r bt-ann${a ? ' arme' : ''}" data-bt-annuler="${echapperTexte(A.code)}" data-bt-type="artillerie">${a ? 'Confirmer ?' : 'Annuler'}</button>`;
    const sous = pret ? `Portée ${po} km · ${A.devoilee ? `visible jusqu’à ${new Date(A.devoile_jusqua).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })} (elle a tiré)` : 'secrète tant qu’elle ne tire pas'}` : `Prête dans ${formatDuree(btPretDans(A))}${A.deplacee ? '' : ` · ${prix} lingots rendus si tu annules`}`;
    corps = `<div class="btl"><span class="btl-ic">${ICONE_ARTILLERIE}</span><span class="btl-t"><button type="button" class="btl-nom" data-voir-carte="${echapperTexte(A.code)}">${echapperTexte(A.nom)} (${echapperTexte(A.dept)})</button><small>${sous}</small></span>${fin}</div>
      ${pret ? `<p class="gl-vide">Pour la déplacer (${s3ArtR('deplacer_prix', 10)} lingots) : ouvre une autre de tes communes sur la carte et choisis « Déplacer l’Artillerie ici ».</p>` : ''}`;
  }
  return `<div class="btl-titre">Artillerie <em>${A ? 1 : 0} / 1</em></div>${corps}`;
}

// ---- la feuille de siège : ce que fait l'Artillerie
function s3SiegeLigne(a){
  if(!s3Art()) return '';
  const proches = Number(a.proches) || 0;
  if(a.artillerie){
    const x = a.artillerie;
    return `<div class="sg-l s3-sg"><span>${ICONE_ARTILLERIE}Artillerie</span><span>${echapperHtml(x.nom)} à ${s3Km(x.km)} km : <b class="sg-plus">malus supprimé</b>, ${x.cout} % d’énergie en plus</span></div>`;
  }
  if(proches <= 0 && !(BATIMENTS && BATIMENTS.artillerie)) return `<div class="sg-l s3-sg"><span>${ICONE_ARTILLERIE}Artillerie</span><span>une Artillerie à moins de ${s3ArtR('portee_km', 50)} km supprimerait ce malus</span></div>`;
  if(proches <= 0) return `<div class="sg-l s3-sg"><span>${ICONE_ARTILLERIE}Artillerie</span><span>la tienne est trop loin (plus de ${s3ArtR('portee_km', 50)} km)</span></div>`;
  return '';
}
function s3SiegeCalc(){
  if(!s3Art()) return '';
  return `<li><b>Artillerie</b> : à moins de ${s3ArtR('portee_km', 50)} km de la cible, elle supprime le malus « aucune commune à moins de 20 km », contre ${s3ArtR('cout', 10)} % d’énergie en plus (dégâts × ${s3Km((1 / (1 + s3ArtR('cout', 10) / 100)).toFixed(2))} au lieu de × ${s3Km(s3ArtR('malus', 0.8))}). Elle se montre sur la carte 24 h après chaque vague qui s’en sert.</li>`;
}

// ---- la carte : les cibles du clan
function s3DessinerOrdres(ctx, liste){
  if(!s3OrdresOk()) return;
  const L = (S3C.ordres.ordres || []).filter(o => !o.prise);
  if(!L.length) return;
  const codes = new Set(L.map(o => String(o.code)));
  const vue = vueCarteUnites(30);
  const u = 1 / (echelleCarte() * mapZoom);
  const px = mapZoom < 2 ? 7 : mapZoom < 12 ? 10 : 15;
  const r = px * u, t = (Date.now() / 1400) % 1;
  for(const c of liste){
    if(!codes.has(String(c.code))) continue;
    if(c.x < vue[0] || c.x > vue[2] || c.y < vue[1] || c.y > vue[3]) continue;
    ctx.save();
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.arc(c.x, c.y, r, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(7,17,31,.85)'; ctx.lineWidth = 4.4 * u; ctx.stroke();
    ctx.beginPath(); ctx.arc(c.x, c.y, r, 0, Math.PI * 2);
    ctx.shadowColor = '#FF5A52'; ctx.shadowBlur = 8;
    ctx.strokeStyle = '#FF6B63'; ctx.lineWidth = 2.2 * u; ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.strokeStyle = '#FFE08A'; ctx.lineWidth = 1.8 * u;
    for(const [dx, dy] of [[0, -1], [0, 1], [-1, 0], [1, 0]]){
      ctx.beginPath(); ctx.moveTo(c.x + dx * r * 0.55, c.y + dy * r * 0.55); ctx.lineTo(c.x + dx * r * 1.45, c.y + dy * r * 1.45); ctx.stroke();
    }
    ctx.beginPath(); ctx.arc(c.x, c.y, r * (1.2 + t * 0.9), 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(255,107,99,${(1 - t) * 0.55})`; ctx.lineWidth = 1.6 * u; ctx.stroke();
    ctx.restore();
  }
}
