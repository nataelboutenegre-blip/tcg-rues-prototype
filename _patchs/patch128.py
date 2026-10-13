# -*- coding: utf-8 -*-
u"""
patch128 — Rafale (idée d'Oshannir) et un QG filtré par jeu (idée de Nataël).

1. Rafale, deuxième duel du QG : une lettre, 30 secondes, le plus de
   communes possible. Duel classé (Elo à part, 20 pts par victoire, 5 par
   jour), défi amical, entraînement (sans serveur, sans points).
   Tout ce qui compte se décide sur le serveur (_sql/rafale-1.sql) : la
   lettre n'arrive qu'au départ du chrono, chaque nom est vérifié.
2. QG : les cartes des jeux en haut (Commune du jour, Radar, Rafale), puis
   les défis des deux jeux, puis côte à côte l'historique (filtre Tous,
   Radar, Rafale) et le classement (filtre Radar, Rafale). Le choix est
   retenu sur l'appareil.
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

js = lire('app.js')
css = lire('style.css')
html = lire('index.html')
assert 'rafaleEtat' not in js, u'patch128 deja applique'

ICO_RAFALE = u'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M13.5 2.5 5 13.5h6l-1.5 8 8.5-11h-6z"/></svg>'

# ================================================================ HTML
# l'onglet cache du jeu
html = rempl(html, u"""      <div class="tab onglet-fusionne" data-tab="radar" aria-hidden="true">
        <div class="icon"><svg viewBox="0 0 24 24"></svg></div>
        Radar
      </div>""", u"""      <div class="tab onglet-fusionne" data-tab="radar" aria-hidden="true">
        <div class="icon"><svg viewBox="0 0 24 24"></svg></div>
        Radar
      </div>
      <div class="tab onglet-fusionne" data-tab="rafale" aria-hidden="true">
        <div class="icon"><svg viewBox="0 0 24 24"></svg></div>
        Rafale
      </div>""", u'onglet rafale')

# la grille du QG : jeux, defis, puis historique et classement
html = rempl(html, u"""      <div class="qg-grille">
        <div class="qg-carte" id="qgCdj">""", u"""      <div class="qg-grille">
        <div class="qg-jeux">
        <div class="qg-carte" id="qgCdj">""", u'grille debut')

html = rempl(html, u"""          <div class="qg-actions"><button type="button" class="qg-btn plein" id="qgLancer">Lancer un duel</button><button type="button" class="qg-btn" id="qgEntr">S'entraîner</button><button type="button" class="qg-btn" id="qgDefier">Défier un joueur</button><span class="qg-petit" id="qgAttente"></span></div>
        </div>
""", u"""          <div class="qg-actions"><button type="button" class="qg-btn plein" id="qgLancer">Lancer un duel</button><button type="button" class="qg-btn" id="qgEntr">S'entraîner</button><button type="button" class="qg-btn" id="qgDefier">Défier un joueur</button><span class="qg-petit" id="qgAttente"></span></div>
        </div>

        <div class="qg-carte" id="qgRafale">
          <div class="qg-tete">
            <span class="qg-ico">""" + ICO_RAFALE + u"""</span>
            <div class="qg-titre"><h2>Rafale</h2><p>Duel classé · une lettre, 30 s · 20 pts par victoire, 5 par jour</p></div>
            <span class="qg-etiquette or" id="rfEtiquette"></span>
          </div>
          <div class="qg-rang">
            <div><b id="rfRangNom">—</b><span class="qg-petit" id="rfRangSuivant"></span></div>
            <span class="qg-elo"><b id="rfElo">—</b> Elo</span>
          </div>
          <div>
            <div class="qg-jauge"><i id="rfJauge"></i></div>
            <div class="qg-paliers"><span>Piéton</span><span>Cycliste</span><span>Motard</span><span>Routier</span><span>Pilote</span></div>
          </div>
          <div class="qg-actions"><button type="button" class="qg-btn plein" id="rfLancer">Lancer un duel</button><button type="button" class="qg-btn" id="rfEntr">S'entraîner</button><button type="button" class="qg-btn" id="rfDefier">Défier un joueur</button><span class="qg-petit" id="rfAttente"></span></div>
        </div>
        </div>
