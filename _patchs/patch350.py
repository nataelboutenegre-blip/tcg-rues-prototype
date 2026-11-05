# patch350 (5/11/2026) : « Invite un ami », un objectif dans les quêtes
# (idée de Nataël, aperçu validé le 5/11). Serveur : _sql/s2-101-inviter-un-ami.sql
# (parrainage_objectif, parrainage_recuperer). Sans lui, rien ne s'affiche.
# Constat : le parrainage existe depuis le 23/10 (lien dans le profil), mais
# aucun parrainage en 13 jours pour ~110 nouveaux comptes : personne ne le voit.
# - Dans la feuille des quêtes (Terra et Front), en tête des défis, une carte
#   « Invite un ami » : le lien (Copier / Partager), les paliers de la saison
#   (1, 3 et 5 amis actifs), les amis en route (jours joués sur 3).
# - Pour un nouveau joueur arrivé par un lien : une carte « X t'a invité »,
#   ses 3 jours, et sa récompense au 3e jour (quand le serveur a validé l'ami :
#   3 jours différents et au moins une carte, comme pour le parrain).
# - Le 3e jour est validé au démarrage (parrainage_jour) : la carte est relue
#   juste après.
# - Au Tirage, sous les quêtes du jour, un bandeau fin « Invite un ami » qui
#   ouvre la feuille sur la carte (sinon elle reste sous les quêtes du jour,
#   et personne ne la voit : c'est le problème d'aujourd'hui).
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')

# 1. chargé avec les quêtes
s = rep(s, """  quetesTout = data || [];
  renderObjectifs();""", """  quetesTout = data || [];
  renderObjectifs();
  invCharger();   // patch350""")

# 2. rendu à chaque rendu des quêtes
s = rep(s, """  setTimeout(() => { majBandeauObjectifs(); mfoRendre(); }, 0);   // patch284, patch288""",
"""  setTimeout(() => { majBandeauObjectifs(); mfoRendre(); }, 0);   // patch284, patch288
  invRendre();   // patch350""")

# 3. le 3e jour est validé au démarrage : relire la carte juste après
s = rep(s, """  try{ const { error } = await sb.rpc('parrainage_jour'); if(error) return; } catch(e){ return; }
  const d = await chargerParrainage();""", """  try{ const { error } = await sb.rpc('parrainage_jour'); if(error) return; } catch(e){ return; }
  if(SAISON2) invCharger(true);   // patch350
  const d = await chargerParrainage();""")

