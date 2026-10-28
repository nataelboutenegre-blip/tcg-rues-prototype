# patch259 : une 2e Fonderie (avec s2-58)
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')

# la production : toutes les Fonderies prêtes
s = rep(s, """function lingotsActuels(){
  const B = BATIMENTS;
  if(!B) return 0;
  const n = Number(B.lingots) || 0, max = Number(B.max) || 30, prod = Number(B.production) || 10;
  if(!B.fonderie || !B.fonderie.pret || n >= max || B.prochain_dans == null) return n;""",
"""// patch259 : la production de toutes les Fonderies prêtes, et la liste des Fonderies
const mesFonderies = () => (BATIMENTS && (BATIMENTS.fonderies || (BATIMENTS.fonderie ? [BATIMENTS.fonderie] : []))) || [];
function btProdTotale(){
  const B = BATIMENTS;
  if(!B) return 0;
  if(B.production_totale != null) return Number(B.production_totale) || 0;
  return B.fonderie && B.fonderie.pret ? Number(B.production) || 10 : 0;
}
function lingotsActuels(){
  const B = BATIMENTS;
  if(!B) return 0;
  const n = Number(B.lingots) || 0, max = Number(B.max) || 30, prod = btProdTotale();
  if(!prod || n >= max || B.prochain_dans == null) return n;""")
s = rep(s, """  if(!B || !B.fonderie || !B.fonderie.pret || B.prochain_dans == null) return null;
  if(lingotsActuels() >= (Number(B.max) || 30)) return null;
  const pas = 86400 / (Number(B.production) || 10);""",
"""  if(!B || !btProdTotale() || B.prochain_dans == null) return null;
  if(lingotsActuels() >= (Number(B.max) || 30)) return null;
  const pas = 86400 / btProdTotale();""")

# la fiche : la Fonderie d'ici
s = rep(s, "  const ici = B.fonderie && B.fonderie.code === code ? B.fonderie : null;",
           "  const ici = mesFonderies().find(x => x.code === code) || null;   // patch259")
s = rep(s, """      <p class="bt-txt">${prete ? `<b>+${B.production} lingots par jour</b>, jusqu’à ${max} en réserve${pr ? ` · prochain dans ${formatDuree(pr)}` : ''}.` : `<b>En construction</b> : prête dans ${formatDuree(btPretDans(ici))}.`}
        Visible de tous : si on te prend ${echapperHtml(c.nom)}, la Fonderie est détruite et l’attaquant pille ${btReglage('pillage', 50)} % de ta réserve.</p>""",
"""      <p class="bt-txt">${prete ? `<b>+${B.production} lingots par jour</b>${mesFonderies().length > 1 ? ' (réserve partagée avec ton autre Fonderie)' : ''}, jusqu’à ${max} en réserve${pr ? ` · prochain dans ${formatDuree(pr)}` : ''}.` : `<b>En construction</b> : prête dans ${formatDuree(btPretDans(ici))}.`}
        Visible de tous : si on te prend ${echapperHtml(c.nom)}, la Fonderie est détruite et l’attaquant pille ${Math.round(btReglage('pillage', 50) / Math.max(1, mesFonderies().length))} % de ta réserve.</p>""")

