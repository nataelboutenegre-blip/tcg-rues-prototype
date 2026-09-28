# -*- coding: utf-8 -*-
"""
patch39 — Le contrat : departement dans le lot, et une vraie fenetre de choix.

1. Chaque ligne du lot porte le numero de departement a droite du nom.
   Les cases passent de 188 a 222 px : a 188 px, « Beaumont-du-Gatinais 77 »
   se faisait couper. Deux colonnes larges valent mieux que trois tronquees.

2. Le bouton « changer » ne prend plus la commune suivante au hasard : il
   ouvre une fenetre avec une barre de recherche (nom OU numero de
   departement) et la liste complete des communes du palier. Celles deja
   dans le lot restent visibles mais grisees — sinon le joueur cherche une
   commune, ne la trouve pas, et ne comprend pas pourquoi.
"""
import io, os, re, sys

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
#  style.css
# ===========================================================================
css = lire('style.css')

css = rempl(css,
u"""  .ct-lot{ display:grid; grid-template-columns:repeat(auto-fill,minmax(188px,1fr)); gap:8px; }""",
u"""  /* .ct-zone n'avait pas de largeur : dans un .tab-panel en align-items:
     flex-start, elle se reduisait au contenu et le lot tenait sur 483 px au
     lieu de 980. Les noms etaient coupes pour rien. */
  .ct-lot{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:8px; }""",
u'largeur des cases du lot')

css = rempl(css,
u"""  .ct-zone{ background: var(--nuit-2); border:1px solid rgba(169,188,212,0.16);
            border-radius:14px; padding:15px; margin-bottom:13px; }""",
u"""  .ct-zone{ background: var(--nuit-2); border:1px solid rgba(169,188,212,0.16);
            border-radius:14px; padding:15px; margin-bottom:13px;
            width:100%; box-sizing:border-box; }""",
u'la zone du lot occupe toute la largeur')

css = rempl(css,
u"""  .ct-l .nm{ font-size:0.79rem; font-weight:600; white-space:nowrap;
             overflow:hidden; text-overflow:ellipsis; }""",
u"""  .ct-l .nm{ font-size:0.79rem; font-weight:600; white-space:nowrap;
             display:flex; align-items:baseline; gap:5px; min-width:0; }
  /* le nom se laisse tronquer, la pastille du departement jamais */
  .ct-l .nm i{ font-style:normal; overflow:hidden; text-overflow:ellipsis; }
  .ct-dp{ font-size:0.62rem; font-weight:700; color:#7F91AB; flex-shrink:0;
          background:rgba(169,188,212,0.13); border-radius:4px; padding:1px 4px; }""",
u'nom + pastille departement')

css = rempl(css,
u"""  .ct-avert{ font-size:0.75rem; color:#7F91AB; text-align:center; margin:9px 0 0; line-height:1.5; }""",
u"""  /* la fenetre de remplacement d'une ligne du lot */
  .fenetre.ct-pick{ width:min(440px,100%); text-align:left; padding:20px 20px 16px;
                    display:flex; flex-direction:column; max-height:min(560px, 82vh); }
  .ct-pick h2{ font:900 1.5rem/1 var(--titre); margin:0 0 3px; letter-spacing:.01em; }
  .ct-pick .ct-sst{ font-size:0.76rem; color:#7F91AB; margin:0 0 13px; }
  .ct-pick input{ font:inherit; font-size:0.86rem; width:100%; box-sizing:border-box;
    background: var(--nuit); color:#fff; border:1px solid rgba(169,188,212,0.22);
    border-radius:9px; padding:9px 11px; margin-bottom:11px; }
  .ct-pick input::placeholder{ color:#6C7E96; }
  .ct-pick input:focus{ outline:none; border-color: var(--c-legendaire); }
  .ct-liste{ overflow-y:auto; flex:1; margin:0 -4px; padding:0 4px; }
  .ct-vide{ font-size:0.78rem; color:#7F91AB; text-align:center; padding:18px 0; margin:0; }
  .ct-o{ display:flex; align-items:center; gap:9px; width:100%; text-align:left;
    font:inherit; cursor:pointer; background:transparent; color:#fff;
    border:1px solid transparent; border-radius:9px; padding:8px 9px; }
  .ct-o:hover{ background: var(--nuit-3); }
  .ct-o:focus-visible{ outline:2px solid var(--c-legendaire); outline-offset:-2px; }
  .ct-o .pt{ width:8px; height:8px; border-radius:2px; flex-shrink:0; background: var(--c-commun); }
  .ct-o.peucommun .pt{ background: var(--c-peucommun); }
  .ct-o .tx{ flex:1; min-width:0; display:flex; flex-direction:column; }
  .ct-o .nm{ font-size:0.82rem; font-weight:600; display:flex; align-items:baseline;
             gap:5px; min-width:0; white-space:nowrap; }
  .ct-o .nm i{ font-style:normal; overflow:hidden; text-overflow:ellipsis; }
  .ct-o .hb{ font-size:0.67rem; color:#7F91AB; }
  .ct-o .dj{ font-size:0.64rem; font-weight:700; color:#6C7E96; flex-shrink:0; }
  .ct-o:disabled{ cursor:default; opacity:0.45; }
  .ct-o:disabled:hover{ background:transparent; }
  /* pas .ct-pied : ce nom sert deja au pied de la revelation, qui est en
     opacity:0 tant qu'il n'a pas la classe .on */
  .ct-pick .ct-pkp{ display:flex; justify-content:flex-end; margin-top:12px; }
  .ct-pick .ct-pkp button{ font:inherit; font-size:0.78rem; font-weight:600; cursor:pointer;
    background:transparent; color:#A9BCD4; border:1px solid rgba(169,188,212,0.22);
    border-radius:9px; padding:7px 15px; }
  .ct-pick .ct-pkp button:hover{ color:#fff; border-color: var(--c-legendaire); }

  .ct-avert{ font-size:0.75rem; color:#7F91AB; text-align:center; margin:9px 0 0; line-height:1.5; }""",
u'styles de la fenetre de choix')