""", u'carte rafale')

html = rempl(html, u"""        <div class="qg-carte" id="qgDerniersBloc" hidden>
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
      </div>""", u"""        <div class="qg-carte" id="qgDerniersBloc">
          <div class="qg-h3-ligne"><h3 class="qg-h3">Tes derniers duels</h3>
            <div class="qg-filtre" role="group" aria-label="Jeu de l'historique"><button type="button" data-hist="tous">Tous</button><button type="button" data-hist="radar">Radar</button><button type="button" data-hist="rafale">Rafale</button></div></div>
          <ul class="qg-duels" id="qgDerniers"></ul>
        </div>

        <div class="qg-carte">
          <div class="qg-h3-ligne"><h3 class="qg-h3">Classement</h3>
            <div class="qg-filtre" role="group" aria-label="Jeu du classement"><button type="button" data-cl="radar">Radar</button><button type="button" data-cl="rafale">Rafale</button></div></div>
          <ol class="qg-classement" id="qgClassement"><li class="qg-vide">Aucun duel joué pour l'instant.</li></ol>
        </div>
      </div>""", u'historique classement')

# le panneau du jeu
html = rempl(html, u"""      <p class="qg-vide" id="rdIndispo" hidden>Radar n'est pas disponible pour le moment.</p>
    </section>""", u"""      <p class="qg-vide" id="rdIndispo" hidden>Radar n'est pas disponible pour le moment.</p>
    </section>

    <section class="tab-panel" id="panel-rafale">
      <h1>Rafale</h1>
      <div class="rd-ecran" id="rfVs" hidden>
        <p class="qg-petit" id="rfVsTexte"></p>
        <div class="rd-vs">
          <div class="rd-joueur"><b>Toi</b><span id="rfVsMoi"></span></div>
          <em>VS</em>
          <div class="rd-joueur"><b id="rfVsLui">?</b><span id="rfVsLuiInfo"></span></div>
        </div>
        <p class="rf-consigne">Une lettre va s'afficher. Tape le plus de communes qui commencent par cette lettre, Entrée après chacune. 30 secondes.</p>
        <div class="qg-actions"><button type="button" class="qg-btn plein" id="rfPartir">Partir</button><button type="button" class="qg-btn" id="rfAnnulerVs">QG</button></div>
      </div>
      <div class="rd-ecran" id="rfJeu" hidden>
        <div class="rf-scene">
          <div class="rf-haut">
            <div class="rf-lettre" id="rfLettre" aria-live="polite">?</div>
            <div class="rf-compteurs">
              <div class="rf-score"><b id="rfScore">0</b><span id="rfScoreMot">commune</span></div>
              <div class="rf-chrono" id="rfChronoBarre"><i id="rfBarre"></i></div>
              <div class="rf-temps" id="rfTemps"><b>30</b> s</div>
            </div>
          </div>
          <form class="rf-form" id="rfForm" autocomplete="off">
            <input id="rfChamp" type="text" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" enterkeyhint="send" aria-label="Nom de commune" placeholder="Une commune…">
            <button class="qg-btn plein" type="submit">OK</button>
          </form>
          <div class="rf-retour" id="rfRetour" role="status" aria-live="polite"></div>
          <div class="rf-plaques" id="rfPlaques"></div>
        </div>
      </div>
      <div class="rd-ecran" id="rfFin" hidden></div>
    </section>""", u'panneau rafale')

# ================================================================ JS
# l'onglet fusionne, et ?onglet=rafale
js = rempl(js, u"""const ONGLETS_FUSIONNES = ['defense', 'succes', 'cdj', 'radar'];
// l'onglet qui s'allume quand on ouvre un volet fusionne
const ONGLET_PARENT = { defense: 'combat', succes: 'profil', cdj: 'qg', radar: 'qg' };""",
u"""const ONGLETS_FUSIONNES = ['defense', 'succes', 'cdj', 'radar', 'rafale'];
// l'onglet qui s'allume quand on ouvre un volet fusionne
const ONGLET_PARENT = { defense: 'combat', succes: 'profil', cdj: 'qg', radar: 'qg', rafale: 'qg' };""", u'fusionnes')

js = rempl(js, u"""  chargerCdj();
  chargerRadar();
  verifierVersion();""", u"""  chargerCdj();
  chargerRadar();
  chargerRafale();   // patch128
  verifierVersion();""", u'demarrage')

# la pastille du QG compte aussi Rafale
js = rempl(js, u"""  const defis = radarEtat && Array.isArray(radarEtat.defis_recus) ? radarEtat.defis_recus.length : 0;
  const n = (cdjAJouer ? 1 : 0) + nonVus + defis;""", u"""  const defis = radarEtat && Array.isArray(radarEtat.defis_recus) ? radarEtat.defis_recus.length : 0;
  // patch128 : Rafale
  const rfNonVus = rafaleEtat ? Number(rafaleEtat.non_vus || 0) : 0;
  const rfDefis = rafaleEtat && Array.isArray(rafaleEtat.defis_recus) ? rafaleEtat.defis_recus.length : 0;
  const n = (cdjAJouer ? 1 : 0) + nonVus + defis + rfNonVus + rfDefis;""", u'badge')

js = rempl(js, u"""  if(!cdjEtat) chargerCdj();
  await chargerRadar();
  renderQG();
  // les resultats affiches sont vus : la pastille s'eteint
  if(radarEtat && radarEtat.non_vus > 0){
    sb.rpc('radar_vu').then(() => { radarEtat.non_vus = 0; majBadgeQG(); });
  }""", u"""  if(!cdjEtat) chargerCdj();
  await Promise.all([chargerRadar(), chargerRafale()]);
  renderQG();
  // les resultats affiches sont vus : la pastille s'eteint
  if(radarEtat && radarEtat.non_vus > 0){
    sb.rpc('radar_vu').then(() => { radarEtat.non_vus = 0; majBadgeQG(); });
  }
  if(rafaleEtat && rafaleEtat.non_vus > 0){
    sb.rpc('rafale_vu').then(() => { rafaleEtat.non_vus = 0; majBadgeQG(); });
  }""", u'ouvrir qg')

# renderQG : la carte Rafale et les listes filtrees remplacent les listes du Radar
js = rempl(js, u"""    document.getElementById('qgAttente').textContent = 'Radar n’est pas disponible pour le moment.';
    lancer.disabled = true;
    return;
  }""", u"""    document.getElementById('qgAttente').textContent = 'Radar n’est pas disponible pour le moment.';
    lancer.disabled = true;
    renderRafaleCarte(); renderQGListes();   // patch128
    return;
  }""", u'radar indispo')

debut_listes = u"""  // derniers duels, et en tete les parties qui attendent un adversaire.
  // Chaque ligne ouvre le resume du duel (patch74)."""
fin_listes = u"""    : '<li class="qg-vide">Aucun duel joué pour l’instant.</li>';
}

document.getElementById('qgCdjBtn')"""
i = js.index(debut_listes); j = js.index(fin_listes)
assert js.count(debut_listes) == 1 and js.count(fin_listes) == 1 and i < j
js = js[:i] + u"""  // patch128 : la carte Rafale, puis les listes des deux jeux, filtrees
  renderRafaleCarte();
  renderQGListes();
}

document.getElementById('qgCdjBtn')""" + js[j + len(fin_listes):]

# les clics des listes : le resume du bon jeu
js = rempl(js, u"""    const rel = e.target.closest('[data-relever]');
    if(rel){ rel.disabled = true; radarRelever(Number(rel.dataset.relever), rel.dataset.pseudo); return; }
    const dec = e.target.closest('[data-decliner]');
    if(dec){ dec.disabled = true; radarDecliner(Number(dec.dataset.decliner)); return; }
    const li = e.target.closest('li[data-id]'); if(li) radarOuvrirResume(Number(li.dataset.id));
  });
  liste.addEventListener('keydown', (e) => {
    if(e.key !== 'Enter' && e.key !== ' ') return;
    const li = e.target.closest('li[data-id]'); if(!li || e.target !== li) return;
    e.preventDefault(); radarOuvrirResume(Number(li.dataset.id));
  });""", u"""    const rel = e.target.closest('[data-relever]');
    if(rel){ rel.disabled = true; (rel.dataset.jeu === 'rafale' ? rafaleRelever : radarRelever)(Number(rel.dataset.relever), rel.dataset.pseudo); return; }
    const dec = e.target.closest('[data-decliner]');
    if(dec){ dec.disabled = true; (dec.dataset.jeu === 'rafale' ? rafaleDecliner : radarDecliner)(Number(dec.dataset.decliner)); return; }
    const li = e.target.closest('li[data-id]'); if(li) ouvrirResumeDuel(li);
  });
  liste.addEventListener('keydown', (e) => {
    if(e.key !== 'Enter' && e.key !== ' ') return;
    const li = e.target.closest('li[data-id]'); if(!li || e.target !== li) return;
    e.preventDefault(); ouvrirResumeDuel(li);
  });""", u'clics defis')

js = rempl(js, u"""  const liste = document.getElementById('qgDerniers');
  liste.addEventListener('click', (e) => {
    const li = e.target.closest('li[data-id]'); if(li) radarOuvrirResume(Number(li.dataset.id));
  });
  liste.addEventListener('keydown', (e) => {
    if(e.key !== 'Enter' && e.key !== ' ') return;
    const li = e.target.closest('li[data-id]'); if(!li) return;
    e.preventDefault(); radarOuvrirResume(Number(li.dataset.id));
  });""", u"""  const liste = document.getElementById('qgDerniers');
  liste.addEventListener('click', (e) => {
    const li = e.target.closest('li[data-id]'); if(li) ouvrirResumeDuel(li);
  });
  liste.addEventListener('keydown', (e) => {
    if(e.key !== 'Enter' && e.key !== ' ') return;
    const li = e.target.closest('li[data-id]'); if(!li) return;
    e.preventDefault(); ouvrirResumeDuel(li);
  });""", u'clics derniers')

