# patch490 : sur les cartes v2, le bandeau du monument recouvrait le nom et le département posés sur la photo
# (capture de Nataël, 22/11 12 h 26 : Périgueux, cathédrale Saint-Front). Le bandeau reste en bas de la photo ;
# le nom et le département montent d'un cran quand la commune a un monument. CSS seulement.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
p = os.path.join(R, 'style.css'); t = open(p, encoding='utf-8').read()
MARQUE = '/* ---------- patch490 : cartes v2, le monument ne recouvre plus le nom ---------- */'
if MARQUE in t:
    print('style.css : déjà fait'); sys.exit(0)
P = 'html.topo:not(.sans-cartes)'
S1 = ':not(.skin):not(.aurore):not(.atl):not(.bri):not(.ecl):not(.hnt)'      # les cartes v2 (patch465)
S2 = ':is(.bri, .ecl):not(.skin):not(.aurore):not(.hnt)'                      # brillantes et éclats (patch488)
css = ['', MARQUE]
for S in (S1, S2):
    C = f'{P} .card.a-monument{S}'
    css += [
        f'{C} .carte-monument{{ left:9px; right:9px; bottom:8px; z-index:3; }}',
        f'{C} .carte-nom{{ bottom:calc(38% + 25px + 30px); }}',
        f'{C} .carte-departement{{ bottom:calc(38% + 9px + 30px); }}',
    ]
css.append('@media (max-width: 760px){')
for S in (S1, S2):
    C = f'{P} .card.a-monument{S}'
    css += [
        f'  {C} .carte-monument{{ left:7px; right:7px; bottom:6px; }}',
        f'  {C} .carte-nom{{ bottom:calc(38% + 22px + 26px); }}',
        f'  {C} .carte-departement{{ bottom:calc(38% + 9px + 26px); }}',
    ]
css.append('}')
open(p, 'a', encoding='utf-8').write('\n'.join(css) + '\n')
print('style.css : ok')
