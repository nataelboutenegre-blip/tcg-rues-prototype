# patch456 (18/11/2026) : saison 3 — l'Artillerie, la Centrale de clan, les ordres du chef (va avec _sql/s3-27).
# Rien ne s'affiche tant que s3-27 n'est pas lancé ou que ses interrupteurs sont éteints.
# Lancer : python3 _patchs/patch456.py .   (puis python3 maj-version.py)
import os, shutil, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
P = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(R, 'app.js')
s = open(p, encoding='utf-8').read()
if 'patch456' in s:
    print('app.js : déjà fait'); sys.exit(0)

def rep(a, b, n=1):
    global s
    c = s.count(a)
    assert c == n, (a[:90], c)
    s = s.replace(a, b)

# 1. les noms, les icônes, les styles
rep("const MBT_NOM = { forteresse: 'Forteresse', fonderie: 'Fonderie', banque: 'Banque', centre: 'Centre de recherche', radar: 'Radar' };",
    "const MBT_NOM = { forteresse: 'Forteresse', fonderie: 'Fonderie', banque: 'Banque', centre: 'Centre de recherche', radar: 'Radar', artillerie: 'Artillerie', centrale: 'Centrale de clan' };   // patch456")
rep("  const ico = { forteresse: ICONE_FORTERESSE, fonderie: ICONE_FONDERIE, banque: ICONE_BANQUE, centre: ICONE_CENTRE, radar: ICONE_RADAR };\n  for(const t of ['forteresse', 'fonderie', 'banque', 'centre', 'radar']){",
    "  const ico = { forteresse: ICONE_FORTERESSE, fonderie: ICONE_FONDERIE, banque: ICONE_BANQUE, centre: ICONE_CENTRE, radar: ICONE_RADAR, artillerie: ICONE_ARTILLERIE, centrale: ICONE_CENTRALE };   // patch456\n  for(const t of ['forteresse', 'fonderie', 'banque', 'centre', 'radar', 'artillerie', 'centrale']){")
rep("<b>${t === 'centre' ? 'Centre' : MBT_NOM[t]}</b>", "<b>${t === 'centre' ? 'Centre' : t === 'centrale' ? 'Centrale' : MBT_NOM[t]}</b>")
rep("const btNom = (type) => type === 'fonderie' ? 'Fonderie' : type === 'centre' ? 'Centre de recherche' : type === 'banque' ? 'Banque' : type === 'radar' ? 'Radar' : 'Forteresse';",
    "const btNom = (type) => type === 'fonderie' ? 'Fonderie' : type === 'centre' ? 'Centre de recherche' : type === 'banque' ? 'Banque' : type === 'radar' ? 'Radar' : type === 'artillerie' ? 'Artillerie' : type === 'centrale' ? 'Centrale de clan' : 'Forteresse';   // patch456")
rep("var BT_STYLES_DEFAUT = { fonderie: ['brique', 'acier'], forteresse: ['chateau', 'bastion', 'tour'], banque: ['classique', 'coffre'], centre: ['labo', 'bunker'], radar: ['parabole', 'dome', 'pylone'] };",
    "var BT_STYLES_DEFAUT = { fonderie: ['brique', 'acier'], forteresse: ['chateau', 'bastion', 'tour'], banque: ['classique', 'coffre'], centre: ['labo', 'bunker'], radar: ['parabole', 'dome', 'pylone'], artillerie: ['canon'], centrale: ['turbine'] };   // patch456")
rep("var BT_STYLE_NOMS = { brique: 'Brique',", "var BT_STYLE_NOMS = { canon: 'Canon', turbine: 'Turbine', brique: 'Brique',")   # patch456

