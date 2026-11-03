# patch335 (3/11/2026) : carte, retours d'Oshannir (aperçu validé « parfait ») :
# - la bordure de chaque territoire passe à l'intérieur de ses communes au lieu de
#   déborder sur les voisines (mode Raretés : la bande de couleur du joueur ; mode
#   Joueurs : le trait sombre). Seul le tour du territoire est tracé : un segment
#   de commune est un bord quand la commune d'en face n'est pas au même joueur.
#   Qui touche qui est préparé une fois par département chargé (numéros, pas de
#   texte) ; le tour est gardé tant que les possessions et les départements
#   affichés ne changent pas (rien à refaire pendant un glissé) ;
# - de près, les limites de département sont nettes (trait clair sur liseré sombre).
import pathlib

F = pathlib.Path('app.js')
s = F.read_text(encoding='utf-8')

def rep(avant, apres, n=1):
    global s
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    s = s.replace(avant, apres)

# 1. le tour de chaque territoire, calculé une fois
rep("""function cheminCommuneCanvas(code, poly){""", """// patch335 : qui touche qui. Pour chaque département chargé, une seule fois :
// chaque segment de contour, numéroté, avec la commune de chaque côté (les
// segments sur une limite de département sont reconnus d'un fichier à l'autre)
const TOPO = { pts: new Map(), px: [], py: [], segs: new Map(), sa: [], sb: [], c1: [], c2: [],
               communes: new Map(), segsCommune: [], deps: new Map(), version: 0 };
function topoDepartement(dep, contours){
  let liste = TOPO.deps.get(dep);
  if(liste) return liste;
  liste = [];
  const point = (q) => {
    const k = Math.round((q[0] + 180) * 1e4) * 4e6 + Math.round((q[1] + 90) * 1e4);
    let i = TOPO.pts.get(k);
    if(i === undefined){
      i = TOPO.px.length; TOPO.pts.set(k, i);
      const r = project(q[1], q[0]);
      TOPO.px.push(Math.round(r.x * MAP_W * 10) / 10); TOPO.py.push(Math.round(r.y * MAP_H * 10) / 10);
    }
    return i;
  };
  for(const code in contours){
    let ci = TOPO.communes.get(code);
    if(ci !== undefined){ liste.push(ci); continue; }   // déjà vue dans un autre fichier
    ci = TOPO.segsCommune.length; TOPO.communes.set(code, ci); TOPO.segsCommune.push([]);
    liste.push(ci);
    const mes = TOPO.segsCommune[ci];
    for(const anneau of contours[code]){
      const n = anneau.length, ids = anneau.map(point);
      for(let i = 0; i < n; i++){
        const a = ids[i], b = ids[(i + 1) % n];
        if(a === b) continue;
        const k = a < b ? a * 67108864 + b : b * 67108864 + a;
        const s = TOPO.segs.get(k);
        if(s === undefined){
          TOPO.segs.set(k, TOPO.sa.length);
          mes.push(TOPO.sa.length); TOPO.sa.push(a); TOPO.sb.push(b); TOPO.c1.push(ci); TOPO.c2.push(-1);
        } else if(TOPO.c2[s] === -1){
          TOPO.c2[s] = ci;
          if(TOPO.c1[s] !== ci) mes.push(s);
        }
      }
    }
  }
  TOPO.deps.set(dep, liste);
  TOPO.version++;
  return liste;
}

// patch335 : le tour de chaque territoire, pour les départements à l'écran : un
// segment est un bord quand la commune d'en face n'est pas au même joueur. Mis
// bout à bout en lignes continues (des milliers de petits traits séparés coûtent
// bien plus cher à dessiner). Gardé tant que les possessions et les départements
// affichés ne changent pas : rien à refaire pendant un glissé
function bordsTerritoires(deps, possedees){
  const prets = [...deps].filter(d => { const c = CONTOURS.get(d); return c && c !== 'erreur'; }).sort();
  for(const d of prets) topoDepartement(d, CONTOURS.get(d));
  const cle = prets.join(',') + '|' + TOPO.version;
  if(CV.bords && CV.bords.possedees === possedees && CV.bords.cle === cle) return CV.bords.parJoueur;
  const proprio = new Int32Array(TOPO.segsCommune.length);   // commune -> joueur (0 : personne)
  const joueursIds = [], numero = new Map();
  for(const [code, c] of possedees){
    const ci = TOPO.communes.get(code);
    if(ci === undefined) continue;
    let k = numero.get(c.joueur);
    if(k === undefined){ joueursIds.push(c.joueur); k = joueursIds.length; numero.set(c.joueur, k); }
    proprio[ci] = k;
  }
  const vue = new Uint8Array(TOPO.segsCommune.length);
  const bordsDe = new Map();   // joueur (numéro) -> segments du bord
  for(const d of prets) for(const ci of TOPO.deps.get(d)){
    const k = proprio[ci];
    if(!k || vue[ci]) continue;
    vue[ci] = 1;
    let l = bordsDe.get(k);
    if(!l){ l = []; bordsDe.set(k, l); }
    for(const s of TOPO.segsCommune[ci]){
      const autre = TOPO.c1[s] === ci ? TOPO.c2[s] : TOPO.c1[s];
      if(autre < 0 || proprio[autre] !== k) l.push(s);
    }
  }
  const { px, py, sa, sb } = TOPO;
  const parJoueur = new Map();
  for(const [k, l] of bordsDe){
    const suite = new Map();   // point -> segments du bord qui y passent
    for(let i = 0; i < l.length; i++){
      for(const q of [sa[l[i]], sb[l[i]]]){ const t = suite.get(q); if(t) t.push(i); else suite.set(q, [i]); }
    }
    const pris = new Uint8Array(l.length);
    const p = new Path2D();
    for(let i0 = 0; i0 < l.length; i0++){
      if(pris[i0]) continue;
      pris[i0] = 1;
      p.moveTo(px[sa[l[i0]]], py[sa[l[i0]]]);
      let bout = sb[l[i0]];
      p.lineTo(px[bout], py[bout]);
      for(;;){
        const t = suite.get(bout);
        let i = -1;
        if(t) for(const j of t) if(!pris[j]){ i = j; break; }
        if(i < 0) break;
        pris[i] = 1;
        bout = sa[l[i]] === bout ? sb[l[i]] : sa[l[i]];
        p.lineTo(px[bout], py[bout]);
      }
    }
    parJoueur.set(joueursIds[k - 1], p);
  }
  CV.bords = { possedees, cle, parJoueur };
  return parJoueur;
}

function cheminCommuneCanvas(code, poly){""")

