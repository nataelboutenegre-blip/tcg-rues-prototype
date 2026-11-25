# patch533 (Maroli) : un paquet du pass ouvert en mode Front partait en tirage Front (erreur) alors que le serveur
# donne des cartes Terra. On passe d'abord en Terra.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', """  boutiqueAchat = { pass: Number(niveau), dep };
  boutiqueOuvert = false;
""", """  if(!enTerra()){   // patch533 : les cartes du pass vont dans la collection Terra
    const bt = document.querySelector('[data-mode="terra"]');
    if(bt) bt.click();
    if(!enTerra()){ notifier({ type: 'erreur', titre: 'Passe en Terra', texte: 'Ce paquet donne des cartes Terra : passe en mode Terra pour l\\'ouvrir.' }); return; }
  }
  boutiqueAchat = { pass: Number(niveau), dep };
  boutiqueOuvert = false;
""")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-25': d.insert(0, {'date': '2026-11-25', 'nouveautes': [], 'correctifs': []})
e = d[0]; e.setdefault('correctifs', [])
l = "🎁 Pass : ouvrir un paquet du pass depuis le mode Front affichait une erreur. Le jeu passe maintenant en Terra pour l'ouvrir (les cartes allaient bien dans ta collection Terra). Merci Maroli."
if l not in e['correctifs']: e['correctifs'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
