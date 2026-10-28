# patch243 : les bâtiments du Front, étape 1 — Fonderie, lingots, Forteresse (avec s2-48)
# Aperçu validé le 28/10 (« parfait »), forteresse « point d'appui » validée (« c'est parfait oui »).
import pathlib
def ouvrir(n): return pathlib.Path(n), pathlib.Path(n).read_text(encoding='utf-8')
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)

f, s = ouvrir('app.js')

# 1. icônes, état, tracés de la carte : tôt dans le fichier (déclarés avant tout usage)
s = rep(s, "const LIBELLE_TIER = {commun: 'commun', peucommun: 'peu commun', rare: 'rare', epique: 'épique', legendaire: 'légendaire'};\n",
"""const LIBELLE_TIER = {commun: 'commun', peucommun: 'peu commun', rare: 'rare', epique: 'épique', legendaire: 'légendaire'};
// ---------- patch243 : les bâtiments du Front (s2-48) ----------
const ICONE_FONDERIE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round" d="M3 20.5h18M4 20.5V11l5 3V11l5 3V5.5h3.2V20.5M17.2 9.5H20v11"/><path fill="currentColor" d="M15.6 2.2c.9.9 1 1.8.4 2.6-.5-.5-1.3-.6-1.6.1-.5-1 .1-2 1.2-2.7z"/></svg>';
const ICONE_FORTERESSE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" d="M5 21V8h2.4V5h2.4v3h2.4V5h2.4v3h2.4V5H19v16zM10 21v-4.2a2 2 0 0 1 4 0V21"/></svg>';
const ICONE_LINGOT = '<i class="lingot" aria-hidden="true"></i>';
const BT_TRACES = typeof Path2D === 'function' ? {
  fonderie: [new Path2D('M3 20.5h18M4 20.5V11l5 3V11l5 3V5.5h3.2V20.5M17.2 9.5H20v11'), new Path2D('M15.6 2.2c.9.9 1 1.8.4 2.6-.5-.5-1.3-.6-1.6.1-.5-1 .1-2 1.2-2.7z')],
  forteresse: [new Path2D('M5 21V8h2.4V5h2.4v3h2.4V5h2.4v3h2.4V5H19v16zM10 21v-4.2a2 2 0 0 1 4 0V21')],
} : null;
let BATIMENTS = null;              // mes_batiments() ; null = bâtiments fermés ou s2-48 absent
let BATIMENTS_CARTE = new Map();   // code -> { fonderie: { moi, pret }, forteresse: { moi, pret } }
let batimentsLu = 0;
let batimentsTimer = null;
let btArme = null;                 // « code|type » : la construction attend sa confirmation
let btRecherche = '';
let attaqueEffetBt = null;         // batiments_effet() de la cible ouverte
""")

# 2. la carte : les icônes des bâtiments, après les marqueurs de rareté
s = rep(s, "  if(CALQUES.raretes) dessinerMarqueursCanvas(ctx, liste, joueurs, k, mode === 'depts');\n",
           "  if(CALQUES.raretes) dessinerMarqueursCanvas(ctx, liste, joueurs, k, mode === 'depts');\n"
           "  if(SAISON2 && BATIMENTS_CARTE.size) dessinerBatimentsCanvas(ctx, liste);   // patch243\n")

# 3. chargement au démarrage
s = rep(s, "  chargerAuroresFront();   // patch228\n",
           "  chargerAuroresFront();   // patch228\n  chargerBatiments();   // patch243\n")

