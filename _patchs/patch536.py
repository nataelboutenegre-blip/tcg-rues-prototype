# patch536 (Arkhannou) : 7 meubles de blason en plus ; 3 rares gagnés par l'or de l'objectif de clan (s3-74).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
LIGNES = open('/tmp/vbl/lignes.txt', encoding='utf-8').read() if os.path.exists('/tmp/vbl/lignes.txt') else open(os.path.join(os.path.dirname(__file__), 'patch536-meubles.txt'), encoding='utf-8').read()
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "\n};\nconst BL_DEFAUT = {", "\n  // patch536 : pour tous, puis 3 rares (rare = n-ième semaine d'or de l'objectif de clan)\n" + LIGNES + "\n};\nlet blRares = 0;   // patch536 : meubles rares débloqués par mon clan (clan_meubles_rares)\nconst BL_DEFAUT = {")
rep('app.js', """    <h2>Meuble</h2><div class="bl-choix bl-meubles">${Object.entries(BL_MEUBLES).map(([k, m]) => bt('meuble', k,""",
              """    <h2>Meuble</h2><div class="bl-choix bl-meubles">${Object.entries(BL_MEUBLES).map(([k, m]) => blVerrou(k, m, B.meuble, bt('meuble', k,""")
rep('app.js', """<span>${m.nom}</span>`)).join('')}</div>""", """<span>${m.nom}</span>`))).join('')}</div>""")
rep('app.js', "function editionClanHtml(){", """// patch536 : un meuble rare pas encore gagné reste visible mais grisé (sauf s'il est déjà sur le blason)
function blVerrou(k, m, actuel, html){
  if(!(m.rare && m.rare > blRares) || actuel === k) return html;
  return html.replace('<button', `<button disabled class="bl-lock" title="${m.nom} : ${m.rare === 1 ? '1re' : m.rare + 'e'} semaine d'or de l'objectif de clan"`);
}
function editionClanHtml(){""")
rep('app.js', "      B.meuble = tire(Object.keys(BL_MEUBLES).slice(1));",
              "      B.meuble = tire(Object.keys(BL_MEUBLES).slice(1).filter(k => !(BL_MEUBLES[k].rare > blRares)));   // patch536")
rep('app.js', "function ouvrirEditionClan(c){\n",
"""function ouvrirEditionClan(c){
  sb.rpc('clan_meubles_rares').then(({ data, error }) => {   // patch536
    if(error) return;
    const n = Number(data) || 0;
    if(n !== blRares){ blRares = n; if(clanEdition){ const y = window.scrollY; renderClan(); window.scrollTo(0, y); } }
  });
""")
rep('app.js', """    <h2>Bordure</h2><div class="bl-emaux">${pastilles('bordure', true)}</div>""",
"""    ${blRares < 3 ? `<p class="clan-note">🔒 Meubles rares : la Rose des vents, l'Aigle bicéphale et la Couronne royale se gagnent avec l'or de l'objectif de clan de la semaine (un de plus à chaque semaine d'or), et restent au clan.</p>` : ''}
    <h2>Bordure</h2><div class="bl-emaux">${pastilles('bordure', true)}</div>""")
rep('style.css', ".ce-filtres{ display:flex;", ".bl-meubles .bl-lock{ opacity:.45; border-style:dashed !important; cursor:not-allowed; }   /* patch536 */\n.ce-filtres{ display:flex;")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = d[0]; assert e['date'] == '2026-11-25'
l = "🛡️ Blasons de clan : 4 nouveaux meubles pour tous (Château, Trèfle, Cloche, Épées croisées) et 3 meubles rares à gagner avec l'or de l'objectif de clan de la semaine (Rose des vents, Aigle bicéphale, Couronne royale). Merci Arkhannou."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
