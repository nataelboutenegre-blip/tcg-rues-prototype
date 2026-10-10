# -*- coding: utf-8 -*-
u"""
patch110 — les clans (CACHÉS tant que CLANS = false). SQL : s2-16-clans.sql.

- Onglet Clan (commun aux deux modes) : créer un clan (nom, sigle, couleur),
  inviter par pseudo (chef), accepter / refuser une invitation, quitter,
  exclure (chef), classement des clans à la moyenne par membre.
- Combat : les communes des membres de son clan disparaissent des cibles
  (le serveur refuse de toute façon l'attaque).
- Carte : nouveau filtre « Clans » qui peint chaque clan dans sa couleur
  (éteint par défaut : chacun garde sa couleur).
- Boutique : correction d'une erreur quand le serveur répond sans données.
Pour ouvrir le jour venu : CLANS = true ici ET config_jeu 'clans_ouverts'.
"""
import io, os

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)

# ---------- index.html ----------------------------------------------------------
html = lire('index.html')
assert 'panel-clan' not in html, u'patch110 deja applique'
html = rempl(html, u"""        Communauté
      </div>
""", u"""        Communauté
      </div>

      <div class="tab" data-tab="clan">
        <div class="icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 3 19.5 5.5v6c0 4.6-3.2 8.2-7.5 9.5-4.3-1.3-7.5-4.9-7.5-9.5v-6z"/>
            <path d="M8.5 10.5h7M12 7.5v8"/>
          </svg>
        </div>
        Clan
      </div>
""", 'onglet')
html = rempl(html, u"""    <section class="tab-panel" id="panel-communaute">""", u"""    <section class="tab-panel" id="panel-clan">
      <h1>Clan</h1>
      <div class="sub">3 à 5 joueurs. En Front, les membres d'un clan ne peuvent pas s'attaquer entre eux, et le filtre « Clans » de la carte montre chaque clan dans sa couleur. Chacun garde ses propres communes.</div>
      <div id="clanZone" class="clan-zone"><p class="collection-empty">Chargement…</p></div>
    </section>

    <section class="tab-panel" id="panel-communaute">""", 'panneau')
ecrire('index.html', html)

# ---------- app.js ----------------------------------------------------------------
js = lire('app.js')
assert 'patch110' not in js

js = rempl(js, u"""const CURRENT_SEASON = 'saison-1';
""", u"""const CURRENT_SEASON = 'saison-1';
// patch110 : les clans. Passer a true le jour de leur ouverture (avec
// config_jeu 'clans_ouverts' cote serveur).
const CLANS = false;
document.documentElement.classList.toggle('clans-ouverts', CLANS);
""", 'drapeau')

js = rempl(js, u"""const ONGLETS_COMMUNS = ['profil', 'communaute'];""",
           u"""const ONGLETS_COMMUNS = CLANS ? ['profil', 'communaute', 'clan'] : ['profil', 'communaute'];""", 'communs')
js = rempl(js, u"""  .filter((id) => SAISON2 || id !== 'boutique');   // patch107""",
           u"""  .filter((id) => SAISON2 || id !== 'boutique')    // patch107
  .filter((id) => CLANS || id !== 'clan');         // patch110""", 'menu')
js = rempl(js, u"""    if(tab.dataset.tab === 'boutique') loadBoutique();
""", u"""    if(tab.dataset.tab === 'boutique') loadBoutique();
    if(tab.dataset.tab === 'clan') loadClan();
""", 'onglet charge')

# combat : pas de cible chez un coequipier
js = rempl(js, u"""  let cibles = combatCibles;
""", u"""  let cibles = combatCibles;
  if(clanMembres.size) cibles = cibles.filter(c => !clanMembres.has(c.joueur_id));   // patch110
""", 'combat')

# carte : filtre Clans
js = rempl(js, u"""  const signature = [collectionMap.size, othersMap.size, showOthers ? 1 : 0, bandeDeZoom()].join('|');""",
           u"""  const signature = [collectionMap.size, othersMap.size, showOthers ? 1 : 0, bandeDeZoom(),
                     CLANS && CALQUES.clans ? 'c' + clansCarteVersion : ''].join('|');""", 'signature')
