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
const T = { donnees: null, pseudos: {}, enLigne: [], canal: null, front: null, frontLu: 0 };

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
  if(v === 'front' && Date.now() - T.frontLu > 25000) chargerFront();   // s3-47
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
  const vals = jours.map(j => Math.round(Number(j[idx]) || 0)), max = Math.max(1, ...vals), der = vals.length - 1;
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

// ---------- s3-47 : l'onglet Front (sièges en cours, coût d'une conquête, énergie) ----------
const RARETES = { commun: 'Commune', peucommun: 'Peu commune', rare: 'Rare', epique: 'Épique', legendaire: 'Légendaire' };
const heure = (t) => new Date(t).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
function dans(t){
  const m = Math.round((new Date(t).getTime() - Date.now()) / 60000);
  if(m <= 0) return 'maintenant';
  if(m < 60) return `dans ${m} min`;
  const h = Math.floor(m / 60), r = m % 60;
  return `dans ${h} h${r ? ' ' + String(r).padStart(2, '0') : ''}`;
}
function quand(t){
  const d = new Date(t), auj = new Date();
  const jour = d.toDateString() === auj.toDateString() ? '' : (d.getTime() - auj.getTime() < 2 * 86400000 ? 'demain ' : d.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric' }) + ' ');
  return jour + heure(t);
}
function rendreFront(){
  const F = T.front; if(!F) return;
  const R = F.reglages || {}, max = Number(R.max) || 120, sg = F.en_cours || [], fins = F.fins || {}, jours = F.jours || [], auj = jours[jours.length - 1] || [];
  const longs = sg.filter(s => s[8]).length, defendus = sg.filter(s => s[9]).length, att = new Set(sg.map(s => s[4])).size;
  $('fEnCours').textContent = nb(sg.length);
  $('fEnCoursS').innerHTML = sg.length ? `<b>${nb(longs)}</b> longs · <b>${nb(defendus)}</b> défendus · <b>${nb(att)}</b> attaquants` : 'aucun en ce moment';
  $('fConq').textContent = nb(fins.conquise);
  const autres = Object.entries(fins).filter(([k]) => k !== 'conquise' && k !== 'en_cours').reduce((a, [, v]) => a + Number(v), 0);
  $('fConqS').innerHTML = `depuis le début de la saison · <b>${nb(autres)}</b> sans prise`;
  $('fDep').textContent = nb(auj[1]);
  $('fDepS').innerHTML = `aujourd’hui · <b>${nb(auj[2])}</b> joueurs · médiane <b>${nb(Math.round(auj[4] || 0))}</b>`;
  const st = F.stock || {};
  $('fStock').innerHTML = `${nb(st.moyenne)}<small style="font-size:18px;color:var(--brume)"> / ${nb(max)}</small>`;
  $('fStockS').innerHTML = `en moyenne, actifs du jour · <b>${nb(st.pleins)}</b> au plein · <b>${nb(st.bas)}</b> sous 20`;
  $('fMaj').textContent = 'mis à jour à ' + heure(F.le);
  // les sièges en cours : [id, code, nom, tier, attaquant, défenseur, dégâts, résistance, long, défendu, mise, défense, créé, dernière vague, tombe le, au plus tôt, garnison]
  $('fSieges').innerHTML = sg.length ? sg.map(s => {
    const p = s[7] ? Math.min(100, Math.round(s[6] / s[7] * 100)) : 0;
    const tot = s[15] && new Date(s[15]).getTime() > Date.now() ? `<b>au plus tôt ${quand(s[15])}</b>` : (s[8] ? '<b>peut tomber maintenant</b>' : '');
    return `<div class="sg">
      <div class="sg-nom"><b>${esc(s[2] || s[1])}</b><span class="rar ${esc(s[3])}">${esc(RARETES[s[3]] || s[3])}</span>${s[8] ? '<span class="tag long">long</span>' : ''}${s[9] ? '<span class="tag def">défendu</span>' : ''}${s[16] ? '<span class="tag gar">garnison</span>' : ''}
        <small>commencé à ${heure(s[12])} · dernière vague ${ilYa(s[13])}</small></div>
      <div class="sg-qui">${esc(s[4] || '?')} <span>→</span> ${esc(s[5] || 'libre')}<small>⚡ ${nb(s[10])} mise${s[11] ? ` · 🛡 ${nb(s[11])} en défense` : ''}</small></div>
      <div class="avance"><span class="jauge"><i class="${p >= 100 ? 'plein' : ''}" style="width:${p}%"></i></span><b>${nb(s[6])} / ${nb(s[7])}</b></div>
      <div class="sg-fin">${tot}<small>tombe ${dans(s[14])} sans vague</small></div></div>`;
  }).join('') : '<span class="vide">Aucun siège en cours.</span>';
  // le coût d'une conquête : [rareté, sièges, conquises, en cours, autres fins, moyenne, médiane, min, max, minutes médianes, défense moyenne]
  const res = R.resistance || {};
  $('fDepuis').textContent = F.debut ? 'depuis le ' + new Date(F.debut).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' }) + ' à ' + heure(F.debut) : '';
  const duree = (m) => m == null ? '—' : m < 1 ? 'aussitôt' : m < 60 ? `${Math.round(m)} min` : `${Math.floor(m / 60)} h ${String(Math.round(m % 60)).padStart(2, '0')}`;
  const pr = F.par_rarete || [];
  $('fCout').innerHTML = pr.length ? `<table><thead><tr><th>Rareté</th><th class="n cache-tel">Résistance</th><th class="n">Conquises</th><th class="n">Énergie moy.</th><th class="n cache-tel">Médiane · écart</th><th class="n">Durée</th><th class="n cache-tel">En cours</th></tr></thead><tbody>${
    pr.map(x => `<tr><td><span class="rar ${esc(x[0])}" style="margin-left:0">${esc(RARETES[x[0]] || x[0])}</span></td><td class="n cache-tel">${nb(res[x[0]])}</td><td class="n">${nb(x[2])}<span class="muet"> / ${nb(x[1])}</span></td>
      <td class="n">${x[5] == null ? '<span class="muet">pas encore</span>' : `<b>⚡ ${String(x[5]).replace('.', ',')}</b>`}</td>
      <td class="n cache-tel">${x[6] == null ? '' : `${nb(x[6])} <span class="muet">· ${nb(x[7])} à ${nb(x[8])}</span>`}</td><td class="n">${duree(x[9])}</td><td class="n cache-tel">${nb(x[3])}</td></tr>`).join('')}</tbody></table>`
    : '<span class="vide">Pas encore de siège.</span>';
  // 14 jours : [jour, dépensée, joueurs, moyenne, médiane, vagues, conquêtes]
  graphique($('gfDep'), jours, 1, 'énergie dépensée');
  graphique($('gfMoy'), jours, 3, 'énergie par joueur');
  graphique($('gfVag'), jours, 5, 'vagues de siège');
  // les gains du jour, par source
  const G = F.gains || {};
  const NOMS = [['quetes', 'Quêtes'], ['roue', 'Roue'], ['recolte', 'Récolte'], ['centrale', 'Centrale du clan'], ['objectif', 'Objectif du clan'], ['mess', 'Mess'], ['sieges_rendue', 'Rendue (sièges)'], ['parrainage', 'Parrainage'], ['remboursements', 'Remboursements']];
  const lignes = NOMS.map(([k, l]) => [l, Number(G[k]) || 0]).sort((a, b) => b[1] - a[1]);
  const gmax = Math.max(1, ...lignes.map(x => x[1])), total = lignes.reduce((a, x) => a + x[1], 0);
  $('fGainsT').textContent = nb(total) + ' en tout';
  $('fGains').innerHTML = `<div class="gains">${lignes.map(([l, v]) => `<div class="gl"><span>${l}</span><span class="jauge"><i style="width:${v / gmax * 100}%"></i></span><b>${v ? nb(v) : '<span class="muet">0</span>'}</b></div>`).join('')}</div>`;
  const parJour = Math.round(86400 / (Number(R.recharge_s) || 420));
  $('fRecharge').innerHTML = `En plus, la <b>recharge</b> : 1 toutes les ${Math.round((Number(R.recharge_s) || 420) / 60)} min, soit ${nb(parJour)} par jour au plus. Elle s’arrête à ${nb(max)} : un joueur au plein ne recharge plus (les gains peuvent monter jusqu’à ${nb(R.plafond)}).`;
  // les joueurs du jour : [pseudo, dépensée, vagues, conquêtes, réserve, sièges en cours, garnisons]
  const js = F.joueurs || [];
  $('fJoueurs').innerHTML = js.length ? `<table><thead><tr><th>Joueur</th><th class="n">Dépensée</th><th class="n">Vagues</th><th class="n cache-tel">Sièges</th><th class="n">Réserve</th></tr></thead><tbody>${
    js.map(j => { const e = Number(j[4]) || 0, cl = e >= max ? 'plein' : e < 20 ? 'bas' : '';
      return `<tr><td>${esc(j[0])}</td><td class="n">${nb(j[1])}</td><td class="n">${nb(j[2])}</td><td class="n cache-tel">${j[5] ? nb(j[5]) : '<span class="muet">–</span>'}</td>
        <td class="n"><div class="res"><span class="jauge"><i class="${cl}" style="width:${Math.min(100, e / max * 100)}%"></i></span><b>${nb(e)}</b></div></td></tr>`; }).join('')}</tbody></table>`
    : '<span class="vide">Personne n’a joué aujourd’hui.</span>';
}
async function chargerFront(){
  try{
    const { data, error } = await sb.rpc('tableau_front');
    if(error || !data){
      $('fSieges').innerHTML = `<span class="vide">${error && /function|fonction/i.test(error.message) ? 'L’onglet Front attend le script s3-47.' : 'Indisponible pour le moment.'}</span>`;
      return;
    }
    T.front = data; T.frontLu = Date.now();
    rendreFront();
  }catch(e){}
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
  montrerVue(['stats', 'front', 'regie', 'carte'].includes(vue) ? vue : 'stats');
  lien('', 'Chargement…');
  await charger();
  suivrePresence(s.session.user.id);
  setInterval(() => { if(!document.hidden) charger(); }, 60000);
  setInterval(() => { if(!document.hidden && !$('vue-front').hidden) chargerFront(); }, 30000);   // s3-47
  document.addEventListener('visibilitychange', () => { if(!document.hidden){ charger(); if(!$('vue-front').hidden) chargerFront(); } });
})();
