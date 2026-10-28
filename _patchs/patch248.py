# patch248 : journal — le département en pastille et le nom de la commune mène à la carte (demande d'Arkhannou)
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
s = rep(s, """  const commune = `<b class="jr-commune ${e.tier || ''}">${echapperTexte(e.commune_nom || 'une commune')}</b>`;
  let texte;""",
"""  // patch248 : comme dans les listes du Front — le nom (et l'icône carte) mène à la commune,
  // et la pastille du département, tirée du code INSEE (3 chiffres en outre-mer)
  const cc = String(e.commune_code || '');
  const nomC = `<b class="jr-commune ${e.tier || ''}">${echapperTexte(e.commune_nom || 'une commune')}</b>`;
  const commune = cc
    ? `<button type="button" class="df-voir jr-voir" data-voir-carte="${echapperTexte(cc)}" title="Voir sur la carte">${nomC}<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/></svg></button> ${badgeDept(cc.startsWith('97') ? cc.slice(0, 3) : cc.slice(0, 2))}`
    : nomC;
  let texte;""")
# le clic : une commune qui n'est ni à moi ni dans le Front (tirage Terra) n'a pas ses coordonnées côté client
s = rep(s, """  const code = b.dataset.voirCarte;
  voirCommuneSurCarte(collectionMap.get(code) || { code });
});""",
"""  const code = b.dataset.voirCarte;
  const connue = collectionMap.get(code) || othersMap.get(code);   // patch248
  if(connue && connue.lat != null) return voirCommuneSurCarte(connue);
  if(estOutremerCode(code)) return voirCommuneSurCarte({ code });
  sb.from('communes').select('latitude, longitude').eq('code', code).maybeSingle()
    .then(({ data }) => voirCommuneSurCarte({ code, lat: data && data.latitude, lon: data && data.longitude }));
});""")
f.write_text(s, encoding='utf-8')
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
s += """
/* ---------- patch248 : journal — commune cliquable + pastille du département ---------- */
.jr-texte .jr-voir{ display:inline-flex; vertical-align:baseline; }
.jr-texte .jr-voir b{ text-decoration:underline dotted rgba(169,188,212,.55); text-underline-offset:3px; }
.jr-texte .dep{ margin-left:2px; }
"""
f.write_text(s, encoding='utf-8')
print('patch248 ok')