# 4. le code
s = rep(s, """function renderObjectifs(){""", r"""// ---------- patch350 : « Invite un ami », dans les quêtes ----------
// parrainage_objectif() : { pseudo, peut_inviter, actifs, energie_ami,
//   paliers: [{ n, paquets, titre, reclame }], en_route: [{ pseudo, jours }],
//   invite_par: { pseudo, jours, paquets, reclame } | null }
const INV = { d: null, lu: 0, enVol: null };
const INV_ICONE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="8" r="3.2"/><path d="M3.5 19.5c.6-3.2 2.8-5.2 5.5-5.2s4.9 2 5.5 5.2"/><path d="M18.5 7.5v6M15.5 10.5h6"/></svg>';
const INV_CADEAU = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 11h16v9H4zM3 7h18v4H3zM12 7v13"/><path d="M12 7c-1.5-3-5-3.2-5-1s3 1 5 1zM12 7c1.5-3 5-3.2 5-1s-3 1-5 1z"/></svg>';
async function invCharger(force){
  if(!SAISON2) return;
  if(!force && INV.d && Date.now() - INV.lu < 60e3){ invRendre(); return; }
  if(INV.enVol) return INV.enVol;
  INV.enVol = (async () => {
    try{ const { data, error } = await sb.rpc('parrainage_objectif'); INV.d = error ? null : data; }
    catch(e){ INV.d = null; }
    INV.lu = Date.now(); INV.enVol = null;
    invRendre();
  })();
  return INV.enVol;
}
function invPrets(){
  const d = INV.d; if(!d) return 0;
  const actifs = Number(d.actifs) || 0;
  const ip = d.invite_par;
  return (d.paliers || []).filter(p => !p.reclame && actifs >= Number(p.n)).length
    + (ip && !ip.reclame && (ip.pret !== undefined ? ip.pret : Number(ip.jours) >= 3) ? 1 : 0);
}
const invPaquets = (n) => `${n} paquet${n > 1 ? 's' : ''} Terra`;
function invAccueilHtml(ip){
  if(!ip || ip.reclame) return '';
  const j = Math.min(3, Number(ip.jours) || 0), p = echapperTexte(ip.pseudo || 'Ton ami');
  const pret = ip.pret !== undefined ? !!ip.pret : j >= 3;
  return `<div class="inv-carte inv-accueil">
      <div class="inv-tete"><span class="inv-ico">${INV_CADEAU}</span><b>${p} t’a invité</b></div>
      <p class="inv-texte">Joue <b>3 jours différents</b> : tu reçois <b>${invPaquets(Number(ip.paquets) || 1)}</b> de plus, et ${p} reçoit sa récompense.</p>
      <div class="inv-jours">${[1, 2, 3].map(i => `<i class="${i <= j ? 'on' : ''}">${i <= j ? '✓ ' : ''}Jour ${i}</i>`).join('')}</div>
      <div class="inv-pied">${pret
        ? `<span>3 jours joués, merci !</span><button type="button" class="obj-btn" data-inv="accueil">Récupérer</button>`
        : j >= 3 ? `<span>3 jours joués : tire une carte pour valider</span>`
        : `<span>${j} jour${j > 1 ? 's' : ''} sur 3 · reviens demain</span>`}</div>
    </div>`;
}
function invCarteHtml(d){
  const actifs = Number(d.actifs) || 0;
  const paliers = (d.paliers || []).map(p => {
    const n = Number(p.n), ok = actifs >= n;
    const etat = p.reclame ? '<span class="obj-fait">Récupéré</span>'
      : ok ? `<button type="button" class="obj-btn" data-inv="palier" data-n="${n}">Récupérer</button>`
      : `<span class="inv-reste">encore ${n - actifs}</span>`;
    return `<li class="${ok ? 'ok' : ''}${p.reclame ? ' fait' : ''}"><span class="inv-pn">${n} ami${n > 1 ? 's' : ''}</span>
      <span class="inv-pg">${invPaquets(Number(p.paquets) || 1)}${p.titre ? ` + titre « ${echapperTexte(p.titre)} »` : ''}</span>${etat}</li>`;
  }).join('');
  const lien = d.peut_inviter ? `
      <div class="inv-lien">
        <code>${echapperTexte(location.host + '/?ref=' + (d.pseudo || ''))}</code>
        <div class="inv-boutons">
          ${navigator.share ? '<button type="button" class="pp-btn" data-inv="partager">Partager</button>' : ''}
          <button type="button" class="pp-btn${navigator.share ? ' second' : ''}" data-inv="copier" data-lien="${echapperTexte(lienParrain(d.pseudo))}">Copier</button>
        </div>
      </div>` : `<p class="pp-note" style="margin-top:0">Tu pourras inviter des amis dès demain.</p>`;
  const route = (d.en_route || []).slice(0, 5).map(a => {
    const j = Math.min(3, Number(a.jours) || 0);
    return `<li><span class="inv-ps">${echapperTexte(a.pseudo)}</span><span class="inv-seg">${[1, 2, 3].map(i => `<i class="${i <= j ? 'on' : ''}"></i>`).join('')}</span><span class="inv-jt">${j} / 3 jours</span></li>`;
  }).join('');
  return `<div class="inv-carte">
      <div class="inv-tete"><span class="inv-ico">${INV_ICONE}</span><b>Invite un ami</b><span class="inv-n">${actifs} ami${actifs > 1 ? 's' : ''} actif${actifs > 1 ? 's' : ''}</span></div>
      <p class="inv-texte">Ton ami reçoit <b>1 paquet Terra et 10 ⚡</b> en arrivant. Toi, <b>+${Number(d.energie_ami) || 10} ⚡</b> pour chaque ami qui joue 3 jours, et les paliers de la saison :</p>
      <ol class="inv-paliers">${paliers}</ol>
      ${lien}
      ${route ? `<ul class="inv-route">${route}</ul>` : ''}
    </div>`;
}
function invBandeau(){
  let b = document.getElementById('invBandeau');
  const ob = document.getElementById('objBandeau');
  if(!b && ob){
    b = document.createElement('button'); b.type = 'button'; b.id = 'invBandeau'; b.className = 'inv-bandeau'; b.hidden = true;
    b.setAttribute('aria-haspopup', 'dialog');
    ob.insertAdjacentElement('afterend', b);
    b.addEventListener('click', () => {
      objOuvrirFeuille();
      const c = document.getElementById('objInvite'), pn = document.querySelector('#objFeuille .obj-panneau');
      if(c && pn) setTimeout(() => pn.scrollTo({ top: Math.max(0, c.offsetTop - 14), behavior: 'smooth' }), 60);
    });
  }
  if(!b) return;
  const d = INV.d;
  if(!d || (!d.peut_inviter && !d.invite_par)){ b.hidden = true; return; }
  const prets = invPrets(), ip = d.invite_par && !d.invite_par.reclame ? d.invite_par : null;
  const route = (d.en_route || [])[0];
  const suivant = (d.paliers || []).find(x => !x.reclame);
  const nP = suivant ? Number(suivant.paquets) || 1 : 0;
  let titre = 'Invite un ami', droite = suivant ? `${nP} paquet${nP > 1 ? 's' : ''} pour toi ›` : 'Partager ›',
      sous = 'Ton ami reçoit 1 paquet Terra et 10 ⚡ en arrivant';
  if(ip){ titre = echapperTexte(ip.pseudo) + ' t’a invité'; droite = `Jour ${Math.min(3, Number(ip.jours) || 0)} / 3 ›`;
          sous = 'Joue 3 jours : un paquet Terra de plus pour toi'; }
  else if(route) sous = `${echapperTexte(route.pseudo)} : ${Math.min(3, Number(route.jours) || 0)} / 3 jours`
    + ((d.en_route || []).length > 1 ? ` · +${d.en_route.length - 1} en route` : '');
  if(prets){ droite = 'Récupérer ›'; sous = prets > 1 ? `${prets} récompenses à récupérer` : 'Une récompense à récupérer'; }
  b.hidden = false;
  b.classList.toggle('pret', prets > 0);
  b.innerHTML = `<span class="inv-b-t">${ip ? INV_CADEAU : INV_ICONE}${titre}</span><span class="inv-b-n">${droite}</span><small class="inv-b-sous">${sous}</small>`;
}
function invRendre(){
  invBandeau();
  const bloc = document.getElementById('objectifs');
  if(!bloc) return;
  let el = document.getElementById('objInvite');
  if(!el){
    el = document.createElement('div'); el.id = 'objInvite'; el.className = 'obj-groupe inv';
    bloc.insertBefore(el, document.getElementById('objUnique'));
  }
  const d = INV.d;
  if(!d){ el.hidden = true; el.innerHTML = ''; return; }
  el.hidden = false;
  el.innerHTML = invAccueilHtml(d.invite_par) + invCarteHtml(d);
}
document.getElementById('objectifs')?.addEventListener('click', async (e) => {
  const b = e.target.closest('[data-inv]');
  if(!b) return;
  const quoi = b.dataset.inv;
  if(quoi === 'copier'){ copierLienParrain(b); return; }   // (secours : sélectionne le lien affiché)
  if(quoi === 'partager'){
    if(navigator.share && INV.d) navigator.share({ title: 'TerraFront', text: 'Viens jouer à TerraFront avec moi : les communes de France en cartes à collectionner.',
      url: lienParrain(INV.d.pseudo) }).catch(() => {});
    return;
  }
  b.disabled = true;
  try{
    const { data, error } = await sb.rpc('parrainage_recuperer', { p_quoi: quoi === 'accueil' ? 'accueil' : 'palier_' + b.dataset.n });
    if(error) throw error;
    notifier({ type: 'succes', titre: 'Récompense récupérée', texte: (data && data.message) || 'Ton paquet t’attend au Tirage.' });
    await invCharger(true);
    loadPackStatus();
  } catch(err){
    notifier({ type: 'erreur', titre: 'Impossible de récupérer', texte: messageLisible(err.message) });
    b.disabled = false;
  }
});

function renderObjectifs(){""")
F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
c += """
/* patch350 : « Invite un ami », dans les quêtes */
.obj-groupe.inv{ display:grid; gap:10px; margin:14px 0 4px; }
.obj-groupe.inv[hidden]{ display:none; }
.inv-carte{ background:linear-gradient(180deg, rgba(240,180,41,.09), rgba(240,180,41,.02)); border:1px solid rgba(240,180,41,.38); border-radius:14px; padding:13px 14px 14px; }
.inv-accueil{ background:linear-gradient(180deg, rgba(61,214,140,.11), rgba(61,214,140,.02)); border-color:rgba(61,214,140,.42); }
.inv-tete{ display:flex; align-items:center; gap:10px; }
.inv-tete b{ flex:1; min-width:0; font-family:var(--titre); font-weight:800; font-size:1.1rem; color:#fff; }
.inv-ico{ width:32px; height:32px; flex:none; display:grid; place-items:center; border-radius:10px; background:rgba(240,180,41,.16); color:var(--c-legendaire); }
.inv-ico svg{ width:19px; height:19px; }
.inv-accueil .inv-ico{ background:rgba(61,214,140,.16); color:#3DD68C; }
.inv-n{ font-size:.76rem; font-weight:700; color:var(--c-legendaire); white-space:nowrap; }
.inv-texte{ font-size:.8rem; line-height:1.45; color:var(--brume); margin:8px 0 11px; }
.inv-texte b{ color:#fff; font-weight:600; }
.inv-paliers{ list-style:none; margin:0 0 12px; padding:0; display:grid; gap:6px; }
.inv-paliers li{ display:flex; align-items:center; gap:10px; min-height:40px; padding:6px 10px; border-radius:10px; background:rgba(169,188,212,.06); font-size:.82rem; }
.inv-pn{ min-width:50px; font-weight:700; color:#fff; }
.inv-pg{ flex:1; min-width:0; color:var(--brume); }
.inv-paliers li.ok{ background:rgba(240,180,41,.13); }
.inv-paliers li.ok .inv-pg{ color:#fff; }
.inv-paliers li.fait{ background:rgba(169,188,212,.06); opacity:.6; }
.inv-reste{ font-size:.72rem; color:#7F91AB; white-space:nowrap; }
.inv-route{ list-style:none; margin:12px 0 0; padding:11px 0 0; border-top:1px solid rgba(169,188,212,.1); display:grid; gap:8px; }
.inv-route li{ display:flex; align-items:center; gap:10px; font-size:.82rem; }
.inv-ps{ flex:1; min-width:0; font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.inv-seg{ display:flex; gap:3px; width:54px; flex:none; }
.inv-seg i{ flex:1; height:5px; border-radius:3px; background:rgba(169,188,212,.18); }
.inv-seg i.on{ background:#3DD68C; }
.inv-jt{ font-size:.72rem; color:var(--brume); white-space:nowrap; }
.inv-jours{ display:flex; gap:7px; margin:0 0 11px; }
.inv-jours i{ flex:1; height:32px; display:grid; place-items:center; border-radius:9px; font-style:normal; font-size:.78rem; font-weight:700; color:#7F91AB; background:rgba(169,188,212,.07); border:1px dashed rgba(169,188,212,.28); }
.inv-jours i.on{ color:#0B1830; background:#3DD68C; border:1px solid #3DD68C; }
.inv-pied{ display:flex; align-items:center; justify-content:space-between; gap:10px; min-height:34px; font-size:.78rem; color:var(--brume); }
.inv-lien code{ display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; background:var(--nuit); border:1px solid rgba(169,188,212,.16); border-radius:10px; padding:11px 12px; font:500 .85rem var(--texte); color:var(--papier); }
.inv-boutons{ display:flex; gap:8px; margin-top:8px; }
.inv-boutons .pp-btn{ flex:1; }
.inv-bandeau{ display:grid; grid-template-columns:1fr auto; align-items:center; gap:3px 8px; width:100%; max-width:620px; box-sizing:border-box; margin:-4px 0 12px; padding:10px 14px 11px;
  border-radius:14px; border:1px solid rgba(240,180,41,.3); background:rgba(240,180,41,.06); color:#fff; font:inherit; text-align:left; cursor:pointer; }
.inv-bandeau[hidden]{ display:none; }
.inv-bandeau:hover{ border-color:rgba(240,180,41,.6); }
.inv-bandeau:focus-visible{ outline:2px solid #F0B429; outline-offset:2px; }
.inv-bandeau.pret{ border-color:#F0B429; background:rgba(240,180,41,.13); }
.inv-b-t{ display:flex; align-items:center; gap:7px; min-width:0; font-size:.9rem; font-weight:700; }
.inv-b-t svg{ width:16px; height:16px; flex:none; color:#F0B429; }
.inv-b-n{ font-size:.82rem; font-weight:700; color:#F0B429; white-space:nowrap; }
.inv-b-sous{ grid-column:1 / -1; font-size:.74rem; color:#C9D3E3; }
.inv-bandeau.pret .inv-b-sous{ color:#F0B429; font-weight:700; }
"""
C.write_text(c, encoding='utf-8')

