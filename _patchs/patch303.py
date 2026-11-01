# patch303 : page Confidentialité (1/11) — avant le mail aux joueurs inactifs
# L'adresse e-mail peut servir, rarement, à écrire au joueur au sujet de son compte et de la vie
# du jeu (nouvelle saison, changement important), avec un lien de désinscription dans chaque mail.
# Base : intérêt légitime. Resend : « e-mails de compte et messages sur le jeu ».
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('confidentialite.html'); s = f.read_text(encoding='utf-8')
assert 'patch303' not in s
s = rep(s, '<p class="pg-maj">Dernière mise à jour : 6 octobre 2026</p>',
           '<p class="pg-maj">Dernière mise à jour : 1er novembre 2026</p><!-- patch303 -->')
s = rep(s, "<td>Créer ton compte, te connecter, réinitialiser ton mot de passe</td></tr>",
           "<td>Créer ton compte, te connecter, réinitialiser ton mot de passe. Et, rarement, t'écrire au sujet de ton compte et de la vie du jeu (nouvelle saison, changement important) : chaque e-mail contient un lien pour ne plus en recevoir</td></tr>")
s = rep(s, "  <li><b>L'intérêt légitime</b> de protéger le jeu contre la triche et les abus : journaux techniques.</li>",
           "  <li><b>L'intérêt légitime</b> de protéger le jeu contre la triche et les abus : journaux techniques.</li>\n"
           "  <li><b>L'intérêt légitime</b> de te tenir au courant de ton compte et de la vie du jeu : les rares e-mails sur le jeu. Tu peux t'y opposer à tout moment, avec le lien présent dans chaque e-mail ou en écrivant à contact@terrafront.fr.</li>")
s = rep(s, "  <li><b>Resend</b> (États-Unis) : envoi des e-mails de compte (confirmation, mot de passe oublié) ;</li>",
           "  <li><b>Resend</b> (États-Unis) : envoi des e-mails de compte (confirmation, mot de passe oublié) et des rares e-mails sur le jeu ;</li>")
f.write_text(s, encoding='utf-8')
print('patch303 appliqué')
