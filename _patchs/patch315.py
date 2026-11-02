# patch315 : les communes des membres de ton clan ne s'affichent plus dans Combat (signalé par Arkhannou)
# Elles étaient bien censées être retirées (patch110), mais la liste des membres du clan
# arrive parfois après le premier affichage de Combat : les cartes restaient là, avec un
# « Attaquer » qui finissait en « Action impossible ». On réaffiche Combat dès que la
# liste des membres change.
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch315' not in s
s = rep(s, """    clanMembres = new Set(moi ? (data || []).filter(r => r.tag === moi.tag && r.joueur_id !== monUidClan).map(r => r.joueur_id) : []);
""", """    const avantClan = [...clanMembres].sort().join(',');   // patch315
    clanMembres = new Set(moi ? (data || []).filter(r => r.tag === moi.tag && r.joueur_id !== monUidClan).map(r => r.joueur_id) : []);
    if([...clanMembres].sort().join(',') !== avantClan && combatCibles.length){ try{ renderCombatGrid(); }catch(e){} }   // patch315
""")
f.write_text(s, encoding='utf-8')
print('patch315 appliqué')
