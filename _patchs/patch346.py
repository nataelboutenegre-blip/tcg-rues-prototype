# patch346 (4/11/2026) : la discussion, avatars, blasons et options de
# modération (aperçus validés « parfait » et « parfait ! », va avec s2-99b).
# - Avatars (l'emoji de Profil, dans un rond de la couleur du joueur ; sinon
#   l'initiale) et blasons de clan à côté du pseudo, dans le fil, la liste @
#   et la modération. Un seul endroit, dgAvatar() : les futurs ornements
#   d'avatar (champ « ornement ») s'y ajouteront.
# - Bouton « 🛡️ Modération » (modérateur) : onglets Signalés / Sanctions /
#   Journal ; lever une sanction ; mode lent (30 s) et fermer la discussion.
# - Message d'un joueur sanctionné : son état et « Lever la sanction » ;
#   « Retirer tous ses messages des dernières 24 h » ; Muet 1 h / 24 h / 7 jours.
# - « Masquer » dit que ça bloque aussi ailleurs ; après un déblocage, les
#   messages de la personne reviennent tout de suite.
import pathlib, json

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')

# --- avatar et blason dans le fil ---
s = rep(s, """  const av = groupe ? '<span class="dg-av vide"></span>' : `<span class="dg-av" style="background:${c}">${echapperTexte((m.pseudo || '?').slice(0, 1).toUpperCase())}</span>`;
  const h = groupe ? '' : `<div class="dg-h"><b style="color:${c}">${echapperTexte(m.pseudo || 'Joueur')}</b>${m.clan ? `<span class="dg-tag">${echapperTexte(m.clan)}</span>` : ''}${m.modo""",
"""  const av = dgAvatar(m, groupe);   // patch346
  const h = groupe ? '' : `<div class="dg-h"><b style="color:${c}">${echapperTexte(m.pseudo || 'Joueur')}</b>${dgClanHtml(m)}${m.modo""")
# --- la liste @ ---
s = rep(s, """data-dg-sugg="${i}"><span class="dg-av" style="background:${colorForPlayer(j.id || '')}">${echapperTexte(p.slice(0, 1).toUpperCase())}</span><span class="dg-sugg-p"><b>${echapperTexte(p.slice(0, n))}</b>${echapperTexte(p.slice(n))}</span>${j.clan ? `<span class="dg-tag">${echapperTexte(j.clan)}</span>` : ''}""",
"""data-dg-sugg="${i}">${dgAvatar(j)}<span class="dg-sugg-p"><b>${echapperTexte(p.slice(0, n))}</b>${echapperTexte(p.slice(n))}</span>${dgClanHtml(j)}""")
s = rep(s, """    vus.set(m.auteur, { id: m.auteur, pseudo: m.pseudo, clan: m.clan, recent: true });""",
"""    vus.set(m.auteur, { id: m.auteur, pseudo: m.pseudo, avatar: m.avatar, clan: m.clan, clan_couleur: m.clan_couleur, ornement: m.ornement, recent: true });""")
s = rep(s, """select('id, pseudo').ilike('pseudo', motif + '%')""", """select('id, pseudo, avatar').ilike('pseudo', motif + '%')""")
s = rep(s, """        DG_SUGG.liste.push({ id: j.id, pseudo: j.pseudo });""", """        DG_SUGG.liste.push({ id: j.id, pseudo: j.pseudo, avatar: j.avatar });""")

# --- l'en-tête : bouton Modération ---
s = rep(s, """<span class="dg-enligne" id="dgEnLigne"></span><button type="button" class="dg-regles" data-dg="regles">Règles</button></div>""",
"""<span class="dg-enligne" id="dgEnLigne"></span><span id="dgModoBtnZ"></span><button type="button" class="dg-regles" data-dg="regles">Règles</button></div>""")
s = rep(s, """    if(DG.sigTete !== html){ mo.innerHTML = html; DG.sigTete = html; }""",
"""    if(DG.sigTete !== html){ mo.innerHTML = html; DG.sigTete = html; }
    const zb = document.getElementById('dgModoBtnZ');   // patch346
    if(zb) zb.innerHTML = DG.moi && DG.moi.moderateur ? '<button type="button" class="dg-modo-btn" data-dg="modo">🛡️ Modération</button>' : '';""")
