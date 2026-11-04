# patch344 (4/11/2026) : la discussion générale (aperçus validés « parfait » et
# « parfait ! », va avec s2-99).
# - Communauté : un salon ouvert à tous les joueurs, en haut de l'onglet. Pseudo
#   dans la couleur du joueur, clan, heure ; mes messages à droite ; badge
#   « Modération » ; @pseudo en doré, liseré doré quand on me cite.
# - Toucher un message : Signaler, Masquer ses messages (blocage d'Amis), Voir
#   son profil. Modération : bandeau des messages signalés, Retirer, Muet 1 h /
#   24 h, Exclure de la discussion, Rien à redire.
# - Écrire : 300 caractères, pas de lien, compte de plus de 24 h (le serveur
#   décide et explique). Joueur muet ou exclu : il peut lire, pas écrire.
# - Temps réel (comme le tchat de clan), plus une relecture toutes les 20 s
#   quand le salon est ouvert.
# - Non lus : point bleu sur la cloche, point sur Communauté (et sur Plus au
#   téléphone) ; citation @pseudo : compteur rouge et ligne « t'a cité » dans la
#   cloche ; « N nouveaux messages · Lire » dans la cloche. Lu = sur le compte.
# - Règles du salon, conditions d'utilisation et confidentialité mises à jour.
#   Une ligne dans la cloche.
# Sans s2-99, le salon reste caché.
import pathlib, json

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

# ================================================================== index.html
F = pathlib.Path('index.html'); s = F.read_text(encoding='utf-8')
s = rep(s, """      <h1>Communauté</h1>
      <div class="sub">Qui possède quoi, et ce qui vient de se passer sur la carte de France.</div>""",
"""      <h1>Communauté</h1>
      <div class="sub">Qui possède quoi, et ce qui vient de se passer sur la carte de France.</div>
      <div class="dg" id="discussion" hidden></div><!-- patch344 : la discussion générale -->""")
s = rep(s, """        Communauté
      </div>""", """        Communauté
        <span class="tab-badge point dg-badge" id="dgBadge" hidden></span><!-- patch344 -->
      </div>""")
F.write_text(s, encoding='utf-8')

# ================================================================ cgu.html
F = pathlib.Path('cgu.html'); s = F.read_text(encoding='utf-8')
s = rep(s, "le harcèlement, les insultes ou les menaces envers d'autres joueurs, notamment dans les messages d'échange ;",
        "le harcèlement, les insultes ou les menaces envers d'autres joueurs, notamment dans la discussion, le tchat de clan et les messages d'échange ; les liens, la publicité et les informations personnelles (les tiennes ou celles d'un autre) dans la discussion ;")
s = rep(s, "selon la gravité : avertir, retirer un contenu,",
        "selon la gravité : avertir, retirer un contenu, rendre un joueur muet ou l'exclure de la discussion,")
F.write_text(s, encoding='utf-8')

# ====================================================== confidentialite.html
F = pathlib.Path('confidentialite.html'); s = F.read_text(encoding='utf-8')
s = rep(s, """    <tr><td><b>Messages joints aux échanges</b></td><td>Les transmettre au joueur concerné</td></tr>""",
"""    <tr><td><b>Messages joints aux échanges</b></td><td>Les transmettre au joueur concerné</td></tr>
    <tr><td><b>Messages de la discussion et du tchat de clan</b>, signalements</td><td>Les montrer aux autres joueurs : <b>tous les joueurs</b> pour la discussion, les membres du clan pour le tchat. Les signalements servent à la modération</td></tr>""")
s = rep(s, """  <li>Les journaux techniques : la courte durée fixée par les hébergeurs.</li>""",
"""  <li>Les journaux techniques : la courte durée fixée par les hébergeurs.</li>
  <li>Les messages de la discussion : 30 jours, avec leurs signalements ; ceux du tchat de clan : 7 jours. Un message retiré par la modération est gardé 1 an dans le journal de modération, pour pouvoir traiter un abus.</li>""")
s = rep(s, "tes amis, tes échanges et leurs messages sont effacés.",
        "tes amis, tes échanges et leurs messages, tes messages de discussion et de tchat sont effacés.")
F.write_text(s, encoding='utf-8')

# ====================================================================== app.js
F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')

# l'onglet Communauté ouvre la discussion
s = rep(s, """    if(tab.dataset.tab === 'communaute'){ loadClassement(); loadJournal(); loadAmis(); }""",
"""    if(tab.dataset.tab === 'communaute'){ loadClassement(); loadJournal(); loadAmis(); dgDemarrer(); }   // patch344""")
# au démarrage : l'état des non lus et le temps réel
s = rep(s, """  chargerReserveAccueil(); setInterval(siVisible(chargerReserveAccueil), 300000);   // patch322""",
"""  chargerReserveAccueil(); setInterval(siVisible(chargerReserveAccueil), 300000);   // patch322
  dgDemarrerFond(); setInterval(siVisible(dgChargerEtat), 120000);   // patch344""")

# la cloche : citations dans la liste, point bleu
s = rep(s, """  const vus = ncVus();
  for(const it of items) it.neuf = !vus.has(it.cle);""",
"""  // patch344 : on me cite dans la discussion
  if(typeof DG !== 'undefined' && DG && DG.etat && Array.isArray(DG.etat.citations))
    for(const m of DG.etat.citations.slice(0, 5))
      items.push({ cle: `dg|${m.id}`, sec: 'disc', c: 'disc', i: '💬', t: `<b>${echapperTexte(m.pseudo || 'Un joueur')}</b> t’a cité dans la discussion`,
        s: `« ${echapperTexte(String(m.texte || '').slice(0, 90))} » · ${ilYA(m.le)}`, a: 'Répondre', aller: () => dgOuvrir(m.pseudo) });
  const vus = ncVus();
  for(const it of items) it.neuf = !vus.has(it.cle);""")
