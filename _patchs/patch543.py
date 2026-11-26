# patch543 (Arkhannou, ASMFCB, H34VEN ; s3-82) : le blason de clan, version 2 : 8 partitions, 24 meubles, ornements
# (manteau, timbre, devise), atelier à 8 calques. Code dans patch543-blason.js, patch543-fonctions.js, patch543-editeur.js.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
ICI = os.path.dirname(os.path.abspath(__file__))
lire = lambda n: open(os.path.join(ICI, n), encoding='utf-8').read()
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:40]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:40]!r})')
A = 'app.js'
t = open(os.path.join(R, A), encoding='utf-8').read()
# 1. le dessin : nouvelles données, puis blasonNet et blasonSVG remplacés
debut = t.index("let blRares = 0;   // patch536")
fin = t.index("let BLASONS = new Map();")
if 'patch543' not in t[debut:fin]:
    vieux = t[t.index("const BL_DEFAUT = {", debut):fin]
    t = t[:debut] + lire('patch543-blason.js') + '\n' + t[debut:t.index("const BL_DEFAUT = {", debut)] + lire('patch543-fonctions.js') + '\n' + lire('patch543-editeur.js') + '\n' + t[fin:]
    open(os.path.join(R, A), 'w', encoding='utf-8').write(t); print('app.js : dessin et éditeur v2')

# 2. l'éditeur
rep(A, """    <div class="bl-tete"><svg class="bl-grand" viewBox="0 0 100 120" aria-hidden="true">${blasonSVG(B)}</svg>""",
       """    <div class="bl-tete">${blasonSvgTag(B, blOptsEdition(), 'class="bl-grand"')}""")
rep(A, "bt('partition', k, `${ecu({ ...B, partition:k, meuble:'aucun', bordure:'aucune' })}<span>${p.nom}</span>`)",
       "bt('partition', k, `${ecu({ ...B, partition:k, meuble:'aucun', bordure:'aucune', calques:[] })}<span>${p.nom}</span>`)")
rep(A, """    <h2>Meuble</h2><div class="bl-choix bl-meubles">${Object.entries(BL_MEUBLES).map(([k, m]) => blVerrou(k, m, B.meuble, bt('meuble', k,
      `<svg viewBox="0 0 40 40" aria-hidden="true">${m.d ? (m.trait ? `<path d="${m.d}" fill="none" stroke="#E6EDF7" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/>` : `<path d="${m.d}" fill-rule="evenodd" fill="#E6EDF7"/>`) : '<path d="M10 10L30 30M30 10L10 30" stroke="#5B6E8C" stroke-width="2.5"/>'}</svg><span>${m.nom}</span>`))).join('')}</div>
    ${BL_MEUBLES[B.meuble].d ? `<div class="bl-deux"><div><h2>Couleur du meuble</h2><div class="bl-emaux">${pastilles('cm')}</div></div>
      <div><h2>Nombre</h2><div class="bl-seg">${bt('nombre', 1, 'Un seul')}${bt('nombre', 3, 'Trois')}</div></div></div>` : ''}""",
"""    ${B.calques.length ? blAtelierHtml(E, B, bt) : `<h2>Meuble</h2><div class="bl-choix bl-meubles">${Object.entries(BL_MEUBLES).map(([k, m]) => blVerrou(k, m, B.meuble, bt('meuble', k,
      `${blMeubleIcone(m)}<span>${m.nom}</span>`))).join('')}</div>
    ${BL_MEUBLES[B.meuble].d ? `<div class="bl-deux"><div><h2>Couleur du meuble</h2><div class="bl-emaux">${pastilles('cm')}</div></div>
      <div><h2>Nombre</h2><div class="bl-seg">${bt('nombre', 1, 'Un seul')}${bt('nombre', 3, 'Trois')}</div></div></div>` : ''}
    <p><button type="button" class="bq-btn secondaire bl-vers-atelier" data-bl-atelier>🧩 Composer librement (jusqu’à ${BL_CALQUES_MAX} meubles)</button></p>`}""")
rep(A, """    <h2>Bordure</h2><div class="bl-emaux">${pastilles('bordure', true)}</div>""",
       """    <h2>Bordure</h2><div class="bl-emaux">${pastilles('bordure', true)}</div>
    ${blOrnementsHtml(E, B, bt, pastilles)}""")
rep(A, """    <p class="clan-note">Le nom et le sigle se changent une fois par semaine ; la couleur et le blason, quand tu veux. Un nom ou un sigle déjà pris est refusé.</p>
  </div>`;""", """    <p class="clan-note">Le nom et le sigle se changent une fois par semaine ; la couleur et le blason, quand tu veux. Un nom ou un sigle déjà pris est refusé.</p>
    <p class="clan-note bl-credits">Animaux et objets ajoutés : game-icons.net (Lorc, Delapouite et autres, CC BY 3.0) ; Lion dressé : gravure de 1862, domaine public.</p>
  </div>`;""")
# les clics de l'atelier, avant les autres
rep(A, "  if(clanEdition){\n    if(b.dataset.blG){ const g = b.dataset.blG, v = b.dataset.blV;",
       "  if(clanEdition){\n    if(blAtelierClic(b)) return;   // patch543\n    if(b.dataset.blG){ const g = b.dataset.blG, v = b.dataset.blV;")
