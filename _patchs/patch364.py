# patch364 (6/11/2026) : la Banque devient une épargne (s2-110, décision de Nataël).
#
# Avant : la Banque ne recevait que le surplus des Fonderies (6 Banques prêtes,
# 0 lingot dedans). Maintenant, dans Défendre › Bâtiments :
#   - « Déposer » 5 / 10 / tout (jusqu'à 60), « Retirer » 5 / 10 / tout ;
#   - +10 % par nuit sur le contenu (affiché : « +X cette nuit ») ;
#   - à l'abri du pillage des Fonderies, toujours secrète, pillée de moitié si
#     on prend sa commune, 20 à 40 % détruits par une bombe.
# Textes mis à jour : fiche de la Banque, bouton de construction, bulle de la
# légende, règles, cloche. Sans s2-110 (réglage « epargne » absent), le jeu
# garde l'ancien affichage.
import json, pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch364' not in s, 'patch364 déjà appliqué'

# --- l'état « épargne »
s = rep(s, "const bqReglage = (cle, defaut) => (BATIMENTS && BATIMENTS.banque_reglages && BATIMENTS.banque_reglages[cle] != null) ? BATIMENTS.banque_reglages[cle] : defaut;",
"""const bqReglage = (cle, defaut) => (BATIMENTS && BATIMENTS.banque_reglages && BATIMENTS.banque_reglages[cle] != null) ? BATIMENTS.banque_reglages[cle] : defaut;
// patch364 : la Banque épargne (s2-110)
const bqEpargne = () => !!bqReglage('epargne', false);
const bqInteretNuit = (contenu) => { const res = Number(bqReglage('reserve', 60)) || 60, c = Number(contenu) || 0; return Math.max(0, Math.floor(Math.min(res, c * (1 + (Number(bqReglage('interet', 10)) || 10) / 100))) - Math.floor(c)); };
let bqEnVol = false;
async function banqueMouvement(sens, n){
  if(bqEnVol || !(n > 0)) return;
  bqEnVol = true;
  try{
    const { data, error } = await sb.rpc(sens === 'depot' ? 'banque_deposer' : 'banque_retirer', { p_lingots: n });
    if(error) notifier({ type: 'erreur', titre: 'Banque', texte: messageLisible(error.message) });
    else notifier({ type: 'succes', titre: sens === 'depot' ? `${n} lingot${n > 1 ? 's' : ''} déposé${n > 1 ? 's' : ''}` : `${n} lingot${n > 1 ? 's' : ''} retiré${n > 1 ? 's' : ''}`,
                    texte: `Banque : ${Number(data && data.contenu) || 0} / ${bqReglage('reserve', 60)}. En poche : ${Number(data && data.lingots) || 0}.` });
  } finally { bqEnVol = false; }
  await chargerBatiments();
}
function banqueGestionHtml(){
  const B = BATIMENTS; if(!B || !B.banque || !bqEpargne()) return '';
  const bq = B.banque, pret = btPretDans(bq) <= 0;
  const res = Number(bqReglage('reserve', 60)) || 60, dedans = Math.min(res, Number(bq.contenu) || 0);
  const poche = Math.floor(lingotsActuels()), place = Math.max(0, res - dedans);
  const nuit = bqInteretNuit(dedans);
  const bouton = (sens, n, txt) => `<button type="button" class="bq-b ${sens}" data-bq="${sens}" data-bq-n="${n}" ${n > 0 && !bqEnVol ? '' : 'disabled'}>${txt}</button>`;
  return `<div class="bq-bloc">
    <div class="bq-haut"><span class="btl-ic">${ICONE_BANQUE}</span>
      <span class="bq-t"><button type="button" class="btl-nom" data-voir-carte="${echapperTexte(bq.code)}">${echapperTexte(bq.nom)} (${echapperTexte(bq.dept)})</button><small>Secrète · ${pret ? `${bqReglage('interet', 10)} % par nuit` : 'prête dans ' + formatDuree(btPretDans(bq))}</small></span>
      <span class="bq-nb"><b>${dedans}</b> / ${res} ${ICONE_LINGOT}</span></div>
    ${pret ? `<div class="bq-barre"><i style="width:${Math.round(100 * dedans / res)}%"></i></div>
    <p class="bq-nuit">${dedans ? (nuit ? `<b>+${nuit}</b> cette nuit` : 'Moins de 10 lingots : l’intérêt s’accumule, il apparaîtra en lingots entiers.') : 'Dépose des lingots : ils rapportent ' + bqReglage('interet', 10) + ' % chaque nuit.'}</p>
    <div class="bq-ligne"><span>Déposer</span>${bouton('depot', Math.min(5, poche, place), '5')}${bouton('depot', Math.min(10, poche, place), '10')}${bouton('depot', Math.min(poche, place), `Tout (${Math.min(poche, place)})`)}</div>
    <div class="bq-ligne"><span>Retirer</span>${bouton('retrait', Math.min(5, dedans), '5')}${bouton('retrait', Math.min(10, dedans), '10')}${bouton('retrait', dedans, `Tout (${dedans})`)}</div>` : ''}
  </div>`;
}""")

