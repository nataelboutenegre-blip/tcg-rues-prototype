# patch503 : sur téléphone (topo), quand le bouton Boutique (sac) est affiché, le sélecteur Terra / Front
# recouvrait la cloche des notifications (place prévue : cloche + règles seulement). Dans ce cas, le livre des
# règles quitte l'en-tête (il reste dans le menu Plus) et la cloche retrouve sa place.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
p = os.path.join(R, 'style.css'); t = open(p, encoding='utf-8').read()
M = '/* patch503 : la cloche ne passe plus sous le sélecteur quand le sac de la boutique est là */'
if M not in t:
    t = t.rstrip('\n') + '\n\n' + M + '\n@media (max-width: 720px){\n  html.topo:has(#bqrMobile:not([hidden])) #reglesBtnMobile{ display:none; }\n  html.topo:has(#bqrMobile:not([hidden])) .mode-bascule{ right:112px; }\n}\n'
    open(p, 'w', encoding='utf-8').write(t); print('style.css : ok')
