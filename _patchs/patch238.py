# patch238 : clans à 8 membres (s2-45)
import pathlib
def ouvrir(n): return pathlib.Path(n), pathlib.Path(n).read_text(encoding='utf-8')
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:70], s.count(a)); return s.replace(a, b)
f, s = ouvrir('app.js')
s = rep(s, "'Le clan est complet (6 membres).'", "'Le clan est complet (8 membres).'")
f.write_text(s, encoding='utf-8')
f, s = ouvrir('index.html')
s = rep(s, "3 à 6 joueurs, comme les côtés de l’Hexagone. En Front", "3 à 8 joueurs. En Front")
s = rep(s, "<p><b>Clan</b> : jusqu'à <b>6 joueurs</b>.", "<p><b>Clan</b> : jusqu'à <b>8 joueurs</b>.")
f.write_text(s, encoding='utf-8'); print('patch238 ok')
