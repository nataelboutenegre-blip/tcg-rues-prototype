# -*- coding: utf-8 -*-
u"""
patch154 — contrats en lot (idée de Sokste, aperçu validé le 23 octobre).

- « Combien de contrats ? » ×1 / ×2 / ×5 / ×10, seulement ce qui est signable.
- ×1 : inchangé (lot modifiable, défilé).
- Au-delà : le lot prend les premières du palier dans l'ordre du serveur (Front :
  les moins peuplées, favoris et exclusions déjà retirés ; Terra : les doublons
  les plus nombreux d'abord). Résumé + liste dépliable, monuments comptés.
- Signature : un appel par contrat, l'un après l'autre (rien à changer côté
  serveur). Une erreur arrête la série ; les contrats déjà signés restent.
- Révélation : une grille des cartes obtenues, qui apparaissent l'une après
  l'autre ; en Terra, les nouvelles sont entourées d'or.
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

# ---------------------------------------------------------------- index.html
h = lire('index.html')
assert 'ctCombien' not in h, u'patch154 deja applique'
h = rempl(h, u'''      <div class="ct-taux" id="ctTaux"></div>
''', u'''      <div class="ct-taux" id="ctTaux"></div>
      <div class="ct-combien" id="ctCombien" hidden></div>
''', 'combien')
ecrire('index.html', h)

# ---------------------------------------------------------------- style.css
css = lire('style.css')
css = rempl(css, u"  /* ---------- Mot de passe oublié ---------- */", u"""  /* ---------- patch154 : contrats en lot ---------- */
  .ct-combien{ background: var(--nuit-2); border:1px solid rgba(169,188,212,0.16); border-radius:14px; padding:12px 14px; margin-bottom:12px; }
  .ct-combien[hidden]{ display:none; }
  .ct-cb-t{ display:flex; justify-content:space-between; align-items:baseline; gap:10px; margin-bottom:9px; flex-wrap:wrap; }
  .ct-cb-t b{ font:700 .68rem/1 var(--texte); letter-spacing:.1em; text-transform:uppercase; color: var(--brume); }
  .ct-cb-t span{ font-size:.75rem; color:#7F91AB; }
  .ct-puces{ display:flex; gap:7px; flex-wrap:wrap; }
  .ct-puces button{ appearance:none; border:1px solid rgba(169,188,212,.3); background: var(--nuit); color:#fff; font:800 1.05rem/1 var(--titre); letter-spacing:.03em; border-radius:10px; padding:9px 14px; min-height:44px; min-width:58px; cursor:pointer; }
  .ct-puces button small{ display:block; font:500 .66rem/1.2 var(--texte); color: var(--brume); margin-top:3px; letter-spacing:0; }
  .ct-puces button[aria-pressed="true"]{ background: var(--c-legendaire); color: var(--encre); border-color: var(--c-legendaire); }
  .ct-puces button[aria-pressed="true"] small{ color: var(--encre); }
  .ct-puces button:disabled{ opacity:.35; cursor:default; }
  .ct-puces button:focus-visible{ outline:2px solid #fff; outline-offset:2px; }
  .ct-resume{ grid-column:1 / -1; display:grid; gap:10px; }
  .ct-res-ch{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:8px; }
  .ct-res-ch div{ background: var(--nuit); border-radius:10px; padding:9px 10px; min-width:0; }
  .ct-res-ch b{ display:block; font:900 1.4rem/1 var(--titre); }
  .ct-res-ch span{ font-size:.7rem; color:#7F91AB; }
  .ct-res-liste{ background: var(--nuit); border-radius:10px; padding:9px 11px; }
  .ct-res-liste summary{ cursor:pointer; font-size:.8rem; color: var(--brume); }
  .ct-res-noms{ display:flex; flex-wrap:wrap; gap:5px; margin-top:9px; max-height:170px; overflow:auto; }
  .ct-res-noms span{ font-size:.72rem; background: var(--nuit-2); border-radius:6px; padding:3px 7px; color: var(--papier); }
  .ct-res-astuce{ font-size:.75rem; color:#7F91AB; margin:0; }
  .fenetre.contrat-lot{ width:min(820px, 94vw); max-width:none; }
  .ctl-haut{ text-align:center; margin-bottom:12px; }
  .ctl-haut h3{ margin:0; font-family: var(--titre); font-weight:900; font-size:1.7rem; line-height:1; }
  .ctl-haut p{ margin:6px 0 0; color: var(--brume); font-size:.84rem; }
  .ctl-grille{ display:grid; grid-template-columns:repeat(auto-fill, minmax(118px, 1fr)); gap:9px; max-height:min(62vh, 560px); overflow:auto; padding:4px; }
  .ctl-grille .mini{ width:100%; opacity:0; transform: translateY(10px) scale(.94); transition: opacity .3s, transform .35s cubic-bezier(.2,.9,.3,1.25); }
  .ctl-grille .mini.on{ opacity:1; transform:none; }
  .ctl-grille .mini.neuve{ box-shadow:0 0 0 2px var(--c-legendaire), 0 8px 16px rgba(0,0,0,0.35); }
  .ctl-pied{ margin-top:14px; }
  @media (prefers-reduced-motion: reduce){ .ctl-grille .mini{ transition:none; opacity:1; transform:none; } }
  /* ---------- Mot de passe oublié ---------- */""", 'css')
ecrire('style.css', css)

# ---------------------------------------------------------------- app.js
js = lire('app.js')
assert 'contratNb' not in js, u'patch154 deja applique'

js = rempl(js, u"""let contratSautes = 0;
""", u"""let contratSautes = 0;
let contratNb = 1;                // patch154 : combien de contrats d'un coup
const CT_NB_CHOIX = [1, 2, 5, 10];
const ctMaxNb = () => contratChoisi
  ? Math.min(10, Math.floor((contratDispo[contratChoisi.de] || []).length / contratChoisi.n)) : 0;
""", 'etat')

# le lot : n x nb
js = rempl(js, u"""  contratLot = (contratDispo[contratChoisi.de] || []).slice(0, contratChoisi.n);
}""", u"""  contratNb = Math.max(1, Math.min(contratNb, ctMaxNb()));   // patch154
  contratLot = (contratDispo[contratChoisi.de] || []).slice(0, contratChoisi.n * contratNb);
}""", 'composerLot')

# rendu : sélecteur, bouton, résumé, avertissement
js = rempl(js, u"""  if(signer){ signer.hidden = false; signer.disabled = contratEnCours || contratLot.length !== contratChoisi.n; }""",
u"""  const total = contratChoisi.n * contratNb;   // patch154
  if(signer){
    signer.hidden = false;
    signer.disabled = contratEnCours || contratLot.length !== total;
    if(!contratEnCours) signer.textContent = contratNb > 1 ? `Signer les ${contratNb} contrats` : 'Signer le contrat';
  }
  renderCombien();""", 'signer')
js = rempl(js, u"""  document.getElementById('ctInfo').textContent = ctTerra()
    ? `${contratChoisi.n} doublons, les plus nombreux d'abord`
    : `${contratChoisi.n} communes, les moins peuplées — favoris`""", u"""  document.getElementById('ctInfo').textContent = ctTerra()
    ? `${total} doublons, les plus nombreux d'abord`
    : `${total} communes, les moins peuplées — favoris`""", 'info')
js = rempl(js, u"""  if(ctTerra()) renderLotTerra(lot);
  else lot.innerHTML = contratLot.map((x, i) => `""", u"""  if(contratNb > 1) lot.innerHTML = resumeLot();   // patch154
  else if(ctTerra()) renderLotTerra(lot);
  else lot.innerHTML = contratLot.map((x, i) => `""", 'lot')
js = rempl(js, u"""    ? `Les ${contratChoisi.n} doublons sont échangés, c'est définitif. Tu gardes au moins un exemplaire de chaque commune.`
    : `Les ${contratChoisi.n} communes sacrifiées retournent au pot. C'est définitif.`""", u"""    ? `Les ${total} doublons sont échangés, c'est définitif. Tu gardes au moins un exemplaire de chaque commune.`
    : `Les ${total} communes sacrifiées retournent au pot. C'est définitif.`""", 'avert')

# signature : en lot si nb > 1
js = rempl(js, u"""async function signerContrat(){
  if(contratEnCours || !contratChoisi) return;
  contratEnCours = true;""", u"""async function signerContrat(){
  if(contratEnCours || !contratChoisi) return;
  if(contratNb > 1) return signerContratsEnLot();   // patch154
  contratEnCours = true;""", 'signer lot')

js = rempl(js, u"""async function terminerContrat(carte){""", u"""// ---------- patch154 : contrats en lot ----------
function renderCombien(){
  const zone = document.getElementById('ctCombien');
  if(!zone) return;
  const max = ctMaxNb();
  if(!contratChoisi || max < 2){ zone.hidden = true; zone.innerHTML = ''; return; }
  zone.hidden = false;
  const n = contratChoisi.n;
  zone.innerHTML = `<div class="ct-cb-t"><b>Combien de contrats ?</b><span>jusqu'à ${max} d'un coup</span></div>
    <div class="ct-puces" role="group" aria-label="Nombre de contrats">${CT_NB_CHOIX.map(k => `
      <button type="button" data-ct-nb="${k}" aria-pressed="${k === contratNb}" ${k > max || contratEnCours ? 'disabled' : ''}>×${k}<small>${k * n}${k === 1 ? ' cartes' : ''}</small></button>`).join('')}
    </div>`;
}
document.getElementById('ctCombien').addEventListener('click', (e) => {
  const b = e.target.closest('button[data-ct-nb]');
  if(!b || b.disabled || contratEnCours) return;
  contratNb = Number(b.dataset.ctNb) || 1;
  composerLot();
  renderContrat();
});

function resumeLot(){
  const terra = ctTerra();
  const pops = contratLot.map(x => Number(x.population || 0));
  const nbMon = terra ? 0 : contratLot.filter(x => monumentsNoms.has(x.commune_code)).length;
  // Terra : une ligne par commune, avec le nombre de doublons pris
  const noms = [];
  for(const x of contratLot){
    const g = noms.find(y => y.code === x.commune_code);
    if(g) g.n++; else noms.push({ code: x.commune_code, nom: x.nom || x.commune_code, n: 1 });
  }
  const ch = terra
    ? `<div><b>${ctNb(contratLot.length)}</b><span>doublons</span></div><div><b>${ctNb(noms.length)}</b><span>communes</span></div><div><b>${ctNb(contratNb)}</b><span>contrats</span></div>`
    : `<div><b>${ctNb(contratLot.length)}</b><span>communes</span></div><div><b>${ctNb(Math.min(...pops))}</b><span>hab. la plus petite</span></div><div><b>${ctNb(Math.max(...pops))}</b><span>hab. la plus grande</span></div>`;
  return `<div class="ct-resume">
    <div class="ct-res-ch">${ch}</div>
    <details class="ct-res-liste"><summary>Voir ${terra ? 'les ' + ctNb(noms.length) + ' communes' : 'les ' + ctNb(contratLot.length) + ' communes'}${nbMon ? ` · ${nbMon} monument${nbMon > 1 ? 's' : ''}` : ''}</summary>
      <div class="ct-res-noms">${noms.map(x => `<span>${echapperTexte(x.nom)}${x.n > 1 ? ' ×' + x.n : ''}${!terra && monumentsNoms.has(x.code) ? ' ★' : ''}</span>`).join('')}</div>
    </details>
    <p class="ct-res-astuce">Pour choisir ${terra ? 'doublon par doublon' : 'commune par commune'}, reste à ×1.</p>
  </div>`;
}

async function signerContratsEnLot(){
  contratEnCours = true;
  const bouton = document.getElementById('ctSigner');
  const c = contratChoisi, nb = contratNb, terra = ctTerra();
  const lot = contratLot.slice();
  renderCombien();
  const cartes = [];
  let erreur = null;
  for(let i = 0; i < nb; i++){
    if(bouton){ bouton.disabled = true; bouton.textContent = `Signature ${i + 1} / ${nb}…`; }
    const codes = lot.slice(i * c.n, (i + 1) * c.n).map(x => x.commune_code);
    if(codes.length !== c.n) break;
    try{
      const { data, error } = await sb.rpc(terra ? 'terra_signer_contrat' : 'signer_contrat', { p_codes: codes, p_vers: c.vers });
      if(error) throw error;
      if(data) cartes.push(data);
    }catch(e){ erreur = e; break; }
  }
  if(!cartes.length){
    contratEnCours = false;
    if(bouton){ bouton.disabled = false; }
    notifier({ type: 'erreur', titre: 'Contrat refusé', texte: messageLisible(erreur ? erreur.message : 'Aucun contrat signé') });
    loadContrat();
    return;
  }
  montrerRevelationLot(c, cartes, nb, erreur);
}

function montrerRevelationLot(c, cartes, nb, erreur){
  const terra = ctTerra();
  const lib = libelleTier(c.vers).toLowerCase();
  const neuves = terra ? cartes.filter(x => x.nouvelle !== false).length : 0;
  const titre = `<span style="color:var(--c-${c.vers})">${cartes.length}</span> ${echapperTexte(lib)}s obtenus`;
  const texte = (terra
      ? `${cartes.length * c.n} doublons échangés.${neuves ? ` ${neuves} nouvelle${neuves > 1 ? 's' : ''} dans ta collection, entourée${neuves > 1 ? 's' : ''} d'or.` : ''}`
      : `${cartes.length * c.n} communes sont retournées au pot. Celles-ci sont à toi.`)
    + (erreur ? ` ${cartes.length} contrat${cartes.length > 1 ? 's' : ''} sur ${nb} signé${cartes.length > 1 ? 's' : ''} : ${messageLisible(erreur.message)}` : '');
  const grille = cartes.map(x => carteDefile(c.vers, x.nom, x.departement, x.population, false, x.code)
    .replace('class="mini ', `class="mini${terra && x.nouvelle !== false ? ' neuve' : ''} `)).join('');
  ouvrirFenetre(`<div class="fenetre contrat-rev contrat-lot" role="dialog" aria-modal="true" aria-labelledby="ctlT">
      <div class="ctl-haut"><h3 id="ctlT">${titre}</h3><p>${echapperTexte(texte)}</p></div>
      <div class="ctl-grille" id="ctlGrille">${grille}</div>
      <div class="fc-actions empilees ctl-pied"><button class="fc-btn principal" data-ctl="continuer">Continuer</button></div>
    </div>`, () => terminerContratsEnLot(cartes));
  const g = document.getElementById('ctlGrille');
  const calme = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  [...(g ? g.children : [])].forEach((el, i) => setTimeout(() => el.classList.add('on'), calme ? 0 : 200 + i * 150));
  const b = document.querySelector('#fenetre [data-ctl="continuer"]');
  if(b){ b.addEventListener('click', () => document.getElementById('fenetre').click()); b.focus(); }
}

async function terminerContratsEnLot(cartes){
  contratEnCours = false;
  const terra = ctTerra();
  if(terra){ terraCharge = false; await chargerCollectionTerra(); }
  else await loadMyCollection();
  await loadContrat();
  notifier({ type: 'succes', titre: 'Contrats honorés',
    texte: `${cartes.length} commune${cartes.length > 1 ? 's rejoignent' : ' rejoint'} ta collection${terra ? ' Terra' : ''}.` });
  if(!terra) cartes.forEach(x => { if(x.code) annoncerMonument(x.code, x.nom); });
}

async function terminerContrat(carte){""", 'fonctions lot')
ecrire('app.js', js)
print(u'patch154 applique. Lancer : python3 maj-version.py')
