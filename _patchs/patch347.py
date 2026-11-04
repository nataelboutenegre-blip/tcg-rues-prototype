# patch347 (4/11/2026) : dans la discussion, mes messages ont aussi mon avatar
# et mon blason de clan, en miroir (aperçu validé « ok parfait »). Pas de SQL :
# discussion_json (s2-99b) envoie déjà l'avatar et le clan.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
s = rep(s, """  if(m.moi) return `<div class="dg-m moi${m.masque ? ' masque' : ''}" data-dg-id="${m.id}"><div class="dg-b">${txt}${m.masque ? '<small class="dg-avert">Masqué pour les autres en attendant la modération</small>' : ''}</div></div>`;""",
"""  if(m.moi){   // patch347 : mon avatar et mon blason, en miroir
    const cm = colorForPlayer(m.auteur || '');
    const hm = groupe ? '' : `<div class="dg-h"><span class="dg-t">${dgHeure(m.le)}</span>${dgClanHtml(m)}<b style="color:${cm}">${echapperTexte(m.pseudo || 'Moi')}</b></div>`;
    return `<div class="dg-m moi${m.masque ? ' masque' : ''}" data-dg-id="${m.id}"><div class="dg-b">${hm}${txt}${m.masque ? '<small class="dg-avert">Masqué pour les autres en attendant la modération</small>' : ''}</div>${dgAvatar(m, groupe)}</div>`;
  }""")
s = rep(s, """    const groupe = !!(p && !m.moi && !m.retire && !p.retire && p.auteur === m.auteur""",
"""    const groupe = !!(p && !m.retire && !p.retire && p.auteur === m.auteur""")
F.write_text(s, encoding='utf-8')

F = pathlib.Path('style.css'); s = F.read_text(encoding='utf-8')
s += """
/* patch347 : mes messages, avec avatar et blason en miroir */
.dg-m.moi .dg-h{ justify-content:flex-end; }
.dg-m.moi .dg-h .dg-t{ margin-left:0; padding-left:0; padding-right:4px; }
"""
F.write_text(s, encoding='utf-8')
print('patch347 appliqué')
