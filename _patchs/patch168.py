# -*- coding: utf-8 -*-
u"""
patch168 — Plus ou moins : entrainement et duels classes (apercu valide le
25 octobre : minuteur 8 s, 20 pts par victoire et 5 par jour, rangs
Arpenteur, Cartographe, Geometre, Recenseur, Prefet).
SQL : _sql/pom-2-duels.sql (AVANT). Sans le SQL, les deux boutons ne
s'affichent pas.
- Carte du QG : rang et Elo, victoires payees du jour, boutons « Duel classe »
  et « S'entrainer ».
- Entrainement : 10 duels tires au hasard, sans points ni minuteur, record
  garde sur l'appareil.
- Duel classe : la paire arrive au moment de la question, 8 s pour repondre
  (minuteur du serveur), resultat contre l'adversaire ou « en attente ».
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

h = lire('index.html')
assert 'qgPomDuel' not in h, u'patch168 deja applique'
h = rempl(h, u'''<div class="qg-titre"><h2>Plus ou moins</h2><p>Solo · 10 duels de population par jour · jusqu'à 50 pts</p></div>''',
u'''<div class="qg-titre"><h2>Plus ou moins</h2><p>10 duels de population · partie du jour jusqu'à 50 pts · duel classé 20 pts par victoire, 5 par jour</p></div>''', 'titre')
h = rempl(h, u'''          <div class="qg-actions"><button type="button" class="qg-btn" id="qgPomBtn">Jouer</button><span class="qg-petit" id="qgPomInfo"></span></div>''',
u'''          <div class="qg-rang" id="qgPomRang" hidden>
            <div><b id="qgPomRangNom">—</b><span class="qg-petit" id="qgPomGains"></span></div>
            <span class="qg-elo"><b id="qgPomElo">—</b> Elo</span>
          </div>
          <div class="qg-actions"><button type="button" class="qg-btn" id="qgPomBtn">Jouer</button>
            <button type="button" class="qg-btn" id="qgPomDuel" hidden>Duel classé</button>
            <button type="button" class="qg-btn" id="qgPomEntr" hidden>S'entraîner</button>
            <span class="qg-petit" id="qgPomInfo"></span></div>''', 'boutons')
ecrire('index.html', h)

js = lire('app.js')
assert 'pom_d_lancer' not in js, u'patch168 deja applique'
js = rempl(js, u"""  chargerPom();   // patch160""", u"""  chargerPom();   // patch160
  chargerPomDuelEtat();   // patch168""", 'qg')