# le bloc Rafale, juste avant le Radar
js = rempl(js, u"""// ---------- QG et Radar (patch70) ----------""", u"""// ---------- patch128 : Rafale, et le QG filtre par jeu ----------
// Le serveur decide de tout (rafale-1.sql) : la lettre n'arrive qu'au depart
// du chrono, chaque nom est verifie la-bas. L'entrainement, lui, se joue ici.
let rafaleEtat = null;
let rafalePartie = null;        // la partie en cours (vue du serveur), ou { entr: true, ... }
let rafaleChrono = null, rafaleFin = 0;
let rafaleFile = [], rafaleEnvoi = false, rafaleDernierOk = 0;
let rafaleNoms = null, rafaleNomsEnCours = null;
const RAFALE_RANGS = [['Piéton', 0], ['Cycliste', 900], ['Motard', 1000], ['Routier', 1100], ['Pilote', 1200]];
const RAFALE_LETTRES = 'ABCDEFGHJLMNOPRSTV';
const RAFALE_SECONDES = 30;
let qgFiltreHist = (() => { try{ const v = localStorage.getItem('tf-qg-hist'); return ['tous', 'radar', 'rafale'].includes(v) ? v : 'tous'; }catch(e){ return 'tous'; } })();
let qgFiltreCl = (() => { try{ return localStorage.getItem('tf-qg-cl') === 'rafale' ? 'rafale' : 'radar'; }catch(e){ return 'radar'; } })();

// meme regle que rafale_norm() sur le serveur
function rafaleNorm(s){
  let t = String(s || '').replace(/œ/g, 'oe').replace(/Œ/g, 'OE').replace(/æ/g, 'ae').replace(/Æ/g, 'AE')
    .normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toUpperCase();
  t = t.replace(/(^|[^A-Z])STE(?=[^A-Z]|$)/g, '$1SAINTE').replace(/(^|[^A-Z])ST(?=[^A-Z]|$)/g, '$1SAINT');
  return t.replace(/[^A-Z]/g, '');
}
function rafaleRangDe(elo){
  let r = RAFALE_RANGS[0][0];
  for(const [nom, seuil] of RAFALE_RANGS) if(elo >= seuil) r = nom;
  return r;
}

async function chargerRafale(){
  const { data, error } = await sb.rpc('rafale_etat');
  if(error){ console.warn('TERRAFRONT rafale indisponible', error); rafaleEtat = null; }
  else rafaleEtat = data;
  majBadgeQG();
  const qg = document.getElementById('panel-qg');
  if(qg && qg.classList.contains('active')) renderQG();
}

function renderRafaleCarte(){
  const r = rafaleEtat;
  const lancer = document.getElementById('rfLancer');
  if(!r){
    document.getElementById('rfRangNom').textContent = '—';
    document.getElementById('rfRangSuivant').textContent = '';
    document.getElementById('rfElo').textContent = '—';
    document.getElementById('rfEtiquette').textContent = '';
    document.getElementById('rfAttente').textContent = 'Rafale n’est pas disponible pour le moment.';
    lancer.disabled = true;
    return;
  }
  lancer.disabled = false;
  const elo = Number(r.elo);
  const nom = document.getElementById('rfRangNom');
  nom.textContent = r.rang;
  nom.className = 'rang-rf-' + sansAccents(r.rang).replace(/\\s+/g, '-');
  let suiv = null;
  for(const [n, seuil] of RAFALE_RANGS) if(elo < seuil){ suiv = [n, seuil]; break; }
  document.getElementById('rfRangSuivant').textContent = r.rang === 'As du volant' ? 'n°1 du classement'
    : (suiv ? `encore ${suiv[1] - elo} pts pour ${suiv[0]}` : 'rang le plus haut');
  document.getElementById('rfElo').textContent = elo.toLocaleString('fr-FR');
  document.getElementById('rfJauge').style.width = Math.max(2, Math.min(100, (elo - 800) / 500 * 100)) + '%';
  document.getElementById('rfEtiquette').textContent = r.en_cours ? 'partie en cours' : '';
  lancer.textContent = r.en_cours ? 'Reprendre la partie' : 'Lancer un duel';
  document.getElementById('rfAttente').textContent = r.en_attente > 0
    ? `${r.en_attente} partie${r.en_attente > 1 ? 's' : ''} en attente d’un adversaire` : '';
}

// une ligne de l'historique, quel que soit le jeu
function ligneDuel(x, jeu, tous){
  const nomAdv = echapperTexte(x.adversaire || 'un joueur');
  const kmQG = (n) => Number(n).toLocaleString('fr-FR');
  const score = (n) => `${Number(n || 0)} commune${Number(n) > 1 ? 's' : ''}`;
  const tag = tous ? `<span class="qg-jeu ${jeu}">${jeu === 'radar' ? 'Radar' : 'Rafale'}</span>` : '';
  const lettre = jeu === 'rafale' && x.lettre ? ` · lettre ${echapperTexte(x.lettre)}` : '';
  const attr = `data-id="${Number(x.id)}" data-jeu="${jeu}" tabindex="0" role="button"`;
  if(x.attente){
    return `<li ${attr}><span class="qg-res attente">En attente</span>
      <span class="qg-adv">${tag}pas encore d’adversaire<small>${jeu === 'radar' ? kmQG(x.total_km) + ' km' : score(x.score)}${lettre}</small></span>
      <span></span><span class="qg-chev" aria-hidden="true">›</span></li>`;
  }
  if(x.resultat === 'refuse' || x.resultat === 'expire'){
    return `<li class="${x.vu ? '' : 'nouveau'}" ${attr}><span class="qg-res sans-reponse">${x.resultat === 'refuse' ? 'Décliné' : 'Expiré'}</span>
      <span class="qg-adv">${tag}défi à <b>${nomAdv}</b><small>${x.resultat === 'refuse' ? 'il a décliné' : 'pas relevé à temps'} · ${jeu === 'radar' ? kmQG(x.total_km) + ' km' : score(x.score)}</small></span>
      <span></span><span class="qg-chev" aria-hidden="true">›</span></li>`;
  }
  const delta = (x.elo_apres != null && x.elo_avant != null) ? x.elo_apres - x.elo_avant : 0;
  const mot = x.resultat === 'victoire' ? 'Victoire' : x.resultat === 'defaite' ? 'Défaite' : 'Égalité';
  const detail = jeu === 'radar'
    ? `${kmQG(x.total_km)} km contre ${kmQG(x.adversaire_km)} km`
    : `${score(x.score)} contre ${Number(x.adversaire_score || 0)}${lettre}`;
  return `<li class="${x.vu ? '' : 'nouveau'}" ${attr}><span class="qg-res ${x.resultat}">${mot}</span>
    <span class="qg-adv">${tag}${x.amical ? 'défi contre' : 'contre'} <b>${nomAdv}</b><small>${detail}</small></span>
    ${x.amical ? '<span class="qg-amical">Amical</span>'
      : `<span class="qg-delta ${delta >= 0 ? 'plus' : 'moins'}">${delta >= 0 ? '+' : ''}${delta}</span>`}<span class="qg-chev" aria-hidden="true">›</span></li>`;
}

function renderQGListes(){
  const rd = radarEtat || {}, rf = rafaleEtat || {};
  // l'historique
  document.querySelectorAll('[data-hist]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.hist === qgFiltreHist)));
  const tous = qgFiltreHist === 'tous';
  const prendre = (jeu, e) => (qgFiltreHist === jeu || tous) ? [
    ...(e.attente_liste || []).map(x => ({ ...x, attente: true, jeu })),
    ...(e.derniers || []).map(x => ({ ...x, jeu }))] : [];
  let lignes = [...prendre('radar', rd), ...prendre('rafale', rf)];
  lignes.sort((a, b) => ((b.attente ? 1 : 0) - (a.attente ? 1 : 0)) || (new Date(b.fin) - new Date(a.fin)));
  if(tous) lignes = lignes.slice(0, 10);
  document.getElementById('qgDerniers').innerHTML = lignes.length
    ? lignes.map(x => ligneDuel(x, x.jeu, tous)).join('')
    : `<li class="qg-vide">Aucun duel ${qgFiltreHist === 'radar' ? 'Radar ' : qgFiltreHist === 'rafale' ? 'Rafale ' : ''}pour l’instant.</li>`;

  // les defis des deux jeux
  const kmQG = (n) => Number(n).toLocaleString('fr-FR');
  const resteJours = (iso) => {
    const j = Math.ceil((new Date(iso).getTime() - Date.now()) / 864e5);
    return j <= 1 ? 'expire aujourd’hui' : `encore ${j} jours`;
  };
  const nomJeu = (jeu) => `<span class="qg-jeu ${jeu}">${jeu === 'radar' ? 'Radar' : 'Rafale'}</span>`;
  const recus = [...(rd.defis_recus || []).map(x => ({ ...x, jeu: 'radar' })), ...(rf.defis_recus || []).map(x => ({ ...x, jeu: 'rafale' }))];
  const envoyes = [...(rd.defis_envoyes || []).map(x => ({ ...x, jeu: 'radar' })), ...(rf.defis_envoyes || []).map(x => ({ ...x, jeu: 'rafale' }))];
  document.getElementById('qgDefisBloc').hidden = recus.length === 0 && envoyes.length === 0;
  document.getElementById('qgDefis').innerHTML = recus.map(x =>
    `<li class="recu"><span class="qg-res defi">Défi</span>
      <span class="qg-adv">${nomJeu(x.jeu)}<b>${echapperTexte(x.pseudo)}</b> te défie<small>${echapperTexte(radarQuand(x.fin))} · ${resteJours(x.expire_le)}</small></span>
      <span class="qg-defi-actions"><button type="button" class="qg-btn plein" data-jeu="${x.jeu}" data-relever="${Number(x.id)}" data-pseudo="${echapperTexte(x.pseudo)}">Relever</button><button type="button" class="qg-btn" data-jeu="${x.jeu}" data-decliner="${Number(x.id)}">Décliner</button></span></li>`).join('')
  + envoyes.map(x =>
    `<li data-id="${Number(x.id)}" data-jeu="${x.jeu}" tabindex="0" role="button"><span class="qg-res attente">Envoyé</span>
      <span class="qg-adv">${nomJeu(x.jeu)}défi à <b>${echapperTexte(x.pseudo)}</b><small>${x.jeu === 'radar' ? kmQG(x.total_km) + ' km' : Number(x.score || 0) + ' communes · lettre ' + echapperTexte(x.lettre || '')} · en attente de sa réponse</small></span>
      <span></span><span class="qg-chev" aria-hidden="true">›</span></li>`).join('');

  // le classement du jeu choisi
  document.querySelectorAll('[data-cl]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.cl === qgFiltreCl)));
  const c = (qgFiltreCl === 'rafale' ? rf.classement : rd.classement) || [];
  const prefixe = qgFiltreCl === 'rafale' ? 'rang-rf-' : 'rang-';
  document.getElementById('qgClassement').innerHTML = c.length ? c.map((x, i) =>
    `<li class="${x.moi ? 'moi' : ''}"><span class="qg-pos">${i + 1}</span><span class="qg-nom">${echapperTexte(x.pseudo)}</span><span class="qg-rangpetit ${prefixe}${sansAccents(x.rang).toLowerCase().replace(/\\s+/g, '-')}">${x.rang}</span><b>${Number(x.elo).toLocaleString('fr-FR')}</b></li>`).join('')
    : `<li class="qg-vide">Aucun duel ${qgFiltreCl === 'rafale' ? 'Rafale' : 'Radar'} joué pour l’instant.</li>`;
}
document.getElementById('panel-qg').addEventListener('click', (e) => {
  const h = e.target.closest('[data-hist]');
  if(h){ qgFiltreHist = h.dataset.hist; try{ localStorage.setItem('tf-qg-hist', qgFiltreHist); }catch(err){} renderQGListes(); return; }
  const c = e.target.closest('[data-cl]');
  if(c){ qgFiltreCl = c.dataset.cl; try{ localStorage.setItem('tf-qg-cl', qgFiltreCl); }catch(err){} renderQGListes(); }
});
function ouvrirResumeDuel(li){
  const id = Number(li.dataset.id);
  if(li.dataset.jeu === 'rafale') rafaleOuvrirResume(id); else radarOuvrirResume(id);
}

// ----- la partie -----
function rafaleMontrer(id){
  for(const x of ['rfVs', 'rfJeu', 'rfFin']) document.getElementById(x).hidden = x !== id;
}
function rafaleAllerAuPanneau(){ const t = document.querySelector('.tab[data-tab="rafale"]'); if(t) t.click(); }
function rafaleAuQG(){ clearInterval(rafaleChrono); const t = document.querySelector('.tab[data-tab="qg"]'); if(t) t.click(); }

// l'ecran d'avant-partie (le bouton Partir ouvre le clavier du telephone)
function rafaleAvant(p, texte, lui, luiInfo, moi){
  rafalePartie = p;
  rafaleAllerAuPanneau();
  rafaleMontrer('rfVs');
  document.getElementById('rfVsTexte').textContent = texte;
  document.getElementById('rfVsLui').textContent = lui;
  document.getElementById('rfVsLuiInfo').textContent = luiInfo || '';
  document.getElementById('rfVsMoi').textContent = moi || '';
  document.getElementById('rfPartir').textContent = p.parti ? 'Reprendre' : 'Partir';
}

document.getElementById('rfLancer').addEventListener('click', async (ev) => {
  const b = ev.currentTarget;
  b.disabled = true;
  try{
    const { data, error } = await sb.rpc('rafale_lancer');
    if(error) throw error;
    const moi = rafaleEtat ? `${rafaleEtat.rang} · ${Number(rafaleEtat.elo).toLocaleString('fr-FR')}` : '';
    const a = data.adversaire;
    if(data.parti) rafaleAvant(data, 'Ta partie est en cours : le chrono tourne toujours.', a ? a.pseudo : '?', '', moi);
    else if(a) rafaleAvant(data, `${a.pseudo} a joué cette lettre. À toi de faire mieux.`, a.pseudo,
      a.elo ? `${rafaleRangDe(a.elo)} · ${Number(a.elo).toLocaleString('fr-FR')}` : '', moi);
    else rafaleAvant(data, 'Personne de disponible pour l’instant : tu joues une lettre neuve, et le prochain joueur l’affrontera. Le résultat arrivera dans le QG.', '?', '', moi);
  } catch(err){
    notifier({ type: 'erreur', titre: 'Rafale', texte: messageLisible(err.message) });
    chargerRafale();
  } finally { b.disabled = false; }
});

document.getElementById('rfPartir').addEventListener('click', async () => {
  const p = rafalePartie;
  if(!p) return;
  // le champ prend le focus pendant le clic : sur telephone, le clavier s'ouvre
  rafaleMontrer('rfJeu');
  const champ = document.getElementById('rfChamp');
  champ.disabled = false; champ.value = ''; champ.focus();
  document.getElementById('rfPlaques').innerHTML = '';
  rafaleRetour('');
  rafaleFile = []; rafaleEnvoi = false; rafaleDernierOk = 0;
  if(p.entr){ rafaleDemarrer(p.lettre, RAFALE_SECONDES * 1000, []); return; }
  document.getElementById('rfLettre').textContent = '…';
  const { data, error } = await sb.rpc('rafale_partir', { p_id: p.id });
  if(error){ notifier({ type: 'erreur', titre: 'Rafale', texte: messageLisible(error.message) }); rafaleAuQG(); return; }
  rafalePartie = data;
  if(data.fini){ rafaleAfficherFin(data, true); return; }
  rafaleDemarrer(data.lettre, data.reste_ms, data.mots || []);
});
document.getElementById('rfAnnulerVs').addEventListener('click', rafaleAuQG);

function rafaleDemarrer(lettre, resteMs, mots){
  document.getElementById('rfLettre').textContent = lettre;
  document.getElementById('rfChamp').placeholder = `Une commune en ${lettre}…`;
  mots.slice().forEach(m => rafalePlaque(m.n, m.d));
  rafaleMajScore(mots.length);
  rafaleFin = Date.now() + resteMs;
  clearInterval(rafaleChrono);
  rafaleChrono = setInterval(rafaleTic, 100);
  rafaleTic();
}
function rafaleTic(){
  const r = Math.max(0, rafaleFin - Date.now());
  document.getElementById('rfBarre').style.transform = `scaleX(${r / (RAFALE_SECONDES * 1000)})`;
  document.getElementById('rfTemps').innerHTML = `<b>${Math.ceil(r / 1000)}</b> s`;
  document.getElementById('rfChronoBarre').classList.toggle('urgent', r <= 5000);
  if(r <= 0) rafaleFinChrono();
}
function rafaleMajScore(n){
  document.getElementById('rfScore').textContent = n;
  document.getElementById('rfScoreMot').textContent = n > 1 ? 'communes' : 'commune';
}
function rafaleRetour(t, non){ const r = document.getElementById('rfRetour'); r.textContent = t; r.className = 'rf-retour' + (non ? ' non' : ''); }
function rafaleFlash(cl){ const c = document.getElementById('rfChamp'); c.classList.remove('non', 'oui'); void c.offsetWidth; c.classList.add(cl); }
function rafalePlaque(nom, dept){
  document.getElementById('rfPlaques').insertAdjacentHTML('afterbegin', `<span class="rf-plaque">${echapperTexte(nom)}<small>${echapperTexte(dept)}</small></span>`);
}
const RAFALE_RAISONS = { lettre: (l) => `ne commence pas par ${l}`, inconnue: () => 'pas de commune de ce nom', deja: () => 'déjà comptée', vite: () => 'trop vite, renvoie-la', vide: () => 'vide', trop: () => 'trop d’envois', fini: () => 'temps écoulé' };

document.getElementById('rfForm').addEventListener('submit', (e) => {
  e.preventDefault();
  const champ = document.getElementById('rfChamp');
  const brut = champ.value.trim();
  champ.value = '';
  if(!brut || !rafalePartie || Date.now() > rafaleFin) return;
  rafaleFile.push(brut);
  rafaleEnvoyer();
});
// un nom a la fois, et au moins 0,55 s apres le dernier accepte (le serveur en veut 0,5)
async function rafaleEnvoyer(){
  if(rafaleEnvoi || !rafaleFile.length) return;
  rafaleEnvoi = true;
  const brut = rafaleFile.shift();
  const p = rafalePartie;
  if(!p){ rafaleEnvoi = false; rafaleFile = []; return; }
  let r;
  if(p.entr) r = rafaleDireLocal(brut);
  else {
    const attente = rafaleDernierOk + 550 - Date.now();
    if(attente > 0) await new Promise(ok => setTimeout(ok, attente));
    const { data, error } = await sb.rpc('rafale_dire', { p_id: p.id, p_nom: brut });
    r = error ? { ok: false, raison: 'erreur' } : data;
  }
  if(r.ok){
    rafaleDernierOk = Date.now();
    rafalePlaque(r.nom, r.dept); rafaleMajScore(r.score);
    rafaleRetour(`+1 · ${r.nom} (${r.dept})`); rafaleFlash('oui');
  } else {
    const f = RAFALE_RAISONS[r.raison];
    rafaleRetour(`« ${brut} » : ${f ? f(p.lettre || (rafalePartie && rafalePartie.lettre) || '') : 'pas comptée'}`, true);
    rafaleFlash('non');
  }
  rafaleEnvoi = false;
  if(rafaleFile.length) rafaleEnvoyer();
  else if(rafaleAttendFin) rafaleTerminer();
}
let rafaleAttendFin = false;
function rafaleFinChrono(){
  clearInterval(rafaleChrono);
  const champ = document.getElementById('rfChamp');
  champ.disabled = true; champ.blur();
  rafaleRetour('Temps écoulé');
  // on laisse partir les noms deja tapes, puis on ferme
  if(rafaleEnvoi || rafaleFile.length){ rafaleAttendFin = true; return; }
  rafaleTerminer();
}
async function rafaleTerminer(){
  rafaleAttendFin = false;
  const p = rafalePartie;
  if(!p) return;
  if(p.entr){ rafaleFinEntr(); return; }
  const { data, error } = await sb.rpc('rafale_terminer', { p_id: p.id });
  if(error){ notifier({ type: 'erreur', titre: 'Rafale', texte: messageLisible(error.message) }); rafaleAuQG(); return; }
  rafaleAfficherFin(data, true);
}

// ----- l'entrainement : rien sur le serveur -----
function rafaleChargerNoms(){
  if(rafaleNoms) return Promise.resolve(rafaleNoms);
  if(!rafaleNomsEnCours){
    rafaleNomsEnCours = fetch('data/noms-communes.json', { cache: 'force-cache' })
      .then(r => r.json())
      .then(l => { rafaleNoms = new Map(); for(const [nom, dept] of l){ const k = rafaleNorm(nom); if(k && !rafaleNoms.has(k)) rafaleNoms.set(k, [nom, dept]); } return rafaleNoms; })
      .catch(err => { rafaleNomsEnCours = null; throw err; });
  }
  return rafaleNomsEnCours;
}
function rafaleDireLocal(brut){
  const p = rafalePartie, k = rafaleNorm(brut);
  if(!k) return { ok: false, raison: 'vide' };
  if(k[0] !== p.lettre) return { ok: false, raison: 'lettre' };
  const v = rafaleNoms.get(k);
  if(!v) return { ok: false, raison: 'inconnue' };
  if(p.vus.has(k)) return { ok: false, raison: 'deja' };
  p.vus.add(k); p.mots.push({ n: v[0], d: v[1] });
  return { ok: true, nom: v[0], dept: v[1], score: p.mots.length };
}
document.getElementById('rfEntr').addEventListener('click', async () => {
  try{ await rafaleChargerNoms(); }
  catch(e){ notifier({ type: 'erreur', titre: 'Rafale', texte: 'La liste des communes ne se charge pas. Recharge la page.' }); return; }
  const lettre = RAFALE_LETTRES[Math.floor(Math.random() * RAFALE_LETTRES.length)];
  rafaleAvant({ entr: true, lettre, mots: [], vus: new Set() }, 'Entraînement : sans adversaire, sans Elo, sans points. Ton record est gardé sur cet appareil.', '—', '', 'Entraînement');
});
function rafaleFinEntr(){
  const p = rafalePartie;
  const records = (() => { try{ return JSON.parse(localStorage.getItem('tf-rafale-records') || '{}'); }catch(e){ return {}; } })();
  const avant = records[p.lettre];
  const nouveau = avant == null || p.mots.length > avant;
  if(nouveau){ records[p.lettre] = p.mots.length; try{ localStorage.setItem('tf-rafale-records', JSON.stringify(records)); }catch(e){} }
  rafaleAfficherFin({ entr: true, lettre: p.lettre, score: p.mots.length, mots: p.mots, record: avant, nouveau }, true);
}

// ----- la fin, et le resume d'un duel -----
async function rafaleOuvrirResume(id){
  try{
    const { data, error } = await sb.rpc('rafale_resume', { p_id: id });
    if(error) throw error;
    rafaleAllerAuPanneau();
    rafaleAfficherFin(data, false);
    window.scrollTo({ top: 0 });
  } catch(err){
    notifier({ type: 'erreur', titre: 'Rafale', texte: messageLisible(err.message) });
  }
}
let rafaleGrandes = null;
const rafaleGainVu = new Set();
function rafaleAfficherFin(p, fin){
  clearInterval(rafaleChrono);
  rafaleMontrer('rfFin');
  rafalePartie = null;
  const fmt = (n) => Number(n || 0).toLocaleString('fr-FR');
  const com = (n) => `${fmt(n)} commune${Number(n) > 1 ? 's' : ''}`;
  const adv = p.adversaire && p.resultat && p.adversaire.score != null ? p.adversaire : null;
  const nomAdv = adv ? echapperTexte(adv.pseudo || 'un joueur') : '';
  const quand = radarQuand(p.regle_le);
  const mot = p.resultat === 'victoire' ? 'Victoire' : p.resultat === 'defaite' ? 'Défaite' : 'Égalité';
  const lettre = `<span class="rf-mini-lettre">${echapperTexte(p.lettre || '?')}</span>`;
  let tete;
  if(p.entr){
    tete = `<span class="rd-etiq">Entraînement · lettre ${echapperTexte(p.lettre)}</span>
      <div class="rd-entr-total"><h2>${com(p.score)}</h2>${p.nouveau && p.record != null ? '<span class="rd-record-ok">Nouveau record !</span>' : ''}</div>
      <p class="qg-petit">${p.record == null ? 'Premier record pour cette lettre.' : (p.nouveau ? `Ancien record : ${com(p.record)}` : `Ton record pour ${echapperTexte(p.lettre)} : ${com(p.record)}`)}</p>`;
  } else if(adv){
    const delta = (p.elo_apres != null && p.elo_avant != null) ? p.elo_apres - p.elo_avant : null;
    tete = `${p.amical ? '<span class="rd-etiq">Défi amical</span>' : ''}
      <div class="rd-titre">${lettre}<h2 class="${p.resultat}">${mot}</h2><span>contre <b>${nomAdv}</b>${quand ? ` · ${quand}` : ''}</span></div>
      <div class="rd-score"><div><b>${fmt(p.score)}</b><span>Toi</span></div><em>contre</em><div><b>${fmt(adv.score)}</b><span>${nomAdv}</span></div></div>
      ${p.amical ? '<p class="qg-petit">Un défi ne compte pas dans l’Elo.</p>'
        : delta != null ? `<div class="rd-elo"><span>Elo</span><b class="${delta >= 0 ? 'plus' : 'moins'}">${delta >= 0 ? '+' : ''}${delta}</b><span class="qg-petit">${fmt(p.elo_apres)} · ${rafaleRangDe(p.elo_apres)}</span></div>` : ''}
      ${p.gain ? `<p class="mj-gain">+${fmt(p.gain)} pts sur ton solde</p>` : ''}`;
    if(p.gain && !rafaleGainVu.has(p.id)){ rafaleGainVu.add(p.id); loadPackStatus(); }
  } else if(p.cible){
    const cible = echapperTexte(p.cible);
    const phrase = p.resultat === 'refuse' ? `${cible} a décliné ton défi.`
      : p.resultat === 'expire' ? `${cible} n’a pas relevé ton défi à temps.`
      : `Défi envoyé à ${cible} : il a 7 jours pour le relever. Le résultat arrivera dans le QG.`;
    tete = `<span class="rd-etiq">Défi amical</span><div class="rd-titre">${lettre}<h2>${com(p.score)}</h2></div><p class="qg-petit">${phrase}</p>`;
  } else {
    tete = `<div class="rd-titre">${lettre}<h2>${com(p.score)}</h2></div>
      <p class="qg-petit">${fin ? 'Ta partie attend un adversaire : le prochain joueur qui lance un duel aura la même lettre. Le résultat et l’Elo arriveront dans le QG.'
        : 'Cette partie attend encore un adversaire. Le résultat et l’Elo arriveront dans le QG.'}</p>`;
  }
  const liste = (mots) => mots && mots.length
    ? mots.map(m => `<span class="rf-plaque">${echapperTexte(m.n)}<small>${echapperTexte(m.d)}</small></span>`).join('')
    : '<span class="qg-petit">Aucune commune.</span>';
  const colonnes = `<div class="rf-colonnes${adv ? '' : ' seule'}">
      <div><h3 class="rd-label">Toi · ${com(p.score)}</h3><div class="rf-plaques">${liste(p.mots)}</div></div>
      ${adv ? `<div><h3 class="rd-label">${nomAdv} · ${com(adv.score)}</h3><div class="rf-plaques lui">${liste(adv.mots)}</div></div>` : ''}
    </div>`;
  const partage = adv
    ? `TerraFront · Rafale, lettre ${p.lettre}\n${mot} contre ${adv.pseudo || 'un joueur'} : ${com(p.score)} contre ${fmt(adv.score)}\nterrafront.fr/?onglet=qg`
    : null;
  document.getElementById('rfFin').innerHTML = `<button type="button" class="rd-retour" id="rfRetourHaut">← QG</button>
    <div class="rd-bloc">${tete}</div>
    <div class="rd-bloc">${colonnes}<p class="rf-oubliees" id="rfOubliees"></p>
      ${partage ? `<pre class="cdj-partage" id="rfPartage">${echapperTexte(partage)}</pre>` : ''}
      <div class="qg-actions">${p.entr
        ? '<button type="button" class="qg-btn plein" id="rfRejouer">Rejouer</button><button type="button" class="qg-btn" id="rfRetourBas">QG</button>'
        : `<button type="button" class="qg-btn plein" id="rfRetourBas">Retour au QG</button>${partage ? '<button type="button" class="qg-btn" id="rfCopier">Copier pour Discord</button>' : ''}`}</div></div>`;
  document.getElementById('rfRetourHaut').onclick = rafaleAuQG;
  document.getElementById('rfRetourBas').onclick = rafaleAuQG;
  const rej = document.getElementById('rfRejouer');
  if(rej) rej.onclick = () => document.getElementById('rfEntr').click();
  const c = document.getElementById('rfCopier');
  if(c) c.onclick = async () => {
    try{ await navigator.clipboard.writeText(partage); c.textContent = 'Copié'; }
    catch(err){ const s = getSelection(), r = document.createRange(); r.selectNodeContents(document.getElementById('rfPartage')); s.removeAllRanges(); s.addRange(r); c.textContent = 'Sélectionné : copie-le'; }
  };
  rafaleMontrerOubliees(p);
  if(!p.entr) chargerRafale();
}
// les plus grandes communes de la lettre que personne n'a dites (liste de l'entrainement du Radar)
async function rafaleMontrerOubliees(p){
  if(!p.lettre) return;
  try{
    if(!rafaleGrandes) rafaleGrandes = await entrCharger();
    const dites = new Set([...(p.mots || []), ...((p.adversaire && p.adversaire.mots) || [])].map(m => rafaleNorm(m.n)));
    const vues = new Set();
    const plus = rafaleGrandes.filter(v => { const k = rafaleNorm(v.nom); if(k[0] !== p.lettre || dites.has(k) || vues.has(k)) return false; vues.add(k); return true; })
      .sort((a, b) => b.pop - a.pop).slice(0, 6);
    const el = document.getElementById('rfOubliees');
    if(el && plus.length) el.innerHTML = `Les plus grandes que personne n’a dites : ${plus.map(v => `<b>${echapperTexte(v.nom)}</b>`).join(', ')}.`;
  } catch(e){}
}

// ----- les defis -----
async function rafaleRelever(id, pseudo){
  try{
    const { data, error } = await sb.rpc('rafale_relever', { p_id: id });
    if(error) throw error;
    rafaleAvant(data, `${pseudo} a joué cette lettre. À toi de faire mieux.`, pseudo, 'sans Elo', 'Défi amical');
  } catch(err){
    notifier({ type: 'erreur', titre: 'Défi', texte: messageLisible(err.message) });
    chargerRafale();
  }
}
async function rafaleDecliner(id){
  const { error } = await sb.rpc('rafale_refuser', { p_id: id });
  if(error) notifier({ type: 'erreur', titre: 'Défi', texte: messageLisible(error.message) });
  chargerRafale();
}
async function rafaleDefier(id, pseudo){
  try{
    const { data, error } = await sb.rpc('rafale_defier', { p_cible: id });
    if(error) throw error;
    rafaleAvant(data, `Tu joues une lettre. ${pseudo} aura 7 jours pour relever ton défi et faire mieux.`, pseudo, 'sans Elo', 'Défi amical');
  } catch(err){
    notifier({ type: 'erreur', titre: 'Défi', texte: messageLisible(err.message) });
    chargerRafale();
  }
}
document.getElementById('rfDefier').addEventListener('click', async () => {
  if(typeof amisCharges !== 'undefined' && !amisCharges) await loadAmis();
  const vus = new Set([ID_MOI]);
  const ligne = (id, pseudo, info) => {
    if(!id || vus.has(id)) return '';
    vus.add(id);
    return `<button type="button" class="dc-joueur" data-defier="${echapperTexte(id)}" data-pseudo="${echapperTexte(pseudo)}"><b>${echapperTexte(pseudo)}</b><span>${info}</span></button>`;
  };
  const amis = (amisListe || []).filter(x => x.etat === 'accepte').map(x => ligne(x.id, x.pseudo, 'ami')).join('');
  const classes = [...((rafaleEtat && rafaleEtat.classement) || []), ...((radarEtat && radarEtat.classement) || [])]
    .filter(x => !x.moi).map(x => ligne(x.id, x.pseudo, 'joueur du QG')).join('');
  const fermer = ouvrirFenetre(`
    <div class="fenetre defi-choix" role="dialog" aria-modal="true" aria-labelledby="dcTitre">
      <h2 id="dcTitre">Défier à Rafale</h2>
      <p class="dc-aide">Défi amical, sans Elo ni points. Tu joues une lettre maintenant ; ton adversaire a 7 jours pour faire mieux avec la même.</p>
      ${amis ? `<h3>Tes amis</h3><div class="dc-liste">${amis}</div>` : ''}
      ${classes ? `<h3>Joueurs du QG</h3><div class="dc-liste">${classes}</div>` : ''}
      ${!amis && !classes ? '<p class="dc-aide">Personne à proposer pour l’instant.</p>' : ''}
      <button type="button" class="open-btn secondary" data-dc-fermer>Annuler</button>
    </div>`);
  const fen = document.querySelector('#fenetre .defi-choix');
  fen.addEventListener('click', (e) => {
    if(e.target.closest('[data-dc-fermer]')){ fermer(null); return; }
    const b = e.target.closest('[data-defier]');
    if(!b) return;
    fermer(null);
    rafaleDefier(b.dataset.defier, b.dataset.pseudo);
  });
});

// ---------- QG et Radar (patch70) ----------""", u'bloc rafale')

