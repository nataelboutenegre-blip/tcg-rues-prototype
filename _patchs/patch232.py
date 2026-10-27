# -*- coding: utf-8 -*-
u"""
patch232 — l'assaut montre l'Aurore (retour de Nataël le 27/10 : il attaque
une Aurore, la carte n'est pas Aurore pendant l'animation).

L'écran d'assaut ne savait dessiner que la carte simple. Maintenant, des deux
côtés :
- une commune Aurore apparaît en vraie carte Aurore, avec « ✦ Aurore » ;
- une carte habillée apparaît avec son skin (la cible, avec le lien vers la
  Boutique, comme au patch230 ; ma carte aussi, sans lien).
Sinon, la carte simple, comme avant.
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
assert 'patch232' not in s
s = rep(s, "function carteAssautSkin(e, k, qui){\n",
"""// patch232 : la vraie carte dans l'assaut, Aurore ou habillée ; lien = étiquette vers la Boutique
function carteAssautReelle(e, qui, k, au, lien){
  const t = e.tier && e.tier.id ? e.tier : (TIERS.find(x => x.id === e.tier) || TIERS[0]);
  const sk = !au && k && skinConnu(k) ? k : undefined;
  const etiquette = au ? '<span class="as-skin-nom as-aurore-nom">✦ Aurore</span>'
    : sk && lien ? `<button type="button" class="as-skin-nom" data-skin-boutique="${echapperTexte(sk)}">✦ Skin ${echapperTexte(SKIN_NOMS[sk] || sk)}</button>` : '';
  return `<div class="as-carte as-carte-skin ${t.id}">${miniTerra({ code: e.code, nom: e.nom, dept: e.dept, tier: t, exemplaires: 1, photo: e.photo,
      rank: e.tierSize ? e.rank : undefined, tierSize: e.tierSize, aurore: au ? 1 : 0, skin: sk })}
    <p class="as-skin-qui">${qui}</p>${etiquette}</div>`;
}
function carteAssautSkin(e, k, qui){
""")
# ma carte : Aurore ou habillée
s = rep(s, "        <div class=\"as-cote as-att\">${proche ? carteAssaut(proche.entry, 'à toi') : '<div class=\"as-carte vide\"></div>'}",
           "        <div class=\"as-cote as-att\">${proche ? ((SAISON2 && (auroreFront(proche.entry.code) || skinDeMaCarte('front', proche.entry.code)))"
           " ? carteAssautReelle(proche.entry, 'à toi', skinDeMaCarte('front', proche.entry.code), auroreFront(proche.entry.code), false)"
           " : carteAssaut(proche.entry, 'à toi')) : '<div class=\"as-carte vide\"></div>'}")
# la cible : Aurore ou habillée
s = rep(s, "          ${cible.skin && skinConnu(cible.skin) && !auroreFront(cible.code) ? carteAssautSkin(cible, cible.skin, 'à <b>' + echapperTexte(cible.pseudo || 'un joueur') + '</b>') : carteAssaut(cible, 'à ' + echapperTexte(cible.pseudo || 'un joueur'))}\n",
           "          ${SAISON2 && (auroreFront(cible.code) || (cible.skin && skinConnu(cible.skin))) ? carteAssautReelle(cible, 'à <b>' + echapperTexte(cible.pseudo || 'un joueur') + '</b>', cible.skin, auroreFront(cible.code), true) : carteAssaut(cible, 'à ' + echapperTexte(cible.pseudo || 'un joueur'))}\n")
# la photo de la cible vient aussi du Combat (patch231 la charge)
s = rep(s, "    lat: c.lat, lon: c.lon, pop: c.pop, photo: c.photo || '', rank: c.rank,",
           "    lat: c.lat, lon: c.lon, pop: c.pop, photo: c.photo || (repli && repli.photo) || '', rank: c.rank || (repli && repli.rang), tierSize: c.tierSize || (repli && repli.palier_total),   // patch232")
ecrire('app.js', s)
c = lire('style.css')
c = c.rstrip('\n') + u'''

/* ---------- patch232 : l'Aurore dans l'assaut ---------- */
.as-skin-nom.as-aurore-nom{ cursor:default; color:#06231A; background:linear-gradient(90deg, #7FF2D0, #8FB4FF 55%, #C9A6FF); box-shadow:0 0 14px rgba(61,242,192,.35); }
.as-att .as-carte-skin + .as-proche{ margin-top:10px; }
'''
ecrire('style.css', c)
print('patch232 ok')
