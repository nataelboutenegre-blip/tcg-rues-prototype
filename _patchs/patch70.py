# -*- coding: utf-8 -*-
u"""
patch70 — Le QG et Radar.

POURQUOI
  Decide le 5 octobre avec Natael (maquette « QG et Radar » validee) :
  un onglet QG qui regroupe les defis (Commune du jour, Radar, et plus tard
  d'autres), et Radar, un duel en differe classe a l'Elo.

CE QUE LE JOUEUR VOIT
  - L'onglet « Commune du jour » devient « QG » (meme place : colonne sur
    ordinateur, tete du menu Plus sur telephone). Pastille si la commune du
    jour n'est pas jouee ou si un resultat de duel attend.
  - QG : la carte Commune du jour, la carte Radar (rang, Elo, jauge, duels
    restants, Lancer / Reprendre), les derniers duels, le classement, et
    une carte « Bientot ».
  - Radar : l'adversaire, cinq manches de 15 s (nom de la commune, carte,
    clic, Valider, puis la vraie position avec ton point et le sien), le
    resultat et l'Elo. Sans adversaire, la partie attend le prochain joueur
    et le resultat arrive dans le QG.
  - Rangs : Promeneur, Randonneur, Guetteur (depart), Vigie, Navigateur ;
    Lapérouse pour le n°1.
  - Liens : ?onglet=qg, ?onglet=radar ; ?onglet=cdj marche toujours.

COTE SERVEUR (_sql/radar-1.sql, a lancer avant)
  Le chrono est celui du serveur, le nom d'une commune n'arrive qu'a
  l'ouverture de sa manche. Aucun gain en points ou paquets.

PAS ENCORE
  « Defier un ami » et les notifications de resultat.
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

def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)


# ======================= index.html =======================
html = lire('index.html')

html = rempl(html,
u"""      <div class="tab" data-tab="cdj">
        <div class="icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.6"/></svg>
        </div>
        Commune du jour
        <span class="tab-badge" id="cdjBadge" hidden></span>
      </div>
""",
u"""      <div class="tab" data-tab="qg">
        <div class="icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><path d="M12 12 L17.6 6.4"/><circle cx="12" cy="12" r="1.1" fill="currentColor"/></svg>
        </div>
        QG
        <span class="tab-badge" id="qgBadge" hidden></span>
      </div>

      <div class="tab onglet-fusionne" data-tab="cdj" aria-hidden="true">
        <div class="icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.6"/></svg>
        </div>
        Commune du jour
        <span class="tab-badge" id="cdjBadge" hidden></span>
      </div>

      <div class="tab onglet-fusionne" data-tab="radar" aria-hidden="true">
        <div class="icon"><svg viewBox="0 0 24 24"></svg></div>
        Radar
      </div>