# 2. mode Raretés : la couleur du joueur en bande à l'intérieur de son territoire
rep("""        ctx.globalAlpha = 1;
        for(const id of ordre([...parJoueur.keys()])){
          const j = joueurs.get(id), chemin = parJoueur.get(id);
          const dehors = new Path2D();
          dehors.rect(-MAP_W, -MAP_H, MAP_W * 3, MAP_H * 3);
          dehors.addPath(chemin);
          ctx.save();
          ctx.clip(dehors, 'evenodd');
          ctx.globalAlpha = opaciteJoueur(id, 1);
          ctx.strokeStyle = '#07111F'; ctx.lineWidth = trait(j.moi ? 8 : 7); ctx.stroke(chemin);
          ctx.strokeStyle = j.couleur; ctx.lineWidth = trait(j.moi ? 5 : 4); ctx.stroke(chemin);
          ctx.restore();
        }""", """        ctx.globalAlpha = 1;
        const bords = bordsTerritoires(deps, possedees);   // patch335 : à l'intérieur, plus sur la voisine
        for(const id of ordre([...parJoueur.keys()])){
          const j = joueurs.get(id), chemin = parJoueur.get(id), bord = bords.get(id);
          if(!bord) continue;
          ctx.save();
          ctx.clip(chemin);
          ctx.globalAlpha = opaciteJoueur(id, 1);
          ctx.strokeStyle = j.couleur; ctx.lineWidth = trait(j.moi ? 10 : 8); ctx.stroke(bord);
          ctx.strokeStyle = '#07111F'; ctx.lineWidth = trait(2.2); ctx.stroke(bord);
          ctx.restore();
        }""")

# 3. mode Joueurs : le trait sombre à l'intérieur du territoire
rep("""      for(const id of ordre([...parJoueur.keys()])){
        const j = joueurs.get(id);
        const p = parJoueur.get(id);
        ctx.globalAlpha = opaciteJoueur(id, 1);
        ctx.strokeStyle = '#07111F'; ctx.lineWidth = trait(3.4); ctx.stroke(p);
        ctx.globalAlpha = opaciteJoueur(id, j.moi ? 0.95 : 0.78);
        ctx.fillStyle = j.couleur; ctx.fill(p);""", """      for(const id of ordre([...parJoueur.keys()])){
        const j = joueurs.get(id);
        const p = parJoueur.get(id);
        ctx.globalAlpha = opaciteJoueur(id, j.moi ? 0.95 : 0.78);
        ctx.fillStyle = j.couleur; ctx.fill(p);
        const bord = bordsTerritoires(deps, possedees).get(id);   // patch335 : le tour, à l'intérieur
        if(bord){
          ctx.save(); ctx.clip(p);
          ctx.globalAlpha = opaciteJoueur(id, 1);
          ctx.strokeStyle = '#07111F'; ctx.lineWidth = trait(3.4); ctx.stroke(bord);
          ctx.restore();
        }""")

# 4. de près, les limites de département bien visibles
rep("""    ctx.strokeStyle = modeContours ? 'rgba(169,188,212,0.16)' : 'rgba(169,188,212,0.28)';
    ctx.lineWidth = trait(0.9);
    ctx.stroke(f.fDept);""", """    if(modeContours){   // patch335 : nettes de près, un trait clair sur un liseré sombre
      ctx.strokeStyle = 'rgba(7,17,31,0.55)'; ctx.lineWidth = trait(3.6); ctx.stroke(f.fDept);
      ctx.strokeStyle = 'rgba(214,230,246,0.62)'; ctx.lineWidth = trait(1.5); ctx.stroke(f.fDept);
    } else {
      ctx.strokeStyle = 'rgba(169,188,212,0.28)'; ctx.lineWidth = trait(0.9); ctx.stroke(f.fDept);
    }""")

F.write_text(s, encoding='utf-8')
print('patch335 appliqué')
