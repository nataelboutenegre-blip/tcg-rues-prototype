# patch510 : Front ralenti (s3-58, décisions du 23/11, nuit : choix B) — les textes côté client.
#  - 🌙 sur la fiche d'un siège entre 0 h et 7 h (heure de Paris) : le Front dort, bouton fermé, l'attente part à 7 h.
#  - « Comment c'est calculé ? » et les règles : proximité graduée (0 : −20 %, 1-2 : −10 %, 3-5 : normal, 6+ : +10 %),
#    rempart (+5 % de résistance par commune du propriétaire à moins de 10 km au-delà de 3, +50 % au plus), la nuit.
#  - une ligne dans les nouveautés.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

# 1. la nuit sur la fiche du siège
rep('app.js', "// « Comment c'est calculé » (les chiffres viennent de config_jeu 'siege', s3-7)\nfunction sgCalcHtml(a){",
"""// patch510 (s3-58) : la nuit (0 h – 7 h, heure de Paris), aucune commune ne tombe
function sgNuit(){
  try { const h = Number(new Intl.DateTimeFormat('fr-FR', { hour: 'numeric', hourCycle: 'h23', timeZone: 'Europe/Paris' }).format(new Date())); return h >= 0 && h < 7; }
  catch(e){ return false; }
}
function sgNuitHtml(){
  return sgNuit() ? '<p class="sg-note sg-nuit"><span class="sg-lune" aria-hidden="true">🌙</span><span><b>Le Front dort</b> : entre 0 h et 7 h, pas de nouveau siège ni de vague, et aucune commune ne tombe. L\\'énergie déjà en attente part toute seule à 7 h. Renforcer reste possible.</span></p>' : '';
}
// « Comment c'est calculé » (les chiffres viennent de config_jeu 'siege', s3-7)
function sgCalcHtml(a){""")
rep('app.js', "  b.innerHTML = tete + chiffres + jauge + retour + lignes + avert + autres + choix",
              "  b.innerHTML = tete + chiffres + jauge + retour + sgNuitHtml() + lignes + avert + autres + choix")   # patch510
rep('app.js', "<li><b>Tes dégâts</b> dépendent de tes communes à moins de 20 km (aucune : −20 %, une : normal, deux ou plus : +10 %).",
              "<li><b>Tes dégâts</b> dépendent de tes communes à moins de 20 km (aucune : −20 %, une ou deux : −10 %, trois à cinq : normal, six ou plus : +10 %).")
rep('app.js', "<li><b>Résistance</b> : commune et peu commune 55, rare 65, épique 125, légendaire 250. Forteresse sur place × 1,5. Une rébellion que tu finances la baisse.</li>",
              "<li><b>Résistance</b> : commune et peu commune 55, rare 65, épique 125, légendaire 250. Forteresse sur place × 1,5. <b>Rempart</b> : +5 % par commune du propriétaire à moins de 10 km au-delà de 3 (+50 % au plus). Une rébellion que tu finances la baisse.</li>\n      <li><b>La nuit</b> (0 h – 7 h) : le Front dort. Pas de nouveau siège ni de vague ; l'énergie en attente part à 7 h.</li>")
rep('style.css', ".sg-note svg{",
    ".sg-nuit{ background:rgba(120,140,255,.08); border:1px solid rgba(120,140,255,.25); border-radius:10px; padding:8px 10px; color:var(--texte, #e8e6f0); }   /* patch510 */\n.sg-nuit .sg-lune{ font-size:1rem; line-height:1.2; }\n.sg-note svg{")

# 1b. le minuteur et la répartition tiennent compte de la nuit
rep('app.js', "  return { fin: Date.now() + min * 60000, suffit, manque: besoin - att };\n}",
"""  const nuit = suffit && sgNuit();   // patch510 : la nuit, elle ne tombe pas avant 7 h
  return { fin: nuit ? Math.max(Date.now() + min * 60000, Date.now() + sgFinNuitMs()) : Date.now() + min * 60000, suffit, manque: besoin - att, nuit };
}
function sgFinNuitMs(){   // patch510 : temps avant 7 h, heure de Paris
  try {
    const p = new Intl.DateTimeFormat('fr-FR', { hour: 'numeric', minute: 'numeric', second: 'numeric', hourCycle: 'h23', timeZone: 'Europe/Paris' }).formatToParts(new Date());
    const v = k => Number((p.find(x => x.type === k) || {}).value) || 0;
    return Math.max(0, ((7 - v('hour')) * 3600 - v('minute') * 60 - v('second')) * 1000);
  } catch(e){ return 0; }
}""")
rep('app.js', "  return i.suffit ? `⏱️ Elle peut tomber ${t}, si personne ne renforce.`",
              "  if(i.suffit && i.nuit) return `🌙 Elle peut tomber à 7 h (${ms <= 0 ? 'au prochain passage' : 'dans <b class=\"sg-chrono\">' + sgChrono(ms) + '</b>'}), si personne ne renforce.`;   // patch510\n  return i.suffit ? `⏱️ Elle peut tomber ${t}, si personne ne renforce.`")