js = rempl(js, u"""document.getElementById('qgPomBtn').addEventListener('click', () => ouvrirPom());""", u"""document.getElementById('qgPomBtn').addEventListener('click', () => ouvrirPom());

// ---------- patch168 : entrainement et duels classes ----------
let pomDuelEtat = null;           // null = pas charge, false = SQL absent
let pomMode = null, pomEntr = null, pomDuel = null, pomQuestion = null;
let pomMinuteur = null, pomFenFermer = null, pomOccupe2 = false;
async function chargerPomDuelEtat(){
  const { data, error } = await sb.rpc('pom_d_etat');
  if(error){ if(fonctionAbsente(error)) pomDuelEtat = false; renderPomDuelCarte(); return; }
  pomDuelEtat = data;
  renderPomDuelCarte();
}
function renderPomDuelCarte(){
  const ok = !!pomDuelEtat;
  ['qgPomDuel', 'qgPomEntr'].forEach(id => { const b = document.getElementById(id); if(b) b.hidden = !ok; });
  const r = document.getElementById('qgPomRang');
  if(r) r.hidden = !ok;
  if(!ok) return;
  const e = pomDuelEtat;
  document.getElementById('qgPomRangNom').textContent = e.rang;
  document.getElementById('qgPomElo').textContent = Number(e.elo).toLocaleString('fr-FR');
  document.getElementById('qgPomGains').textContent = ` · ${e.gains_jour} / ${e.gains_max} victoires payées`
    + (e.en_attente > 0 ? ` · ${e.en_attente} en attente` : '');
  const d = document.getElementById('qgPomDuel');
  d.textContent = e.en_cours ? 'Reprendre le duel' : 'Duel classé';
  d.classList.add('plein');
}
function pomCacher(c){ return Object.assign({}, c, { population: null }); }
function pomStopMinuteur(){ if(pomMinuteur){ cancelAnimationFrame(pomMinuteur); pomMinuteur = null; } }
function pomEcart(pa, pb){
  const rapport = Math.max(pa, pb) / Math.max(1, Math.min(pa, pb));
  return rapport >= 2 ? `${rapport.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} fois plus d'habitants`
                      : `${Math.max(1, Math.round(100 * (rapport - 1)))} % d'habitants de plus`;
}
function pomLireRecord(){ try{ return Number(localStorage.getItem('tf-pom-record')) || 0; }catch(e){ return 0; } }
function pomEcrireRecord(n){ try{ localStorage.setItem('tf-pom-record', String(n)); }catch(e){} }
function pomPastillesListe(res, total){
  return '<span class="pom-pastilles">' + Array.from({ length: total }, (_, k) =>
    `<i class="${k < res.length ? (res[k] ? 'ok' : 'ko') : (k === res.length ? 'ici' : '')}"></i>`).join('') + '</span>';
}
function pomReveler(pa, pb, k, juste, tard){
  const tuiles = document.querySelectorAll('#pomCorps .pom-commune');
  const grand = pa > pb ? 0 : 1;
  tuiles.forEach((t, j) => {
    t.disabled = true;
    t.classList.add(j === grand ? 'gagne' : 'perd');
    if(j === k && !juste) t.classList.add('mauvais');
    pomCompter(document.getElementById('pomPop' + j), j === 0 ? pa : pb);
  });
  return grand;
}
function pomOuvrirFenetre(mode){
  pomMode = mode;
  pomFenFermer = ouvrirFenetre(`<div class="fenetre pom" role="dialog" aria-modal="true" aria-labelledby="pomTitre">
      <button type="button" class="pom-fermer" data-pom2="fermer" aria-label="Fermer">✕</button>
      <div id="pomCorps"></div></div>`, () => { pomFenFermer = null; pomStopMinuteur(); pomMode = null; chargerPomDuelEtat(); });
  const f = document.querySelector('.fenetre.pom');
  if(f) f.addEventListener('click', (ev) => {
    const c = ev.target.closest('[data-pom-choix]');
    if(c && !c.disabled) return pomMode === 'entr' ? pomEntrChoisir(Number(c.dataset.pomChoix)) : pomDuelChoisir(Number(c.dataset.pomChoix));
    const a = ev.target.closest('[data-pom2]');
    if(!a) return;
    const q = a.dataset.pom2;
    if(q === 'fermer' && pomFenFermer) pomFenFermer(null);
    else if(q === 'entr-suivant') renderPomEntr();
    else if(q === 'entr-encore') pomEntrDemarrer();
    else if(q === 'duel-suivant') pomDuelQuestion();
    else if(q === 'duel-rejouer') pomDuelLancer();
  });
}

// ----- entrainement -----
async function pomEntrDemarrer(){
  const { data, error } = await sb.rpc('pom_entrainement');
  if(error){ notifier({ type: 'erreur', titre: 'Plus ou moins', texte: messageLisible(error.message) }); return; }
  pomEntr = { duels: data, res: [] };
  renderPomEntr();
}
async function ouvrirPomEntr(){
  pomOuvrirFenetre('entr');
  document.getElementById('pomCorps').innerHTML = '<p class="pom-note">Préparation des duels…</p>';
  await pomEntrDemarrer();
}
function renderPomEntr(){
  const corps = document.getElementById('pomCorps');
  if(!corps || !pomEntr) return;
  const i = pomEntr.res.length, total = pomEntr.duels.length;
  if(i >= total){
    const n = pomEntr.res.filter(Boolean).length, avant = pomLireRecord();
    if(n > avant) pomEcrireRecord(n);
    corps.innerHTML = `<div class="pom-fin">
        <span class="pom-sur">Entraînement · sans points</span>
        <div class="pom-score">${n}<span> / ${total}</span></div>
        <div class="pom-ligne">${pomEntr.res.map(x => x ? '🟩' : '🟥').join('')}</div>
        <span class="pom-gain">${n > avant ? 'Nouveau record !' : `Record d'entraînement : ${avant} / ${total}`}</span>
        <button type="button" class="pom-btn" data-pom2="entr-encore">Encore 10 duels</button>
      </div>`;
    return;
  }
  const d = pomEntr.duels[i];
  corps.innerHTML = `<div class="pom-tete"><h2 id="pomTitre">Entraînement <span>duel ${i + 1} / ${total} · sans points</span></h2>${pomPastillesListe(pomEntr.res, total)}</div>
    <p class="pom-question">Laquelle a le plus d'habitants ?</p>
    <div class="pom-duel">${pomTuile(pomCacher(d.a), 0)}<span class="pom-ou">ou</span>${pomTuile(pomCacher(d.b), 1)}</div>
    <p class="pom-verdict" id="pomVerdict" aria-live="polite"></p>
    <button type="button" class="pom-btn" data-pom2="entr-suivant" id="pomSuivant" hidden>${i === total - 1 ? 'Voir mon score' : 'Duel suivant'}</button>
    ${pomCredits(d)}`;
}
function pomEntrChoisir(k){
  const i = pomEntr.res.length, d = pomEntr.duels[i];
  if(!d || document.querySelector('#pomCorps .pom-commune:disabled')) return;
  const pa = d.a.population, pb = d.b.population;
  const juste = (k === 0 && pa > pb) || (k === 1 && pb > pa);
  pomEntr.res.push(juste);
  const grand = pomReveler(pa, pb, k, juste, false);
  const nom = (grand === 0 ? d.a : d.b).nom;
  const v = document.getElementById('pomVerdict');
  v.className = 'pom-verdict ' + (juste ? 'ok' : 'ko');
  v.textContent = juste ? `Bien vu ! ${nom} compte ${pomEcart(pa, pb)}.` : `Raté : c'est ${nom}, avec ${pomEcart(pa, pb)}.`;
  const p = document.querySelector('#pomCorps .pom-pastilles');
  if(p) p.outerHTML = pomPastillesListe(pomEntr.res, pomEntr.duels.length);
  const s = document.getElementById('pomSuivant'); if(s){ s.hidden = false; s.focus(); }
}

// ----- duel classe -----
async function ouvrirPomDuel(){
  pomOuvrirFenetre('duel');
  await pomDuelLancer();
}
async function pomDuelLancer(){
  const corps = document.getElementById('pomCorps');
  if(corps) corps.innerHTML = '<p class="pom-note">Recherche d\\'un adversaire…</p>';
  const { data, error } = await sb.rpc('pom_d_lancer');
  if(error){ notifier({ type: 'erreur', titre: 'Duel classé', texte: messageLisible(error.message) }); if(pomFenFermer) pomFenFermer(null); return; }
  pomDuel = data;
  if(pomDuel.fini) return renderPomDuelFin();
  pomDuelQuestion();
}
function pomDuelTete(){
  const e = pomDuelEtat || {}, adv = pomDuel && pomDuel.adversaire;
  const res = (pomDuel.reponses || []).map((r, k) => {
    const j = (pomDuel.joues || [])[k];
    return j ? ((r === 0 && j.a.population > j.b.population) || (r === 1 && j.b.population > j.a.population)) : false;
  });
  return `<div class="pom-tete"><h2 id="pomTitre">Duel classé <span>${adv ? 'contre ' + echapperTexte(adv.pseudo) : 'nouvelle partie'}</span></h2>${pomPastillesListe(res, pomDuel.total || 10)}</div>
    <p class="pom-sous-tete">${e.rang ? echapperTexte(e.rang) + ' · ' + Number(e.elo).toLocaleString('fr-FR') + ' Elo' : ''}${adv && adv.elo ? ' · adversaire ' + Number(adv.elo).toLocaleString('fr-FR') + ' Elo' : ''}</p>`;
}
async function pomDuelQuestion(){
  pomStopMinuteur();
  const { data, error } = await sb.rpc('pom_d_question', { p_id: pomDuel.id });
  if(error){ notifier({ type: 'erreur', titre: 'Duel classé', texte: messageLisible(error.message) }); return; }
  if(data.fini){ pomDuel = data.vue; return renderPomDuelFin(); }
  pomQuestion = data;
  // les reponses deja donnees (ex. trop tard enregistre par le serveur)
  if((pomDuel.reponses || []).length !== data.i){
    const r = await sb.rpc('pom_d_lancer');
    if(!r.error && r.data) pomDuel = r.data;
  }
  const corps = document.getElementById('pomCorps');
  if(!corps) return;
  corps.innerHTML = `${pomDuelTete()}
    <div class="pom-minuteur"><i id="pomBarre"></i></div>
    <p class="pom-question">Laquelle a le plus d'habitants ? <span class="pom-q-num">${data.i + 1} / ${data.total}</span></p>
    <div class="pom-duel">${pomTuile(data.a, 0)}<span class="pom-ou">ou</span>${pomTuile(data.b, 1)}</div>
    <p class="pom-verdict" id="pomVerdict" aria-live="polite"></p>
    <button type="button" class="pom-btn" data-pom2="duel-suivant" id="pomSuivant" hidden>${data.i === data.total - 1 ? 'Voir le résultat' : 'Duel suivant'}</button>`;
  const total = (pomDuelEtat && pomDuelEtat.ms) || 8000, fin = performance.now() + Number(data.reste_ms);
  const barre = document.getElementById('pomBarre');
  const pas = () => {
    const reste = Math.max(0, fin - performance.now());
    if(barre) barre.style.width = (100 * reste / 8000) + '%';
    if(reste <= 0){ pomMinuteur = null; return pomDuelTropTard(); }
    pomMinuteur = requestAnimationFrame(pas);
  };
  pomMinuteur = requestAnimationFrame(pas);
}
function pomDuelTropTard(){
  document.querySelectorAll('#pomCorps .pom-commune').forEach(t => { t.disabled = true; t.classList.add('perd'); });
  const v = document.getElementById('pomVerdict');
  if(v){ v.className = 'pom-verdict ko'; v.textContent = 'Temps écoulé : compté faux.'; }
  // le serveur garde une marge de 1,5 s : on attend qu'elle passe avant la suite
  const s = document.getElementById('pomSuivant');
  if(s) setTimeout(() => { s.hidden = false; s.focus(); }, 1700);
}
async function pomDuelChoisir(k){
  if(pomOccupe2 || !pomQuestion) return;
  pomOccupe2 = true;
  pomStopMinuteur();
  document.querySelectorAll('#pomCorps .pom-commune').forEach(t => { t.disabled = true; });
  const { data, error } = await sb.rpc('pom_d_repondre', { p_id: pomDuel.id, p_i: pomQuestion.i, p_choix: k });
  pomOccupe2 = false;
  if(error){ notifier({ type: 'erreur', titre: 'Duel classé', texte: messageLisible(error.message) }); return pomDuelQuestion(); }
  pomDuel = data.vue;
  const grand = pomReveler(data.pop_a, data.pop_b, k, data.juste, data.tard);
  const nom = (grand === 0 ? pomQuestion.a : pomQuestion.b).nom;
  const v = document.getElementById('pomVerdict');
  v.className = 'pom-verdict ' + (data.juste ? 'ok' : 'ko');
  v.textContent = data.tard ? 'Trop tard : compté faux.'
    : data.juste ? `Bien vu en ${(data.ms / 1000).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} s ! ${nom} compte ${pomEcart(data.pop_a, data.pop_b)}.`
                 : `Raté : c'est ${nom}, avec ${pomEcart(data.pop_a, data.pop_b)}.`;
  const p = document.querySelector('#pomCorps .pom-tete');
  if(p){ const t = document.createElement('div'); t.innerHTML = pomDuelTete(); p.replaceWith(t.firstElementChild); }
  const s = document.getElementById('pomSuivant'); if(s){ s.hidden = false; s.focus(); }
}
function renderPomDuelFin(){
  pomStopMinuteur();
  const corps = document.getElementById('pomCorps');
  if(!corps || !pomDuel) return;
  const d = pomDuel, adv = d.adversaire;
  const lignes = (d.reponses || []).map((r, k) => {
    const j = (d.joues || [])[k];
    return j && ((r === 0 && j.a.population > j.b.population) || (r === 1 && j.b.population > j.a.population)) ? '🟩' : '🟥';
  }).join('');
  const sec = (ms) => (Number(ms || 0) / 1000).toLocaleString('fr-FR', { maximumFractionDigits: 1 }) + ' s';
  let titre, detail = '', gains = '';
  if(d.resultat){
    titre = d.resultat === 'victoire' ? 'Victoire' : d.resultat === 'defaite' ? 'Défaite' : 'Égalité';
    titre += ` ${d.justes} – ${adv && adv.justes != null ? adv.justes : '?'}`;
    if(adv && adv.justes === d.justes) detail = `À égalité de réponses : ${sec(d.temps_total)} contre ${sec(adv.temps_total)}.`;
    const delta = (d.elo_apres || 0) - (d.elo_avant || 0);
    gains = `<span class="pom-gain">${delta >= 0 ? '+' : ''}${delta} Elo → ${Number(d.elo_apres).toLocaleString('fr-FR')}</span>`
          + (d.gain ? `<span class="pom-gain">+${d.gain} points Terra</span>` : '');
  } else {
    titre = `${d.justes} / ${d.total}`;
    detail = "En attente d'un adversaire : le duel se règle quand un autre joueur aura joué les mêmes 10 duels. Tu verras le résultat dans le QG.";
  }
  corps.innerHTML = `<div class="pom-fin">
      <span class="pom-sur">Duel classé${adv ? ' contre ' + echapperTexte(adv.pseudo) : ''}</span>
      <div class="pom-score pom-${d.resultat || 'attente'}">${titre}</div>
      <div class="pom-ligne">${lignes}</div>
      <div class="pom-gains">${gains}</div>
      ${detail ? `<p class="pom-note">${detail}</p>` : ''}
      <button type="button" class="pom-btn" data-pom2="duel-rejouer">Rejouer</button>
    </div>`;
  if(d.gain) loadPackStatus();
  chargerPomDuelEtat();
}
document.getElementById('qgPomDuel').addEventListener('click', () => ouvrirPomDuel());
document.getElementById('qgPomEntr').addEventListener('click', () => ouvrirPomEntr());""", 'module')
ecrire('app.js', js)

css = lire('style.css')
css = rempl(css, u"/* patch115 : l'astuce sous la recherche d'echange */", u"""/* ---------- patch168 : Plus ou moins, entrainement et duels ---------- */
.pom-sous-tete{ margin:-12px 0 0; color: var(--brume); font-size:.82rem; }
.pom-minuteur{ height:8px; border-radius:4px; background:#2A3B57; overflow:hidden; }
.pom-minuteur i{ display:block; height:100%; width:100%; background: linear-gradient(90deg, #E5484D, var(--c-legendaire) 40%, #3DD68C); }
.pom-q-num{ color: var(--brume); font-size:.95rem; margin-left:6px; }
.pom-gains{ display:flex; gap:8px; flex-wrap:wrap; justify-content:center; }
.pom-gains:empty{ display:none; }
.pom-score.pom-victoire{ color:#3DD68C; } .pom-score.pom-defaite{ color:#E5484D; }
.pom-score.pom-victoire, .pom-score.pom-defaite, .pom-score.pom-egalite{ font-size:2.4rem; }

/* patch115 : l'astuce sous la recherche d'echange */""", 'css')
ecrire('style.css', css)
print(u'patch168 applique. Lancer : python3 maj-version.py')
