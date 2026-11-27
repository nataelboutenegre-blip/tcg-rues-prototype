# patch559 (27/11) : lingots dans le bouton Front (Saaslil), sauvegardes de motifs (Arkhannou), coffre du clan (Bonjean).
# Serveur : _sql/s3-90-motifs-sauvegardes.sql, _sql/s3-91-coffre-clan.sql (coffre allumé par config_jeu clans_s3.coffre).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
D = os.path.dirname(os.path.abspath(__file__))
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
def ajouter(f, src, marque):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if marque in t: print(f'{f} : déjà ajouté'); return
    open(p, 'a', encoding='utf-8').write(open(os.path.join(D, src), encoding='utf-8').read()); print(f'{f} : ajouté')
rep('app.js', """${ICONE_ENERGIE}<b id="mbEnergie">—</b>/ <span id="mbMax">50</span><span class="mb-u"> énergie</span></span></button>`;""",
    """${ICONE_ENERGIE}<b id="mbEnergie">—</b><span class="mb-sur">/ <span id="mbMax">50</span></span><span class="mb-u"> énergie</span><span class="mb-lg" id="mbLingots" hidden title="Tes lingots">${ICONE_LINGOT}<b>—</b></span></span></button>`;   // patch559 : les lingots""")
ajouter('app.js', 'patch559-trois.js', 'patch559 : trois idées du salon')
ajouter('style.css', 'patch559.css', 'patch559 : lingots dans le bouton Front')
p = os.path.join(R, 'data/nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
assert d[0]['date'] in ('2026-11-26', '2026-11-27')
for c in ["Tes lingots s'affichent en haut, dans le bouton Front, à côté de ton énergie. Idée de Saaslil.",
          "Mon motif › Modèles : 6 places pour sauvegarder tes motifs et les recharger quand tu veux, sur téléphone comme sur ordinateur. Idée d'Arkhannou.",
          "Le coffre du clan (onglet Clan) : tout le monde y dépose des lingots, chacun peut en retirer 15 par jour après 48 h dans le clan. Le journal montre qui dépose et qui retire, et le chef peut bloquer les retraits. Idée de Bonjean."]:
    if c not in d[0].setdefault('nouveautes', []): d[0]['nouveautes'].insert(0, c)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('nouveautes : ok')
