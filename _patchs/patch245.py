# patch245 : plus de rappel « contrat » dans la collection du Front
# Les contrats du Front sont fermés depuis s2-32 (signer_contrat n'est plus appelable) et
# l'onglet Contrat n'existe qu'en Terra : le bandeau menait nulle part.
import pathlib
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
a = "  if(!c || ctTerra()){ bloc.hidden = true; return; }\n"
assert s.count(a) == 1, s.count(a)
s = s.replace(a, "  if(!c || ctTerra() || SAISON2){ bloc.hidden = true; return; }   // patch245 : pas de contrat en Front\n")
f.write_text(s, encoding='utf-8'); print('patch245 ok')
