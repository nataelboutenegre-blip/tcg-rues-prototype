# -*- coding: utf-8 -*-
u"""
patch194 — les echanges entre membres d'un clan, en Front (apercu valide le
26 octobre). Bloc « Echanges du clan » dans l'onglet Clan, sous les membres,
en mode Front et seulement dans un clan : propositions recues (accepter /
refuser), proposer en 3 temps (avec qui, je donne, je recois — meme rarete),
envoyees (annuler), regles. Pastille sur l'onglet Clan quand une proposition
attend. SQL : _sql/s2-29-clans-echanges.sql, a passer AVANT.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

js = lire('app.js')
assert 'clan_ech_etat' not in js, u'patch194 deja applique'

# 1. l'etat, les listes, le rendu du bloc
js = rempl(js, u"""let monUidClan = null;
let clanCache = null;""", u"""let monUidClan = null;
let clanCache = null;
// patch194 : les echanges entre membres du clan (Front)
const clanEch = { etat: null, qui: null, donne: null, recoit: null, mes: null, leurs: null, r1: '', r2: '' };
const enFrontClan = () => SAISON2 && modeJeu === 'front';
async function chargerClanEch(){
  if(!SAISON2) return null;
  try{
    const { data, error } = await sb.rpc('clan_ech_etat');
    clanEch.etat = error ? null : data;
  }catch(e){ clanEch.etat = null; }
  majBadgeClanEch();
  return clanEch.etat;
}
function majBadgeClanEch(){
  const tab = document.querySelector('.tab[data-tab="clan"]');
  if(!tab) return;
  let b = tab.querySelector('.tab-badge');
  const n = clanEch.etat && clanEch.etat.recus ? clanEch.etat.recus.length : 0;
  if(!n){ if(b) b.hidden = true; return; }
  if(!b){ b = document.createElement('span'); b.className = 'tab-badge'; tab.appendChild(b); }
  b.hidden = false;
  b.textContent = n;
}
function ceTier(id){ return TIERS.find(t => t.id === id) || TIERS[TIERS.length - 1]; }
function ceCommune(c, tier){
  const t = ceTier(tier || c.tier);
  return `<span class="ce-com"><i style="background:var(--c-${t.id})"></i><b>${echapperTexte(c.nom)}</b><small>${t.label} · ${echapperTexte(c.dept || c.departement || '')}</small></span>`;
}
function ceDans(iso){
  const h = Math.max(0, Math.round((new Date(iso).getTime() - Date.now()) / 3600000));
  return h < 1 ? 'expire dans moins d\\'une heure' : `expire dans ${h} h`;
}
function ceListeHtml(liste, cle, choisi, filtre){
  if(!liste) return '<p class="ce-attente">Chargement…</p>';
  const f = sansAccents((filtre || '').toLowerCase());
  const l = liste.filter(c => !f || sansAccents(c.nom.toLowerCase()).includes(f) || String(c.departement).toLowerCase() === f);
  if(!l.length) return '<p class="ce-attente">Aucune commune.</p>';
  return l.slice(0, 80).map(c => `<button type="button" class="ce-choix" data-${cle}="${echapperTexte(c.code)}" aria-pressed="${c.code === choisi}"${c.raison ? ' disabled' : ''}>${ceCommune(c)}${c.raison ? `<span class="ce-raison">${echapperTexte(c.raison)}</span>` : ''}</button>`).join('');
}
function ceLeursFiltrees(){
  if(!clanEch.leurs) return null;
  const mienne = clanEch.mes && clanEch.donne ? clanEch.mes.find(c => c.code === clanEch.donne) : null;
  return mienne ? clanEch.leurs.filter(c => c.tier === mienne.tier) : clanEch.leurs;
}
function ceRecapHtml(){
  const m = clanEch.mes && clanEch.donne ? clanEch.mes.find(c => c.code === clanEch.donne) : null;
  const s = clanEch.leurs && clanEch.recoit ? clanEch.leurs.find(c => c.code === clanEch.recoit) : null;
  const qui = (clanEch.etat && clanEch.etat.membres || []).find(x => x.id === clanEch.qui);
  return m && s && qui
    ? `<span>Tu donnes <b>${echapperTexte(m.nom)}</b> à ${echapperTexte(qui.pseudo)} contre <b>${echapperTexte(s.nom)}</b>.</span><button type="button" class="bq-btn" data-ce-proposer>Proposer l'échange</button>`
    : `<span class="ce-attente">Choisis une commune de chaque côté.</span><button type="button" class="bq-btn" disabled>Proposer l'échange</button>`;
}
function majListesCe(){
  const d = document.getElementById('ceDonne'), r = document.getElementById('ceRecoit'), rc = document.getElementById('ceRecap'), t3 = document.getElementById('ceT3');
  if(d) d.innerHTML = ceListeHtml(clanEch.mes, 'ce-donne', clanEch.donne, clanEch.r1);
  const leurs = ceLeursFiltrees();
  if(leurs && clanEch.recoit && !leurs.some(c => c.code === clanEch.recoit)) clanEch.recoit = null;
  if(r) r.innerHTML = clanEch.qui ? ceListeHtml(leurs, 'ce-recoit', clanEch.recoit, clanEch.r2) : '<p class="ce-attente">Choisis d\\'abord un coéquipier.</p>';
  const mienne = clanEch.mes && clanEch.donne ? clanEch.mes.find(c => c.code === clanEch.donne) : null;
  if(t3) t3.textContent = '3. Tu reçois · ' + (mienne ? ceTier(mienne.tier).label.toLowerCase() : 'même rareté');
  if(rc) rc.innerHTML = ceRecapHtml();
}
function blocEchangesClan(){
  const e = clanEch.etat;
  if(!enFrontClan() || !e || !e.clan) return '';
  const restant = Math.max(0, (e.max || 2) - (e.faits || 0));
  const prop = (x, recu) => `<div class="ce-prop"><div>
      <div class="ce-qui">${recu ? `<b>${echapperTexte(x.pseudo)}</b> te propose` : `à <b>${echapperTexte(x.pseudo)}</b> · en attente`} · ${ceDans(x.expire_le)}</div>
      <div class="ce-troc">${ceCommune(recu ? x.recoit : x.donne, x.tier)}<span class="ce-fl" aria-hidden="true">⇄</span>${ceCommune(recu ? x.donne : x.recoit, x.tier)}</div>
      ${recu ? `<div class="ce-attente">Tu donnes ${echapperTexte(x.donne.nom)}, tu reçois ${echapperTexte(x.recoit.nom)}.</div>` : ''}</div>
    <div class="ce-actions">${recu ? `<button type="button" class="bq-btn" data-ce-accepter="${Number(x.id)}">Accepter</button><button type="button" class="bq-btn secondaire" data-ce-refuser="${Number(x.id)}">Refuser</button>`
                                  : `<button type="button" class="bq-btn secondaire" data-ce-annuler="${Number(x.id)}">Annuler</button>`}</div></div>`;
  const pret = e.pret_le ? new Date(e.pret_le) : null;
  const membres = e.membres || [];
  const proposer = pret
    ? `<p class="clan-note">Tu pourras échanger avec ton clan à partir du ${pret.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })} à ${pret.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })} (48 h après ton arrivée).</p>`
    : !membres.length ? '<p class="clan-note">Il faut au moins un coéquipier pour échanger.</p>'
    : restant === 0 ? '<p class="clan-note">Tu as fait tes 2 échanges du jour. Reviens demain.</p>'
    : `<div class="ce-etape"><div class="ce-attente">1. Avec qui</div>
        <div class="ce-membres">${membres.map(m => `<button type="button" class="ce-membre" data-ce-qui="${echapperTexte(m.id)}" aria-pressed="${m.id === clanEch.qui}"><span class="av" style="--clan:${(clanCache && clanCache.moi && clanCache.moi.clan || {}).couleur || '#E07A2E'}">${echapperTexte((m.pseudo || '?')[0].toUpperCase())}</span>${echapperTexte(m.pseudo)}</button>`).join('')}</div></div>
      <div class="ce-deux">
        <div><div class="ce-attente">2. Tu donnes</div><input type="search" class="ce-recherche" id="ceR1" placeholder="Une de tes communes…" aria-label="Chercher une de tes communes" value="${echapperTexte(clanEch.r1)}"><div class="ce-liste" id="ceDonne"></div></div>
        <div><div class="ce-attente" id="ceT3">3. Tu reçois · même rareté</div><input type="search" class="ce-recherche" id="ceR2" placeholder="Une commune de ton coéquipier…" aria-label="Chercher une commune du coéquipier" value="${echapperTexte(clanEch.r2)}"><div class="ce-liste" id="ceRecoit"></div></div>
      </div>
      <div class="ce-recap" id="ceRecap"></div>`;
  return `<div class="ce-bloc"><div class="ce-tete"><h2>Échanges du clan</h2><span class="puce">${restant ? `<b>${restant}</b> échange${restant > 1 ? 's' : ''} possible${restant > 1 ? 's' : ''} aujourd'hui` : 'plus d\\'échange aujourd\\'hui'}</span></div>
    ${(e.recus || []).length ? `<h3 class="ce-h3">Reçus</h3>${e.recus.map(x => prop(x, true)).join('')}` : ''}
    <h3 class="ce-h3">Proposer un échange</h3>${proposer}
    ${(e.envoyes || []).length ? `<h3 class="ce-h3">Envoyés</h3>${e.envoyes.map(x => prop(x, false)).join('')}` : ''}
    <ul class="clan-regles"><li>Seulement entre membres du clan, une commune contre une commune de même rareté.</li><li>2 échanges par jour et par joueur. Une proposition expire au bout de 24 h.</li><li>Impossible pour une commune prise il y a moins de 24 h, en garnison, ou échangée il y a moins de 48 h.</li><li>Il faut être dans le clan depuis 48 h. Un échange ne rapporte aucun point de combat.</li></ul></div>`;
}
async function ceChargerCommunes(){
  if(!monUidClan){ const { data: u } = await sb.auth.getUser(); monUidClan = u && u.user ? u.user.id : null; }
  if(!clanEch.mes && monUidClan){
    const { data, error } = await sb.rpc('clan_ech_communes', { p_joueur: monUidClan });
    clanEch.mes = error ? [] : (data || []);
  }
  if(clanEch.qui && !clanEch.leurs){
    const { data, error } = await sb.rpc('clan_ech_communes', { p_joueur: clanEch.qui });
    clanEch.leurs = error ? [] : (data || []);
  }
  majListesCe();
}
async function ceAction(nom, args, apres){
  const { data, error } = await sb.rpc(nom, args);
  if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); return; }
  notifier({ type: 'succes', titre: String(data || 'C\\'est fait') });
  if(apres) apres();
  clanEch.mes = null; clanEch.leurs = null;
  await chargerClanEch();
  if(nom === 'clan_ech_repondre') await loadClansCarte();
  renderClan();
}""", 'etat')

# 2. le bloc sous les membres, en Front
js = rempl(js, u"""      ${(c.invites || []).length ? `<p class="clan-note">Invitations en attente : ${c.invites.map(echapperTexte).join(', ')}.</p>` : ''}
      <ul class="clan-regles">""", u"""      ${(c.invites || []).length ? `<p class="clan-note">Invitations en attente : ${c.invites.map(echapperTexte).join(', ')}.</p>` : ''}
      ${blocEchangesClan()}
      <ul class="clan-regles">""", 'bloc')
js = rempl(js, u"""  zone.innerHTML = `<div class="clan-grille">${gauche}${blocClassement}</div>`;
}""", u"""  zone.innerHTML = `<div class="clan-grille">${gauche}${blocClassement}</div>`;
  if(document.getElementById('ceDonne')) ceChargerCommunes();   // patch194
}""", 'apres rendu')
js = rempl(js, u"""  clanCache = { moi: mc.data || {}, classement: cl.error ? [] : (cl.data || []), formation: cf.error ? [] : (cf.data || []),""",
u"""  if(SAISON2) await chargerClanEch();   // patch194
  clanCache = { moi: mc.data || {}, classement: cl.error ? [] : (cl.data || []), formation: cf.error ? [] : (cf.data || []),""", 'loadClan')

# 3. les clics et la recherche
js = rempl(js, u"""  if(b.dataset.clanVoir){ basculerClanVu(b.dataset.clanVoir); return; }   // patch186""",
u"""  if(b.dataset.clanVoir){ basculerClanVu(b.dataset.clanVoir); return; }   // patch186
  // patch194 : les echanges du clan
  if(b.dataset.ceQui){ if(clanEch.qui !== b.dataset.ceQui){ clanEch.qui = b.dataset.ceQui; clanEch.leurs = null; clanEch.recoit = null; clanEch.r2 = ''; }
    document.querySelectorAll('.ce-membre').forEach(x => x.setAttribute('aria-pressed', String(x === b)));
    const r2 = document.getElementById('ceR2'); if(r2) r2.value = '';
    majListesCe(); ceChargerCommunes(); return; }
  if(b.dataset.ceDonne){ clanEch.donne = b.dataset.ceDonne; majListesCe(); return; }
  if(b.dataset.ceRecoit){ clanEch.recoit = b.dataset.ceRecoit; majListesCe(); return; }
  if(b.hasAttribute('data-ce-proposer')){ b.disabled = true;
    return ceAction('clan_ech_proposer', { p_cible: clanEch.qui, p_ma: clanEch.donne, p_sa: clanEch.recoit }, () => { clanEch.donne = null; clanEch.recoit = null; }); }
  if(b.dataset.ceAccepter){ b.disabled = true; return ceAction('clan_ech_repondre', { p_id: Number(b.dataset.ceAccepter), p_accepter: true }); }
  if(b.dataset.ceRefuser){ return ceAction('clan_ech_repondre', { p_id: Number(b.dataset.ceRefuser), p_accepter: false }); }
  if(b.dataset.ceAnnuler){ return ceAction('clan_ech_annuler', { p_id: Number(b.dataset.ceAnnuler) }); }""", 'clics')
js = rempl(js, u"""if(CLANS) setTimeout(loadClansCarte, 1500);""", u"""if(CLANS) setTimeout(loadClansCarte, 1500);
if(CLANS) setTimeout(chargerClanEch, 2500);   // patch194 : la pastille des propositions recues
document.getElementById('panel-clan').addEventListener('input', (e) => {
  if(e.target.id === 'ceR1'){ clanEch.r1 = e.target.value; majListesCe(); }
  if(e.target.id === 'ceR2'){ clanEch.r2 = e.target.value; majListesCe(); }
});""", 'init')
ecrire('app.js', js)

css = lire('style.css')
assert 'patch194' not in css
css += u"""

/* ---------- patch194 : les echanges du clan ---------- */
.ce-bloc{ margin-top:18px; padding-top:14px; border-top:1px solid rgba(169,188,212,0.14); display:grid; gap:12px; }
.ce-tete{ display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; }
.ce-tete h2{ margin:0 !important; }
.ce-h3{ margin:4px 0 0; font-size:.7rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:#8297B5; }
.ce-com{ display:inline-flex; align-items:center; gap:8px; min-width:0; }
.ce-com i{ width:10px; height:10px; border-radius:3px; flex:none; }
.ce-com b{ font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.ce-com small{ color: var(--brume); font-size:.76rem; white-space:nowrap; }
.ce-prop{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:10px; align-items:center; padding:12px; border-radius:12px; background:rgba(8,19,37,.5); border:1px solid rgba(169,188,212,0.14); }
@media (max-width: 560px){ .ce-prop{ grid-template-columns:minmax(0,1fr); } }
.ce-qui{ font-size:.82rem; color: var(--brume); margin-bottom:6px; }
.ce-qui b{ color:#fff; }
.ce-troc{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.ce-fl{ color: var(--brume); }
.ce-actions{ display:flex; gap:8px; flex-wrap:wrap; }
.ce-attente{ font-size:.78rem; color: var(--brume); margin:0 0 6px; }
.ce-membres{ display:flex; gap:8px; flex-wrap:wrap; }
.ce-membre{ display:inline-flex; align-items:center; gap:8px; padding:6px 12px 6px 6px; border-radius:999px; border:1px solid rgba(169,188,212,0.14); background:rgba(8,19,37,.5); color:#fff; font:inherit; cursor:pointer; min-height:40px; }
.ce-membre .av{ width:28px; height:28px; border-radius:50%; background: var(--nuit-3); display:grid; place-items:center; font-family: var(--titre); font-weight:800; box-shadow:0 0 0 2px var(--clan); }
.ce-membre[aria-pressed="true"]{ border-color: var(--c-legendaire); background: rgba(240,180,41,.12); }
.ce-deux{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:12px; }
@media (max-width: 620px){ .ce-deux{ grid-template-columns:minmax(0,1fr); } }
.ce-recherche{ width:100%; padding:9px 12px; border-radius:9px; border:1px solid rgba(169,188,212,0.3); background: var(--nuit); color:#fff; font:inherit; }
.ce-liste{ display:grid; gap:4px; max-height:220px; overflow:auto; padding:6px; margin-top:8px; border-radius:12px; background:rgba(8,19,37,.5); border:1px solid rgba(169,188,212,0.14); }
.ce-choix{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:8px; align-items:center; text-align:left; padding:8px 10px; border-radius:9px; border:1px solid transparent; background:none; color:#fff; font:inherit; cursor:pointer; min-height:40px; }
.ce-choix:hover:not(:disabled){ background: rgba(169,188,212,.06); }
.ce-choix[aria-pressed="true"]{ border-color: var(--c-legendaire); background: rgba(240,180,41,.1); }
.ce-choix:disabled{ cursor:not-allowed; opacity:.55; }
.ce-raison{ font-size:.72rem; color: var(--brume); white-space:nowrap; }
.ce-recap{ display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; padding:12px; border-radius:12px; background: rgba(240,180,41,.08); border:1px solid rgba(240,180,41,.35); }
.ce-membre:focus-visible, .ce-choix:focus-visible{ outline:2px solid var(--c-legendaire); outline-offset:2px; }
"""
ecrire('style.css', css)
print(u'patch194 applique. Lancer : python3 maj-version.py')
