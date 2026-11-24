# patch532 (après D.C.A) : l'assaut final annoncé (s3-70) se voit côté défenseur et côté attaquant, et dans les règles.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js', "function sgChuteHtml(m){\n",
"""function sgAssautMin(s){   // patch532 : minutes avant l'assaut final, ou 0
  const t = s && s.assaut_le ? new Date(s.assaut_le).getTime() - Date.now() : 0;
  return t > 0 ? Math.max(1, Math.ceil(t / 60000)) : 0;
}
function sgChuteHtml(m){
  const am = sgAssautMin(m);   // patch532
  if(am){
    const res = Number(m.resistance) || 0, deg = Number(m.degats) || 0;
    const n = Math.max(1, Math.ceil((deg - res * 2 / 3 + 1) / sgPireRecul()));
    return `<p class="sg-chute alerte"><b>🚨 Assaut final</b> : elle tombe à <b>${sgHeure(m.assaut_le)}</b> (dans ${am} min) si tu ne repousses pas la jauge sous les deux tiers, ≈ <b>${n} ⚡</b>${Number(m.attente) > 0 ? `, plus de quoi absorber ses ${m.attente} ⚡ en attente` : ''}.</p>`;
  }
""")
rep('app.js', "function sgSuffit(v){", "function sgPireRecul(){ return typeof SG_PIRE_RENFORT !== 'undefined' ? SG_PIRE_RENFORT : 11.52; }   // patch532\nfunction sgSuffit(v){")
# Mon front : la ligne de la commune
rep('app.js', "${echapperTexte(m.attaquant_pseudo || 'un joueur')} · jauge à ${p} % · ${m.long ? 'siège long' : 'siège éclair'}</small>",
              "${echapperTexte(m.attaquant_pseudo || 'un joueur')} · jauge à ${p} % · ${sgAssautMin(m) ? `🚨 tombe dans ${sgAssautMin(m)} min` : m.long ? 'siège long' : 'siège éclair'}</small>")
# Mes sièges (attaquant)
rep('app.js', "${echapperTexte(s.proprio_pseudo || '')}${s.long ? ' · long' : ' · éclair'}${Number(s.attente) > 0 ? ` · ${s.attente} ⚡ en attente` : ''}</small>",
              "${echapperTexte(s.proprio_pseudo || '')}${s.long ? ' · long' : ' · éclair'}${sgAssautMin(s) ? ` · 🚨 assaut final dans ${sgAssautMin(s)} min` : Number(s.attente) > 0 ? ` · ${s.attente} ⚡ en attente` : ''}</small>")
# les règles
rep('index.html', "Tu as <b>8 places</b> de sièges longs.</p>",
    "Tu as <b>8 places</b> de sièges longs.</p>\n          <p class=\"gd-p\"><b>Assaut final</b> : sur un siège long que le propriétaire a déjà défendu, une jauge pleine ne prend pas la commune tout de suite. Le défenseur est prévenu et la commune tombe <b>30 min</b> plus tard, sauf s'il repousse la jauge sous les deux tiers.</p>")
rep('index.html', "part toute seule, au fil du temps.</p>",
    "part toute seule, au fil du temps. <b>Assaut final</b> : si le propriétaire a déjà défendu, une jauge pleine ne prend pas la commune tout de suite : il est prévenu, et elle tombe <b>30 min</b> plus tard s'il ne repousse pas ta jauge sous les deux tiers.</p>")

p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = d[0]; assert e['date'] == '2026-11-24'
for l in ["🚨 Front : assaut final annoncé. Sur un siège long que tu as déjà défendu, une jauge pleine ne prend plus ta commune d'un coup : tu es prévenu et elle tombe 30 min plus tard, sauf si tu repousses la jauge sous les deux tiers.",
          "🔔 Front : une vague qui remplit la moitié de la jauge d'un siège en cours te prévient, et l'alerte « en danger » revient chaque fois que la jauge repasse les deux tiers."]:
    if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
