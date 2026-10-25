# -*- coding: utf-8 -*-
u"""
patch192 — QG : on choisit son mini-jeu (apercu valide le 26 octobre).
 - une rangee des 4 jeux en haut, avec leur etat du jour et la pastille des defis ;
 - le jeu choisi s'affiche seul, en grand, avec une phrase qui explique le jeu ;
 - le classement et les dernieres parties a cote ne montrent que ce jeu
   (les filtres disparaissent) ; Commune du jour : pas de classement (solo) ;
 - les defis recus restent visibles en haut ; le choix est retenu.
Aucun SQL.
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
assert 'qgJeuChoisi' not in js, u'patch192 deja applique'
js = rempl(js, u"""function renderQGListes(){""", u"""// ---------- patch192 : on choisit son mini-jeu dans le QG ----------
const QG_JEUX = [
  { id: 'cdj', carte: 'qgCdj', etat: 'qgCdjEtat', nom: 'Commune du jour',
    explic: 'La même commune mystère pour tout le monde : six essais pour la trouver. Chaque essai te dit à quelle distance tu es et dans quelle direction chercher, chaque erreur dévoile un indice.' },
  { id: 'pom', carte: 'qgPom', etat: 'qgPomEtat', nom: 'Plus ou moins',
    explic: 'Deux communes s\\'affichent : choisis celle qui a le plus d\\'habitants. Dix duels d\\'affilée, seul pour la partie du jour ou contre un joueur en duel classé.' },
  { id: 'radar', carte: 'qgRadar', etat: 'qgRestants', nom: 'Radar',
    explic: 'Une commune s\\'affiche : place-la sur la carte de France. Le joueur qui a le moins de kilomètres d\\'écart au total gagne le duel.' },
  { id: 'rafale', carte: 'qgRafale', etat: 'rfEtiquette', nom: 'Rafale',
    explic: 'Une lettre s\\'affiche : tape le plus de communes qui commencent par cette lettre en 30 secondes. Celui qui en trouve le plus gagne.' },
];
let qgJeuChoisi = (() => { try{ const v = localStorage.getItem('tf-qg-jeu'); return ['cdj', 'pom', 'radar', 'rafale'].includes(v) ? v : 'radar'; }catch(e){ return 'radar'; } })();
function choixQG(){
  const panneau = document.getElementById('panel-qg');
  const grille = panneau ? panneau.querySelector('.qg-grille') : null;
  if(!grille) return;
  panneau.classList.add('qg-choix-actif');
  // une fois : la rangee des jeux, les phrases, les reperes des blocs
  let rangee = document.getElementById('qgChoix');
  if(!rangee){
    rangee = document.createElement('div');
    rangee.id = 'qgChoix';
    rangee.className = 'qg-choix';
    rangee.setAttribute('role', 'group');
    rangee.setAttribute('aria-label', 'Choisir un mini-jeu');
    grille.insertAdjacentElement('beforebegin', rangee);
    rangee.addEventListener('click', (e) => {
      const b = e.target.closest('[data-qgjeu]');
      if(!b || b.dataset.qgjeu === qgJeuChoisi) return;
      qgJeuChoisi = b.dataset.qgjeu;
      try{ localStorage.setItem('tf-qg-jeu', qgJeuChoisi); }catch(err){}
      renderQGListes();
    });
    for(const j of QG_JEUX){
      const c = document.getElementById(j.carte);
      const tete = c ? c.querySelector('.qg-tete') : null;
      if(tete && !c.querySelector('.qg-explic')) tete.insertAdjacentHTML('afterend', `<p class="qg-explic">${j.explic}</p>`);
    }
    const cl = document.getElementById('qgClassement');
    if(cl && cl.closest('.qg-carte')) cl.closest('.qg-carte').id = 'qgClassementBloc';
    const note = document.createElement('div');
    note.className = 'qg-carte';
    note.id = 'qgCdjNote';
    note.innerHTML = '<h3 class="qg-h3">Commune du jour</h3><p class="qg-petit">Pas de classement : c\\'est un défi solo, la même commune pour tout le monde. Ta série et tes points du jour sont sur la carte du jeu.</p>';
    grille.appendChild(note);
  }
  // un jeu indisponible (Plus ou moins cache) ne se choisit pas
  const dispo = QG_JEUX.filter(j => { const c = document.getElementById(j.carte); return c && !c.hidden; });
  if(!dispo.some(j => j.id === qgJeuChoisi) && dispo.length) qgJeuChoisi = dispo.some(j => j.id === 'radar') ? 'radar' : dispo[0].id;
  const defis = (jeu) => { try{ const e = jeu === 'radar' ? radarEtat : jeu === 'rafale' ? rafaleEtat : null; return e && e.defis_recus ? e.defis_recus.length : 0; }catch(err){ return 0; } };
  rangee.innerHTML = dispo.map(j => {
    const c = document.getElementById(j.carte);
    const ico = c.querySelector('.qg-ico') ? c.querySelector('.qg-ico').innerHTML : '';
    const et = document.getElementById(j.etat);
    const etat = et ? et.textContent.trim() : '';
    const n = defis(j.id);
    return `<button type="button" class="qg-choix-jeu" data-qgjeu="${j.id}" aria-pressed="${j.id === qgJeuChoisi}">
      <span class="qg-ico" aria-hidden="true">${ico}</span><span><b>${j.nom}</b>${etat ? `<small>${echapperTexte(etat)}</small>` : ''}</span>
      ${n ? `<i class="qg-choix-pastille" aria-label="${n} défi${n > 1 ? 's' : ''}">${n}</i>` : ''}</button>`;
  }).join('');
  for(const j of QG_JEUX){ const c = document.getElementById(j.carte); if(c) c.classList.toggle('qg-pas-choisi', j.id !== qgJeuChoisi); }
  const solo = qgJeuChoisi === 'cdj';
  panneau.classList.toggle('qg-solo', solo);
  if(!solo){ qgFiltreHist = qgJeuChoisi; qgFiltreCl = qgJeuChoisi; }
  const nom = (QG_JEUX.find(j => j.id === qgJeuChoisi) || {}).nom || '';
  const titreD = document.querySelector('#qgDerniersBloc .qg-h3');
  if(titreD) titreD.innerHTML = `Tes dernières parties <small>${nom}</small>`;
  const titreC = document.querySelector('#qgClassementBloc .qg-h3');
  if(titreC) titreC.innerHTML = `Classement <small>${nom}</small>`;
}
function renderQGListes(){
  choixQG();   // patch192""", 'choix')
ecrire('app.js', js)

css = lire('style.css')
assert 'patch192' not in css, u'patch192 deja applique (css)'
css += u"""

/* ---------- patch192 : le QG, un jeu choisi en grand ---------- */
.qg-choix{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:10px; margin-top:16px; width:100%; }
@media (max-width: 720px){ .qg-choix{ grid-template-columns:repeat(2, minmax(0,1fr)); } }
.qg-choix-jeu{ position:relative; display:grid; grid-template-columns:36px minmax(0,1fr); gap:10px; align-items:center; text-align:left; min-height:64px;
  background: var(--nuit-2); border:1px solid rgba(169,188,212,.18); border-radius:14px; padding:12px; color:#fff; font:inherit; cursor:pointer; }
.qg-choix-jeu:hover{ border-color: rgba(169,188,212,.38); }
.qg-choix-jeu:focus-visible{ outline:2px solid var(--c-legendaire); outline-offset:2px; }
.qg-choix-jeu[aria-pressed="true"]{ border-color: var(--c-legendaire); background: linear-gradient(160deg, rgba(240,180,41,.14), var(--nuit-2)); box-shadow: inset 0 0 0 1px var(--c-legendaire); }
.qg-choix-jeu .qg-ico{ width:36px; height:36px; border-radius:10px; }
.qg-choix-jeu .qg-ico svg{ width:20px; height:20px; }
.qg-choix-jeu b{ display:block; font-family: var(--titre); font-size:1.12rem; font-weight:800; line-height:1.05; }
.qg-choix-jeu small{ display:block; margin-top:2px; font-size:.74rem; font-weight:700; color: var(--c-legendaire); }
.qg-choix-pastille{ position:absolute; top:-6px; right:-6px; min-width:20px; height:20px; padding:0 6px; border-radius:10px; background:#E5484D; color:#fff;
  font-style:normal; font-size:.7rem; font-weight:700; display:grid; place-items:center; }
.qg-explic{ margin:0; color: var(--brume); font-size:.9rem; line-height:1.5; max-width:62ch; }

.qg-choix-actif .qg-grille{ grid-template-columns:minmax(0,1.35fr) minmax(0,1fr); }
.qg-choix-actif .qg-jeux{ display:block; grid-column:1; grid-row:2 / span 2; }
.qg-choix-actif #qgDefisBloc{ grid-column:1 / -1; grid-row:1; }
.qg-choix-actif #qgDerniersBloc{ grid-column:2; grid-row:2; }
.qg-choix-actif #qgClassementBloc{ grid-column:2; grid-row:3; }
.qg-choix-actif #qgCdjNote{ grid-column:2; grid-row:2; }
.qg-choix-actif .qg-jeux .qg-carte.qg-pas-choisi{ display:none; }
.qg-choix-actif .qg-jeux .qg-carte{ padding:22px; gap:16px; border-color: rgba(240,180,41,.35); }
.qg-choix-actif .qg-jeux .qg-titre h2{ font-size:2rem; }
.qg-choix-actif .qg-jeux .qg-ico{ width:56px; height:56px; }
.qg-choix-actif .qg-filtre{ display:none; }
.qg-h3 small{ font-family: var(--texte); font-size:.74rem; font-weight:500; color: var(--brume); text-transform:none; letter-spacing:0; margin-left:6px; }
#qgCdjNote{ display:none; }
.qg-choix-actif.qg-solo #qgCdjNote{ display:flex; }
.qg-choix-actif.qg-solo #qgDerniersBloc, .qg-choix-actif.qg-solo #qgClassementBloc{ display:none; }
@media (max-width: 900px){
  .qg-choix-actif .qg-grille{ grid-template-columns:minmax(0,1fr); }
  .qg-choix-actif .qg-jeux, .qg-choix-actif #qgDefisBloc, .qg-choix-actif #qgDerniersBloc,
  .qg-choix-actif #qgClassementBloc, .qg-choix-actif #qgCdjNote{ grid-column:1; grid-row:auto; }
}
"""
ecrire('style.css', css)
print(u'patch192 applique. Lancer : python3 maj-version.py')