js = rempl(js, u"""  CV.donnees = territoiresVisibles();
""", u"""  CV.donnees = territoiresVisibles();
  if(CLANS && CALQUES.clans) peindreClans(CV.donnees.joueurs);   // patch110
""", 'peindre')
js = rempl(js, u"""                   raretes: true, passage: false };""",
           u"""                   raretes: true, passage: false, clans: false };""", 'calque defaut')
js = rempl(js, u"""  const NOMS = { regions: 'Régions', depts: 'Départements', communes: 'Communes',
                 noms: 'Noms', raretes: 'Raretés', passage: 'Mon passage' };""",
u"""  const NOMS = { regions: 'Régions', depts: 'Départements', communes: 'Communes',
                 noms: 'Noms', raretes: 'Raretés', passage: 'Mon passage' };
  // patch110 : le filtre des clans
  if(CLANS){
    NOMS.clans = 'Clans';
    ICONES.clans = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M12 3 19.5 5.5v6c0 4.6-3.2 8.2-7.5 9.5-4.3-1.3-7.5-4.9-7.5-9.5v-6z"/></svg>';
  }""", 'calque noms')

# legende : se redessine quand les couleurs changent (filtre Clans)
js = rempl(js, u"""  const sig = [...joueurs.values()].map(j => j.id + ':' + j.nb).join(',')""",
           u"""  const sig = [...joueurs.values()].map(j => j.id + ':' + j.nb + ':' + j.couleur).join(',')""", 'legende')

# boutique : reponse vide
js = rempl(js, u"""  const { data, error } = await sb.rpc('boutique');
  if(error){""", u"""  const { data, error } = await sb.rpc('boutique');
  if(error || !data){""", 'boutique vide')
js = rempl(js, u"""    if(!silencieux){
      const st = document.getElementById('bqStatut');
      if(st) st.innerHTML = `<span class="puce">${echapperTexte(messageLisible(error.message))}</span>`;""",
u"""    if(!silencieux && error){
      const st = document.getElementById('bqStatut');
      if(st) st.innerHTML = `<span class="puce">${echapperTexte(messageLisible(error.message))}</span>`;""", 'boutique vide 2')

# messages
js = rempl(js, u"""    [/La boutique ouvre avec la saison 2/i, 'La boutique ouvre avec la saison 2.'],""",
u"""    [/La boutique ouvre avec la saison 2/i, 'La boutique ouvre avec la saison 2.'],
    [/Les clans ouvrent bientot/i, 'Les clans ouvrent bientôt.'],
    [/Tu es deja dans un clan/i, 'Tu es déjà dans un clan.'],
    [/Attente de 48 h apres un depart/i, 'Après avoir quitté un clan, il faut attendre 48 h.'],
    [/Nom du clan : 3 a 24/i, 'Le nom du clan fait de 3 à 24 caractères.'],
    [/Sigle : 2 a 4/i, 'Le sigle fait 2 à 4 lettres ou chiffres.'],
    [/Ce nom de clan est deja pris/i, 'Ce nom de clan est déjà pris.'],
    [/Ce sigle est deja pris/i, 'Ce sigle est déjà pris.'],
    [/Seul le chef peut inviter/i, 'Seul le chef du clan peut inviter.'],
    [/Joueur introuvable/i, 'Aucun joueur avec ce pseudo.'],
    [/Ce joueur est deja dans un clan/i, 'Ce joueur est déjà dans un clan.'],
    [/Le clan est complet/i, 'Le clan est complet (5 membres).'],
    [/Invitation introuvable ou expiree/i, 'Cette invitation a expiré.'],
    [/Tu ne peux pas attaquer un membre de ton clan/i, 'Tu ne peux pas attaquer un membre de ton clan.'],""", 'messages')

