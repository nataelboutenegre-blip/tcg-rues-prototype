# patch307 : postuler dans un clan depuis le jeu (s2-75)
# - Sans clan : en dépliant un clan (classement ou « en formation »), un mot facultatif
#   et « Postuler » ; ensuite « Candidature envoyée · Retirer ». Sous le nom de chaque
#   clan : « Recrute · n / 8 », « Complet » ou « Ne recrute pas ».
# - Chef (et bras droit qui peut inviter) : bloc « Candidatures » (Accepter / Refuser)
#   et « Recrutement ouvert / fermé ». Les candidatures en attente s'ajoutent à la
#   pastille de l'onglet Clan.
# - Le candidat est prévenu (notification) quand sa candidature est acceptée ou refusée.
# Sans s2-75, rien ne s'affiche et rien ne change.
import json, pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch307' not in s

# ---- l'état, les morceaux d'écran
s = rep(s, """async function loadClan(){
  const zone = document.getElementById('clanZone');""",
"""// ---------- patch307 : candidatures de clan (s2-75) ----------
var CAND = null;   // null tant que s2-75 n'est pas passé (var : lue par la pastille, peut-être avant cette ligne)
async function chargerCandidatures(){
  if(!CLANS) return;
  try{
    const { data, error } = await sb.rpc('clan_candidatures_etat');
    CAND = !error && data ? data : null;
  }catch(e){ CAND = null; }
  candPrevenir();
  majBadgeClanTotal();
}
// le candidat apprend la réponse une fois (acceptée ou refusée)
function candPrevenir(){
  if(!CAND) return;
  let vus = [];
  try{ vus = JSON.parse(localStorage.getItem('tf-cand-vues') || '[]'); }catch(e){}
  let change = false;
  for(const k of CAND.mes || []){
    if(k.statut === 'attente' || !k.decide_le) continue;
    const cle = k.clan_id + '|' + k.decide_le;
    if(vus.includes(cle)) continue;
    vus.push(cle); change = true;
    if(k.statut === 'acceptee') notifier({ type: 'succes', titre: 'Candidature acceptée', texte: `Bienvenue chez ${k.nom} !` });
    else notifier({ type: 'info', titre: 'Candidature refusée', texte: `${k.nom} n’a pas retenu ta candidature. D’autres clans recrutent : jette un œil au classement.` });
  }
  if(change){ try{ localStorage.setItem('tf-cand-vues', JSON.stringify(vus.slice(-30))); }catch(e){} }
}
const candEnAttente = (id) => CAND && (CAND.mes || []).find(k => k.clan_id === id && k.statut === 'attente');
const candRefusee = (id) => CAND && (CAND.mes || []).find(k => k.clan_id === id && k.statut === 'refusee');
const candFerme = (id) => !!(CAND && (CAND.fermes || []).includes(id));
function candEtiquette(x){
  if(!CAND) return '';
  const n = Number(x.membres) || 0;
  if(n >= 8) return '<small class="cl-rec ferme">Complet · 8 / 8</small>';
  if(candFerme(x.clan_id)) return '<small class="cl-rec ferme">Ne recrute pas</small>';
  if(candEnAttente(x.clan_id)) return '<small class="cl-rec">Candidature envoyée</small>';
  return `<small class="cl-rec">Recrute · ${n} / 8</small>`;
}
function candPostulerHtml(x){
  if(!CAND || !clanCache || !clanCache.moi || clanCache.moi.clan) return '';
  const note = (t) => `<div class="cl-postuler"><p class="clan-note">${t}</p></div>`;
  if(clanCache.moi.attente_jusqua) return note('Tu as quitté un clan il y a moins de 48 h : tu pourras postuler ensuite.');
  if((Number(x.membres) || 0) >= 8) return note('Ce clan est complet (8 membres).');
  if(candFerme(x.clan_id)) return note('Ce clan ne recrute pas en ce moment.');
  if(candEnAttente(x.clan_id)) return `<div class="cl-postuler"><div class="cl-envoyee"><span>✓ Candidature envoyée · en attente du chef</span><button type="button" class="bq-btn secondaire" data-cand-retirer="${echapperTexte(x.clan_id)}">Retirer</button></div></div>`;
  if(candRefusee(x.clan_id)) return note('Ce clan a refusé ta candidature. Tu pourras réessayer dans quelques jours.');
  return `<div class="cl-postuler"><textarea id="candMsg-${echapperTexte(x.clan_id)}" maxlength="140" rows="2" placeholder="Un mot pour le chef (facultatif) : ta région, quand tu joues…"></textarea>
    <div class="cl-postuler-l"><small>Le chef ou un bras droit te répond</small><button type="button" class="bq-btn" data-cand-postuler="${echapperTexte(x.clan_id)}">Postuler</button></div></div>`;
}
function candIlYa(d){
  const m = Math.max(0, Math.round((Date.now() - new Date(d).getTime()) / 60000));
  return m < 60 ? `il y a ${Math.max(1, m)} min` : m < 1440 ? `il y a ${Math.round(m / 60)} h` : `il y a ${Math.round(m / 1440)} j`;
}
function candGererHtml(c){
  if(!CAND || !CAND.gere) return '';
  const R = CAND.recues || [];
  const lignes = R.map(k => {
    const jours = k.inscrit_le ? Math.floor((Date.now() - new Date(k.inscrit_le).getTime()) / 86400000) : null;
    const anc = jours === null ? '' : jours < 1 ? 'arrivé aujourd’hui' : jours < 14 ? `joue depuis ${jours} jour${jours > 1 ? 's' : ''}` : `joue depuis ${Math.round(jours / 7)} semaines`;
    return `<div class="clan-cand"><div class="clan-cand-h"><span class="av" style="--clan:${c.couleur}">${echapperTexte((k.pseudo || '?')[0].toUpperCase())}</span>
        <div><button type="button" class="cl-mb-pseudo" data-clan-profil="${echapperTexte(k.joueur_id)}">${echapperTexte(k.pseudo || 'Joueur')}</button>
        <small>${nbClan(k.communes)} commune${k.communes > 1 ? 's' : ''} au Front${anc ? ' · ' + anc : ''} · ${candIlYa(k.le)}</small></div></div>
      ${k.message ? `<p class="clan-cand-msg">« ${echapperTexte(k.message)} »</p>` : ''}
      <div class="clan-cand-b"><button type="button" class="bq-btn" data-cand-oui="${echapperTexte(k.joueur_id)}">Accepter</button><button type="button" class="bq-btn secondaire" data-cand-non="${echapperTexte(k.joueur_id)}">Refuser</button></div></div>`;
  }).join('');
  const plein = (c.membres || []).length >= 8;
  return `<h2>Candidatures${R.length ? ` <span class="cand-pastille">${R.length}</span>` : ''}</h2>
    ${lignes || `<p class="clan-note">Aucune candidature en attente.${CAND.recrute ? ' Les joueurs sans clan peuvent postuler depuis le classement.' : ''}</p>`}
    ${plein && R.length ? '<p class="clan-note">Ton clan est complet : libère une place pour accepter quelqu’un.</p>' : ''}
    <div class="cl-recrute"><span>Recrutement ${CAND.recrute ? 'ouvert' : 'fermé'}<small>${CAND.recrute ? 'Ferme-le pour ne plus recevoir de candidatures' : 'Personne ne peut postuler'} (les invitations marchent toujours)</small></span>
      <button type="button" class="filter-pill${CAND.recrute ? ' active' : ''}" aria-pressed="${!!CAND.recrute}" data-cand-recrute="${CAND.recrute ? '0' : '1'}">${CAND.recrute ? '✓ Ouvert' : 'Fermé'}</button></div>`;
}

async function loadClan(){
  const zone = document.getElementById('clanZone');""")

