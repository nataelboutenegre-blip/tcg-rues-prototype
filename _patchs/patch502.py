# patch502 : le pass de saison sort de l'Arcade (idée de Maroli, 22/11). Il devient un onglet à lui,
# dans le groupe « Moi » à côté du Profil (rail sur PC, menu Plus sur téléphone), avec une pastille
# du nombre de récompenses à réclamer. L'encart du pass en haut de l'Arcade disparaît.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
H, A = 'index.html', 'app.js'
rep(H, '      <div class="tab onglet-fusionne" data-tab="pass" aria-hidden="true"><div class="icon"></div>Pass de saison</div>\n',
       '      <div class="tab" data-tab="pass">\n'
       '        <div class="icon"><!-- patch502 : le pass sort de l\'Arcade -->\n'
       '          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">\n'
       '            <path d="M4 7.5A1.5 1.5 0 0 1 5.5 6h13A1.5 1.5 0 0 1 20 7.5V10a2 2 0 0 0 0 4v2.5a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 16.5V14a2 2 0 0 0 0-4z"/><path d="M14.5 6v12" stroke-dasharray="1.6 2"/><path d="m9.2 9.6.9 1.8 2 .3-1.45 1.4.35 2-1.8-.95-1.8.95.35-2L6.3 11.7l2-.3z"/>\n'
       '          </svg>\n'
       '        </div>\n'
       '        Pass de saison\n'
       '        <span class="tab-badge" id="passBadge" hidden></span>\n'
       '      </div>\n')
rep(H, '''      <div class="volets" role="tablist" aria-label="QG">
        <button type="button" class="volet" data-volet="qg" role="tab" aria-selected="false">QG</button>
        <button type="button" class="volet actif" data-volet="pass" role="tab" aria-selected="true">Pass de saison</button>
      </div>
      <div id="passCorps">''', '''      <h1>Pass de saison</h1><!-- patch502 : plus un volet de l'Arcade -->
      <div id="passCorps">''')
rep(A, "'monuments', 'pass', 'bourse', 'echange'];", "'monuments', 'bourse', 'echange'];   // patch502 : le pass n'est plus fusionné")
rep(A, " pass: 'qg', bourse:", " bourse:")
rep(A, "const ONGLETS_COMMUNS = CLANS ? ['profil', 'communaute', 'clan'] : ['profil', 'communaute'];",
       "const ONGLETS_COMMUNS = CLANS ? ['profil', 'pass', 'communaute', 'clan'] : ['profil', 'pass', 'communaute'];   // patch502")
rep(A, "          ['Joueurs', ['communaute', 'clan']], ['Moi', ['profil']]],\n", "          ['Joueurs', ['communaute', 'clan']], ['Moi', ['profil', 'pass']]],   // patch502\n", 2)
rep(A, """  const e = passEtat;
  if(!e || !e.recompenses){ el.hidden = true; return; }
  el.hidden = false;
  const prets = e.recompenses.filter(r => psEtatRecompense(r, e) === 'pret').length;""",
"""  const e = passEtat;
  // patch502 : plus d'encart dans l'Arcade ; la pastille de l'onglet compte ce qu'il y a à réclamer
  const pb = document.getElementById('passBadge');
  const nPrets = e && e.recompenses ? e.recompenses.filter(r => psEtatRecompense(r, e) === 'pret').length : 0;
  if(pb){ pb.hidden = !nPrets; pb.textContent = nPrets ? String(nPrets) : ''; try{ majBadgePlus(); }catch(err){} }
  el.hidden = true; return;
  const prets = nPrets;""")
rep(A, "  chargerAnnonce();   // patch137\n", "  chargerAnnonce();   // patch137\n  chargerPass();   // patch502 : la pastille du pass dès l'arrivée\n")
rep(A, "  renderObjectifs();\n  invCharger();   // patch350", "  renderObjectifs();\n  if(passEtat) chargerPass();   // patch502 : une quête finie fait avancer le pass\n  invCharger();   // patch350")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = next(x for x in d if x.get('date') == '2026-11-22')
l = "🎟️ Le pass de saison sort de l'Arcade : il a maintenant son propre onglet, à côté du Profil (dans « Plus » sur téléphone), avec une pastille quand une récompense t'attend (idée de Maroli)."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
