# patch511 : « Tout repousser (N ⚡) » dans Défendre et sur la fiche de ma commune assiégée (à faire du 23/11, point 2).
# N = ceil(dégâts / (10 × 1,2 × 0,8)) : le pire tirage (aléa 0,8) ramène quand même la jauge à 0 ; 60 au plus (siege_renforcer).
# Rien à changer côté serveur : le bouton envoie siege_renforcer avec N.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js', "function sgLaisses(){",
"""// patch511 : « Tout repousser » — assez d'énergie pour ramener la jauge à 0 même au pire tirage (10 × 1,2 × 0,8 par ⚡)
function sgToutN(deg){ return Math.min(60, Math.max(1, Math.ceil((Number(deg) || 0) / 9.6))); }
function sgToutHtml(m, petit){
  const deg = Number(m.degats) || 0; if(deg <= 0) return '';
  const n = sgToutN(deg), e = sgEnergie(), manque = e !== null && e < n;
  const txt = n >= 60 && deg / 9.6 > 60 ? `Repousser au maximum · 60 ⚡` : `Tout repousser · ${n} ⚡`;
  return `<button type="button" class="sg-tout${petit ? ' petit' : ''}" data-sg-renf="${n}" data-code="${echapperTexte(m.commune)}" data-att="${echapperTexte(m.attaquant)}"${manque ? ' disabled' : ''}>🛡️ ${txt}<small>${manque ? `tu as ${e} ⚡` : 'la jauge revient à 0'}</small></button>`;
}
function sgLaisses(){""")
rep('app.js', """        <span class="sg-renf-l">Renforcer</span>${[2, 5, 10].map(x => `<button type="button" class="sg-renf" data-sg-renf="${x}" data-code="${echapperTexte(m.commune)}" data-att="${echapperTexte(m.attaquant)}">${x} ⚡</button>`).join('')}
      </div>""",
"""        <span class="sg-renf-l">Renforcer</span>${[2, 5, 10].map(x => `<button type="button" class="sg-renf" data-sg-renf="${x}" data-code="${echapperTexte(m.commune)}" data-att="${echapperTexte(m.attaquant)}">${x} ⚡</button>`).join('')}
      </div>${sgToutHtml(m)}""")   # patch511
rep('app.js', """      <div class="sg-fiche-a"><span>Renforcer</span>${[2, 5, 10].map(x => `<button type="button" class="sg-renf" data-sg-renf="${x}" data-code="${echapperTexte(m.commune)}" data-att="${echapperTexte(m.attaquant)}">${x} ⚡</button>`).join('')}</div>""",
"""      <div class="sg-fiche-a"><span>Renforcer</span>${[2, 5, 10].map(x => `<button type="button" class="sg-renf" data-sg-renf="${x}" data-code="${echapperTexte(m.commune)}" data-att="${echapperTexte(m.attaquant)}">${x} ⚡</button>`).join('')}</div>${sgToutHtml(m, true)}""")   # patch511
rep('app.js', "    notifier({ type: 'succes', titre: 'Renfort envoyé', texte: recul > 0 ? `La jauge recule de ${sgNb(recul)} points. Le siège est long maintenant.` : 'Le siège est long maintenant.' });",
              "    notifier({ type: 'succes', titre: 'Renfort envoyé', texte: data && Number(data.degats) <= 0 ? 'Le siège est repoussé : sa jauge est à 0. Il est long maintenant.' : recul > 0 ? `La jauge recule de ${sgNb(recul)} points. Le siège est long maintenant.` : 'Le siège est long maintenant.' });   // patch511")
rep('style.css', ".sg-renf-l{",
""".sg-tout{ display:flex; flex-direction:column; align-items:center; gap:1px; width:100%; margin-top:8px; font:inherit; font-size:.9rem; font-weight:800; padding:10px 12px; border-radius:12px; border:1px solid rgba(255,255,255,.18); background:linear-gradient(180deg, #3a6df0, #2a52c4); color:#fff; cursor:pointer; }   /* patch511 */
.sg-tout small{ font-size:.72rem; font-weight:500; opacity:.85; }
.sg-tout.petit{ padding:8px 10px; font-size:.82rem; }
.sg-tout:disabled{ opacity:.5; cursor:default; }
.sg-renf-l{""")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-23': d.insert(0, {'date': '2026-11-23', 'nouveautes': []})
e = d[0]; e.setdefault('nouveautes', [])
l = "🛡️ Défendre : un bouton « Tout repousser » sous chaque siège contre toi. Il met d'un coup l'énergie qu'il faut pour ramener la jauge de l'attaquant à 0 (60 ⚡ au plus)."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