# loadClan : l'état des candidatures avant le rendu
s = rep(s, """  if(SAISON2) await chargerClanEch();   // patch194
  clanCache = { moi: mc.data || {},""",
"""  if(SAISON2) await chargerClanEch();   // patch194
  await chargerCandidatures();   // patch307
  clanCache = { moi: mc.data || {},""")

# classement : étiquette sous le nom, et Postuler sous les membres
s = rep(s, """<span class="cl-nom">${echapperTexte(x.nom)}</span><span class="cl-score">${nbClan(x.moyenne)}""",
           """<span class="cl-nom">${echapperTexte(x.nom)}${!c ? candEtiquette(x) : ''}</span><span class="cl-score">${nbClan(x.moyenne)}""")
s = rep(s, """${CHEVRON_CLAN}</button>${clansOuverts.has(x.clan_id) ? membresClanHtml(x) : ''}</div>`).join('') + '<p class="clan-note">Touche un clan pour voir ses membres.</p>'""",
           """${CHEVRON_CLAN}</button>${clansOuverts.has(x.clan_id) ? membresClanHtml(x) + candPostulerHtml(x) : ''}</div>`).join('') + `<p class="clan-note">${!c && CAND ? 'Touche un clan pour voir ses membres et postuler. 3 candidatures en attente au plus ; sans réponse, elles expirent au bout de 3 jours.' : 'Touche un clan pour voir ses membres.'}</p>`""")
