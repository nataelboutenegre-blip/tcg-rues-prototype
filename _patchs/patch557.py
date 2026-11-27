# patch557 (27/11) : trois bugs du salon #bugs.
# 1. Skins de cartes invisibles depuis le 22/11 (Maroli) : patch499 avait mis gl.compileShader dans un commentaire.
# 2. Radar (ASMFCB) : tirer la carte vers le bas relançait la page (geste « tirer pour rafraîchir »).
# 3. Téléphone (Arkhannou) : la barre de patch548 au-dessus de la carte élargissait la page sur les écrans de moins de 393 px.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
D = os.path.dirname(os.path.abspath(__file__))
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
def ajouter(f, src, marque):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if marque in t: print(f'{f} : déjà ajouté'); return
    open(p, 'a', encoding='utf-8').write(open(os.path.join(D, src), encoding='utf-8').read()); print(f'{f} : ajouté')
rep('app.js', "SKIN_GLSL_FIN);   // patch499 gl.compileShader(fs);",
    "SKIN_GLSL_FIN); gl.compileShader(fs);   // patch499 ; patch557 : la compilation était tombée dans le commentaire")
rep('app.js', "    const surCarte = e.target.closest('#mapWrap');",
    "    const surCarte = e.target.closest('#mapWrap, .rd-carte, .mf-cadre, #blApercu, .c3d-scene');   // patch557 : + la carte du Radar et les autres zones qui glissent")
ajouter('style.css', 'patch557.css', 'patch557 : la barre au-dessus de la carte')
p = os.path.join(R, 'data/nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
assert d[0]['date'] in ('2026-11-26', '2026-11-27')
for c in ["Les skins de cartes s'affichent à nouveau (ils avaient disparu depuis le 22 novembre).",
          "Radar : faire glisser la carte vers le bas ne relance plus la page pendant une manche.",
          "Sur les petits téléphones, la page ne dépasse plus de l'écran sur la carte du Territoire.",
          "Classement : le détail de « Mes points » s'ouvre à nouveau pour les grosses collections."]:
    if c not in d[0].setdefault('correctifs', []): d[0]['correctifs'].append(c)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('nouveautes : ok')