""", 'onglets')

PANNEAUX = u"""    <section class="tab-panel" id="panel-qg">
      <h1>QG</h1>
      <div class="sub">Les défis du jour et les duels contre les autres joueurs.</div>

      <div class="qg-grille">
        <div class="qg-carte" id="qgCdj">
          <div class="qg-tete">
            <span class="qg-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.6"/></svg></span>
            <div class="qg-titre"><h2>Commune du jour</h2><p>Solo · une commune mystère par jour</p></div>
            <span class="qg-etiquette" id="qgCdjEtat"></span>
          </div>
          <div class="qg-actions"><button type="button" class="qg-btn" id="qgCdjBtn">Jouer</button><span class="qg-petit" id="qgCdjInfo"></span></div>
        </div>

        <div class="qg-carte" id="qgRadar">
          <div class="qg-tete">
            <span class="qg-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><path d="M12 12 L17.6 6.4"/><circle cx="12" cy="12" r="1.1" fill="currentColor"/></svg></span>
            <div class="qg-titre"><h2>Radar</h2><p>Duel classé · place 5 communes sur la carte</p></div>
            <span class="qg-etiquette or" id="qgRestants"></span>
          </div>
          <div class="qg-rang">
            <div><b id="qgRangNom">—</b><span class="qg-petit" id="qgRangSuivant"></span></div>
            <span class="qg-elo"><b id="qgElo">—</b> Elo</span>
          </div>
          <div>
            <div class="qg-jauge"><i id="qgJauge"></i></div>
            <div class="qg-paliers"><span>Promeneur</span><span>Randonneur</span><span>Guetteur</span><span>Vigie</span><span>Navigateur</span></div>
          </div>
          <div class="qg-actions"><button type="button" class="qg-btn plein" id="qgLancer">Lancer un duel</button><span class="qg-petit" id="qgAttente"></span></div>
        </div>

        <div class="qg-carte" id="qgDerniersBloc" hidden>
          <h3 class="qg-h3">Tes derniers duels</h3>
          <ul class="qg-duels" id="qgDerniers"></ul>
        </div>

        <div class="qg-carte">
          <h3 class="qg-h3">Classement Radar</h3>
          <ol class="qg-classement" id="qgClassement"><li class="qg-vide">Aucun duel joué pour l'instant.</li></ol>
        </div>

        <div class="qg-carte qg-bientot">
          <div class="qg-tete">
            <span class="qg-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M5 12h14M12 5v14"/></svg></span>
            <div class="qg-titre"><h2>Bientôt</h2><p>D'autres duels arriveront ici</p></div>
          </div>
        </div>
      </div>
    </section>

    <section class="tab-panel" id="panel-radar">
      <h1>Radar</h1>
      <div class="rd-ecran" id="rdVs" hidden>
        <p class="qg-petit" id="rdVsTexte"></p>
        <div class="rd-vs">
          <div class="rd-joueur"><b>Toi</b><span id="rdVsMoi"></span></div>
          <em>VS</em>
          <div class="rd-joueur"><b id="rdVsLui">?</b><span id="rdVsLuiInfo"></span></div>
        </div>
      </div>
      <div class="rd-ecran" id="rdManche" hidden>
        <div class="rd-points" id="rdPoints"></div>
        <div class="rd-tete">
          <div><small id="rdNum"></small><b id="rdNom">—</b></div>
          <span class="rd-chrono" id="rdChrono"></span>
        </div>
        <div class="rd-carte"><svg id="rdCarte" role="img" aria-label="Carte de France : clique pour placer la commune"></svg></div>
        <div class="rd-verdict" id="rdVerdict"></div>
        <div class="qg-actions"><button type="button" class="qg-btn plein" id="rdValider" disabled>Valider</button></div>
      </div>
      <div class="rd-ecran" id="rdFin" hidden></div>
      <p class="qg-vide" id="rdIndispo" hidden>Radar n'est pas disponible pour le moment.</p>
    </section>

    <section class="tab-panel" id="panel-cdj">"""

html = rempl(html, u"""    <section class="tab-panel" id="panel-cdj">""", PANNEAUX, 'panneaux')
ecrire('index.html', html)


# ======================= app.js =======================
js = lire('app.js')

js = rempl(js,
u"""const ONGLETS_FUSIONNES = ['defense', 'succes'];""",
u"""const ONGLETS_FUSIONNES = ['defense', 'succes', 'cdj', 'radar'];""", 'fusion')
js = rempl(js,
u"""const ONGLET_PARENT = { defense: 'combat', succes: 'profil' };""",
u"""const ONGLET_PARENT = { defense: 'combat', succes: 'profil', cdj: 'qg', radar: 'qg' };""", 'parents')
js = rempl(js,
u"""const ONGLETS_CONNUS = ['tirage', 'collection', 'territoire', 'bourse', 'combat', 'defense', 'regles', 'cdj'];""",
u"""const ONGLETS_CONNUS = ['tirage', 'collection', 'territoire', 'bourse', 'combat', 'defense', 'regles', 'cdj', 'qg', 'radar'];""", 'liens')

js = rempl(js,
u"""  const cdj = document.getElementById('cdjBadge');
  const cdjAJouer = surTelephone() && cdj && !cdj.hidden;""",
u"""  const cdj = document.getElementById('qgBadge');
  const cdjAJouer = surTelephone() && cdj && !cdj.hidden;""", 'badge plus')

js = rempl(js,
u"""    if(tab.dataset.tab === 'cdj') ouvrirCdj();""",
u"""    if(tab.dataset.tab === 'cdj') ouvrirCdj();
    if(tab.dataset.tab === 'qg') ouvrirQG();""", 'ouverture qg')

# la pastille du QG suit celle de la commune du jour
js = rempl(js,
u"""    badge.hidden = e.fini;""",
u"""    badge.hidden = e.fini;
    majBadgeQG();""", 'badge cdj 1')
js = rempl(js,
u"""    if(badge) badge.hidden = true;""",
u"""    if(badge) badge.hidden = true;
    majBadgeQG();""", 'badge cdj 2')

js = rempl(js,
u"""  chargerSaison();
  chargerCdj();""",
u"""  chargerSaison();
  chargerCdj();
  chargerRadar();""", 'demarrage')

js = rempl(js,
u"""
initAuth();
""",
u"""
// ---------- QG et Radar (patch70) ----------
// Tout ce qui compte (chrono, distances, Elo) se decide sur le serveur.
let radarEtat = null;
let radarPartie = null;
let radarPin = null;
let radarRevele = false;
let radarChrono = null, radarFin = 0, radarEnvoi = false;
const RADAR_RANGS = [['Promeneur', 0], ['Randonneur', 900], ['Guetteur', 1000], ['Vigie', 1100], ['Navigateur', 1200]];

