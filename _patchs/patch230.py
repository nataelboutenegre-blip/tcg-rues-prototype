# -*- coding: utf-8 -*-
u"""
patch230 — le skin de la cible pendant l'assaut (aperçu validé le 27/10).

Quand on attaque une commune habillée d'un skin, la carte de la cible
apparaît en entier avec son skin (animé), face à la nôtre, avec « à pseudo »
et l'étiquette « ✦ Skin Brasier » : la toucher ouvre ce skin dans la
Boutique. Le skin est demandé au serveur juste avant l'attaque
(skin_front_commune, s2-41 ; 0,7 s au plus, sinon carte normale). Une Aurore
n'a pas de skin. Sans s2-41 : carte normale, comme avant.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a); assert c == n, ('MATCH', a[:70], 'trouve', c, 'attendu', n); return s.replace(a, b)

s = lire('app.js')
assert 'patch230' not in s
# 1. la carte de la cible habillée
s = rep(s, "// cible : { code, nom, dept, tier (id), pseudo, lat, lon } — capturee AVANT\n",
"""// patch230 : le skin de la carte du Front visée (celui de son propriétaire), demandé juste avant l'attaque
const skinsCibles = new Map();   // code -> { k, t }
async function skinCibleFront(code){
  if(!SAISON2) return null;
  const c = skinsCibles.get(code);
  if(c && Date.now() - c.t < 120000) return c.k;
  try{
    const r = await Promise.race([sb.rpc('skin_front_commune', { p_code: code }), new Promise(ok => setTimeout(() => ok(null), 700))]);
    if(!r) return null;
    const k = r.error ? null : skinCle(r.data);
    skinsCibles.set(code, { k, t: Date.now() });
    return k;
  }catch(e){ return null; }
}
function carteAssautSkin(e, k, qui){
  const t = e.tier && e.tier.id ? e.tier : (TIERS.find(x => x.id === e.tier) || TIERS[0]);
  return `<div class="as-carte as-carte-skin ${t.id}">${miniTerra({ code: e.code, nom: e.nom, dept: e.dept, tier: t, exemplaires: 1, photo: e.photo, skin: k })}
    <p class="as-skin-qui">${qui}</p>
    <button type="button" class="as-skin-nom" data-skin-boutique="${echapperTexte(k)}">✦ Skin ${echapperTexte(SKIN_NOMS[k] || k)}</button></div>`;
}
// le nom du skin mène à sa fiche dans la Boutique
async function ouvrirSkinBoutique(k){
  const fond = document.getElementById('fenetre');
  if(fond && !fond.hidden){ fond.classList.remove('visible'); fond.hidden = true; fond.innerHTML = ''; }
  const tab = document.querySelector('.tab[data-tab="boutique"]');
  if(tab) tab.click();
  const v = document.querySelector('.volet[data-volet="boutiqueeuros"]');
  if(v) v.click();
  for(let i = 0; i < 30; i++){
    if(typeof bqeCat !== 'undefined' && bqeCat && (bqeCat.articles || []).some(a => a.id === 'skin-' + k)){ bqeOuvrirFiche('skin-' + k); return; }
    await new Promise(ok => setTimeout(ok, 150));
  }
}
document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-skin-boutique]');
  if(b){ e.preventDefault(); ouvrirSkinBoutique(b.dataset.skinBoutique); }
});

// cible : { code, nom, dept, tier (id), pseudo, lat, lon } — capturee AVANT
""")
s = rep(s, "          ${carteAssaut(cible, 'à ' + echapperTexte(cible.pseudo || 'un joueur'))}\n",
           "          ${cible.skin && skinConnu(cible.skin) && !auroreFront(cible.code) ? carteAssautSkin(cible, cible.skin, 'à <b>' + echapperTexte(cible.pseudo || 'un joueur') + '</b>') : carteAssaut(cible, 'à ' + echapperTexte(cible.pseudo || 'un joueur'))}\n")
# 2. le skin demandé avant l'attaque (carte et Combat)
s = rep(s, "    const cibleVue = cibleAssaut(code);\n    const { data, error } = await sb.rpc('attaquer', { p_commune_code: code, p_intensite: intensiteChoisie });\n",
           "    const cibleVue = cibleAssaut(code);\n    cibleVue.skin = await skinCibleFront(code);   // patch230\n    const { data, error } = await sb.rpc('attaquer', { p_commune_code: code, p_intensite: intensiteChoisie });\n")
s = rep(s, "        let { data, error } = await sb.rpc('attaquer', { p_commune_code: code, p_intensite: intensiteChoisie });\n",
           "        cibleVueCombat.skin = await skinCibleFront(code);   // patch230\n        let { data, error } = await sb.rpc('attaquer', { p_commune_code: code, p_intensite: intensiteChoisie });\n")
# 3. le skin de l'assaut est animé, comme dans la grande vitrine
s = rep(s, "    for(const mini of document.querySelectorAll('.c3d .mini, .vt-grande .mini')){",
           "    for(const mini of document.querySelectorAll('.c3d .mini, .vt-grande .mini, .as-carte-skin .mini')){")
s = rep(s, "        if(mini.closest('.c3d, .vt-grande')) continue;   // animées plus haut",
           "        if(mini.closest('.c3d, .vt-grande, .as-carte-skin')) continue;   // animées plus haut")
ecrire('app.js', s)

c = lire('style.css')
c = c.rstrip('\n') + u'''

/* ---------- patch230 : le skin de la cible pendant l'assaut ---------- */
.as-carte.as-carte-skin{ aspect-ratio:auto; height:auto; background:none; border:0; padding:0; overflow:visible; box-shadow:none; display:flex; flex-direction:column; align-items:center; gap:7px; }
.as-carte-skin .mini{ width:100%; content-visibility:visible; box-shadow:0 16px 36px rgba(0,0,0,.45); }
.as-carte-skin .mini:hover{ transform:none; }
.as-skin-qui{ margin:0; font-size:.7rem; color:var(--brume); }
.as-skin-qui b{ color:#fff; }
.as-skin-nom{ border:0; cursor:pointer; font:inherit; font-size:.68rem; font-weight:800; letter-spacing:.03em; padding:4px 10px; border-radius:999px; color:#fff;
  background:rgba(8,16,30,.72); box-shadow:0 0 0 1px rgba(255,255,255,.25); }
.as-skin-nom:hover{ background:rgba(8,16,30,.95); box-shadow:0 0 0 1px var(--c-legendaire); }
.as-skin-nom:focus-visible{ outline:2px solid #fff; outline-offset:2px; }
.as-cib:has(.as-carte-skin) .as-pastilles{ margin-top:12px; }
'''
ecrire('style.css', c)
print('patch230 ok')
