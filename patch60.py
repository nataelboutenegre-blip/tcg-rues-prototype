# -*- coding: utf-8 -*-
u"""
patch60 — Ne jamais sacrifier certaines communes ni certains departements.

LE BESOIN
  Le lot de dix se compose tout seul, des moins peuplees aux plus peuplees.
  Les memes communes reviennent donc a chaque contrat, et il faut les retirer
  a la main a chaque fois.

DEUX GESTES, UNE SEULE LISTE
  — Sur chaque ligne du lot, un cadenas : « ne plus proposer celle-ci ». Le
    geste est la ou naît l'agacement, au moment ou on la voit revenir.
  — Un bloc repliable sous le lot, qui liste ce qui est exclu et permet
    d'ajouter un departement entier. Protéger sa region sans cocher cent
    communes une par une.

  Les deux ecrivent dans la meme table. Ce n'est pas deux fonctionnalites,
  c'est une seule avec deux portes.

CE QUE CA NE FAIT PAS, ET C'EST ECRIT DANS L'ECRAN
  Ca ne protege de rien d'autre : ni du combat, ni de la vente, ni des
  echanges. C'est une protection contre sa propre main sur le contrat. Le
  dire dans l'interface evite qu'un joueur se croie a l'abri.

OU C'EST GARDE
  En base, pas dans le navigateur. Les etiquettes et les bandeaux fermes
  vivent dans le navigateur parce qu'en perdre un n'a aucune consequence.
  Ici, perdre la liste en changeant d'appareil signifie sacrifier des
  communes qu'on voulait garder, et un contrat ne se defait pas.

DEMANDE contrat-exclusions.sql
  Sans lui, les appels echouent proprement : le bloc reste vide, le cadenas
  previent qu'il n'a pas pu enregistrer, et le contrat fonctionne comme
  avant.
"""
import io, os

BASE = os.path.dirname(os.path.abspath(__file__))

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


# ===========================================================================
#  index.html — le bloc des exclusions
# ===========================================================================
html = lire('index.html')

html = rempl(html,
u"""      <button class="open-btn" id="ctSigner" hidden>Signer le contrat</button>""",
u"""      <details class="ct-excl" id="ctExcl" hidden>
        <summary>Ne jamais sacrifier <span class="ct-excl-nb" id="ctExclNb"></span></summary>
        <p class="ct-excl-aide">Ces communes et ces départements ne seront plus jamais proposés dans un contrat. Ça ne les protège de rien d'autre : ni du combat, ni de la vente, ni des échanges.</p>
        <div class="ct-excl-liste" id="ctExclListe"></div>
        <div class="ct-excl-ajout">
          <input type="text" id="ctExclDept" maxlength="30" autocomplete="off"
                 placeholder="Ajouter un département : 16 ou Charente">
          <button class="ct-excl-btn" id="ctExclAjouter">Ajouter</button>
        </div>
        <p class="ct-excl-err" id="ctExclErr" hidden></p>
      </details>

      <button class="open-btn" id="ctSigner" hidden>Signer le contrat</button>""",
u'le bloc des exclusions')

ecrire('index.html', html)


# ===========================================================================
#  app.js
# ===========================================================================
js = lire('app.js')

