# patch237 : énergie du Front 45 au maximum, +1 toutes les 8 minutes (s2-44)
import pathlib
def ouvrir(n): return pathlib.Path(n), pathlib.Path(n).read_text(encoding='utf-8')
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:70], s.count(a)); return s.replace(a, b)
f, s = ouvrir('app.js')
s = rep(s, "energieEtat = { energie: Number(data[0].energie), prochaine_dans: data[0].prochaine_dans, lu: Date.now() };",
           "energieEtat = { energie: Number(data[0].energie), maximum: Number(data[0].maximum) || 45, prochaine_dans: data[0].prochaine_dans, lu: Date.now() };")
s = rep(s, "<b id=\"mbEnergie\">—</b>/ 40 énergie", "<b id=\"mbEnergie\">—</b>/ 45 énergie")
s = rep(s, "const e = energieEtat.energie, max = 40;", "const e = energieEtat.energie, max = energieEtat.maximum || 45;   // patch237")
s = rep(s, "prochaineMin + (manque - 1) * 10 : 0;", "prochaineMin + (manque - 1) * 8 : 0;")
s = rep(s, "L'énergie se recharge seule : +1 toutes les 10 minutes.", "L'énergie se recharge seule : +1 toutes les 8 minutes.")
s = rep(s, "40 au maximum, +1 toutes les 10 minutes.", "45 au maximum, +1 toutes les 8 minutes.")
f.write_text(s, encoding='utf-8')
f, s = ouvrir('style.css')
s = rep(s, ".je-barre{ display:grid; grid-template-columns:repeat(40,1fr);", ".je-barre{ display:grid; grid-template-columns:repeat(45,1fr);")
f.write_text(s, encoding='utf-8')
f, s = ouvrir('index.html')
s = rep(s, "<b>40</b><span>énergie au maximum</span></div><div class=\"chiffre-bloc\"><b>10 min</b>",
           "<b>45</b><span>énergie au maximum</span></div><div class=\"chiffre-bloc\"><b>8 min</b>")
s = rep(s, "L'énergie récoltée peut dépasser 40, jusqu'à 60.", "L'énergie récoltée peut dépasser 45, jusqu'à 60.")
s = rep(s, "elle peut faire dépasser les 40, jusqu'à 60.", "elle peut faire dépasser les 45, jusqu'à 60.")
f.write_text(s, encoding='utf-8'); print('patch237 ok')