# la fiche : construire la 1re ou la 2e Fonderie
s = rep(s, """  if(!B.fonderie){
    boutons.push(`<button class="pc-action bt-action${arme('fonderie') ? ' arme' : ''}" data-pc="bt-construire" data-bt="fonderie">${ICONE_FONDERIE}<span>${arme('fonderie') ? `Confirmer : la Fonderie à ${echapperHtml(c.nom)}` : 'Construire la Fonderie ici'}<small>Une seule · prête dans ${h} h · ${B.production} lingots par jour</small></span><span class="prix">gratuit</span></button>`);
  }""",
"""  const nF = mesFonderies().length, maxNF = btReglage('fonderies_max', 1);
  if(!nF){
    boutons.push(`<button class="pc-action bt-action${arme('fonderie') ? ' arme' : ''}" data-pc="bt-construire" data-bt="fonderie">${ICONE_FONDERIE}<span>${arme('fonderie') ? `Confirmer : la Fonderie à ${echapperHtml(c.nom)}` : 'Construire la Fonderie ici'}<small>Prête dans ${h} h · ${B.production} lingots par jour</small></span><span class="prix">gratuit</span></button>`);
  } else if(nF < maxNF && !mesFonderies().some(x => x.code === code)){   // patch259 : la 2e Fonderie
    const p2 = btReglage('fonderie2_prix', 30), n = lingotsActuels();
    const bloque = n < p2 ? `Il te faut ${p2} lingots (tu en as ${n})` : '';
    boutons.push(`<button class="pc-action bt-action${arme('fonderie') ? ' arme' : ''}" data-pc="bt-construire" data-bt="fonderie" ${bloque ? 'disabled' : ''}>${ICONE_FONDERIE}<span>${arme('fonderie') ? `Confirmer : ${p2} lingots` : 'Construire une 2e Fonderie ici'}<small>${bloque || `Prête dans ${h} h · +${B.production} lingots par jour · réserve jusqu’à ${btReglage('fonderie_max2', 45)}`}</small></span><span class="prix">${p2} ${ICONE_LINGOT}</span></button>`);
  }""")

# Défendre : les Fonderies
s = rep(s, """      <span class="btr-prod">${F ? (btPretDans(F) <= 0 ? `+${B.production} par jour<br>${pr ? 'prochain dans ' + formatDuree(pr) : 'réserve pleine'}` : 'Fonderie<br>en construction') : 'Pas encore<br>de Fonderie'}</span></div>
    <div class="btl-titre">Fonderie</div>
    ${F ? ligne(ICONE_FONDERIE, F, btPretDans(F) <= 0 ? `Produit ${B.production} lingots par jour` : 'En construction')
        : '<p class="gl-vide">Ouvre une de tes communes sur la carte et choisis « Construire la Fonderie ici ». Elle est gratuite, mais visible de tous : choisis bien l’endroit.</p>'}""",
"""      <span class="btr-prod">${F ? (btProdTotale() > 0 ? `+${btProdTotale()} par jour<br>${pr ? 'prochain dans ' + formatDuree(pr) : 'réserve pleine'}` : 'Fonderie<br>en construction') : 'Pas encore<br>de Fonderie'}</span></div>
    <div class="btl-titre">Fonderies <em>${mesFonderies().length} / ${btReglage('fonderies_max', 1)}</em></div>
    ${F ? mesFonderies().map(x => ligne(ICONE_FONDERIE, x, btPretDans(x) <= 0 ? `Produit ${B.production} lingots par jour` : 'En construction')).join('')
        + (mesFonderies().length < btReglage('fonderies_max', 1) ? `<p class="gl-vide">2e Fonderie : ${btReglage('fonderie2_prix', 30)} lingots. Ouvre une de tes communes sur la carte et choisis « Construire une 2e Fonderie ici ». La réserve monte alors à ${btReglage('fonderie_max2', 45)}.</p>` : '')
        : '<p class="gl-vide">Ouvre une de tes communes sur la carte et choisis « Construire la Fonderie ici ». Elle est gratuite, mais visible de tous : choisis bien l’endroit.</p>'}""")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
s = rep(s, "construis ta <b>Fonderie</b> (gratuite, une seule) : elle produit <b>10 lingots par jour</b>, 30 en réserve.",
           "construis ta <b>Fonderie</b> (gratuite) : elle produit <b>10 lingots par jour</b>, 30 en réserve. Une <b>2e Fonderie</b> coûte 30 lingots : 10 lingots de plus par jour, réserve jusqu'à 45.")
s = rep(s, "prendre une Fonderie pille la moitié des lingots de son propriétaire.",
           "prendre une Fonderie pille la moitié des lingots de son propriétaire (le quart s'il en a deux).")
f.write_text(s, encoding='utf-8')
print('patch259 ok')
