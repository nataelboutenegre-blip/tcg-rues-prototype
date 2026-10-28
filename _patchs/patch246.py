# patch246 : (1) une notif sur une commune de métropole ramène la carte sur la France
#            quand on regardait l'outre-mer ; (2) en outre-mer, la proximité = le territoire (s2-49)
import pathlib
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
s = rep(s, """  if(fermerFiche) fermerFiche(null);
  const onglet = document.querySelector('.tab[data-tab="territoire"]');
  if(onglet) onglet.click();
  const carte = document.getElementById('mapWrap');""", """  if(fermerFiche) fermerFiche(null);
  const onglet = document.querySelector('.tab[data-tab="territoire"]');
  if(onglet) onglet.click();
  if(frontZone === 'outremer') basculerZoneFront('france');   // patch246 : retour à la France
  const carte = document.getElementById('mapWrap');""")
s = rep(s, """      ${a.a_distance
        ? 'Aucune de tes communes à moins de 20 km : <b>attaque à distance</b>, tes chances baissent.'
        : `<b>${a.proches}</b> de tes communes à moins de 20 km`}""", """      ${estOutremerCode(code)   // patch246 : en outre-mer, tout le territoire compte (s2-49)
        ? (a.a_distance
          ? 'Aucune de tes communes dans ce territoire : <b>attaque à distance</b>, tes chances baissent.'
          : `<b>${a.proches}</b> de tes communes dans ce territoire`)
        : a.a_distance
        ? 'Aucune de tes communes à moins de 20 km : <b>attaque à distance</b>, tes chances baissent.'
        : `<b>${a.proches}</b> de tes communes à moins de 20 km`}""")
f.write_text(s, encoding='utf-8'); print('patch246 ok')
