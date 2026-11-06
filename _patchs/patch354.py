# patch354 (6/11/2026) : la Banque (s2-104) et la 4e part du classement, « bâtiments » (s2-105).
# Aperçus validés par Nataël le 6/11 (apercu-banque.png, apercu-score.png).
# À appliquer APRÈS les patchs du lot du 6/11 (lot-jeu-1 à 5) et patch350.
#
# Banque :
#   - icône et tracé sur la carte (seul son propriétaire la voit : le serveur la cache aux autres) ;
#   - fiche d'une commune : « Construire la Banque ici » (20 lingots, une Fonderie, une seule) et,
#     une fois construite, son encadré vert avec son contenu ;
#   - Défendre : réserve « x / 105 » avec le détail Fonderies / Banque, section Banque ;
#   - la jauge de la Fonderie s'arrête à la réserve des Fonderies ;
#   - alertes de bombe : ce que la Banque a perdu.
# Classement : 4e couleur orange « bâtiments » (barre, légende, « Comment c'est calculé ? »).
# Règles, cloche du 6/11.
import pathlib, json

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:80]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch354' not in s, 'patch354 déjà appliqué'
assert 'garnisonsMax()' in s, 'appliquer d’abord les patchs du lot du 6/11'

# ---------- icône et tracé ----------
s = rep(s, "if(BT_TRACES) BT_TRACES.centre = [new Path2D('M9.5 3h5M10.5 3v6.5L5 19.2c-.5 1 .2 1.8 1.2 1.8h11.6c1 0 1.7-.8 1.2-1.8l-5.5-9.7V3M7.6 15h8.8')];\n",
"if(BT_TRACES) BT_TRACES.centre = [new Path2D('M9.5 3h5M10.5 3v6.5L5 19.2c-.5 1 .2 1.8 1.2 1.8h11.6c1 0 1.7-.8 1.2-1.8l-5.5-9.7V3M7.6 15h8.8')];\n"
"// patch354 : la Banque (un coffre)\n"
"const ICONE_BANQUE = '<svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><rect x=\"3.5\" y=\"4.5\" width=\"17\" height=\"14\" rx=\"2\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.8\"/><circle cx=\"12\" cy=\"11.5\" r=\"3.4\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.8\"/><path d=\"M12 8.1v1.4M12 13.5v1.4M8.6 11.5H10M14 11.5h1.4M6.5 18.5v1.5M17.5 18.5v1.5\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\"/></svg>';\n"
"if(BT_TRACES) BT_TRACES.banque = [new Path2D('M5.5 4.5h13a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2v-10a2 2 0 0 1 2-2zM15.4 11.5a3.4 3.4 0 1 1-6.8 0a3.4 3.4 0 1 1 6.8 0M6.5 18.5v1.5M17.5 18.5v1.5')];\n"
"const bqReglage = (cle, defaut) => (BATIMENTS && BATIMENTS.banque_reglages && BATIMENTS.banque_reglages[cle] != null) ? BATIMENTS.banque_reglages[cle] : defaut;\n")

s = rep(s, "    const types = ['fonderie', 'forteresse', 'centre'].filter(t => bt[t]);   // patch260",
           "    const types = ['fonderie', 'forteresse', 'centre', 'banque'].filter(t => bt[t] && BT_TRACES[t]);   // patch260, patch354")
s = rep(s, "  if(bt && ['fonderie', 'forteresse', 'centre'].some(t => bt[t])) return 'batiment';",
           "  if(bt && ['fonderie', 'forteresse', 'centre', 'banque'].some(t => bt[t])) return 'batiment';   // patch354")

# ---------- noms, prix ----------
s = rep(s, "  if(type === 'centre') return Number(btReglage('centre_prix', 40)) || 0;\n",
           "  if(type === 'centre') return Number(btReglage('centre_prix', 40)) || 0;\n"
           "  if(type === 'banque') return Number(bqReglage('prix', 20)) || 0;   // patch354\n")
