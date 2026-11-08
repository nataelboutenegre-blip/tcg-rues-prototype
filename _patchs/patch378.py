# patch378 (8/11/2026) : l'impact de la bombe sur la carte en direct (s2-120).
# Aperçu validé le 5/11 (2e partie), « ok pour la carte en direct » le 8/11 à 15 h 35.
#   - direct/bombe.js (nouveau) : zoom sur la zone, viseur, flash plein écran, trois ondes,
#     tremblement, garnisons soufflées, carton « 💥 BOMBE SUR … », retour à la France à 9 s ;
#     le cercle reste 24 h ; ?bombe=demo pour une démonstration ;
#   - recherche.js (page TikTok) : ne prend plus les bombes dans son zoom auto et attend
#     la fin de l'animation avant la fiche suivante ou une demande de la régie ;
#   - styles dans direct.css ; versions des fichiers montées à la main.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:80]!r}'
    return s.replace(avant, apres)

R = pathlib.Path('direct/recherche.js'); r = R.read_text(encoding='utf-8')
assert 'patch378' not in r
r = rep(r, "    if(!ATTAQUES || !e || !['conquete', 'defense', 'bombe'].includes(e[1])) return;",
           "    if(!ATTAQUES || !e || !['conquete', 'defense'].includes(e[1])) return;   // patch378 : les bombes ont leur animation (bombe.js)")
r = rep(r, "    if(codeAffiche || maintenant < pauseJusqua) return;",
           "    if(codeAffiche || maintenant < pauseJusqua || window.BOMBE_EN_COURS) return;   // patch378")
r = rep(r, "    if(enCours || !D.cat || !D.chemins.size) return;",
           "    if(enCours || !D.cat || !D.chemins.size || window.BOMBE_EN_COURS) return;   // patch378 : la demande attend la fin de la bombe")
R.write_text(r, encoding='utf-8')

C = pathlib.Path('direct/direct.css'); c = C.read_text(encoding='utf-8')
assert 'patch378' not in c
c += """
/* patch378 : l'impact d'une bombe */
.carte canvas.bombe-fx{ pointer-events:none; cursor:default; }
.bombe-flash{ position:absolute; inset:0; z-index:30; pointer-events:none; opacity:0;
  background:radial-gradient(circle at 29% 50%, rgba(255,255,255,.95), rgba(255,200,180,.6) 40%, rgba(255,90,82,.25) 75%); }
.vertical .bombe-flash{ background:radial-gradient(circle at 50% 45%, rgba(255,255,255,.95), rgba(255,200,180,.6) 40%, rgba(255,90,82,.25) 75%); }
.bombe-carton{ position:absolute; left:560px; bottom:64px; z-index:31; pointer-events:none; opacity:0; text-align:center; min-width:520px;
  transform:translate(-50%, 0) scale(.6); transition:transform .45s cubic-bezier(.2,.9,.3,1.3), opacity .3s;
  background:linear-gradient(90deg,#5a1a1f,#13284A 70%); border:3px solid rgba(255,90,82,.9); border-radius:20px; padding:16px 34px;
  box-shadow:0 0 60px rgba(255,90,82,.45); color:#fff; }
.bombe-carton.vu{ transform:translate(-50%, 0) scale(1); opacity:1; }
.bombe-carton .gros{ font-family:var(--titre); font-weight:900; font-size:62px; line-height:1; letter-spacing:.03em; white-space:nowrap; }
.bombe-carton .detail{ color:#FFD2CE; font-size:24px; margin-top:8px; white-space:nowrap; }
.bombe-carton .detail b{ color:#fff; }
.vertical .bombe-carton{ left:540px; top:1140px; bottom:auto; width:max-content; max-width:920px; padding:14px 26px; }
.vertical .bombe-carton .gros{ font-size:48px; white-space:normal; }
.vertical .bombe-carton .detail{ font-size:22px; white-space:normal; }
"""
C.write_text(c, encoding='utf-8')

for f in ['direct/index.html', 'direct/tiktok.html']:
    P = pathlib.Path(f); h = P.read_text(encoding='utf-8')
    assert 'bombe.js' not in h
    h = rep(h, '<link rel="stylesheet" href="direct.css?v=3">', '<link rel="stylesheet" href="direct.css?v=4">')
    if 'recherche.js' in h:
        h = rep(h, '<script defer src="recherche.js?v=3"></script>', '<script defer src="recherche.js?v=4"></script>\n<script defer src="bombe.js?v=1"></script>')
    else:
        h = rep(h, '<script defer src="direct.js?v=4"></script>', '<script defer src="direct.js?v=4"></script>\n<script defer src="bombe.js?v=1"></script>')
    P.write_text(h, encoding='utf-8')
print('patch378 ok')
