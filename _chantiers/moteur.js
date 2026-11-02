// =====================================================================
//  Grands chantiers — moteur des dessins en pixel art
//  Une scène de 192 x 108 pixels, agrandie sans lissage. Chaque monument
//  est peint avec des formes simples (rectangles, polygones, arcs) dans des
//  « matières » (pierre, ardoise, or…). Le moteur ajoute seul les contours,
//  les joints, les ombres, le plan bleu des parties pas encore bâties,
//  l'échafaudage, la grue, les ouvriers et, une fois restauré, les visiteurs.
// =====================================================================
const PW = 192, PH = 108, SOL = 90;

function bruit(x, y) {
  let h = (x * 374761393 + y * 668265263) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

// ---------------------------------------------------------------- matières
// rampe : 6 teintes, de la plus claire à la plus sombre ; trait : le contour
const MATIERES = [null];
const PAR_NOM = {};
function matiere(nom, rampe, trait, tex, opts) {
  const m = Object.assign({ nom: nom, rampe: rampe, trait: trait, tex: tex, z: 1, contour: true }, opts || {});
  m.id = MATIERES.length;
  MATIERES.push(m);
  PAR_NOM[nom] = m;
}
matiere('tuffeau', ['#FFFDF6', '#F6EFDC', '#E5DAC0', '#CBBC98', '#A69873', '#7B6F52'], '#4A4232', 'pierre');
matiere('calcaire', ['#FFF7E4', '#EFE2C1', '#DAC69C', '#BCA478', '#987F55', '#6F5A3A'], '#463722', 'pierre');
matiere('pierre', ['#FBE3AE', '#EBC98A', '#D4AC69', '#B0884A', '#8A6634', '#634722'], '#3B2A14', 'pierre');
matiere('granit', ['#E4E3DE', '#C9C7C0', '#ABA9A1', '#8A877F', '#6A6861', '#4C4A45'], '#2B2A27', 'brut');
matiere('gres', ['#EFE2C8', '#D9C7A5', '#BFAA85', '#9E8A68', '#7C6A4F', '#5A4C38'], '#352C1F', 'brut');
matiere('brique', ['#F2A47E', '#D97D57', '#BC6040', '#97472E', '#723321', '#4F2316'], '#341409', 'brique');
matiere('ardoise', ['#A9B6CA', '#8391A8', '#68758C', '#505B71', '#3B4457', '#283040'], '#161B26', 'ardoise');
matiere('plomb', ['#C5CDD8', '#A2ACB9', '#848F9E', '#697483', '#525B68', '#3C434E'], '#22272F', 'lisse');
matiere('tuile', ['#F4A673', '#DE8551', '#C46A3A', '#A0522A', '#7C3E1F', '#582B14'], '#3A1A0B', 'tuile');
matiere('cuivre', ['#B8F0DA', '#86D3B6', '#5EB596', '#438F75', '#2F6B56', '#1F4A3B'], '#12302A', 'lisse');
matiere('or', ['#FFF6C2', '#FFE27A', '#F5C33B', '#D49A17', '#A9740C', '#7A5106'], '#4D3203', 'or', { z: 2 });
matiere('fer', ['#C8A47E', '#A8845E', '#8B6946', '#6E5135', '#543C27', '#3B2A1B'], '#24180E', 'lisse');
matiere('treillis', ['#C8A47E', '#A8845E', '#8B6946', '#6E5135', '#543C27', '#3B2A1B'], '#24180E', 'plat', { contour: false });
matiere('acier', ['#FFFFFF', '#EEF2F7', '#D6DEE8', '#B6C2D0', '#93A0B2', '#6C788B'], '#3E4858', 'lisse');
matiere('cable', ['#E9EEF4', '#D6DEE8', '#C2CCD8', '#A9B5C4', '#8E9AAB', '#6E7A8C'], '#6E7A8C', 'plat', { contour: false });
matiere('blanc', ['#FFFFFF', '#F4F1EA', '#E2DDD1', '#C8C1B1', '#A69F8D', '#807A6A'], '#3F3C37', 'enduit');
matiere('rocher', ['#CFC3A9', '#B3A68B', '#988B71', '#7C7058', '#615743', '#473F30'], '#2B261C', 'roche');
matiere('bois', ['#D9A066', '#B57F47', '#956336', '#774C27', '#5A381B', '#3F2611'], '#2A1909', 'bois');
matiere('feuille', ['#A6D86E', '#7DBA4B', '#5E9A37', '#467A29', '#325A1E', '#223F15'], '#162B0D', 'feuille');
matiere('lame', ['#956336', '#774C27', '#5A381B', '#4A2E16', '#3F2611', '#2E1C0C'], '#1F1308', 'plat', { plan: false });
matiere('vitre', ['#FFF8CC', '#FFE68E', '#FFCD5E', '#F2A93F', '#C98329', '#9A5F19'], '#4A2E0E', 'vitre', { z: 0 });
matiere('noir', ['#3B4354', '#2D3442', '#232936', '#1B202B', '#141820', '#0E1117'], '#0B0D12', 'plat', { z: 0 });
matiere('bleu', ['#7FA8F0', '#4F7FD9', '#3563BE', '#284D98', '#1D3A74', '#142852'], '#0E1C3A', 'lisse');
matiere('rouge', ['#FF8C8C', '#EF5350', '#D43B3B', '#A92C2C', '#7E2020', '#561515'], '#3A0D0D', 'lisse');
matiere('vitrail', ['#9FD0FF', '#5FA8F5', '#3F7FD6', '#2F5FB0', '#23478A', '#183163'], '#0E2042', 'vitrail', { z: 0 });

const VARIANTES = { '': 0, h: 1, o: 2, oo: 3 };
const DECALAGE = [0, -1, 1, 2];
const CODES = {};
function code(s) {
  if (s === null) return 0;   // null : on efface (une arche ajourée, un vide)
  let c = CODES[s];
  if (c !== undefined) return c;
  const p = s.split('.'), m = PAR_NOM[p[0]];
  if (!m) throw new Error('matière inconnue : ' + s);
  c = (m.id << 2) | VARIANTES[p[1] || ''];
  CODES[s] = c;
  return c;
}

// ---------------------------------------------------------------- le peintre
function Peintre() {
  const buf = new Uint16Array(PW * PH);
  const mettre = function (x, y, c) { if (x >= 0 && y >= 0 && x < PW && y < PH) buf[y * PW + x] = c; };
  const g = {
    buf: buf,
    px: function (x, y, m) { mettre(Math.floor(x), Math.floor(y), code(m)); },
    rect: function (x, y, w, h, m) {
      const c = code(m);
      for (let j = Math.floor(y); j < y + h; j++) for (let i = Math.floor(x); i < x + w; i++) mettre(i, j, c);
    },
    // polygone : un pixel est rempli si son centre est dedans
    poly: function (pts, m) {
      const c = code(m);
      let y0 = Infinity, y1 = -Infinity;
      for (let k = 0; k < pts.length; k++) { y0 = Math.min(y0, pts[k][1]); y1 = Math.max(y1, pts[k][1]); }
      for (let y = Math.floor(y0); y <= Math.ceil(y1); y++) {
        const yc = y + 0.5, xs = [];
        for (let k = 0; k < pts.length; k++) {
          const a = pts[k], b = pts[(k + 1) % pts.length];
          if ((a[1] <= yc && b[1] > yc) || (b[1] <= yc && a[1] > yc)) xs.push(a[0] + (yc - a[1]) * (b[0] - a[0]) / (b[1] - a[1]));
        }
        xs.sort(function (p, q) { return p - q; });
        for (let k = 0; k + 1 < xs.length; k += 2)
          for (let x = Math.ceil(xs[k] - 0.5); x < Math.ceil(xs[k + 1] - 0.5); x++) mettre(x, y, c);
      }
    },
    ellipse: function (cx, cy, rx, ry, m) {
      const c = code(m);
      for (let y = Math.floor(cy - ry); y <= Math.ceil(cy + ry); y++)
        for (let x = Math.floor(cx - rx); x <= Math.ceil(cx + rx); x++) {
          const dx = (x + 0.5 - cx) / rx, dy = (y + 0.5 - cy) / ry;
          if (dx * dx + dy * dy <= 1) mettre(x, y, c);
        }
    },
    // arc en plein cintre : demi-cercle de centre (cx, yc) et de rayon r, puis droit jusqu'à « bas »
    arche: function (cx, yc, r, bas, m) {
      const c = code(m);
      for (let y = Math.floor(yc - r); y < bas; y++)
        for (let x = Math.floor(cx - r); x <= Math.ceil(cx + r); x++) {
          const dx = x + 0.5 - cx, dy = y + 0.5 - yc;
          if (Math.abs(dx) <= r && (dy >= 0 || dx * dx + dy * dy <= r * r)) mettre(x, y, c);
        }
    },
    // arc brisé (gothique) : deux cercles de rayon k*r qui se croisent au sommet
    ogive: function (cx, yc, r, bas, m, k) {
      const c = code(m), R = (k || 1.5) * r, d = R - r;
      const sommet = Math.sqrt(R * R - d * d);
      for (let y = Math.floor(yc - sommet - 1); y < bas; y++)
        for (let x = Math.floor(cx - r); x <= Math.ceil(cx + r); x++) {
          const dx = x + 0.5 - cx, dy = y + 0.5 - yc;
          if (Math.abs(dx) > r) continue;
          if (dy >= 0 || ((dx + d) * (dx + d) + dy * dy <= R * R && (dx - d) * (dx - d) + dy * dy <= R * R)) mettre(x, y, c);
        }
    },
    ligne: function (x0, y0, x1, y1, m) {
      const c = code(m);
      x0 = Math.round(x0); y0 = Math.round(y0); x1 = Math.round(x1); y1 = Math.round(y1);
      const dx = Math.abs(x1 - x0), dy = -Math.abs(y1 - y0), sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
      let e = dx + dy;
      for (;;) {
        mettre(x0, y0, c);
        if (x0 === x1 && y0 === y1) break;
        const e2 = 2 * e;
        if (e2 >= dy) { e += dy; x0 += sx; }
        if (e2 <= dx) { e += dx; y0 += sy; }
      }
    },
    // toit conique ou flèche : triangle de base [cx-demi, cx+demi] et de sommet (cx, haut)
    cone: function (cx, bas, demi, haut, m) {
      g.poly([[cx - demi, bas], [cx + demi, bas], [cx, haut]], m);
    },
    creneaux: function (x, y, w, h, m, merlon, creux) {
      merlon = merlon || 3; creux = creux || 2;
      for (let i = x; i < x + w; i += merlon + creux) g.rect(i, y, Math.min(merlon, x + w - i), h, m);
    },
    // fenêtre à croisée : vitre avec meneau et traverse dans la matière du mur
    croisee: function (x, y, w, h, mur) {
      g.rect(x, y, w, h, 'vitre');
      if (w >= 5) g.rect(x + Math.floor(w / 2), y, 1, h, mur);
      if (h >= 7) g.rect(x, y + Math.floor(h * 0.4), w, 1, mur);
    },
    get: function (x, y) { return (x >= 0 && y >= 0 && x < PW && y < PH) ? buf[y * PW + x] : 0; }
  };
  return g;
}

// ---------------------------------------------------------------- texture et lumière
function texture(m, x, y, R) {
  const n = bruit(x, y);
  switch (m.tex) {
    case 'pierre': {
      const rang = Math.floor(y / 4);
      if (y % 4 === 3) return R(2);
      if ((x + (rang & 1) * 4) % 8 === 0) return R(2);
      return n < 0.06 ? R(0) : (n > 0.92 ? R(2) : R(1));
    }
    case 'brut': {
      const rang = Math.floor(y / 3), dec = Math.floor(bruit(rang, 7) * 5);
      if (y % 3 === 2) return R(2);
      if ((x + dec) % 6 === 0) return R(2);
      const cel = bruit(Math.floor((x + dec) / 6), rang);
      return cel < 0.22 ? R(2) : (n < 0.07 ? R(0) : R(1));
    }
    case 'roche': {
      const b = bruit(x >> 2, y >> 1), b2 = bruit((x + 2) >> 2, (y + 1) >> 2);
      return b < 0.18 ? R(3) : (b2 < 0.35 ? R(2) : (n < 0.1 ? R(0) : R(1)));
    }
    case 'brique': {
      if (y % 3 === 2) return R(3);
      if ((x + (Math.floor(y / 3) & 1) * 2) % 4 === 0) return R(3);
      return n < 0.3 ? R(2) : R(1);
    }
    case 'ardoise': {
      if (y % 2 === 1) return R(2);
      return (x + (Math.floor(y / 2) & 1) * 2) % 4 === 0 ? R(3) : R(1);
    }
    case 'tuile': {
      if (y % 3 === 0) return R(3);
      return (x + Math.floor(y / 3)) % 2 ? R(1) : R(2);
    }
    case 'or': return n < 0.08 ? R(0) : (n < 0.35 ? R(1) : R(2));
    case 'vitre': return n < 0.22 ? R(2) : R(1);
    case 'vitrail': return n < 0.3 ? R(1) : (n < 0.55 ? R(3) : R(2));
    case 'plat': return R(2);
    case 'bois': return x % 3 === 0 ? R(3) : (n < 0.3 ? R(2) : R(1));
    case 'feuille': { const b = bruit(x >> 1, y >> 1); return b < 0.25 ? R(0) : (b < 0.6 ? R(1) : (b < 0.85 ? R(2) : R(3))); }
    case 'enduit': return n < 0.05 ? R(0) : (n > 0.94 ? R(2) : R(1));
    default: return n < 0.04 ? R(0) : R(1);
  }
}

const PLAN_TRAIT = '#5AA9FF', PLAN_POINT = '#1F4A80';

// calcule, une fois par dessin, la couleur « bâtie » et la couleur « plan » de chaque pixel
function preparer(d) {
  const g = Peintre();
  d.peindre(g);
  const buf = g.buf;
  const bati = new Array(PW * PH), plan = new Array(PW * PH);
  let haut = PH, gauche = PW, droite = 0;
  const z = function (c) { return c ? MATIERES[c >> 2].z : -1; };
  for (let y = 0; y < PH; y++) for (let x = 0; x < PW; x++) {
    const i = y * PW + x, c = buf[i];
    if (!c) continue;
    if (y < haut) haut = y;
    if (x < gauche) gauche = x;
    if (x > droite) droite = x;
    const m = MATIERES[c >> 2], k = DECALAGE[c & 3], id = c >> 2;
    const R = function (n) { return m.rampe[Math.max(0, Math.min(5, n + k))]; };
    const H = y > 0 ? buf[i - PW] : 0, B = y < PH - 1 ? buf[i + PW] : 0;
    const G = x > 0 ? buf[i - 1] : 0, D = x < PW - 1 ? buf[i + 1] : 0;
    let col = texture(m, x, y, R);
    if (m.contour && (!H || !B || !G || !D)) col = m.trait;
    else if (m.z >= 1) {
      if (H && (H >> 2) !== id && z(H) >= 1) col = R(3);                 // ombre sous une avancée
      else if ((B && (B >> 2) !== id && z(B) >= 1) || (D && (D >> 2) !== id && z(D) >= 1)) col = R(3);
      else if ((G && z(G) === 0) || (H && z(H) === 0)) col = R(0);         // tableau éclairé d'une ouverture
    } else {
      if ((H && z(H) >= 1) || (G && z(G) >= 1)) col = R(4);               // ombre dans l'ouverture
    }
    bati[i] = col;
    // le plan : un trait d'un pixel à chaque arête (côté du mur pour une ouverture) ;
    // les détails « plan: false » (lames, barreaux) se fondent dans leur ouverture
    const cle = function (c2) {
      if (!c2) return 0;
      if (MATIERES[c2 >> 2].plan === false) return code('noir');
      return ((c2 >> 2) << 2) | ((c2 & 3) === 1 ? 0 : (c2 & 3));
    };
    const zp = function (c2) { return MATIERES[c2 >> 2].plan === false ? 0 : z(c2); };
    const k0 = cle(c), z0 = zp(c);
    const bord = !H || !B || !G || !D
      || (cle(H) !== k0 && zp(H) <= z0) || (cle(G) !== k0 && zp(G) <= z0)
      || (cle(B) !== k0 && zp(B) < z0) || (cle(D) !== k0 && zp(D) < z0);
    plan[i] = (bord && z0 >= 1) || (!H || !B || !G || !D) ? PLAN_TRAIT : ((x + y) % 4 === 0 && z0 >= 1 ? PLAN_POINT : null);
  }
  return { d: d, buf: buf, bati: bati, plan: plan, haut: haut, gauche: gauche, droite: droite };
}

// ---------------------------------------------------------------- couleurs
const CACHE_RGB = {};
function rgb(h) {
  let v = CACHE_RGB[h];
  if (!v) { v = [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]; CACHE_RGB[h] = v; }
  return v;
}
function melange(a, b, t) {
  const p = rgb(a), q = rgb(b);
  return 'rgb(' + Math.round(p[0] + (q[0] - p[0]) * t) + ',' + Math.round(p[1] + (q[1] - p[1]) * t) + ',' + Math.round(p[2] + (q[2] - p[2]) * t) + ')';
}

// ---------------------------------------------------------------- le sol
function eauEn(sol, x) {
  if (!sol.eau) return false;
  for (let k = 0; k < sol.eau.length; k++) if (x >= sol.eau[k][0] && x <= sol.eau[k][1]) return true;
  return false;
}
function couleurSol(sol, x, y, t) {
  const n = bruit(x, y), j = y - SOL;
  const type = sol.type;
  if (eauEn(sol, x) && j >= (sol.berge || 0)) {
    if (bruit(x + Math.floor(t / 420), y) < 0.025) return '#A8DEF8';
    return ((x + y) & 1) ? '#2B74AA' : '#226495';
  }
  if (type === 'pave') {
    if (j === 0) return '#6E675C';
    const rang = Math.floor((j - 1) / 3);
    if ((j - 1) % 3 === 2 || (x + (rang & 1) * 2) % 5 === 0) return '#5B554C';
    return n < 0.4 ? '#A49C8D' : '#958D7E';
  }
  if (type === 'roche') {
    if (j === 0) return '#4A4640';
    const b = bruit(x >> 1, y >> 1);
    return b < 0.3 ? '#5C5853' : (n < 0.5 ? '#6E6A64' : '#7C776F');
  }
  if (type === 'sable') {
    if (bruit(x >> 2, y) < 0.08) return '#7FB3C9';
    return n < 0.5 ? '#D9C79E' : '#CDBB92';
  }
  if (type === 'jardin') {
    const dx = Math.abs(x + 0.5 - 96);
    if (j <= 1) return ((x + y) & 1) ? '#6E9A36' : '#557A27';
    if (dx < 16 + j * 1.5) return n < 0.5 ? '#E2D6B8' : '#D3C6A5';              // l'allée
    if ((x % 12 === 0) || (j % 6 === 3)) return '#2F5A1C';                      // les buis
    return ((x + y) & 1) ? '#5E9A37' : '#4E8530';
  }
  // herbe (par défaut)
  if (j <= 1) return ((x + y) & 1) ? '#6E9A36' : '#557A27';
  if (j === 2 && n < 0.3) return '#557A27';
  return n < 0.07 ? '#5A4020' : (((x + y) & 1) ? '#8E6C38' : '#7A5A2E');
}

// ---------------------------------------------------------------- personnages
const OUVRIER = [
  ['.YYY..', 'YYYYY.', '.SSS..', 'OOOOO.', 'SOOOS.', '.OOO..', '.B.B..', '.B.B..'],
  ['.YYY.G', 'YYYYYG', '.SSS.S', 'OOOOOO', 'SOOO..', '.OOO..', '.B.B..', '.B.B..']
];
function sprite(ctx, s, x, y, couleurs) {
  for (let r = 0; r < s.length; r++) for (let k = 0; k < s[r].length; k++) {
    const ch = s[r][k];
    if (ch === '.') continue;
    ctx.fillStyle = couleurs[ch];
    ctx.fillRect(x + k, y + r, 1, 1);
  }
}
function dessinerOuvrier(ctx, x, y, cadre, casque) {
  sprite(ctx, OUVRIER[cadre], x, y, { Y: casque, S: '#F2C79A', O: '#FF8A2B', B: '#2B4A7A', G: '#AEB6C0' });
}
// visiteurs : cheveux, peau, haut, jambes ; deux pas
const VISITEUR = [
  ['.HH.', 'HSS.', '.SS.', 'CCCC', 'SCCS', '.CC.', '.L.L', '.L.L'],
  ['.HH.', 'HSS.', '.SS.', 'CCCC', 'SCCS', '.CC.', '.LL.', 'L..L']
];
const HAUTS = ['#E5484D', '#3E7CF0', '#F0B429', '#2BB673', '#C45BD6', '#FFFFFF', '#1ABC9C', '#FF8A2B'];
const CHEVEUX = ['#3B2A1B', '#6B4423', '#E8C26A', '#1B1B1B', '#A0522D', '#D9D9D9'];
const PEAUX = ['#F2C79A', '#E0AC7E', '#B57E55', '#8A5A3B'];

// ---------------------------------------------------------------- la scène
// etat : { pct 0..1, fini, ouvriers, bonus, visiteurs, casques[] }
function creerScene() {
  let prep = null, parts = [], gens = [];
  const vis = new Array(PW * PH);
  return function dessiner(ctx, d, etat, t) {
    if (!prep || prep.d !== d) { prep = preparer(d); gens = []; }
    const sol = d.sol || { type: 'herbe' };
    ctx.clearRect(0, 0, PW, PH);
    vis.fill(null);
    const p = Math.max(0, Math.min(1, etat.pct));
    const bas = SOL + (d.fondation || 0);
    const niveau = bas - p * (bas - prep.haut);
    const ligne = Math.floor(niveau), frac = niveau - ligne;
    for (let y = prep.haut; y < PH; y++) for (let x = prep.gauche; x <= prep.droite; x++) {
      const i = y * PW + x;
      if (!prep.buf[i]) continue;
      let c;
      if (etat.fini || y > ligne || (y === ligne && bruit(x, y) > frac)) c = prep.bati[i];
      else c = prep.plan[i];
      if (c) { vis[i] = c; ctx.fillStyle = c; ctx.fillRect(x, y, 1, 1); }
    }
    // le sol (et le reflet dans l'eau)
    for (let y = SOL; y < PH; y++) for (let x = 0; x < PW; x++) {
      if (prep.buf[y * PW + x]) continue;
      let c = couleurSol(sol, x, y, t);
      if (eauEn(sol, x) && y - SOL >= (sol.berge || 0)) {
        const ym = 2 * SOL - y - 1 + Math.round(Math.sin((y + t / 300) * 0.9) * 0.6);
        const xm = x + (((y + Math.floor(t / 250)) & 3) === 0 ? 1 : 0);
        const r = ym >= 0 && xm < PW ? vis[ym * PW + xm] : null;
        if (r && r.charAt(0) === '#' && r !== PLAN_TRAIT && r !== PLAN_POINT) c = melange(r, '#1E5F90', 0.55);
      }
      ctx.fillStyle = c; ctx.fillRect(x, y, 1, 1);
    }
    if (d.deco) d.deco(ctx, t, etat);

    const n = etat.ouvriers || 0;
    const g0 = Math.max(4, prep.gauche - 4), d0 = Math.min(PW - 5, prep.droite + 4);
    if (!etat.fini && n > 0) {
      const planche = Math.min(SOL - 1, ligne + 1);
      const haut = Math.max(2, planche - 13);
      ctx.fillStyle = '#7A4E22';
      for (let x = g0 + 2; x < d0; x += 22) ctx.fillRect(x, haut, 1, Math.min(SOL, planche + 13) - haut);
      for (let x = g0; x <= d0; x++) {
        ctx.fillStyle = (x & 3) ? '#B07A3C' : '#8A5A2B';
        ctx.fillRect(x, planche, 1, 1);
        if (planche - 12 > haut) ctx.fillRect(x, planche - 12, 1, 1);
      }
      // la grue, à droite du chantier
      const mat = Math.min(PW - 3, d0 + 2), sommet = Math.max(2, Math.min(prep.haut - 4, haut - 4));
      ctx.fillStyle = '#F0B429';
      for (let y = sommet; y < SOL; y++) if (y % 4) ctx.fillRect(mat, y, 1, 1); else { ctx.fillRect(mat - 1, y, 3, 1); }
      for (let x = mat - 20; x <= mat + 3; x++) ctx.fillRect(x, sommet, 1, 1);
      ctx.fillStyle = '#3B4354'; ctx.fillRect(mat + 2, sommet + 1, 2, 2);
      const bout = mat - 19, cycle = (t / 2600) % 1;
      const yb = Math.round(sommet + 3 + (SOL - 5 - sommet - 3) * (cycle < 0.5 ? 1 - cycle * 2 : (cycle - 0.5) * 2));
      ctx.fillStyle = '#D9D2C0';
      for (let y = sommet + 1; y < yb; y++) ctx.fillRect(bout, y, 1, 1);
      ctx.fillStyle = '#B48A4C'; ctx.fillRect(bout - 1, yb, 3, 3);
      const casques = etat.casques || [];
      for (let k = 0; k < n; k++) {
        const base = n > 1 ? g0 + 8 + k * ((d0 - g0 - 22) / (n - 1)) : (g0 + d0) / 2;
        const x = Math.round(base + Math.sin(t / 900 + k * 1.7) * 3);
        const cadre = Math.floor(t / 260 + k) % 2;
        dessinerOuvrier(ctx, x, planche - 8, cadre, casques[k] || (k === n - 1 && etat.bonus ? '#FFFFFF' : '#F0B429'));
        if (cadre === 1 && bruit(k, Math.floor(t / 260)) < 0.6)
          parts.push({ x: x + 5, y: planche - 7, vx: (bruit(k, Math.floor(t)) - 0.5) * 1.2, vy: -0.7, vie: 7 });
      }
    } else if (etat.fini && n > 0) {
      for (let k = 0; k < n; k++) {
        const x = Math.round(g0 + 10 + k * ((d0 - g0 - 26) / Math.max(1, n - 1)));
        const saut = Math.floor(t / 300 + k) % 2 ? 2 : 0;
        dessinerOuvrier(ctx, x, SOL - 8 - saut, 0, '#F0B429');
      }
      for (let k = 0; k < 4; k++) {
        const r = bruit(k, Math.floor(t / 180));
        parts.push({ x: prep.gauche + r * (prep.droite - prep.gauche), y: prep.haut + bruit(Math.floor(t / 180), k) * (SOL - prep.haut), vx: 0, vy: -0.2, vie: 5 });
      }
    }
    // les visiteurs d'un monument restauré
    if (etat.fini && etat.visiteurs) {
      const zone = d.promenade || [8, PW - 12];
      while (gens.length < etat.visiteurs) {
        const k = gens.length;
        gens.push({ x: zone[0] + bruit(k, 3) * (zone[1] - zone[0]), v: (bruit(k, 5) < 0.5 ? -1 : 1) * (0.012 + bruit(k, 9) * 0.01),
          haut: HAUTS[k % HAUTS.length], cheveux: CHEVEUX[(k * 7) % CHEVEUX.length], peau: PEAUX[(k * 3) % PEAUX.length], photo: bruit(k, 11) < 0.4 });
      }
      for (let k = 0; k < etat.visiteurs; k++) {
        const q = gens[k];
        let x = q.x + q.v * t;
        const L = zone[1] - zone[0];
        x = ((x - zone[0]) % (2 * L) + 2 * L) % (2 * L);
        const sens = x > L ? -1 : 1;
        x = zone[0] + (x > L ? 2 * L - x : x);
        const cadre = Math.floor(t / 220 + k) % 2;
        const s = sens * Math.sign(q.v) > 0 ? VISITEUR[cadre] : VISITEUR[cadre].map(function (r) { return r.split('').reverse().join(''); });
        sprite(ctx, s, Math.round(x), SOL - 7, { H: q.cheveux, S: q.peau, C: q.haut, L: '#2B3A55' });
        if (q.photo && Math.floor(t / 90 + k * 13) % 37 === 0) { ctx.fillStyle = '#FFFFFF'; ctx.fillRect(Math.round(x) + (sens > 0 ? 4 : -1), SOL - 6, 1, 1); }
      }
    }
    const restes = [];
    for (let k = 0; k < parts.length; k++) {
      const q = parts[k];
      q.x += q.vx; q.y += q.vy; q.vy += 0.12; q.vie--;
      if (q.vie <= 0) continue;
      ctx.fillStyle = (q.vie & 1) ? '#FFE08A' : '#FFFFFF';
      ctx.fillRect(Math.round(q.x), Math.round(q.y), 1, 1);
      restes.push(q);
    }
    parts = restes.slice(-120);
  };
}
