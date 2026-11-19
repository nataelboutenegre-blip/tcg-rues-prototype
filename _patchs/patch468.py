# patch468 : cinq dos de carte assortis aux nouveaux skins (Givre, Vitrail, Topo, Aquarelle, Kintsugi).
# Idée de Nataël (19/11/2026) : vendre le recto et le verso ensemble. Les dos sont dessinés par la carte graphique,
# au même format que les dos premium (DOS_GLSL). Invisibles tant que les articles dos-<clé> / pack-<clé> n'existent
# pas en base (_sql/s3-36-dos-assortis.sql) : personne ne peut les porter ni les voir en boutique.
# Sources : _patchs/patch468-dos.js (les cinq dessins) et _patchs/patch468-dos.css (liseré, coins, épingle).
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
ICI = os.path.dirname(os.path.abspath(__file__))
lire = lambda f: open(os.path.join(ICI, f), encoding='utf-8').read()

p = os.path.join(R, 'app.js'); t = open(p, encoding='utf-8').read()
if 'patch468' in t: print('app.js : déjà fait')
else:
    a = "const DOS_GLSL_FIN = `"
    assert t.count(a) == 1, t.count(a)
    t = t.replace(a, lire('patch468-dos.js') + a)
    # image figée (appareil réglé sur « moins de mouvement ») : Topo sans la bande du relevé
    b = "const DOS_T_FIXE = { orage: 4.62, juillet: .9 };"
    assert t.count(b) == 1
    t = t.replace(b, "const DOS_T_FIXE = { orage: 4.62, juillet: .9, topo: 4. };   // patch468 : topo")
    open(p, 'w', encoding='utf-8').write(t); print('app.js : ok')

p = os.path.join(R, 'style.css'); t = open(p, encoding='utf-8').read()
if 'patch468' in t: print('style.css : déjà fait')
else:
    open(p, 'w', encoding='utf-8').write(t.rstrip('\n') + '\n\n' + lire('patch468-dos.css')); print('style.css : ok')
print('patch468 : fini')
