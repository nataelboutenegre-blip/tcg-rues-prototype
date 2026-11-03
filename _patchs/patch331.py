# patch331 (3/11/2026) : saison 3, la carte France + Suisse (aperçu validé le 3/11),
# éteinte comme patch330 (SUISSE_OUVERTE = false, ?suisse=test pour essayer).
# Quand la Suisse est allumée :
# - le cadre de la carte s'élargit vers l'est (les Grisons vont jusqu'à 10,5 °E) ;
# - les pays voisins sont dessinés, éteints (gris hachuré, noms en sourdine) ;
# - la terre suisse, ses lacs (Léman, Constance, Neuchâtel…) et sa frontière
#   (trait de région, plus épais) ; le trait de côte de la France s'efface le
#   long de la frontière suisse ;
# - les cantons rejoignent les départements (vue de loin, limites, nom
#   « SUISSE ») et leurs communes se chargent par canton (contours/GE.json…).
# Sources : swisstopo (swissBOUNDARIES3D, swissTLMRegio), Natural Earth pour les voisins.
import pathlib

F = pathlib.Path('app.js')
s = F.read_text(encoding='utf-8')

def rep(avant, apres, n=1):
    global s
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    s = s.replace(avant, apres)

# 1. le fond suisse se charge avec le contour de la France, avant le calcul du cadre
rep("""async function chargerContourFrance(){
  const res = await fetch('data/france-outline.json');
  FRANCE_OUTLINE = await res.json();
  computeMapBounds();""", """// patch331 : le fond de la saison 3 (Suisse, lacs, frontière, voisins)
let FOND_S3 = null;
async function chargerFondSuisse(){
  try {
    const lire = (f) => fetch('data/' + f + '?v=1', { cache: 'force-cache' }).then(r => { if(!r.ok) throw new Error(f); return r.json(); });
    const [terre, frontiere, lacs, voisins] = await Promise.all(
      ['suisse-terre.json', 'suisse-frontiere.json', 'lacs-suisse.json', 'voisins.json'].map(lire));
    FOND_S3 = { terre, frontiere, lacs, voisins, chemins: null };
  } catch(e){ FOND_S3 = null; }
}
function cheminsFondS3(){
  if(!FOND_S3 || !mapBounds) return null;
  if(FOND_S3.chemins) return FOND_S3.chemins;
  const ch = (rings) => new Path2D(rings.map(r => 'M' + r.map(([lon, lat]) => {
    const p = project(lat, lon);
    return (p.x * MAP_W).toFixed(1) + ',' + (p.y * MAP_H).toFixed(1);
  }).join('L') + 'Z').join(''));
  const voisins = new Path2D();
  const etiquettes = [];
  for(const v of FOND_S3.voisins){
    voisins.addPath(ch(v.a));
    if(v.e){ const p = project(v.e[1], v.e[0]); etiquettes.push({ nom: v.nom, x: p.x * MAP_W, y: p.y * MAP_H }); }
  }
  FOND_S3.chemins = { terre: ch(FOND_S3.terre), frontiere: ch(FOND_S3.frontiere), lacs: ch(FOND_S3.lacs), voisins, etiquettes, motif: null };
  return FOND_S3.chemins;
}

async function chargerContourFrance(){
  const res = await fetch('data/france-outline.json');
  FRANCE_OUTLINE = await res.json();
  if(SUISSE) await chargerFondSuisse();   // patch331
  computeMapBounds();""")

# 2. le cadre englobe la Suisse
rep("""  let latMin=90, latMax=-90, lonMin=180, lonMax=-180;
  for(const ring of FRANCE_OUTLINE){
    for(const [lon, lat] of ring){""", """  let latMin=90, latMax=-90, lonMin=180, lonMax=-180;
  for(const ring of FRANCE_OUTLINE.concat(FOND_S3 ? FOND_S3.terre : [])){   // patch331
    for(const [lon, lat] of ring){""")

# 3. dessin : voisins sous la terre, terre suisse avec la France, côte effacée le long de la Suisse
rep("""  // ombre portee, puis la terre
  if(fond.ombre){""", """  // patch331 : les voisins, éteints, sous tout le reste
  const s3 = SUISSE ? cheminsFondS3() : null;
  if(s3){
    if(!s3.motif){
      const t = document.createElement('canvas'); t.width = t.height = 10;
      const tc = t.getContext('2d');
      tc.fillStyle = '#1A2331'; tc.fillRect(0, 0, 10, 10);
      tc.strokeStyle = 'rgba(169,188,212,0.075)'; tc.lineWidth = 1;
      tc.beginPath(); tc.moveTo(-2, 12); tc.lineTo(12, -2); tc.moveTo(-2, 2); tc.lineTo(2, -2); tc.moveTo(8, 12); tc.lineTo(12, 8); tc.stroke();
      s3.motif = ctx.createPattern(t, 'repeat');
    }
    if(s3.motif.setTransform) s3.motif.setTransform(new DOMMatrix().scale(CV.dpr / k));
    ctx.fillStyle = s3.motif; ctx.fill(s3.voisins);
    ctx.strokeStyle = 'rgba(169,188,212,0.30)'; ctx.lineWidth = trait(0.9);
    ctx.setLineDash([trait(3), trait(3)]); ctx.stroke(s3.voisins); ctx.setLineDash([]);
  }

  // ombre portee, puis la terre
  if(fond.ombre){""")
