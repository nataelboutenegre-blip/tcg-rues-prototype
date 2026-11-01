# patch304 : deux bugs signalés par Maroli (1/11, #bugs)
# 1. Échanges de clan : la liste de ses communes s'arrêtait à 1 000 (limite de Supabase par
#    réponse). Maroli en a ~1 900, triées de la plus rare à la plus commune : ses communes
#    « commun » (ex. Saint-Auban, 06) n'arrivaient jamais. Chargement par pages
#    (toutesLesLignes, comme la collection et les contrats), tri refait ici. Et une erreur de
#    chargement n'est plus gardée en mémoire : le jeu réessaie au rendu suivant.
# 2. Carte sur téléphone : toucher une commune ouvre sa fiche au relâcher du doigt, puis le
#    navigateur envoie un « clic » au même endroit, qui tombait sur le bouton qui venait
#    d'apparaître dessous (ex. « +1 » de la garnison). Les clics reçus par la fiche dans les
#    400 ms qui suivent son ouverture au doigt sont ignorés.
import json, pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch304' not in s

# 1. échanges de clan : par pages, tri, pas d'erreur figée
s = rep(s, """async function ceChargerCommunes(){
  if(!monUidClan){ const { data: u } = await sb.auth.getUser(); monUidClan = u && u.user ? u.user.id : null; }
  if(!clanEch.mes && monUidClan){
    const { data, error } = await sb.rpc('clan_ech_communes', { p_joueur: monUidClan });
    clanEch.mes = error ? [] : (data || []);
  }
  if(clanEch.qui && !clanEch.leurs){
    const { data, error } = await sb.rpc('clan_ech_communes', { p_joueur: clanEch.qui });
    clanEch.leurs = error ? [] : (data || []);
  }
  majListesCe();""",
"""// patch304 : par pages (plus de 1 000 communes chez les gros joueurs), de la plus rare à la plus commune
async function ceCommunesDe(joueur){
  const { data, error } = await toutesLesLignes(() => sb.rpc('clan_ech_communes', { p_joueur: joueur }), 'code');
  if(error) return null;
  const rang = (t) => { const i = TIERS.findIndex(x => x.id === t); return i < 0 ? 99 : i; };
  return (data || []).sort((a, b) => rang(a.tier) - rang(b.tier) || String(a.nom).localeCompare(String(b.nom), 'fr'));
}
async function ceChargerCommunes(){
  if(!monUidClan){ const { data: u } = await sb.auth.getUser(); monUidClan = u && u.user ? u.user.id : null; }
  if(clanEch.mesErreur){ clanEch.mes = null; clanEch.mesErreur = false; }   // patch304 : on réessaie
  if(clanEch.leursErreur){ clanEch.leurs = null; clanEch.leursErreur = false; }
  if(!clanEch.mes && monUidClan){
    const l = await ceCommunesDe(monUidClan);
    clanEch.mes = l || []; clanEch.mesErreur = !l;
  }
  if(clanEch.qui && !clanEch.leurs){
    const qui = clanEch.qui, l = await ceCommunesDe(qui);
    if(clanEch.qui === qui){ clanEch.leurs = l || []; clanEch.leursErreur = !l; }
  }
  majListesCe();""")

# 2. carte : le clic fantôme après l'ouverture de la fiche au doigt
s = rep(s, """    const t = communeSousLePoint(x, y);
    if(t) ouvrirPanneau(t.commune.code, x, y);
    else fermerPanneau();
  });""",
"""    const t = communeSousLePoint(x, y);
    if(t){ ouvrirPanneau(t.commune.code, x, y); if(e.pointerType !== 'mouse') panneauOuvertAuDoigt = performance.now(); }   // patch304
    else fermerPanneau();
  });""")
s = rep(s, """      if(dep) ouvrirPanneauDept(dep, x, y);
      else fermerPanneau();
      return;
    }
    const t = communeSousLePoint(x, y);""",
"""      if(dep){ ouvrirPanneauDept(dep, x, y); if(e.pointerType !== 'mouse') panneauOuvertAuDoigt = performance.now(); }   // patch304
      else fermerPanneau();
      return;
    }
    const t = communeSousLePoint(x, y);""")
s = rep(s, """document.getElementById('mapPanneau').addEventListener('click', (e) => {""",
"""// patch304 : après l'ouverture de la fiche au doigt, le navigateur envoie un clic au même endroit,
// qui tombait sur le bouton apparu dessous (« +1 » de la garnison) : on l'ignore.
let panneauOuvertAuDoigt = 0;
document.getElementById('mapPanneau').addEventListener('click', (e) => {
  if(performance.now() - panneauOuvertAuDoigt < 400){ e.stopPropagation(); e.preventDefault(); }
}, true);
document.getElementById('mapPanneau').addEventListener('click', (e) => {""")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('data/nouveautes.json'); d = json.loads(f.read_text(encoding='utf-8'))
e = next(x for x in d if x['date'] == '2026-11-01')
e['correctifs'].insert(0, 'Échanges de clan : toutes tes communes sont proposées, même au-delà de 1 000 ; et toucher une ville sur la carte n’ajoute plus d’énergie en garnison par erreur')
f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch304 appliqué')