# 4. la fiche d'une commune
s = rep(s, "  if(SAISON2 && auroreFront(code)) lignes.push(['Carte', '<b class=\"pc-aurore\">✦ Aurore</b>']);   // patch228\n",
"""  if(SAISON2 && auroreFront(code)) lignes.push(['Carte', '<b class="pc-aurore">✦ Aurore</b>']);   // patch228
  if(SAISON2 && !mienne && BATIMENTS){   // patch243 : les bâtiments des autres se voient
    const bt = BATIMENTS_CARTE.get(String(code));
    if(bt){
      const t = [];
      if(bt.fonderie) t.push(bt.fonderie.pret ? 'Fonderie' : 'Fonderie en construction');
      if(bt.forteresse) t.push(bt.forteresse.pret ? 'Forteresse' : 'Forteresse en construction');
      lignes.push(['Bâtiment', t.join(' + ')]);
    }
  }
""")
s = rep(s, "  let gnBloc = '';\n", "  let gnBloc = '', btEtat = '', btActions = '';\n")
s = rep(s, "      gnBloc = blocGarnisonFiche(code);\n",
           "      gnBloc = blocGarnisonFiche(code);\n"
           "      btEtat = blocBatimentsEtat(code, c);   // patch243\n"
           "      btActions = blocBatimentsActions(code, c);\n")
s = rep(s, "    ${alerte}\n    ${gnBloc}\n", "    ${alerte}\n    ${gnBloc}${btEtat}\n")
s = rep(s, """`<button class="pc-action ${cl}" data-pc="${ic}" title="${echapperHtml(titre)}">${ICONES_PC[ic]}${txt}</button>`).join('')}</div>` : ''}`;

  el.hidden = false;""", """`<button class="pc-action ${cl}" data-pc="${ic}" title="${echapperHtml(titre)}">${ICONES_PC[ic]}${txt}</button>`).join('')}</div>` : ''}${btActions}`;

  el.hidden = false;""")

# 5. les clics de la fiche
s = rep(s, "  if(quoi === 'assaut'){ lancerAssaut(code); return; }\n",
"""  if(quoi === 'assaut'){ lancerAssaut(code); return; }
  if(quoi === 'bt-construire'){   // patch243 : deux temps, comme le retrait de garnison
    const t = b.dataset.bt;
    if(btArme !== code + '|' + t){ btArme = code + '|' + t; const a = panneauAncre; ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40); return; }
    btArme = null;
    b.disabled = true;
    batimentConstruire(code, t);
    return;
  }
""")

# 6. le panneau d'attaque : forteresse de la cible, point d'appui
s = rep(s, "  const [apercu, siege, gnv] = await Promise.all([\n", "  const [apercu, siege, gnv, bte] = await Promise.all([\n")
s = rep(s, """    SAISON2 ? sb.rpc('garnisons_visibles', { p_codes: [code] }) : Promise.resolve({ data: [] }),
  ]);
  attaqueEnGarnison = !!(gnv && Array.isArray(gnv.data) && gnv.data.length);
""", """    SAISON2 ? sb.rpc('garnisons_visibles', { p_codes: [code] }) : Promise.resolve({ data: [] }),
    SAISON2 && BATIMENTS ? sb.rpc('batiments_effet', { p_code: code }) : Promise.resolve({ data: [] }),   // patch243
  ]);
  attaqueEnGarnison = !!(gnv && Array.isArray(gnv.data) && gnv.data.length);
  attaqueEffetBt = bte && !bte.error && Array.isArray(bte.data) && bte.data[0] ? bte.data[0] : null;
""")
s = rep(s, "(1 chance sur 2).</span></div>` : ''}\n    <div class=\"pc-prox",
"""(1 chance sur 2).</span></div>` : ''}
    ${attaqueEffetBt && attaqueEffetBt.defense > 0 ? `<div class="gn-badge bt-badge">${ICONE_FORTERESSE}<span><b>Forteresse.</b> −${attaqueEffetBt.defense} % à tes chances sur cette commune.</span></div>` : ''}
    ${attaqueEffetBt && attaqueEffetBt.appui > 0 ? `<p class="bt-appui">${ICONE_FORTERESSE}<span>+${attaqueEffetBt.appui} % grâce à ta forteresse${attaqueEffetBt.appui_de ? ' de <b>' + echapperHtml(attaqueEffetBt.appui_de) + '</b>' : ''}</span></p>` : ''}
    <div class="pc-prox""")

