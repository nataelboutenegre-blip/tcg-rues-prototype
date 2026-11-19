# patch473 : la roue du Front garde jusqu'à 5 tours en réserve (idée d'ASMFCB, 17/11), avec s3-37.
# Le jeu lit la réserve envoyée par le serveur (ROUE.reserve) ; sans elle, il reste à 3.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
rep(A, """function roueJetons(){
  if(!ROUE) return 0;
  const j = Number(ROUE.jetons) || 0;
  if(j >= 3) return j;   // un cadeau au-dessus de 3 est gardé
  return Math.min(3, j + (Date.now() - roueLu) / 1200000);
}""", """function roueReserve(){   // patch473 : tours gardés en réserve (s3-37 : 5)
  return Math.max(3, Number(ROUE && ROUE.reserve) || 3);
}
function roueJetons(){
  if(!ROUE) return 0;
  const j = Number(ROUE.jetons) || 0, cap = roueReserve();
  if(j >= cap) return j;   // un cadeau au-dessus de la réserve est gardé
  return Math.min(cap, j + (Date.now() - roueLu) / 1200000);
}""")
rep(A, "  const prochain = live >= 3 ? 0 : (1 - (live % 1)) * 1200;", "  const prochain = live >= roueReserve() ? 0 : (1 - (live % 1)) * 1200;   // patch473")
rep(A, "  roueEcrire('rdfSlots', [0, 1, 2].map(i => slot(i < dispo)).join(''));",
       "  roueEcrire('rdfSlots', Array.from({ length: roueReserve() }, (_, i) => slot(i < dispo)).join(''));   // patch473")
rep(A, "    : dispo >= 3 ? 'Réserve pleine", "    : dispo >= roueReserve() ? 'Réserve pleine")   # patch473
rep('index.html', "(toujours 1 toutes les 20 min, 3 en réserve)", "(1 toutes les 20 min, jusqu'à 5 en réserve)")
rep('style.css', ".rdf-slot.vide{ border:1.5px dashed rgba(169,188,212,.35); background:transparent; color:rgba(169,188,212,.35); }",
    ".rdf-slot.vide{ border:1.5px dashed rgba(169,188,212,.35); background:transparent; color:rgba(169,188,212,.35); }\n"
    "@media (max-width:360px){   /* patch473 : 5 cases sur un petit écran */\n"
    "  .rdf-slots:has(.rdf-slot:nth-child(4)){ gap:4px; }\n"
    "  .rdf-slots:has(.rdf-slot:nth-child(4)) .rdf-slot{ width:25px; height:25px; border-radius:8px; }\n"
    "  .rdf-slots:has(.rdf-slot:nth-child(4)) .rdf-slot svg{ width:14px; height:14px; }\n"
    "}")
print('patch473 : fini')
