# patch333 (3/11/2026) : Commune du jour, la région dès le départ (avec s2-92 ; aperçu validé « parfait »).
# Le libellé « après n essais » suit ce que dit le serveur (« apres ») ; sans ce
# champ (s2-92 pas encore lancé), l'ancien calcul reste. Texte d'intro adapté.
import pathlib

F = pathlib.Path('app.js')
s = F.read_text(encoding='utf-8')
H = pathlib.Path('index.html')
h = H.read_text(encoding='utf-8')

def rep(avant, apres, n=1):
    global s
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    s = s.replace(avant, apres)

rep("""<span class="cdj-val">${ouvert ? echapperTexte(valeur) : `après ${n + 1} essai${n ? 's' : ''}`}</span></li>`;""",
    """<span class="cdj-val">${ouvert ? echapperTexte(valeur) : (() => { const k = i.apres != null ? i.apres : n + 1; return `après ${k} essai${k > 1 ? 's' : ''}`; })()}</span></li>`;   // patch333""")

a = "six essais pour la trouver. Chaque erreur dévoile un indice,"
assert h.count(a) == 1, h.count(a)
h = h.replace(a, "six essais pour la trouver. Tu pars avec sa région, puis chaque erreur dévoile un nouvel indice,")

F.write_text(s, encoding='utf-8')
H.write_text(h, encoding='utf-8')
print('patch333 appliqué')