s = rep(s, "const btNom = (type) => type === 'fonderie' ? 'Fonderie' : type === 'centre' ? 'Centre de recherche' : 'Forteresse';",
           "const btNom = (type) => type === 'fonderie' ? 'Fonderie' : type === 'centre' ? 'Centre de recherche' : type === 'banque' ? 'Banque' : 'Forteresse';   // patch354")
s = rep(s, "  const nom = type === 'fonderie' ? 'Fonderie' : type === 'centre' ? 'Centre de recherche' : 'Forteresse';   // patch260",
           "  const nom = btNom(type);   // patch260, patch354")

# ---------- fiche d'une commune : ce qui est construit ----------
s = rep(s, "  if(ici){\n    const n = lingotsActuels(), max = Number(B.max) || 30;",
           "  if(ici){\n    const max = Number(B.max_fonderies || B.max) || 30, n = Math.min(lingotsActuels(), max);   // patch354 : la part des Fonderies")
s = rep(s, "Visible de tous : si on te prend ${echapperHtml(c.nom)}, la Fonderie est détruite et l’attaquant pille ${Math.round(btReglage('pillage', 50) / Math.max(1, mesFonderies().length))} % de ta réserve.</p>",
           "Visible de tous : si on te prend ${echapperHtml(c.nom)}, la Fonderie est détruite et l’attaquant pille ${Math.round(btReglage('pillage', 50) / Math.max(1, mesFonderies().length))} % de ta réserve${B.banque ? ' (pas ce qui est dans ta Banque)' : ''}.</p>")
s = rep(s, "      ${pret ? '' : btAnnulerHtml(code, 'centre')}\n    </div>`;\n  }\n  return html;\n}",
"""      ${pret ? '' : btAnnulerHtml(code, 'centre')}
    </div>`;
  }
  const bq = B.banque && B.banque.code === code ? B.banque : null;   // patch354 : la Banque
  if(bq){
    const pret = btPretDans(bq) <= 0, res = Number(bqReglage('reserve', 60)) || 60, dedans = Math.min(res, Number(bq.contenu) || 0);
    html += `<div class="bt bt-banque">
      <div class="bt-haut">${ICONE_BANQUE}Banque <b>${pret ? `${dedans} / ${res} ${ICONE_LINGOT}` : 'prête dans ' + formatDuree(btPretDans(bq))}</b></div>
      ${pret ? `<div class="bt-barre" style="grid-template-columns:repeat(${res},1fr)">${Array.from({ length: res }, (_, i) => `<i class="${i < dedans ? 'b' : ''}"></i>`).join('')}</div>` : ''}
      <p class="bt-txt">Ce qui dépasse la réserve de tes Fonderies (${Number(B.max_fonderies) || 30}) est rangé ici : <b>tu peux garder jusqu’à ${(Number(B.max_fonderies) || 30) + res} lingots</b>. Secrète : les autres ne la voient pas sur la carte.
        Si on te prend ${echapperHtml(c.nom)}, elle est détruite et l’attaquant pille <b>la moitié de son contenu</b>. Une bombe qui tombe sur la zone en détruit ${(bqReglage('bombe', [20, 30, 40]) || [20])[0]} à ${(bqReglage('bombe', [20, 30, 40]) || [40]).slice(-1)[0]} %.</p>
      ${pret ? '' : btAnnulerHtml(code, 'banque')}
    </div>`;
  }
  return html;
}""")

