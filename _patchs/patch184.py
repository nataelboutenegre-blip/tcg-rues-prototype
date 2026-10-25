# -*- coding: utf-8 -*-
u"""
patch184 — l'onglet Clan (idées de Maroli, 25 octobre) :
- sous chaque membre, ce qu'il a fait aujourd'hui : cartes obtenues,
  communes conquises, défenses, énergie dépensée ; « absent depuis N jours »
  pour un membre qui n'a pas ouvert le jeu depuis plus de 6 jours ;
- en haut, le total du clan pour la journée ;
- le classement et la moyenne ne comptent que les membres actifs (jeu ouvert
  dans les 7 derniers jours).
Demande _sql/s2-26-clans-activite.sql (sans lui : pas de bloc d'activité,
moyenne comme avant).
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
js = lire('app.js'); css = lire('style.css')
assert 'patch184' not in js

js = rempl(js, u"""  const [mc, cl, cf] = await Promise.all([sb.rpc('mon_clan'), sb.rpc('clans_classement'), sb.rpc('clans_en_formation')]);
  if(mc.error){ zone.innerHTML = `<p class="collection-empty">${echapperTexte(messageLisible(mc.error.message))}</p>`; return; }
  clanCache = { moi: mc.data || {}, classement: cl.error ? [] : (cl.data || []), formation: cf.error ? [] : (cf.data || []) };""",
u"""  const [mc, cl, cf, ac] = await Promise.all([sb.rpc('mon_clan'), sb.rpc('clans_classement'), sb.rpc('clans_en_formation'),
    sb.rpc('clan_activite').then(r => r, () => ({ error: true }))]);   // patch184
  if(mc.error){ zone.innerHTML = `<p class="collection-empty">${echapperTexte(messageLisible(mc.error.message))}</p>`; return; }
  clanCache = { moi: mc.data || {}, classement: cl.error ? [] : (cl.data || []), formation: cf.error ? [] : (cf.data || []),
                activite: ac.error ? null : new Map((ac.data || []).map(a => [a.joueur_id, a])) };""", 'load')

js = rempl(js, u"""function renderClan(){
  const zone = document.getElementById('clanZone');""",
u"""// patch184 : l'activite du jour d'un membre, et depuis quand il n'a pas joue
const CLAN_ACTIF_JOURS = 7;
function joursDepuis(jour){
  if(!jour) return null;
  const auj = new Date().toLocaleDateString('en-CA', { timeZone: 'Europe/Paris' });   // AAAA-MM-JJ
  const jj = (s) => { const [a, m, d] = String(s).slice(0, 10).split('-').map(Number); return Date.UTC(a, m - 1, d); };
  return Math.max(0, Math.round((jj(auj) - jj(jour)) / 86400000));
}
function membreActif(a){ const j = a ? joursDepuis(a.dernier_jour) : null; return j !== null && j < CLAN_ACTIF_JOURS; }
function activiteClanHtml(a){
  if(!a) return '';
  const j = joursDepuis(a.dernier_jour);
  if(j === null || j >= CLAN_ACTIF_JOURS)
    return `<div class="clan-act absent">${j === null ? 'Pas encore joué' : `Absent depuis ${j} jours`} · ne compte pas dans la moyenne</div>`;
  const vals = [[a.cartes, 'carte', 'cartes'], [a.conquetes, 'conquête', 'conquêtes'], [a.defenses, 'défense', 'défenses'], [a.energie, 'énergie', 'énergie']];
  if(!vals.some(v => v[0] > 0)) return `<div class="clan-act calme">${j === 0 ? 'Passé aujourd\\'hui, rien de joué encore' : j === 1 ? 'Vu hier' : `Vu il y a ${j} jours`}</div>`;
  return `<div class="clan-act">${vals.map(([n, un, plus]) => `<span class="${n > 0 ? '' : 'zero'}"><b>${nbClan(n)}</b> ${n > 1 ? plus : un}</span>`).join('')}</div>`;
}
function renderClan(){
  const zone = document.getElementById('clanZone');""", 'fonctions')

js = rempl(js, u"""<span class="cl-score">${nbClan(x.moyenne)}<small>par membre</small></span></div>`).join('')""",
u"""<span class="cl-score">${nbClan(x.moyenne)}<small>${x.actifs != null ? 'par membre actif' : 'par membre'}</small></span></div>`).join('')""", 'classement')
js = rempl(js, u"""    <p class="clan-note">À la moyenne de communes du Front par membre, jamais au total : un gros clan n'a pas d'avantage.</p>${blocFormation}</div>`;""",
u"""    <p class="clan-note">À la moyenne de communes du Front par membre actif (jeu ouvert dans les 7 derniers jours), jamais au total : un gros clan n'a pas d'avantage, et un membre absent ne fait pas baisser son clan.</p>${blocFormation}</div>`;""", 'note')

js = rempl(js, u"""    const membres = (c.membres || []).map(m => `<div class="clan-membre"><span class="av" style="--clan:${c.couleur}">${echapperTexte((m.pseudo || '?')[0].toUpperCase())}</span>
        <div><b>${echapperTexte(m.pseudo)}</b><small>${m.chef ? 'Chef' : 'Membre'}${m.moi ? ' · toi' : ''}</small></div>
        <span class="clan-nb">${nbClan(m.communes)} communes</span>
        ${c.chef && !m.moi ? `<button class="bq-btn secondaire" data-clan-exclure="${m.id}">Exclure</button>` : '<span></span>'}</div>`).join('');
    const total = (c.membres || []).reduce((s, m) => s + (m.communes || 0), 0);
    const n = (c.membres || []).length;""",
u"""    const act = clanCache.activite;   // patch184 : null si le SQL n'est pas passe
    const membres = (c.membres || []).map(m => `<div class="clan-membre"><span class="av" style="--clan:${c.couleur}">${echapperTexte((m.pseudo || '?')[0].toUpperCase())}</span>
        <div><b>${echapperTexte(m.pseudo)}</b><small>${m.chef ? 'Chef' : 'Membre'}${m.moi ? ' · toi' : ''}</small></div>
        <span class="clan-nb">${nbClan(m.communes)} communes</span>
        ${c.chef && !m.moi ? `<button class="bq-btn secondaire" data-clan-exclure="${m.id}">Exclure</button>` : '<span></span>'}
        ${act ? activiteClanHtml(act.get(m.id)) : ''}</div>`).join('');
    const total = (c.membres || []).reduce((s, m) => s + (m.communes || 0), 0);
    const n = (c.membres || []).length;
    const actifs = act ? (c.membres || []).filter(m => membreActif(act.get(m.id))) : null;
    const moyenne = actifs ? (actifs.length ? Math.round(actifs.reduce((s, m) => s + (m.communes || 0), 0) / actifs.length) : 0)
                           : (n ? Math.round(total / n) : 0);
    const somme = (k) => [...(act ? act.values() : [])].reduce((s, a) => s + (a[k] || 0), 0);
    const blocJour = act ? `<div class="clan-jour"><span class="clan-jour-t">Le clan aujourd'hui</span>
        <span><b>${nbClan(somme('cartes'))}</b> cartes</span><span><b>${nbClan(somme('conquetes'))}</b> conquêtes</span>
        <span><b>${nbClan(somme('defenses'))}</b> défenses</span><span><b>${nbClan(somme('energie'))}</b> énergie</span></div>` : '';""", 'membres')

js = rempl(js, u"""<span class="puce">Moyenne par membre <b>${nbClan(n ? Math.round(total / n) : 0)}</b></span>""",
u"""<span class="puce">Moyenne par membre${actifs ? ' actif' : ''} <b>${nbClan(moyenne)}</b></span>${actifs ? `<span class="puce">Actifs <b>${actifs.length}</b> sur ${n}</span>` : ''}""", 'puces')
js = rempl(js, u"""      <h2>Membres</h2>${membres}""", u"""      ${blocJour}
      <h2>Membres</h2>${membres}""", 'bloc jour')

css += u"""
/* patch184 : l'activite du jour dans l'onglet Clan */
.clan-act{ grid-column: 2 / -1; margin-top:-4px; display:flex; flex-wrap:wrap; gap:4px 12px; font-size:.76rem; color: var(--brume); }
.clan-act span b{ color:#fff; font-weight:700; }
.clan-act span.zero{ opacity:.45; }
.clan-act.absent{ color:#E8907A; }
.clan-act.calme{ font-style:italic; }
.clan-jour{ display:flex; flex-wrap:wrap; align-items:baseline; gap:6px 16px; margin:14px 0 2px; padding:10px 12px; border-radius:10px;
  background: rgba(240,180,41,.07); border:1px solid rgba(240,180,41,.18); font-size:.84rem; color: var(--brume); }
.clan-jour b{ color: var(--c-legendaire); font-family: var(--titre); font-weight:800; font-size:1.05rem; }
.clan-jour-t{ width:100%; font-size:.68rem; letter-spacing:.08em; text-transform:uppercase; color: var(--brume); }
"""
ecrire('app.js', js); ecrire('style.css', css)
print(u'patch184 appliqué')