rep(A, "      B.nombre = tire([1, 1, 3]); B.bordure = tire(['aucune', 'aucune', 'aucune', ...cles]);",
       "      B.nombre = tire([1, 1, 3]); B.bordure = tire(['aucune', 'aucune', 'aucune', ...cles]); B.calques = [];   // patch543")
# 3. la page du clan et sa fiche : le grand blason avec ses ornements
rep(A, """function blasonHtml(tag, couleur, petit){
  const bl = BLASONS.get(tag);   // patch253
  const lr = (h) => typeof laurierAutour === 'function' ? laurierAutour(h, tag, petit) : h;   // patch459
  if(bl && bl.blason) return lr(`<span class="blason blason-svg${petit ? ' petit' : ''}" title="${echapperTexte(tag)}"><svg viewBox="0 0 100 120" aria-hidden="true">${blasonSVG(bl.blason)}</svg></span>`);""",
"""function blasonHtml(tag, couleur, petit, nom){
  const bl = BLASONS.get(tag);   // patch253
  const lr = (h) => typeof laurierAutour === 'function' ? laurierAutour(h, tag, petit) : h;   // patch459
  if(bl && bl.blason && !petit && nom !== undefined && blAOrnements(blasonNet(bl.blason))){   // patch543 : le grand blason, avec ses ornements
    const b = blasonNet(bl.blason);
    return lr(`<span class="blason blason-svg orne" title="${echapperTexte(tag)}">${blasonSvgTag(b, { orne: true, devise: blDeviseTexte(b, nom, tag) })}</span>`);
  }
  if(bl && bl.blason) return lr(`<span class="blason blason-svg${petit ? ' petit' : ''}" title="${echapperTexte(tag)}"><svg viewBox="0 0 100 120" aria-hidden="true">${blasonSVG(bl.blason)}</svg></span>`);""")
rep(A, """      <div class="clan-tete">${blasonHtml(c.tag, c.couleur)}<div><div class="clan-nom">""", """      <div class="clan-tete">${blasonHtml(c.tag, c.couleur, false, c.nom)}<div><div class="clan-nom">""")
rep(A, """        <div class="cf-blason">${blasonHtml(c.tag, c.couleur)}</div>""", """        <div class="cf-blason">${blasonHtml(c.tag, c.couleur, false, c.nom)}</div>""")

S = 'style.css'
rep(S, ".bl-seg{ display:inline-flex; background:var(--nuit); padding:3px; border-radius:10px; gap:2px; }", """.bl-seg{ display:inline-flex; background:var(--nuit); padding:3px; border-radius:10px; gap:2px; }
/* patch543 : ornements et atelier */
.bl-petit{ font-size:.7rem; font-weight:600; color:var(--brume); margin-left:6px; }
.bl-h3{ font-size:.8rem; color:var(--brume); margin:12px 0 6px; font-weight:700; }
.bl-marge{ margin-top:8px; }
.bl-choix.bl-timbres svg{ width:64px; height:26px; }
.bl-timbres .bl-lock{ opacity:.45; border-style:dashed !important; cursor:not-allowed; }
.blason.blason-svg.orne{ width:92px; height:107px; }
.cf-blason .blason.blason-svg.orne{ width:110px; height:128px; }
.bl-atelier{ display:flex; gap:12px; align-items:flex-start; }
.bl-at-ecu{ flex:none; display:flex; flex-direction:column; align-items:center; gap:4px; }
.bl-at-ecu small{ font-size:.66rem; color:var(--brume); max-width:130px; text-align:center; }
#blApercu{ width:130px; height:156px; touch-action:none; cursor:grab; filter:drop-shadow(0 6px 14px rgba(0,0,0,.4)); }
.bl-cqs{ flex:1; min-width:0; display:flex; flex-direction:column; gap:5px; max-height:220px; overflow:auto; }
.bl-cq{ display:flex; align-items:center; gap:4px; background:var(--nuit-2); border-radius:9px; padding:3px; border:1.5px solid transparent; }
.bl-cq.on{ border-color:var(--c-legendaire, #F0B429); }
.bl-cq-choisir{ flex:1; min-width:0; display:flex; align-items:center; gap:7px; background:none; border:0; color:#fff; font:inherit; font-size:.8rem; cursor:pointer; padding:3px 4px; text-align:left; }
.bl-cq-choisir svg{ width:22px; height:22px; flex:none; }
.bl-cq-choisir b{ white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-weight:600; }
.bl-cq-mini{ background:none; border:0; color:var(--brume); font-size:.95rem; width:28px; height:28px; border-radius:7px; cursor:pointer; }
.bl-cq-mini:disabled{ opacity:.3; }
.bl-curseur{ display:grid; grid-template-columns:78px minmax(0,1fr) 46px; gap:8px; align-items:center; font-size:.8rem; color:var(--brume); margin:8px 0; }
.bl-curseur input{ width:100%; accent-color:var(--c-legendaire, #F0B429); }
.bl-curseur output{ color:#fff; font-variant-numeric:tabular-nums; text-align:right; }
.bl-at-actions{ display:flex; flex-wrap:wrap; gap:6px; margin:8px 0; }
.bl-at-actions [aria-pressed="true"]{ border-color:var(--c-legendaire, #F0B429); color:#FFD36B; }
.bl-vers-atelier{ margin-top:4px; }
.bl-credits{ font-size:.68rem; opacity:.8; }
@media (max-width:420px){ #blApercu{ width:112px; height:134px; } }""")
