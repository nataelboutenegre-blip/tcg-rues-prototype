
// patch559 : trois idées du salon #idées (27/11).
// 1. Les lingots dans le bouton Front, à côté de l'énergie (Saaslil). Le « / 120 » laisse la place ; il revient sur grand écran.
function mbLingotsMaj(){
  const el = document.getElementById('mbLingots');
  if(!el) return;
  if(!BATIMENTS){ el.hidden = true; return; }
  el.hidden = false;
  const b = el.querySelector('b'); if(b) b.textContent = String(Math.floor(lingotsActuels() || 0));
}
(function(){
  const avant = chargerBatiments;
  chargerBatiments = async function(){ const r = await avant.apply(this, arguments); try{ mbLingotsMaj(); }catch(e){} return r; };
  setInterval(() => { try{ mbLingotsMaj(); }catch(e){} }, 30000);
})();

// 2. Les sauvegardes de motifs, 6 places (Arkhannou) : dans la fenêtre « Modèles » de l'éditeur.
const MSV = { liste: null, arme: null, minuteur: null };
async function msvCharger(){
  try{ const r = await sb.rpc('motif_sauvegardes'); MSV.liste = !r.error && Array.isArray(r.data) ? r.data : (MSV.liste || []); }
  catch(e){ MSV.liste = MSV.liste || []; }
}
function msvVignette(cv, m, fond){
  motVignette(cv, (g, s) => { g.fillStyle = fond; g.fillRect(0, 0, s, s); const t = motTuile(m, Math.round(s / 2)); g.globalAlpha = (m.intensite || 60) / 100; const h = m.quinconce ? s : s / 2; for(let y = 0; y < s; y += h) for(let x = 0; x < s; x += s / 2) g.drawImage(t, x, y); g.globalAlpha = 1; });
}
function msvRendre(){
  const z = motEl('motModeles');
  if(!z) return;
  let s = z.parentElement.querySelector('.msv');
  if(!s){
    s = document.createElement('div'); s.className = 'msv';
    z.before(s);
    z.insertAdjacentHTML('beforebegin', '<h4 class="msv-t">Modèles</h4>');
    s.addEventListener('click', msvClic);
  }
  const L = MSV.liste || [], fond = motMaCouleur();
  const libre = [1, 2, 3, 4, 5, 6].find(p => !L.some(x => x.place === p));
  const vide = !!(ME.M && ME.M.calques && ME.M.calques.length);
  s.innerHTML = `<h4 class="msv-t">Mes sauvegardes · ${L.length} / 6</h4>`
    + (MSV.liste === null ? '<p class="mot-note">Un instant…</p>' : `<div class="mot-modeles">${L.map(x => `<button type="button" data-msv-charger="${x.place}"><canvas></canvas>${echapperTexte(x.nom)}<span class="msv-x${MSV.arme === x.place ? ' arme' : ''}" data-msv-retirer="${x.place}" role="button" aria-label="Supprimer ${echapperTexte(x.nom)}">${MSV.arme === x.place ? 'Sûr ?' : '✕'}</span></button>`).join('')}`
      + (libre ? `<button type="button" class="msv-plus" data-msv-nouveau${vide ? '' : ' disabled'}><span>＋</span>Sauver mon motif</button>` : '') + '</div>'
      + `<div class="msv-form" hidden><input type="text" maxlength="24" placeholder="Nom de la sauvegarde" aria-label="Nom de la sauvegarde"><button type="button" class="mot-ok" data-msv-sauver>Sauver</button></div>`
      + (libre ? '' : '<p class="mot-note">Les 6 places sont prises : supprime une sauvegarde pour en faire une nouvelle.</p>')
      + (vide ? '' : '<p class="mot-note">Ton motif est vide : ajoute un calque pour pouvoir le sauver.</p>'));
  s.querySelectorAll('[data-msv-charger]').forEach(b => {
    const x = L.find(y => y.place === Number(b.dataset.msvCharger));
    if(x) msvVignette(b.querySelector('canvas'), x.motif, fond);
  });
}
async function msvClic(e){
  const s = e.currentTarget;
  const rt = e.target.closest('[data-msv-retirer]');
  if(rt){
    e.stopPropagation();
    const p = Number(rt.dataset.msvRetirer);
    if(MSV.arme !== p){ MSV.arme = p; clearTimeout(MSV.minuteur); MSV.minuteur = setTimeout(() => { MSV.arme = null; msvRendre(); }, 3000); msvRendre(); return; }
    MSV.arme = null;
    const r = await sb.rpc('motif_sauvegarde_retirer', { p_place: p });
    if(r.error){ notifier({ type: 'erreur', titre: 'Mes sauvegardes', texte: r.error.message }); return; }
    MSV.liste = r.data || []; msvRendre(); return;
  }
  const ch = e.target.closest('[data-msv-charger]');
  if(ch){
    const x = (MSV.liste || []).find(y => y.place === Number(ch.dataset.msvCharger));
    if(!x) return;
    ME.M = motCopie(x.motif); ME.sel = 0; motEl('motVModeles').hidden = true; motGarder(); motTout(true);
    notifier({ type: 'info', titre: x.nom, texte: 'Chargé dans l’éditeur. Appuie sur « Enregistrer » pour le mettre sur ton territoire.' });
    return;
  }
  if(e.target.closest('[data-msv-nouveau]')){
    const f = s.querySelector('.msv-form'); f.hidden = false;
    const i = f.querySelector('input'); i.value = ''; i.focus(); return;
  }
  if(e.target.closest('[data-msv-sauver]')){
    const L = MSV.liste || [], libre = [1, 2, 3, 4, 5, 6].find(p => !L.some(x => x.place === p));
    if(!libre) return;
    const nom = s.querySelector('.msv-form input').value;
    const b = e.target.closest('[data-msv-sauver]'); b.disabled = true;
    const r = await sb.rpc('motif_sauver', { p_place: libre, p_nom: nom, p_motif: ME.M });
    b.disabled = false;
    if(r.error){ notifier({ type: 'erreur', titre: 'Mes sauvegardes', texte: r.error.message }); return; }
    MSV.liste = r.data || []; msvRendre();
  }
}
(function(){
  const avant = motModelesOuvrir;
  motModelesOuvrir = function(){
    const r = avant.apply(this, arguments);
    const t = document.querySelector('#motVModeles h2'); if(t) t.textContent = 'Mes motifs et modèles';
    msvRendre();
    msvCharger().then(msvRendre);
    return r;
  };
})();
document.addEventListener('keydown', (e) => {
  if(e.key !== 'Enter' || !e.target.closest || !e.target.closest('.msv-form')) return;
  e.preventDefault(); const b = document.querySelector('.msv-form [data-msv-sauver]'); if(b) b.click();
});