# en formation
s = rep(s, """<span class="cl-nom">${echapperTexte(x.nom)}<small>${x.chef ? 'chef : ' + echapperTexte(x.chef) : ''}</small></span>""",
           """<span class="cl-nom">${echapperTexte(x.nom)}<small>${x.chef ? 'chef : ' + echapperTexte(x.chef) : ''}</small>${!c ? candEtiquette(x) : ''}</span>""")
s = rep(s, """${clansOuverts.has(x.clan_id) ? membresClanHtml(x, x.chef || 'son chef') : ''}</div>`).join('')}""",
           """${clansOuverts.has(x.clan_id) ? membresClanHtml(x, x.chef || 'son chef') + candPostulerHtml(x) : ''}</div>`).join('')}""")
s = rep(s, """<p class="clan-note">Pour en rejoindre un, demande une invitation à son chef (sur le Discord, salon recrutement-clans). Il sera classé à partir de 3 membres.</p>""",
           """<p class="clan-note">${CAND ? 'Pour en rejoindre un, déplie-le et postule, ou demande une invitation à son chef.' : 'Pour en rejoindre un, demande une invitation à son chef (sur le Discord, salon recrutement-clans).'} Il sera classé à partir de 3 membres.</p>""")
# chef : le bloc Candidatures, sous « Le clan aujourd'hui »
s = rep(s, """      ${blocJour}
""", """      ${blocJour}
      ${candGererHtml(c)}   <!-- patch307 -->
""")
# les clics
s = rep(s, """  if(b.dataset.clanOui) return actionClan('clan_repondre', { p_clan: b.dataset.clanOui, p_accepter: true }, 'Bienvenue dans le clan');""",
"""  // patch307 : candidatures
  if(b.dataset.candPostuler){
    const id = b.dataset.candPostuler, t = document.getElementById('candMsg-' + id);
    b.disabled = true;
    return actionClan('clan_postuler', { p_clan: id, p_message: t ? t.value : '' }, 'Candidature envoyée').then(ok => { if(!ok) b.disabled = false; });
  }
  if(b.dataset.candRetirer) return actionClan('clan_candidature_retirer', { p_clan: b.dataset.candRetirer }, 'Candidature retirée');
  if(b.dataset.candOui){ b.disabled = true; return actionClan('clan_candidature_repondre', { p_joueur: b.dataset.candOui, p_accepter: true }, 'Nouveau membre dans le clan'); }
  if(b.dataset.candNon){ b.disabled = true; return actionClan('clan_candidature_repondre', { p_joueur: b.dataset.candNon, p_accepter: false }, 'Candidature refusée'); }
  if(b.dataset.candRecrute) return actionClan('clan_recrutement', { p_ouvert: b.dataset.candRecrute === '1' }, b.dataset.candRecrute === '1' ? 'Recrutement ouvert' : 'Recrutement fermé');
  if(b.dataset.clanOui) return actionClan('clan_repondre', { p_clan: b.dataset.clanOui, p_accepter: true }, 'Bienvenue dans le clan');""")
