# patch480 : la finition Or de l'atelier, dernière récompense du pass complet de la saison 3 (avec s3-39).
# L'atelier dit où la gagner ; la piste du pass montre une carte dorée ; le pass sait réclamer un élément de l'atelier.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
rep(A, "  { id: 'or', nom: 'Or', src: 'pass', comment: 'Pass de saison · bientôt' }",
       "  { id: 'or', nom: 'Or', src: 'pass', comment: 'Pass de saison 3 · niveau 20' }   // patch480")
rep(A, "const PS_TYPE = { tp: 'TerraPoints', energie: 'Énergie', titre: 'Titre', dos: 'Dos de carte', habillage: 'Habillage de paquet', skin: 'Skin de carte', paquet: '5 communes', lingots: 'Lingots' };",
       "const PS_TYPE = { tp: 'TerraPoints', energie: 'Énergie', titre: 'Titre', dos: 'Dos de carte', habillage: 'Habillage de paquet', skin: 'Skin de carte', paquet: '5 communes', lingots: 'Lingots', atelier: 'Finition de l’atelier' };   // patch480 : atelier\n"
       "PS_ICO.atelier = '<svg viewBox=\"0 0 56 56\" aria-hidden=\"true\"><defs><linearGradient id=\"psOr\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\"><stop offset=\"0\" stop-color=\"#8A5A10\"/><stop offset=\".45\" stop-color=\"#F0B429\"/><stop offset=\".58\" stop-color=\"#FFF1B8\"/><stop offset=\"1\" stop-color=\"#8A5A10\"/></linearGradient></defs><rect x=\"13\" y=\"6\" width=\"30\" height=\"44\" rx=\"4\" fill=\"url(#psOr)\" stroke=\"#0B1830\" stroke-width=\"2\"/><path d=\"M18 16c4-3 8 3 12 0s7 1 9-1\" stroke=\"rgba(255,248,220,.75)\" stroke-width=\"1.6\" fill=\"none\"/><path d=\"M18 23c4-3 8 3 12 0s7 1 9-1\" stroke=\"rgba(255,248,220,.6)\" stroke-width=\"1.4\" fill=\"none\"/></svg>';")
rep(A, "  if(t === 'paquet') return psxSachet(r.valeur);\n",
       "  if(t === 'paquet') return psxSachet(r.valeur);\n"
       "  if(t === 'atelier') return `<span class=\"psx-or\" aria-hidden=\"true\"><i></i><b>Or</b></span>`;   // patch480 : la finition Or\n")
rep(A, "r.type === 'dos' || r.type === 'habillage' || r.type === 'skin' ? ' : dans Profil › Personnaliser.' : '')",
       "r.type === 'dos' || r.type === 'habillage' || r.type === 'skin' ? ' : dans Profil › Personnaliser.' : r.type === 'atelier' ? ' : dans Profil › Personnaliser › L’atelier.' : '')")
rep('style.css', ".as-zone-garn{",
""".psx-or{ position:relative; display:block; width:46px; height:66px; margin:auto; border-radius:6px; overflow:hidden;   /* patch480 : la finition Or dans le pass */
  background:linear-gradient(140deg, #8A5A10, #F0B429 40%, #FFF1B8 55%, #C9952A 70%, #8A5A10); box-shadow:0 4px 10px rgba(0,0,0,.4), inset 0 0 0 1.5px rgba(255,241,184,.55); }
.psx-or i{ position:absolute; inset:0; background:linear-gradient(115deg, transparent 35%, rgba(255,250,220,.8) 50%, transparent 65%); background-size:300% 100%; animation:psxOr 3.2s ease-in-out infinite; }
.psx-or b{ position:absolute; left:0; right:0; bottom:6px; text-align:center; font:900 13px/1 "Big Shoulders Display", Impact, sans-serif; letter-spacing:.06em; color:#5A3A06; text-shadow:0 1px 0 rgba(255,241,184,.6); }
@keyframes psxOr{ 0%{ background-position:100% 0; } 60%,100%{ background-position:0 0; } }
@media (prefers-reduced-motion: reduce){ .psx-or i{ animation:none; } }
.as-zone-garn{""")
rep(A, "const PSX_TYPE = { tp: 'TerraPoints', energie: 'Énergie', titre: 'Titre de profil', dos: 'Dos de carte', habillage: 'Habillage de paquet', skin: 'Skin de carte', paquet: '5 communes', lingots: 'Lingots' };",
       "const PSX_TYPE = { tp: 'TerraPoints', energie: 'Énergie', titre: 'Titre de profil', dos: 'Dos de carte', habillage: 'Habillage de paquet', skin: 'Skin de carte', paquet: '5 communes', lingots: 'Lingots', atelier: 'Finition de l’atelier, sur toutes tes cartes Terra' };   // patch480")
print('patch480 : fini')
