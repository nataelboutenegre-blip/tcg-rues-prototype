# -*- coding: utf-8 -*-
u"""
patch214 — Échange en trois onglets (Proposer · Mes alertes · En cours) et
alertes d'échange (idée d'Arkhannou, Discord, 26 octobre). Aperçu validé
(« parfait ! ») : 10 communes au plus, prévenir seulement dans le jeu,
liste visible par ceux qui ont tes communes en double.
 - Je cherche : mes communes voulues, qui les a en double, « Proposer » remplit
   le formulaire (rareté, commune, joueur).
 - On cherche tes doublons : qui cherche mes doublons, « Voir ses doublons »
   choisit ma commune et filtre « Tu reçois » sur ce joueur.
 - Les plus recherchées.
 - Pastilles : onglet Échange (propositions reçues + nouveautés), Mes alertes,
   En cours ; notification quand une commune cherchée devient disponible.
SQL : _sql/s2-31-alertes-echange.sql, À PASSER AVANT de pousser.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a)
    assert c == n, (a[:90], c, n)
    return s.replace(a, b)

# ---------------------------------------------------------------- index.html
h = lire('index.html')
assert 'echOnglets' not in h
h = rep(h, u"""        <button type="button" class="ech-raccourci" id="echRaccourci" hidden></button></div>
""", u"""        <button type="button" class="ech-raccourci" id="echRaccourci" hidden></button></div>
      <div class="ech-onglets" id="echOnglets" role="tablist" hidden>
        <button type="button" data-ech-vue="proposer" class="actif" aria-selected="true">Proposer</button>
        <button type="button" data-ech-vue="alertes" aria-selected="false">Mes alertes<i class="ech-pastille" id="echAlertesBadge" hidden></i></button>
        <button type="button" data-ech-vue="cours" aria-selected="false">En cours<i class="ech-pastille" id="echCoursBadge" hidden></i></button>
      </div>
