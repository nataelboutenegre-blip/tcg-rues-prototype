# -*- coding: utf-8 -*-
u"""
patch182 — toucher une carte d'une vitrine l'ouvre en grand (inclinable,
retournable), chez soi comme chez les autres joueurs. Les infos dessous :
habitants, rareté, Terra ou Front, gentilé, le savais-tu. On revient ensuite
là où on était (fiche du joueur, grande vitrine).
Sur l'étagère du profil, la case « +N » ouvre toujours la grande vitrine.
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
assert 'patch182' not in js

# l'etagere : chaque carte porte son rang (sauf la case « +N »)
js = rempl(js, u"""    cases.push(c ? `<div class="vt-case${plus ? ' vt-a-plus' : ''}">${miniVitrine(c)}""",
u"""    cases.push(c ? `<div class="vt-case${plus ? ' vt-a-plus' : ''}"${plus ? '' : ` data-vt-carte="${i}"`}>${miniVitrine(c)}""", 'etagere')

# la grande vitrine : une carte touchee s'ouvre en grand, puis on y revient
js = rempl(js, u"""        ${cartes.map((c, i) => `<div class="vt-place"><span class="vt-rang">${i + 1}</span>${miniTerra({ ...c, exemplaires: 1 })}</div>`).join('')}""",
u"""        ${cartes.map((c, i) => `<div class="vt-place" data-vtg-carte="${i}"><span class="vt-rang">${i + 1}</span>${miniTerra({ ...c, exemplaires: 1 })}</div>`).join('')}""", 'grande cartes')
js = rempl(js, u"""    </div>`, (v) => { if(apres) apres(v); });
  document.querySelector('#fenetre .vt-grande').addEventListener('click', (e) => {
    const b = e.target.closest('[data-vtg]');
    if(b) fermer(b.dataset.vtg);
  });""",
u"""    </div>`, (v) => {
      if(typeof v === 'string' && v.startsWith('carte:')){   // patch182
        const c = cartes[Number(v.slice(6))];
        if(c) setTimeout(() => ouvrirCarteVitrine(c, pseudo,
          () => setTimeout(() => ouvrirGrandeVitrine(cartes, moi, pseudo, apres, source), 200)), 200);
        return;
      }
      if(apres) apres(v);
    });
  document.querySelector('#fenetre .vt-grande').addEventListener('click', (e) => {
    const b = e.target.closest('[data-vtg]');
    if(b){ fermer(b.dataset.vtg); return; }
    const c = e.target.closest('[data-vtg-carte]');
    if(c) fermer('carte:' + c.dataset.vtgCarte);
  });""", 'grande clic')

# depuis la fiche d'un joueur
js = rempl(js, u"""  const voir = e.target.closest('[data-vt-voir]');
  const modif = e.target.closest('[data-pr="vitrine"]');
  if(!voir && !(modif && profilEnCours.est_moi)) return;
  const p = profilEnCours;
  const cartes = p.vitrine || [];
  const src = sourceVitrine(voir || modif);
  if(fermerProfil) fermerProfil(null);
  setTimeout(() => {""",
u"""  const voir = e.target.closest('[data-vt-voir]');
  const modif = e.target.closest('[data-pr="vitrine"]');
  const uneCarte = e.target.closest('[data-vt-carte]');   // patch182
  if(!voir && !(modif && profilEnCours.est_moi)) return;
  const p = profilEnCours;
  const cartes = p.vitrine || [];
  const src = sourceVitrine(voir || modif);
  if(fermerProfil) fermerProfil(null);
  setTimeout(() => {
    const c = uneCarte && vitrineDe(cartes, src)[Number(uneCarte.dataset.vtCarte)];
    if(c){ ouvrirCarteVitrine(c, p.pseudo, () => setTimeout(() => { profilEnCours = p; rendreProfil(); }, 200)); return; }""", 'fiche joueur')

# depuis le panneau Profil
js = rempl(js, u"""  const src = sourceVitrine(e.target);
  if(e.target.closest('[data-pr="vitrine"]')) ouvrirChoixVitrine(vt, 'panneau', src);
  if(e.target.closest('[data-vt-voir]')) ouvrirGrandeVitrine(""",
u"""  const src = sourceVitrine(e.target);
  if(e.target.closest('[data-pr="vitrine"]')) ouvrirChoixVitrine(vt, 'panneau', src);
  const uneCarte = e.target.closest('[data-vt-carte]');   // patch182
  if(uneCarte){ const c = vitrineDe(vt, src)[Number(uneCarte.dataset.vtCarte)]; if(c) ouvrirCarteVitrine(c, (profilPanneau || {}).pseudo); return; }
  if(e.target.closest('[data-vt-voir]')) ouvrirGrandeVitrine(""", 'panneau')

# la carte en grand, pour une carte de vitrine (la sienne ou celle d'un autre)
js = rempl(js, u"""async function ouvrirCarteTerra(code){""",
u"""// patch182 : une carte de vitrine en grand. Pas de bouton d'action : elle
// peut appartenir a un autre joueur.
async function ouvrirCarteVitrine(e, pseudo, apres){
  const code = e.code;
  const nb = (x) => Number(x || 0).toLocaleString('fr-FR');
  const front = e.source === 'front';
  const rendre = (d) => {
    const gentile = d && d.gentile ? String(d.gentile).trim() : '';
    const faits = d ? faitsTries(d.faits) : null;
    const savais = faits === null ? '<p class="fc-attente">Recherche des faits…</p>'
      : !faits.length ? '' : '<h3>Le savais-tu ?</h3>' + faits.slice(0, 3).map((f, i) => `<div class="fc-fait${i ? '' : ' phare'}"><i>${i ? iconeFait(f.t) : '🏅'}</i><span>${i ? echapperTexte(f.t) : '<b>' + echapperTexte(f.t) + '</b>'}</span></div>`).join('');
    return `
    <div class="fenetre fiche fiche-terra ${e.tier.id}" data-tcode="${echapperTexte(code)}" role="dialog" aria-modal="true" aria-labelledby="ftNom">
      <button class="fc-fermer" data-ft="fermer" aria-label="Fermer">✕</button>
      <div class="fc-tete">${carte3dDebut(150, 225, 1.65)}${miniTerra({ ...e, exemplaires: 1 })}${carte3dFin()}</div>
      <div class="fc-corps">
        <h2 id="ftNom" class="fc-nom ${e.nom.length > 22 ? 'long' : ''}">${echapperTexte(e.nom)}</h2>
        <p class="fc-dep">${DEPT_NAMES[e.dept] ? echapperTexte(DEPT_NAMES[e.dept]) + ' (' + echapperTexte(e.dept) + ')' : echapperTexte(e.dept)}</p>
        ${gentile ? `<p class="fc-gent">les ${echapperTexte(gentile)}</p>` : ''}
        <div class="fc-chiffres">
          <div class="fc-ch"><b>${nb(e.pop)}</b><span>habitants</span></div>
          <div class="fc-ch"><b class="fc-rar">${e.tier.label}</b><span>${e.rank ? 'n° ' + nb(e.rank) + ' / ' + nb(e.tierSize) : 'rareté'}</span></div>
          <div class="fc-ch"><b>${front ? 'Front' : 'Terra'}</b><span>${e.aurore > 0 ? 'Aurore' : 'vitrine'}</span></div>
        </div>
        ${pseudo ? `<p class="fc-vitrine-de">Dans la vitrine de <b>${echapperTexte(pseudo)}</b></p>` : ''}
        ${savais}
      </div>
    </div>`;
  };
  const fermer = ouvrirFenetre(rendre(null), () => { if(apres) apres(); });
  const boite = document.querySelector('#fenetre .fiche-terra');
  if(boite){
    armerCarte3d(boite.querySelector('.c3d'));
    boite.addEventListener('click', (ev) => { if(ev.target.closest('[data-ft="fermer"]')) fermer(null); });
  }
  let d = {};
  try { d = await detailsCommune(code); } catch(err){ d = {}; }
  const ouverte = document.querySelector('#fenetre .fiche-terra[data-tcode="' + code + '"]');
  if(!ouverte) return;
  const tmp = document.createElement('div'); tmp.innerHTML = rendre(d);
  const neuf = tmp.querySelector('.fc-corps'), vieux = ouverte.querySelector('.fc-corps');
  if(neuf && vieux) vieux.replaceWith(neuf);
}

async function ouvrirCarteTerra(code){""", 'fonction')

css = lire('style.css')
assert 'patch182' not in css
css += u"""
/* patch182 : la carte de vitrine en grand */
.vt-case[data-vt-carte], .vt-place[data-vtg-carte]{ cursor:pointer; }
.fc-vitrine-de{ font-size:.78rem; color:var(--brume); margin:10px 0 0; text-align:center; }
.fc-vitrine-de b{ color:var(--c-legendaire); font-weight:600; }
"""
ecrire('app.js', js); ecrire('style.css', css)
print(u'patch182 appliqué')
