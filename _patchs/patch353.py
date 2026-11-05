# patch353 (5/11/2026) : deux idées de joueurs sur Discord.
#
# 1. Roue du Front : les chances sous la roue sont rangées de la plus fréquente
#    à la plus rare (avant : dans l'ordre des cases sur la roue).
# 2. Collection Terra, filtre « Doublons » : les cartes sont rangées par nombre
#    d'exemplaires (le « ×N » affiché sur la carte), du plus petit au plus grand
#    (demandé : « dans l'ordre croissant ») ; toucher à nouveau « Doublons »
#    inverse l'ordre (flèche ↑ / ↓ sur le bouton, retenue dans le navigateur).
#    Puis rareté et population comme avant. Les autres filtres ne changent pas.
# Rien d'autre ne change, aucun SQL.
import pathlib, json

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch353' not in s, 'patch353 déjà appliqué'

s = rep(s, "return `<h4>Chances de chaque case</h4>${A.map(x => `<div class=\"rdf-ch\">",
           "return `<h4>Chances de chaque case</h4>${[...A].sort((a, b) => b.p - a.p).map(x => `<div class=\"rdf-ch\">")   # patch353
s = rep(s, "    .sort((a, b) => RANG_TIER[b.tier.id] - RANG_TIER[a.tier.id] || (b.pop || 0) - (a.pop || 0));\n  if(terraFiltre === 'evenement'){   // patch282",
           "    .sort((a, b) => (terraFiltre === 'doublons' ? (terraDblCroissant ? 1 : -1) * ((a.exemplaires || 0) - (b.exemplaires || 0)) : 0)   // patch353\n"
           "      || RANG_TIER[b.tier.id] - RANG_TIER[a.tier.id] || (b.pop || 0) - (a.pop || 0));\n  if(terraFiltre === 'evenement'){   // patch282")
s = rep(s, "let terraFiltre = 'tous';\n",
           "let terraFiltre = 'tous';\n"
           "// patch353 : ordre du filtre « Doublons » (croissant par défaut ; toucher à nouveau le bouton inverse)\n"
           "let terraDblCroissant = (() => { try{ return localStorage.getItem('tf-terra-dbl') !== 'desc'; }catch(e){ return true; } })();\n")
s = rep(s, ">Doublons <span class=\"nb\">${fmtNombre(nbDbl)}</span></button>",
           ">Doublons${terraFiltre === 'doublons' ? (terraDblCroissant ? ' ↑' : ' ↓') : ''} <span class=\"nb\">${fmtNombre(nbDbl)}</span></button>")   # patch353
s = rep(s, "  if(f){ terraFiltre = f.dataset.tcf; terraLimite = 120; renderCollectionTerra(); return; }",
           "  if(f){\n"
           "    if(f.dataset.tcf === 'doublons' && terraFiltre === 'doublons'){   // patch353 : deuxième appui = ordre inversé\n"
           "      terraDblCroissant = !terraDblCroissant;\n"
           "      try{ localStorage.setItem('tf-terra-dbl', terraDblCroissant ? 'asc' : 'desc'); }catch(err){}\n"
           "    }\n"
           "    terraFiltre = f.dataset.tcf; terraLimite = 120; renderCollectionTerra(); return;\n"
           "  }")
F.write_text(s, encoding='utf-8')

N = pathlib.Path('data/nouveautes.json')
d = json.loads(N.read_text(encoding='utf-8'))
assert d and d[0].get('date') == '2026-11-05', 'la première entrée n’est pas celle du 5/11'
lignes = ['🎡 Roue du Front : les chances sous la roue sont rangées de la plus fréquente à la plus rare (idée d’Arkhannou)',
          '🃏 Collection Terra : le filtre « Doublons » range les cartes par nombre d’exemplaires, du plus petit au plus grand. Touche-le une deuxième fois pour inverser l’ordre (idée de Maroli)']
for l in lignes:
    if l not in d[0]['nouveautes']: d[0]['nouveautes'].append(l)
N.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch353 appliqué')