""")
h = rep(h, u"""      <div class="bourse-section">
        <h2>Proposer un échange</h2>""", u"""      <div class="bourse-section" data-ech-zone="proposer">
        <h2>Proposer un échange</h2>""")
h = rep(h, u"""      <div class="bourse-section" id="echPropositions" hidden>""", u"""      <div class="bourse-section ech-alertes" id="echAlertes" data-ech-zone="alertes" hidden></div>

      <div class="bourse-section" id="echPropositions" data-ech-zone="cours" hidden>""")
ecrire('index.html', h)

# ---------------------------------------------------------------- app.js
js = lire('app.js')
assert 'patch214' not in js

# 1. les propositions : en mode onglets, le bloc suit l'onglet et dit quand il est vide
js = rep(js, u"""  bloc.hidden = echangesEnCours.length === 0;
  liste.innerHTML = echangesEnCours.map(ligneEchange).join('');""", u"""  bloc.hidden = ongletsEchange() ? echVue !== 'cours' : echangesEnCours.length === 0;   // patch214
  liste.innerHTML = echangesEnCours.map(ligneEchange).join('')
    || (ongletsEchange() ? '<p class="collection-empty">Aucune proposition en cours. Propose un échange ou regarde tes alertes.</p>' : '');""")

# 2. la pastille de l'onglet Échange compte aussi les nouveautés des alertes
js = rep(js, u"""  const recues = echangesEnCours.filter(e => e.sens === 'recu').length;
  const badge = document.getElementById('echangeBadge');
  if(!badge) return;
  badge.hidden = recues === 0;
  badge.textContent = recues;
}""", u"""  const recues = echangesEnCours.filter(e => e.sens === 'recu').length;
  const nouv = alertesNouvelles().size;   // patch214
  const pc = document.getElementById('echCoursBadge');
  if(pc){ pc.hidden = recues === 0; pc.textContent = recues; }
  const pa = document.getElementById('echAlertesBadge');
  if(pa){ pa.hidden = nouv === 0; pa.textContent = nouv; }
  const badge = document.getElementById('echangeBadge');
  if(!badge) return;
  badge.hidden = recues + nouv === 0;
  badge.textContent = recues + nouv;
}""")

# 3. chargements
js = rep(js, u"""  await chargerEchangesEnCours();
  renderEchangePropositions();
  renderEchangeMien();
  await chargerCiblesEchange();""", u"""  await chargerEchangesEnCours();
  majVueEchange();   // patch214
  if(ongletsEchange()) chargerAlertes();
  renderEchangePropositions();
  renderEchangeMien();
  await chargerCiblesEchange();""")
js = rep(js, u"""  if(panneau && panneau.classList.contains('active')) renderEchangePropositions();
  signalerNouveauxEchanges();
}""", u"""  if(panneau && panneau.classList.contains('active')) renderEchangePropositions();
  signalerNouveauxEchanges();
  if(ongletsEchange() && Date.now() - alertesLu > 180000) chargerAlertes();   // patch214
}""")

# 4. le raccourci du haut ouvre l'onglet En cours
js = rep(js, u"""document.getElementById('echRaccourci').addEventListener('click', () => {
  const bloc = document.getElementById('echPropositions');""", u"""document.getElementById('echRaccourci').addEventListener('click', () => {
  if(ongletsEchange()){ majVueEchange('cours'); return; }   // patch214
  const bloc = document.getElementById('echPropositions');""")

# 5. le module des alertes
js = rep(js, u"""document.getElementById('echTiers').addEventListener('click', async (e) => {""", u"""// ---------- patch214 : Échange en onglets et alertes d'échange ----------
let echVue = 'proposer';
let alertesEtat = null, alertesLu = 0, alertesCles = null, alertesMontrees = new Set();
const CLE_ALERTES_VUES = 'tf-alertes-vues';
const ALERTES_MAX = 10;
const ongletsEchange = () => marcheTerra();
function alertesVues(){
  try{ return new Set(JSON.parse(localStorage.getItem(CLE_ALERTES_VUES) || '[]')); }catch(e){ return new Set(); }
}
function clesAlertes(a){
  const k = new Set();
  if(!a) return k;
  for(const c of a.je_cherche || []) for(const d of c.dispo || []) k.add('c|' + c.code + '|' + d.id);
  for(const c of a.mes_doublons || []) for(const d of c.chercheurs || []) k.add('d|' + c.code + '|' + d.id);
  return k;
}
function alertesNouvelles(){
  if(!alertesEtat) return new Set();
  const vues = alertesVues();
  return new Set([...clesAlertes(alertesEtat)].filter(k => !vues.has(k)));
}
function marquerAlertesVues(){
  const k = [...clesAlertes(alertesEtat)];
  try{ localStorage.setItem(CLE_ALERTES_VUES, JSON.stringify(k.slice(-300))); }catch(e){}
}
async function chargerAlertes(){
  if(!ongletsEchange()) return;
  alertesLu = Date.now();
  const { data, error } = await sb.rpc('terra_mes_alertes');
  if(error){ console.warn('TERRAFRONT alertes indisponibles', error); return; }
  alertesEtat = data || { je_cherche: [], mes_doublons: [], plus_recherchees: [] };
  // prévenir une seule fois par commune et par joueur, pendant la séance
  const cles = clesAlertes(alertesEtat), vues = alertesVues();
  const neuves = [...cles].filter(k => !vues.has(k) && !(alertesCles && alertesCles.has(k)) && !alertesMontrees.has(k));
  neuves.forEach(k => alertesMontrees.add(k));
  const surAlertes = echVue === 'alertes' && document.getElementById('panel-echange')?.classList.contains('active');
  if(neuves.length && !surAlertes){
    const dispo = neuves.filter(k => k[0] === 'c'), cherche = neuves.filter(k => k[0] === 'd');
    const nomDe = (k) => { const code = k.split('|')[1]; const c = [...alertesEtat.je_cherche, ...alertesEtat.mes_doublons].find(x => x.code === code); return c ? c.nom : code; };
    if(dispo.length) notifier({ type: 'info', titre: dispo.length === 1 ? `${nomDe(dispo[0])} est disponible` : 'Des communes que tu cherches sont disponibles',
                                texte: 'Un joueur l\\u2019a en double : regarde Échange › Mes alertes.' });
    else if(cherche.length) notifier({ type: 'info', titre: `On cherche ${nomDe(cherche[0])}`,
                                texte: 'Un joueur cherche une commune que tu as en double : Échange › Mes alertes.' });
  }
  alertesCles = cles;
  majBadgeEchange();
  if(surAlertes){ renderAlertes(); marquerAlertesVues(); majBadgeEchange(); }
}
function majVueEchange(vue){
  if(vue) echVue = vue;
  const actif = ongletsEchange();
  const ong = document.getElementById('echOnglets');
  if(ong){
    ong.hidden = !actif;
    ong.querySelectorAll('[data-ech-vue]').forEach(b => {
      const on = b.dataset.echVue === echVue;
      b.classList.toggle('actif', on); b.setAttribute('aria-selected', String(on));
    });
  }
  const zp = document.querySelector('#panel-echange [data-ech-zone="proposer"]');
  if(zp) zp.hidden = actif && echVue !== 'proposer';
  const za = document.getElementById('echAlertes');
  if(za) za.hidden = !actif || echVue !== 'alertes';
  renderEchangePropositions();
  if(actif && echVue === 'alertes'){
    renderAlertes();
    if(alertesEtat){ marquerAlertesVues(); majBadgeEchange(); }
    if(Date.now() - alertesLu > 30000) chargerAlertes();
  }
}
const tierInfo = (id) => TIERS.find(t => t.id === id) || TIERS[TIERS.length - 1];
function alerteMini(tier){ return `<span class="al-mini" style="--t:${tierInfo(tier).color}"></span>`; }
function alertePseudos(liste, max, attr, c){
  const n = liste.length;
  const vus = liste.slice(0, max).map(d => `<button type="button" class="al-qui" ${attr}="${echapperTexte(c.code)}" data-al-id="${echapperTexte(d.id)}" data-al-pseudo="${echapperTexte(d.pseudo || '')}">${echapperTexte(d.pseudo || 'un joueur')}</button>`);
  const reste = n - vus.length;
  return vus.length === 1 ? vus[0] : vus.slice(0, -1).join(', ') + (reste > 0 ? ', ' + vus[vus.length - 1] + ` et ${reste} autre${reste > 1 ? 's' : ''}` : ' et ' + vus[vus.length - 1]);
}
function renderAlertes(){
  const zone = document.getElementById('echAlertes');
  if(!zone) return;
  if(!alertesEtat){ zone.innerHTML = '<p class="collection-empty">Chargement…</p>'; return; }
  const nouv = alertesNouvelles();
  const a = alertesEtat, cherche = a.je_cherche || [];
  const neuf = (prefixe, code, liste) => liste.some(d => nouv.has(prefixe + '|' + code + '|' + d.id));
  const champ = document.getElementById('alAjout');
  const garde = champ ? champ.value : '';
  let h = `<h2>Je cherche</h2>
    <p class="ech-astuce">Ajoute les communes que tu veux (${ALERTES_MAX} au plus). Dès qu'un joueur en a une en double, elle passe en vert ici et l'onglet Échange s'allume.</p>
    <div class="al-ajout"><input type="search" id="alAjout" class="bourse-search" placeholder="Ajouter une commune…" autocomplete="off"${cherche.length >= ALERTES_MAX ? ' disabled' : ''}><b>${cherche.length} / ${ALERTES_MAX}</b></div>
    <div class="al-sugg" id="alSugg"></div>`;
  h += cherche.length ? cherche.map(c => {
    const dispo = c.dispo || [], t = tierInfo(c.tier), n = neuf('c', c.code, dispo);
    return `<div class="al-ligne${dispo.length ? ' dispo' : ''}${n ? ' nouveau' : ''}">${alerteMini(c.tier)}
      <div class="al-info"><div class="al-nom">${echapperTexte(c.nom)}${n ? '<span class="al-neuf">NOUVEAU</span>' : ''}</div>
      <div class="al-tier" style="color:${t.color}">${t.label} · ${echapperTexte(c.dept)}</div>
      <div class="al-etat${dispo.length ? ' ok' : ''}">${dispo.length ? 'En double chez ' + alertePseudos(dispo, 3, 'data-al-proposer', c) : 'Personne ne l\\u2019a en double pour l\\u2019instant'}</div></div>
      ${dispo.length ? `<button type="button" class="al-btn" data-al-proposer="${echapperTexte(c.code)}" data-al-id="${echapperTexte(dispo[0].id)}" data-al-pseudo="${echapperTexte(dispo[0].pseudo || '')}">Proposer</button>` : ''}
      <button type="button" class="al-x" data-al-retirer="${echapperTexte(c.code)}" aria-label="Retirer ${echapperTexte(c.nom)} de ma liste">✕</button></div>`;
  }).join('') : '<p class="collection-empty">Ta liste est vide : ajoute la commune qui te manque.</p>';
  const md = a.mes_doublons || [];
  if(md.length){
    h += `<h2>On cherche tes doublons</h2><p class="ech-astuce">Des joueurs cherchent des communes que tu as en double : un échange tout trouvé.</p>`;
    h += md.map(c => {
      const ch = c.chercheurs || [], t = tierInfo(c.tier), n = neuf('d', c.code, ch);
      return `<div class="al-ligne${n ? ' nouveau' : ''}">${alerteMini(c.tier)}
        <div class="al-info"><div class="al-nom">${echapperTexte(c.nom)}${n ? '<span class="al-neuf">NOUVEAU</span>' : ''}</div>
        <div class="al-tier" style="color:${t.color}">${t.label} · ${c.libres} en double</div>
        <div class="al-etat">Cherchée par ${alertePseudos(ch, 3, 'data-al-voir', c)}${Number(c.nb) > ch.length ? ` (${c.nb} joueurs)` : ''}</div></div>
        ${ch.length ? `<button type="button" class="al-btn" data-al-voir="${echapperTexte(c.code)}" data-al-id="${echapperTexte(ch[0].id)}" data-al-pseudo="${echapperTexte(ch[0].pseudo || '')}">Voir ses doublons</button>` : ''}</div>`;
    }).join('');
  }
  const top = a.plus_recherchees || [];
  if(top.length){
    h += `<h2>Les plus recherchées</h2><p class="ech-astuce">Les communes en alerte chez le plus de joueurs.</p>`;
    h += top.map(c => `<div class="al-ligne">${alerteMini(c.tier)}<div class="al-info"><div class="al-nom">${echapperTexte(c.nom)}</div>
      <div class="al-etat">${c.nb} joueurs la cherchent</div></div></div>`).join('');
  }
  zone.innerHTML = h;
  const nc = document.getElementById('alAjout');
  if(nc && garde){ nc.value = garde; }
}
const alerteDe = (code) => alertesEtat && [...(alertesEtat.je_cherche || []), ...(alertesEtat.mes_doublons || [])].find(c => c.code === code);
async function choisirRareteEchange(tier){
  document.querySelectorAll('#echTiers .filter-pill').forEach(p => p.classList.toggle('active', p.dataset.tier === tier));
  echangeTier = tier;
}
async function allerProposerAlerte(code, id, pseudo){
  const c = alerteDe(code);
  if(!c) return;
  majVueEchange('proposer');
  await choisirRareteEchange(c.tier);
  echangeMien = null; echangeCible = null;
  echangeRecherche = c.nom + (pseudo ? ', ' + pseudo : '');
  const champ = document.getElementById('echSearch'); if(champ) champ.value = echangeRecherche;
  renderEchangeMien();
  await chargerCiblesEchange();
  echangeCible = echangeCibles.find(x => x.commune_code === code && x.proprietaire === id) || echangeCibles.find(x => x.commune_code === code) || null;
  renderEchangeCibles();
  document.getElementById('echMien')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  notifier({ type: 'info', titre: `${c.nom} chez ${pseudo || 'ce joueur'}`, texte: 'Choisis ce que tu donnes en échange (même rareté).' });
}
async function allerVoirAlerte(code, id, pseudo){
  const c = alerteDe(code);
  if(!c) return;
  majVueEchange('proposer');
  await choisirRareteEchange(c.tier);
  const cm = document.getElementById('echSearchMien'); if(cm) cm.value = '';
  echangeMien = code; echangeCible = null;
  echangeRecherche = pseudo || '';
  const champ = document.getElementById('echSearch'); if(champ) champ.value = echangeRecherche;
  renderEchangeMien();
  await chargerCiblesEchange();
  document.getElementById('echCibles')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  notifier({ type: 'info', titre: `${pseudo || 'Ce joueur'} cherche ${c.nom}`, texte: echangeCibles.length ? 'Choisis ce que tu veux recevoir parmi ses doublons.' : 'Il n\\u2019a aucun doublon de cette rareté pour l\\u2019instant.' });
}
let alertesMinuteur = null;
document.getElementById('echOnglets').addEventListener('click', (e) => {
  const b = e.target.closest('[data-ech-vue]');
  if(b) majVueEchange(b.dataset.echVue);
});
document.getElementById('echAlertes').addEventListener('input', (e) => {
  if(e.target.id !== 'alAjout') return;
  clearTimeout(alertesMinuteur);
  const texte = e.target.value.trim();
  alertesMinuteur = setTimeout(async () => {
    const zone = document.getElementById('alSugg');
    if(!zone) return;
    if(texte.length < 2){ zone.innerHTML = ''; return; }
    const { data, error } = await sb.rpc('terra_recherche_suggerer', { p_texte: texte });
    if(error){ zone.innerHTML = `<p class="prix-erreur">${echapperTexte(messageLisible(error.message))}</p>`; return; }
    const deja = new Set((alertesEtat && alertesEtat.je_cherche || []).map(c => c.code));
    const l = (data || []).filter(c => !deja.has(c.code));
    zone.innerHTML = l.length ? l.map(c => `<button type="button" class="al-sugg-b" data-al-ajouter="${echapperTexte(c.code)}">
        ${alerteMini(c.tier)}<b>${echapperTexte(c.nom)}</b><small>${echapperTexte(c.departement)} · ${tierInfo(c.tier).label}</small></button>`).join('')
      : '<p class="ech-astuce">Aucune commune à ajouter (ou tu l\\u2019as déjà).</p>';
  }, 250);
});
document.getElementById('echAlertes').addEventListener('click', async (e) => {
  const aj = e.target.closest('[data-al-ajouter]');
  const re = e.target.closest('[data-al-retirer]');
  const pr = e.target.closest('[data-al-proposer]');
  const vo = e.target.closest('[data-al-voir]');
  if(pr) return allerProposerAlerte(pr.dataset.alProposer, pr.dataset.alId, pr.dataset.alPseudo);
  if(vo) return allerVoirAlerte(vo.dataset.alVoir, vo.dataset.alId, vo.dataset.alPseudo);
  const b = aj || re;
  if(!b) return;
  b.disabled = true;
  const { error } = await sb.rpc(aj ? 'terra_recherche_ajouter' : 'terra_recherche_retirer', { p_code: aj ? aj.dataset.alAjouter : re.dataset.alRetirer });
  if(error){ b.disabled = false; notifier({ type: 'erreur', titre: 'Liste de recherche', texte: messageLisible(error.message) }); return; }
  if(aj){ const ch = document.getElementById('alAjout'); if(ch) ch.value = ''; }
  await chargerAlertes();
  renderAlertes();
  marquerAlertesVues(); majBadgeEchange();
});

document.getElementById('echTiers').addEventListener('click', async (e) => {""")
ecrire('app.js', js)

css = lire('style.css')
assert 'patch214' not in css
css += u"""
/* patch214 : Échange en onglets, alertes d'échange */
.ech-onglets{ display:flex; gap:6px; background:rgba(0,0,0,.25); padding:4px; border-radius:12px; margin:4px 0 16px; }
.ech-onglets button{ flex:1; font:inherit; font-size:.88rem; font-weight:700; color:var(--brume); background:none; border:0; border-radius:9px; padding:8px 4px; cursor:pointer; }
.ech-onglets button.actif{ background:rgba(255,255,255,.09); color:#fff; }
.ech-pastille{ display:inline-grid; place-items:center; min-width:18px; height:18px; padding:0 5px; margin-left:5px; border-radius:9px; background:#E5484D; color:#fff; font-size:.7rem; font-style:normal; vertical-align:1px; }
.ech-pastille[hidden]{ display:none; }
.ech-alertes h2{ margin-top:18px; }
.ech-alertes h2:first-child{ margin-top:0; }
.al-ajout{ display:flex; gap:10px; align-items:center; margin:8px 0 6px; }
.al-ajout input{ flex:1; margin:0; }
.al-ajout b{ font-size:.8rem; color:var(--brume); white-space:nowrap; }
.al-sugg{ display:flex; flex-direction:column; gap:6px; margin-bottom:10px; }
.al-sugg-b{ display:flex; align-items:center; gap:10px; font:inherit; color:inherit; text-align:left; background:rgba(255,255,255,.05); border:1px solid rgba(169,188,212,.18); border-radius:10px; padding:7px 10px; cursor:pointer; }
.al-sugg-b small{ color:var(--brume); margin-left:auto; font-size:.75rem; }
.al-sugg-b .al-mini{ width:20px; }
.al-ligne{ display:flex; gap:10px; align-items:center; background:rgba(255,255,255,.04); border:1px solid rgba(169,188,212,.16); border-radius:12px; padding:9px 10px; margin-bottom:8px; }
.al-ligne.nouveau{ border-color:rgba(61,214,140,.55); box-shadow:0 0 0 1px rgba(61,214,140,.22) inset; }
.al-mini{ flex:none; width:34px; aspect-ratio:2/3; border-radius:6px; border:2px solid var(--t); background:linear-gradient(160deg, var(--t) -50%, #0E1F36 60%); }
.al-info{ flex:1; min-width:0; }
.al-nom{ font-weight:700; display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
.al-tier{ font-size:.72rem; font-weight:700; }
.al-etat{ font-size:.8rem; color:var(--brume); margin-top:1px; }
.al-etat.ok{ color:#3DD68C; }
.al-qui{ font:inherit; color:#fff; background:none; border:0; padding:0; cursor:pointer; text-decoration:underline; text-decoration-color:rgba(255,255,255,.3); text-underline-offset:2px; }
.al-neuf{ font-size:.62rem; font-weight:800; background:#3DD68C; color:#04210f; border-radius:5px; padding:1px 5px; }
.al-btn{ flex:none; font:inherit; font-size:.8rem; font-weight:800; border:0; border-radius:9px; padding:8px 10px; background:var(--c-legendaire, #F0B429); color:#1a1200; cursor:pointer; }
.al-x{ flex:none; font:inherit; color:var(--brume); background:none; border:0; padding:4px 6px; cursor:pointer; font-size:.95rem; }
@media (max-width:420px){ .al-btn{ padding:7px 8px; font-size:.75rem; } }
"""
ecrire('style.css', css)
print('patch214 ok')