s = rep(s, """    b.setAttribute('aria-label', n ? `Notifications : ${n} nouvelle${n > 1 ? 's' : ''}` : 'Notifications');
  });
  if(NC.ouvert && NC.vue === 'liste') ncRendre();""",
"""    b.setAttribute('aria-label', n ? `Notifications : ${n} nouvelle${n > 1 ? 's' : ''}` : 'Notifications');
    b.classList.toggle('dg-non-lu', n === 0 && typeof dgNonLus === 'function' && dgNonLus() > 0);   // patch344
  });
  if(NC.ouvert && NC.vue === 'liste') ncRendre();""")
s = rep(s, """  const hi = NC.items.map((x, k) => [x, k]).filter(([x]) => x.sec === 'histo');""",
"""  const hi = NC.items.map((x, k) => [x, k]).filter(([x]) => x.sec === 'histo');
  const di = NC.items.map((x, k) => [x, k]).filter(([x]) => x.sec === 'disc');   // patch344
  const dgN = typeof dgNonLus === 'function' ? dgNonLus() : 0;""")
s = rep(s, """    <div class="nc-corps">${ncMajHtml()}""",
"""    <div class="nc-corps">${di.length || dgN ? `<p class="nc-titre">Discussion</p>${di.map(([x, k]) => ligne(x, k)).join('')}${dgN ? dgLigneCloche() : ''}` : ''}${ncMajHtml()}""")
s = rep(s, """async function ncClic(e){
  const b = e.target.closest('button');
  if(!b) return;""", """async function ncClic(e){
  const b = e.target.closest('button');
  if(!b) return;
  if(b.dataset.ncDg){ dgOuvrir(); return; }   // patch344""")

# menu Plus (téléphone) : un point quand la discussion a du neuf
s = rep(s, """  const bq = document.querySelector('.tab[data-tab="boutique"] .bq-nouveau');
  const bqMenu = surTelephone() && ONGLETS_MENU.includes('boutique') && bq && !bq.hidden;
  cible.hidden = !bqMenu;
  cible.textContent = '';
  cible.classList.toggle('point', !!bqMenu);
}""", """  const bq = document.querySelector('.tab[data-tab="boutique"] .bq-nouveau');
  const bqMenu = surTelephone() && ONGLETS_MENU.includes('boutique') && bq && !bq.hidden;
  const dgMenu = surTelephone() && ONGLETS_MENU.includes('communaute') && typeof dgNonLus === 'function' && dgNonLus() > 0;   // patch344
  cible.hidden = !(bqMenu || dgMenu);
  cible.textContent = '';
  cible.classList.toggle('point', !!(bqMenu || dgMenu));
}""")
s = rep(s, """    const bq = document.querySelector('.tab[data-tab="boutique"] .bq-nouveau');
    const bqMenu = surTelephone() && ONGLETS_MENU.includes('boutique') && bq && !bq.hidden;
    cible.hidden = !(cdjAJouer || bqMenu);
    cible.textContent = cdjAJouer ? '1' : '';
    cible.classList.toggle('point', !cdjAJouer && !!bqMenu);""", """    const bq = document.querySelector('.tab[data-tab="boutique"] .bq-nouveau');
    const bqMenu = surTelephone() && ONGLETS_MENU.includes('boutique') && bq && !bq.hidden;
    const dgMenu = surTelephone() && ONGLETS_MENU.includes('communaute') && typeof dgNonLus === 'function' && dgNonLus() > 0;   // patch344
    cible.hidden = !(cdjAJouer || bqMenu || dgMenu);
    cible.textContent = cdjAJouer ? '1' : '';
    cible.classList.toggle('point', !cdjAJouer && !!(bqMenu || dgMenu));""")
# la tuile Communauté du menu Plus : un point, pas une pastille vide
s = rep(s, """    const nb = badge && !badge.hidden ? `<span class="fp-badge">${badge.textContent}</span>` : '';""",
"""    const nb = badge && !badge.hidden ? (badge.classList.contains('dg-badge') ? '<span class="fp-badge dg-point"></span>' : `<span class="fp-badge">${badge.textContent}</span>`) : '';   // patch344""")