s = rep(s, """    if(q === 'signales') return dgFeuilleSignales();""",
"""    if(q === 'signales') return dgFeuilleModeration('signales');   // patch346
    if(q === 'modo') return dgFeuilleModeration(DG.modoOnglet || 'signales');""")

# --- la saisie : discussion fermée, mode lent ---
s = rep(s, """      : 'La discussion est fermée pour le moment.';""",
"""      : '🔒 La discussion est fermée pour le moment par la modération. Tu peux toujours lire.';""")
s = rep(s, """    <div class="dg-pied"><span>Pas d’insultes, pas de liens, pas de pub</span><b id="dgCompte">0 / 300</b></div>`;""",
"""    <div class="dg-pied"><span>${M.ouvert === false ? '🔒 Discussion fermée : toi seul peux écrire' : Number(M.delai_s) > 5 ? `🐢 Mode lent : un message toutes les ${Number(M.delai_s)} s` : 'Pas d’insultes, pas de liens, pas de pub'}</span><b id="dgCompte">0 / 300</b></div>`;""")
s = rep(s, """  const sg = JSON.stringify([DG.moi && DG.moi.peut_ecrire, DG.moi && DG.moi.sanction, DG.moi && DG.moi.jusqua, DG.moi && DG.moi.ouvre_le]);""",
"""  const sg = JSON.stringify([DG.moi && DG.moi.peut_ecrire, DG.moi && DG.moi.sanction, DG.moi && DG.moi.jusqua, DG.moi && DG.moi.ouvre_le, DG.moi && DG.moi.ouvert, DG.moi && DG.moi.delai_s]);   // patch346""")

# --- « Masquer » : dire que c'est un vrai blocage ---
s = rep(s, """<small>Pour toi seulement. Tu pourras le rétablir dans Amis › Bloqués.</small>""",
"""<small>Pour toi seulement. Ça le bloque aussi ailleurs dans le jeu (défis, messages d’échange). Tu pourras le débloquer dans Amis › Bloqués.</small>""")
s = rep(s, """      <li>Un message signalé par 3 joueurs est masqué en attendant la modération, qui peut le retirer, rendre son auteur muet ou l’exclure de la discussion.</li>""",
"""      <li>Un message signalé par 3 joueurs est masqué en attendant la modération, qui peut le retirer, rendre son auteur muet ou l’exclure de la discussion. En cas de besoin, elle peut passer la discussion en mode lent ou la fermer un moment.</li>""")