function majBadgeQG(){
  const b = document.getElementById('qgBadge');
  if(!b) return;
  const cdj = document.getElementById('cdjBadge');
  const cdjAJouer = cdj && !cdj.hidden;
  const nonVus = radarEtat ? Number(radarEtat.non_vus || 0) : 0;
  const n = (cdjAJouer ? 1 : 0) + nonVus;
  b.hidden = n === 0;
  b.textContent = n;
  majBadgePlus();
}

async function chargerRadar(){
  const { data, error } = await sb.rpc('radar_etat');
  if(error){ console.warn('TERRAFRONT radar indisponible', error); radarEtat = null; }
  else radarEtat = data;
  majBadgeQG();
  const qg = document.getElementById('panel-qg');
  if(qg && qg.classList.contains('active')) renderQG();
}

async function ouvrirQG(){
  renderQG();
  if(!cdjEtat) chargerCdj();
  await chargerRadar();
  renderQG();
  // les resultats affiches sont vus : la pastille s'eteint
  if(radarEtat && radarEtat.non_vus > 0){
    sb.rpc('radar_vu').then(() => { radarEtat.non_vus = 0; majBadgeQG(); });
  }
}

function rangSuivant(elo){
  for(const [nom, seuil] of RADAR_RANGS) if(elo < seuil) return [nom, seuil];
  return null;
}

function renderQG(){
  // Commune du jour
  const e = cdjEtat;
  const etat = document.getElementById('qgCdjEtat'), info = document.getElementById('qgCdjInfo'), btn = document.getElementById('qgCdjBtn');
  if(!e){ etat.textContent = ''; info.textContent = 'Pas disponible pour le moment.'; btn.hidden = true; }
  else {
    btn.hidden = false;
    const nb = e.essais.length;
    etat.className = 'qg-etiquette' + (e.fini ? (e.trouve ? ' vert' : '') : ' or');
    etat.textContent = e.fini ? (e.trouve ? `Trouvée en ${nb}` : 'Pas trouvée') : (nb ? `${nb} essai${nb > 1 ? 's' : ''} sur 6` : 'À jouer');
    btn.textContent = e.fini ? 'Revoir' : (nb ? 'Continuer' : 'Jouer');
    btn.classList.toggle('plein', !e.fini);
    info.textContent = (e.serie > 0 ? `Série de ${e.serie} jour${e.serie > 1 ? 's' : ''} · ` : '') + 'nouvelle commune à minuit';
  }

  // Radar
  const r = radarEtat;
  const lancer = document.getElementById('qgLancer');
  if(!r){
    document.getElementById('qgRangNom').textContent = '—';
    document.getElementById('qgRangSuivant').textContent = '';
    document.getElementById('qgElo').textContent = '—';
    document.getElementById('qgRestants').textContent = '';
    document.getElementById('qgAttente').textContent = 'Radar n’est pas disponible pour le moment.';
    lancer.disabled = true;
    return;
  }
  const elo = Number(r.elo);
  document.getElementById('qgRangNom').textContent = r.rang;
  document.getElementById('qgRangNom').className = 'rang-' + sansAccents(r.rang).toLowerCase();
  const suiv = rangSuivant(elo);
  document.getElementById('qgRangSuivant').textContent = r.rang === 'Lapérouse' ? 'n°1 du classement'
    : (suiv ? `encore ${suiv[1] - elo} pts pour ${suiv[0]}` : 'rang le plus haut');
  document.getElementById('qgElo').textContent = elo.toLocaleString('fr-FR');
  document.getElementById('qgJauge').style.width = Math.max(2, Math.min(100, (elo - 800) / 500 * 100)) + '%';
  document.getElementById('qgRestants').textContent = r.en_cours ? 'partie en cours'
    : (r.restants > 0 ? `${r.restants} duel${r.restants > 1 ? 's' : ''} aujourd’hui` : 'reviens demain');
  lancer.textContent = r.en_cours ? 'Reprendre la partie' : 'Lancer un duel';
  lancer.disabled = !r.en_cours && r.restants <= 0;
  document.getElementById('qgAttente').textContent = r.en_attente > 0
    ? `${r.en_attente} partie${r.en_attente > 1 ? 's' : ''} en attente d’un adversaire` : '';

  // derniers duels
  const d = r.derniers || [];
  document.getElementById('qgDerniersBloc').hidden = d.length === 0;
  document.getElementById('qgDerniers').innerHTML = d.map(x => {
    const delta = (x.elo_apres != null && x.elo_avant != null) ? x.elo_apres - x.elo_avant : 0;
    const mot = x.resultat === 'victoire' ? 'Victoire' : x.resultat === 'defaite' ? 'Défaite' : 'Égalité';
    return `<li class="${x.vu ? '' : 'nouveau'}"><span class="qg-res ${x.resultat}">${mot}</span>
      <span class="qg-adv">contre <b>${echapperTexte(x.adversaire || 'un joueur')}</b><small>${Number(x.total_km).toLocaleString('fr-FR')} km contre ${Number(x.adversaire_km).toLocaleString('fr-FR')} km</small></span>
      <span class="qg-delta ${delta >= 0 ? 'plus' : 'moins'}">${delta >= 0 ? '+' : ''}${delta}</span></li>`;
  }).join('');

  // classement
  const c = r.classement || [];
  document.getElementById('qgClassement').innerHTML = c.length ? c.map((x, i) =>
    `<li class="${x.moi ? 'moi' : ''}"><span class="qg-pos">${i + 1}</span><span class="qg-nom">${echapperTexte(x.pseudo)}</span><span class="qg-rangpetit rang-${sansAccents(x.rang).toLowerCase()}">${x.rang}</span><b>${Number(x.elo).toLocaleString('fr-FR')}</b></li>`).join('')
    : '<li class="qg-vide">Aucun duel joué pour l’instant.</li>';
}