# 7. la conquête d'une Fonderie
s = rep(s, "        + (mon ? `<span class=\"as-mon\">${ICONE_MONUMENT}Monument conquis : <b>${echapperTexte(mon.nom)}</b></span>` : '');\n",
"""        + (mon ? `<span class="as-mon">${ICONE_MONUMENT}Monument conquis : <b>${echapperTexte(mon.nom)}</b></span>` : '')
        + (SAISON2 && (BATIMENTS_CARTE.get(String(cible.code)) || {}).fonderie ? `<span class="as-mon as-bt">${ICONE_FONDERIE}Fonderie détruite : tu pilles la moitié de ses lingots</span>` : '');   // patch243
      if(SAISON2 && BATIMENTS) setTimeout(chargerBatiments, 800);
""")

# 8. la légende de la carte
s = rep(s, "stroke=\"#0B1830\"/></svg>Aurore</div>",
           "stroke=\"#0B1830\"/></svg>Aurore</div>${SAISON2 && BATIMENTS ? `<div><span class=\"leg-bt\">${ICONE_FONDERIE}</span>Fonderie</div><div><span class=\"leg-bt\">${ICONE_FORTERESSE}</span>Forteresse</div>` : ''}")

# 9. Défendre : le bloc Bâtiments, au-dessus des garnisons
s = rep(s, "    if(sect) sect.insertAdjacentElement('beforebegin', g); else defense.appendChild(g);\n",
"""    if(sect) sect.insertAdjacentElement('beforebegin', g); else defense.appendChild(g);
    // patch243 : les bâtiments, au-dessus des garnisons
    const bt = document.createElement('div');
    bt.id = 'batimentsBloc';
    bt.className = 'garnisons-bloc batiments-bloc';
    bt.hidden = true;
    g.insertAdjacentElement('beforebegin', bt);
    bt.addEventListener('click', (e) => {
      const fo = e.target.closest('[data-bt-fortifier]');
      if(!fo) return;
      const code = fo.dataset.btFortifier;
      if(btArme !== code + '|forteresse'){ btArme = code + '|forteresse'; renderBatimentsBloc(); return; }
      btArme = null;
      fo.disabled = true;
      batimentConstruire(code, 'forteresse');
    });
""")
s = rep(s, "  chargerGarnisons();\n}\n\n// ---------- patch91 : garnisons ----------\n",
"""  chargerGarnisons();
  chargerBatiments();   // patch243
  if(!batimentsTimer) batimentsTimer = setInterval(siVisible(chargerBatiments), 120000);
}

// ---------- patch243 : les bâtiments ----------
async function chargerBatiments(){
  if(!SAISON2) return;
  try{
    const [m, v] = await Promise.all([sb.rpc('mes_batiments'), sb.rpc('batiments_visibles')]);
    if(m.error || !m.data || !m.data.ouverts){ BATIMENTS = null; BATIMENTS_CARTE = new Map(); renderBatimentsBloc(); return; }
    BATIMENTS = m.data;
    batimentsLu = Date.now();
    const carte = new Map();
    for(const b of (v.data || [])){
      const k = String(b.commune_code);
      const e = carte.get(k) || {};
      e[b.type] = { moi: b.joueur_id === window.__monId, pret: !!b.pret };
      carte.set(k, e);
    }
    BATIMENTS_CARTE = carte;
    renderBatimentsBloc();
    if(typeof demanderDessin === 'function' && canvasActif()){ CV.donneesSignature = null; demanderDessin(); }
  }catch(e){ console.error('Bâtiments :', e); }
}
// la réserve « maintenant », sans rappeler le serveur
function lingotsActuels(){
  const B = BATIMENTS;
  if(!B) return 0;
  const n = Number(B.lingots) || 0, max = Number(B.max) || 30, prod = Number(B.production) || 10;
  if(!B.fonderie || !B.fonderie.pret || n >= max || B.prochain_dans == null) return n;
  const ecoule = (Date.now() - batimentsLu) / 1000;
  if(ecoule < B.prochain_dans) return n;
  return Math.min(max, n + 1 + Math.floor((ecoule - B.prochain_dans) / (86400 / prod)));
}
function prochainLingotMs(){
  const B = BATIMENTS;
  if(!B || !B.fonderie || !B.fonderie.pret || B.prochain_dans == null) return null;
  if(lingotsActuels() >= (Number(B.max) || 30)) return null;
  const pas = 86400 / (Number(B.production) || 10);
  const ecoule = (Date.now() - batimentsLu) / 1000;
  const reste = ecoule < B.prochain_dans ? B.prochain_dans - ecoule : pas - ((ecoule - B.prochain_dans) % pas);
  return Math.max(60, reste) * 1000;
}
const btPretDans = (b) => Math.max(0, new Date(b.pret_le).getTime() - Date.now());
const mesForteresses = () => (BATIMENTS && BATIMENTS.forteresses) || [];
const btReglage = (cle, defaut) => (BATIMENTS && BATIMENTS.reglages && BATIMENTS.reglages[cle] != null) ? BATIMENTS.reglages[cle] : defaut;

// sur la fiche : ce qui est construit ici
function blocBatimentsEtat(code, c){
  const B = BATIMENTS;
  if(!B) return '';
  let html = '';
  const ici = B.fonderie && B.fonderie.code === code ? B.fonderie : null;
  if(ici){
    const n = lingotsActuels(), max = Number(B.max) || 30;
    const prete = btPretDans(ici) <= 0;
    const pr = prochainLingotMs();
    html += `<div class="bt">
      <div class="bt-haut">${ICONE_FONDERIE}Fonderie <b>${n} / ${max} ${ICONE_LINGOT}</b></div>
      <div class="bt-barre" style="grid-template-columns:repeat(${max},1fr)">${Array.from({ length: max }, (_, i) => `<i class="${i < n ? 'p' : ''}"></i>`).join('')}</div>
      <p class="bt-txt">${prete ? `<b>+${B.production} lingots par jour</b>, jusqu’à ${max} en réserve${pr ? ` · prochain dans ${formatDuree(pr)}` : ''}.` : `<b>En construction</b> : prête dans ${formatDuree(btPretDans(ici))}.`}
        Visible de tous : si on te prend ${echapperHtml(c.nom)}, la Fonderie est détruite et l’attaquant pille ${btReglage('pillage', 50)} % de ta réserve.</p>
    </div>`;
  }
  const fort = mesForteresses().find(x => x.code === code);
  if(fort){
    const prete = btPretDans(fort) <= 0;
    html += `<div class="bt bt-fort">
      <div class="bt-haut">${ICONE_FORTERESSE}Forteresse <b>${prete ? 'active' : 'prête dans ' + formatDuree(btPretDans(fort))}</b></div>
      <p class="bt-txt"><b>−${btReglage('forteresse_defense', 15)} %</b> aux chances des attaquants ici, et <b>+${btReglage('forteresse_appui', 5)} %</b> à tes attaques à moins de ${btReglage('rayon_km', 20)} km.</p>
    </div>`;
  }
  return html;
}
// sur la fiche : ce qu'on peut y construire
function blocBatimentsActions(code, c){
  const B = BATIMENTS;
  if(!B) return '';
  const h = btReglage('construction_h', 24);
  const arme = (t) => btArme === code + '|' + t;
  const boutons = [];
  if(!B.fonderie){
    boutons.push(`<button class="pc-action bt-action${arme('fonderie') ? ' arme' : ''}" data-pc="bt-construire" data-bt="fonderie">${ICONE_FONDERIE}<span>${arme('fonderie') ? `Confirmer : la Fonderie à ${echapperHtml(c.nom)}` : 'Construire la Fonderie ici'}<small>Une seule · prête dans ${h} h · ${B.production} lingots par jour</small></span><span class="prix">gratuit</span></button>`);
  }
  if(!mesForteresses().some(x => x.code === code)){
    const nb = mesForteresses().length, maxF = btReglage('forteresse_max', 3), prix = btReglage('forteresse_prix', 20);
    const n = lingotsActuels();
    const bloque = !B.fonderie ? 'Il te faut d’abord une Fonderie'
      : nb >= maxF ? `Déjà ${maxF} forteresses`
      : n < prix ? `Il te faut ${prix} lingots (tu en as ${n})` : '';
    boutons.push(`<button class="pc-action bt-action${arme('forteresse') ? ' arme' : ''}" data-pc="bt-construire" data-bt="forteresse" ${bloque ? 'disabled' : ''}>${ICONE_FORTERESSE}<span>${arme('forteresse') ? `Confirmer : ${prix} lingots` : `Faire de ${echapperHtml(c.nom)} une Forteresse`}<small>${bloque || `Prête dans ${h} h · ${nb} / ${maxF} · −${btReglage('forteresse_defense', 15)} % en défense, +${btReglage('forteresse_appui', 5)} % autour`}</small></span><span class="prix">${prix} ${ICONE_LINGOT}</span></button>`);
  }
  return boutons.length ? `<p class="pc-titre-bt">Bâtiments</p><div class="pc-actions pc-actions-bt">${boutons.join('')}</div>` : '';
}
async function batimentConstruire(code, type){
  const nom = type === 'fonderie' ? 'Fonderie' : 'Forteresse';
  const { error } = await sb.rpc('batiment_construire', { p_code: code, p_type: type });
  if(error) notifier({ type: 'erreur', titre: nom, texte: messageLisible(error.message) });
  else notifier({ type: 'succes', titre: nom + ' en construction', texte: `Prête dans ${btReglage('construction_h', 24)} h.` });
  await chargerBatiments();
  if(panneauCommune === code && collectionMap.get(code)){ const a = panneauAncre; ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40); }
}
// Défendre : réserve, Fonderie, forteresses
function renderBatimentsBloc(){
  const el = document.getElementById('batimentsBloc');
  if(!el) return;
  const B = BATIMENTS;
  el.hidden = !B;
  if(!B) return;
  const n = lingotsActuels(), max = Number(B.max) || 30;
  const pr = prochainLingotMs();
  const F = B.fonderie;
  const forts = mesForteresses();
  const maxF = btReglage('forteresse_max', 3), prix = btReglage('forteresse_prix', 20);
  const etat = (b) => btPretDans(b) <= 0 ? '<span class="btl-etat ok">Active</span>' : `<span class="btl-etat cours">prête dans ${formatDuree(btPretDans(b))}</span>`;
  const ligne = (ic, b, sous) => `<div class="btl"><span class="btl-ic">${ic}</span>
      <span class="btl-t"><button type="button" class="btl-nom" data-voir-carte="${echapperTexte(b.code)}">${echapperTexte(b.nom)} (${echapperTexte(b.dept)})</button><small>${sous}</small></span>${etat(b)}</div>`;
  el.innerHTML = `<h2>Bâtiments</h2>
    <div class="bt-reserve"><span class="btr-nb">${n}</span>${ICONE_LINGOT}<span class="btr-max">/ ${max} lingots</span>
      <span class="btr-prod">${F ? (btPretDans(F) <= 0 ? `+${B.production} par jour<br>${pr ? 'prochain dans ' + formatDuree(pr) : 'réserve pleine'}` : 'Fonderie<br>en construction') : 'Pas encore<br>de Fonderie'}</span></div>
    <div class="btl-titre">Fonderie</div>
    ${F ? ligne(ICONE_FONDERIE, F, btPretDans(F) <= 0 ? `Produit ${B.production} lingots par jour` : 'En construction')
        : '<p class="gl-vide">Ouvre une de tes communes sur la carte et choisis « Construire la Fonderie ici ». Elle est gratuite, mais visible de tous : choisis bien l’endroit.</p>'}
    <div class="btl-titre">Forteresses <em>${forts.length} / ${maxF}</em></div>
    ${forts.map(x => ligne(ICONE_FORTERESSE, x, btPretDans(x) <= 0 ? `−${btReglage('forteresse_defense', 15)} % aux attaquants · +${btReglage('forteresse_appui', 5)} % autour` : 'En construction')).join('')}
    ${F && forts.length < maxF ? (n >= prix
        ? `<input type="search" class="bourse-search gn-cherche" id="btCherche" placeholder="Fortifier une de mes communes (${prix} lingots)…" autocomplete="off" value="${echapperTexte(btRecherche)}"><div class="gn-choix" id="btChoix">${btChoixHtml()}</div>`
        : `<p class="gl-vide">Prochaine forteresse : ${prix} lingots (tu en as ${n}).</p>`) : ''}
    <p class="btl-regle">Les lingots ne servent qu’aux bâtiments : ils ne s’échangent pas, ne s’achètent pas et repartent à zéro à chaque saison. Un bâtiment est perdu si on prend sa commune.</p>`;
  const champ = document.getElementById('btCherche');
  if(champ) champ.addEventListener('input', (e) => {
    btRecherche = e.target.value;
    const z = document.getElementById('btChoix'); if(z) z.innerHTML = btChoixHtml();
  });
}
function btChoixHtml(){
  const q = sansAccents(btRecherche.trim().toLowerCase());
  const deja = new Set(mesForteresses().map(x => x.code));
  const rang = (t) => TIERS.findIndex(x => x.id === t.id);
  const mes = [...collectionMap.values()].filter(c => !deja.has(c.code)
    && (!q || sansAccents(c.nom.toLowerCase()).includes(q) || c.dept === q.toUpperCase()));
  mes.sort((a, b) => rang(a.tier) - rang(b.tier) || a.nom.localeCompare(b.nom, 'fr'));
  if(!mes.length) return `<p class="gl-vide">${collectionMap.size ? 'Aucune de tes communes ne correspond.' : 'Tu n\\'as pas encore de commune dans le Front.'}</p>`;
  const prix = btReglage('forteresse_prix', 20);
  return mes.slice(0, 6).map(c => {
    const a = btArme === c.code + '|forteresse';
    return `<div class="gl gn-ligne"><i class="gl-c ${c.tier.id}"></i><div class="gl-t"><b>${echapperTexte(c.nom)}</b>
      <span>${c.tier.label} · ${echapperTexte(DEPT_NAMES[c.dept] || c.dept)} (${echapperTexte(c.dept)})</span></div>
      <button class="gl-r bt-fortifier${a ? ' arme' : ''}" data-bt-fortifier="${echapperTexte(c.code)}">${a ? `Confirmer · ${prix} lingots` : 'Fortifier'}</button></div>`;
  }).join('') + (mes.length > 6 ? `<p class="gl-vide">+ ${mes.length - 6} autre${mes.length - 6 > 1 ? 's' : ''} : affine la recherche.</p>` : '');
}
// la carte : une pastille par bâtiment (doré : les miens), pointillés tant qu'il est en construction
function dessinerBatimentsCanvas(ctx, liste){
  if(!BT_TRACES) return;
  const e = 1 / Math.max(1, mapZoom);
  const vue = vueCarteUnites(12);
  for(const c of liste){
    const bt = BATIMENTS_CARTE.get(String(c.code));
    if(!bt) continue;
    const x = c.x, y = c.y;
    if(x < vue[0] || x > vue[2] || y < vue[1] || y > vue[3]) continue;
    const types = ['fonderie', 'forteresse'].filter(t => bt[t]);
    types.forEach((t, i) => {
      const r = 7.5 * e;
      const cx = x + (types.length > 1 ? (i ? 1 : -1) * r * 0.95 : 0), cy = y - r * 1.1;
      ctx.globalAlpha = bt[t].pret ? 1 : 0.65;
      ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fillStyle = '#2A1A0E'; ctx.fill();
      ctx.lineWidth = 1.6 * e; ctx.strokeStyle = bt[t].moi ? '#F0B429' : '#E8833A';
      if(!bt[t].pret) ctx.setLineDash([2.2 * e, 1.6 * e]);
      ctx.stroke(); ctx.setLineDash([]);
      ctx.save();
      const k = r / 14;
      ctx.translate(cx - 12 * k, cy - 12 * k); ctx.scale(k, k);
      ctx.strokeStyle = '#FFB27A'; ctx.fillStyle = '#FFB27A'; ctx.lineWidth = 1.9; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      ctx.stroke(BT_TRACES[t][0]); if(BT_TRACES[t][1]) ctx.fill(BT_TRACES[t][1]);
      ctx.restore();
    });
  }
  ctx.globalAlpha = 1;
}

// ---------- patch91 : garnisons ----------
""")
f.write_text(s, encoding='utf-8')

