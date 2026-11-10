# patch400 (10/11/2026) : la diplomatie entre clans (s2-134) : onglet Clan › Diplomatie (salons privés sur
# le Discord entre deux clans, proposés et fermés par les chefs), notification au chef qui reçoit une
# proposition, pastille de l'onglet Clan, règles du jeu.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
# l'état
rep(A, """async function chargerClanEch(){
  if(!SAISON2) return null;""", """// patch400 : la diplomatie (s2-134)
const clanDiplo = { etat: null, choix: '', confirmer: null };
async function chargerClanDiplo(){
  try{
    const { data, error } = await sb.rpc('clan_diplo_etat');
    clanDiplo.etat = error ? null : data;
  }catch(e){ clanDiplo.etat = null; }
  majBadgeClanTotal();
  return clanDiplo.etat;
}
function dpDans(t){
  const h = Math.max(0, Math.round((Date.parse(t) - Date.now()) / 3600000));
  return h >= 24 ? `expire dans ${Math.round(h / 24)} j` : h >= 1 ? `expire dans ${h} h` : 'expire bientôt';
}
function blocDiplomatie(){
  const e = clanDiplo.etat;
  if(!e || !e.clan) return '';
  const chef = !!e.chef, salons = e.salons || [], max = Number(e.max) || 5, n = Number(e.utilises) || 0;
  const clanDe = (x, info) => `${blasonHtml(x.tag, x.couleur, true)}<div class="dp-nom"><b>[${echapperTexte(x.tag)}] ${echapperTexte(x.nom)}</b><small>${info}</small></div>`;
  const ligne = (x) => {
    let info, actions = '';
    if(x.etat === 'ouvert'){
      info = `salon ouvert${x.ouvert_le ? ' depuis le ' + new Date(x.ouvert_le).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' }) : ''} · <span class="dp-ok">sur le Discord, dans 🤝 Diplomatie</span>`;
      if(chef) actions = clanDiplo.confirmer === x.id
        ? `<button type="button" class="bq-btn confirmer" data-dp-fermer="${Number(x.id)}">Confirmer : supprimer le salon</button><button type="button" class="bq-btn secondaire" data-dp-garder>Garder</button>`
        : `<button type="button" class="bq-btn secondaire" data-dp-confirmer="${Number(x.id)}">Fermer</button>`;
    } else if(x.sens === 'recu'){
      info = `propose un salon à ton clan · ${dpDans(x.expire_le)}`;
      actions = chef ? `<button type="button" class="bq-btn" data-dp-accepter="${Number(x.id)}">Accepter</button><button type="button" class="bq-btn secondaire" data-dp-refuser="${Number(x.id)}">Refuser</button>`
                     : '<span class="dp-attente">ton chef décide</span>';
    } else {
      info = `proposé par ton clan · en attente de leur chef · ${dpDans(x.expire_le)}`;
      if(chef) actions = `<button type="button" class="bq-btn secondaire" data-dp-fermer="${Number(x.id)}">Annuler</button>`;
    }
    return `<div class="dp-item"><div class="dp-ligne">${clanDe(x, info)}</div>${actions ? `<div class="dp-actions">${actions}</div>` : ''}</div>`;
  };
  const recus = salons.filter(x => x.etat === 'en_attente' && x.sens === 'recu');
  const ouverts = salons.filter(x => x.etat === 'ouvert');
  const envoyes = salons.filter(x => x.etat === 'en_attente' && x.sens === 'envoye');
  const libres = (e.clans || []).filter(c => !c.plein);
  const proposer = !chef ? '<p class="clan-note">Seul le chef du clan peut proposer, accepter ou fermer un salon.</p>'
    : n >= max ? `<p class="clan-note">Ton clan a déjà ${max} salons (ouverts ou proposés) : ferme-en un pour en proposer un autre.</p>`
    : !libres.length ? '<p class="clan-note">Aucun autre clan disponible pour l’instant.</p>'
    : `<div class="dp-proposer"><select id="dpChoix" aria-label="Choisis un clan"><option value="">Choisis un clan…</option>${libres.map(c => `<option value="${echapperTexte(c.id)}"${c.id === clanDiplo.choix ? ' selected' : ''}>[${echapperTexte(c.tag)}] ${echapperTexte(c.nom)} · ${Number(c.membres) || 0} membre${Number(c.membres) > 1 ? 's' : ''}</option>`).join('')}</select>
       <button type="button" class="bq-btn" data-dp-proposer${clanDiplo.choix ? '' : ' disabled'}>Proposer un salon</button></div>`;
  return `<div class="ce-bloc dp-bloc"><div class="ce-tete"><h2>Diplomatie</h2><span class="puce"><b>${n}</b> / ${max} salons</span></div>
    <p class="clan-note">Un <b>salon privé sur le Discord</b> avec un autre clan, pour parler alliances, frontières ou trêves : seuls les membres des deux clans le voient. Il apparaît dans les 10 minutes après l’accord des deux chefs.</p>
    ${recus.length ? `<h3 class="ce-h3">Propositions reçues</h3>${recus.map(ligne).join('')}` : ''}
    ${ouverts.length ? `<h3 class="ce-h3">Salons ouverts</h3>${ouverts.map(ligne).join('')}` : ''}
    ${envoyes.length ? `<h3 class="ce-h3">Propositions envoyées</h3>${envoyes.map(ligne).join('')}` : ''}
    <h3 class="ce-h3">Proposer un salon</h3>${proposer}
    <ul class="clan-regles"><li>${max} salons au plus par clan (ouverts ou proposés). Une proposition attend 3 jours.</li><li>Chacun des deux chefs peut fermer le salon : il est alors <b>supprimé du Discord, avec ses messages</b>.</li><li>Il faut être sur le Discord de TerraFront, reconnu par le bot des clans (même pseudo), pour voir le salon. Les modérateurs du Discord voient tous les salons.</li></ul></div>`;
}
async function dpAction(nom, args){
  const { data, error } = await sb.rpc(nom, args);
  if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); }
  else notifier({ type: 'succes', titre: String(data || 'C\\'est fait') });
  clanDiplo.confirmer = null; clanDiplo.choix = '';
  await chargerClanDiplo();
  renderClan();
}
async function chargerClanEch(){
  if(!SAISON2) return null;""")