document.getElementById('qgCdjBtn').addEventListener('click', () => {
  const t = document.querySelector('.tab[data-tab="cdj"]'); if(t) t.click();
});

// ----- la partie -----
function radarMontrer(id){
  for(const x of ['rdVs', 'rdManche', 'rdFin']) document.getElementById(x).hidden = x !== id;
  document.getElementById('rdIndispo').hidden = true;
}

document.getElementById('qgLancer').addEventListener('click', async (ev) => {
  const b = ev.currentTarget;
  b.disabled = true;
  try{
    const { data, error } = await sb.rpc('radar_lancer');
    if(error) throw error;
    radarPartie = data;
    const t = document.querySelector('.tab[data-tab="radar"]'); if(t) t.click();
    // reprise d'une partie deja commencee : directement la manche
    if(data.jouees.length > 0 || data.en_cours){ radarSuite(); return; }
    radarMontrer('rdVs');
    const moi = radarEtat ? `${radarEtat.rang} · ${Number(radarEtat.elo).toLocaleString('fr-FR')}` : '';
    document.getElementById('rdVsMoi').textContent = moi;
    const a = data.adversaire;
    if(a){
      document.getElementById('rdVsLui').textContent = a.pseudo;
      document.getElementById('rdVsLuiInfo').textContent = a.elo ? `${radarRangDe(a.elo)} · ${Number(a.elo).toLocaleString('fr-FR')}` : '';
      document.getElementById('rdVsTexte').textContent = `${a.pseudo} a joué ces 5 communes. À toi de faire mieux.`;
    } else {
      document.getElementById('rdVsLui').textContent = '?';
      document.getElementById('rdVsLuiInfo').textContent = '';
      document.getElementById('rdVsTexte').textContent = 'Personne de disponible pour l’instant : tu joues 5 communes neuves, et le prochain joueur les affrontera. Le résultat arrivera dans le QG.';
    }
    setTimeout(radarSuite, a ? 2200 : 3200);
  } catch(err){
    notifier({ type: 'erreur', titre: 'Radar', texte: messageLisible(err.message) });
    chargerRadar();
  } finally { b.disabled = false; }
});

function radarRangDe(elo){
  let r = RADAR_RANGS[0][0];
  for(const [nom, seuil] of RADAR_RANGS) if(elo >= seuil) r = nom;
  return r;
}

async function radarSuite(){
  if(!radarPartie) return;
  if(radarPartie.fini){ radarResultat(); return; }
  const { data, error } = await sb.rpc('radar_ouvrir', { p_id: radarPartie.id });
  if(error){ notifier({ type: 'erreur', titre: 'Radar', texte: messageLisible(error.message) }); return; }
  radarPartie = data;
  if(data.fini){ radarResultat(); return; }
  radarPin = null; radarRevele = false; radarEnvoi = false;
  radarMontrer('rdManche');
  const n = data.manche;
  document.getElementById('rdNum').textContent = `Commune ${n + 1} sur ${data.manches}`;
  document.getElementById('rdNom').textContent = data.en_cours ? data.en_cours.nom : '—';
  document.getElementById('rdPoints').innerHTML = Array.from({ length: data.manches }, (_, i) =>
    `<i class="${i < n ? 'fait' : i === n ? 'encours' : ''}"></i>`).join('');
  document.getElementById('rdVerdict').innerHTML = '<span>Clique sur la carte, puis valide.</span>';
  const v = document.getElementById('rdValider');
  v.disabled = true; v.textContent = 'Valider';
  radarDessiner();
  radarFin = Date.now() + (data.en_cours ? data.en_cours.reste_ms : 0);
  clearInterval(radarChrono);
  radarChrono = setInterval(radarTic, 200);
  radarTic();
}