# la pastille de l'onglet Clan : + les candidatures reçues
s = rep(s, """  const n = (Number(tchat.nonLus) || 0) + (clanEch.etat && Array.isArray(clanEch.etat.recus) ? clanEch.etat.recus.length : 0);""",
           """  const n = (Number(tchat.nonLus) || 0) + (clanEch.etat && Array.isArray(clanEch.etat.recus) ? clanEch.etat.recus.length : 0)
    + (CAND && Array.isArray(CAND.recues) ? CAND.recues.length : 0);   // patch307""")
# au démarrage, puis toutes les 5 minutes
s = rep(s, """  chargerPremiersPas();   // patch306
""", """  chargerPremiersPas();   // patch306
  chargerCandidatures(); setInterval(siVisible(chargerCandidatures), 300000);   // patch307
""")
# patch306 : var plutôt que let (lu par loadPackStatus, peut-être avant la fin du chargement du script)
s = rep(s, "let PREMIERS_PAS = null, ppMinuteur = null;", "var PREMIERS_PAS = null, ppMinuteur = null;   // patch307 : var")
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- style.css
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch307' not in s
s = s.rstrip('\n') + """

/* patch307 : candidatures de clan */
.cl-nom small.cl-rec{ display:block; font-size:.68rem; font-weight:700; color:#5BE3A6; margin-top:2px; }
.cl-nom small.cl-rec.ferme{ color:#7B8FAB; }
.cl-postuler{ padding:10px 12px 12px; border-top:1px solid rgba(169,188,212,.12); background:rgba(10,22,40,.3); }
.cl-postuler .clan-note{ margin:0; }
.cl-postuler textarea{ width:100%; box-sizing:border-box; font:inherit; font-size:.82rem; color:#fff; background:rgba(10,22,40,.55); border:1px solid rgba(169,188,212,.25); border-radius:9px; padding:8px 10px; resize:none; height:54px; }
.cl-postuler textarea::placeholder{ color:#7B8FAB; }
.cl-postuler-l{ display:flex; align-items:center; justify-content:space-between; gap:10px; margin-top:8px; }
.cl-postuler-l small{ font-size:.7rem; color:#7B8FAB; }
.cl-envoyee{ display:flex; align-items:center; justify-content:space-between; gap:10px; font-size:.78rem; color:#5BE3A6; }
.cl-envoyee .bq-btn{ font-size:.74rem; padding:6px 12px; }
.clan-cand{ padding:10px 0; border-top:1px solid rgba(169,188,212,.1); }
.clan-cand-h{ display:grid; grid-template-columns:34px minmax(0,1fr); gap:10px; align-items:center; }
.clan-cand-h .av{ width:34px; height:34px; border-radius:50%; display:grid; place-items:center; font-weight:800; color:#fff; background:var(--clan); }
.clan-cand-h small{ display:block; color:var(--brume,#A9BCD4); font-size:.74rem; margin-top:2px; }
.clan-cand-msg{ margin:8px 0 0 44px; font-size:.8rem; color:#DCE6F2; background:rgba(10,22,40,.45); border-radius:9px; padding:7px 10px; font-style:italic; overflow-wrap:anywhere; }
.clan-cand-b{ display:flex; gap:8px; margin:8px 0 0 44px; }
.clan-cand-b .bq-btn{ font-size:.78rem; padding:7px 14px; }
.cand-pastille{ display:inline-grid; place-items:center; min-width:18px; height:18px; padding:0 5px; margin-left:6px; border-radius:999px; background:#E5484D; color:#fff; font-size:.68rem; font-weight:800; vertical-align:2px; font-family:inherit; }
.cl-recrute{ display:flex; align-items:center; justify-content:space-between; gap:10px; margin:10px 0 4px; font-size:.8rem; color:#DCE6F2; }
.cl-recrute small{ display:block; font-size:.7rem; color:#7B8FAB; }
.cl-recrute .filter-pill{ white-space:nowrap; }
"""
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- nouveautés
f = pathlib.Path('data/nouveautes.json'); d = json.loads(f.read_text(encoding='utf-8'))
e = next(x for x in d if x['date'] == '2026-11-02')
e['nouveautes'].insert(0, '🛡 Clans : tu peux postuler directement depuis le jeu (déplie un clan dans le classement) ; les chefs acceptent ou refusent dans l’onglet Clan')
f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch307 appliqué')