DG_JS = r"""
// ---------- patch344 : la discussion générale (s2-99) ----------
// Un salon ouvert à tous les joueurs, en haut de Communauté. Le serveur décide
// de tout (qui peut écrire, filtre, masquage à 3 signalements, modération) ;
// le jeu affiche. Temps réel comme le tchat de clan (patch258), plus une
// relecture toutes les 20 s quand le salon est ouvert. Lu = sur le compte.
var DG = { msgs: [], moi: null, etat: null, canal: null, charge: false, envoi: false, lu: 0, minuteries: {}, sigTete: '', sigSaisie: '', confirmer: null };
const DG_ENV = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12l16-8-6 16-2.5-6.5z"/></svg>';
function dgNonLus(){ return DG.etat ? Number(DG.etat.non_lus) || 0 : 0; }
function dgPanneauVisible(){ const p = document.getElementById('panel-communaute'); return !!(p && p.classList.contains('active') && !document.hidden); }
function dgPlanifier(f, ms){ clearTimeout(DG.minuteries[f.name]); DG.minuteries[f.name] = setTimeout(f, ms); }
function dgDemarrerFond(){
  dgChargerEtat();
  if(DG.canal || typeof sb.channel !== 'function') return;
  try{
    DG.canal = sb.channel('discussion')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'discussion_messages' }, dgEvenement)
      .subscribe();
  }catch(e){ console.error('Discussion :', e); }
}
async function dgChargerEtat(){
  try{
    const { data, error } = await sb.rpc('discussion_etat');
    DG.etat = !error && data ? data : null;   // s2-99 pas lancé : rien
  }catch(e){ DG.etat = null; }
  dgMajIndicateurs();
}
function dgMajIndicateurs(){
  const b = document.getElementById('dgBadge');
  if(b) b.hidden = !(dgNonLus() > 0);
  if(typeof NC !== 'undefined' && NC.demarre && typeof ncConstruire === 'function') ncConstruire();
  if(typeof majBadgePlus === 'function') majBadgePlus();
}
function dgEvenement(ev){
  if(ev.eventType === 'INSERT'){
    if(dgPanneauVisible() && DG.charge) dgPlanifier(dgSuite, 200);
    else if(!document.hidden) dgPlanifier(dgChargerEtat, 4000);
    return;
  }
  const r = ev.new || {}, id = r.id || (ev.old || {}).id;
  const m = DG.msgs.find(x => x.id === id);
  if(ev.eventType === 'DELETE'){ DG.msgs = DG.msgs.filter(x => x.id !== id); dgRendreFil(); return; }
  if(m){
    m.retire = !!r.retire; m.masque = !!r.masque;
    if(m.retire) m.texte = '';
    else if(m.masque && !m.moi && !(DG.moi && DG.moi.moderateur)) m.texte = '';
    else if(!m.masque && r.texte) m.texte = r.texte;
    dgRendreFil();
  }
  if(!dgPanneauVisible() && !document.hidden) dgPlanifier(dgChargerEtat, 4000);
}
async function dgDemarrer(){
  const z = document.getElementById('discussion');
  if(!z) return;
  if(!DG.charge){
    try{
      const { data, error } = await sb.rpc('discussion_lire', { p_apres: null });
      if(error || !data){ z.hidden = true; return; }   // s2-99 pas lancé : pas de salon
      DG.msgs = data.messages || []; DG.moi = data.moi || null; DG.charge = true;
    }catch(e){ z.hidden = true; return; }
    z.hidden = false;
    dgRendre(true);
    if(!DG.releve) DG.releve = setInterval(() => { if(dgPanneauVisible()){ dgSuite(); dgRendreTete(); } }, 20000);
    if(!DG.canal) dgDemarrerFond();
  } else {
    z.hidden = false;
    dgSuite();
  }
}
async function dgSuite(){
  if(!DG.charge) return;
  const der = DG.msgs.length ? DG.msgs[DG.msgs.length - 1].id : null;
  try{
    const { data, error } = await sb.rpc('discussion_lire', { p_apres: der });
    if(error || !data) return;
    if(data.moi) DG.moi = data.moi;
    for(const m of data.messages || []) dgRecevoir(m, true);
  }catch(e){ return; }
  dgRendre(false);
}
function dgRecevoir(m, sansRendu){
  if(!m || !m.id) return;
  const i = DG.msgs.findIndex(x => x.id === m.id);
  if(i >= 0) DG.msgs[i] = m; else { DG.msgs.push(m); DG.msgs.sort((a, b) => a.id - b.id); if(DG.msgs.length > 150) DG.msgs.shift(); }
  if(!sansRendu) dgRendre(false);
}
function dgHeure(le){ return new Date(le).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }); }
function dgJour(le){
  const d = new Date(le), a = new Date(), h = new Date(Date.now() - 86400000);
  if(d.toDateString() === a.toDateString()) return 'Aujourd’hui';
  if(d.toDateString() === h.toDateString()) return 'Hier';
  return d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
}
function dgTexteHtml(t){ return echapperTexte(t || '').replace(/(^|\s)(@[^\s@]{2,20})/g, '$1<span class="dg-at">$2</span>'); }
function dgMsgHtml(m, groupe){
  if(m.retire) return `<div class="dg-m retire" data-dg-id="${m.id}"><span class="dg-av vide"></span><div class="dg-b">Message retiré par la modération</div></div>`;
  const cache = m.masque && !m.texte;
  const txt = cache ? '<i>Message masqué en attendant la modération</i>' : dgTexteHtml(m.texte);
  const modo = DG.moi && DG.moi.moderateur;
  const sig = modo && Number(m.signale) > 0 ? `<small class="dg-sig">Signalé ${m.signale} fois${m.masque ? ' · masqué' : ''}</small>` : '';
  if(m.moi) return `<div class="dg-m moi${m.masque ? ' masque' : ''}" data-dg-id="${m.id}"><div class="dg-b">${txt}${m.masque ? '<small class="dg-avert">Masqué pour les autres en attendant la modération</small>' : ''}</div></div>`;
  const c = colorForPlayer(m.auteur || '');
  const av = groupe ? '<span class="dg-av vide"></span>' : `<span class="dg-av" style="background:${c}">${echapperTexte((m.pseudo || '?').slice(0, 1).toUpperCase())}</span>`;
  const h = groupe ? '' : `<div class="dg-h"><b style="color:${c}">${echapperTexte(m.pseudo || 'Joueur')}</b>${m.clan ? `<span class="dg-tag">${echapperTexte(m.clan)}</span>` : ''}${m.modo ? '<span class="dg-badge">Modération</span>' : ''}<span class="dg-t">${dgHeure(m.le)}</span></div>`;
  return `<div class="dg-m${m.cite ? ' mention' : ''}${cache ? ' masque' : ''}" data-dg-id="${m.id}">${av}<div class="dg-b">${h}${txt}${sig}</div></div>`;
}
function dgFilHtml(){
  if(!DG.msgs.length) return '<p class="dg-vide">Personne n’a encore écrit. Lance la discussion !</p>';
  let html = '', jour = '';
  DG.msgs.forEach((m, i) => {
    const j = dgJour(m.le);
    if(j !== jour){ html += `<div class="dg-jour">${j}</div>`; jour = j; }
    const p = DG.msgs[i - 1];
    const groupe = !!(p && !m.moi && !m.retire && !p.retire && p.auteur === m.auteur && dgJour(p.le) === j && new Date(m.le) - new Date(p.le) < 5 * 60000);
    html += dgMsgHtml(m, groupe);
  });
  return html;
}
function dgAuBas(f){ return !f || f.scrollHeight - f.scrollTop - f.clientHeight < 60; }
function dgRendreFil(forcerBas){
  const f = document.getElementById('dgFil');
  if(!f) return;
  const bas = forcerBas || dgAuBas(f), avant = f.scrollHeight;
  f.innerHTML = dgFilHtml();
  if(bas){ f.scrollTop = f.scrollHeight; dgMarquerLu(); }
  else if(f.scrollHeight > avant){ const n = document.getElementById('dgNouveaux'); if(n) n.hidden = false; }
}
function dgRendreTete(){
  const e = document.getElementById('dgEnLigne');
  if(e){ const n = typeof enLigne !== 'undefined' ? enLigne.size : 0; e.innerHTML = n > 0 ? `<i></i>${n} en ligne` : ''; }
  const mo = document.getElementById('dgModo');
  if(mo){
    const n = DG.moi && DG.moi.moderateur ? Number(DG.moi.signalements) || 0 : 0;
    const html = n ? `<button type="button" class="dg-modo" data-dg="signales">🛡️ <b>${n} message${n > 1 ? 's' : ''} signalé${n > 1 ? 's' : ''}</b> à regarder<span>Voir</span></button>` : '';
    if(DG.sigTete !== html){ mo.innerHTML = html; DG.sigTete = html; }
  }
}
function dgSaisieHtml(){
  const M = DG.moi || {};
  if(M.peut_ecrire === false){
    const hm = (x) => new Date(x).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    const t = M.sanction === 'exclu' ? '⛔ Tu as été exclu de la discussion par la modération. Tu peux toujours lire et jouer.'
      : M.sanction === 'muet' ? `🔇 Tu ne peux plus écrire dans la discussion jusqu’à <b>${hm(M.jusqua)}</b> (modération). Tu peux toujours lire.`
      : M.ouvre_le ? `⏳ La discussion s’ouvre 24 h après ton inscription : tu pourras écrire le <b>${new Date(M.ouvre_le).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })} à ${hm(M.ouvre_le)}</b>. En attendant, tu peux lire.`
      : 'La discussion est fermée pour le moment.';
    return `<div class="dg-muet">${t}</div>`;
  }
  return `<form class="dg-saisie" id="dgForm"><input id="dgTexte" class="dg-champ" maxlength="300" autocomplete="off" enterkeyhint="send" placeholder="Écris à tout le monde…" aria-label="Message à tous les joueurs"><button type="submit" class="dg-envoyer" id="dgEnvoyer" aria-label="Envoyer" disabled>${DG_ENV}</button></form>
    <div class="dg-pied"><span>Pas d’insultes, pas de liens, pas de pub</span><b id="dgCompte">0 / 300</b></div>`;
}
function dgRendre(premier){
  const z = document.getElementById('discussion');
  if(!z || !DG.charge) return;
  if(!z.querySelector('#dgFil')){
    z.innerHTML = `<div class="dg-tete"><h2>Discussion</h2><span class="dg-enligne" id="dgEnLigne"></span><button type="button" class="dg-regles" data-dg="regles">Règles</button></div>
      <p class="dg-sous">Visible par tous les joueurs. Touche un message pour le signaler ou masquer son auteur.</p>
      <div id="dgModo"></div>
      <div class="dg-cadre"><div class="dg-fil" id="dgFil" role="log" aria-live="polite"></div>
      <button type="button" class="dg-nouveaux" id="dgNouveaux" data-dg="bas" hidden>↓ Nouveaux messages</button></div>
      <div id="dgSaisie"></div>`;
    DG.sigTete = ''; DG.sigSaisie = '';
    document.getElementById('dgFil').addEventListener('scroll', () => {
      const f = document.getElementById('dgFil');
      if(dgAuBas(f)){ const n = document.getElementById('dgNouveaux'); if(n) n.hidden = true; dgPlanifier(dgMarquerLu, 400); }
    }, { passive: true });
  }
  dgRendreTete();
  const sg = JSON.stringify([DG.moi && DG.moi.peut_ecrire, DG.moi && DG.moi.sanction, DG.moi && DG.moi.jusqua, DG.moi && DG.moi.ouvre_le]);
  if(sg !== DG.sigSaisie){ document.getElementById('dgSaisie').innerHTML = dgSaisieHtml(); DG.sigSaisie = sg; }
  dgRendreFil(premier);
}
async function dgMarquerLu(){
  if(!dgPanneauVisible() || !DG.msgs.length) return;
  const f = document.getElementById('dgFil');
  if(!dgAuBas(f)) return;
  const der = DG.msgs[DG.msgs.length - 1].id;
  if(der <= DG.lu && !dgNonLus()) return;
  DG.lu = Math.max(DG.lu, der);
  if(DG.etat){ DG.etat.non_lus = 0; DG.etat.citations = []; DG.etat.dernier = null; }
  dgMajIndicateurs();
  try{ await sb.rpc('discussion_marquer_lu', { p_id: der }); }catch(e){}
}
function dgOuvrir(pseudo){
  const aller = () => {
    dgDemarrer().then(() => {
      const z = document.getElementById('discussion');
      if(z) z.scrollIntoView({ block: 'start' });
      const f = document.getElementById('dgFil'); if(f) f.scrollTop = f.scrollHeight;
      dgMarquerLu();
      const c = document.getElementById('dgTexte');
      if(c && pseudo){ c.value = '@' + pseudo + ' '; c.dispatchEvent(new Event('input', { bubbles: true })); c.focus(); }
    });
  };
  if(typeof ncAller === 'function') ncAller(null, 'communaute', aller);
  else aller();
}
function dgLigneCloche(){
  const n = dgNonLus(), d = DG.etat && DG.etat.dernier;
  const t = n >= 99 ? '99+ nouveaux messages' : `${n} nouveau${n > 1 ? 'x' : ''} message${n > 1 ? 's' : ''}`;
  return `<div class="dg-nc"><span class="nc-ico disc" aria-hidden="true">💬</span><div class="nc-txt"><b>${t}</b>${d ? `<small>Dernier : ${echapperTexte(d.pseudo || '')} · « ${echapperTexte(d.texte || '')} »</small>` : ''}</div><button type="button" class="nc-action" data-nc-dg="lire">Lire</button></div>`;
}
// --- les feuilles (toucher un message, modération, règles) ---
function dgFermerFeuille(){ document.querySelectorAll('.dg-voile, .dg-feuille').forEach(x => x.remove()); document.querySelectorAll('#dgFil .choisi').forEach(x => x.classList.remove('choisi')); DG.confirmer = null; }
function dgFeuille(html){
  dgFermerFeuille();
  document.body.insertAdjacentHTML('beforeend', `<div class="dg-voile" data-dg="fermer"></div><div class="dg-feuille" role="dialog" aria-modal="true"><div class="poignee"></div>${html}</div>`);
}
function dgCiteHtml(m){
  const c = colorForPlayer(m.auteur || '');
  return `<div class="dg-cite"><b style="color:${c}">${echapperTexte(m.pseudo || 'Joueur')} · ${dgHeure(m.le)}</b>${m.texte ? dgTexteHtml(m.texte) : '<i>Message masqué</i>'}${Number(m.signale) > 0 ? `<small>Signalé ${m.signale} fois</small>` : ''}</div>`;
}
function dgFeuilleMessage(m){
  if(!m || m.retire) return;
  const modo = DG.moi && DG.moi.moderateur;
  if(modo) return dgFeuilleModo(m);
  if(m.moi) return;
  const p = echapperTexte(m.pseudo || 'ce joueur');
  dgFeuille(`${dgCiteHtml(m)}
    <button type="button" class="dg-act" data-dg-act="signaler" data-id="${m.id}"><span class="ic">🚩</span><span>Signaler ce message<small>Nataël le verra. Ton nom n’est pas montré à ${p}.</small></span></button>
    <button type="button" class="dg-act" data-dg-act="masquer" data-id="${m.id}"><span class="ic">🙈</span><span>Masquer les messages de ${p}<small>Pour toi seulement. Tu pourras le rétablir dans Amis › Bloqués.</small></span></button>
    <button type="button" class="dg-act" data-dg-act="profil" data-id="${m.id}"><span class="ic">👤</span><span>Voir son profil</span></button>
    <button type="button" class="dg-act neutre" data-dg="fermer">Annuler</button>`);
}
function dgFeuilleModo(m){
  const autre = !m.moi;
  const p = echapperTexte(m.pseudo || 'ce joueur');
  dgFeuille(`<p class="dg-titre-f">Modération</p>${dgCiteHtml(m)}
    <button type="button" class="dg-act rouge" data-dg-act="retirer" data-id="${m.id}"><span class="ic">🗑️</span><span>Retirer le message<small>Remplacé par « Message retiré par la modération »</small></span></button>
    ${autre ? `<div class="dg-ligne2"><button type="button" class="dg-act" data-dg-act="muet1h" data-id="${m.id}">🔇 Muet 1 h</button><button type="button" class="dg-act" data-dg-act="muet24h" data-id="${m.id}">🔇 Muet 24 h</button></div>
    <button type="button" class="dg-act rouge" data-dg-act="exclure" data-id="${m.id}"><span class="ic">⛔</span><span>Exclure de la discussion<small>${p} ne pourra plus écrire ; il peut toujours jouer</small></span></button>` : ''}
    ${Number(m.signale) > 0 || m.masque ? `<button type="button" class="dg-act" data-dg-act="classer" data-id="${m.id}"><span class="ic">✅</span><span>Rien à redire<small>Le signalement est classé${m.masque ? ', le message réapparaît' : ''}</small></span></button>` : ''}
    ${autre ? `<button type="button" class="dg-act" data-dg-act="profil" data-id="${m.id}"><span class="ic">👤</span><span>Voir son profil</span></button>` : ''}
    <button type="button" class="dg-act neutre" data-dg="fermer">Annuler</button>`);
}
async function dgFeuilleSignales(){
  let liste = [];
  try{ const { data, error } = await sb.rpc('discussion_signales'); if(error) throw error; liste = data || []; }
  catch(e){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible((e && e.message) || '') }); return; }
  DG.signales = liste;
  dgFeuille(`<p class="dg-titre-f">Messages signalés</p>${liste.length ? liste.map(m => `<button type="button" class="dg-sig-ligne" data-dg-sig="${m.id}">${dgCiteHtml(m)}</button>`).join('')
    : '<p class="dg-vide">Plus rien à regarder.</p>'}<button type="button" class="dg-act neutre" data-dg="fermer">Fermer</button>`);
}
function dgFeuilleRegles(){
  dgFeuille(`<p class="dg-titre-f">Règles de la discussion</p>
    <ul class="dg-regles-l">
      <li>Respecte les autres : pas d’insultes, de harcèlement, ni de propos racistes, sexistes ou homophobes.</li>
      <li>Pas de liens ni de pub. Pas d’informations personnelles (adresse, téléphone…), ni les tiennes ni celles des autres.</li>
      <li>300 caractères par message, un message toutes les 5 secondes. Il faut un compte de plus de 24 h pour écrire.</li>
      <li>Un message signalé par 3 joueurs est masqué en attendant la modération, qui peut le retirer, rendre son auteur muet ou l’exclure de la discussion.</li>
      <li>Les messages sont gardés 30 jours.</li>
    </ul>
    <p class="dg-sous">Un problème grave ? Écris à <a href="mailto:contact@terrafront.fr">contact@terrafront.fr</a>.</p>
    <button type="button" class="dg-act neutre" data-dg="fermer">Fermer</button>`);
}
function dgTrouver(id){ id = Number(id); return DG.msgs.find(x => x.id === id) || (DG.signales || []).find(x => x.id === id); }
async function dgAction(act, id, bouton){
  const m = dgTrouver(id);
  if(!m) return dgFermerFeuille();
  if(act === 'profil'){ dgFermerFeuille(); if(typeof ouvrirProfil === 'function') ouvrirProfil(m.auteur); return; }
  if((act === 'retirer' || act === 'exclure') && DG.confirmer !== act + id){
    DG.confirmer = act + id;
    const s = bouton.querySelector('span:not(.ic)') || bouton;
    s.innerHTML = act === 'retirer' ? 'Confirmer : retirer le message' : 'Confirmer : exclure de la discussion';
    return;
  }
  if(act === 'signaler'){
    const { data, error } = await sb.rpc('discussion_signaler', { p_id: m.id });
    dgFermerFeuille();
    if(error){ notifier({ type: 'erreur', titre: 'Signalement impossible', texte: messageLisible(error.message) }); return; }
    notifier({ type: 'succes', titre: 'Message signalé', texte: data && data.masque ? 'Merci. Il est masqué en attendant la modération.' : 'Merci, Nataël le verra.' });
    if(data && data.masque) dgSuite();
    return;
  }
  if(act === 'masquer'){
    const { error } = await sb.rpc('bloquer_joueur', { p_ami: m.auteur });
    dgFermerFeuille();
    if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); return; }
    DG.msgs = DG.msgs.filter(x => x.auteur !== m.auteur);
    dgRendreFil();
    if(typeof loadAmis === 'function') loadAmis();
    notifier({ type: 'info', titre: 'Messages masqués', texte: `Tu ne vois plus les messages de ${m.pseudo || 'ce joueur'}. Ça se rétablit dans Amis › Bloqués.` });
    dgChargerEtat();
    return;
  }
  // modération
  const { data, error } = await sb.rpc('discussion_moderer', { p_id: m.id, p_action: act });
  dgFermerFeuille();
  if(error){ notifier({ type: 'erreur', titre: 'Modération impossible', texte: messageLisible(error.message) }); return; }
  if(data) dgRecevoir(data);
  const quoi = { retirer: 'Message retiré', muet1h: `${m.pseudo} est muet 1 h`, muet24h: `${m.pseudo} est muet 24 h`, exclure: `${m.pseudo} est exclu de la discussion`, classer: 'Signalement classé' }[act];
  notifier({ type: 'succes', titre: quoi || 'Fait', texte: '' });
  dgSuite();
}
document.addEventListener('click', (e) => {
  const z = e.target.closest('#discussion, .dg-feuille, .dg-voile');
  if(!z) return;
  const a = e.target.closest('[data-dg-act]');
  if(a){ dgAction(a.dataset.dgAct, a.dataset.id, a); return; }
  const sg = e.target.closest('[data-dg-sig]');
  if(sg){ const m = dgTrouver(sg.dataset.dgSig); if(m) dgFeuilleModo(m); return; }
  const d = e.target.closest('[data-dg]');
  if(d){
    const q = d.dataset.dg;
    if(q === 'fermer') return dgFermerFeuille();
    if(q === 'regles') return dgFeuilleRegles();
    if(q === 'signales') return dgFeuilleSignales();
    if(q === 'bas'){ const f = document.getElementById('dgFil'); if(f) f.scrollTop = f.scrollHeight; d.hidden = true; dgMarquerLu(); return; }
  }
  const msg = e.target.closest('#dgFil .dg-m');
  if(msg){
    const m = dgTrouver(msg.dataset.dgId);
    if(m && !m.retire && (!m.moi || (DG.moi && DG.moi.moderateur))){ msg.classList.add('choisi'); dgFeuilleMessage(m); }
  }
});
document.addEventListener('keydown', (e) => { if(e.key === 'Escape' && document.querySelector('.dg-feuille')) dgFermerFeuille(); });
document.addEventListener('input', (e) => {
  if(e.target.id !== 'dgTexte') return;
  const n = e.target.value.length, c = document.getElementById('dgCompte'), b = document.getElementById('dgEnvoyer');
  if(c) c.textContent = `${n} / 300`;
  if(b) b.disabled = !e.target.value.trim();
});
document.addEventListener('submit', async (e) => {
  if(!e.target.closest('#dgForm')) return;
  e.preventDefault();
  const champ = document.getElementById('dgTexte');
  const t = (champ && champ.value || '').trim();
  if(!t || DG.envoi) return;
  DG.envoi = true;
  const b = document.getElementById('dgEnvoyer'); if(b) b.disabled = true;
  const { data, error } = await sb.rpc('discussion_envoyer', { p_texte: t });
  DG.envoi = false;
  if(error){
    if(b) b.disabled = false;
    notifier({ type: 'erreur', titre: 'Message non envoyé', texte: messageLisible(error.message) });
    dgSuite();
    return;
  }
  champ.value = ''; champ.dispatchEvent(new Event('input', { bubbles: true }));
  dgRecevoir(data, true);
  dgRendreFil(true);
  champ.focus();
});
"""
s = rep(s, """
// ---------- patch313 : le sondage « d'autres pays ? » (s2-80) ----------""", DG_JS + """
// ---------- patch313 : le sondage « d'autres pays ? » (s2-80) ----------""")
F.write_text(s, encoding='utf-8')

