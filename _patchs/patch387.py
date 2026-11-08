# patch387 : l'énergie se recharge toutes les 7 min (réglage config_jeu 'energie_front'.recharge_s = 420,
# décision de Nataël le 8/11 à 21 h 48). Le jeu lit déjà le réglage ; restent les textes en dur.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
s = rep(s, "return x ? Math.max(1, Math.round(x / 60)) : 10; }", "return x ? Math.max(1, Math.round(x / 60)) : 7; }   // patch387")
s = rep(s, "90 au maximum, +1 toutes les 10 minutes. Elle sert", "90 au maximum, +1 toutes les 7 minutes. Elle sert")
F.write_text(s, encoding='utf-8')

H = pathlib.Path('index.html'); h = H.read_text(encoding='utf-8')
h = rep(h, '<div class="chiffre-bloc"><b>10 min</b><span>pour recharger 1 énergie</span></div>',
           '<div class="chiffre-bloc"><b>7 min</b><span>pour recharger 1 énergie</span></div><!-- patch387 -->')
H.write_text(h, encoding='utf-8')
print('patch387 ok')