js = rempl(js,
u"""function renderContrat(){""",
u"""// ---------- Ne jamais sacrifier ----------
// La liste vit en base : la perdre en changeant d'appareil reviendrait a
// sacrifier des communes qu'on voulait garder, et un contrat ne se defait pas.
const ICONE_CADENAS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="4.5" y="10.5" width="15" height="10" rx="2"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/></svg>';

let contratExclusions = [];

async function chargerExclusions(){
  const { data, error } = await sb.rpc('mes_exclusions_contrat');
  // contrat-exclusions.sql pas encore passe : on continue sans, le contrat
  // marche comme avant
  if(error){ contratExclusions = []; return false; }
  contratExclusions = data || [];
  return true;
}

function renderExclusions(){
  const bloc = document.getElementById('ctExcl');
  const liste = document.getElementById('ctExclListe');
  const nb = document.getElementById('ctExclNb');
  if(!bloc || !liste) return;
  bloc.hidden = false;
  if(nb) nb.textContent = contratExclusions.length
    ? contratExclusions.length + (contratExclusions.length > 1 ? ' exclusions' : ' exclusion')
    : 'aucune pour l’instant';

  if(!contratExclusions.length){
    liste.innerHTML = '<p class="ct-excl-vide">Rien d’exclu. Le cadenas sur une ligne du lot ajoute la commune ici.</p>';
    return;
  }
  liste.innerHTML = contratExclusions.map(x => x.departement
    ? `<span class="ct-excl-item dept">${echapperTexte(DEPT_NAMES[x.departement] || '')} (${echapperTexte(x.departement)}) — tout le département
         <button data-ct-inclure-dept="${echapperTexte(x.departement)}" aria-label="Ne plus exclure">&#10005;</button></span>`
    : `<span class="ct-excl-item">${echapperTexte(x.nom || x.commune_code)}${badgeDept(x.dept_commune)}
         <button data-ct-inclure="${echapperTexte(x.commune_code)}" aria-label="Ne plus exclure">&#10005;</button></span>`
  ).join('');
}

function direErreurExclusion(texte){
  const el = document.getElementById('ctExclErr');
  if(!el) return;
  el.hidden = !texte;
  el.textContent = texte || '';
}

async function exclureDuContrat(args){
  direErreurExclusion('');
  const { error } = await sb.rpc('exclure_du_contrat', args);
  if(error){ direErreurExclusion(messageLisible(error.message)); return; }
  await chargerExclusions();
  renderExclusions();
  await loadContrat();          // le serveur ne les propose plus : on relit
}

async function inclureAuContrat(args){
  direErreurExclusion('');
  const { error } = await sb.rpc('inclure_au_contrat', args);
  if(error){ direErreurExclusion(messageLisible(error.message)); return; }
  await chargerExclusions();
  renderExclusions();
  await loadContrat();
}

document.getElementById('ctExclAjouter').addEventListener('click', () => {
  const champ = document.getElementById('ctExclDept');
  const saisi = (champ.value || '').trim();
  if(!saisi) return;
  // « charente » devient « 16 » : le meme utilitaire que les recherches
  const code = codeDepartement(saisi) || saisi;
  if(!DEPT_NAMES[code]){
    direErreurExclusion('Département inconnu. Essaie un numéro (16) ou un nom (Charente).');
    return;
  }
  champ.value = '';
  exclureDuContrat({ p_departement: code });
});
document.getElementById('ctExclDept').addEventListener('keydown', (e) => {
  if(e.key === 'Enter'){ e.preventDefault(); document.getElementById('ctExclAjouter').click(); }
});
document.getElementById('ctExclListe').addEventListener('click', (e) => {
  const c = e.target.closest('[data-ct-inclure]');
  if(c){ inclureAuContrat({ p_commune: c.dataset.ctInclure }); return; }
  const d = e.target.closest('[data-ct-inclure-dept]');
  if(d){ inclureAuContrat({ p_departement: d.dataset.ctInclureDept }); }
});


function renderContrat(){""",
u'le bloc des exclusions en JS')

# --- le cadenas sur chaque ligne du lot ------------------------------------
js = rempl(js,
u"""      <button data-ct-changer="${i}">changer</button>""",
u"""      <button class="ct-cadenas" data-ct-exclure="${echapperTexte(x.commune_code)}" title="Ne plus jamais proposer ${echapperTexte(x.nom || x.commune_code)}">${ICONE_CADENAS}</button>
      <button data-ct-changer="${i}">changer</button>""",
u'le cadenas sur la ligne')

# --- le clic sur le cadenas -------------------------------------------------
js = rempl(js,
u"""async function loadContrat(){""",
u"""document.getElementById('ctLot').addEventListener('click', (e) => {
  const b = e.target.closest('[data-ct-exclure]');
  if(!b) return;
  exclureDuContrat({ p_commune: b.dataset.ctExclure });
});

async function loadContrat(){""",
u'le clic sur le cadenas')

# --- les exclusions se chargent avec le contrat -----------------------------
js = rempl(js,
u"""  composerLot();
  renderContrat();
  majRappelContrat();
}""",
u"""  composerLot();
  renderContrat();
  majRappelContrat();
}

// L'onglet charge sa liste d'exclusions en meme temps que ses candidats.
async function loadContratEtExclusions(){
  const ok = await chargerExclusions();
  if(ok) renderExclusions();
  await loadContrat();
}""",
u'chargement conjoint')

js = rempl(js,
u"""    if(tab.dataset.tab === 'contrat') loadContrat();""",
u"""    if(tab.dataset.tab === 'contrat') loadContratEtExclusions();""",
u'l’onglet appelle le chargement conjoint')