rep("""  ctx.fillStyle = gt;
  ctx.fill(fond.terre);
""", """  ctx.fillStyle = gt;
  ctx.fill(fond.terre);
  if(s3) ctx.fill(s3.terre);   // patch331
""")
rep("""  if(fond.cote){
    ctx.strokeStyle = 'rgba(169,188,212,0.45)'; ctx.lineWidth = trait(1.2);
    ctx.stroke(fond.cote);
  }""", """  if(fond.cote){
    ctx.strokeStyle = 'rgba(169,188,212,0.45)'; ctx.lineWidth = trait(1.2);
    if(s3){   // patch331 : pas de côte le long de la Suisse, la frontière la remplace
      ctx.save();
      const hors = new Path2D(); hors.rect(-MAP_W, -MAP_H, MAP_W * 3, MAP_H * 3); hors.addPath(s3.terre);
      ctx.clip(hors, 'evenodd');
      ctx.stroke(fond.cote);
      ctx.restore();
    } else ctx.stroke(fond.cote);
  }""")

# 4. les lacs par-dessus les fonds, la frontière suisse par-dessus les limites
rep("""  const mode = dessinerFondsCanvas(ctx, trait, k, liste, joueurs);
  if(mode === 'contours') dessinerArrondissementsParis(ctx, trait, k, liste);   // patch108
  dessinerFrontieres(ctx, trait, mode === 'contours');""", """  const mode = dessinerFondsCanvas(ctx, trait, k, liste, joueurs);
  if(mode === 'contours') dessinerArrondissementsParis(ctx, trait, k, liste);   // patch108
  const s3 = SUISSE ? cheminsFondS3() : null;   // patch331 : les lacs
  if(s3){
    ctx.fillStyle = '#0D2240'; ctx.fill(s3.lacs);
    ctx.strokeStyle = 'rgba(169,188,212,0.25)'; ctx.lineWidth = trait(0.8); ctx.stroke(s3.lacs);
  }
  dessinerFrontieres(ctx, trait, mode === 'contours');
  if(s3){   // patch331 : la frontière suisse, comme une limite de région, plus épaisse
    ctx.strokeStyle = 'rgba(7,17,31,0.6)'; ctx.lineWidth = trait(6.6); ctx.stroke(s3.frontiere);
    ctx.strokeStyle = 'rgba(214,230,246,0.8)'; ctx.lineWidth = trait(3); ctx.stroke(s3.frontiere);
    ctx.setLineDash([trait(7), trait(5)]);
    ctx.strokeStyle = 'rgba(15,31,56,0.85)'; ctx.lineWidth = trait(1.1); ctx.stroke(s3.frontiere);
    ctx.setLineDash([]);
  }""")

# 5. les noms des voisins, en sourdine, avec ceux des régions
rep("""    ctx.fillStyle = 'rgba(224,236,250,0.82)';
    ctx.fillText(e.nom, x, y);
  }
  ctx.globalAlpha = 1;""", """    ctx.fillStyle = 'rgba(224,236,250,0.82)';
    ctx.fillText(e.nom, x, y);
  }
  const s3 = SUISSE ? cheminsFondS3() : null;   // patch331 : les voisins, éteints
  if(s3) for(const e of s3.etiquettes){
    const x = e.x * ech + mapPanX * CV.dpr, y = e.y * ech + mapPanY * CV.dpr;
    if(x < -80 || y < -20 || x > CV.largeur * CV.dpr + 80 || y > CV.hauteur * CV.dpr + 20) continue;
    ctx.strokeStyle = 'rgba(7,17,31,0.6)'; ctx.lineWidth = 3.4 * CV.dpr;
    ctx.strokeText(e.nom, x, y);
    ctx.fillStyle = 'rgba(169,188,212,0.42)';
    ctx.fillText(e.nom, x, y);
  }
  ctx.globalAlpha = 1;""")

# 6. les cantons rejoignent les départements (vue de loin, limites, étiquette « SUISSE »)
rep("""    CONTOURS_DEPTS = await rep.json();
  } catch(e){
    CONTOURS_DEPTS = 'erreur';
  }
  renderMapOverlay();""", """    const deps = await rep.json();
    if(SUISSE){   // patch331
      try { Object.assign(deps, await (await fetch('data/contours-cantons.json?v=1', { cache: 'force-cache' })).json()); } catch(e){}
    }
    CONTOURS_DEPTS = deps;
  } catch(e){
    CONTOURS_DEPTS = 'erreur';
  }
  renderMapOverlay();""")

F.write_text(s, encoding='utf-8')
print('patch331 appliqué')