# ---------- fiche d'une commune : construire la Banque ----------
s = rep(s, "  return boutons.length ? `<p class=\"pc-titre-bt\">Bâtiments</p>",
"""  if(B.banques_ouvertes && !B.banque){   // patch354 : la Banque
    const pb = bqReglage('prix', 20), nl = lingotsActuels();
    const bloque = !nF ? 'Il te faut d’abord une Fonderie' : nl < pb ? `Il te faut ${pb} lingots (tu en as ${nl})` : '';
    boutons.push(`<button class="pc-action bt-action${arme('banque') ? ' arme' : ''}" data-pc="bt-construire" data-bt="banque" ${bloque ? 'disabled' : ''}>${ICONE_BANQUE}<span>${arme('banque') ? `Confirmer : ${pb} lingots` : 'Construire la Banque ici'}<small>${bloque || `Prête dans ${h} h · une seule · <b class="bt-plus">+${bqReglage('reserve', 60)} lingots de réserve</b> · secrète : les autres ne la voient pas sur la carte`}</small></span><span class="prix">${pb} ${ICONE_LINGOT}</span></button>`);
  }
  return boutons.length ? `<p class="pc-titre-bt">Bâtiments</p>""")

# ---------- Défendre ----------
s = rep(s, "    ${lingotsCombatHtml()}\n    <div class=\"btl-titre\">Fonderies",
"""    ${B.banque && btPretDans(B.banque) <= 0 ? `<div class="bt-split"><span><i class="pt f"></i>${Math.min(n, Number(B.max_fonderies) || 30)} / ${Number(B.max_fonderies) || 30} dans tes Fonderies</span><span><i class="pt b"></i>${Math.max(0, n - (Number(B.max_fonderies) || 30))} / ${bqReglage('reserve', 60)} à l’abri dans la Banque</span></div>` : ''}
    ${lingotsCombatHtml()}
    <div class="btl-titre">Fonderies""")
s = rep(s, "    ${centreHtml()}\n    <p class=\"btl-regle\">",
"""    ${centreHtml()}
    ${B.banques_ouvertes ? `<div class="btl-titre">Banque <em>${B.banque ? 1 : 0} / 1</em></div>${B.banque
      ? `<div class="btl banque"><span class="btl-ic">${ICONE_BANQUE}</span><span class="btl-t"><button type="button" class="btl-nom" data-voir-carte="${echapperTexte(B.banque.code)}">${echapperTexte(B.banque.nom)} (${echapperTexte(B.banque.dept)})</button><small>${btPretDans(B.banque) <= 0 ? `${Math.min(Number(bqReglage('reserve', 60)), Number(B.banque.contenu) || 0)} / ${bqReglage('reserve', 60)} lingots à l’abri · secrète` : 'En construction · secrète'}</small></span>${btPretDans(B.banque) <= 0 ? '<span class="btl-etat ok">Active</span>' : `<span class="btl-etat cours">prête dans ${formatDuree(btPretDans(B.banque))}</span>`}</div>`
      : `<p class="gl-vide">${bqReglage('prix', 20)} lingots, une Fonderie demandée : +${bqReglage('reserve', 60)} lingots de réserve, à l’abri du pillage des Fonderies. Ouvre une de tes communes sur la carte et choisis « Construire la Banque ici ». Elle est secrète.</p>`}` : ''}
    <p class="btl-regle">""")
s = rep(s, " ne s’échangent pas, ne s’achètent pas et repartent à zéro à chaque saison. Un bâtiment est perdu si on prend sa commune.</p>`;",
           " ne s’échangent pas, ne s’achètent pas et repartent à zéro à chaque saison. Un bâtiment est perdu si on prend sa commune.${B.banque ? ' Une Fonderie prise ne pille que les lingots des Fonderies : ceux de la Banque sont à l’abri, sauf si on prend sa commune ou qu’une bombe tombe dessus.' : ''}</p>`;")