# ================================================================ CSS
css += u"""
/* ---------- patch128 : Rafale, et le QG filtré par jeu ---------- */
.qg-jeux{ grid-column:1 / -1; display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:16px; align-items:stretch; }
@media (max-width: 1180px){ .qg-jeux{ grid-template-columns:repeat(2, minmax(0,1fr)); } .qg-jeux #qgCdj{ grid-column:1 / -1; } }
@media (max-width: 900px){ .qg-jeux{ grid-template-columns:minmax(0,1fr); } }
#qgDefisBloc{ grid-column:1 / -1; }
.qg-h3-ligne{ display:flex; align-items:center; justify-content:space-between; gap:8px 12px; flex-wrap:wrap; }
.qg-filtre{ display:inline-flex; padding:3px; gap:2px; border-radius:999px; background: var(--nuit); border:1px solid rgba(169,188,212,.2); }
.qg-filtre button{ font:inherit; font-size:12.5px; font-weight:600; color: var(--brume); background:transparent; border:0; border-radius:999px; padding:4px 11px; cursor:pointer; }
.qg-filtre button:hover{ color:#fff; }
.qg-filtre button[aria-pressed="true"]{ background: var(--c-legendaire); color: var(--nuit); }
.qg-filtre button:focus-visible{ outline:2px solid #fff; outline-offset:1px; }
.qg-jeu{ display:inline-block; margin-right:6px; font-size:10px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; padding:1px 6px; border-radius:4px; vertical-align:1px; }
.qg-jeu.radar{ color:#9DC3FF; background: rgba(77,141,255,.14); }
.qg-jeu.rafale{ color:#FFD27A; background: rgba(240,180,41,.14); }
.qg-duels .qg-vide, .qg-classement .qg-vide{ display:block; padding:4px 8px; }
.rang-rf-pieton{ color: var(--brume); } .rang-rf-cycliste{ color:#9DC3FF; } .rang-rf-motard{ color: var(--c-peucommun); }
.rang-rf-routier{ color: var(--c-epique, #B07CFF); } .rang-rf-pilote, .rang-rf-as-du-volant{ color: var(--c-legendaire); }

/* le jeu : une lettre sur plaque bleue, un chrono en barre, les communes en panneaux de direction */
#panel-rafale .rd-ecran{ max-width:640px; }
.rf-consigne{ margin:0; color: var(--brume); font-size:14px; text-align:center; }
#rfVs .qg-actions{ justify-content:center; }
.rf-scene{ background: var(--nuit-2); border:1px solid rgba(169,188,212,.18); border-radius:16px; padding:16px; display:flex; flex-direction:column; gap:14px; }
.rf-haut{ display:flex; align-items:center; gap:16px; }
.rf-lettre{ width:88px; height:88px; flex:none; border-radius:13px; background:#1F4FA8; border:3px solid #fff; box-shadow:0 0 0 3px #1F4FA8, 0 12px 26px rgba(0,0,0,.4);
  display:grid; place-items:center; font-family: var(--titre); font-weight:900; font-size:64px; color:#fff; line-height:1; }
.rf-compteurs{ flex:1; min-width:0; display:flex; flex-direction:column; gap:8px; }
.rf-score{ display:flex; align-items:baseline; gap:8px; }
.rf-score b{ font-family: var(--titre); font-weight:900; font-size:50px; line-height:.85; font-variant-numeric:tabular-nums; }
.rf-score span{ color: var(--brume); font-size:14px; }
.rf-chrono{ height:10px; border-radius:6px; background: var(--nuit); overflow:hidden; }
.rf-chrono i{ display:block; height:100%; background: var(--c-legendaire); transform-origin:left; transition:transform .1s linear; }
.rf-chrono.urgent i{ background: var(--c-rouge); }
.rf-temps{ font-size:13px; color: var(--brume); font-variant-numeric:tabular-nums; }
.rf-temps b{ color:#fff; }
.rf-form{ display:flex; gap:8px; }
.rf-form input{ flex:1; min-width:0; font:600 19px var(--texte, inherit); padding:12px 14px; border-radius:11px; border:2px solid rgba(169,188,212,.3); background: var(--nuit); color:#fff; }
.rf-form input:disabled{ opacity:.5; }
.rf-form input.non{ border-color: var(--c-rouge); animation: rfSecoue .35s; }
.rf-form input.oui{ border-color: var(--c-peucommun); }
@keyframes rfSecoue{ 20%,60%{ transform:translateX(-6px); } 40%,80%{ transform:translateX(6px); } }
.rf-retour{ min-height:20px; font-size:13.5px; color: var(--brume); }
.rf-retour.non{ color:#FF9A90; }
.rf-plaques{ display:flex; flex-wrap:wrap; gap:7px; }
.rf-plaque{ background:#1F4FA8; color:#fff; border:2px solid #fff; border-radius:5px; padding:3px 8px 2px; font-family: var(--titre); font-weight:800; font-size:16px; text-transform:uppercase; letter-spacing:.04em; line-height:1.2; animation: rfPose .25s ease-out; }
.rf-plaque small{ font-size:10.5px; opacity:.75; margin-left:5px; }
.rf-plaques.lui .rf-plaque{ background:#2B3A55; }
@keyframes rfPose{ from{ transform:translateY(-8px) scale(.9); opacity:0; } }
.rf-colonnes{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }
.rf-colonnes.seule{ grid-template-columns:1fr; }
@media (max-width: 560px){ .rf-colonnes{ grid-template-columns:1fr; } }
.rf-oubliees{ margin:0; font-size:13.5px; color: var(--brume); }
.rf-oubliees:empty{ display:none; }
.rf-oubliees b{ color:#fff; font-weight:600; }
.rf-mini-lettre{ align-self:center; width:34px; height:34px; border-radius:7px; background:#1F4FA8; border:2px solid #fff; display:grid; place-items:center; font-family: var(--titre); font-weight:900; font-size:22px; color:#fff; }
@media (prefers-reduced-motion: reduce){ .rf-plaque, .rf-form input.non{ animation:none; } .rf-chrono i{ transition:none; } }
"""

ecrire('app.js', js)
ecrire('style.css', css)
ecrire('index.html', html)
print(u'patch128 applique')
