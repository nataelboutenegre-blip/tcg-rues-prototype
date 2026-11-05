# patch351 (5/11/2026) : la roue du Front à 30 tours par jour (va avec
# _sql/s2-102-roue-30-tours.sql ; décision de Nataël du 5/11).
# - Trois cases nouvelles : TerraPoints (+10 TP), Cagnotte (+50 TP), Relance
#   (tour offert : le jeton est rendu et le tour ne compte pas dans les 30).
# - Leurs couleurs et icônes sur la roue (pièce « TP », flèche de relance),
#   leur texte dans les chances et à l'arrivée ; le solde de TP est relu après
#   un gain de TP.
# - Les chances affichent aussi les TP moyens par tour.
# - Règles : 30 tours, TerraPoints, tour offert ; ligne dans la cloche.
# Sans s2-102 : la roue garde ses 8 cases et rien ne change.
import pathlib, json, datetime, os

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')

# 1. styles des nouvelles cases
s = rep(s, """  jackpot: { c1: '#FF6FA0', c2: '#C2124F', puce: '#E8306F', ic: 's', muet: true, fort: true },
};""", """  jackpot: { c1: '#FF6FA0', c2: '#C2124F', puce: '#E8306F', ic: 's', muet: true, fort: true },
  tp:       { c1: '#62E3F0', c2: '#147C8C', puce: '#2FB9CC', ic: 'tp' },                           // patch351
  cagnotte: { c1: '#FFF0A8', c2: '#B78A10', puce: '#E6BE2E', ic: 'tp', fort: true },
  relance:  { c1: '#EEF2F8', c2: '#7C889C', puce: '#B7C2D4', ic: 'r', muet: true },
};""")
s = rep(s, """  return ROUE_STYLE[k.id] || { c1: '#8A9BB4', c2: '#3D4B60', puce: '#8A9BB4', ic: e && l ? 'el' : e ? 'e' : l ? 'l' : Number(k.terra) > 0 ? 't' : 's' };""",
"""  return ROUE_STYLE[k.id] || { c1: '#8A9BB4', c2: '#3D4B60', puce: '#8A9BB4',
    ic: e && l ? 'el' : e ? 'e' : l ? 'l' : Number(k.terra) > 0 ? 't' : Number(k.tp) > 0 ? 'tp' : Number(k.relance) ? 'r' : 's' };   // patch351""")

# 2. icônes : pièce TP et flèche de relance
s = rep(s, """  if(ic === 't') return `<g transform="scale(${s})"><rect""", """  if(ic === 'tp') return `<g transform="scale(${s})"><circle r="10" fill="#E9FBFF" stroke="#0d5560" stroke-width="1.5"/><circle r="7.4" fill="none" stroke="#2FB9CC" stroke-width="1"/><text y="0.5" font-size="8.6" font-weight="900" text-anchor="middle" dominant-baseline="middle" fill="#0d5560">TP</text></g>`;   // patch351
  if(ic === 'r') return `<g transform="scale(${s})"><path d="M7.5 -3.2 A8 8 0 1 0 8.2 3" fill="none" stroke="#2F3A4C" stroke-width="2.6" stroke-linecap="round"/><path d="M9.8 -8.6 L8.4 -1.6 L1.8 -4.4 Z" fill="#2F3A4C"/></g>`;
  if(ic === 't') return `<g transform="scale(${s})"><rect""")

# 3. textes : sur la roue, dans les chances, à l'arrivée
s = rep(s, """  const e = Number(k.energie) || 0, l = Number(k.lingots) || 0;
  return e && l ? `+${e} · +${l}` : e ? `+${e}` : l ? `+${l}` : '';""", """  const e = Number(k.energie) || 0, l = Number(k.lingots) || 0, tp = Number(k.tp) || 0;
  return e && l ? `+${e} · +${l}` : e ? `+${e}` : l ? `+${l}` : tp ? `+${tp}` : '';   // patch351""")
s = rep(s, """  const e = Number(k.energie) || 0, l = Number(k.lingots) || 0, t = Number(k.terra) || 0;
  return [e ? `+${e}<span class="rdf-e">${ICONE_ENERGIE}</span>` : '', l ? `+${l} lingot${l > 1 ? 's' : ''}` : '', t ? `${t} paquet${t > 1 ? 's' : ''} Terra` : '']
    .filter(Boolean).join(' ');""", """  const e = Number(k.energie) || 0, l = Number(k.lingots) || 0, t = Number(k.terra) || 0, tp = Number(k.tp) || 0;
  if(Number(k.relance)) return 'Un tour offert';   // patch351
  return [e ? `+${e}<span class="rdf-e">${ICONE_ENERGIE}</span>` : '', l ? `+${l} lingot${l > 1 ? 's' : ''}` : '', t ? `${t} paquet${t > 1 ? 's' : ''} Terra` : '',
          tp ? `+${tp} TP` : '']
    .filter(Boolean).join(' ');""")
s = rep(s, """  const moyE = A.reduce((s, x) => s + x.p / 100 * (Number(x.k.energie) || 0), 0), moyL = A.reduce((s, x) => s + x.p / 100 * (Number(x.k.lingots) || 0), 0);""",
"""  const moyE = A.reduce((s, x) => s + x.p / 100 * (Number(x.k.energie) || 0), 0), moyL = A.reduce((s, x) => s + x.p / 100 * (Number(x.k.lingots) || 0), 0);
  const moyTP = A.reduce((s, x) => s + x.p / 100 * (Number(x.k.tp) || 0), 0), offert = A.some(x => Number(x.k.relance));   // patch351""")