# --- la fiche d'un message, côté modération ---
debut = s.index("function dgFeuilleModo(m){")
fin = s.index("function dgFeuilleRegles(){")
s = s[:debut] + r"""function dgSanctionTexte(type, jusqua){
  if(type === 'exclu') return '⛔ Exclu';
  if(!jusqua) return '🔇 Muet';
  const d = new Date(jusqua), h = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  return d.toDateString() === new Date().toDateString() ? `🔇 Muet jusqu’à ${h}` : `🔇 Muet jusqu’au ${d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })} à ${h}`;
}
function dgFeuilleModo(m){   // patch346
  const autre = !m.moi;
  const p = echapperTexte(m.pseudo || 'ce joueur');
  const n24 = DG.msgs.filter(x => x.auteur === m.auteur && !x.retire && Date.now() - new Date(x.le) < 86400000).length;
  dgFeuille(`<p class="dg-titre-f">Modération</p>${dgCiteHtml(m)}
    ${autre && m.sanction ? `<div class="dg-etat-s">${dgSanctionTexte(m.sanction, m.jusqua).replace(/^(\S+) /, '$1 <b>' + p + '</b> · ')}</div>
    <button type="button" class="dg-act" data-dg-lever="${echapperTexte(m.auteur)}"><span class="ic">✅</span><span>Lever la sanction<small>${p} peut écrire de nouveau tout de suite</small></span></button>` : ''}
    <button type="button" class="dg-act rouge" data-dg-act="retirer" data-id="${m.id}"><span class="ic">🗑️</span><span>Retirer le message<small>Remplacé par « Message retiré par la modération »</small></span></button>
    ${autre && n24 > 1 ? `<button type="button" class="dg-act rouge" data-dg-act="retirer24h" data-id="${m.id}"><span class="ic">🧹</span><span>Retirer tous ses messages (24 h)<small>Pour un spam ou un flood : ${n24} messages</small></span></button>` : ''}
    ${autre ? `<div class="dg-ligne3"><button type="button" class="dg-act" data-dg-act="muet1h" data-id="${m.id}">🔇 1 h</button><button type="button" class="dg-act" data-dg-act="muet24h" data-id="${m.id}">🔇 24 h</button><button type="button" class="dg-act" data-dg-act="muet7j" data-id="${m.id}">🔇 7 jours</button></div>
    <button type="button" class="dg-act rouge" data-dg-act="exclure" data-id="${m.id}"><span class="ic">⛔</span><span>Exclure de la discussion<small>${p} ne pourra plus écrire ; il peut toujours jouer</small></span></button>` : ''}
    ${Number(m.signale) > 0 || m.masque ? `<button type="button" class="dg-act" data-dg-act="classer" data-id="${m.id}"><span class="ic">✅</span><span>Rien à redire<small>Le signalement est classé${m.masque ? ', le message réapparaît' : ''}</small></span></button>` : ''}
    ${autre ? `<button type="button" class="dg-act" data-dg-act="profil" data-id="${m.id}"><span class="ic">👤</span><span>Voir son profil</span></button>` : ''}
    <button type="button" class="dg-act neutre" data-dg="fermer">Annuler</button>`);
}
async function dgFeuilleSignales(){ return dgFeuilleModeration('signales'); }
// la fiche Modération : Signalés / Sanctions / Journal, et les réglages
async function dgFeuilleModeration(onglet){
  DG.modoOnglet = onglet;
  const lire = async (f) => {
    try{ const { data, error } = await sb.rpc(f); if(error) throw error; return data || []; }
    catch(e){ notifier({ type: 'erreur', titre: 'Modération indisponible', texte: messageLisible((e && e.message) || '') }); return null; }
  };
  const [sig, sanc, jour] = await Promise.all([lire('discussion_signales'), lire('discussion_sanctions_liste'), onglet === 'journal' ? lire('discussion_journal') : null]);
  if(!sig || !sanc) return;
  DG.signales = sig;
  if(DG.moi){ DG.moi.signalements = sig.length; DG.moi.sanctions = sanc.length; dgRendreTete(); }
  const pastille = (n) => n ? ` <i>${n}</i>` : '';
  const quand = (le) => { const d = new Date(le), a = new Date(), h = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    return d.toDateString() === a.toDateString() ? h : d.toDateString() === new Date(Date.now() - 86400000).toDateString() ? 'Hier' : d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' }); };
  let corps = '';
  if(onglet === 'signales'){
    corps = sig.length ? sig.map(m => `<button type="button" class="dg-sig-ligne" data-dg-sig="${m.id}">${dgCiteHtml(m)}</button>`).join('') : '<p class="dg-vide">Plus rien à regarder.</p>';
  } else if(onglet === 'sanctions'){
    corps = (sanc.length ? sanc.map(x => `<div class="dg-sanc">${dgAvatar({ id: x.joueur_id, pseudo: x.pseudo, avatar: x.avatar, ornement: x.ornement })}<div><b>${echapperTexte(x.pseudo || 'Joueur')}</b><small><span class="etat">${dgSanctionTexte(x.type, x.jusqua)}</span> · ${x.par_moi ? 'par toi' : 'par ' + echapperTexte(x.par || 'la modération')} ${quand(x.le) === 'Hier' ? 'hier' : (/:/.test(quand(x.le)) ? 'à ' : 'le ') + quand(x.le)}</small></div><button type="button" class="dg-lever" data-dg-lever="${echapperTexte(x.joueur_id)}">Lever</button></div>`).join('')
      : '<p class="dg-vide">Aucune sanction en cours.</p>')
      + `<p class="dg-sec">Réglages de la discussion</p>
      <button type="button" class="dg-regl" data-dg-regler="lent"><div>Mode lent<small>Un message toutes les 30 s au lieu de 5 s, pour tout le monde</small></div><span class="dg-inter${DG.moi && Number(DG.moi.delai_s) > 5 ? ' on' : ''}" role="switch" aria-checked="${!!(DG.moi && Number(DG.moi.delai_s) > 5)}"></span></button>
      <button type="button" class="dg-regl" data-dg-regler="fermer"><div>Fermer la discussion<small>Plus personne n’écrit (sauf toi) ; tout le monde peut lire</small></div><span class="dg-inter${DG.moi && DG.moi.ouvert === false ? ' on' : ''}" role="switch" aria-checked="${!!(DG.moi && DG.moi.ouvert === false)}"></span></button>`;
  } else {
    const L = { retirer: ['Retiré', ''], muet1h: ['Muet 1 h', ''], muet24h: ['Muet 24 h', ''], muet7j: ['Muet 7 j', ''], exclure: ['Exclu', ''], classer: ['Classé', 'gris'], lever: ['Levée', 'vert'], regler: ['Réglage', 'gris'] };
    const regle = (t) => ({ 'delai_s = 5': 'Mode lent coupé', 'delai_s = 30': 'Mode lent activé', 'ouvert = 0': 'Discussion fermée', 'ouvert = 1': 'Discussion rouverte' })[t] || t;
    corps = (jour || []).length ? jour.map(x => { const [lab, cl] = L[x.action] || [x.action, 'gris'];
      const qui = x.pseudo ? `<b>${echapperTexte(x.pseudo)}</b>` : '';
      const det = x.action === 'lever' ? ` n’est plus ${x.texte === 'exclu' ? 'exclu' : 'muet'}` : x.action === 'regler' ? echapperTexte(regle(x.texte || '')) : '';
      const q = x.action !== 'lever' && x.action !== 'regler' && x.texte ? `<q>${echapperTexte(x.texte)}</q>` : '';
      return `<div class="dg-jl"><time>${quand(x.le)}</time><div><span class="act ${cl}">${lab}</span>${qui}${det}${q}</div></div>`; }).join('')
      : '<p class="dg-vide">Rien pour l’instant.</p>';
  }
  dgFeuille(`<p class="dg-titre-f">Modération</p>
    <div class="dg-onglets"><button type="button" data-dg-onglet="signales"${onglet === 'signales' ? ' class="on"' : ''}>Signalés${pastille(sig.length)}</button><button type="button" data-dg-onglet="sanctions"${onglet === 'sanctions' ? ' class="on"' : ''}>Sanctions${pastille(sanc.length)}</button><button type="button" data-dg-onglet="journal"${onglet === 'journal' ? ' class="on"' : ''}>Journal</button></div>
    ${corps}
    <button type="button" class="dg-act neutre" data-dg="fermer">Fermer</button>`);
}
async function dgLever(joueur){
  const { error } = await sb.rpc('discussion_lever', { p_joueur: joueur });
  if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); return; }
  notifier({ type: 'succes', titre: 'Sanction levée', texte: 'Le joueur peut écrire de nouveau.' });
  DG.msgs.forEach(m => { if(m.auteur === joueur){ m.sanction = null; m.jusqua = null; } });
  if(document.querySelector('.dg-onglets')) dgFeuilleModeration(DG.modoOnglet || 'sanctions'); else dgFermerFeuille();
}
async function dgRegler(quoi){
  const M = DG.moi || {};
  const [cle, val] = quoi === 'lent' ? ['delai_s', Number(M.delai_s) > 5 ? 5 : 30] : ['ouvert', M.ouvert === false ? 1 : 0];
  const { data, error } = await sb.rpc('discussion_regler', { p_cle: cle, p_valeur: val });
  if(error){ notifier({ type: 'erreur', titre: 'Réglage impossible', texte: messageLisible(error.message) }); return; }
  if(data) DG.moi = data;
  notifier({ type: 'succes', titre: cle === 'delai_s' ? (val > 5 ? 'Mode lent activé' : 'Mode lent coupé') : (val ? 'Discussion rouverte' : 'Discussion fermée'), texte: '' });
  dgRendre(false);
  dgFeuilleModeration('sanctions');
}
// l'avatar d'un joueur dans la discussion : un seul endroit. Les futurs
// ornements d'avatar (champ « ornement », à envoyer par discussion_json)
// s'ajouteront ici et apparaîtront partout dans la discussion.
function dgAvatar(j, groupe){
  if(groupe) return '<span class="dg-av vide"></span>';
  const id = j.auteur || j.id || j.joueur_id || '', c = colorForPlayer(id);
  const orn = j.ornement ? ` data-ornement="${echapperTexte(String(j.ornement))}"` : '';
  return j.avatar ? `<span class="dg-av emo" style="--j:${c}"${orn}>${echapperTexte(j.avatar)}</span>`
    : `<span class="dg-av" style="background:${c}"${orn}>${echapperTexte(String(j.pseudo || '?').slice(0, 1).toUpperCase())}</span>`;
}
// le clan : son blason (s'il en a un) et son sigle
function dgClanHtml(j){
  if(!j || !j.clan) return '';
  const bl = typeof BLASONS !== 'undefined' && BLASONS ? BLASONS.get(j.clan) : null;
  const ecu = bl && bl.blason ? `<span class="blason blason-svg mini" title="${echapperTexte(j.clan)}"><svg viewBox="0 0 100 120" aria-hidden="true">${blasonSVG(bl.blason)}</svg></span>` : '';
  const coul = !ecu && /^#[0-9A-Fa-f]{6}$/.test(j.clan_couleur || '') ? ` style="background:${j.clan_couleur}33;color:${j.clan_couleur}"` : '';
  return `<span class="dg-clan">${ecu}<span class="dg-tag"${coul}>${echapperTexte(j.clan)}</span></span>`;
}
function dgRecharger(){
  DG.charge = false; DG.msgs = [];
  if(dgPanneauVisible()) dgDemarrer();
  dgChargerEtat();
}
// un joueur débloqué (Amis ou profil) : ses messages reviennent tout de suite
function dgApresAmis(){
  const b = new Set([...amisEtat].filter(([, e]) => e === 'bloque').map(([id]) => id));
  const avant = DG.bloques;
  DG.bloques = b;
  if(avant && DG.charge) for(const id of avant) if(!b.has(id)){ dgRecharger(); return; }
}
document.addEventListener('click', (e) => {
  const o = e.target.closest('[data-dg-onglet]'); if(o){ dgFeuilleModeration(o.dataset.dgOnglet); return; }
  const l = e.target.closest('[data-dg-lever]'); if(l){ dgLever(l.dataset.dgLever); return; }
  const r = e.target.closest('[data-dg-regler]'); if(r){ dgRegler(r.dataset.dgRegler); return; }
});
""" + s[fin:]

