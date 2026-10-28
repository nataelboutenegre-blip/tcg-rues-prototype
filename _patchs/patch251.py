# patch251 : l'écran Clan était resté à 6 (patch238 n'avait changé que le message d'erreur) :
# le champ « Inviter » disparaissait dès 6 membres, et « sur 6 » s'affichait encore
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
s = rep(s, "${c.chef && n < 6 ? `<div class=\"clan-inviter\">", "${c.chef && n < 8 ? `<div class=\"clan-inviter\">")
s = rep(s, "<small>${n} membre${n > 1 ? 's' : ''} sur 6${n < 3", "<small>${n} membre${n > 1 ? 's' : ''} sur 8${n < 3")
s = rep(s, "${liste.length} membre${liste.length > 1 ? 's' : ''} sur 6 · ", "${liste.length} membre${liste.length > 1 ? 's' : ''} sur 8 · ")
f.write_text(s, encoding='utf-8'); print('patch251 ok')
