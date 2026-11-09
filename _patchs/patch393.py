# patch393 (10/11/2026) : l'animation d'assaut montre la même chance que la fiche quand la commune
# est en garnison (ASMFCB, 9/11 : « 43 % sur la fiche, 85 % pendant la simulation »).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
rep(A, "function mettreEnSceneAssaut(cible, r){",
       "function mettreEnSceneAssaut(cible, r, enGarnison){   // patch393 : enGarnison = la fiche divisait la chance par deux")
rep(A, """  const chances = Math.max(1, Math.min(99, Number(r.chances) || 50));
""", """  const chances = Math.max(1, Math.min(99, Number(r.chances) || 50));
  const garn = SAISON2 && (enGarnison || !!r.par_garnison);   // patch393
""")
rep(A, """        <div class="as-jleg"><span>Tes chances : <b>${chances} %</b></span>${r.cout ? `<span>Coût : <b class="blanc">${coutTexte(r.cout)}</b></span>` : ''}</div></div>""",
"""        <div class="as-jleg"><span>Tes chances : <b>${garn ? Math.round(chances / 2) : chances} %</b></span>${r.cout ? `<span>Coût : <b class="blanc">${coutTexte(r.cout)}</b></span>` : ''}</div>${garn ? `<p class="as-jgarn">${chances} % aux dés, la garnison en annule une sur deux</p>` : ''}</div>""")
rep(A, "    mettreEnSceneAssaut(cibleVue, r);", "    mettreEnSceneAssaut(cibleVue, r, attaqueEnGarnison);")
rep(A, """        mettreEnSceneAssaut(cibleVueCombat, result);""",
"""        const vuGrille = chancesCibles.get(code);   // patch393 : la grille affichait la moitié des dés = garnison
        mettreEnSceneAssaut(cibleVueCombat, result, !!(vuGrille && Number(vuGrille.chances) > 0 && Number(vuGrille.chances) < Number(result.chances) && Math.abs(Number(vuGrille.chances) * 2 - Number(result.chances)) <= 2));""")
# l'aiguille : une victoire annulée par la garnison a été gagnée aux dés, elle s'arrête dans le vert
rep(A, "  const arret = res === 'ko' ? chances + (100 - chances) * (0.25 + Math.random() * 0.6)",
       "  const arret = res === 'ko' && !parGarnison ? chances + (100 - chances) * (0.25 + Math.random() * 0.6)   // patch393")
rep('style.css', ".as-jleg b{ color:#2BD48B; } .as-jleg b.blanc{ color:#fff; }",
    ".as-jleg b{ color:#2BD48B; } .as-jleg b.blanc{ color:#fff; }\n.as-jgarn{ font-size:.7rem; color: var(--brume); margin:4px 0 0; }   /* patch393 */")
print('patch393 ok')