# =================================================================== style.css
F = pathlib.Path('style.css'); s = F.read_text(encoding='utf-8')
s += """
/* patch344 : la discussion générale (Communauté) */
.dg{ background:var(--nuit-2); border:1px solid rgba(169,188,212,.16); border-radius:14px; padding:14px 12px 12px; margin:0 0 18px; position:relative; }
.dg[hidden]{ display:none; }
.dg-tete{ display:flex; align-items:center; gap:10px; margin:0 2px 4px; }
.dg-tete h2{ font-family:var(--titre); font-weight:900; font-size:1.6rem; margin:0; text-transform:uppercase; letter-spacing:.02em; }
.dg-enligne{ font-size:.78rem; color:#7FE0AE; display:flex; align-items:center; gap:5px; }
.dg-enligne i{ width:7px; height:7px; border-radius:50%; background:#3DD68C; box-shadow:0 0 6px #3DD68C; }
.dg-regles{ margin-left:auto; padding:4px 0 4px 8px; border:0; background:none; font:inherit; font-size:.74rem; color:var(--brume); text-decoration:underline; cursor:pointer; }
.dg-sous{ font-size:.74rem; color:#8FA4BF; margin:0 2px 10px; line-height:1.35; }
.dg-sous a{ color:#A9BCD4; }
.dg-modo{ display:flex; align-items:center; gap:8px; width:100%; box-sizing:border-box; margin:0 0 10px; padding:8px 10px; border-radius:10px; background:rgba(229,72,77,.12); border:1px solid rgba(229,72,77,.4); font:inherit; font-size:.8rem; color:#FFC9CB; text-align:left; cursor:pointer; }
.dg-modo b{ color:#fff; }
.dg-modo span{ margin-left:auto; font-weight:700; color:#FF9C9F; }
.dg-cadre{ position:relative; }
.dg-fil{ height:min(430px, 56vh); overflow-y:auto; overscroll-behavior:contain; display:flex; flex-direction:column; gap:6px; padding:6px 2px; box-sizing:border-box; border-radius:10px;
  background:rgba(6,12,24,.45); border:1px solid rgba(169,188,212,.08); }
.dg-fil > :first-child{ margin-top:auto; }
.dg-vide{ text-align:center; color:#7F92AA; font-size:.84rem; margin:auto 10px; }
.dg-jour{ align-self:center; font-size:.66rem; letter-spacing:.12em; text-transform:uppercase; color:#6F84A3; margin:2px 0 4px; }
.dg-m{ display:flex; gap:8px; align-items:flex-end; padding:0 6px; cursor:pointer; -webkit-tap-highlight-color:transparent; }
.dg-av{ flex:none; width:28px; height:28px; border-radius:50%; display:grid; place-items:center; font:900 .8rem/1 var(--titre); color:#0B1626; }
.dg-av.vide{ background:none; }
.dg-b{ max-width:78%; min-width:0; padding:6px 10px 7px; border-radius:12px 12px 12px 4px; background:rgba(22,44,75,.95); border:1px solid rgba(169,188,212,.12); font-size:.86rem; line-height:1.35; color:#E6EDF6; overflow-wrap:anywhere; }
.dg-h{ display:flex; align-items:baseline; gap:6px; margin-bottom:1px; }
.dg-h b{ font-weight:800; font-size:.8rem; }
.dg-tag{ font-size:.6rem; font-weight:800; letter-spacing:.06em; padding:1px 5px; border-radius:4px; background:rgba(169,188,212,.14); color:#C8D5E6; }
.dg-badge{ font-size:.6rem; font-weight:800; letter-spacing:.06em; padding:1px 6px; border-radius:4px; background:#F0B429; color:#2A1804; text-transform:uppercase; }
.dg-t{ margin-left:auto; padding-left:8px; font-size:.64rem; color:#6F84A3; }
.dg-m.moi{ justify-content:flex-end; }
.dg-m.moi .dg-b{ background:rgba(240,180,41,.18); border-color:rgba(240,180,41,.4); border-radius:12px 12px 4px 12px; }
.dg-m.mention .dg-b{ border-left:3px solid #F0B429; }
.dg-at{ color:#FFD35A; font-weight:700; }
.dg-m.retire, .dg-m.retire .dg-b{ cursor:default; }
.dg-m.retire .dg-b, .dg-m.masque:not(.moi) .dg-b{ background:none; border:1px dashed rgba(169,188,212,.25); color:#7F92AA; font-style:italic; font-size:.78rem; }
.dg-m.choisi .dg-b{ outline:2px solid #F0B429; outline-offset:2px; }
.dg-sig, .dg-avert{ display:block; margin-top:3px; font-size:.68rem; font-weight:700; color:#FF9C9F; font-style:normal; }
.dg-avert{ color:#C9A55A; font-weight:600; }
.dg-nouveaux{ position:absolute; left:50%; bottom:10px; transform:translateX(-50%); padding:6px 12px; border-radius:999px; border:0; background:#F0B429; color:#2A1804; font:inherit; font-size:.76rem; font-weight:800; box-shadow:0 6px 16px rgba(0,0,0,.45); cursor:pointer; }
.dg-nouveaux[hidden]{ display:none; }
.dg-saisie{ display:flex; gap:8px; align-items:center; margin:10px 0 0; }
.dg-champ{ flex:1; min-width:0; padding:11px 12px; border-radius:12px; background:rgba(9,16,30,.85); border:1px solid rgba(169,188,212,.22); color:#E6EDF6; font:inherit; font-size:1rem; }
.dg-champ::placeholder{ color:#7F92AA; }
.dg-champ:focus{ outline:none; border-color:rgba(240,180,41,.6); }
.dg-envoyer{ flex:none; width:44px; height:44px; border-radius:12px; border:0; background:#F0B429; color:#2A1804; display:grid; place-items:center; cursor:pointer; }
.dg-envoyer svg{ width:20px; height:20px; }
.dg-envoyer:disabled{ background:rgba(169,188,212,.18); color:#6F84A3; cursor:default; }
.dg-pied{ font-size:.68rem; color:#6F84A3; margin:6px 2px 0; display:flex; gap:8px; }
.dg-pied b{ margin-left:auto; color:#8FA4BF; font-weight:600; font-variant-numeric:tabular-nums; }
.dg-muet{ margin-top:10px; padding:11px 12px; border-radius:12px; background:rgba(229,72,77,.1); border:1px solid rgba(229,72,77,.35); color:#FFC9CB; font-size:.84rem; line-height:1.35; }
.dg-muet b{ color:#fff; }
.dg-voile{ position:fixed; inset:0; background:rgba(3,8,18,.62); z-index:950; }
.dg-feuille{ position:fixed; left:0; right:0; bottom:0; z-index:951; max-height:85vh; overflow:auto; box-sizing:border-box; background:#0F1D33; border-top:1px solid rgba(169,188,212,.2); border-radius:18px 18px 0 0; padding:10px 14px calc(18px + env(safe-area-inset-bottom)); }
@media (min-width: 721px){ .dg-feuille{ left:50%; right:auto; bottom:auto; top:50%; transform:translate(-50%, -50%); width:440px; border-radius:18px; border:1px solid rgba(169,188,212,.2); } .dg-feuille .poignee{ display:none; } }
.dg-feuille .poignee{ width:42px; height:4px; border-radius:2px; background:rgba(169,188,212,.34); margin:0 auto 12px; }
.dg-cite{ padding:9px 11px; border-radius:10px; background:rgba(22,44,75,.9); border:1px solid rgba(169,188,212,.14); font-size:.84rem; color:#E6EDF6; margin-bottom:10px; text-align:left; overflow-wrap:anywhere; }
.dg-cite b{ display:block; font-size:.76rem; margin-bottom:2px; }
.dg-cite small{ display:block; margin-top:5px; color:#FF9C9F; font-size:.72rem; font-weight:700; }
.dg-act{ display:flex; align-items:center; gap:10px; width:100%; box-sizing:border-box; padding:13px 12px; margin:0 0 6px; border-radius:12px; border:1px solid rgba(169,188,212,.14); background:rgba(22,44,75,.85); color:#E6EDF6; font:inherit; font-size:.92rem; font-weight:600; text-align:left; cursor:pointer; }
.dg-act small{ display:block; font-weight:400; font-size:.72rem; color:#8FA4BF; margin-top:1px; }
.dg-act.rouge{ background:rgba(229,72,77,.14); border-color:rgba(229,72,77,.4); color:#FFC9CB; }
.dg-act.neutre{ background:none; justify-content:center; color:#A9BCD4; }
.dg-act .ic{ width:22px; text-align:center; flex:none; }
.dg-titre-f{ font-size:.72rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; color:#F0B429; margin:0 0 8px; }
.dg-ligne2{ display:grid; grid-template-columns:1fr 1fr; gap:6px; }
.dg-ligne2 .dg-act{ justify-content:center; }
.dg-sig-ligne{ display:block; width:100%; padding:0; border:0; background:none; font:inherit; cursor:pointer; }
.dg-regles-l{ margin:0 0 10px; padding-left:18px; font-size:.86rem; line-height:1.45; color:#DCE5F0; }
.dg-regles-l li{ margin-bottom:6px; }
/* la cloche et le menu */
.nc-cloche.dg-non-lu::after{ content:''; position:absolute; top:-3px; right:-3px; width:11px; height:11px; border-radius:50%; background:#4C9BFF; box-shadow:0 0 0 2px #0B1A30, 0 0 8px rgba(76,155,255,.8); }
.nc-ico.disc{ background:rgba(76,155,255,.18); }
.dg-nc{ margin:4px 12px 6px; padding:10px 12px; border-radius:12px; background:rgba(76,155,255,.1); border:1px solid rgba(76,155,255,.35); display:flex; gap:11px; align-items:center; }
.dg-nc .nc-txt{ flex:1; min-width:0; font-size:.88rem; line-height:1.3; }
.dg-nc .nc-txt b{ color:#fff; }
.dg-nc .nc-txt small{ display:block; color:#A9BCD4; font-size:.74rem; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.dg-nc .nc-action{ flex:none; }
.tab-badge.dg-badge{ background:#4C9BFF; box-shadow:0 0 6px rgba(76,155,255,.8); }
.fp-badge.dg-point{ min-width:10px; width:10px; height:10px; padding:0; background:#4C9BFF; box-shadow:0 0 0 2px #1B2D4A, 0 0 8px rgba(76,155,255,.8); }
"""
F.write_text(s, encoding='utf-8')

# ======================================================= data/nouveautes.json
F = pathlib.Path('data/nouveautes.json'); d = json.loads(F.read_text(encoding='utf-8'))
assert d[0]['date'] == '2026-11-04', d[0]['date']
d[0]['nouveautes'].insert(0, "💬 Discussion : un salon ouvert à tous les joueurs, en haut de Communauté. Touche un message pour le signaler ou masquer son auteur. Un point bleu sur la cloche quand il y a du neuf, et le compteur quand on te cite avec @pseudo")
F.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch344 appliqué')