# --- les actions : retirer 24 h (avec confirmation), muet 7 jours ---
s = rep(s, """  if((act === 'retirer' || act === 'exclure') && DG.confirmer !== act + id){
    DG.confirmer = act + id;
    const s = bouton.querySelector('span:not(.ic)') || bouton;
    s.innerHTML = act === 'retirer' ? 'Confirmer : retirer le message' : 'Confirmer : exclure de la discussion';
    return;
  }""", """  if((act === 'retirer' || act === 'exclure' || act === 'retirer24h') && DG.confirmer !== act + id){
    DG.confirmer = act + id;
    const s = bouton.querySelector('span:not(.ic)') || bouton;
    s.innerHTML = act === 'retirer' ? 'Confirmer : retirer le message' : act === 'retirer24h' ? 'Confirmer : retirer tous ses messages' : 'Confirmer : exclure de la discussion';
    return;
  }""")
s = rep(s, """  const quoi = { retirer: 'Message retiré', muet1h: `${m.pseudo} est muet 1 h`, muet24h: `${m.pseudo} est muet 24 h`, exclure: `${m.pseudo} est exclu de la discussion`, classer: 'Signalement classé' }[act];
  notifier({ type: 'succes', titre: quoi || 'Fait', texte: '' });""",
"""  const quoi = { retirer: 'Message retiré', retirer24h: `Messages de ${m.pseudo} retirés`, muet1h: `${m.pseudo} est muet 1 h`, muet24h: `${m.pseudo} est muet 24 h`, muet7j: `${m.pseudo} est muet 7 jours`, exclure: `${m.pseudo} est exclu de la discussion`, classer: 'Signalement classé' }[act];
  notifier({ type: 'succes', titre: quoi || 'Fait', texte: '' });
  if(act === 'retirer24h'){ dgRecharger(); return; }   // patch346""")

