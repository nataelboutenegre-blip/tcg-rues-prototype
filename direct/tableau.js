// TerraFront · le tableau de bord (s2-139, 12/11/2026). Les chiffres du jeu (tableau_de_bord(), toutes les minutes),
// qui est en ligne (le même canal de présence que le jeu, sans s'y compter), et la régie et la carte en direct
// dans deux autres onglets. Session du jeu partagée (même navigateur) ; réservé à la modération.
'use strict';
const SUPABASE_URL = 'https://yzcgroprydxhbwaufkdu.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_s829mEa2YUPWr9DOks2FTg_k9gpTQTA';
const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const nb = (n) => Number(n || 0).toLocaleString('fr-FR');
const T = { donnees: null, pseudos: {}, enLigne: [], canal: null };

function lien(etat, txt){ $('lien').className = 'lien ' + etat; $('lienTxt').textContent = txt; }
function message(html){ document.querySelectorAll('.vue').forEach(v => v.hidden = true); $('msg').innerHTML = html; $('msg').hidden = false; }
function ilYa(t){
  const m = Math.round((Date.now() - new Date(t).getTime()) / 60000);
  if(m < 60) return `${Math.max(1, m)} min`;
  const h = Math.round(m / 60);
  if(h < 24) return `${h} h`;
  return `${Math.round(h / 24)} j`;
}
const JOURS = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
function jourCourt(d){ const x = new Date(d + 'T12:00:00'); return `${JOURS[x.getDay()]} ${x.getDate()}`; }

// ---------- les onglets ----------
function montrerVue(v){
  document.querySelectorAll('.onglet').forEach(b => b.classList.toggle('actif', b.dataset.vue === v));
  document.querySelectorAll('.vue').forEach(x => { x.hidden = x.id !== 'vue-' + v; });
  // la régie et la carte ne se chargent qu'à la première visite de leur onglet
  if(v === 'regie' && !$('vue-regie').firstChild) $('vue-regie').innerHTML = '<iframe src="regie.html" title="Régie du direct"></iframe>';
  if(v === 'carte' && !$('vue-carte').firstChild) $('vue-carte').innerHTML = '<iframe src="index.html" title="Carte en direct"></iframe>';
  try{ localStorage.setItem('tf-tableau-vue', v); }catch(e){}
}

// ---------- qui est en ligne : le canal de présence du jeu, en simple spectateur ----------
function majEnLigne(){
  const ids = T.enLigne;
  $('tEnLigne').textContent = nb(ids.length);
  $('enLigneNb').textContent = ids.length ? `${nb(ids.length)} joueur${ids.length > 1 ? 's' : ''}` : '';
  const noms = ids.map(id => T.pseudos[id] || null).filter(Boolean).sort((a, b) => a.localeCompare(b, 'fr'));
  const inconnus = ids.length - noms.length;
  $('enLigne').innerHTML = ids.length
    ? noms.map(p => `<span class="puce"><i></i>${esc(p)}</span>`).join('') + (inconnus > 0 ? `<span class="puce">+ ${inconnus} nouveau${inconnus > 1 ? 'x' : ''}</span>` : '')
    : '<span class="vide">Personne en ligne pour le moment.</span>';
}
function suivrePresence(uid){
  try{
    T.canal = sb.channel('en-ligne', { config: { presence: { key: uid } } });
    T.canal.on('presence', { event: 'sync' }, () => { T.enLigne = Object.keys(T.canal.presenceState()); majEnLigne(); });
    T.canal.subscribe();   // sans track() : le tableau ne compte pas comme un joueur
  }catch(e){ $('enLigne').innerHTML = '<span class="vide">Présence indisponible.</span>'; }
}

