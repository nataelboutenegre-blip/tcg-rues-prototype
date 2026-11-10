# patch406 (10/11/2026) : la suite du siège (saison 3), toujours éteint tant que le serveur ne l'allume pas
#  - la fiche de la carte : « Assiéger » / « Continuer le siège » ; sur ma commune, qui l'assiège et Renforcer sur place ;
#    sur celle d'un autre, mon siège et ceux des autres (sieges_commune) ;
#  - la vague animée dans la feuille de siège (la jauge part de l'ancienne valeur, tremble, brille) ;
#  - « Comment c'est calculé ? » dans la feuille de siège.
# Demande patch405 appliqué.
import sys, os
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, C = 'app.js', 'style.css'
ICI = os.path.dirname(os.path.abspath(__file__))
if 'patch405 : le siège (saison 3, s3-7)' not in open(A, encoding='utf-8').read(): sys.exit('patch405 d\'abord')

# la fiche de la carte
rep(A, """  const lignes = [];
  if(SAISON2 && auroreFront(code)) lignes.push(['Carte', '<b class="pc-aurore">✦ Aurore</b>']);   // patch228""",
"""  if(SIEGE) alerte = mienne ? sgFicheMienne(code) : '<div class="sg-fiche" id="sgFicheAutres" hidden></div>';   // patch406
  const lignes = [];
  if(SAISON2 && auroreFront(code)) lignes.push(['Carte', '<b class="pc-aurore">✦ Aurore</b>']);   // patch228""")
rep(A, """  if(attaquable && !immunisee) actions.push(['attaque', 'attaque', 'Attaquer', 'Attaquer ' + c.nom]);""",
"""  if(SIEGE){   // patch406 : on assiège
    const monSg = sgMonSiege(code);
    if(attaquable && (!immunisee || monSg)) actions.push(['attaque', 'attaque', monSg ? 'Continuer le siège' : 'Assiéger', (monSg ? 'Continuer le siège de ' : 'Assiéger ') + c.nom]);
  } else if(attaquable && !immunisee) actions.push(['attaque', 'attaque', 'Attaquer', 'Attaquer ' + c.nom]);""")
rep(A, """  else if(immunisee) note = 'Prise il y a moins de 3 heures : encore immunisée.';""",
"""  else if(immunisee) note = SIEGE ? (sgMonSiege(code) ? '' : 'Prise il y a moins de 3 heures : pas de nouveau siège pour l’instant.') : 'Prise il y a moins de 3 heures : encore immunisée.';   // patch406""")
rep(A, """  if(allie && clanP) el.style.setProperty('--clan', clanP.couleur || '#4C9BE8'); else el.style.removeProperty('--clan');
  el.hidden = false;
  const wrap = document.getElementById('mapWrap');
  if(wrap) wrap.classList.add('panneau-ouvert');
  el.scrollTop = 0;
  placerPanneau(el, xCss, yCss);
}""",
"""  if(allie && clanP) el.style.setProperty('--clan', clanP.couleur || '#4C9BE8'); else el.style.removeProperty('--clan');
  el.hidden = false;
  const wrap = document.getElementById('mapWrap');
  if(wrap) wrap.classList.add('panneau-ouvert');
  el.scrollTop = 0;
  placerPanneau(el, xCss, yCss);
  if(SIEGE && !mienne) sgFicheAutres(code);   // patch406
}""")

# la feuille de siège : animation et « Comment c'est calculé »
rep(A, """  b.innerHTML = tete + chiffres + jauge + retour + lignes + avert + autres + choix + bouton + places + (SG.err ? `<p class="sg-err">${echapperTexte(SG.err)}</p>` : '') + sec;
}""",
"""  b.innerHTML = tete + chiffres + jauge + retour + lignes + avert + autres + choix + bouton + places + (SG.err ? `<p class="sg-err">${echapperTexte(SG.err)}</p>` : '') + sgCalcHtml(a) + sec;
  sgAnimerVague(b);   // patch406
}""")
rep(A, """  if(act === 'fermer'){ sgFermer(); return; }
  if(act === 'abandon'){""",
"""  if(act === 'fermer'){ sgFermer(); return; }
  if(act === 'calc'){ ev.preventDefault(); SG.calc = !SG.calc; const d = t.closest('details'); if(d) d.open = SG.calc; return; }   // patch406
  if(act === 'abandon'){""")
rep(A, """  SG.ap.siege = s;
  await sgCharger(false);""",
"""  SG.ap.siege = s;
  SG.anim = { de: avantRes > 0 ? 100 * avant / avantRes : 0, bcl: gagne <= 0 && Number(s.attente || 0) <= 0 };   // patch406
  await sgCharger(false);""")
rep(A, """  const code = SG.code, avant = SG.ap.siege ? Number(SG.ap.siege.degats) || 0 : 0;""",
"""  const code = SG.code, avant = SG.ap.siege ? Number(SG.ap.siege.degats) || 0 : 0;
  const avantRes = SG.ap.siege ? Number(SG.ap.siege.resistance) || 0 : Number(SG.ap.resistance) || 0;   // patch406""")
rep(A, """  SG = { code, ap: null, n: 5, envoi: false, dernier: null, err: '' };""",
"""  SG = { code, ap: null, n: 5, envoi: false, dernier: null, err: '', anim: null, calc: SG.calc || false };   // patch406 : anim, calc""")

# la fiche suit les renforts
rep(A, """  sgMenaces = Array.isArray(data) ? data : [];
  renderMenacesSiege();""",
"""  sgMenaces = Array.isArray(data) ? data : [];
  renderMenacesSiege();
  sgRafraichirFiche();   // patch406""")

t = open(A, encoding='utf-8').read()
if 'patch406 : le siège sur la fiche de la carte' in t: sys.exit('déjà appliqué')
open(A, 'a', encoding='utf-8').write(open(os.path.join(ICI, 'patch406-siege.js'), encoding='utf-8').read())
open(C, 'a', encoding='utf-8').write(open(os.path.join(ICI, 'patch406-siege.css'), encoding='utf-8').read())
print('patch406 OK')