function radarTic(){
  const r = Math.max(0, Math.ceil((radarFin - Date.now()) / 1000));
  const el = document.getElementById('rdChrono');
  el.textContent = r;
  el.classList.toggle('court', r <= 5);
  // a zero, on envoie ce qu'on a (le point pose, ou rien)
  if(r === 0 && !radarRevele && !radarEnvoi) radarViser();
}

async function radarViser(){
  if(radarEnvoi || radarRevele || !radarPartie) return;
  radarEnvoi = true;
  clearInterval(radarChrono);
  document.getElementById('rdValider').disabled = true;
  const p = radarPin;
  const { data, error } = await sb.rpc('radar_viser', { p_id: radarPartie.id, p_lon: p ? p[0] : null, p_lat: p ? p[1] : null });
  radarEnvoi = false;
  if(error){ notifier({ type: 'erreur', titre: 'Radar', texte: messageLisible(error.message) }); return; }
  radarPartie = data;
  radarRevele = true;
  const m = data.jouees[data.jouees.length - 1];
  const moi = m.moi, lui = m.lui;
  const temps = moi.lon === null;
  document.getElementById('rdVerdict').innerHTML =
    `<b>${temps ? 'Temps écoulé · ' : ''}${Number(moi.km).toLocaleString('fr-FR')} km</b>` +
    (lui ? `<span>${echapperTexte(data.adversaire ? data.adversaire.pseudo : 'Adversaire')} : ${Number(lui.km).toLocaleString('fr-FR')} km</span>` : `<span>${echapperTexte(m.nom)} (${echapperTexte(m.dept)})</span>`);
  const v = document.getElementById('rdValider');
  v.disabled = false;
  v.textContent = data.fini ? 'Voir le résultat' : 'Commune suivante';
  radarDessiner(m);
}

document.getElementById('rdValider').addEventListener('click', () => {
  if(!radarRevele){ if(radarPin) radarViser(); return; }
  if(radarPartie.fini) radarResultat(); else radarSuite();
});

function radarAssurerBornes(){
  const contour = FRANCE_OUTLINE || cdjContour;
  if(cdjBornes || !contour) return !!cdjBornes;
  let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
  for(const anneau of contour) for(const [lo, la] of anneau){
    x0 = Math.min(x0, lo * CDJ_K); x1 = Math.max(x1, lo * CDJ_K);
    y0 = Math.min(y0, -la); y1 = Math.max(y1, -la);
  }
  cdjBornes = { x0: x0 - 0.3, y0: y0 - 0.3, w: x1 - x0 + 0.6, h: y1 - y0 + 0.6 };
  return true;
}

function radarDessiner(manche){
  const svg = document.getElementById('rdCarte');
  if(!svg || !radarAssurerBornes()) return;
  const contour = FRANCE_OUTLINE || cdjContour;
  svg.setAttribute('viewBox', `0 0 ${cdjBornes.w.toFixed(2)} ${cdjBornes.h.toFixed(2)}`);
  const ray = cdjBornes.w / 80;
  let h = '';
  for(const a of contour) h += `<path class="cdj-fr" d="M${a.map(([lo, la]) => cdjPx(lo, la).join(',')).join('L')}Z"/>`;
  if(manche){
    const [cx, cy] = cdjPx(+manche.lon, +manche.lat);
    if(manche.lui && manche.lui.lon !== null){
      const [ax, ay] = cdjPx(+manche.lui.lon, +manche.lui.lat);
      h += `<line class="rd-trait lui" x1="${ax}" y1="${ay}" x2="${cx}" y2="${cy}" stroke-width="${ray / 3}" stroke-dasharray="${ray / 2} ${ray / 2}"/>`;
      h += `<circle class="rd-lui" cx="${ax}" cy="${ay}" r="${ray * 0.8}" stroke-width="${ray / 4}"/>`;
    }
    if(manche.moi && manche.moi.lon !== null){
      const [x, y] = cdjPx(+manche.moi.lon, +manche.moi.lat);
      h += `<line class="rd-trait moi" x1="${x}" y1="${y}" x2="${cx}" y2="${cy}" stroke-width="${ray / 3}" stroke-dasharray="${ray / 2} ${ray / 2}"/>`;
    }
    h += `<circle class="cdj-cible" cx="${cx}" cy="${cy}" r="${ray * 2.2}" stroke-width="${ray / 2.5}"/><circle class="cdj-cible-c" cx="${cx}" cy="${cy}" r="${ray * 0.9}"/>`;
    h += `<text class="rd-etiquette" x="${cx}" y="${(cy - ray * 2.8).toFixed(3)}" font-size="${ray * 2.2}">${echapperTexte(manche.nom)}</text>`;
  }
  const pin = manche ? (manche.moi && manche.moi.lon !== null ? [manche.moi.lon, manche.moi.lat] : null) : radarPin;
  if(pin){
    const [x, y] = cdjPx(+pin[0], +pin[1]);
    h += `<circle class="rd-moi" cx="${x}" cy="${y}" r="${ray}" stroke-width="${ray / 3.5}"/>`;
  }
  svg.innerHTML = h;
}