js += u"""

// ---------- patch110 : les clans ----------
const CLAN_COULEURS = ['#E07A2E', '#4C9BE8', '#C45BD6', '#2BB673', '#E5484D', '#E8C547', '#1ABC9C', '#8E9AAF'];
let clanMembres = new Set();          // ids des autres membres de mon clan (cibles exclues)
let clansCarte = new Map();           // joueur_id -> { tag, couleur }
let clansCarteVersion = 0;
let monUidClan = null;
let clanCache = null;
let clanCouleurChoisie = CLAN_COULEURS[0];

async function loadClansCarte(){
  if(!CLANS) return;
  try{
    if(!monUidClan){ const { data: u } = await sb.auth.getUser(); monUidClan = u && u.user ? u.user.id : null; }
    const { data, error } = await sb.rpc('clans_carte');
    if(error) return;
    clansCarte = new Map((data || []).map(r => [r.joueur_id, { tag: r.tag, couleur: r.couleur }]));
    clansCarteVersion++;
    const moi = monUidClan ? clansCarte.get(monUidClan) : null;
    clanMembres = new Set(moi ? (data || []).filter(r => r.tag === moi.tag && r.joueur_id !== monUidClan).map(r => r.joueur_id) : []);
    if(typeof demanderDessin === 'function'){ CV.donneesSignature = ''; demanderDessin(); }
  }catch(e){ /* les clans restent invisibles */ }
}
function peindreClans(joueurs){
  for(const j of joueurs.values()){
    const k = clansCarte.get(j.id === ID_MOI ? monUidClan : j.id);
    if(!k) continue;
    j.couleur = k.couleur;
    j.fonce = couleurFoncee(k.couleur);
    j.clan = k.tag;
  }
}

async function loadClan(){
  const zone = document.getElementById('clanZone');
  if(!CLANS || !zone) return;
  const [mc, cl] = await Promise.all([sb.rpc('mon_clan'), sb.rpc('clans_classement')]);
  if(mc.error){ zone.innerHTML = `<p class="collection-empty">${echapperTexte(messageLisible(mc.error.message))}</p>`; return; }
  clanCache = { moi: mc.data || {}, classement: cl.error ? [] : (cl.data || []) };
  renderClan();
}
function blasonHtml(tag, couleur, petit){
  return `<span class="blason${petit ? ' petit' : ''}" style="--clan:${couleur}">${echapperTexte(tag)}</span>`;
}
function nbClan(n){ return Number(n || 0).toLocaleString('fr-FR'); }
function renderClan(){
  const zone = document.getElementById('clanZone');
  if(!zone || !clanCache) return;
  const { moi, classement } = clanCache;
  const c = moi.clan;
  const rang = c ? classement.findIndex(x => x.clan_id === c.id) : -1;
  const lignesClassement = classement.length
    ? classement.map((x, i) => `<div class="cl-ligne${c && x.clan_id === c.id ? ' moi' : ''}"><b>${i + 1}</b>${blasonHtml(x.tag, x.couleur, true)}<span>${echapperTexte(x.nom)}</span><span class="cl-score">${nbClan(x.moyenne)}<small>par membre</small></span></div>`).join('')
    : '<p class="collection-empty">Aucun clan classé pour l\\'instant (il faut 3 membres).</p>';
  const blocClassement = `<div class="clan-carte"><h2>Classement des clans</h2>${lignesClassement}
    <p class="clan-note">À la moyenne de communes du Front par membre, jamais au total : un gros clan n'a pas d'avantage.</p></div>`;

  let gauche;
  if(!c){
    const invits = (moi.invitations || []).map(i => `<div class="clan-invit">${blasonHtml(i.tag, i.couleur)}<div><b>${echapperTexte(i.nom)}</b><small>${nbClan(i.membres)} membre${i.membres > 1 ? 's' : ''} · invitation de ${echapperTexte(i.par || 'un joueur')}</small></div>
        <button class="bq-btn" data-clan-oui="${i.clan_id}">Rejoindre</button><button class="bq-btn secondaire" data-clan-non="${i.clan_id}">Refuser</button></div>`).join('');
    const attente = moi.attente_jusqua ? new Date(moi.attente_jusqua) : null;
    gauche = `<div class="clan-carte">
      ${invits ? `<h2>Invitations</h2>${invits}` : ''}
      <h2>Créer un clan</h2>
      ${attente ? `<p class="clan-note">Tu as quitté un clan récemment : tu pourras en créer ou en rejoindre un le ${attente.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })} à ${attente.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}.</p>` : `
      <div class="clan-form">
        <label>Nom du clan<input id="clanNom" maxlength="24" placeholder="Les Charentais"></label>
        <label>Sigle<input id="clanTag" maxlength="4" placeholder="CHA"></label>
      </div>
      <div class="clan-couleurs" id="clanCouleurs">${CLAN_COULEURS.map(k => `<button type="button" aria-label="Couleur du clan" data-clan-couleur="${k}" aria-pressed="${k === clanCouleurChoisie}" style="background:${k}"></button>`).join('')}</div>
      <button class="bq-btn" id="clanCreer">Créer le clan</button>`}
      <p class="clan-note">Ou attends qu'un chef t'invite : son invitation apparaîtra ici.</p>
    </div>`;
  } else {
    const membres = (c.membres || []).map(m => `<div class="clan-membre"><span class="av" style="--clan:${c.couleur}">${echapperTexte((m.pseudo || '?')[0].toUpperCase())}</span>
        <div><b>${echapperTexte(m.pseudo)}</b><small>${m.chef ? 'Chef' : 'Membre'}${m.moi ? ' · toi' : ''}</small></div>
        <span class="clan-nb">${nbClan(m.communes)} communes</span>
        ${c.chef && !m.moi ? `<button class="bq-btn secondaire" data-clan-exclure="${m.id}">Exclure</button>` : '<span></span>'}</div>`).join('');
    const total = (c.membres || []).reduce((s, m) => s + (m.communes || 0), 0);
    const n = (c.membres || []).length;
    gauche = `<div class="clan-carte">
      <div class="clan-tete">${blasonHtml(c.tag, c.couleur)}<div><div class="clan-nom">${echapperTexte(c.nom)}</div><small>${n} membre${n > 1 ? 's' : ''} sur 5${n < 3 ? ' · classé à partir de 3' : ''}</small></div></div>
      <div class="puces"><span class="puce">Communes en Front <b>${nbClan(total)}</b></span><span class="puce">Moyenne par membre <b>${nbClan(n ? Math.round(total / n) : 0)}</b></span>${rang >= 0 ? `<span class="puce">Rang <b>${rang + 1}</b> sur ${classement.length}</span>` : ''}</div>
      <h2>Membres</h2>${membres}
      ${c.chef && n < 5 ? `<div class="clan-inviter"><input id="clanPseudo" placeholder="Pseudo du joueur à inviter"><button class="bq-btn" id="clanInviter">Inviter</button></div>` : ''}
      ${(c.invites || []).length ? `<p class="clan-note">Invitations en attente : ${c.invites.map(echapperTexte).join(', ')}.</p>` : ''}
      <ul class="clan-regles"><li>Pas d'attaque entre membres : leurs communes n'apparaissent plus dans tes cibles.</li><li>Aucun bonus de combat : le territoire d'un coéquipier ne compte pas dans tes chances.</li><li>Après avoir quitté un clan, il faut attendre 48 h avant d'en rejoindre un autre.</li><li>Pour discuter, demande un salon privé pour ton clan sur le Discord.</li></ul>
      <button class="bq-btn secondaire" id="clanQuitter" data-prix="0">Quitter le clan</button>
    </div>`;
  }
  zone.innerHTML = `<div class="clan-grille">${gauche}${blocClassement}</div>`;
}
async function actionClan(nom, args, succes){
  const { data, error } = await sb.rpc(nom, args || {});
  if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); return false; }
  if(succes) notifier({ type: 'succes', titre: succes });
  clanCache = clanCache || { classement: [] };
  clanCache.moi = data || {};
  await loadClansCarte();
  await loadClan();
  return true;
}
document.getElementById('panel-clan').addEventListener('click', (e) => {
  const b = e.target.closest('button');
  if(!b) return;
  if(b.dataset.clanCouleur){ clanCouleurChoisie = b.dataset.clanCouleur; document.querySelectorAll('#clanCouleurs button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); return; }
  if(b.id === 'clanCreer'){
    const nom = (document.getElementById('clanNom') || {}).value || '';
    const tag = (document.getElementById('clanTag') || {}).value || '';
    return actionClan('clan_creer', { p_nom: nom, p_tag: tag, p_couleur: clanCouleurChoisie }, 'Clan créé');
  }
  if(b.id === 'clanInviter'){
    const p = (document.getElementById('clanPseudo') || {}).value || '';
    if(!p.trim()) return;
    return actionClan('clan_inviter', { p_pseudo: p.trim() }, 'Invitation envoyée');
  }
  if(b.dataset.clanOui) return actionClan('clan_repondre', { p_clan: b.dataset.clanOui, p_accepter: true }, 'Bienvenue dans le clan');
  if(b.dataset.clanNon) return actionClan('clan_repondre', { p_clan: b.dataset.clanNon, p_accepter: false });
  if(b.dataset.clanExclure){
    if(!b.classList.contains('confirmer')){ b.classList.add('confirmer'); b.textContent = 'Confirmer'; return; }
    return actionClan('clan_exclure', { p_joueur: b.dataset.clanExclure }, 'Joueur exclu');
  }
  if(b.id === 'clanQuitter'){
    if(!b.classList.contains('confirmer')){ b.classList.add('confirmer'); b.textContent = 'Confirmer : quitter (48 h d\\'attente)'; return; }
    return actionClan('clan_quitter', {}, 'Tu as quitté le clan');
  }
});
if(CLANS) setTimeout(loadClansCarte, 1500);
"""
ecrire('app.js', js)