# 10. styles
f, s = ouvrir('style.css')
s += """
/* ---------- patch243 : les bâtiments du Front ---------- */
.lingot{ display:inline-block; width:14px; height:9px; vertical-align:-1px; flex:none;
  background:linear-gradient(180deg,#FFE08A,#F0B429 55%,#B98316); clip-path:polygon(18% 0,82% 0,100% 100%,0 100%); }
.bt{ margin-top:11px; padding:10px 11px; border-radius:11px; background:linear-gradient(160deg,rgba(232,131,58,.16),rgba(232,131,58,.05)); border:1px solid rgba(232,131,58,.4); }
.bt-haut{ display:flex; align-items:center; gap:7px; color:#FFB27A; font-weight:700; font-size:.8rem; text-transform:uppercase; letter-spacing:.06em; }
.bt-haut svg{ width:16px; height:16px; flex:none; }
.bt-haut b{ margin-left:auto; color:#fff; font-size:.9rem; letter-spacing:0; text-transform:none; display:flex; align-items:center; gap:5px; }
.bt-barre{ display:grid; gap:2px; margin:8px 0 6px; }
.bt-barre i{ height:8px; border-radius:2px; background:rgba(169,188,212,.16); }
.bt-barre i.p{ background:linear-gradient(180deg,#FFE08A,#F0B429); }
.bt-txt{ font-size:.72rem; color:#D6C2B2; line-height:1.4; margin:0; }
.bt-txt b{ color:#fff; }
.bt.bt-fort .bt-txt{ margin-top:6px; }
.pc-titre-bt{ margin:12px 0 0; font-size:.68rem; letter-spacing:.08em; text-transform:uppercase; color:#B9A08C; font-weight:600; }
.pc-actions.pc-actions-bt{ margin-top:6px; }
.pc-action.bt-action{ border-color:rgba(232,131,58,.45); background:rgba(232,131,58,.12); white-space:normal; overflow:visible; }
.pc-action.bt-action:hover{ background:rgba(232,131,58,.22); }
.pc-action.bt-action:disabled{ opacity:.55; cursor:default; }
.pc-action.bt-action:disabled:hover{ background:rgba(232,131,58,.12); }
.pc-action.bt-action.arme{ border-color:#E8833A; background:rgba(232,131,58,.3); }
.pc-action.bt-action svg{ color:#FFB27A; }
.pc-action.bt-action > span:first-of-type{ flex:1; min-width:0; }
.pc-action.bt-action small{ display:block; font-size:.68rem; color:#C9AE97; font-weight:400; margin-top:1px; }
.pc-action .prix{ margin-left:auto; flex:none; display:flex; align-items:center; gap:5px; font-size:.78rem; color:#FFD9B8; font-weight:600; }
.gn-badge.bt-badge{ background:rgba(232,131,58,.12); border-color:rgba(232,131,58,.38); }
.gn-badge.bt-badge svg{ color:#FFB27A; }
.bt-appui{ display:flex; align-items:center; gap:7px; margin:8px 0 0; font-size:.76rem; color:#FFD9B8; }
.bt-appui svg{ width:15px; height:15px; flex:none; color:#FFB27A; }
.bt-appui b{ color:#fff; }
.as-mon.as-bt{ color:#FFD9B8; }
.as-mon.as-bt svg{ color:#FFB27A; }
.batiments-bloc[hidden]{ display:none; }
.bt-reserve{ display:flex; align-items:center; gap:8px; padding:12px; border-radius:13px; background:linear-gradient(160deg,rgba(232,131,58,.18),rgba(232,131,58,.05)); border:1px solid rgba(232,131,58,.4); }
.bt-reserve .lingot{ width:20px; height:13px; }
.btr-nb{ font-family:var(--titre); font-weight:900; font-size:2.1rem; line-height:1; }
.btr-max{ color:#B9A08C; font-size:.85rem; }
.btr-prod{ margin-left:auto; font-size:.76rem; color:#FFD9B8; text-align:right; line-height:1.3; }
.btl-titre{ margin:16px 2px 2px; font-size:.7rem; letter-spacing:.08em; text-transform:uppercase; color:#8FA4BF; font-weight:600; display:flex; }
.btl-titre em{ margin-left:auto; font-style:normal; color:#fff; }
.btl{ display:flex; align-items:center; gap:10px; padding:10px 11px; margin-top:8px; border-radius:11px; background:var(--nuit-2); border:1px solid rgba(169,188,212,.14); }
.btl-ic{ width:32px; height:32px; border-radius:9px; display:grid; place-items:center; background:rgba(232,131,58,.16); color:#FFB27A; flex:none; }
.btl-ic svg{ width:19px; height:19px; }
.btl-t{ flex:1; min-width:0; }
.btl-nom{ display:block; background:none; border:0; padding:0; font:inherit; font-weight:600; font-size:.86rem; color:#fff; cursor:pointer; text-align:left; }
.btl-nom:hover{ text-decoration:underline; }
.btl-t small{ display:block; font-size:.72rem; color:#8FA4BF; margin-top:2px; }
.btl-etat{ font-size:.7rem; font-weight:600; padding:3px 8px; border-radius:999px; white-space:nowrap; }
.btl-etat.ok{ background:rgba(43,212,139,.16); color:#5BE3A6; }
.btl-etat.cours{ background:rgba(232,131,58,.18); color:#FFB27A; }
.btl-regle{ margin:12px 2px 0; font-size:.72rem; color:#7B8FAB; line-height:1.45; }
.gl-r.bt-fortifier{ border-color:rgba(232,131,58,.55); background:rgba(232,131,58,.14); }
.gl-r.bt-fortifier.arme{ background:rgba(232,131,58,.32); border-color:#E8833A; }
.leg-bt{ display:inline-grid; place-items:center; width:20px; height:20px; border-radius:50%; background:#2A1A0E; border:1.5px solid #E8833A; color:#FFB27A; margin:0 3px; }
.leg-bt svg{ width:13px; height:13px; }
"""
f.write_text(s, encoding='utf-8')

# 11. les règles du Front
f, s = ouvrir('index.html')
s = rep(s, "            <p><b>Aurore et skins</b> :",
"""            <p><b>Bâtiments</b> : sur une de tes communes, construis ta <b>Fonderie</b> (gratuite, une seule) : elle produit <b>10 lingots par jour</b>, 30 en réserve. Avec <b>20 lingots</b>, fais d'une commune une <b>Forteresse</b> (3 au plus) : <b>−15 %</b> aux chances des attaquants sur elle, et <b>+5 %</b> à tes attaques à moins de 20 km. Un bâtiment met 24 h à se construire, se voit sur la carte et disparaît si on prend sa commune ; prendre une Fonderie pille la moitié des lingots de son propriétaire. Les lingots ne servent qu'aux bâtiments et repartent à zéro à chaque saison.</p>
            <p><b>Aurore et skins</b> :""")
f.write_text(s, encoding='utf-8')
print('patch243 ok')