document.getElementById('rdCarte').addEventListener('click', (e) => {
  if(radarRevele || radarEnvoi || !cdjBornes) return;
  const svg = e.currentTarget, pt = svg.createSVGPoint();
  pt.x = e.clientX; pt.y = e.clientY;
  const q = pt.matrixTransform(svg.getScreenCTM().inverse());
  radarPin = [(q.x + cdjBornes.x0) / CDJ_K, -(q.y + cdjBornes.y0)];
  document.getElementById('rdValider').disabled = false;
  document.getElementById('rdVerdict').innerHTML = '<span>Tu peux déplacer ton point, puis valider.</span>';
  radarDessiner();
});

function radarResultat(){
  clearInterval(radarChrono);
  const p = radarPartie;
  radarMontrer('rdFin');
  const fmt = (n) => Number(n).toLocaleString('fr-FR');
  const lignes = p.jouees.map(m => `<tr><td>${echapperTexte(m.nom)} <small>(${echapperTexte(m.dept)})</small></td>
    <td class="${m.lui && m.moi.km < m.lui.km ? 'mieux' : ''}">${fmt(m.moi.km)} km</td>
    ${p.adversaire ? `<td class="${m.lui && m.lui.km < m.moi.km ? 'mieux' : ''}">${m.lui ? fmt(m.lui.km) + ' km' : ''}</td>` : ''}</tr>`).join('');
  const tableau = `<table class="rd-detail"><thead><tr><th>Commune</th><th>Toi</th>${p.adversaire ? `<th>${echapperTexte(p.adversaire.pseudo)}</th>` : ''}</tr></thead><tbody>${lignes}</tbody></table>`;
  let tete;
  if(p.adversaire && p.resultat){
    const mot = p.resultat === 'victoire' ? 'Victoire' : p.resultat === 'defaite' ? 'Défaite' : 'Égalité';
    const delta = p.elo_apres - p.elo_avant;
    const avant = radarRangDe(p.elo_avant), apres = radarRangDe(p.elo_apres);
    tete = `<h2 class="${p.resultat}">${mot}</h2>
      <div class="rd-score"><div><b>${fmt(p.total_km)} km</b><span>Toi</span></div><em>contre</em><div><b>${fmt(p.adversaire.total_km)} km</b><span>${echapperTexte(p.adversaire.pseudo)}</span></div></div>
      <div class="rd-elo"><span>Elo</span><b class="${delta >= 0 ? 'plus' : 'moins'}">${delta >= 0 ? '+' : ''}${delta}</b><span class="qg-petit">${fmt(p.elo_apres)} · ${apres}${apres !== avant ? (delta > 0 ? ' (promu !)' : ' (rétrogradé)') : ''}</span></div>`;
  } else {
    tete = `<h2>${fmt(p.total_km)} km</h2>
      <p class="qg-petit">Ta partie attend un adversaire : le prochain joueur qui lance un duel affrontera ces 5 communes. Le résultat et l’Elo arriveront dans le QG.</p>`;
  }
  const partage = p.adversaire && p.resultat
    ? `TerraFront · Radar\\n${p.resultat === 'victoire' ? 'Victoire' : p.resultat === 'defaite' ? 'Défaite' : 'Égalité'} contre ${p.adversaire.pseudo} : ${fmt(p.total_km)} km contre ${fmt(p.adversaire.total_km)} km\\n${p.jouees.map(m => m.lui && m.moi.km < m.lui.km ? '🟦' : '🟥').join('')}\\nterrafront.fr/?onglet=qg`
    : null;
  document.getElementById('rdFin').innerHTML = `<div class="rd-bloc">${tete}${tableau}
    ${partage ? `<pre class="cdj-partage" id="rdPartage">${echapperTexte(partage)}</pre>` : ''}
    <div class="qg-actions"><button type="button" class="qg-btn plein" id="rdRetour">Retour au QG</button>${partage ? '<button type="button" class="qg-btn" id="rdCopier">Copier pour Discord</button>' : ''}</div></div>`;
  document.getElementById('rdRetour').onclick = () => { const t = document.querySelector('.tab[data-tab="qg"]'); if(t) t.click(); };
  const c = document.getElementById('rdCopier');
  if(c) c.onclick = async () => {
    try{ await navigator.clipboard.writeText(partage); c.textContent = 'Copié'; }
    catch(err){ const s = getSelection(), r = document.createRange(); r.selectNodeContents(document.getElementById('rdPartage')); s.removeAllRanges(); s.addRange(r); c.textContent = 'Sélectionné : copie-le'; }
  };
  radarPartie = null;
  chargerRadar();
}

