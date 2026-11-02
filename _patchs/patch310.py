# patch310 : les bâtiments dans le journal (s2-77)
# « Maroli a construit une Fonderie à Sens 89 », « … une Forteresse à Auxerre 89 »,
# « Oshannir a détruit la Fonderie de Maroli à Joigny 89 » (ta Fonderie, si c'est la tienne).
# Le Centre de recherche n'y apparaît jamais (il est secret). Une construction annulée
# disparaît du journal (s2-77). Pas encore de pastille de filtre « Bâtiments » : ces lignes
# sont dans « Tout » et dans « Ce qui me concerne ».
import json, pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch310' not in s

# les icônes (après celles des bâtiments, définies plus bas que ICONES_JOURNAL)
i = s.index("const ICONE_FORTERESSE = ")
j = s.index("\n", i)
s = s[:j + 1] + """// patch310 : les bâtiments dans le journal
ICONES_JOURNAL.fonderie = ICONE_FONDERIE;
ICONES_JOURNAL.forteresse = ICONE_FORTERESSE;
ICONES_JOURNAL.fonderie_detruite = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3c.6 3.2 4.5 4.6 4.5 9a4.5 4.5 0 0 1-9 0c0-2 1-3.2 2-4.2.2 1.6 1 2.4 1.9 2.7C11 8.6 11.2 5.5 12 3z"/><path d="M4 21h16"/></svg>';
""" + s[j + 1:]

s = rep(s, """  else if(e.type === 'contrat') texte = `${acteur} ${a} obtenu ${commune} par un contrat`;
""", """  else if(e.type === 'contrat') texte = `${acteur} ${a} obtenu ${commune} par un contrat`;
  else if(e.type === 'fonderie') texte = `${acteur} ${a} construit une Fonderie à ${commune}`;   // patch310
  else if(e.type === 'forteresse') texte = `${acteur} ${a} construit une Forteresse à ${commune}`;
  else if(e.type === 'fonderie_detruite') texte = `${acteur} ${a} détruit ${e.je_suis_cible ? '<b>ta</b> Fonderie' : `la Fonderie de ${cible}`} à ${commune}`;
""")
s = rep(s, """  const perso = e.je_suis_cible && (e.type === 'conquete' || e.type === 'achat');""",
           """  const perso = e.je_suis_cible && (e.type === 'conquete' || e.type === 'achat' || e.type === 'fonderie_detruite');   // patch310""")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch310' not in s
s = s.rstrip('\n') + """

/* patch310 : les bâtiments dans le journal */
.jr-ligne.fonderie, .jr-ligne.forteresse{ border-left-color:#E8833A; }
.jr-ligne.fonderie .jr-icone, .jr-ligne.forteresse .jr-icone{ color:#FFB27A; background:rgba(232,131,58,.16); }
.jr-ligne.fonderie_detruite{ border-left-color:#E5484D; }
.jr-ligne.fonderie_detruite .jr-icone{ color:#FF8F92; background:rgba(229,72,77,.15); }
"""
f.write_text(s, encoding='utf-8')

f = pathlib.Path('data/nouveautes.json'); d = json.loads(f.read_text(encoding='utf-8'))
e = next(x for x in d if x['date'] == '2026-11-02')
e['nouveautes'].insert(0, '📰 Journal : les Fonderies et Forteresses construites, et les Fonderies détruites, y apparaissent (jamais le Centre de recherche, qui reste secret)')
f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch310 appliqué')