# --- Défendre : la ligne « dans tes Fonderies / dans la Banque » disparaît avec l'épargne
s = rep(s, "    ${B.banque && btPretDans(B.banque) <= 0 ? `<div class=\"bt-split\">",
           "    ${B.banque && btPretDans(B.banque) <= 0 && !bqEpargne() ? `<div class=\"bt-split\">")
# --- Défendre : la Banque avec ses boutons
s = rep(s, "    ${B.banques_ouvertes ? `<div class=\"btl-titre\">Banque <em>${B.banque ? 1 : 0} / 1</em></div>${B.banque\n      ? `<div class=\"btl banque\">",
           "    ${B.banques_ouvertes ? `<div class=\"btl-titre\">Banque <em>${B.banque ? 1 : 0} / 1</em></div>${B.banque && bqEpargne() ? banqueGestionHtml() : B.banque   /* patch364 */\n      ? `<div class=\"btl banque\">")
s = rep(s, "      : `<p class=\"gl-vide\">${bqReglage('prix', 20)} lingots, une Fonderie demandée : +${bqReglage('reserve', 60)} lingots de réserve, à l’abri du pillage des Fonderies.",
           "      : `<p class=\"gl-vide\">${bqReglage('prix', 20)} lingots, une Fonderie demandée : ${bqEpargne() ? `une épargne jusqu’à ${bqReglage('reserve', 60)} lingots, +${bqReglage('interet', 10)} % par nuit, à l’abri du pillage des Fonderies` : `+${bqReglage('reserve', 60)} lingots de réserve, à l’abri du pillage des Fonderies`}.")
s = rep(s, "${B.banque ? ' Une Fonderie prise ne pille que les lingots des Fonderies : ceux de la Banque sont à l’abri, sauf si on prend sa commune ou qu’une bombe tombe dessus.' : ''}</p>`;",
           "${B.banque ? (bqEpargne() ? ' Les lingots déposés dans la Banque ne se dépensent pas : retire-les d’abord. Ils sont à l’abri du pillage des Fonderies, sauf si on prend la commune de la Banque (l’attaquant en pille la moitié) ou qu’une bombe tombe dessus.' : ' Une Fonderie prise ne pille que les lingots des Fonderies : ceux de la Banque sont à l’abri, sauf si on prend sa commune ou qu’une bombe tombe dessus.') : ''}</p>`;")
# --- les clics
s = rep(s, "      if(e.target.closest('[data-bt-mallette]')){ ouvrirMallette(); return; }\n      const fo = e.target.closest('[data-bt-fortifier]');",
           "      if(e.target.closest('[data-bt-mallette]')){ ouvrirMallette(); return; }\n"
           "      const bqb = e.target.closest('[data-bq]');   // patch364 : déposer, retirer\n"
           "      if(bqb){ bqb.disabled = true; banqueMouvement(bqb.dataset.bq, Number(bqb.dataset.bqN) || 0); return; }\n"
           "      const fo = e.target.closest('[data-bt-fortifier]');")

# --- la fiche de la commune de la Banque
s = rep(s, "      <p class=\"bt-txt\">Ce qui dépasse la réserve de tes Fonderies (${Number(B.max_fonderies) || 30}) est rangé ici : <b>tu peux garder jusqu’à ${(Number(B.max_fonderies) || 30) + res} lingots</b>. Secrète : les autres ne la voient pas sur la carte.",
           "      <p class=\"bt-txt\">${bqEpargne() ? `Ton épargne : dépose des lingots dans Défendre, ils rapportent <b>${bqReglage('interet', 10)} % par nuit</b> (jusqu’à ${res}). Pour les dépenser, retire-les. Secrète : les autres ne la voient pas sur la carte.` : `Ce qui dépasse la réserve de tes Fonderies (${Number(B.max_fonderies) || 30}) est rangé ici : <b>tu peux garder jusqu’à ${(Number(B.max_fonderies) || 30) + res} lingots</b>. Secrète : les autres ne la voient pas sur la carte.`}")
