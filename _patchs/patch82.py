# -*- coding: utf-8 -*-
u"""
patch82 — Carte dézoomée : le département sous la souris (idée d'un joueur).

De loin, une commune ne fait que quelques pixels : le survol qui donnait son
nom n'apprenait rien. Tant que la carte est en vue « départements »
(zoom < SEUIL_CONTOURS) :
- ordinateur : le survol affiche le département, ses 3 premiers joueurs
  (pastille de couleur, part du département entier), ta part si tu n'es
  pas dans les 3, et la part de communes libres ;
- clic (ordinateur) ou toucher (téléphone) : la même fiche s'ouvre dans la
  bulle, avec un bouton « Zoomer ici ».
Les parts se calculent sur TOUTES les communes du département (décision de
Nataël, 7 octobre). Les totaux par département viennent de data/communes.json.
Dès qu'on zoome, on retrouve le survol et le clic des communes. Aucun SQL.
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

TOTAUX = u'01:391,02:797,03:316,04:197,05:161,06:161,07:335,08:447,09:325,10:431,11:433,12:282,13:134,14:526,15:245,16:359,17:462,18:286,19:277,21:698,22:344,23:255,24:503,25:563,26:362,27:585,28:363,29:277,2A:123,2B:234,30:349,31:586,32:458,33:534,34:341,35:332,36:241,37:272,38:512,39:492,40:327,41:267,42:320,43:250,44:207,45:325,46:312,47:319,48:145,49:176,50:444,51:610,52:426,53:240,54:590,55:493,56:249,57:725,58:309,59:647,60:680,61:381,62:887,63:463,64:545,65:469,66:226,67:514,68:366,69:274,70:536,71:563,72:351,73:273,74:279,75:20,76:707,77:507,78:259,79:252,80:771,81:314,82:195,83:152,84:151,85:253,86:265,87:195,88:506,89:423,90:101,91:194,92:36,93:39,94:47,95:183'

js = lire('app.js')

# --- 1. les outils : totaux, departement sous le point, statistiques ---------
js = rempl(js,
u'''function communeSousLePoint(xCss, yCss){''',
u'''// ---------- De loin : le departement sous le curseur (patch82) ----------
// Nombre de communes par departement (data/communes.json) : les parts se
// calculent sur le departement entier, communes libres comprises.
const COMMUNES_PAR_DEPT = Object.fromEntries('@@TOTAUX@@'
  .split(',').map(x => { const [d, n] = x.split(':'); return [d, Number(n)]; }));

function vueDepartements(){
  return mapZoom < SEUIL_CONTOURS && CONTOURS_DEPTS && typeof CONTOURS_DEPTS === 'object';
}
let ctxTestDept = null;
function departementSousLePoint(xCss, yCss){
  if(!vueDepartements()) return null;
  if(!ctxTestDept) ctxTestDept = document.createElement('canvas').getContext('2d');
  const p = ecranVersCarte(xCss, yCss);
  for(const dep in CONTOURS_DEPTS){
    if(ctxTestDept.isPointInPath(cheminDeptCanvas(dep, CONTOURS_DEPTS[dep]), p.x, p.y)) return dep;
  }
  return null;
}
// Qui tient quoi dans un departement : toutes les communes connues, sans
// tenir compte des calques affiches.
function statsDepartement(dep){
  const total = COMMUNES_PAR_DEPT[dep] || 0;
  const parJoueur = new Map();
  const compter = (id, pseudo) => {
    const j = parJoueur.get(id) || { id, pseudo, n: 0 };
    j.n++; parJoueur.set(id, j);
  };
  for(const c of collectionMap.values()) if(c.dept === dep) compter(ID_MOI, 'Toi');
  for(const c of othersMap.values()) if(c.dept === dep) compter(c.joueurId, c.pseudo);
  const joueurs = [...parJoueur.values()].sort((a, b) => b.n - a.n);
  const pris = joueurs.reduce((s, j) => s + j.n, 0);
  const couleurs = (CV.reperage && CV.reperage.joueurs) || new Map();
  for(const j of joueurs){
    const k = couleurs.get(j.id);
    j.couleur = k ? k.couleur : (j.id === ID_MOI ? COULEUR_MOI : '#8FA4BF');
    j.moi = j.id === ID_MOI;
  }
  return { dep, total: Math.max(total, pris), pris, joueurs };
}
function partDept(n, total){
  if(!total) return '0 %';
  const p = 100 * n / total;
  if(p > 0 && p < 0.1) return '< 0,1 %';
  return (p < 10 ? p.toFixed(1).replace('.', ',') : Math.round(p)) + ' %';
}
// les 3 premiers, plus moi si je n'y suis pas
function lignesDept(s){
  const tete = s.joueurs.slice(0, 3);
  const moi = s.joueurs.find(j => j.moi);
  if(moi && !tete.includes(moi)) tete.push(moi);
  return tete;
}

function communeSousLePoint(xCss, yCss){''', 'outils')

# --- 2. le survol --------------------------------------------------------------
js = rempl(js,
u'''    const rect = cv.getBoundingClientRect();
    const t = communeSousLePoint(e.clientX - rect.left, e.clientY - rect.top);
    if(!t){ bulle.hidden = true; CV.survol = null; return; }
    CV.survol = t.commune;
    bulle.hidden = false;
    bulle.textContent = t.commune.nom + ' (' + t.commune.dept + '), '
      + LIBELLE_TIER[t.commune.tier] + ', '
      + (t.joueur.moi ? 'à toi' : 'à ' + t.joueur.pseudo);''',
u'''    const rect = cv.getBoundingClientRect();
    if(vueDepartements()){
      // de loin : le departement, pas une commune de quelques pixels
      CV.survol = null;
      const dep = departementSousLePoint(e.clientX - rect.left, e.clientY - rect.top);
      if(!dep){ bulle.hidden = true; bulle.dataset.dep = ''; return; }
      if(bulle.dataset.dep !== dep){
        const s = statsDepartement(dep);
        bulle.dataset.dep = dep;
        bulle.classList.add('dept');
        bulle.innerHTML = `<b class="ib-titre">${echapperHtml(DEPT_NAMES[dep] || dep)} (${echapperHtml(dep)})</b>`
          + lignesDept(s).map(j => `<span class="ib-j${j.moi ? ' moi' : ''}"><i style="background:${j.couleur}"></i>${echapperHtml(j.pseudo)}<em>${partDept(j.n, s.total)}</em></span>`).join('')
          + `<span class="ib-libre">Libres<em>${partDept(s.total - s.pris, s.total)}</em></span>`;
      }
      bulle.hidden = false;
    } else {
    const t = communeSousLePoint(e.clientX - rect.left, e.clientY - rect.top);
    if(!t){ bulle.hidden = true; CV.survol = null; return; }
    CV.survol = t.commune;
    bulle.hidden = false;
    bulle.classList.remove('dept');
    bulle.dataset.dep = '';
    bulle.textContent = t.commune.nom + ' (' + t.commune.dept + '), '
      + LIBELLE_TIER[t.commune.tier] + ', '
      + (t.joueur.moi ? 'à toi' : 'à ' + t.joueur.pseudo);
    }''', 'survol')

# --- 3. le clic / toucher --------------------------------------------------------
js = rempl(js,
u'''    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    const t = communeSousLePoint(x, y);
    if(t) ouvrirPanneau(t.commune.code, x, y);
    else fermerPanneau();''',
u'''    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    if(vueDepartements()){
      const dep = departementSousLePoint(x, y);
      if(dep) ouvrirPanneauDept(dep, x, y);
      else fermerPanneau();
      return;
    }
    const t = communeSousLePoint(x, y);
    if(t) ouvrirPanneau(t.commune.code, x, y);
    else fermerPanneau();''', 'clic')

# --- 4. la fiche du departement dans la bulle -----------------------------------
js = rempl(js,
u'''function ouvrirPanneau(code, xCss, yCss){''',
u'''let panneauDept = null;
const ICONE_LOUPE_PC = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5 5M8 10.5h5M10.5 8v5"/></svg>';
function ouvrirPanneauDept(dep, xCss, yCss){
  const el = document.getElementById('mapPanneau');
  if(!el) return;
  const s = statsDepartement(dep);
  const vus = lignesDept(s);
  panneauCommune = null;
  panneauDept = dep;
  panneauAncre = { x: xCss, y: yCss };
  const lignes = vus.map(j => `
    <div class="pc-ligne pd-j${j.moi ? ' moi' : ''}">
      <span><i class="pd-pastille" style="background:${j.couleur}"></i>${j.moi ? '<b>Toi</b>'
        : `<button class="pc-proprio" data-profil="${echapperHtml(j.id)}">${echapperHtml(j.pseudo)}</button>`}</span>
      <b>${partDept(j.n, s.total)} <small>· ${nbFr(j.n)}</small></b>
    </div>`).join('');
  const autres = s.joueurs.length - vus.length;
  el.innerHTML = `
    <div class="pc-tete">
      <div class="pc-titre">
        <b>${echapperHtml(DEPT_NAMES[dep] || dep)}</b>
        <span class="pc-dep">${nbFr(s.total)} communes</span>
      </div>
      <span class="pc-rarete pd-num">${echapperHtml(dep)}</span>
      <button class="pc-fermer" data-pc="fermer" aria-label="Fermer">&times;</button>
    </div>
    <div class="pc-lignes">
      ${s.joueurs.length ? lignes : '<p class="pc-note">Personne n’a encore de commune ici.</p>'}
      ${autres > 0 ? `<div class="pc-ligne"><span>${autres} autre${autres > 1 ? 's' : ''} joueur${autres > 1 ? 's' : ''}</span><b></b></div>` : ''}
      <div class="pc-ligne pd-libre"><span>Libres</span><b>${partDept(s.total - s.pris, s.total)} <small>· ${nbFr(s.total - s.pris)}</small></b></div>
    </div>
    <div class="pc-actions"><button class="pc-action" data-pc="zoom-dept">${ICONE_LOUPE_PC}Zoomer ici</button></div>`;
  el.hidden = false;
  const wrap = document.getElementById('mapWrap');
  if(wrap) wrap.classList.add('panneau-ouvert');
  el.scrollTop = 0;
  placerPanneau(el, xCss, yCss);
}

// Cadrer un departement : sa boite englobante, avec de la marge.
function zoomerSurDept(dep){
  const poly = CONTOURS_DEPTS && CONTOURS_DEPTS[dep];
  const wrap = document.getElementById('mapWrap');
  if(!poly || !wrap || !mapBounds) return;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for(const anneau of poly) for(const [lon, lat] of anneau){
    const p = project(lat, lon), x = p.x * MAP_W, y = p.y * MAP_H;
    if(x < x0) x0 = x;
    if(x > x1) x1 = x;
    if(y < y0) y0 = y;
    if(y > y1) y1 = y;
  }
  const L = wrap.clientWidth, H = wrap.clientHeight, ech = echelleCarte();
  const z = Math.min(L * 0.8 / ((x1 - x0) * ech), H * 0.8 / ((y1 - y0) * ech));
  mapZoom = Math.min(zoomMaxCarte(), Math.max(SEUIL_CONTOURS * 1.05, z));
  mapPanX = L / 2 - (x0 + x1) / 2 * ech * mapZoom;
  mapPanY = H / 2 - (y0 + y1) / 2 * ech * mapZoom;
  applyMapTransform();
  renderMapOverlay();
  demanderDessin();
}

function ouvrirPanneau(code, xCss, yCss){''', 'ouvrirPanneauDept')

js = rempl(js,
u'''  panneauCommune = code;
  if(typeof xCss === 'number' && typeof yCss === 'number'){''',
u'''  panneauCommune = code;
  panneauDept = null;
  if(typeof xCss === 'number' && typeof yCss === 'number'){''', 'ouvrirPanneau reset')
js = rempl(js,
u'''  panneauCommune = null;
  panneauAncre = null;
  panneauDeplace = null;
}''',
u'''  panneauCommune = null;
  panneauDept = null;
  panneauAncre = null;
  panneauDeplace = null;
}''', 'fermerPanneau')
js = rempl(js,
u'''  const quoi = b.dataset.pc;
  const code = panneauCommune;''',
u'''  const quoi = b.dataset.pc;
  if(quoi === 'zoom-dept' && panneauDept){ const d = panneauDept; fermerPanneau(); zoomerSurDept(d); return; }
  const code = panneauCommune;''', 'dispatcher')
js = js.replace(u'@@TOTAUX@@', TOTAUX)
ecrire('app.js', js)

css = lire('style.css')
css += u'''

/* ---------- patch82 : de loin, le departement sous le curseur ---------- */
.map-infobulle.dept{ white-space:normal; min-width:170px; padding:8px 11px; display:flex; flex-direction:column; gap:3px; }
.map-infobulle .ib-titre{ font-weight:700; font-size:.84rem; margin-bottom:2px; }
.map-infobulle .ib-j, .map-infobulle .ib-libre{ display:flex; align-items:center; gap:7px; font-size:.76rem; color:#DCE6F2; }
.map-infobulle .ib-j i{ width:9px; height:9px; border-radius:50%; flex-shrink:0; }
.map-infobulle .ib-j.moi{ font-weight:700; color:#fff; }
.map-infobulle em{ margin-left:auto; padding-left:12px; font-style:normal; font-weight:600; font-variant-numeric:tabular-nums; }
.map-infobulle .ib-libre{ color:#8FA4BF; border-top:1px solid rgba(169,188,212,.18); padding-top:4px; margin-top:2px; }
.pd-pastille{ display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:7px; vertical-align:0; }
.pd-j b small, .pd-libre b small{ font-weight:400; color:#8FA4BF; }
.pd-j.moi span b{ color:#fff; }
.pc-rarete.pd-num{ background:rgba(169,188,212,.16); color:#DCE6F2; }
'''
ecrire('style.css', css)
print(u'patch82 : OK')
