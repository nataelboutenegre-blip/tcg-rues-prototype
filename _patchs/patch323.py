# patch323 : plus d'attente pour rejoindre un clan (s2-84, décidé le 2/11 au soir)
#  Les textes qui parlaient des 48 h d'attente après un départ disent maintenant qu'on
#  change de clan quand on veut, et rappellent la protection des échanges (48 h après
#  l'arrivée, inchangée). Le bouton « Quitter le clan » ne parle plus d'attente.
#  À pousser APRÈS avoir lancé s2-84 (sinon le texte promet ce que le serveur refuse).
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch323' not in s
s = rep(s, "<li>Après avoir quitté un clan, il faut attendre 48 h avant d'en rejoindre un autre.</li>",
           "<li>Tu peux changer de clan quand tu veux. Dans un nouveau clan, les échanges s'ouvrent 48 h après ton arrivée.</li>")
s = rep(s, "b.textContent = 'Confirmer : quitter (48 h d\\'attente)'; return; }",
           "b.textContent = 'Confirmer : quitter le clan'; return; }   // patch323 : plus d'attente (s2-84)")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
assert 'patch323' not in s
s = rep(s, " Après avoir quitté un clan, il faut attendre 48 h pour en rejoindre un autre.</p>",
           " Tu peux changer de clan quand tu veux ; dans un nouveau clan, les échanges s'ouvrent 48 h après ton arrivée.</p><!-- patch323 -->")
f.write_text(s, encoding='utf-8')
print('patch323 ok')