// 3. Le coffre du clan (Bonjean) : une carte de plus dans l'onglet Clan.
const COF = { etat: null, lu: 0, lecture: null, arme: null, minuteur: null };
async function cofCharger(force){
  if(COF.lecture) return COF.lecture;
  if(!force && COF.etat && Date.now() - COF.lu < 30000) return;
  COF.lecture = (async () => {
    try{ const r = await sb.rpc('clan_coffre_etat'); if(!r.error && r.data){ COF.etat = r.data; COF.lu = Date.now(); } }catch(e){}
    COF.lecture = null;
  })();
  return COF.lecture;
}
function cofHtml(){
  const C = COF.etat;
  if(!C || !C.ouvert || !C.clan) return '';
  const pct = Math.min(100, Math.round(100 * C.contenu / Math.max(1, C.max)));
  const resteJour = Math.max(0, C.retrait_jour - C.retire_aujourdhui);
  const placePerso = Math.max(0, C.mon_max - C.mes_lingots);
  const peutRetirer = Math.min(resteJour, C.contenu, placePerso);
  const bt = (sens, n, txt, off) => {
    const k = sens + n, a = COF.arme === k;
    return `<button type="button" class="s3c-don${sens === 'r' ? ' cof-r' : ''}${a ? ' arme' : ''}" data-cof="${sens}" data-n="${n}" ${off ? 'disabled' : ''}>${a ? 'Confirmer : ' + (sens === 'r' ? '−' : '+') + n : txt}</button>`;
  };
  const deposer = [5, 10, 15].map(n => bt('d', n, '+' + n, C.mes_lingots < n || C.contenu + n > C.max)).join('');
  let retrait;
  if(C.bloque) retrait = '<p class="s3c-p cof-bloque">🔒 Le chef a bloqué les retraits.</p>';
  else if(C.retrait_des) retrait = `<p class="s3c-p">Tu pourras retirer ${C.anciennete_h} h après ton arrivée dans le clan : dans <b>${formatDuree(new Date(C.retrait_des).getTime() - Date.now())}</b>.</p>`;
  else retrait = `<div class="s3c-dons"><span>Retirer</span>${[5, 10, 15].map(n => bt('r', n, '−' + n, n > peutRetirer)).join('')}</div>
      <p class="clan-note">${resteJour ? `Encore ${resteJour} ${ICONE_LINGOT} à retirer aujourd’hui.` : 'Tu as retiré ton maximum aujourd’hui.'}${placePerso < resteJour ? ` Ta réserve est presque pleine : ${placePerso} de place.` : ''}</p>`;
  const sens = { depot: 'a déposé', retrait: 'a retiré', blocage: 'a bloqué les retraits', deblocage: 'a rouvert les retraits' };
  const J = C.journal || [];
  const journal = J.length ? `<details class="cof-journal"><summary>Journal du coffre · ${J.length}</summary><ul>${J.map(x => `<li><b>${x.moi ? 'Toi' : echapperHtml(x.pseudo || '?')}</b> ${sens[x.sens] || x.sens}${x.lingots ? ` <b>${x.lingots}</b> ${ICONE_LINGOT}` : ''}<small>${new Date(x.le).toLocaleString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</small></li>`).join('')}</ul></details>` : '';
  return `<div class="s3-carte cof"><h3><span class="cob-ic">🏦</span>Coffre du clan <small>${C.retrait_jour} ${ICONE_LINGOT} par jour et par membre</small></h3>
    <div class="s3c-caisse"><div class="s3c-barre"><i style="width:${pct}%"></i></div><b>${C.contenu} / ${C.max}</b>${ICONE_LINGOT}</div>
    <div class="s3c-dons"><span>Déposer</span>${deposer}<small>tu as ${C.mes_lingots}</small></div>
    ${retrait}
    ${C.chef ? `<button type="button" class="cof-chef" data-cof="bloquer">${C.bloque ? 'Rouvrir les retraits' : 'Bloquer les retraits'}</button>` : ''}
    ${journal}
    <p class="clan-note">Tout le clan voit qui dépose et qui retire. Ce que tu déposes reste au clan si tu pars. Le coffre repart à zéro avec la saison.</p></div>`;
}
(function(){
  const avant = s3ClanHtml;
  s3ClanHtml = function(){
    let h = avant.apply(this, arguments);
    h += cofHtml();
    if(!COF.etat || Date.now() - COF.lu > 30000) cofCharger().then(() => { if(COF.etat && COF.etat.ouvert && COF.etat.clan) s3MajClan(); });
    return h;
  };
})();
document.addEventListener('click', async (e) => {
  const b = e.target.closest('[data-cof]');
  if(!b || b.disabled) return;
  const sens = b.dataset.cof, n = Number(b.dataset.n) || 0;
  if(sens === 'd' || sens === 'r'){
    const k = sens + n;
    if(COF.arme !== k){ COF.arme = k; clearTimeout(COF.minuteur); COF.minuteur = setTimeout(() => { COF.arme = null; s3MajClan(); }, 4000); s3MajClan(); return; }
    COF.arme = null; b.disabled = true;
    const r = await sb.rpc(sens === 'd' ? 'clan_coffre_deposer' : 'clan_coffre_retirer', { p_lingots: n });
    if(r.error){ notifier({ type: 'erreur', titre: 'Coffre du clan', texte: r.error.message }); await cofCharger(true); s3MajClan(); return; }
    COF.etat = r.data; COF.lu = Date.now(); s3MajClan();
    try{ await chargerBatiments(); }catch(err){}
    return;
  }
  if(sens === 'bloquer'){
    b.disabled = true;
    const r = await sb.rpc('clan_coffre_bloquer', { p_bloque: !(COF.etat && COF.etat.bloque) });
    if(r.error){ notifier({ type: 'erreur', titre: 'Coffre du clan', texte: r.error.message }); b.disabled = false; return; }
    COF.etat = r.data; COF.lu = Date.now(); s3MajClan();
  }
});
