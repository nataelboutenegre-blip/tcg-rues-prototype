# -*- coding: utf-8 -*-
u"""
patch213 — ordre de la vitrine (idée d'Arkhannou, Discord, 26 octobre).
Dans « Ma vitrine », toucher une carte de la bande la sélectionne (soulevée,
cerclée d'or) ; toucher une autre carte échange leurs places ; toucher la
première place vide l'envoie au bout ; la croix rouge la retire. Avant, toucher
une carte la retirait tout de suite. Aperçu validé (« parfait »). Sans SQL :
l'ordre est déjà enregistré tel quel par terra_vitrine_definir(_front).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a)
    assert c == n, (a[:90], c, n)
    return s.replace(a, b)

js = lire('app.js')
assert 'patch213' not in js
js = rep(js, u"""  let recherche = '';
  const rangTier = (t) => TIERS.findIndex""", u"""  let recherche = '';
  let vtSel = null, vtSaute = -1;   // patch213 : place sélectionnée dans la bande
  const rangTier = (t) => TIERS.findIndex""")
js = rep(js, u"""Touche une carte de la vitrine pour la retirer.${front""", u"""Touche une carte de la vitrine pour la déplacer ou la retirer.${front""")
js = rep(js, u"""      <p class="vt-compte" id="vtCompte"></p>
      <div class="vt-etagere vt-bande" id="vtApercu"></div>""", u"""      <p class="vt-compte" id="vtCompte"></p>
      <p class="vt-deplacer" id="vtDeplacer" hidden></p>
      <div class="vt-etagere vt-bande" id="vtApercu"></div>""")
js = rep(js, u"""      cases.push(c ? `<div class="vt-case-w"><button type="button" class="vt-case" data-vt-retirer="${echapperTexte(c.code)}" aria-label="Retirer ${echapperTexte(c.nom)}">${miniVitrine({ ...c, skin: skinDeMaCarte(front ? 'front' : 'terra', c.code) })}</button>${dosC""",
u"""      cases.push(c ? `<div class="vt-case-w"><button type="button" class="vt-case${vtSel === i ? ' choisie' : ''}${vtSaute === i ? ' saute' : ''}" data-vt-place="${i}" aria-pressed="${vtSel === i}" aria-label="Déplacer ${echapperTexte(c.nom)}">${miniVitrine({ ...c, skin: skinDeMaCarte(front ? 'front' : 'terra', c.code) })}</button>${vtSel === i ? `<button type="button" class="vt-retirer" data-vt-retirer="${echapperTexte(c.code)}" aria-label="Retirer ${echapperTexte(c.nom)}">✕</button>` : ''}${dosC""")
js = rep(js, u"""                   : `<div class="vt-case vide"><span>${i + 1}</span></div>`);
    }
    const bande = document.getElementById('vtApercu');""", u"""                   : (vtSel !== null && i === choix.length
                      ? `<button type="button" class="vt-case vide cible" data-vt-bout aria-label="Mettre au bout"><span>${i + 1}</span></button>`
                      : `<div class="vt-case vide"><span>${i + 1}</span></div>`));
    }
    vtSaute = -1;
    const vdep = document.getElementById('vtDeplacer'), cs = vtSel !== null && reserve.get(choix[vtSel]);
    vdep.hidden = !cs;
    if(cs) vdep.textContent = `${cs.nom} : touche une autre carte pour échanger leurs places, ou la place vide pour la mettre au bout.`;
    const bande = document.getElementById('vtApercu');
    bande.classList.toggle('vt-sel', vtSel !== null);""")
js = rep(js, u"""    const r = e.target.closest('[data-vt-retirer]');
    if(r){ choix = choix.filter(x => x !== r.dataset.vtRetirer); erreur.textContent = ''; dessiner(); return; }
    const c = e.target.closest('[data-vt-code]');
    if(c){""", u"""    const r = e.target.closest('[data-vt-retirer]');
    if(r){ choix = choix.filter(x => x !== r.dataset.vtRetirer); vtSel = null; erreur.textContent = ''; dessiner(); return; }
    // patch213 : sélectionner, échanger, envoyer au bout
    const pl = e.target.closest('[data-vt-place]');
    if(pl){
      const i = Number(pl.dataset.vtPlace);
      if(vtSel === null) vtSel = i;
      else if(vtSel === i) vtSel = null;
      else { [choix[vtSel], choix[i]] = [choix[i], choix[vtSel]]; vtSaute = i; vtSel = null; }
      erreur.textContent = ''; dessiner(); return;
    }
    if(e.target.closest('[data-vt-bout]') && vtSel !== null){
      const [x] = choix.splice(vtSel, 1); choix.push(x); vtSaute = choix.length - 1; vtSel = null;
      dessiner(); return;
    }
    const c = e.target.closest('[data-vt-code]');
    if(c){
      vtSel = null;""")
ecrire('app.js', js)

css = lire('style.css')
assert 'patch213' not in css
css += u"""
/* patch213 : déplacer les cartes de la vitrine */
.vt-deplacer{ font-size:.78rem; color:var(--c-legendaire, #F0B429); margin:-4px 0 10px; line-height:1.4; }
.vt-bande > .vt-case-w > .vt-case{ transition: transform .18s, box-shadow .18s, opacity .18s; border-radius:10px; cursor:pointer; }
.vt-bande.vt-sel > .vt-case-w > .vt-case:not(.choisie){ opacity:.78; }
.vt-bande > .vt-case-w > .vt-case.choisie{ transform: translateY(-6px) scale(1.06); box-shadow: 0 0 0 3px #F0B429, 0 12px 22px rgba(0,0,0,.55); z-index:2; }
.vt-retirer{ position:absolute; left:-7px; top:-12px; z-index:4; width:24px; height:24px; border-radius:50%; border:0; padding:0;
  background:#E5484D; color:#fff; font-weight:900; font-size:12px; line-height:24px; text-align:center; cursor:pointer; box-shadow:0 2px 6px rgba(0,0,0,.5); }
.vt-bande > .vt-case.vide.cible{ flex:0 0 66px; width:66px; cursor:pointer; background:none; border-color:rgba(240,180,41,.55); }
.vt-case.vide.cible span{ color:rgba(240,180,41,.75); }
@keyframes vtSaute{ 0%{ transform:scale(.85); } 60%{ transform:scale(1.08); } 100%{ transform:none; } }
.vt-bande > .vt-case-w > .vt-case.saute{ animation: vtSaute .3s ease-out; }
@media (prefers-reduced-motion: reduce){ .vt-bande > .vt-case-w > .vt-case.saute{ animation:none; } }
"""
ecrire('style.css', css)
print('patch213 ok')