s = rep(s, """    <p class="rdf-ch-pied">En moyenne : ${fr1(moyE, 1)} énergie et ${fr1(moyL, 2)} lingot par tour. ${ROUE.par_jour} tours au plus par jour.</p>`;""",
"""    <p class="rdf-ch-pied">En moyenne : ${fr1(moyE, 1)} énergie, ${fr1(moyL, 2)} lingot${moyTP ? ` et ${fr1(moyTP, 1)} TP` : ''} par tour. ${ROUE.par_jour} tours au plus par jour${offert ? ', sans compter les tours offerts' : ''}.</p>`;""")
s = rep(s, """<div class="rdf-sous">Énergie et lingots à gagner</div>""",
           """<div class="rdf-sous">${roueCases().some(k => Number(k.tp) > 0) ? 'Énergie, lingots et TerraPoints à gagner' : 'Énergie et lingots à gagner'}</div>""")

# 4. l'arrivée : TP et tour offert
s = rep(s, """  const k = seg ? seg.k : { nom: 'Gagné', energie: d.energie_prevue, lingots: d.lingots_prevus, terra: d.terra };
  const e = Number(d.energie) || 0, ep = Number(d.energie_prevue) || 0, l = Number(d.lingots) || 0, lp = Number(d.lingots_prevus) || 0, t = Number(d.terra) || 0;
  const parts = [];""", """  const k = seg ? seg.k : { nom: 'Gagné', energie: d.energie_prevue, lingots: d.lingots_prevus, terra: d.terra, tp: d.tp };
  const e = Number(d.energie) || 0, ep = Number(d.energie_prevue) || 0, l = Number(d.lingots) || 0, lp = Number(d.lingots_prevus) || 0, t = Number(d.terra) || 0;
  const tp = Number(d.tp) || 0, offert = d.relance === true;   // patch351
  const parts = [];
  if(offert) parts.push('Tour offert');
  if(tp) parts.push(`+${tp} TP`);""")
s = rep(s, """  else if(lp) note = `Tes lingots : ${d.lingots_total}`;
  else note = 'À ouvrir dans Terra';""", """  else if(lp) note = `Tes lingots : ${d.lingots_total}`;
  else if(offert) note = 'Ton tour est rendu : il ne compte pas dans la journée';   // patch351
  else if(tp) note = d.solde != null ? `Tes TerraPoints : ${Number(d.solde).toLocaleString('fr-FR')}` : 'Ajoutés à tes TerraPoints';
  else note = 'À ouvrir dans Terra';""")
s = rep(s, """  if(Number(data.energie) > 0 && typeof majEnergie === 'function') majEnergie();
}""", """  if(Number(data.energie) > 0 && typeof majEnergie === 'function') majEnergie();
  if(Number(data.tp) > 0 && data.solde != null){   // patch351 : le solde de TP suit
    if(packStatusCache) packStatusCache.solde = Number(data.solde);
    if(typeof majSoldeGlobal === 'function') majSoldeGlobal(Number(data.solde));
    majBascule();
  }
}""")
F.write_text(s, encoding='utf-8')

# 5. règles
H = pathlib.Path('index.html'); h = H.read_text(encoding='utf-8')
h = rep(h, """<b>15 tours par jour</b> au plus, gratuite. Elle donne de l'énergie (sans dépasser le maximum des bonus), des lingots (sans dépasser ta réserve de lingots) ou un paquet Terra.""",
"""<b>30 tours par jour</b> au plus, gratuite. Elle donne de l'énergie (sans dépasser le maximum des bonus), des lingots (sans dépasser ta réserve de lingots), des TerraPoints, un paquet Terra, ou un <b>tour offert</b> : ton tour est rendu et ne compte pas dans les 30.""")
H.write_text(h, encoding='utf-8')

# 6. la cloche, à la date du jour où le patch est appliqué
N = pathlib.Path('data/nouveautes.json')
if N.exists():
    t = N.read_text(encoding='utf-8')
    ligne = ("🎡 Roue du Front : 30 tours par jour au lieu de 15, et trois cases nouvelles : TerraPoints (+10 TP), "
             "Cagnotte (+50 TP) et Relance (ton tour est rendu). Les cases d'énergie et de lingots sont un peu plus rares, "
             "pour qu'une journée de roue rapporte à peu près autant au Front. Les chances sont sous la roue")
    if 'Roue du Front : 30 tours' not in t:
        jour = os.environ.get('JOUR_LOT') or datetime.date.today().isoformat()
        L = json.loads(t)
        ancre = f'"date": "{jour}",\n    "nouveautes": [\n'
        if L and L[0].get('date') == jour and t.count(ancre) == 1:
            t = t.replace(ancre, ancre + '      ' + json.dumps(ligne, ensure_ascii=False) + ',\n', 1)
        else:
            assert t.startswith('[\n'), 'nouveautes.json : début inattendu'
            t = '[\n  {\n    "date": "' + jour + '",\n    "nouveautes": [\n      ' + json.dumps(ligne, ensure_ascii=False) + '\n    ]\n  },\n' + t[2:]
        json.loads(t)
        N.write_text(t, encoding='utf-8')
print('patch351 appliqué')
