# -*- coding: utf-8 -*-
u"""
patch102 — Contrat Terra : le lot regroupé (« Faimbe ×6 »).
(saison 2, CACHÉ tant que SAISON2 = false). Aucun SQL.

- Une ligne par commune avec son nombre de doublons dans le lot, boutons
  − et + (dans la limite de ses doublons et des 10 du contrat).
- Moins de 10 : « + Choisir N doublons de plus » ouvre la liste des
  communes (doublons restants affichés) ; « Signer » attend d'en avoir 10.
Rien ne change en saison 1.
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
assert 'renderLotTerra' not in js, u'patch102 deja applique'

js = rempl(js, u"""  if(signer){ signer.hidden = false; signer.disabled = contratEnCours; }

  // dire « favoris exclus »""", u"""  if(signer){ signer.hidden = false; signer.disabled = contratEnCours || contratLot.length !== contratChoisi.n; }

  // dire « favoris exclus »""", 'signer')
js = rempl(js, u"""  lot.innerHTML = contratLot.map((x, i) => `
    <div class="ct-l ${contratChoisi.de}">""", u"""  if(ctTerra()) renderLotTerra(lot);
  else lot.innerHTML = contratLot.map((x, i) => `
    <div class="ct-l ${contratChoisi.de}">""", 'lot')

js = rempl(js, u"""// ---------- Bandeaux qu'on peut fermer ----------""", u"""// ---------- patch102 : le lot Terra regroupe par commune ----------
function renderLotTerra(lot){
  const groupes = [];
  for(const x of contratLot){
    let g = groupes.find(y => y.code === x.commune_code);
    if(!g){ g = { code: x.commune_code, x, n: 0 }; groupes.push(g); }
    g.n++;
  }
  const manque = contratChoisi.n - contratLot.length;
  lot.innerHTML = groupes.map(g => `
    <div class="ct-l ${contratChoisi.de} ct-gr">
      <span class="pt"></span>
      <span class="tx"><span class="nm"><i>${echapperTexte(g.x.nom || g.code)}</i>${badgeDept(g.x.departement)}</span><span class="hb">${g.n} de tes ${g.x.dispo} doublon${g.x.dispo > 1 ? 's' : ''}</span></span>
      <span class="ct-qte"><button type="button" data-ct-moins="${echapperTexte(g.code)}" aria-label="Un de moins">−</button><b>×${g.n}</b><button type="button" data-ct-plus="${echapperTexte(g.code)}" aria-label="Un de plus" ${g.n >= g.x.dispo || manque <= 0 ? 'disabled' : ''}>+</button></span>
    </div>`).join('')
    + (manque > 0 ? `<button type="button" class="ct-ajout" data-ct-ajout>+ Choisir ${manque} doublon${manque > 1 ? 's' : ''} de plus</button>` : '');
}

function ctUniteLibre(code){
  return (contratDispo[contratChoisi.de] || []).find(u => u.commune_code === code && !contratLot.some(l => l.cle === u.cle));
}

function ajouterDoublonTerra(){
  if(!contratChoisi) return;
  const toutes = (contratDispo[contratChoisi.de] || []).filter(x => x.cle.endsWith('#0'));
  const dansLot = (code) => contratLot.filter(x => x.commune_code === code).length;
  const fermer = ouvrirFenetre(`
    <div class="fenetre ct-pick" role="dialog" aria-modal="true" aria-labelledby="ctPickT">
      <h2 id="ctPickT">Ajouter un doublon</h2>
      <p class="ct-sst">${ctNb(toutes.length)} commune${toutes.length > 1 ? 's' : ''} avec des doublons</p>
      <input type="search" id="ctRech" autocomplete="off" placeholder="Nom ou département…" aria-label="Chercher une commune">
      <div class="ct-liste" id="ctPickL"></div>
      <div class="ct-pkp"><button type="button" id="ctPickA">Annuler</button></div>
    </div>`);
  const champ = document.getElementById('ctRech');
  const liste = document.getElementById('ctPickL');
  const dessiner = () => {
    const m = sansAccents(champ.value.trim());
    const vus = m ? toutes.filter(x => correspondRecherche(x.nom || x.commune_code, x.departement, m)) : toutes;
    if(!vus.length){ liste.innerHTML = '<p class="ct-vide">Aucune commune ne correspond.</p>'; return; }
    liste.innerHTML = vus.slice(0, 300).map(x => {
      const n = dansLot(x.commune_code);
      const plein = n >= x.dispo;
      return `<button type="button" class="ct-o ${contratChoisi.de}" ${plein ? 'disabled' : ''} data-code="${echapperTexte(x.commune_code)}">
        <span class="pt"></span>
        <span class="tx"><span class="nm"><i>${echapperTexte(x.nom || x.commune_code)}</i>${badgeDept(x.departement)}</span><span class="hb">${x.dispo} doublon${x.dispo > 1 ? 's' : ''}</span></span>
        ${n ? `<span class="dj">${n} dans le lot</span>` : ''}
      </button>`;
    }).join('');
  };
  dessiner();
  champ.addEventListener('input', dessiner);
  document.getElementById('ctPickA').addEventListener('click', () => fermer(null));
  liste.addEventListener('click', (e) => {
    const b = e.target.closest('.ct-o');
    if(!b || b.disabled) return;
    const u = ctUniteLibre(b.dataset.code);
    if(u && contratLot.length < contratChoisi.n) contratLot.push(u);
    fermer(null);
    renderContrat();
  });
  if(!/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) champ.focus();
}

document.getElementById('ctLot').addEventListener('click', (e) => {
  const moins = e.target.closest('[data-ct-moins]');
  if(moins){
    const code = moins.dataset.ctMoins;
    for(let i = contratLot.length - 1; i >= 0; i--){
      if(contratLot[i].commune_code === code){ contratLot.splice(i, 1); break; }
    }
    renderContrat();
    return;
  }
  const plus = e.target.closest('[data-ct-plus]');
  if(plus && !plus.disabled){
    const u = ctUniteLibre(plus.dataset.ctPlus);
    if(u && contratLot.length < contratChoisi.n) contratLot.push(u);
    renderContrat();
    return;
  }
  if(e.target.closest('[data-ct-ajout]')) ajouterDoublonTerra();
});

// ---------- Bandeaux qu'on peut fermer ----------""", 'fonctions')
ecrire('app.js', js)

css = lire('style.css')
assert '.ct-qte' not in css
css += u"""
/* patch102 : lot Terra regroupe */
.ct-l.ct-gr .hb{ white-space:normal; }
.ct-qte{ display:inline-flex; align-items:center; gap:6px; flex-shrink:0; }
.ct-qte b{ min-width:28px; text-align:center; font-family: var(--titre); font-size:1rem; }
.ct-l .ct-qte button{ width:28px; height:28px; padding:0; border-radius:8px; font-size:1rem; font-weight:800; line-height:1; }
.ct-l .ct-qte button:disabled{ opacity:.35; cursor:default; }
.ct-ajout{ grid-column:1 / -1; border:1px dashed rgba(169,188,212,.45); background:transparent; color: var(--brume); border-radius:10px; padding:10px; font:inherit; font-size:.8rem; font-weight:700; cursor:pointer; }
"""
ecrire('style.css', css)
print(u'patch102 applique')
