# patch390 : réserve d'énergie du Front 90 -> 120 (s2-128, décision de Nataël le 9/11 à 16 h 14).
# Le jeu lit déjà le maximum du serveur ; restent les textes en dur et la valeur de repli.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
s = rep(s, "function energieMax(){ return (energieEtat && Number(energieEtat.maximum)) || 90; }",
           "function energieMax(){ return (energieEtat && Number(energieEtat.maximum)) || 120; }   // patch390")
s = rep(s, "l\\'énergie remplace les TerraPoints : 90 au maximum, +1 toutes les 7 minutes.",
           "l\\'énergie remplace les TerraPoints : 120 au maximum, +1 toutes les 7 minutes.")
F.write_text(s, encoding='utf-8')

H = pathlib.Path('index.html'); h = H.read_text(encoding='utf-8')
h = rep(h, '<div class="chiffre-bloc"><b>90</b><span>énergie au maximum</span></div>',
           '<div class="chiffre-bloc"><b>120</b><span>énergie au maximum</span></div><!-- patch390 -->')
H.write_text(h, encoding='utf-8')
print('patch390 ok')