// ---------- les graphiques : une série, des barres, une bulle au survol ou au toucher ----------
function graphique(el, jours, idx, libelle){
  const vals = jours.map(j => Number(j[idx]) || 0), max = Math.max(1, ...vals), der = vals.length - 1;
  const iMax = vals.indexOf(Math.max(...vals));
  el.innerHTML = `<div class="graph">${vals.map((v, i) => {
      const h = Math.max(1.5, v / max * 100);
      const etiquette = (i === der || i === iMax) && v > 0 ? `<em style="bottom:calc(${h}% + 3px)">${nb(v)}</em>` : '';
      return `<div class="barre${i === der ? ' auj' : ''}" data-b="${esc(jourCourt(jours[i][0]))}|${v}|${esc(libelle)}"><i style="height:${h}%"></i>${etiquette}</div>`;
    }).join('')}</div>
    <div class="axe">${jours.map((j, i) => `<span>${i % 2 === der % 2 ? Number(String(j[0]).slice(8, 10)) : ''}</span>`).join('')}</div>`;
}
function bulle(e){
  const b = e.target.closest && e.target.closest('[data-b]'), bu = $('bulle');
  document.querySelectorAll('.barre.vue-on').forEach(x => { if(x !== b) x.classList.remove('vue-on'); });
  if(!b){ bu.hidden = true; return; }
  const [j, v, l] = b.dataset.b.split('|');
  b.classList.add('vue-on');
  bu.innerHTML = `${j} · <b>${nb(v)}</b> ${l}`;
  bu.hidden = false;
  const r = b.getBoundingClientRect(), w = bu.offsetWidth;
  bu.style.left = Math.min(window.innerWidth - w - 8, Math.max(8, r.left + r.width / 2 - w / 2)) + 'px';
  bu.style.top = Math.max(8, r.top - bu.offsetHeight - 8) + 'px';
}

// ---------- les chiffres ----------
function rendre(){
  const D = T.donnees; if(!D) return;
  const J = D.joueurs || {}, A = D.aujourdhui || {}, jours = D.jours || [];
  $('tTotal').textContent = nb(J.total);
  $('tTotalS').innerHTML = `<b>${nb(J.avec_communes)}</b> avec des communes · <b>${nb(J.en_clan)}</b> en clan`;
  $('tNouveaux').textContent = nb(J.nouveaux_jour);
  $('tNouveauxS').innerHTML = `aujourd’hui · <b>${nb(J.nouveaux_7j)}</b> sur 7 jours`;
  $('tActifs').textContent = nb(J.actifs_jour);
  $('tActifsS').innerHTML = `<b>${nb(J.actifs_7j)}</b> sur 7 jours · <b>${nb(J.actifs_30j)}</b> sur 30`;
  const jeux = (Number(A.radar) || 0) + (Number(A.rafale) || 0) + (Number(A.pom) || 0);
  const cases = [
    [A.rounds, 'rounds d’attaque', ''],
    [A.conquetes, 'conquêtes', ''],
    [A.defenses, 'défenses', `${nb(A.defenses_reussies)} réussies`],
    [(Number(A.messages) || 0) + (Number(A.messages_clans) || 0), 'messages', `${nb(A.messages)} discussion · ${nb(A.messages_clans)} clans`],
    [jeux, 'parties de mini-jeux', `Radar ${nb(A.radar)} · Rafale ${nb(A.rafale)} · ± ${nb(A.pom)}`],
    [A.echanges, 'échanges proposés', ''],
    [A.achats, 'achats en boutique', ''],
    [A.batiments, 'bâtiments lancés', ''],
  ];
  $('activite').innerHTML = cases.map(([v, l, s]) => `<div class="act"><b>${nb(v)}</b><span>${l}</span>${s ? `<small>${s}</small>` : ''}</div>`).join('');
  $('maj').textContent = 'mis à jour à ' + new Date(D.le).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  // jours = [jour, inscrits, actifs, rounds, conquêtes, défenses, messages]
  graphique($('gActifs'), jours, 2, 'joueurs actifs');
  graphique($('gInscrits'), jours, 1, 'inscrits');
  graphique($('gConquetes'), jours, 4, 'conquêtes');
  // les nouveaux restent-ils ? [lundi, inscrits, éligibles J1, revenus J1, éligibles J7, encore là J7, joué ces 7 jours]
  const co = D.cohortes || [];
  const taux = (n, e, objectif) => {
    if(!e) return '<span class="muet">trop tôt</span>';
    const p = Math.round(n / e * 100);
    const obj = objectif ? (p >= objectif ? ' <span class="ok-obj">✓ objectif</span>' : ' <span class="ko-obj">sous l’objectif</span>') : '';
    return `<div class="taux"><span class="jauge"><i style="width:${Math.min(100, p)}%"></i></span><b>${p} %</b><small>${nb(n)} / ${nb(e)}</small></div>${obj}`;
  };
  const semaine = (d) => { const x = new Date(d + 'T12:00:00'); return 'du ' + x.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }); };
  $('cohortes').innerHTML = co.length ? `<table><thead><tr><th>Semaine</th><th class="n">Inscrits</th><th class="n">Revenus le lendemain</th><th class="n">Encore là après 7 jours</th><th class="n">Ont joué ces 7 jours</th></tr></thead><tbody>${
    co.slice().reverse().map(c => `<tr><td>${semaine(c[0])}</td><td class="n">${nb(c[1])}</td><td class="n">${taux(c[3], c[2])}</td><td class="n">${taux(c[5], c[4], 20)}</td><td class="n">${nb(c[6])}</td></tr>`).join('')}</tbody></table>`
    : '<span class="vide">Pas encore de données.</span>';
  const top = D.top_jour || [];
  $('top').innerHTML = top.length ? `<table><thead><tr><th>Joueur</th><th class="n">Rounds</th><th class="n">Conquêtes</th></tr></thead><tbody>${
    top.map(t => `<tr><td>${esc(t[1])}</td><td class="n">${nb(t[2])}</td><td class="n">${nb(t[3])}</td></tr>`).join('')}</tbody></table>`
    : '<span class="vide">Pas encore d’attaque aujourd’hui.</span>';
  const der = D.derniers || [];
  $('derniers').innerHTML = der.length ? `<table><thead><tr><th>Joueur</th><th>Il y a</th><th class="n">Jours joués</th><th class="n">Communes</th></tr></thead><tbody>${
    der.map(d => `<tr><td>${esc(d[1])}</td><td><span class="muet">${ilYa(d[2])}</span></td><td class="n">${nb(d[3])}</td><td class="n">${nb(d[4])}</td></tr>`).join('')}</tbody></table>`
    : '<span class="vide">Aucun.</span>';
}
async function charger(){
  try{
    const { data, error } = await sb.rpc('tableau_de_bord');
    if(error || !data){ lien('ko', error && /Réservé/.test(error.message) ? 'Accès refusé' : 'Hors ligne'); return false; }
    T.donnees = data; T.pseudos = data.pseudos || {};
    lien('ok', 'À jour');
    rendre(); majEnLigne();
    return true;
  }catch(e){ lien('ko', 'Hors ligne'); return false; }
}