# --- Amis : un déblocage fait revenir les messages ---
s = rep(s, """  amisEtat = new Map(amisListe.map(x => [x.id, x.etat]));""",
"""  amisEtat = new Map(amisListe.map(x => [x.id, x.etat]));
  if(typeof dgApresAmis === 'function') dgApresAmis();   // patch346""")
F.write_text(s, encoding='utf-8')

# =================================================================== style.css
F = pathlib.Path('style.css'); s = F.read_text(encoding='utf-8')
s += """
/* patch346 : avatars, blasons et modération de la discussion */
.dg-av{ position:relative; box-sizing:border-box; }
.dg-av.emo{ background:#0B1626; border:2px solid var(--j, #A9BCD4); font-size:1rem; line-height:1; }
.dg-sugg-l .dg-av.emo{ font-size:.85rem; }
.dg-h{ align-items:center; }
.dg-clan{ display:inline-flex; align-items:center; gap:4px; }
.dg-clan .blason.blason-svg.mini{ width:17px; height:20px; margin:-3px 0; }
#dgModoBtnZ{ margin-left:auto; }
.dg-tete #dgModoBtnZ + .dg-regles{ margin-left:6px; }
.dg-modo-btn{ padding:5px 9px; border-radius:9px; border:1px solid rgba(240,180,41,.45); background:rgba(240,180,41,.12); color:#FFD35A; font:inherit; font-size:.72rem; font-weight:800; cursor:pointer; }
.dg-onglets{ display:flex; gap:6px; margin:0 0 10px; }
.dg-onglets button{ flex:1; padding:8px 6px; border-radius:10px; border:1px solid rgba(169,188,212,.18); background:rgba(22,44,75,.6); color:#A9BCD4; font:inherit; font-size:.8rem; font-weight:700; cursor:pointer; }
.dg-onglets button.on{ background:rgba(240,180,41,.16); border-color:rgba(240,180,41,.5); color:#FFE29A; }
.dg-onglets button i{ font-style:normal; display:inline-block; min-width:16px; padding:0 4px; margin-left:4px; border-radius:999px; background:#E5484D; color:#fff; font-size:.66rem; }
.dg-sanc{ display:flex; align-items:center; gap:10px; padding:9px 10px; margin:0 0 6px; border-radius:12px; background:rgba(22,44,75,.85); border:1px solid rgba(169,188,212,.14); }
.dg-sanc .dg-av{ width:30px; height:30px; }
.dg-sanc > div{ flex:1; min-width:0; font-size:.88rem; line-height:1.3; }
.dg-sanc small{ display:block; color:#8FA4BF; font-size:.72rem; }
.dg-sanc .etat{ color:#FFC9CB; font-weight:700; }
.dg-lever{ flex:none; padding:7px 11px; border-radius:9px; border:1px solid rgba(95,211,157,.5); background:rgba(53,185,126,.14); color:#7FE0AE; font:inherit; font-size:.78rem; font-weight:800; cursor:pointer; }
.dg-sec{ margin:14px 0 6px; font-size:.66rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; color:#8FA4BF; }
.dg-regl{ display:flex; align-items:center; gap:10px; width:100%; box-sizing:border-box; padding:10px 12px; margin:0 0 6px; border-radius:12px; background:rgba(22,44,75,.6); border:1px solid rgba(169,188,212,.14); color:#E6EDF6; font:inherit; font-size:.88rem; text-align:left; cursor:pointer; }
.dg-regl > div{ flex:1; }
.dg-regl small{ display:block; color:#8FA4BF; font-size:.72rem; }
.dg-inter{ flex:none; width:42px; height:24px; border-radius:999px; background:rgba(169,188,212,.25); position:relative; transition:background .2s; }
.dg-inter::after{ content:''; position:absolute; top:3px; left:3px; width:18px; height:18px; border-radius:50%; background:#E6EDF6; transition:left .2s; }
.dg-inter.on{ background:#F0B429; }
.dg-inter.on::after{ left:21px; background:#2A1804; }
.dg-jl{ display:grid; grid-template-columns:44px 1fr; gap:8px; padding:8px 4px; border-bottom:1px solid rgba(169,188,212,.08); font-size:.82rem; color:#DCE5F0; }
.dg-jl time{ color:#6F84A3; font-size:.72rem; padding-top:2px; }
.dg-jl b{ color:#fff; }
.dg-jl q{ display:block; color:#8FA4BF; font-size:.76rem; margin-top:2px; quotes:'« ' ' »'; overflow-wrap:anywhere; }
.dg-jl .act{ display:inline-block; padding:0 6px; margin-right:5px; border-radius:4px; font-size:.64rem; font-weight:800; letter-spacing:.04em; text-transform:uppercase; background:rgba(229,72,77,.18); color:#FF9C9F; }
.dg-jl .act.vert{ background:rgba(53,185,126,.16); color:#7FE0AE; }
.dg-jl .act.gris{ background:rgba(169,188,212,.14); color:#C8D5E6; }
.dg-etat-s{ margin:0 0 10px; padding:9px 11px; border-radius:10px; background:rgba(229,72,77,.1); border:1px solid rgba(229,72,77,.35); color:#FFC9CB; font-size:.82rem; }
.dg-etat-s b{ color:#fff; }
.dg-ligne3{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; }
.dg-ligne3 .dg-act{ justify-content:center; padding:13px 6px; }
"""
F.write_text(s, encoding='utf-8')

# ======================================================= data/nouveautes.json
F = pathlib.Path('data/nouveautes.json'); d = json.loads(F.read_text(encoding='utf-8'))
assert d[0]['nouveautes'][0].startswith('💬 Discussion'), d[0]['nouveautes'][0][:30]
d[0]['nouveautes'][0] = d[0]['nouveautes'][0].replace("Un point bleu sur la cloche", "Chacun y a son avatar et le blason de son clan. Un point bleu sur la cloche")
F.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch346 appliqué')
