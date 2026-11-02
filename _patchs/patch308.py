# patch308 : le numéro du département dans la cloche (idée d'Arkhannou, 2/11)
# « Nataël t'attaque à Sotta 2A », « … t'a pris Joigny 89 », « Tu as repoussé … à Sens 89 » :
# la même pastille que dans le journal (tirée du code INSEE, 3 chiffres en outre-mer).
import json, pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch308' not in s
s = rep(s, """function badgeDept(dep){""",
"""// patch308 : le département d'une commune, depuis son code INSEE (3 chiffres en outre-mer)
const depDuCode = (cc) => { cc = String(cc || ''); return cc.startsWith('97') ? cc.slice(0, 3) : cc.slice(0, 2); };
function badgeDept(dep){""")
s = rep(s, """<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/></svg></button>`,""",
           """<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/></svg></button> ${badgeDept(depDuCode(m.commune_code))}`,   // patch308""")
s = rep(s, """    const nom = `<b>${echapperTexte(e.commune_nom || '')}</b>`;""",
           """    const nom = `<b>${echapperTexte(e.commune_nom || '')}</b>${e.commune_code ? ' ' + badgeDept(depDuCode(e.commune_code)) : ''}`;   // patch308""")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('data/nouveautes.json'); d = json.loads(f.read_text(encoding='utf-8'))
e = next(x for x in d if x['date'] == '2026-11-02')
e['correctifs'].insert(0, 'Notifications : le numéro du département s’affiche à côté de la commune attaquée (merci Arkhannou)')
f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch308 appliqué')
