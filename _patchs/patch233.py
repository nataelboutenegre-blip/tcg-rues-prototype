# -*- coding: utf-8 -*-
u"""
patch233 — dire qu'un skin ne se gagne pas en prenant la commune (27/10).
- Assaut : sous « ✦ Skin … » de la cible, une ligne : le skin reste à son
  propriétaire.
- Règles (Front) : un paragraphe « Aurore et skins ».
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
assert 'patch233' not in s
s = rep(s, "    : sk && lien ? `<button type=\"button\" class=\"as-skin-nom\" data-skin-boutique=\"${echapperTexte(sk)}\">✦ Skin ${echapperTexte(SKIN_NOMS[sk] || sk)}</button>` : '';",
           "    : sk && lien ? `<button type=\"button\" class=\"as-skin-nom\" data-skin-boutique=\"${echapperTexte(sk)}\">✦ Skin ${echapperTexte(SKIN_NOMS[sk] || sk)}</button>`\n"
           "      + '<span class=\"as-skin-note\">Le skin reste à son propriétaire, même si tu prends la commune.</span>' : '';   // patch233")
ecrire('app.js', s)

h = lire('index.html')
h = rep(h, "            <p>Astuce : dans Combat comme dans Échange, sépare tes critères par une virgule.",
           "            <p><b>Aurore et skins</b> : une commune Aurore reste Aurore quand elle change de main ; dans un paquet Front, une commune de la liste Aurore sort en Aurore une fois sur trois. Un skin, lui, appartient à celui qui l'a acheté : prendre une commune habillée ne te donne pas son skin, elle prend ton apparence.</p>\n"
           "            <p>Astuce : dans Combat comme dans Échange, sépare tes critères par une virgule.")
ecrire('index.html', h)

c = lire('style.css')
c = c.rstrip('\n') + u'''

/* ---------- patch233 : le skin ne se gagne pas ---------- */
.as-skin-note{ display:block; max-width:150px; text-align:center; font-size:.6rem; line-height:1.35; color:var(--brume); }
'''
ecrire('style.css', c)
print('patch233 ok')
