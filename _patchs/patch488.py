# patch488 : les brillantes et les éclats passent aux cartes v2 (demande de Nataël, 22/11 12 h 08).
# Jusque-là, patch465 les laissait dans l'ancienne mise en page. Maintenant : grande photo, nom posé dessus,
# plaque du département, rareté en pastille, comme les autres cartes ; et leurs effets suivent la photo, comme
# les nouveaux skins : le film holographique d'une brillante teinte la photo sans la cacher (le papier du bas
# reste nacré), l'éclat pose une lumière dorée en haut de la photo et réchauffe la carte.
# CSS seulement. S'éteint avec les cartes v2 (config_jeu 'interface'.cartes = 0) : l'ancien aspect revient.
# Les cartes qui portent un skin, une Aurore ou une carte hantée gardent leur aspect.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
p = os.path.join(R, 'style.css'); t = open(p, encoding='utf-8').read()
MARQUE = '/* ---------- patch488 : brillantes et éclats en cartes v2 ---------- */'
if MARQUE in t:
    print('style.css : déjà fait'); sys.exit(0)

SUF = ':not(.skin):not(.aurore):not(.atl):not(.bri):not(.ecl):not(.hnt)'
SUF2 = ':is(.bri, .ecl):not(.skin):not(.aurore):not(.hnt)'
debut = t.index('/* ---------- patch465 : cartes v2 (piste A), saison 3 ---------- */')
lignes = [l for l in t[debut:].split('\n') if ('.mini' + SUF) in l or ('.card' + SUF) in l]
assert len(lignes) >= 60, len(lignes)
# 1. la mise en page v2, telle quelle, pour les brillantes et les éclats (les cadres par rareté compris)
copie = [l.replace('.mini' + SUF, '.mini' + SUF2).replace('.card' + SUF, '.card' + SUF2) for l in lignes]
dans_media = [l for l in copie if l.startswith('  ')]
hors_media = [l for l in copie if not l.startswith('  ')]