rep('app.js', 'return `<p class="sg-minuteur" data-sg-fin="${Math.round(i.fin)}" data-sg-suffit="${i.suffit ? 1 : 0}" data-sg-manque="${i.manque}">${sgMinuteurTexte(i)}</p>`;',
              'return `<p class="sg-minuteur" data-sg-fin="${Math.round(i.fin)}" data-sg-suffit="${i.suffit ? 1 : 0}" data-sg-nuit="${i.nuit ? 1 : 0}" data-sg-manque="${i.manque}">${sgMinuteurTexte(i)}</p>`;')
rep('app.js', "  const i = { fin: Number(el.dataset.sgFin), suffit: el.dataset.sgSuffit === '1', manque: Number(el.dataset.sgManque) || 0 };",
              "  const i = { fin: Number(el.dataset.sgFin), suffit: el.dataset.sgSuffit === '1', nuit: el.dataset.sgNuit === '1', manque: Number(el.dataset.sgManque) || 0 };")
rep('app.js', "(r.finit ? `elle peut tomber dans ≈ <b>${sgDuree(r.minutes)}</b> si personne ne renforce`",
              "(r.finit ? (sgNuit() ? 'elle pourra tomber à 7 h au plus tôt' : `elle peut tomber dans ≈ <b>${sgDuree(r.minutes)}</b> si personne ne renforce`)")

rep('app.js', "  const bloque = a.bouclier_jusqua ? `Protégée par un bouclier",
              "  const bloque = sgNuit() ? '🌙 Le Front dort jusqu\\'à 7 h'   // patch510\n    : a.bouclier_jusqua ? `Protégée par un bouclier")

# 2. les règles
rep('index.html', "<p><b>Tes dégâts</b> : <b>× 0,8</b> sans commune à toi à moins de 20 km, <b>× 1,1</b> avec deux ou plus ;",
                  "<p><b>Tes dégâts</b> selon tes communes à moins de 20 km : aucune <b>× 0,8</b>, une ou deux <b>× 0,9</b>, trois à cinq <b>× 1</b>, six ou plus <b>× 1,1</b> ;<!-- patch510 -->")
rep('index.html', "<p><b>La résistance</b> : <b>× 1,5</b> sur une Forteresse ; une rébellion que tu finances la baisse jusqu'à <b>−15 %</b> face à toi seul.</p>",
                  "<p><b>La résistance</b> : <b>× 1,5</b> sur une Forteresse ; <b>rempart</b> : +5 % par commune du propriétaire à moins de 10 km au-delà de 3, jusqu'à <b>+50 %</b> (une commune au cœur d'un territoire est plus dure à prendre qu'une commune isolée) ; une rébellion que tu finances la baisse jusqu'à <b>−15 %</b> face à toi seul.</p>\n            <p><b>La nuit</b> (0 h – 7 h, heure de Paris) : le Front dort. On ne pose pas de siège et on n'envoie pas de vague ; l'énergie déjà en attente dans un siège part toute seule à 7 h. Renforcer ses communes reste possible.</p><!-- patch510 -->")

# 3. nouveautés
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-23': d.insert(0, {'date': '2026-11-23', 'nouveautes': []})
e = d[0]; e.setdefault('nouveautes', [])
for l in ["🌙 Front : le Front dort la nuit. Entre 0 h et 7 h (heure de Paris), pas de nouveau siège ni de vague, aucune commune ne tombe ; l'énergie déjà en attente part toute seule à 7 h. Renforcer reste possible.",
          "🏰 Front : une commune entourée par son propriétaire résiste mieux (rempart : +5 % par commune à lui à moins de 10 km au-delà de 3, jusqu'à +50 %). Et le bonus de proximité est plus progressif : une ou deux communes à toi autour de la cible ×0,9, trois à cinq ×1, six ou plus ×1,1."]:
    if l not in e['nouveautes']: e['nouveautes'].append(l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