# 2. la carte : deux types de plus, et la couleur de la Centrale
rep("const types = ['fonderie', 'forteresse', 'centre', 'banque', 'radar'].filter(t => bt[t] && BT_TRACES[t]);", "const types = ['fonderie', 'forteresse', 'centre', 'banque', 'radar', 'artillerie', 'centrale'].filter(t => bt[t] && BT_TRACES[t]);   // patch456", 2)
rep("t === 'radar' ? 'rgba(110,195,240,.75)' :", "t === 'radar' ? 'rgba(110,195,240,.75)' : t === 'centrale' ? 'rgba(95,211,157,.75)' :", 2)
rep("t === 'radar' ? '#6EC3F0' :", "t === 'radar' ? '#6EC3F0' : t === 'centrale' ? '#5FD39D' :", 2)
rep("  if(typeof SIEGE !== 'undefined' && SIEGE && (sgMes.length || sgMenaces.length)) dessinerSiegesCanvas(ctx, liste);   // patch435",
    "  if(typeof SIEGE !== 'undefined' && SIEGE && (sgMes.length || sgMenaces.length)) dessinerSiegesCanvas(ctx, liste);   // patch435\n  if(typeof s3DessinerOrdres === 'function') s3DessinerOrdres(ctx, liste);   // patch456 : les cibles du clan")

# 3. l'écran Bâtiments
rep("  if(BATIMENTS.radar) l.push(Object.assign({}, BATIMENTS.radar, { type: 'radar' }));   // patch371",
    "  if(BATIMENTS.radar) l.push(Object.assign({}, BATIMENTS.radar, { type: 'radar' }));   // patch371\n  if(BATIMENTS.artillerie && BATIMENTS.artilleries_ouvertes) l.push(Object.assign({}, BATIMENTS.artillerie, { type: 'artillerie' }));   // patch456")
rep("  return 'Il prépare une bombe. Le prendre fait perdre la bombe à son propriétaire';\n}",
    "  if(type === 'artillerie') return `Supprime le malus de distance des sièges à ${s3ArtR('portee_km', 50)} km. Secrète tant qu’elle ne tire pas`;   // patch456\n  if(type === 'centrale') return `${(S3C.centrale && S3C.centrale.part) || 8} énergie par jour pour chaque membre de son clan`;\n  return 'Il prépare une bombe. Le prendre fait perdre la bombe à son propriétaire';\n}")
rep("  if(b.type === 'radar'){ const n = (b.voit || []).length + (b.voit_banques || []).length;",
    "  if(b.type === 'artillerie') return b.devoilee ? { t: 'Visible : elle a tiré', c: 'rouge' } : { t: 'Secrète', c: 'or' };   // patch456\n  if(b.type === 'radar'){ const n = (b.voit || []).length + (b.voit_banques || []).length;")
rep("['radar', 'Radars'], ['centre', 'Centres'], ['banque', 'Banques']];", "['radar', 'Radars'], ['centre', 'Centres'], ['banque', 'Banques'], ['artillerie', 'Artilleries'], ['centrale', 'Centrales']];   // patch456")
rep("    ${radarHtml()}\n", "    ${radarHtml()}\n    ${typeof s3ArtillerieHtml === 'function' ? s3ArtillerieHtml() : ''}\n")   # patch456

# 4. la fiche d'une commune
rep("      if(bt.banque) t.push(bt.banque.pret ? 'Banque (vue par ton Radar)' : 'Banque en chantier (vue par ton Radar)');   // patch375",
    "      if(bt.banque) t.push(bt.banque.pret ? 'Banque (vue par ton Radar)' : 'Banque en chantier (vue par ton Radar)');   // patch375\n      if(bt.artillerie) t.push(bt.artillerie.pret ? 'Artillerie' : 'Artillerie en construction');   // patch456\n      if(bt.centrale) t.push(bt.centrale.pret ? 'Centrale de clan' : 'Centrale de clan en construction');")
rep("  return boutons.length ? `<p class=\"pc-titre-bt\">Bâtiments</p>",
    "  if(typeof s3BoutonsBt === 'function') boutons.push(...s3BoutonsBt(code, c));   // patch456\n  return boutons.length ? `<p class=\"pc-titre-bt\">Bâtiments</p>")