ecrire('style.css', css)


# ===========================================================================
#  app.js
# ===========================================================================
js = lire('app.js')

# --- 1. la ligne du lot porte le departement -------------------------------
js = rempl(js,
u"""      <span class="tx"><span class="nm">${echapperTexte(x.nom || x.commune_code)}</span><span class="hb">${ctNb(x.population || 0)} hab.</span></span>""",
u"""      <span class="tx"><span class="nm"><i>${echapperTexte(x.nom || x.commune_code)}</i>${ctDept(x.departement)}</span><span class="hb">${ctNb(x.population || 0)} hab.</span></span>""",
u'departement dans la ligne du lot')

# --- 2. la fenetre de choix remplace le « changer » aveugle -----------------
js = rempl(js,
u"""// Remplace une ligne par la premiere candidate qui n'est pas deja dans le lot.
function changerLigne(i){
  if(!contratChoisi) return;
  const pris = new Set(contratLot.map(x => x.commune_code));
  const suivante = (contratDispo[contratChoisi.de] || [])
    .find(x => !pris.has(x.commune_code));
  if(!suivante){
    notifier({ type: 'info', titre: 'Plus de remplaçante',
      texte: 'Toutes tes communes de ce palier sont déjà dans le lot.' });
    return;
  }
  contratLot[i] = suivante;
  renderContrat();
}""",
u"""// La pastille du departement. Vide si la base ne le connait pas : mieux
// vaut pas de pastille qu'une pastille vide.
function ctDept(dep){
  const d = String(dep || '').trim();
  if(!d) return '';
  const nom = DEPT_NAMES[d] || '';
  return `<span class="ct-dp"${nom ? ` title="${echapperTexte(nom)}"` : ''}>${echapperTexte(d)}</span>`;
}

// Remplacer une ligne : on ouvre la liste complete du palier, avec une
// recherche sur le nom ou le numero de departement. Les communes deja dans
// le lot restent affichees mais grisees — les cacher ferait chercher en
// vain une commune qu'on possede bel et bien.
function changerLigne(i){
  if(!contratChoisi) return;
  const actuelle = contratLot[i];
  if(!actuelle) return;
  const toutes = contratDispo[contratChoisi.de] || [];
  const pris = new Set(contratLot.map(x => x.commune_code));

  const fermer = ouvrirFenetre(`
    <div class="fenetre ct-pick" role="dialog" aria-modal="true" aria-labelledby="ctPickT">
      <h2 id="ctPickT">Remplacer ${echapperTexte(actuelle.nom || actuelle.commune_code)}</h2>
      <p class="ct-sst">${ctNb(toutes.length)} commune${toutes.length > 1 ? 's' : ''} à choisir</p>
      <input type="search" id="ctRech" autocomplete="off" placeholder="Nom ou département…"
             aria-label="Chercher une commune">
      <div class="ct-liste" id="ctPickL"></div>
      <div class="ct-pkp"><button type="button" id="ctPickA">Annuler</button></div>
    </div>`);

  const champ = document.getElementById('ctRech');
  const liste = document.getElementById('ctPickL');

  const dessiner = () => {
    // correspondRecherche() : le meme filtre que la Collection et la carte,
    // nom OU numero de departement OU nom du departement
    const m = sansAccents(champ.value.trim());
    const vus = m ? toutes.filter(x =>
      correspondRecherche(x.nom || x.commune_code, x.departement, m)) : toutes;
    if(!vus.length){
      liste.innerHTML = `<p class="ct-vide">Aucune commune ne correspond.</p>`;
      return;
    }
    liste.innerHTML = vus.slice(0, 300).map(x => {
      const soi = x.commune_code === actuelle.commune_code;
      const dedans = pris.has(x.commune_code);
      const note = soi ? 'celle-ci' : (dedans ? 'déjà dans le lot' : '');
      return `<button type="button" class="ct-o ${contratChoisi.de}" ${dedans ? 'disabled' : ''}
                      data-code="${echapperTexte(x.commune_code)}">
        <span class="pt"></span>
        <span class="tx"><span class="nm"><i>${echapperTexte(x.nom || x.commune_code)}</i>${ctDept(x.departement)}</span><span class="hb">${ctNb(x.population || 0)} hab.</span></span>
        ${note ? `<span class="dj">${note}</span>` : ''}
      </button>`;
    }).join('');
  };

  dessiner();
  champ.addEventListener('input', dessiner);
  document.getElementById('ctPickA').addEventListener('click', () => fermer(null));
  liste.addEventListener('click', (e) => {
    const b = e.target.closest('.ct-o');
    if(!b || b.disabled) return;
    const choisie = toutes.find(x => x.commune_code === b.dataset.code);
    if(!choisie) return;
    contratLot[i] = choisie;
    fermer(null);
    renderContrat();
  });
  // sur ordinateur on peut taper tout de suite ; sur telephone on ne force
  // pas le clavier a s'ouvrir par-dessus la liste
  if(!/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) champ.focus();
}""",
u'fenetre de choix du remplacement')

ecrire('app.js', js)

print(u'patch39 applique.')