initAuth();
""", 'module radar')

ecrire('app.js', js)


# ======================= style.css =======================
css = lire('style.css')
css += u"""

/* ---------- QG et Radar (patch70) ---------- */
.qg-grille{ display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:16px; margin-top:16px; align-items:start; }
@media (max-width: 900px){ .qg-grille{ grid-template-columns:minmax(0,1fr); } }
.qg-carte{ background: var(--nuit-2); border:1px solid rgba(169,188,212,.18); border-radius:14px; padding:16px; display:flex; flex-direction:column; gap:12px; min-width:0; }
.qg-carte[hidden]{ display:none; }
.qg-tete{ display:flex; align-items:center; gap:8px 12px; flex-wrap:wrap; }
.qg-ico{ width:46px; height:46px; flex:none; border-radius:12px; display:grid; place-items:center; background: var(--nuit-3); color: var(--c-legendaire); }
.qg-ico svg{ width:28px; height:28px; }
.qg-titre{ flex:1; min-width:150px; }
.qg-titre h2{ font-family: var(--titre); font-weight:800; font-size:24px; letter-spacing:.02em; text-transform:uppercase; margin:0; line-height:1; }
.qg-titre p{ margin:3px 0 0; font-size:13px; color: var(--brume); }
.qg-h3{ font-family: var(--titre); font-weight:800; font-size:20px; letter-spacing:.02em; text-transform:uppercase; margin:0; }
.qg-etiquette{ font-size:11.5px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; padding:3px 8px; border-radius:20px; border:1px solid rgba(169,188,212,.3); color: var(--brume); white-space:nowrap; }
.qg-etiquette:empty{ display:none; }
.qg-etiquette.or{ color: var(--c-legendaire); border-color: rgba(240,180,41,.5); }
.qg-etiquette.vert{ color: var(--c-peucommun); border-color: rgba(34,160,107,.5); }
.qg-actions{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
.qg-btn{ font: inherit; font-weight:600; font-size:14px; padding:9px 14px; border-radius:10px; cursor:pointer; background:transparent; color:#fff; border:1px solid rgba(169,188,212,.3); }
.qg-btn.plein{ font-family: var(--titre); font-weight:800; font-size:18px; letter-spacing:.04em; text-transform:uppercase; background: var(--c-legendaire); color: var(--nuit); border-color: var(--c-legendaire); }
.qg-btn:disabled{ opacity:.4; cursor:default; }
.qg-btn:focus-visible{ outline:2px solid #fff; outline-offset:2px; }
.qg-btn[hidden]{ display:none; }
.qg-petit{ font-size:13px; color: var(--brume); }
.qg-rang{ display:flex; align-items:center; gap:12px; padding:10px 12px; border-radius:10px; background: rgba(255,255,255,.04); }
.qg-rang > div{ display:flex; flex-direction:column; }
.qg-rang b{ font-family: var(--titre); font-size:22px; font-weight:800; letter-spacing:.02em; }
.qg-elo{ margin-left:auto; color: var(--brume); font-variant-numeric:tabular-nums; white-space:nowrap; }
.qg-elo b{ font-family: var(--titre); font-size:22px; color:#fff; }
.qg-jauge{ height:6px; border-radius:4px; background: rgba(255,255,255,.08); overflow:hidden; }
.qg-jauge i{ display:block; height:100%; background: var(--c-legendaire); }
.qg-paliers{ display:grid; grid-template-columns:repeat(5, 1fr); font-size:10.5px; color: var(--brume); margin-top:4px; }
.rang-promeneur{ color:#7E8BA0; } .rang-randonneur{ color:#22A06B; } .rang-guetteur{ color:#2F7CF6; }
.rang-vigie{ color:#8E7CF6; } .rang-navigateur{ color:#E5484D; } .rang-laperouse{ color:#F0B429; }
.qg-duels, .qg-classement{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:4px; font-variant-numeric:tabular-nums; }
.qg-duels li{ display:grid; grid-template-columns:auto minmax(0,1fr) auto; gap:10px; align-items:center; padding:7px 8px; border-radius:8px; }
.qg-duels li.nouveau{ background: rgba(240,180,41,.1); }
.qg-res{ font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; }
.qg-res.victoire{ color: var(--c-peucommun); } .qg-res.defaite{ color: var(--c-rouge); } .qg-res.egalite{ color: var(--brume); }
.qg-adv small{ display:block; font-size:12px; color: var(--brume); }
.qg-delta.plus{ color: var(--c-peucommun); font-weight:700; } .qg-delta.moins{ color: var(--c-rouge); font-weight:700; }
.qg-classement li{ display:grid; grid-template-columns:22px minmax(0,1fr) auto auto; gap:10px; align-items:center; padding:6px 8px; border-radius:8px; font-size:14px; }
.qg-classement li.moi{ background: rgba(240,180,41,.14); }
.qg-pos{ color: var(--brume); }
.qg-nom{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.qg-rangpetit{ font-size:12px; }
.qg-vide{ color: var(--brume); font-size:14px; }
.qg-bientot{ opacity:.6; }

.rd-ecran{ display:flex; flex-direction:column; gap:14px; margin-top:12px; max-width:640px; }
.rd-ecran[hidden]{ display:none; }
.rd-vs{ display:flex; justify-content:center; align-items:center; gap:18px; padding:20px 0; }
.rd-joueur{ display:flex; flex-direction:column; align-items:center; gap:2px; }
.rd-joueur b{ font-family: var(--titre); font-size:26px; font-weight:800; }
.rd-joueur span{ font-size:12.5px; color: var(--brume); }
.rd-vs em{ font-family: var(--titre); font-style:normal; font-size:30px; color: var(--c-legendaire); }
.rd-points{ display:flex; gap:6px; }
.rd-points i{ flex:1; height:5px; border-radius:3px; background: rgba(255,255,255,.1); }
.rd-points i.fait{ background: var(--c-legendaire); }
.rd-points i.encours{ background: rgba(240,180,41,.45); }
.rd-tete{ display:flex; align-items:flex-end; gap:12px; }
.rd-tete small{ display:block; font-size:12px; letter-spacing:.07em; text-transform:uppercase; color: var(--brume); }
.rd-tete b{ font-family: var(--titre); font-size:clamp(28px,7vw,40px); font-weight:900; line-height:1; }
.rd-chrono{ margin-left:auto; font-family: var(--titre); font-size:30px; font-weight:800; font-variant-numeric:tabular-nums; color: var(--c-legendaire); }
.rd-chrono.court{ color: var(--c-rouge); }
.rd-carte{ background: var(--nuit-2); border:1px solid rgba(169,188,212,.18); border-radius:14px; padding:12px; touch-action:manipulation; }
.rd-carte svg{ width:100%; height:auto; display:block; cursor:crosshair; }
.rd-moi{ fill: var(--c-rare); stroke:#fff; }
.rd-lui{ fill: var(--c-rouge); stroke: var(--nuit); }
.rd-trait.moi{ stroke: var(--c-rare); } .rd-trait.lui{ stroke: var(--c-rouge); stroke-opacity:.6; }
.rd-etiquette{ fill:#fff; font-weight:700; text-anchor:middle; }
.rd-verdict{ display:flex; justify-content:space-between; gap:10px; align-items:baseline; flex-wrap:wrap; min-height:28px; }
.rd-verdict b{ font-family: var(--titre); font-size:26px; font-weight:800; }
.rd-verdict span{ color: var(--brume); font-size:14px; }
.rd-bloc{ background: var(--nuit-2); border:1px solid rgba(169,188,212,.18); border-radius:14px; padding:16px; display:flex; flex-direction:column; gap:14px; }
.rd-bloc h2{ font-family: var(--titre); font-weight:900; font-size:40px; text-transform:uppercase; margin:0; line-height:1; }
.rd-bloc h2.victoire{ color: var(--c-legendaire); } .rd-bloc h2.defaite{ color: var(--brume); }
.rd-score{ display:grid; grid-template-columns:1fr auto 1fr; gap:10px; align-items:center; text-align:center; }
.rd-score b{ display:block; font-family: var(--titre); font-size:32px; font-weight:800; font-variant-numeric:tabular-nums; }
.rd-score span{ font-size:13px; color: var(--brume); }
.rd-score em{ font-style:normal; color: var(--brume); }
.rd-elo{ display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:10px; background: rgba(255,255,255,.04); }
.rd-elo b{ font-family: var(--titre); font-size:24px; }
.rd-elo .plus{ color: var(--c-peucommun); } .rd-elo .moins{ color: var(--c-rouge); }
.rd-detail{ width:100%; border-collapse:collapse; font-variant-numeric:tabular-nums; font-size:14px; }
.rd-detail th{ font-weight:500; color: var(--brume); font-size:12px; text-align:right; padding:4px 6px; }
.rd-detail th:first-child, .rd-detail td:first-child{ text-align:left; white-space:normal; }
.rd-detail td{ padding:7px 6px; border-top:1px solid rgba(169,188,212,.18); text-align:right; white-space:nowrap; }
.rd-detail td small{ color: var(--brume); }
.rd-detail td.mieux{ color: var(--c-legendaire); font-weight:600; }
"""
ecrire('style.css', css)

print(u'patch70 applique : index.html, app.js, style.css')