# --- les textes disent que les exclusions comptent -------------------------
js = rempl(js,
u"""  document.getElementById('ctInfo').textContent =
    `${contratChoisi.n} communes, les moins peuplées — favoris exclus`;""",
u"""  // dire « favoris exclus » alors qu'on ecarte aussi une liste posee par le
  // joueur, c'est lui cacher la moitie de la regle
  document.getElementById('ctInfo').textContent =
    `${contratChoisi.n} communes, les moins peuplées — favoris`
    + (contratExclusions.length ? ' et exclusions' : '') + ' exclus';""",
u'le resume mentionne les exclusions')

js = rempl(js,
u"""        + 'hors ventes en cours et hors échanges en attente.';""",
u"""        + 'hors ventes en cours, hors échanges en attente'
        + (contratExclusions.length ? ' et hors liste « ne jamais sacrifier ».' : '.');""",
u'le message vide mentionne les exclusions')

ecrire('app.js', js)


# ===========================================================================
#  style.css
# ===========================================================================
css = lire('style.css')

css += (
u"""
  /* ---------- Ne jamais sacrifier ---------- */
  .ct-cadenas{
    flex-shrink:0; width:30px; height:30px; padding:5px;
    border:1px solid rgba(169,188,212,0.24); border-radius:8px;
    background:none; color: var(--brume); cursor:pointer;
    transition: color .15s, border-color .15s;
  }
  .ct-cadenas svg{ width:100%; height:100%; display:block; }
  .ct-cadenas:hover{ color: var(--c-legendaire); border-color: rgba(240,180,41,0.5); }
  .ct-excl{
    width:100%; margin: 12px 0 0; padding: 10px 14px;
    border:1px solid rgba(169,188,212,0.18); border-radius:12px;
    background: var(--nuit-2);
  }
  .ct-excl[hidden]{ display:none; }
  .ct-excl > summary{
    cursor:pointer; font-size:0.88rem; font-weight:600; list-style:none;
  }
  .ct-excl > summary::-webkit-details-marker{ display:none; }
  .ct-excl > summary::before{ content:'▸ '; color: var(--brume); }
  .ct-excl[open] > summary::before{ content:'▾ '; }
  .ct-excl-nb{ font-weight:400; color: var(--brume); font-size:0.8rem; margin-left:4px; }
  .ct-excl-aide{
    margin: 8px 0 10px; font-size:0.76rem; line-height:1.5; color: var(--brume);
    max-width:66ch;
  }
  .ct-excl-liste{ display:flex; flex-wrap:wrap; gap:7px; }
  .ct-excl-vide{ margin:0; font-size:0.78rem; color: var(--brume); font-style:italic; }
  .ct-excl-item{
    display:inline-flex; align-items:center; gap:6px;
    padding:4px 4px 4px 10px; border-radius:999px;
    background: rgba(169,188,212,0.12); font-size:0.8rem;
  }
  .ct-excl-item.dept{ background: rgba(240,180,41,0.14); color: var(--c-legendaire); }
  .ct-excl-item button{
    width:20px; height:20px; padding:0; border:0; border-radius:50%;
    background: rgba(10,22,41,0.35); color:inherit; cursor:pointer;
    font-size:0.68rem; line-height:1;
  }
  .ct-excl-item button:hover{ background: rgba(229,72,77,0.5); color:#fff; }
  .ct-excl-ajout{ display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; }
  .ct-excl-ajout input{
    flex:1; min-width:200px; max-width:340px;
    padding:8px 12px; border-radius:9px;
    border:1px solid rgba(169,188,212,0.2); background: var(--nuit);
    color:#fff; font:inherit; font-size:0.84rem;
  }
  .ct-excl-ajout input::placeholder{ color: var(--brume); }
  .ct-excl-ajout input:focus{ outline:none; border-color: var(--c-legendaire); }
  .ct-excl-btn{
    padding:8px 16px; border-radius:9px; cursor:pointer;
    border:1px solid rgba(169,188,212,0.28); background: var(--nuit-3);
    color:#fff; font:inherit; font-size:0.84rem; font-weight:600;
  }
  .ct-excl-btn:hover{ border-color: rgba(240,180,41,0.5); }
  .ct-excl-err{ margin:10px 0 0; font-size:0.78rem; color: var(--c-rouge); }
  .ct-excl-err[hidden]{ display:none; }
""")

ecrire('style.css', css)
print(u'patch60 applique.')