# --- le bouton de construction
s = rep(s, "· une seule · <b class=\"bt-plus\">+${bqReglage('reserve', 60)} lingots de réserve</b> · secrète",
           "· une seule · <b class=\"bt-plus\">${bqEpargne() ? `épargne jusqu’à ${bqReglage('reserve', 60)}, +${bqReglage('interet', 10)} % par nuit` : `+${bqReglage('reserve', 60)} lingots de réserve`}</b> · secrète")
# --- la bulle de la légende
s = rep(s, "  banque: { titre: 'Banque', role: 'Elle met tes lingots à l’abri, en plus de la réserve de tes Fonderies.',   // patch356\n"
           "    li: ['Coûte <b>20 lingots</b>, une seule par joueur, il faut une Fonderie.', '<b>+60 lingots</b> de réserve, à l’abri du pillage des Fonderies.',",
           "  banque: { titre: 'Banque', role: 'Ton épargne : tu y déposes des lingots, ils rapportent chaque nuit.',   // patch356, patch364\n"
           "    li: ['Coûte <b>20 lingots</b>, une seule par joueur, il faut une Fonderie.', 'Dépose jusqu’à <b>60 lingots</b> : <b>+10 % par nuit</b>, à l’abri du pillage des Fonderies. Retire-les pour les dépenser.',")
F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch364' not in c
c += """
/* patch364 : la Banque épargne (Défendre) */
.bq-bloc{ padding:10px 12px; border-radius:12px; background:rgba(240,180,41,.06); border:1px solid rgba(240,180,41,.28); display:flex; flex-direction:column; gap:8px; }
.bq-haut{ display:flex; align-items:center; gap:10px; }
.bq-t{ flex:1; min-width:0; display:flex; flex-direction:column; }
.bq-t small{ color: var(--brume); font-size:.78rem; }
.bq-nb{ white-space:nowrap; font-size:.9rem; color: var(--brume); display:flex; align-items:center; gap:4px; }
.bq-nb b{ color:#fff; font-size:1.15rem; }
.bq-nb svg{ width:16px; height:16px; }
.bq-barre{ height:8px; border-radius:4px; background:rgba(169,188,212,.16); overflow:hidden; }
.bq-barre i{ display:block; height:100%; background:linear-gradient(90deg,#C98A12,#F0B429); border-radius:4px; }
.bq-nuit{ margin:0; font-size:.82rem; color: var(--brume); }
.bq-nuit b{ color:#7FE3B4; }
.bq-ligne{ display:grid; grid-template-columns: 64px repeat(3, minmax(0,1fr)); gap:6px; align-items:center; font-size:.84rem; color: var(--brume); }
.bq-b{ height:40px; border-radius:10px; font: inherit; font-weight:700; font-size:.88rem; cursor:pointer; border:1px solid rgba(169,188,212,.25); background:rgba(31,56,96,.8); color:#fff; }
.bq-b.depot{ border-color:rgba(240,180,41,.55); color:#F0B429; }
.bq-b:disabled{ opacity:.4; cursor:default; }
"""
C.write_text(c, encoding='utf-8')

H = pathlib.Path('index.html'); h = H.read_text(encoding='utf-8')
h = rep(h, "Elle ajoute <b>60 lingots</b> de réserve : ce qui dépasse la réserve de tes Fonderies y est rangé, à l'abri du pillage des Fonderies.",
           "C'est ton <b>épargne</b> : tu y déposes jusqu'à <b>60 lingots</b>, qui rapportent <b>10 % par nuit</b> et sont à l'abri du pillage des Fonderies. Pour les dépenser, retire-les (Défendre › Bâtiments).")
h = rep(h, "<!-- patch354 -->", "<!-- patch354, patch364 -->", 1) if h.count("<!-- patch354 -->") == 1 else h
H.write_text(h, encoding='utf-8')

N = pathlib.Path('data/nouveautes.json'); raw = N.read_text(encoding='utf-8'); d = json.loads(raw)
e = d[0] if isinstance(d, list) else None
assert e and e.get('date') == '2026-11-06', 'entrée du 6/11 attendue en tête'
cle = 'nouveautes' if 'nouveautes' in e else None
assert cle, list(e.keys())
i = [k for k, x in enumerate(e[cle]) if x.startswith('🏦')]
assert len(i) == 1, i
e[cle][i[0]] = ("🏦 La Banque devient une épargne : dépose tes lingots (jusqu'à 60), ils rapportent 10 % chaque nuit, à l'abri du pillage des Fonderies. Retire-les pour les dépenser (Défendre › Bâtiments). Elle se construit sur une de tes communes (20 lingots, une Fonderie demandée) et reste secrète")
N.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch364 appliqué')