# ---------- alertes de bombe ----------
s = rep(s, "      ${a.garnisons} garnison${a.garnisons > 1 ? 's' : ''} et ${a.forteresses} forteresse${a.forteresses > 1 ? 's' : ''} soufflée${a.garnisons + a.forteresses > 1 ? 's' : ''}${perte ? ` <em>dont ${[a.mes_garnisons ? a.mes_garnisons + ' garnison' + (a.mes_garnisons > 1 ? 's' : '') : '', a.mes_forteresses ? a.mes_forteresses + ' forteresse' + (a.mes_forteresses > 1 ? 's' : '') : ''].filter(Boolean).join(' et ')} à toi</em>` : ''}.",
           "      ${a.garnisons} garnison${a.garnisons > 1 ? 's' : ''} et ${a.forteresses} forteresse${a.forteresses > 1 ? 's' : ''} soufflée${a.garnisons + a.forteresses > 1 ? 's' : ''}${perte ? ` <em>dont ${[a.mes_garnisons ? a.mes_garnisons + ' garnison' + (a.mes_garnisons > 1 ? 's' : '') : '', a.mes_forteresses ? a.mes_forteresses + ' forteresse' + (a.mes_forteresses > 1 ? 's' : '') : ''].filter(Boolean).join(' et ')} à toi</em>` : ''}.${a.mes_banque ? ` <em>Ta Banque a perdu ${a.mes_banque} lingot${a.mes_banque > 1 ? 's' : ''}.</em>` : ''}")   # patch354

# ---------- classement : 4e part ----------
s = rep(s, "  return `<span class=\"sc-barre\" title=\"cartes ${nb(d.cartes)} · combats ${nb(d.combats)} · territoires ${nb(d.territoires)}\">`\n    + part(d.cartes, 'c') + part(d.combats, 'co') + part(d.territoires, 't') + '</span>';",
           "  return `<span class=\"sc-barre\" title=\"cartes ${nb(d.cartes)} · combats ${nb(d.combats)} · territoires ${nb(d.territoires)} · bâtiments ${nb(d.batiments)}\">`\n    + part(d.cartes, 'c') + part(d.combats, 'co') + part(d.territoires, 't') + part(d.batiments, 'b') + '</span>';   // patch354")
s = rep(s, "  <p class=\"cl-calc-pied\">Cartes et territoires se comptent en direct : perdre une commune fait baisser ton score. Les combats restent acquis.</p>`;",
"""  <div class="cl-calc-l"><i class="sc-pt b"></i><div><b>Bâtiments</b><span>Chaque bâtiment terminé : Fonderie <b>+50</b> · Forteresse <b>+80</b> · Centre de recherche <b>+150</b> · Banque <b>+80</b>. Acquis même s’il est détruit, jusqu’au maximum de chaque type (2 Fonderies, 5 Forteresses, 1 Centre, 1 Banque : <b>730</b> au plus).<br>Bombe lancée <b>+300</b>. Rébellion financée ou étouffée : <b>+2</b> par lingot, 60 par jour au plus.</span></div></div>
  <p class="cl-calc-pied">Cartes et territoires se comptent en direct : perdre une commune fait baisser ton score. Les combats et les bâtiments restent acquis.</p>`;   // patch354""")
s = rep(s, "    : '<i class=\"sc-pt c\"></i>cartes <i class=\"sc-pt co\"></i>combats <i class=\"sc-pt t\"></i>territoires') + bouton;",
           "    : '<i class=\"sc-pt c\"></i>cartes <i class=\"sc-pt co\"></i>combats <i class=\"sc-pt t\"></i>territoires <i class=\"sc-pt b\"></i>bâtiments') + bouton;   // patch354")
F.write_text(s, encoding='utf-8')

# ---------- styles ----------
C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch354' not in c
c += """
/* patch354 : la Banque (vert) et la part « bâtiments » du classement (orange) */
.sc-pt.b, .sc-barre .b{ background:#E8833A; }
.bt.bt-banque{ background:linear-gradient(160deg,rgba(63,191,133,.16),rgba(63,191,133,.04)); border-color:rgba(63,191,133,.45); }
.bt.bt-banque .bt-haut{ color:#7FE0B0; }
.bt-barre i.b{ background:linear-gradient(180deg,#B8F0D2,#3FBF85); }
.btl.banque .btl-ic{ background:rgba(63,191,133,.16); color:#7FE0B0; }
.pc-action.bt-action small .bt-plus{ color:#FFE08A; font-weight:600; }
.bt-split{ display:flex; flex-direction:column; gap:4px; margin:8px 2px 0; font-size:.76rem; color:#D6C2B2; }
.bt-split .pt{ display:inline-block; width:9px; height:9px; border-radius:3px; margin-right:6px; vertical-align:-1px; }
.bt-split .pt.f{ background:#F0B429; } .bt-split .pt.b{ background:#3FBF85; }
"""
C.write_text(c, encoding='utf-8')

