# patch475 : trois retours d'Oshannir (20/11)
# 1. Le calcul des points (Cartes) montrait « 60 », « 45 » et « . » sur trois lignes : la règle
#    « .cl-calc-l span{display:block} » passait devant celle qui cache le chiffre de l'autre saison.
# 2. Pendant le compte à rebours, la jauge disait « La fin de saison s'enclenche à 3000 » au lieu de la date de fin.
# 3. Sur téléphone, toucher vite (la roue) zoomait la page : plus de zoom au double toucher (le pincement reste possible).
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
rep('style.css', ".cl-calc-l span{ display:block; font-size:.76rem; color:#C9D3E3; line-height:1.45; }",
    ".cl-calc-l > div > span{ display:block; font-size:.76rem; color:#C9D3E3; line-height:1.45; }   /* patch475 : pas les span dedans */")
rep('app.js', "  if(s.fin_prevue && s.etat === 'en_cours'){",
    "  if(s.fin_prevue && (s.etat === 'en_cours' || s.etat === 'compte_a_rebours')){   // patch475 : aussi pendant le compte à rebours")
rep('style.css', ".nom-s3{ display: none; }",
    ".nom-s3{ display: none; }\n"
    "/* patch475 : pas de zoom au double toucher sur téléphone (toucher vite la roue zoomait la page) ; le pincement reste */\n"
    ":where(html, button, a, [role=\"button\"], input, label){ touch-action: manipulation; }")
print('patch475 : fini')
