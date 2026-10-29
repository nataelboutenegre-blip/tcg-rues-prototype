# patch268 : la fiche d'une commune montre son clan (idée d'Arkhannou) ; liseré + bandeau si c'est ton clan, et plus de « Attaquer » entre membres
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch268' not in s
s = rep(s, """  if(!c){ fermerPanneau(); return; }
  panneauCommune = code;
  panneauDept = null;""", """  if(!c){ fermerPanneau(); return; }
  // patch268 : le clan du propriétaire (idée d'Arkhannou)
  const clanP = CLANS && (mienne ? window.__monId : c.joueurId) ? clansCarte.get(mienne ? window.__monId : c.joueurId) : null;
  const allie = !mienne && !!c.joueurId && clanMembres.has(c.joueurId);
  panneauCommune = code;
  panneauDept = null;""")
s = rep(s, "  const attaquable = !mienne && !protegee;\n", "  const attaquable = !mienne && !protegee && !allie;   // patch268 : pas entre membres d'un clan\n")
s = rep(s, """  if(protegee) lignes.push(['Bouclier', 'jusqu’à '""", """  if(clanP) lignes.push(['Clan', `<span class="pc-clan">${blasonHtml(clanP.tag, clanP.couleur, true)}${echapperHtml(clanP.tag)}</span>`]);   // patch268
  if(protegee) lignes.push(['Bouclier', 'jusqu’à '""")
s = rep(s, """  if(!mienne && protegee) note = 'Protégée par un bouclier : impossible de l’attaquer pour l’instant.';""",
           """  if(allie) note = 'Commune d’un membre de ton clan : vous ne pouvez pas vous attaquer.';   // patch268
  else if(!mienne && protegee) note = 'Protégée par un bouclier : impossible de l’attaquer pour l’instant.';""")
s = rep(s, """    ${alerte}
    ${gnBloc}${btEtat}""", """    ${allie && clanP ? `<p class="pc-allie-bandeau">${blasonHtml(clanP.tag, clanP.couleur, true)}<span>Commune de ton clan</span></p>` : ''}
    ${alerte}
    ${gnBloc}${btEtat}""")
s = rep(s, """      `<button class="pc-action ${cl}" data-pc="${ic}" title="${echapperHtml(titre)}">${ICONES_PC[ic]}${txt}</button>`).join('')}</div>` : ''}${btActions}`;

  el.hidden = false;""", """      `<button class="pc-action ${cl}" data-pc="${ic}" title="${echapperHtml(titre)}">${ICONES_PC[ic]}${txt}</button>`).join('')}</div>` : ''}${btActions}`;

  el.classList.toggle('pc-allie', allie && !!clanP);   // patch268 : liseré aux couleurs du clan
  if(allie && clanP) el.style.setProperty('--clan', clanP.couleur || '#4C9BE8'); else el.style.removeProperty('--clan');
  el.hidden = false;""")
f.write_text(s, encoding='utf-8')
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch268' not in s
s = s.rstrip('\n') + """
/* patch268 : le clan dans la fiche d'une commune */
.pc-clan{ display:inline-flex; align-items:center; gap:6px; }
.pc-clan .blason.petit{ margin:0; width:18px; height:22px; font-size:.5rem; }
.pc-clan .blason.petit svg{ width:18px; height:22px; }
#mapPanneau.pc-allie{ border:2px solid var(--clan); box-shadow:0 0 0 1px rgba(0,0,0,.4), 0 0 22px color-mix(in srgb, var(--clan) 45%, transparent), 0 18px 40px rgba(0,0,0,.5); }
.pc-allie-bandeau{ display:flex; align-items:center; gap:8px; margin:2px 0 8px; padding:7px 10px; border-radius:10px; font-size:.8rem; font-weight:700; color:#fff;
  background:color-mix(in srgb, var(--clan) 22%, transparent); border:1px solid color-mix(in srgb, var(--clan) 55%, transparent); }
.pc-allie-bandeau .blason.petit{ margin:0; }
"""
f.write_text(s, encoding='utf-8')
print('patch268 appliqué')