# ---------- règles ----------
H = pathlib.Path('index.html'); h = H.read_text(encoding='utf-8')
h = rep(h, "            <p><b>Le classement du Front</b> additionne tes cartes, tes victoires et tes territoires :</p>",
           "            <p><b>Le classement du Front</b> additionne tes cartes, tes victoires, tes territoires et tes bâtiments :</p>")
h = rep(h, """                  <tr><td>Région : seul en tête avec 10 % ou plus dans plus de la moitié de ses départements</td><td class="chiffre or">+1 200</td></tr><!-- patch339 -->""",
"""                  <tr><td>Région : seul en tête avec 10 % ou plus dans plus de la moitié de ses départements</td><td class="chiffre or">+1 200</td></tr><!-- patch339 -->
                  <tr><td>Bâtiment terminé, acquis même s'il est détruit, jusqu'au maximum de chaque type : Fonderie · Forteresse · Centre de recherche · Banque</td><td class="chiffre or">+50 · +80 · +150 · +80</td></tr>
                  <tr><td>Bombe lancée</td><td class="chiffre or">+300</td></tr>
                  <tr><td>Rébellion financée ou étouffée, par lingot (60 par jour au plus)</td><td class="chiffre or">+2</td></tr><!-- patch354 -->""")
h = rep(h, " Les lingots ne servent qu'aux bâtiments et repartent à zéro à chaque saison.</p>\n            <p><b>Centre de recherche et bombe</b>",
           " Les lingots ne servent qu'aux bâtiments et repartent à zéro à chaque saison.</p>\n"
           "            <p><b>Banque</b> : avec une Fonderie, construis ta <b>Banque</b> (20 lingots, une seule). Elle ajoute <b>60 lingots</b> de réserve : ce qui dépasse la réserve de tes Fonderies y est rangé, à l'abri du pillage des Fonderies. Elle est <b>secrète</b> : les autres ne la voient pas sur la carte. Si on prend sa commune, elle est détruite et l'attaquant pille la moitié de son contenu ; une bombe qui tombe sur sa zone en détruit 20, 30 ou 40 % selon son niveau.</p><!-- patch354 -->\n"
           "            <p><b>Centre de recherche et bombe</b>")
H.write_text(h, encoding='utf-8')

# ---------- cloche ----------
N = pathlib.Path('data/nouveautes.json')
d = json.loads(N.read_text(encoding='utf-8'))
assert d and d[0].get('date') == '2026-11-06', 'la première entrée n’est pas celle du 6/11 (appliquer d’abord le lot)'
for l in ['🏦 Nouveau bâtiment : la Banque (20 lingots, une Fonderie demandée). +60 lingots de réserve, à l’abri du pillage des Fonderies, et secrète. Mais si on prend sa commune, l’attaquant pille la moitié de son contenu, et une bombe peut en détruire une partie',
          '🏆 Classement du Front : tes bâtiments comptent maintenant (Fonderie +50, Forteresse +80, Centre +150, Banque +80, acquis même s’ils sont détruits, jusqu’au maximum de chaque type), ainsi que tes bombes lancées (+300) et tes rébellions, financées ou étouffées (+2 par lingot, 60 par jour au plus). Détail dans « Comment c’est calculé ? »']:
    if l not in d[0]['nouveautes']: d[0]['nouveautes'].append(l)
N.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch354 appliqué')
