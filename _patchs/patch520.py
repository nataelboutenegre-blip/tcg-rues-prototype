# patch520 : Défendre — quand ma commune peut tomber (idée de Cairnan217, choix B de Nataël, s3-62 siege_chute).
# Sous chaque siège contre moi, et sur la fiche du siège : l'heure au plus tôt, et si l'énergie que l'attaquant a déjà
# mise en attente suffit (alors elle tombera vers cette heure-là sans autre vague).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js', "function sgLaisses(){",
"""// patch520 : quand ma commune peut tomber (s3-62)
function sgHeure(t){
  const d = new Date(t), auj = new Date(), dem = new Date(); dem.setDate(auj.getDate() + 1);
  const h = d.getHours() + ' h ' + String(d.getMinutes()).padStart(2, '0');
  if(d.toDateString() === auj.toDateString()) return h;
  if(d.toDateString() === dem.toDateString()) return 'demain ' + h;
  return d.toLocaleDateString('fr-FR', { weekday: 'short' }) + ' ' + h;
}
function sgChuteHtml(m){
  const c = m && m.chute; if(!c || !c.plus_tot) return '';
  const quand = c.maintenant ? null : sgHeure(c.plus_tot);
  const manque = Math.max(0, (Number(c.besoin) || 0) - (Number(c.attente) || 0));
  if(c.suffit) return `<p class="sg-chute alerte"><b>⚠️ L'énergie déjà envoyée suffit</b> : ${quand ? `elle tombera vers <b>${quand}</b> sans autre vague` : 'elle peut tomber d\\'un instant à l\\'autre'}. Renforce avant.</p>`;
  return `<p class="sg-chute">⏱️ ${quand ? `Au plus tôt vers <b>${quand}</b>` : 'Elle peut tomber dès maintenant'}, si l'attaquant envoie encore ≈ <b>${manque} ⚡</b>${Number(c.attente) > 0 ? ` (il en a ${c.attente} en attente)` : ''}.</p>`;
}
function sgLaisses(){""")
rep("app.js", "      ${tombe > 0 ? `<p class=\"sg-tombe\">Sans nouvelle vague, son siège",
              "      ${sgChuteHtml(m)}${tombe > 0 ? `<p class=\"sg-tombe\">Sans nouvelle vague, son siège")   # patch520
rep('app.js', "${x} ⚡</button>`).join('')}</div>${sgToutHtml(m, true)}",
              "${x} ⚡</button>`).join('')}</div>${sgChuteHtml(m)}${sgToutHtml(m, true)}")   # patch520
rep('style.css', ".sg-tout{",
""".sg-chute{ margin:6px 0 0; font-size:.8rem; line-height:1.4; color:var(--brume); }   /* patch520 */
.sg-chute b{ color:#fff; }
.sg-chute.alerte{ color:#FFB4B7; background:rgba(229,72,77,.12); border:1px solid rgba(229,72,77,.3); border-radius:10px; padding:7px 10px; }
.sg-tout{""")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-23': d.insert(0, {'date': '2026-11-23', 'nouveautes': []})
e = d[0]; e.setdefault('nouveautes', [])
l = "⏱️ Défendre : sous chaque siège contre toi, l'heure à laquelle ta commune peut tomber au plus tôt, et une alerte si l'énergie que l'attaquant a déjà envoyée suffit à la prendre sans autre vague. Idée de Cairnan217."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
