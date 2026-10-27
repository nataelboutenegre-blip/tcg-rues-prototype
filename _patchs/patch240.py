# patch240 : la série est gardée après une défaite, 2 défenses par attaque (s2-46)
import pathlib
def ouvrir(n): return pathlib.Path(n), pathlib.Path(n).read_text(encoding='utf-8')
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:80], s.count(a)); return s.replace(a, b)
f, s = ouvrir('app.js')
# l'assaut : pastilles de départ = la série gardée ; la garnison se lit dans la réponse
s = rep(s, "const serieAvant = r.conquise ? 2 : (r.gagne ? Math.max(0, Number(r.victoires_consecutives) - 1) : null);",
           "const serieAvant = r.conquise ? 2 : (r.gagne ? Math.max(0, Number(r.victoires_consecutives) - 1) : Number(r.victoires_consecutives) || 0);   // patch240")
s = rep(s, "const parGarnison = SAISON2 && !r.gagne && !r.conquise && Number(r.victoires_consecutives) > 0;",
           "const parGarnison = SAISON2 && !r.gagne && !r.conquise && (r.par_garnison !== undefined ? !!r.par_garnison : Number(r.victoires_consecutives) > 0);   // patch240 : s2-46 le dit")
s = rep(s, "bl.forEach((b, i) => b.className = parGarnison ? (i < Number(r.victoires_consecutives) ? 'gagne' : '') : 'perdu');",
           "bl.forEach((b, i) => b.className = i < Number(r.victoires_consecutives) ? 'gagne' : '');   // patch240 : la série reste")
s = rep(s, "        : `${nomCible} tient bon : ta série repart à zéro.`;",
           """        : Number(r.victoires_consecutives) > 0
          ? `${nomCible} tient bon, mais tu gardes ta série <span class="as-serie">${[0, 1, 2].map(i => `<i class="${i < r.victoires_consecutives ? 'plein' : ''}"></i>`).join('')}</span><br>`
            + (3 - Number(r.victoires_consecutives) <= 1 ? 'Encore une victoire pour la prendre.' : `Encore ${3 - Number(r.victoires_consecutives)} victoires pour la prendre.`)
            + ` <span class="as-petit">Prochain assaut dans ${Math.round((DELAI_ATTAQUE_MS[tierId] || 0) / 60000) >= 60 ? Math.round(DELAI_ATTAQUE_MS[tierId] / 3600000) + ' h' : Math.round((DELAI_ATTAQUE_MS[tierId] || 0) / 60000) + ' min'}.</span>`
          : `${nomCible} tient bon. Retente ta chance : une défaite ne te fait rien perdre.`;""")
# sous le bouton d'attaque
s = rep(s, """  const txt = reste === 3 ? `Il faut 3 victoires d’affilée pour la prendre : <b>${proba}\\u00A0%</b> de chances d’y arriver sans perdre un round.`
            : reste === 2 ? `Encore 2 victoires d’affilée pour la prendre : <b>${proba}\\u00A0%</b> de chances.`
            :               `Une dernière victoire pour la prendre : <b>${proba}\\u00A0%</b> de chances.`;""",
"""  // patch240 : la série est gardée, chaque round gagné rapproche de la conquête
  void proba;
  const txt = reste === 3 ? 'Il faut 3 victoires pour la prendre, pas forcément d’affilée. Une défaite ne te fait rien perdre.'
            : reste === 2 ? 'Encore 2 victoires pour la prendre.'
            :               'Une dernière victoire pour la prendre.';""")
s = rep(s, "'en Front, une commune tombe après 3 rounds gagnés d’affilée\u00A0: défends-la ou pose un bouclier.'",
           "'en Front, une commune tombe après 3 rounds gagnés\u00A0: défends-la ou mets-la en garnison.'")
s = rep(s, "title=\"${v} victoire${v > 1 ? 's' : ''} d'affilée sur 3\"", "title=\"${v} victoire${v > 1 ? 's' : ''} sur 3\"")
s = rep(s, "'<span class=\"df-note\">défense déjà utilisée</span>'", "'<span class=\"df-note\">deux défenses utilisées</span>'")
s = rep(s, "note = 'Le défenseur a déjà utilisé sa défense';", "note = 'Le défenseur a utilisé ses deux défenses';")
f.write_text(s, encoding='utf-8')
f, s = ouvrir('index.html')
s = rep(s, "trois victoires d'affilée et elle est à toi.", "trois victoires et elle est à toi.")
s = rep(s, "se prennent par la force : trois victoires d'affilée.", "se prennent par la force : trois victoires.")
s = rep(s, "<div class=\"sub\">3 victoires d'affilée pour conquérir une commune, une défaite remet ta série à zéro.",
           "<div class=\"sub\">3 victoires pour conquérir une commune, pas forcément d'affilée : une défaite ne te fait rien perdre.")
s = rep(s, "<b>3</b><span>victoires d'affilée pour conquérir</span>", "<b>3</b><span>victoires pour conquérir</span>")
s = rep(s, "Gagne <b>3 rounds d'affilée</b> pour prendre la commune ; une défaite remet ta série à zéro.",
           "Gagne <b>3 rounds</b> pour prendre la commune, pas forcément d'affilée : <b>une défaite ne te fait rien perdre</b>, ta série reste où elle était.")
s = rep(s, "Aligne 3 victoires d'affilée contre une commune rare ou légendaire pour la prendre.",
           "Gagne 3 victoires contre une commune pour la prendre.")
s = rep(s, "<li><b>3 victoires d'affilée</b> et la commune est à toi. <b>Une défaite remet ta série à zéro.</b></li>",
           "<li><b>3 victoires</b> et la commune est à toi, pas forcément d'affilée. <b>Une défaite ne te fait rien perdre.</b></li>")
s = rep(s, "Tu as droit à <b>une seule défense par attaque</b>. Si la série de l'attaquant retombe à zéro, tu récupères ta défense pour sa prochaine attaque.",
           "Tu as droit à <b>deux défenses par attaque</b>. Si la série de l'attaquant retombe à zéro, tu les récupères pour sa prochaine attaque.")
s = rep(s, "tu peux tenter une défense pour <b>1 énergie</b>, une fois par attaque.", "tu peux tenter une défense pour <b>1 énergie</b>, deux fois par attaque.")
f.write_text(s, encoding='utf-8'); print('patch240 ok')
