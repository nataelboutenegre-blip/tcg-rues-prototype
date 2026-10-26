# -*- coding: utf-8 -*-
u"""
patch209 — les skins de face s'intègrent mieux à la carte (aperçu validé :
« A · Fondu ») :
- la photo a les coins arrondis d'une carte normale et se fond dans le bas
  de la carte au lieu d'être coupée net ;
- un liseré de la couleur du skin, qui s'efface vers le bas, borde la photo ;
- le cadre du skin devient un filet (plus deux cadres l'un dans l'autre) ;
- la marque du skin passe en bas à droite, petite, avec un losange ; sur les
  cartes étroites (téléphone, choix de la vitrine) il ne reste que le losange ;
- le Brasier : les flammes montent du bas de la photo et débordent un peu ;
- la Gravure garde sa plaque nette (trait d'encre), juste un peu arrondie.
Aucun SQL.
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
assert 'patch209' not in js

# 1. le masque de la photo des skins : coins arrondis (6 px = 7,8 unités) et fondu en bas
INR = u"float inR(vec2 q,vec4 R){ float p=upx(); return smoothstep(R.x-p,R.x+p,q.x)*(1.-smoothstep(R.z-p,R.z+p,q.x))*smoothstep(R.y-p,R.y+p,q.y)*(1.-smoothstep(R.w-p,R.w+p,q.y)); }"
assert js.count(INR) == 1   # dans DOS_GLSL_COMMUN, dont SKIN_GLSL_COMMUN est tiré
js = rep(js, u"""  .replace('vec4 photoRect(float b){ return vec4(b,b,W-b,b+(H-2.*b)*.6); }', 'vec4 photoRect(float b){ return vec4(5.2,5.2,W-5.2,116.); }');""",
u"""  .replace('vec4 photoRect(float b){ return vec4(b,b,W-b,b+(H-2.*b)*.6); }', 'vec4 photoRect(float b){ return vec4(5.2,5.2,W-5.2,116.); }')
  // patch209 : la photo a les coins arrondis d'une carte normale et se fond dans le bas de la carte ;
  // inRnet garde un bord net (la plaque de la Gravure, les flammes du Brasier)
  .replace('""" + INR + u"""',
    'float inR(vec2 q,vec4 R){ vec2 c=(R.xy+R.zw)*.5,h=(R.zw-R.xy)*.5; float p=upx(); return (1.-smoothstep(-p,p,sdBox(q-c,h,7.8)))*(1.-smoothstep(R.w-24.,R.w-1.,q.y)); }\\n'
    + 'float inRnet(vec2 q,vec4 R){ vec2 c=(R.xy+R.zw)*.5,h=(R.zw-R.xy)*.5; float p=upx(); return 1.-smoothstep(-p,p,sdBox(q-c,h,2.5)); }');""")

# 2. les faces des skins
d = js.index(u'const SKIN_GLSL = {'); f = js.index(u'const SKIN_GLSL_FIN = `', d)
sk = js[d:f]
# le cadre du skin devient un filet
sk = rep(sk, u"float b=5.; vec4 R=photoRect(b); float ii=interior(q,b);", u"float b=3.; vec4 R=photoRect(b); float ii=interior(q,b);", 6)
sk = rep(sk, u"float b=7.; vec4 R=photoRect(b); float ii=interior(q,b);", u"float b=4.; vec4 R=photoRect(b); float ii=interior(q,b);")
# le Brasier : les flammes montent du bas de la photo et débordent un peu sur la carte
sk = rep(sk, u"col+=fire(max(fl,0.)*1.7)*ip*(1.-smoothstep(0.,1.2,v));",
             u"col+=fire(max(fl,0.)*1.7)*inRnet(q,vec4(R.xyz,R.w+14.))*(1.-smoothstep(R.w-4.,R.w+14.,q.y))*(1.-smoothstep(0.,1.2,v));")
# la Gravure garde sa plaque nette
sk = rep(sk, u"float b=6.; vec4 R=photoRect(b); float ip=inR(q,R); vec3 ink=vec3(.19,.13,.07);",
             u"float b=6.; vec4 R=photoRect(b); float ip=inRnet(q,R); vec3 ink=vec3(.19,.13,.07);")
sk = rep(sk, u"float dr=abs(sdBox(q-(R.xy+R.zw)*.5,(R.zw-R.xy)*.5,0.));", u"float dr=abs(sdBox(q-(R.xy+R.zw)*.5,(R.zw-R.xy)*.5,2.5));")
js = js[:d] + sk + js[f:]

# 3. la marque : sur une carte étroite, seulement le losange
js = rep(js, u"    if(m){ if(anime) m.remove(); else m.textContent = SKIN_NOMS[k]; }",
u"""    if(m){ if(anime) m.remove(); else { m.textContent = SKIN_NOMS[k]; m.classList.toggle('court', (mini.offsetWidth || 150) < 130); } }   // patch209""")
ecrire('app.js', js)

css = lire('style.css')
assert 'patch209' not in css
css = rep(css, u""".mini .skin-marque{ position: absolute; right: 6px; top: 6px; z-index: 2; font: 700 8px/1 var(--texte, sans-serif); letter-spacing: .08em; text-transform: uppercase;
  padding: 3px 5px; border-radius: 999px; background: rgba(8,19,37,.75); color: #fff; pointer-events: none; }""",
u""".mini .skin-marque{ position: absolute; right: 7px; bottom: 9px; z-index: 2; font: 700 7px/1 var(--texte, sans-serif); letter-spacing: .12em; text-transform: uppercase;
  display: inline-flex; align-items: center; gap: 3px; color: var(--sk-acc, #fff); opacity: .9; pointer-events: none; }   /* patch209 */""")
ACC = [('comete', '#9FC0FF'), ('juillet', '#FF6B77'), ('maree', '#7FE8FF'), ('feu', '#FF9A4A'), ('prisme', '#D7B8FF'),
       ('orfondu', '#F3CD6A'), ('neon', '#FF5BE3'), ('gravure', '#5A4426'), ('orage', '#B9CCEA')]
css = css.rstrip('\n') + u"""

/* ---------- patch209 : le skin mieux fondu dans la carte ---------- */
""" + u'\n'.join(u'.mini.skin-%s{ --sk-acc: %s; }' % a for a in ACC) + u"""
/* un liseré de la couleur du skin autour de la photo, qui s'efface vers le bas comme la photo */
.mini.skin .mini-art::after{ content: ''; position: absolute; inset: 0; border-radius: inherit; pointer-events: none; z-index: 2; padding: 1px; opacity: .7;
  background: linear-gradient(180deg, color-mix(in srgb, var(--sk-acc) 75%, #fff) 0%, color-mix(in srgb, var(--sk-acc) 40%, transparent) 45%, transparent 80%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor; mask-composite: exclude; }
.mini.skin-gravure .mini-art::after{ display: none; }
.mini .skin-marque::before{ content: ''; flex: none; width: 5px; height: 5px; transform: rotate(45deg); background: currentColor; border-radius: 1px; }
.mini .skin-marque.court{ font-size: 0; gap: 0; right: 6px; bottom: 8px; }
"""
ecrire('style.css', css)
print(u'patch209 applique. Lancer : python3 maj-version.py')