import datetime, json
N = pathlib.Path('data/nouveautes.json')
if N.exists():
    t = N.read_text(encoding='utf-8')
    ligne = ("👥 Invite un ami : ton lien est maintenant dans les quêtes (et un bandeau au Tirage). Ton ami reçoit 1 paquet Terra "
             "et 10 ⚡ en arrivant, puis 1 paquet de plus après 3 jours de jeu. Toi, +10 ⚡ par ami et des paliers chaque saison : "
             "1, 3 et 5 amis actifs pour 1, 2 et 3 paquets Terra. Tu peux inviter dès ton premier jour")
    if 'Invite un ami : ton lien' not in t:
        import os
        jour = os.environ.get('JOUR_LOT') or datetime.date.today().isoformat()
        L = json.loads(t)
        ancre = f'"date": "{jour}",\n    "nouveautes": [\n'
        if L and L[0].get('date') == jour and t.count(ancre) == 1:
            t = t.replace(ancre, ancre + '      ' + json.dumps(ligne, ensure_ascii=False) + ',\n', 1)
        else:
            assert t.startswith('[\n'), 'nouveautes.json : début inattendu'
            t = '[\n  {\n    "date": "' + jour + '",\n    "nouveautes": [\n      ' + json.dumps(ligne, ensure_ascii=False) + '\n    ]\n  },\n' + t[2:]
        json.loads(t)
        N.write_text(t, encoding='utf-8')
print('patch350 appliqué')