# chargé avec l'onglet Clan, affiché après les échanges
rep(A, """  if(SAISON2) await chargerClanEch();   // patch194
  await chargerCandidatures();   // patch307""", """  if(SAISON2) await Promise.all([chargerClanEch(), chargerClanDiplo()]);   // patch194, patch400
  await chargerCandidatures();   // patch307""")
rep(A, """      ${blocEchangesClan()}""", """      ${blocEchangesClan()}
      ${blocDiplomatie()}""")
# les clics
rep(A, """  if(b.dataset.ceAccepter){ b.disabled = true; return ceAction('clan_ech_repondre', { p_id: Number(b.dataset.ceAccepter), p_accepter: true }); }""",
"""  if(b.dataset.ceAccepter){ b.disabled = true; return ceAction('clan_ech_repondre', { p_id: Number(b.dataset.ceAccepter), p_accepter: true }); }
  // patch400 : la diplomatie
  if(b.hasAttribute('data-dp-proposer')){ if(!clanDiplo.choix) return; b.disabled = true; return dpAction('clan_diplo_proposer', { p_clan: clanDiplo.choix }); }
  if(b.dataset.dpAccepter){ b.disabled = true; return dpAction('clan_diplo_repondre', { p_id: Number(b.dataset.dpAccepter), p_accepter: true }); }
  if(b.dataset.dpRefuser){ b.disabled = true; return dpAction('clan_diplo_repondre', { p_id: Number(b.dataset.dpRefuser), p_accepter: false }); }
  if(b.dataset.dpConfirmer){ clanDiplo.confirmer = Number(b.dataset.dpConfirmer); renderClan(); return; }
  if(b.hasAttribute('data-dp-garder')){ clanDiplo.confirmer = null; renderClan(); return; }
  if(b.dataset.dpFermer){ b.disabled = true; return dpAction('clan_diplo_fermer', { p_id: Number(b.dataset.dpFermer) }); }""")