# ---------- style.css ---------------------------------------------------------------
css = lire('style.css')
assert '.clan-grille' not in css
css += u"""
/* patch110 : les clans */
html:not(.clans-ouverts) .tab[data-tab="clan"]{ display:none !important; }
.clan-zone{ width:100%; }
.clan-grille{ display:grid; grid-template-columns:minmax(0,1.25fr) minmax(0,1fr); gap:18px; align-items:start; width:100%; }
@media (max-width: 900px){ .clan-grille{ grid-template-columns:minmax(0,1fr); } }
.clan-carte{ background: rgba(15,31,56,0.55); border:1px solid rgba(169,188,212,0.18); border-radius:14px; padding:18px; }
.clan-carte h2{ font-family: var(--titre); font-size:1.3rem; margin:14px 0 8px; }
.clan-carte h2:first-child{ margin-top:0; }
.clan-tete{ display:flex; gap:16px; align-items:center; margin-bottom:12px; }
.clan-nom{ font-family: var(--titre); font-weight:900; font-size:2rem; line-height:1; }
.clan-tete small, .clan-invit small, .clan-membre small{ display:block; color: var(--brume); font-size:.8rem; margin-top:3px; }
.blason{ --clan:#E07A2E; width:64px; height:74px; flex-shrink:0; background: var(--clan); color:#1a0d02;
  clip-path: polygon(50% 0, 100% 15%, 100% 55%, 50% 100%, 0 55%, 0 15%);
  display:inline-flex; align-items:center; justify-content:center; font-family: var(--titre); font-weight:900; font-size:1.3rem; }
.blason.petit{ width:28px; height:32px; font-size:.6rem; }
.clan-membre, .clan-invit{ display:grid; grid-template-columns:34px minmax(0,1fr) auto auto; gap:12px; align-items:center; padding:9px 0; border-top:1px solid rgba(169,188,212,0.1); }
.clan-invit{ grid-template-columns:64px minmax(0,1fr) auto auto; }
.clan-membre .av{ width:34px; height:34px; border-radius:50%; background: var(--nuit-3); display:flex; align-items:center; justify-content:center; font-family: var(--titre); font-weight:800; box-shadow:0 0 0 2px var(--clan); }
.clan-nb{ color: var(--brume); font-size:.85rem; }
.clan-inviter, .clan-form{ display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; }
.clan-form label{ display:flex; flex-direction:column; gap:4px; font-size:.8rem; color: var(--brume); flex:1; min-width:140px; }
.clan-inviter input, .clan-form input{ flex:1; background: var(--nuit); border:1px solid rgba(169,188,212,0.3); border-radius:9px; padding:9px 12px; color:#fff; font:inherit; }
.clan-couleurs{ display:flex; gap:8px; margin:12px 0; }
.clan-couleurs button{ width:28px; height:28px; border-radius:50%; border:2px solid rgba(255,255,255,.2); cursor:pointer; padding:0; }
.clan-couleurs button[aria-pressed="true"]{ border-color:#fff; box-shadow:0 0 0 2px var(--nuit), 0 0 0 4px #fff; }
.clan-note{ color: var(--brume); font-size:.82rem; line-height:1.5; margin:10px 0 0; }
.clan-regles{ margin:14px 0; padding-left:18px; color: var(--brume); font-size:.84rem; line-height:1.55; }
.cl-ligne{ display:grid; grid-template-columns:22px 30px minmax(0,1fr) auto; gap:10px; align-items:center; padding:8px 4px; border-top:1px solid rgba(169,188,212,0.1); }
.cl-ligne.moi{ background: rgba(240,180,41,0.08); border-radius:8px; }
.cl-ligne .cl-score{ font-family: var(--titre); font-size:1.1rem; text-align:right; }
.cl-ligne .cl-score small{ display:block; font-family: var(--texte); font-size:.68rem; color: var(--brume); }
"""
ecrire('style.css', css)
print(u'patch110 applique')
