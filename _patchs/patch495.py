# patch495 : les textes suivent s3-49 (une rare demande au moins 20 min, même en siège éclair ; décision de Nataël 17 h 52).
# Règles, « Comment c'est calculé ? », et « elle peut tomber d'un coup » dans Défendre et « Ton clan est assiégé »
# (faux pour une rare et une épique). La fiche du siège lit déjà eclair_min du serveur (« au moins 20 min »). Cloche.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A, H = 'app.js', 'index.html'
rep(H, "une épique demande quand même <b>1 h</b>", "une rare demande quand même <b>20 min</b> et une épique <b>1 h</b>")
rep(A, "      <li><b>Épique en éclair</b> : au moins 1 h, même sans défense.</li>",
       "      <li><b>Rare et épique en éclair</b> : au moins 20 min pour une rare, 1 h pour une épique, même sans défense (10 % tout de suite, le reste suit le temps).</li>")
rep(A, "const etat = m.long ? `<b class=\"sg-long\">Siège long</b> · au plus ${sgNb(m.rythme_h)} points par heure` : `<b class=\"sg-eclair\">Siège éclair</b> · elle peut tomber d'un coup`;",
       "const etat = m.long ? `<b class=\"sg-long\">Siège long</b> · au plus ${sgNb(m.rythme_h)} points par heure` : `<b class=\"sg-eclair\">Siège éclair</b> · ${sgEclairTxt(m.tier)}`;   // patch495")
rep(A, "const etat = m.long ? `<b class=\"sg-long\">Siège long</b>` : `<b class=\"sg-eclair\">Siège éclair</b> · elle peut tomber d'un coup`;",
       "const etat = m.long ? `<b class=\"sg-long\">Siège long</b>` : `<b class=\"sg-eclair\">Siège éclair</b> · ${sgEclairTxt(m.tier)}`;   // patch495")
rep(A, "function sgDuree(min){", "// patch495 : un siège éclair de rare ou d'épique a une durée minimale (s3-49 : rare 20 min, épique 1 h)\n"
       "function sgEclairTxt(tier){ return tier === 'rare' ? 'elle peut tomber 20 min après le début' : tier === 'epique' ? 'elle peut tomber 1 h après le début' : 'elle peut tomber d\\'un coup'; }\n"
       "function sgDuree(min){")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = next(x for x in d if x.get('date') == '2026-11-22')
l = "⏱️ Siège : une rare demande maintenant au moins 20 min, même si personne ne défend (comme l'épique, 1 h). Le propriétaire prévenu a le temps de renforcer. Tu envoies ta vague une fois, l'énergie part toute seule. Commune et peu commune : inchangées. On regarde vos retours."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