# le choix du clan (select)
rep(A, """async function ceAction(nom, args, apres){""", """document.addEventListener('change', (ev) => {   // patch400 : le clan choisi pour la diplomatie
  const s = ev.target;
  if(!s || s.id !== 'dpChoix') return;
  clanDiplo.choix = s.value || '';
  const bt = document.querySelector('[data-dp-proposer]');
  if(bt) bt.disabled = !clanDiplo.choix;
});
async function ceAction(nom, args, apres){""")
# la pastille de l'onglet Clan : les propositions reçues par le chef
rep(A, """  const n = (Number(tchat.nonLus) || 0) + (clanEch.etat && Array.isArray(clanEch.etat.recus) ? clanEch.etat.recus.length : 0)
    + (CAND && Array.isArray(CAND.recues) ? CAND.recues.length : 0);   // patch307""",
"""  const n = (Number(tchat.nonLus) || 0) + (clanEch.etat && Array.isArray(clanEch.etat.recus) ? clanEch.etat.recus.length : 0)
    + (CAND && Array.isArray(CAND.recues) ? CAND.recues.length : 0)   // patch307
    + (typeof clanDiplo !== 'undefined' && clanDiplo.etat && clanDiplo.etat.chef && Array.isArray(clanDiplo.etat.salons)
       ? clanDiplo.etat.salons.filter(x => x.etat === 'en_attente' && x.sens === 'recu').length : 0);   // patch400""")
# la cloche : le chef reçoit une proposition
rep(A, """    SAISON2 ? rpc('mes_sieges_effaces') : null,   // patch326""", """    SAISON2 ? rpc('mes_sieges_effaces') : null,   // patch326
    SAISON2 && CLANS ? rpc('clan_diplo_etat') : null,   // patch400""")
rep(A, """  const [prefs, journal, sieges, ech, clanE, alertes, quetes, recolte, clan, effaces] = await Promise.all([""",
"""  const [prefs, journal, sieges, ech, clanE, alertes, quetes, recolte, clan, effaces, diplo] = await Promise.all([""")
rep(A, """  NC.d = { journal, sieges, ech, clanE, alertes, quetes, recolte: Array.isArray(recolte) ? recolte[0] : recolte, clan, effaces };""",
"""  NC.d = { journal, sieges, ech, clanE, alertes, quetes, recolte: Array.isArray(recolte) ? recolte[0] : recolte, clan, effaces, diplo };
  if(diplo !== undefined && diplo !== null){ clanDiplo.etat = diplo; majBadgeClanTotal(); }   // patch400""")
rep(A, """  if(p.jeu.clan && d.clan && Array.isArray(d.clan.invitations)){""",
"""  if(p.jeu.clan && d.diplo && d.diplo.chef && Array.isArray(d.diplo.salons)){   // patch400
    for(const x of d.diplo.salons.filter(s => s.etat === 'en_attente' && s.sens === 'recu')){
      items.push({ cle: `diplo|${x.id}`, sec: 'afaire', c: 'clan', i: '🤝', mode: 'front',
        t: `Le clan <b>[${echapperTexte(x.tag)}] ${echapperTexte(x.nom)}</b> propose un salon de diplomatie`,
        s: 'Un salon privé sur le Discord, entre vos deux clans', a: 'Voir', aller: () => ncAller('front', 'clan') });
    }
  }
  if(p.jeu.clan && d.clan && Array.isArray(d.clan.invitations)){""")
rep('style.css', "/* patch396 : le fil de la roue */",
"""/* patch400 : la diplomatie */
.dp-bloc .ce-h3{ margin-top:12px; }
.dp-item{ border-top:1px solid rgba(169,188,212,.1); padding:8px 0 4px; }
.dp-ligne{ display:flex; align-items:center; gap:10px; }
.dp-ligne > svg, .dp-ligne > .blason{ flex:none; }
.dp-nom{ min-width:0; display:flex; flex-direction:column; gap:2px; }
.dp-nom b{ color:#fff; font-size:.86rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.dp-nom small{ color:#A9BCD4; font-size:.72rem; }
.dp-ok{ color:#2BD48B; }
.dp-actions{ display:flex; flex-wrap:wrap; gap:6px; margin:8px 0 4px; }
.dp-actions .bq-btn{ padding:6px 12px; font-size:.78rem; }
.dp-attente{ font-size:.72rem; color:#7F92AA; }
.dp-proposer{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
.dp-proposer select{ flex:1 1 200px; min-width:0; padding:8px 10px; border-radius:10px; border:1px solid rgba(169,188,212,.3); background:#0E1A2E; color:#fff; font:inherit; font-size:.82rem; }
/* patch396 : le fil de la roue */""")
print('patch400 ok')