P = 'html.topo:not(.sans-cartes)'
N = ':not(.skin):not(.aurore):not(.hnt)'
MB, ME = f'{P} .mini.bri{N}', f'{P} .mini.ecl{N}'
CB, CE = f'{P} .card.bri{N}', f'{P} .card.ecl{N}'
css = ['', MARQUE] + hors_media + ['@media (max-width: 600px){'] + dans_media + ['}']
css += [
    '/* --- la brillante : le film holographique suit la photo, le papier du bas est nacré --- */',
    f'{MB}{{ --ep:3px; }} {MB}.commun, {MB}.peucommun{{ --ep:2px; }}',
    f'{CB} .carte-cadre{{ --ep:5px; }} {CB}.commun .carte-cadre, {CB}.peucommun .carte-cadre{{ --ep:4px; }} {CB}.legendaire .carte-cadre{{ --ep:6px; }}',
    # la photo garde ses formes : le film ne change que sa couleur, puis un reflet qui passe
    f'{MB} .bx-b-art, {CB} .bx-b-art{{ z-index:1; mix-blend-mode:color; opacity:.5; background-size:300% 300%; }}',
    f'{MB} .bx-b-art::after, {CB} .bx-b-art::after{{ mix-blend-mode:overlay; opacity:.55; }}',
    f'{MB} .bx-b-art::before, {CB} .bx-b-art::before{{ content:""; position:absolute; inset:0; mix-blend-mode:soft-light;',
    '  background: linear-gradient(118deg, transparent 30%, rgba(255,255,255,.85) 46%, rgba(255,255,255,.2) 54%, transparent 68%);',
    '  background-size:260% 260%; background-position: calc(var(--bx-px) * 1%) calc(var(--bx-py) * 1%); }',
    f'{MB} .bx-b-paillettes, {CB} .bx-b-paillettes{{ z-index:1; opacity:.9; }}',
    # le bas de la carte : papier nacré et courbes irisées, seulement sous la photo
    f'{MB} .bx-b-voile, {MB} .bx-b-courbes{{ top:64%; }}',
    f'{CB} .bx-b-voile, {CB} .bx-b-courbes{{ top:62%; }}',
    f'{MB} .bx-b-voile, {CB} .bx-b-voile{{ opacity:.5; }}',
    f'{MB} .bx-b-courbes, {CB} .bx-b-courbes{{ opacity:.4; -webkit-mask-size:100% 280%; mask-size:100% 280%; -webkit-mask-position:center bottom; mask-position:center bottom; }}',
    f'{MB} .bx-b-reflet, {CB} .bx-b-reflet{{ opacity:.5; }}',
    f'{MB} .mini-infos, {CB} .carte-int{{ background-image:none; }}',
    '/* --- l\'éclat : une lumière dorée en haut de la photo, la carte réchauffée --- */',
    f'{ME} .bx-e-rayons, {ME} .bx-e-noyau{{ --pin-x:50% !important; --pin-y:30% !important; z-index:1; }}',
    f'{CE} .bx-e-rayons, {CE} .bx-e-noyau{{ --pin-x:50% !important; --pin-y:30% !important; z-index:1; }}',
    f'{ME} .mini-art::after, {CE} .carte-art::after{{ background: radial-gradient(120% 90% at 50% 28%, rgba(255,214,120,.34) 0%, rgba(255,170,60,.12) 46%, transparent 72%),',
    '  linear-gradient(180deg, rgba(60,30,0,0) 40%, rgba(46,24,2,.86) 100%); }',
    f'{ME} .mini-nom, {CE} .carte-nom{{ color:#FFE9A8; text-shadow:0 1px 3px rgba(40,20,0,.6); }}',
    f'{CE} .carte-departement{{ color:#F6E3B4; }}',
    f'{ME}:not(.bri) .mini-infos{{ background: repeating-radial-gradient(ellipse at 88% 130%, transparent 0 11px, rgba(176,120,16,.11) 11px 12px), linear-gradient(180deg, #FFF9EA, #FBEDC6); }}',
    f'{CE}:not(.bri) .carte-int{{ background: repeating-radial-gradient(ellipse at 88% 130%, transparent 0 11px, rgba(176,120,16,.11) 11px 12px), linear-gradient(180deg, #FFF9EA, #FBEDC6); }}',
    # la lueur colle au bord de la carte (2 px plus loin, l'ombre de la carte faisait un liseré sombre)
    f'{ME} > .bx-e-aura, {CE} .bx-e-aura{{ inset:0; border-radius:var(--r); }}',
    '/* --- les sceaux, sur la photo --- */',
    f'{P} .mini:is(.bri, .ecl){N} .bx-sceau{{ z-index:4; }}',
    f'{P} .card:is(.bri, .ecl){N} .bx-sceau{{ z-index:4; left:8px; top:8px; height:19px; padding:0 9px 0 7px; font-size:8.4px; }}',
    f'{P} .card:is(.bri, .ecl){N} .bx-sceau b{{ font-size:9.6px; }}',
    f'{P} .card:is(.bri, .ecl){N} .bx-sceau + .bx-sceau{{ top:31px; }}',
    # une carte suisse, belge, luxembourgeoise ou d'outre-mer a déjà son drapeau en haut à gauche : les sceaux se décalent
    f'{P} .mini:is(.bri, .ecl):is(.suisse, .belgique, .luxembourg, .outremer){N} .bx-sceau{{ left:25px; }}',
    f'{P} .mini:is(.bri, .ecl):is(.suisse, .belgique, .luxembourg, .outremer){N} .bx-sceau + .bx-sceau{{ left:42px; }}',
    f'{P} .c3d .mini:is(.bri, .ecl):is(.suisse, .belgique, .luxembourg, .outremer){N} .bx-sceau{{ left:3px; top:24px; }}',
    f'{P} .c3d .mini:is(.bri, .ecl):is(.suisse, .belgique, .luxembourg, .outremer){N} .bx-sceau + .bx-sceau{{ left:3px; top:40px; }}',
    f'{P} .card:is(.bri, .ecl):is(.suisse, .belgique, .luxembourg, .outremer){N} .bx-sceau{{ top:36px; }}',
    f'{P} .card:is(.bri, .ecl):is(.suisse, .belgique, .luxembourg, .outremer){N} .bx-sceau + .bx-sceau{{ top:59px; }}',
]
open(p, 'a', encoding='utf-8').write('\n'.join(css) + '\n')
print(f'style.css : ok ({len(lignes)} règles de mise en page reprises)')
