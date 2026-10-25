# -*- coding: utf-8 -*-
u"""
patch183 — on retourne une carte de la vitrine d'un joueur : on voit SON dos
de carte équipé, pas le sien. Demande _sql/s2-25-dos-visible.sql (sans lui,
on voit son propre dos, comme avant).
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
js = lire('app.js'); css = lire('style.css')
assert 'patch183' not in js

# le dos de la scene 3D peut etre celui d'un autre joueur
js = rempl(js, u"""function carte3dFin(){
  return `</div><span class="c3d-reflet"></span></div>
      <div class="c3d-face c3d-dos"><div class="c3d-base"><div class="face face-back c3d-dosint">${DOS_MOTIF_SVG}
        <span class="dos-coin hg"></span><span class="dos-coin hd"></span><span class="dos-coin bg"></span><span class="dos-coin bd"></span>
        <div class="dos-embleme">${ICONE_EPINGLE}</div></div></div><span class="c3d-reflet"></span></div>""",
u"""function carte3dFin(dos){
  // patch183 : dos = la cle d'un dos (celui d'un autre joueur) ; sinon le mien
  const autre = typeof dos === 'string' && /^[a-z0-9-]+$/.test(dos);
  return `</div><span class="c3d-reflet"></span></div>
      <div class="c3d-face c3d-dos"><div class="c3d-base">${autre ? `<div class="bq-dos-apercu c3d-dosde" data-dos="${dos}">` : ''}<div class="face face-back c3d-dosint">${DOS_MOTIF_SVG}
        <span class="dos-coin hg"></span><span class="dos-coin hd"></span><span class="dos-coin bg"></span><span class="dos-coin bd"></span>
        <div class="dos-embleme">${ICONE_EPINGLE}</div></div>${autre ? '</div>' : ''}</div><span class="c3d-reflet"></span></div>""", 'carte3dFin')

# la vitrine lit le dos equipe du joueur
js = rempl(js, u"""  let s1 = new Set();   // patch170""",
u"""  let dos;   // patch183 : undefined = inconnu (SQL pas passe), on garde le mien
  try{ const r4 = await sb.rpc('dos_equipe', { p_joueur: id }); if(!r4.error) dos = dosCle(r4.data || null); }catch(err){}
  let s1 = new Set();   // patch170""", 'lecture dos')
js = rempl(js, u"""    source: r.source === 'front' ? 'front' : 'terra',   // patch180""",
u"""    source: r.source === 'front' ? 'front' : 'terra',   // patch180
    dos,""", 'carte dos')

# la carte de vitrine en grand montre ce dos
js = rempl(js, u"""      <div class="fc-tete">${carte3dDebut(150, 225, 1.65)}${miniTerra({ ...e, exemplaires: 1 })}${carte3dFin()}</div>""",
u"""      <div class="fc-tete">${carte3dDebut(150, 225, 1.65)}${miniTerra({ ...e, exemplaires: 1 })}${carte3dFin(e.dos)}</div>""", 'vitrine grand')

css += u"""
/* patch183 : le dos d'un autre joueur dans la scene 3D */
.c3d-base > .bq-dos-apercu.c3d-dosde{ position: absolute; inset: 0; width: auto; height: auto; margin: 0; }
"""
ecrire('app.js', js); ecrire('style.css', css)
print(u'patch183 appliqué')