// ---------- départ ----------
(async function demarrer(){
  document.querySelector('.onglets').addEventListener('click', (e) => { const b = e.target.closest('[data-vue]'); if(b) montrerVue(b.dataset.vue); });
  document.addEventListener('pointerover', bulle);
  document.addEventListener('pointerdown', bulle);
  const { data: s } = await sb.auth.getSession();
  if(!s || !s.session){
    lien('ko', 'Non connecté');
    message('Connecte-toi d’abord au jeu <b>dans ce navigateur</b> : <a href="../">ouvrir terrafront.fr</a>, puis reviens sur cette page.'
      + '<br><br><small>Sur iPhone, l’appli posée sur l’écran d’accueil ne partage pas sa connexion avec Safari.</small>');
    return;
  }
  const { data: ok, error } = await sb.rpc('direct_regie_ok');
  if(error || ok !== true){ lien('ko', 'Accès refusé'); message('Cette page est réservée à l’administration du jeu.'); return; }
  let vue = 'stats'; try{ vue = localStorage.getItem('tf-tableau-vue') || 'stats'; }catch(e){}
  montrerVue(['stats', 'regie', 'carte'].includes(vue) ? vue : 'stats');
  lien('', 'Chargement…');
  await charger();
  suivrePresence(s.session.user.id);
  setInterval(() => { if(!document.hidden) charger(); }, 60000);
  document.addEventListener('visibilitychange', () => { if(!document.hidden) charger(); });
})();
