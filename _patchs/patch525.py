# patch525 : la nuit (0 h – 7 h), le Front ne dort plus : les attaques font moitié moins de dégâts (s3-65, décision
# de Nataël le 24/11 à 8 h 58). Le bouton d'attaque n'est plus fermé la nuit ; l'encadré 🌙, « Comment c'est calculé ? »,
# les règles et le Guide disent la nouvelle règle. SG_NUIT_MODE = 'ferme' redonnerait l'affichage de la coupure.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js', "function sgNuit(){\n", "const SG_NUIT_MODE = 'moitie';   // patch525 : 'moitie' (dégâts ÷ 2 la nuit) ou 'ferme' (la coupure du 23/11)\nfunction sgNuit(){\n")
rep('app.js', "  const nuit = suffit && sgNuit();   // patch510 : la nuit, elle ne tombe pas avant 7 h",
              "  const nuit = suffit && sgNuit() && SG_NUIT_MODE !== 'moitie';   // patch510, patch525")
rep('app.js', "(r.finit ? (sgNuit() ? 'elle pourra tomber à 7 h au plus tôt' :", "(r.finit ? (sgNuit() && SG_NUIT_MODE !== 'moitie' ? 'elle pourra tomber à 7 h au plus tôt' :")
rep('app.js', "  const bloque = sgNuit() ? '🌙 Le Front dort jusqu\\'à 7 h'   // patch510",
              "  const bloque = sgNuit() && SG_NUIT_MODE !== 'moitie' ? '🌙 Le Front dort jusqu\\'à 7 h'   // patch510, patch525")
rep('app.js', "  return sgNuit() ? '<p class=\"sg-note sg-nuit\"><span class=\"sg-lune\" aria-hidden=\"true\">🌙</span><span><b>Le Front dort</b> :",
              "  if(sgNuit() && SG_NUIT_MODE === 'moitie') return '<p class=\"sg-note sg-nuit\"><span class=\"sg-lune\" aria-hidden=\"true\">🌙</span><span><b>C\\'est la nuit</b> : entre 0 h et 7 h, tes vagues font <b>moitié moins de dégâts</b> (les chiffres ci-dessus en tiennent compte). L\\'énergie mise en attente avant minuit attend 7 h pour garder sa valeur, sauf si tu relances ce siège cette nuit.</span></p>';   // patch525\n  return sgNuit() ? '<p class=\"sg-note sg-nuit\"><span class=\"sg-lune\" aria-hidden=\"true\">🌙</span><span><b>Le Front dort</b> :")
rep('app.js', "      <li><b>La nuit</b> (0 h – 7 h) : le Front dort. Pas de nouveau siège ni de vague ; l'énergie en attente part à 7 h.</li>",
              "      <li><b>La nuit</b> (0 h – 7 h) : les attaques font moitié moins de dégâts. L'énergie mise en attente avant minuit attend 7 h, sauf si tu relances le siège pendant la nuit.</li>")
rep('app.js', "  if(m) L.push(`<span class=\"${m > 0 ? 'p' : 'm'}\">tes dégâts ${m > 0 ? '+' : '−'}${Math.abs(m)} %</span>`);",
              "  if(m) L.push(`<span class=\"${m > 0 ? 'p' : 'm'}\">tes dégâts ${m > 0 ? '+' : '−'}${Math.abs(m)} %${sgNuit() && SG_NUIT_MODE === 'moitie' ? ' (nuit)' : ''}</span>`);   // patch525")
rep('index.html', "<p><b>La nuit</b> (0 h – 7 h, heure de Paris) : le Front dort. On ne pose pas de siège et on n'envoie pas de vague ; l'énergie déjà en attente dans un siège part toute seule à 7 h. Renforcer ses communes reste possible.</p><!-- patch510 -->",
                  "<p><b>La nuit</b> (0 h – 7 h, heure de Paris) : on peut attaquer, mais chaque énergie fait <b>moitié moins de dégâts</b> ; prendre une commune coûte donc le double. L'énergie mise en attente dans un siège avant minuit attend 7 h pour garder sa valeur, sauf si tu relances ce siège pendant la nuit. Renforcer ses communes ne change pas.</p><!-- patch525 -->")
rep('index.html', "<b>La nuit, le Front dort</b><small>De 0 h à 7 h, heure de Paris</small></span></summary>\n          <p class=\"gd-p\">Pas de nouveau siège ni de vague, et aucune commune ne tombe. L'énergie déjà en attente dans un siège part à 7 h. Renforcer reste possible.</p>",
                  "<b>La nuit, attaquer coûte le double</b><small>De 0 h à 7 h, heure de Paris</small></span></summary>\n          <p class=\"gd-p\">On peut attaquer à toute heure, mais la nuit chaque énergie fait <b>moitié moins de dégâts</b>. L'énergie mise en attente avant minuit attend 7 h pour garder sa valeur, sauf si tu relances le siège pendant la nuit. Renforcer ne change pas.</p>")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-24': d.insert(0, {'date': '2026-11-24', 'nouveautes': []})
e = d[0]; e.setdefault('nouveautes', [])
l = "🌙 Front : la coupure de nuit est remplacée. Entre 0 h et 7 h, on peut de nouveau attaquer, mais chaque énergie fait moitié moins de dégâts (prendre une commune coûte le double). L'énergie mise en attente avant minuit attend 7 h, sauf si tu relances le siège pendant la nuit."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