rep("    ${alerte}\n    ${gnBloc}${btEtat}\n",
    "    ${alerte}${typeof s3OrdreFiche === 'function' ? s3OrdreFiche(code, c, !!mienne, !!allie) : ''}\n    ${gnBloc}${btEtat}${typeof s3EtatFiche === 'function' ? s3EtatFiche(code, c, !!mienne) : ''}\n")   # patch456
rep("${echInter}${btActions}${libBloc}`;", "${echInter}${btActions}${typeof s3ActionsFiche === 'function' ? s3ActionsFiche(code, c, !!mienne, !!allie) : ''}${libBloc}`;")   # patch456
rep("  if(libClicPanneau(quoi, code)) return;   // patch273",
    "  if(typeof s3ClicPanneau === 'function' && s3ClicPanneau(quoi, code, b)) return;   // patch456\n  if(libClicPanneau(quoi, code)) return;   // patch273")

# 5. la feuille de siège
rep("      <div class=\"sg-l\"><span>Tes communes proches</span><span>${procheTxt} · ${multTxt}</span></div>\n",
    "      <div class=\"sg-l\"><span>Tes communes proches</span><span>${procheTxt} · ${multTxt}</span></div>\n      ${typeof s3SiegeLigne === 'function' ? s3SiegeLigne(a) : ''}\n")   # patch456
rep("      <li><b>Résistance</b> : commune et peu commune 55,", "      ${typeof s3SiegeCalc === 'function' ? s3SiegeCalc() : ''}\n      <li><b>Résistance</b> : commune et peu commune 55,")   # patch456

# 6. Mon front et l'onglet Clan
rep("<div class=\"mfo-jauge\">${Array.from({ length: max }, (_, i) => `<i class=\"${i < e ? 'p' : ''}\"></i>`).join('')}</div>${rc}</div>`;",
    "<div class=\"mfo-jauge\">${Array.from({ length: max }, (_, i) => `<i class=\"${i < e ? 'p' : ''}\"></i>`).join('')}</div>${rc}${typeof s3MfoCentrale === 'function' ? s3MfoCentrale() : ''}</div>`;   // patch456")
rep("  z.innerHTML = blocDanger + blocEnergie + blocAtt + mfoBatimentsHtml() + blocCom + blocQ;   // patch366",
    "  z.innerHTML = blocDanger + (typeof s3MfoOrdres === 'function' ? s3MfoOrdres() : '') + blocEnergie + blocAtt + mfoBatimentsHtml() + blocCom + blocQ;   // patch366, patch456")
rep("      ${blocJour}\n      ${candGererHtml(c)}   <!-- patch307 -->",
    "      ${blocJour}\n      ${typeof s3ClanBlocs === 'function' ? s3ClanBlocs() : ''}\n      ${candGererHtml(c)}   <!-- patch307 -->")   # patch456

# 7. le chargement : avec les bâtiments
rep("    if(btEcranOuvert() && BTE.vue === 'miens') btEcranRendre();\n",
    "    if(btEcranOuvert() && BTE.vue === 'miens') btEcranRendre();\n    if(typeof s3Charger === 'function') s3Charger();   // patch456\n")

# 8. le journal : ce qu'on perd
rep("    if(x.t === 'radar') return '<b>ton Radar</b>';", "    if(x.t === 'radar') return '<b>ton Radar</b>';\n    if(x.t === 'artillerie') return '<b>ton Artillerie</b>';   // patch456\n    if(x.t === 'centrale') return '<b>la Centrale de ton clan</b>';")

s = s.rstrip('\n') + '\n' + open(os.path.join(P, 'patch456.js'), encoding='utf-8').read()
open(p, 'w', encoding='utf-8').write(s)
print('app.js : ok')

c = os.path.join(R, 'style.css')
t = open(c, encoding='utf-8').read()
if 'patch456' not in t:
    open(c, 'w', encoding='utf-8').write(t.rstrip('\n') + '\n' + open(os.path.join(P, 'patch456.css'), encoding='utf-8').read())
    print('style.css : ok')
for f in ('artillerie-canon.svg', 'centrale-turbine.svg'):
    shutil.copy(os.path.join(P, f), os.path.join(R, 'batiments', f))
print('batiments/ : ok')
