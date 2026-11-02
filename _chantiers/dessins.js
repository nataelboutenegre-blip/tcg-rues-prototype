// =====================================================================
//  Grands chantiers — les dessins (192 x 108, sol à y = 90)
//  8 types de monuments + Cordouan, Ronchamp et les 10 merveilles.
// =====================================================================

// ---------------------------------------------------------------- aides
// tour ronde : ombre à droite, reflet à gauche
function cylindre(g, x, y, w, h, m) {
  g.rect(x, y, w, h, m);
  const o = Math.round(w * 0.64);
  g.rect(x + o, y, w - o, h, m + '.o');
  if (w >= 8) g.rect(x + Math.round(w * 0.2), y, Math.max(1, Math.round(w * 0.14)), h, m + '.h');
}
// toit conique : pan droit dans l'ombre
function toitCone(g, cx, bas, demi, haut, m) {
  g.poly([[cx - demi, bas], [cx + demi, bas], [cx, haut]], m);
  g.poly([[cx + demi * 0.25, bas], [cx + demi, bas], [cx, haut]], m + '.o');
}
// lucarne à pignon
function lucarne(g, cx, bas, w, h, mur, fen) {
  const x = cx - Math.floor(w / 2);
  g.rect(x, bas - h, w, h, mur);
  g.poly([[x - 1, bas - h + 1], [x + w + 1, bas - h + 1], [cx + 0.5, bas - h - Math.ceil(w * 0.75)]], mur);
  g.croisee(x + 2, bas - h + 3, w - 4, h - 4, fen || mur);
  g.px(cx, bas - h - Math.ceil(w * 0.75) - 1, mur);
}
// rose de cathédrale
function rose(g, cx, cy, r, mur) {
  g.ellipse(cx, cy, r + 1.4, r + 1.4, mur + '.o');
  g.ellipse(cx, cy, r, r, 'vitrail');
  for (let k = 0; k < 12; k++) {
    const a = k * Math.PI / 6;
    g.ligne(cx + Math.cos(a) * 2, cy + Math.sin(a) * 2, cx + Math.cos(a) * (r - 0.5), cy + Math.sin(a) * (r - 0.5), mur + '.o');
  }
  g.ellipse(cx, cy, r * 0.5, r * 0.5, 'vitrail');
  for (let k = 0; k < 6; k++) {
    const a = k * Math.PI / 3 + Math.PI / 6;
    g.px(cx + Math.cos(a) * r * 0.5 - 0.5, cy + Math.sin(a) * r * 0.5 - 0.5, mur + '.o');
  }
  g.ellipse(cx, cy, 1.6, 1.6, mur);
}
// cheminée
function cheminee(g, x, haut, bas, mur) {
  g.rect(x, haut, 4, bas - haut, mur);
  g.rect(x + 3, haut, 1, bas - haut, mur + '.o');
  g.rect(x - 1, haut - 1, 6, 2, mur + '.h');
}
// arbre (décor, toujours visible) : cyprès ou arbre rond
function arbre(ctx, x, h, rond) {
  for (let y = 0; y < h; y++) {
    const t = y / h;
    const demi = rond ? Math.sqrt(Math.max(0, 1 - Math.pow((t - 0.45) / 0.55, 2))) * h * 0.42 : Math.sin(Math.min(1, t * 1.15) * Math.PI) * 3.2 + 0.6;
    for (let dx = -Math.ceil(demi); dx <= Math.ceil(demi); dx++) {
      if (Math.abs(dx) > demi) continue;
      const n = bruit(x + dx, y + h);
      ctx.fillStyle = dx > demi * 0.3 ? (n < 0.5 ? '#325A1E' : '#2A4E18') : (n < 0.25 ? '#7DBA4B' : (n < 0.7 ? '#5E9A37' : '#467A29'));
      ctx.fillRect(x + dx, SOL - h + y - 1, 1, 1);
    }
  }
  ctx.fillStyle = '#5A3B1E';
  ctx.fillRect(x, SOL - 2, 1, 2);
}

const DESSINS = {};

// =============================================================== LES TYPES

// ---------------------------------------------------- château Renaissance
DESSINS.chateau = {
  nom: 'Château Renaissance', sol: { type: 'herbe' }, promenade: [8, 178],
  peindre: function (g) {
    // corps de logis et son grand toit
    g.rect(46, 47, 100, 43, 'tuffeau');
    g.poly([[43, 48], [149, 48], [136, 22], [56, 22]], 'ardoise');
    g.poly([[118, 48], [149, 48], [136, 22], [124, 22]], 'ardoise.o');
    g.rect(44, 46, 104, 2, 'tuffeau.h');
    cheminee(g, 62, 10, 23, 'tuffeau');
    cheminee(g, 126, 10, 23, 'tuffeau');
    [70, 88, 106, 124].forEach(function (cx) { lucarne(g, cx, 46, 9, 13, 'tuffeau'); });
    // deux étages de fenêtres à croisée
    g.rect(46, 66, 100, 1, 'tuffeau.o');
    [54, 68, 82, 104, 118, 132].forEach(function (x) {
      g.croisee(x, 52, 6, 10, 'tuffeau');
      g.croisee(x, 71, 6, 10, 'tuffeau');
    });
    // porte
    g.arche(96, 80, 5, 90, 'tuffeau.h');
    g.arche(96, 81, 3.5, 90, 'bois.o');
    // les deux tours rondes
    [26, 146].forEach(function (x) {
      cylindre(g, x, 42, 20, 48, 'tuffeau');
      for (let i = x - 1; i < x + 21; i += 3) g.rect(i, 40, 2, 3, 'tuffeau.h');
      g.rect(x - 1, 38, 22, 2, 'tuffeau.h');
      toitCone(g, x + 10, 38, 13, 6, 'ardoise');
      g.rect(x + 10, 2, 1, 5, 'or');
      g.px(x + 9, 3, 'or'); g.px(x + 11, 3, 'or');
      g.croisee(x + 6, 52, 6, 9, 'tuffeau');
      g.croisee(x + 6, 70, 6, 9, 'tuffeau');
    });
  }
};

// ---------------------------------------------------- château fort
DESSINS.fort = {
  nom: 'Château fort', sol: { type: 'herbe' }, promenade: [6, 182],
  peindre: function (g) {
    // courtine
    g.rect(34, 58, 124, 32, 'granit');
    g.creneaux(34, 53, 124, 5, 'granit', 4, 3);
    g.rect(34, 58, 124, 1, 'granit.o');
    // donjon carré : face éclairée et face dans l'ombre
    g.rect(74, 20, 34, 70, 'granit');
    g.rect(108, 23, 10, 67, 'granit.o');
    for (let x = 72; x < 120; x += 4) g.rect(x, 18, 3, 4, 'granit.h');
    g.rect(72, 14, 48, 4, 'granit');
    g.creneaux(72, 9, 48, 5, 'granit', 4, 3);
    // fenêtres et archères
    g.arche(85, 32, 2.5, 40, 'noir'); g.arche(97, 32, 2.5, 40, 'noir');
    g.arche(91, 50, 2.5, 58, 'noir');
    [80, 102].forEach(function (x) { g.rect(x, 46, 1, 7, 'noir'); g.rect(x - 1, 49, 3, 1, 'noir'); });
    [46, 60, 132, 146].forEach(function (x) { g.rect(x, 66, 1, 7, 'noir'); g.rect(x - 1, 69, 3, 1, 'noir'); });
    // porte et herse
    g.arche(91, 76, 8, 90, 'granit.h');
    g.arche(91, 77, 6.5, 90, 'noir');
    for (let x = 86; x <= 96; x += 3) g.rect(x, 71, 1, 13, 'lame');
    for (let y = 74; y <= 82; y += 4) g.rect(85, y, 13, 1, 'lame');
    // les deux tours rondes
    [16, 152].forEach(function (x) {
      cylindre(g, x, 42, 24, 48, 'granit');
      for (let i = x - 2; i < x + 26; i += 3) g.rect(i, 40, 2, 3, 'granit.h');
      g.rect(x - 2, 36, 28, 4, 'granit');
      g.creneaux(x - 2, 31, 28, 5, 'granit', 4, 3);
      g.rect(x + 8, 54, 1, 7, 'noir'); g.rect(x + 7, 57, 3, 1, 'noir');
      g.rect(x + 8, 72, 1, 7, 'noir'); g.rect(x + 7, 75, 3, 1, 'noir');
    });
    // bannière
    g.rect(96, 0, 1, 10, 'bois');
    g.rect(97, 1, 8, 2, 'rouge'); g.rect(97, 3, 8, 2, 'or'); g.rect(97, 5, 6, 1, 'rouge');
  }
};

// ---------------------------------------------------- palais classique
DESSINS.palais = {
  nom: 'Palais classique', sol: { type: 'pave' }, promenade: [6, 180],
  peindre: function (g) {
    g.rect(30, 47, 132, 43, 'calcaire');
    // toit à la Mansart
    g.poly([[27, 48], [165, 48], [160, 37], [152, 30], [40, 30], [32, 37]], 'ardoise');
    g.rect(32, 37, 128, 1, 'ardoise.oo');
    g.rect(28, 46, 136, 2, 'calcaire.h');
    cheminee(g, 48, 22, 31, 'calcaire');
    cheminee(g, 140, 22, 31, 'calcaire');
    [44, 60, 132, 148].forEach(function (cx) {
      g.rect(cx - 3, 37, 7, 9, 'calcaire');
      g.poly([[cx - 4, 38], [cx + 5, 38], [cx + 0.5, 34]], 'calcaire');
      g.ellipse(cx + 0.5, 41.5, 2, 2.4, 'vitre');
    });
    // les ailes : hautes fenêtres cintrées sur deux niveaux
    g.rect(30, 68, 132, 1, 'calcaire.o');
    [35, 45, 55, 65, 121, 131, 141, 151].forEach(function (x) {
      g.rect(x - 1, 52, 8, 1, 'calcaire.h');
      g.arche(x + 3, 56, 3, 66, 'vitre'); g.rect(x + 3, 55, 1, 11, 'calcaire');
      g.arche(x + 3, 75, 3, 86, 'vitre'); g.rect(x + 3, 74, 1, 12, 'calcaire');
    });
    // avant-corps central, colonnes et fronton
    g.rect(76, 42, 40, 48, 'calcaire.h');
    g.poly([[72, 43], [120, 43], [96, 27]], 'calcaire.h');
    g.poly([[80, 41], [112, 41], [96, 31]], 'calcaire.o');
    g.ellipse(96, 37, 2.6, 2.6, 'or');
    g.rect(74, 42, 44, 2, 'calcaire');
    [79, 87, 103, 111].forEach(function (cx) {
      g.rect(cx - 1, 48, 5, 2, 'calcaire');
      g.rect(cx, 50, 3, 34, 'calcaire');
      g.rect(cx + 2, 50, 1, 34, 'calcaire.o');
      g.rect(cx - 1, 84, 5, 2, 'calcaire');
    });
    g.arche(95.5, 56, 3, 66, 'vitre'); g.rect(95, 55, 1, 11, 'calcaire.h');
    g.arche(96, 78, 4.5, 86, 'bois.o');
    // perron
    g.rect(80, 86, 32, 2, 'calcaire.h');
    g.rect(76, 88, 40, 2, 'calcaire.h');
  }
};

// ---------------------------------------------------- cathédrale gothique
DESSINS.cathedrale = {
  nom: 'Cathédrale gothique', sol: { type: 'pave' }, promenade: [4, 184],
  peindre: function (g) {
    [40, 118].forEach(function (x) {
      g.rect(x, 30, 34, 60, 'calcaire');
      g.rect(x + 23, 30, 11, 60, 'calcaire.o');
      // contreforts
      g.rect(x, 30, 4, 60, 'calcaire.h');
      g.rect(x + 30, 30, 4, 60, 'calcaire.oo');
      // baies géminées
      g.ogive(x + 13, 42, 3, 58, 'noir'); g.ogive(x + 21, 42, 3, 58, 'noir');
      g.ogive(x + 17, 64, 2, 70, 'noir');
      // flèche à crochets
      g.poly([[x + 4, 31], [x + 30, 31], [x + 17, 1]], 'calcaire');
      g.poly([[x + 18, 1], [x + 30, 31], [x + 20, 31]], 'calcaire.o');
      for (let y = 6; y < 30; y += 4) {
        const d = (y - 1) * 13 / 30;
        g.px(x + 17 - d - 1, y, 'calcaire'); g.px(x + 17 + d + 1, y, 'calcaire.o');
      }
      g.rect(x + 3, 28, 28, 3, 'calcaire.h');
      // clochetons d'angle
      toitCone(g, x + 2, 29, 2.5, 19, 'calcaire');
      toitCone(g, x + 32, 29, 2.5, 19, 'calcaire');
      // portail latéral
      g.ogive(x + 17, 80, 6, 90, 'calcaire.oo');
      g.ogive(x + 17, 82, 4.5, 90, 'noir');
    });
    // façade centrale et pignon
    g.rect(74, 38, 44, 52, 'calcaire');
    g.poly([[74, 39], [118, 39], [96, 18]], 'calcaire');
    g.ogive(96, 32, 3, 38, 'noir');
    rose(g, 96, 54, 11, 'calcaire');
    // galerie des rois
    g.rect(74, 68, 44, 1, 'calcaire.h');
    for (let x = 76; x < 116; x += 4) g.ogive(x + 1.5, 71, 1.2, 75, 'calcaire.oo');
    g.rect(74, 75, 44, 1, 'calcaire.h');
    // portail central
    g.ogive(96, 82, 10, 90, 'calcaire.oo');
    g.ogive(96, 84, 8, 90, 'noir');
    g.rect(95, 83, 2, 7, 'calcaire');
  }
};

// ---------------------------------------------------- abbaye romane
DESSINS.abbaye = {
  nom: 'Abbaye romane', sol: { type: 'herbe' }, promenade: [6, 182],
  peindre: function (g) {
    // nef haute
    g.rect(28, 50, 112, 14, 'pierre');
    g.poly([[25, 51], [143, 51], [137, 37], [31, 37]], 'tuile');
    // bas-côté et son toit en appentis
    g.rect(26, 69, 116, 21, 'pierre');
    g.poly([[24, 70], [144, 70], [144, 63], [24, 63]], 'tuile');
    // contreforts et baies en plein cintre
    for (let x = 30; x <= 136; x += 13) g.rect(x, 71, 3, 19, 'pierre.h');
    for (let x = 38; x <= 128; x += 13) {
      g.arche(x, 77, 2, 85, 'noir');
      g.arche(x, 55, 1.6, 61, 'noir');
    }
    // clocher de la croisée
    g.rect(102, 18, 22, 33, 'pierre');
    g.rect(115, 18, 9, 33, 'pierre.o');
    g.rect(100, 34, 26, 2, 'pierre.h');
    [107, 115].forEach(function (cx) { g.arche(cx, 24, 2, 32, 'noir'); g.arche(cx, 40, 2, 48, 'noir'); });
    g.rect(100, 16, 26, 2, 'pierre.h');
    g.poly([[99, 17], [127, 17], [113, 3]], 'tuile');
    g.poly([[113, 3], [127, 17], [116, 17]], 'tuile.o');
    // chevet et chapelle rayonnante
    g.rect(140, 58, 18, 32, 'pierre');
    g.rect(150, 58, 8, 32, 'pierre.o');
    g.poly([[138, 59], [160, 59], [141, 45]], 'tuile');
    g.arche(148, 70, 2, 78, 'noir');
    g.rect(156, 72, 12, 18, 'pierre.o');
    g.poly([[154, 73], [170, 73], [157, 65]], 'tuile');
    // façade ouest
    g.rect(16, 44, 12, 46, 'pierre');
    g.poly([[14, 45], [30, 45], [22, 31]], 'pierre');
    g.arche(22, 78, 4, 90, 'noir');
    g.arche(22, 52, 1.6, 58, 'noir');
  },
  deco: function (ctx) { arbre(ctx, 7, 26); arbre(ctx, 182, 22); }
};

// ---------------------------------------------------- monument antique
DESSINS.antique = {
  nom: 'Temple antique', sol: { type: 'herbe' }, promenade: [6, 182],
  peindre: function (g) {
    // podium et escalier
    g.rect(46, 74, 100, 16, 'pierre');
    g.rect(44, 72, 104, 2, 'pierre.h');
    for (let y = 75; y < 90; y += 2) { g.rect(66, y, 60, 1, 'pierre.h'); g.rect(66, y + 1, 60, 1, 'pierre.o'); }
    g.rect(64, 74, 2, 16, 'pierre'); g.rect(126, 74, 2, 16, 'pierre');
    // cella dans l'ombre, et sa porte
    g.rect(52, 40, 88, 32, 'pierre.oo');
    g.arche(96, 54, 7, 72, 'noir');
    // colonnes corinthiennes
    [56, 72, 88, 104, 120, 136].forEach(function (cx) {
      g.rect(cx - 3, 43, 6, 29, 'pierre');
      g.rect(cx + 1, 43, 2, 29, 'pierre.o');
      g.rect(cx - 2, 43, 1, 29, 'pierre.h');
      g.rect(cx - 4, 39, 8, 4, 'pierre.h');
      g.px(cx - 4, 41, 'pierre'); g.px(cx + 3, 41, 'pierre');
      g.rect(cx - 4, 70, 8, 2, 'pierre');
    });
    // entablement et fronton
    g.rect(48, 32, 96, 7, 'pierre');
    g.rect(48, 35, 96, 1, 'pierre.o');
    g.rect(46, 30, 100, 2, 'pierre.h');
    g.poly([[46, 31], [146, 31], [96, 13]], 'pierre');
    g.poly([[56, 29], [136, 29], [96, 17]], 'pierre.o');
    g.rect(94, 10, 5, 3, 'pierre.h');
    g.rect(45, 27, 4, 3, 'pierre.h'); g.rect(143, 27, 4, 3, 'pierre.h');
  },
  deco: function (ctx) { arbre(ctx, 18, 30); arbre(ctx, 172, 26); }
};

// ---------------------------------------------------- église à dôme
DESSINS.dome = {
  nom: 'Église à dôme', sol: { type: 'pave' }, promenade: [6, 182],
  peindre: function (g) {
    // le dôme (le tambour le recouvre en bas)
    g.ellipse(96, 30, 25, 20, 'plomb');
    g.poly([[104, 10], [121, 30], [112, 30]], 'plomb.o');
    for (let k = -2; k <= 2; k++) g.ligne(96 + k * 4, 11 + Math.abs(k), 96 + k * 11, 30, 'plomb.o');
    g.rect(93, 4, 7, 7, 'calcaire');
    g.rect(94, 6, 1, 4, 'noir'); g.rect(98, 6, 1, 4, 'noir');
    g.ellipse(96.5, 4, 4, 2.2, 'plomb');
    g.rect(96, 0, 1, 3, 'or');
    // tambour à colonnade
    g.rect(68, 30, 57, 3, 'calcaire.h');
    g.rect(70, 33, 53, 13, 'noir');
    for (let x = 71; x < 122; x += 4) g.rect(x, 33, 2, 13, 'calcaire');
    g.rect(68, 46, 57, 2, 'calcaire.h');
    // le corps de l'église
    g.rect(34, 52, 124, 38, 'calcaire.o');
    g.rect(32, 50, 128, 2, 'calcaire');
    [42, 54, 138, 150].forEach(function (cx) { g.arche(cx, 64, 2.5, 74, 'noir'); });
    // portique : colonnes et fronton
    g.rect(58, 60, 76, 30, 'noir');
    [62, 74, 86, 102, 114, 126].forEach(function (cx) {
      g.rect(cx, 60, 4, 30, 'calcaire');
      g.rect(cx + 3, 60, 1, 30, 'calcaire.o');
      g.rect(cx - 1, 58, 6, 2, 'calcaire.h');
    });
    g.rect(56, 52, 80, 6, 'calcaire');
    g.rect(56, 55, 80, 1, 'calcaire.o');
    g.poly([[52, 53], [140, 53], [96, 38]], 'calcaire');
    g.poly([[62, 51], [130, 51], [96, 42]], 'calcaire.o');
  }
};

// ---------------------------------------------------- édifice à beffroi
DESSINS.edifice = {
  nom: 'Édifice à beffroi', sol: { type: 'pave' }, promenade: [6, 182],
  peindre: function (g) {
    g.rect(36, 53, 120, 37, 'brique');
    g.poly([[33, 54], [159, 54], [150, 41], [42, 41]], 'ardoise');
    g.poly([[134, 54], [159, 54], [150, 41], [140, 41]], 'ardoise.o');
    g.rect(34, 52, 124, 2, 'calcaire');
    // chaînes d'angle et bandeau
    for (let y = 54; y < 90; y += 4) { g.rect(36, y, 4, 2, 'calcaire'); g.rect(152, y, 4, 2, 'calcaire'); g.rect(36, y + 2, 3, 2, 'calcaire'); g.rect(153, y + 2, 3, 2, 'calcaire'); }
    g.rect(36, 71, 120, 2, 'calcaire');
    // fenêtres encadrées de pierre
    [44, 56, 68, 118, 130, 142].forEach(function (x) {
      g.rect(x - 1, 56, 8, 12, 'calcaire');
      g.croisee(x, 57, 6, 10, 'calcaire');
    });
    // arcades du rez-de-chaussée
    [46, 58, 70, 122, 134, 146].forEach(function (cx) {
      g.arche(cx + 0.5, 80, 5, 90, 'calcaire');
      g.arche(cx + 0.5, 81, 3.5, 90, 'noir');
    });
    [52, 76, 116, 140].forEach(function (cx) { lucarne(g, cx, 52, 7, 9, 'calcaire'); });
    // le beffroi
    g.rect(83, 25, 26, 65, 'calcaire');
    g.rect(101, 25, 8, 65, 'calcaire.o');
    g.arche(96, 80, 6, 90, 'bois.o');
    g.croisee(93, 58, 6, 11, 'calcaire');
    g.ellipse(96, 44, 7, 7, 'or');
    g.ellipse(96, 44, 5.6, 5.6, 'blanc');
    g.ligne(96, 44, 96, 40, 'noir'); g.ligne(96, 44, 99, 45, 'noir');
    [90, 102].forEach(function (cx) { g.arche(cx, 30, 2, 36, 'noir'); });
    g.rect(81, 23, 30, 2, 'calcaire.h');
    g.ellipse(96, 23, 13, 9, 'cuivre');
    g.poly([[96, 14], [109, 23], [101, 23]], 'cuivre.o');
    g.rect(93, 9, 7, 5, 'calcaire');
    g.cone(96.5, 10, 4, 1, 'cuivre');
    g.px(96, 0, 'or');
  }
};

// ---------------------------------------------------- phare de Cordouan
DESSINS.phare = {
  nom: 'Phare de Cordouan', sol: { type: 'roche', eau: [[0, 43], [149, 191]] }, promenade: [50, 140],
  peindre: function (g) {
    // l'enceinte ronde
    g.rect(44, 81, 104, 9, 'granit');
    g.rect(122, 81, 26, 9, 'granit.o');
    g.creneaux(44, 78, 104, 3, 'granit', 3, 2);
    // rez-de-chaussée : le logis du roi
    g.rect(70, 60, 52, 21, 'blanc');
    g.rect(108, 60, 14, 21, 'blanc.o');
    [72, 84, 106, 118].forEach(function (x) { g.rect(x, 60, 2, 21, 'blanc.h'); });
    g.arche(96, 72, 5, 81, 'noir');
    g.arche(79, 66, 2, 74, 'vitre'); g.arche(113, 66, 2, 74, 'vitre');
    g.rect(66, 57, 60, 3, 'granit');
    g.creneaux(68, 54, 56, 3, 'blanc', 1, 1);
    // la chapelle
    g.rect(76, 40, 40, 14, 'blanc');
    g.rect(106, 40, 10, 14, 'blanc.o');
    [84, 96, 108].forEach(function (cx) { g.arche(cx, 45, 2, 52, 'vitre'); });
    g.rect(73, 38, 46, 2, 'granit');
    // le fût du XVIIIe siècle, qui s'affine
    g.poly([[81, 38], [111, 38], [107, 16], [85, 16]], 'blanc');
    g.poly([[100, 38], [111, 38], [107, 16], [101, 16]], 'blanc.o');
    for (let y = 22; y < 38; y += 8) g.rect(83, y, 26, 1, 'blanc.h');
    [26, 34].forEach(function (y) { g.arche(96, y - 2, 1.2, y + 1, 'noir'); });
    g.rect(82, 14, 28, 2, 'granit');
    g.creneaux(83, 12, 26, 2, 'blanc', 1, 1);
    // la lanterne
    g.rect(88, 6, 16, 6, 'vitre');
    for (let x = 88; x <= 104; x += 4) g.rect(x, 6, 1, 6, 'noir');
    g.ellipse(96, 6, 8, 3.5, 'cuivre');
    g.rect(87, 5, 18, 1, 'cuivre');
    g.rect(96, 0, 1, 3, 'or');
  },
  deco: function (ctx, t, etat) {
    if (!etat.fini) return;
    // le faisceau tourne
    const a = (t / 1600) % 2;
    const sens = a < 1 ? 1 : -1, long = Math.abs(Math.sin(a * Math.PI)) * 74;
    for (let k = 0; k < long; k++) {
      const w = 1 + Math.floor(k / 16), x = 96 + sens * (9 + k);
      for (let j = 0; j < w; j++) {
        if (bruit(x, j + Math.floor(t / 200)) < k / long * 0.8) continue;
        ctx.fillStyle = k < long * 0.35 ? '#FFF2B0' : '#FFE08A';
        ctx.fillRect(x, 9 - Math.floor(w / 2) + j, 1, 1);
      }
    }
  }
};

// ---------------------------------------------------- chapelle de Ronchamp
DESSINS.ronchamp = {
  nom: 'Chapelle de Ronchamp', sol: { type: 'herbe' }, promenade: [8, 180],
  peindre: function (g) {
    for (let y = 20; y < 90; y++) for (let x = 40; x < 160; x++) {
      if (x >= 48 && x <= 64) {
        if (y >= 36) { g.px(x, y, (x >= 54 && x <= 57 && y >= 44 && y <= 49) ? 'vitre' : (x > 60 ? 'blanc.o' : 'blanc')); continue; }
        const dx = x + 0.5 - 56, dy = 36.5 - y;
        if (dx * dx + dy * dy <= 64) g.px(x, y, x > 60 ? 'blanc.o' : 'blanc');
        continue;
      }
      if (x < 64 || x > 150) continue;
      const t = (x - 64) / 86;
      const bas = Math.round(56 - 14 * t * t), haut = bas - 7 + Math.round(2 * t);
      if (y >= haut && y < bas) { g.px(x, y, y < bas - 2 ? 'bois.oo' : 'bois.o'); continue; }
      if (y >= bas) g.px(x, y, x > 136 ? 'blanc.o' : 'blanc');
    }
    [[70, 64, 2, 4], [78, 70, 3, 5], [88, 62, 2, 3], [98, 68, 4, 6], [110, 63, 2, 4], [120, 70, 3, 4], [130, 62, 2, 5], [138, 68, 2, 3], [94, 79, 2, 3]]
      .forEach(function (f, k) { g.rect(f[0], f[1], f[2], f[3], k % 3 === 1 ? 'vitrail' : 'vitre'); });
    g.rect(112, 77, 9, 13, 'bois.o');
  },
  deco: function (ctx) { arbre(ctx, 26, 30, true); arbre(ctx, 170, 24, true); }
};

// =============================================================== LES MERVEILLES

// ---------------------------------------------------- tour Eiffel
// Vraies proportions : 1er étage à 57 m, 2e à 115 m, 3e à 276 m sur 330 m.
// Le pied est un peu élargi pour qu'elle tienne la scène ; illuminée en or, la nuit.
const EIFFEL_PROFIL = [[90, 28], [86, 23.5], [82, 19.8], [78, 16.8], [75, 14.8], [72, 12.8], [66, 10.4], [60, 8.6], [57, 7.7],
  [54, 6.6], [46, 5.2], [38, 4.2], [30, 3.4], [22, 2.8], [15, 2.3], [12, 1.9]];
function eiffelDemi(y) {
  const P = EIFFEL_PROFIL;
  for (let k = 0; k + 1 < P.length; k++) if (y <= P[k][0] && y >= P[k + 1][0]) {
    const a = P[k], b = P[k + 1], u = (a[0] - y) / (a[0] - b[0]);
    return a[1] + (b[1] - a[1]) * u;
  }
  return 1.5;
}
DESSINS.eiffel = {
  nom: 'Tour Eiffel', merveille: true, sol: { type: 'pave' }, promenade: [4, 186],
  peindre: function (g) {
    const cx = 96;
    for (let y = 12; y < 90; y++) {
      const w = eiffelDemi(y + 0.5);
      for (let x = Math.floor(cx - w); x <= Math.ceil(cx + w); x++) {
        const dx = x + 0.5 - cx, adx = Math.abs(dx);
        if (adx > w) continue;
        // la grande arche entre les piliers, jusque sous le 1er étage
        const ax = dx / 16, ay = (y + 0.5 - 90) / 14.5, r = ax * ax + ay * ay;
        if (y > 75 && r < 1) continue;
        // entre le 1er et le 2e étage, les piliers restent séparés : un vide en pointe
        if (y > 57 && y < 72 && adx < (y - 57) * 4.6 / 15) continue;
        const bordArche = y > 74 && r < 1.22;
        const bordVide = y > 56 && y < 72 && adx < (y - 57) * 4.6 / 15 + 1.3;
        const epaisseur = y > 75 ? 3.2 : (y > 56 ? 2.2 : (y > 30 ? 1.5 : 1.1));
        if (adx > w - epaisseur || bordArche || bordVide) { g.px(x, y, adx > w - 0.9 && !bordArche ? 'ferdore.o' : 'ferdore'); continue; }
        // le treillis : croisillons
        if ((x - cx + y + 600) % 3 === 0 || (x - cx - y + 600) % 3 === 0) g.px(x, y, 'treillisdore');
      }
    }
    // 1er étage et sa galerie
    g.rect(cx - 17, 72, 35, 4, 'ferdore');
    for (let x = cx - 15; x < cx + 16; x += 3) g.rect(x, 73, 2, 2, 'vitre');
    g.rect(cx - 18, 71, 37, 1, 'ferdore.h');
    // 2e étage
    g.rect(cx - 10, 55, 21, 3, 'ferdore');
    for (let x = cx - 8; x < cx + 9; x += 3) g.rect(x, 56, 2, 1, 'vitre');
    g.rect(cx - 11, 54, 23, 1, 'ferdore.h');
    // 3e étage, campanile et antenne
    g.rect(cx - 4, 12, 9, 2, 'ferdore');
    g.rect(cx - 2, 7, 5, 5, 'ferdore');
    g.rect(cx - 1, 8, 3, 3, 'vitre');
    g.rect(cx - 2, 6, 5, 1, 'ferdore.h');
    g.rect(cx, 0, 1, 6, 'ferdore.h');
  },
  // Paris, au pied de la tour : immeubles haussmanniens, toits d'ardoise, fenêtres allumées
  fond: function (ctx) {
    // les toits de Paris, loin à l'horizon
    let x = 0, k = 0;
    while (x < PW) {
      const w = 6 + Math.floor(bruit(k, 1) * 9), h = 4 + Math.floor(bruit(k, 2) * 5);
      const haut = SOL - h;
      for (let y = haut; y < SOL; y++) for (let i = x; i < x + w && i < PW; i++) {
        let c;
        if (y < haut + 2) c = (i === x || i === x + w - 1) ? '#1B2230' : (((i + y) & 1) ? '#333B4C' : '#2D3444');
        else {
          const fen = (i - x) % 2 === 1 && (y - haut) % 2 === 0 && i < x + w - 1 && bruit(i, y) < 0.5;
          c = fen ? '#FFD86B' : (i === x ? '#323A4A' : '#3D4658');
        }
        ctx.fillStyle = c; ctx.fillRect(i, y, 1, 1);
      }
      if (bruit(k, 3) < 0.5) { ctx.fillStyle = '#232A38'; ctx.fillRect(x + 2, haut - 1, 1, 1); }
      x += w; k++;
    }
    // le dôme des Invalides, au loin
    for (let y = 0; y < 9; y++) for (let i = -5; i <= 5; i++) {
      const r = i * i / 25 + (y - 8) * (y - 8) / 64;
      if (r > 1) continue;
      ctx.fillStyle = y < 3 ? '#E8C25A' : (i > 1 ? '#3B4457' : '#4C566A');
      ctx.fillRect(160 + i, SOL - 14 + y, 1, 1);
    }
    ctx.fillStyle = '#4C566A'; ctx.fillRect(155, SOL - 6, 11, 6);
    ctx.fillStyle = '#E8C25A'; ctx.fillRect(160, SOL - 17, 1, 3);
    // les arbres du Champ-de-Mars, au pied
    for (let k2 = 0; k2 < 16; k2++) {
      const ax = 4 + k2 * 12 + Math.floor(bruit(k2, 2) * 4);
      if (ax > 62 && ax < 130) continue;
      for (let dy = 0; dy < 4; dy++) for (let dx = -2; dx <= 2; dx++) {
        if (dx * dx + (dy - 1.5) * (dy - 1.5) * 1.8 > 5) continue;
        ctx.fillStyle = dx > 0 ? '#1F4A2A' : (bruit(ax + dx, dy) < 0.4 ? '#3E7A3E' : '#2F6233');
        ctx.fillRect(ax + dx, SOL - 4 + dy, 1, 1);
      }
    }
  },
  deco: function (ctx, t, etat) {
    if (!etat.fini) return;
    // le phare du sommet balaie le ciel : un pinceau qui s'élargit et s'éteint en s'éloignant
    const a = (t / 2600) % 2;
    const sens = a < 1 ? 1 : -1, long = Math.abs(Math.sin(a * Math.PI)) * 92;
    const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
    for (let k = 0; k < long; k++) {
      const x = 96 + sens * (3 + k);
      if (x < 0 || x >= PW) break;
      const yc = 9.5 - k * 0.06, demi = 0.7 + k * 0.04, f = 1 - Math.pow(k / long, 1.7);
      for (let y = Math.floor(yc - demi); y <= Math.ceil(yc + demi); y++) {
        const bord = Math.min(1, Math.abs(y + 0.5 - yc) / demi);
        const v = f * (1 - bord * 0.7);
        if (v * 16 <= BAYER[(y & 3) * 4 + (x & 3)]) continue;
        ctx.fillStyle = v > 0.55 ? '#FFF6D0' : '#FFE29A';
        ctx.fillRect(x, y, 1, 1);
      }
    }
    // le scintillement, au début de chaque heure
    if (Math.floor(t / 6000) % 2 === 0) {
      for (let k = 0; k < 26; k++) {
        if (bruit(k, Math.floor(t / 120)) > 0.5) continue;
        const y = 13 + Math.floor(bruit(k, 3) * 76), w = eiffelDemi(y + 0.5);
        const x = Math.round(96 + (bruit(k, 4) * 2 - 1) * (w - 1));
        ctx.fillStyle = '#FFFFFF'; ctx.fillRect(x, y, 1, 1);
      }
    }
  }
};

// ---------------------------------------------------- Notre-Dame de Paris
DESSINS.notredame = {
  nom: 'Notre-Dame de Paris', merveille: true, sol: { type: 'pave' }, promenade: [4, 184],
  peindre: function (g) {
    // la nef derrière, avec ses arcs-boutants
    [[40, 66], [126, 152]].forEach(function (c, k) {
      const x0 = c[0], x1 = c[1];
      g.poly([[x0, 90], [x1, 90], [x1, 50], [x0, 58]].map(function (p) { return k ? [x0 + x1 - p[0], p[1]] : p; }), 'calcaire.oo');
      for (let x = x0 + 3; x < x1 - 4; x += 9) {
        const xx = k ? x0 + x1 - x : x, s = k ? -1 : 1;
        g.rect(xx - 1, 64, 3, 26, 'calcaire');
        toitCone(g, xx + 0.5, 64, 2, 56, 'calcaire');
        g.ligne(xx + s * 2, 64, xx + s * 8, 58, 'calcaire');
        g.ligne(xx + s * 2, 65, xx + s * 8, 59, 'calcaire');
      }
    });
    g.poly([[52, 50], [140, 50], [124, 40], [68, 40]], 'plomb.o');
    // la flèche, à la croisée
    g.rect(93, 24, 7, 14, 'plomb');
    g.rect(94, 26, 1, 8, 'noir'); g.rect(97, 26, 1, 8, 'noir');
    g.poly([[92, 25], [101, 25], [96.5, 1]], 'plomb');
    g.poly([[96.5, 1], [101, 25], [98, 25]], 'plomb.o');
    g.px(96, 0, 'or');
    // la façade : trois travées
    g.rect(66, 42, 60, 48, 'calcaire');
    // les deux tours
    [66, 106].forEach(function (x) {
      g.rect(x, 14, 20, 28, 'calcaire');
      g.rect(x + 14, 14, 6, 28, 'calcaire.o');
      g.rect(x - 1, 12, 22, 2, 'calcaire.h');
      g.creneaux(x - 1, 9, 22, 3, 'calcaire', 1, 1);
      toitCone(g, x, 10, 1.5, 4, 'calcaire'); toitCone(g, x + 20, 10, 1.5, 4, 'calcaire');
      [x + 6, x + 14].forEach(function (cx) {
        g.ogive(cx, 20, 2.5, 38, 'noir');
        for (let y = 19; y < 38; y += 3) g.rect(cx - 2, y, 5, 1, 'lame');
      });
      // baies jumelles au niveau de la rose
      g.ogive(x + 7, 52, 2.2, 62, 'calcaire.oo'); g.ogive(x + 13, 52, 2.2, 62, 'calcaire.oo');
      // portail latéral
      g.ogive(x + 10, 80, 6, 90, 'calcaire.oo');
      g.ogive(x + 10, 82, 4.5, 90, 'noir');
    });
    // contreforts
    [66, 85, 105, 124].forEach(function (x) { g.rect(x, 42, 2, 48, 'calcaire.h'); });
    // galerie des chimères, ajourée
    g.rect(66, 36, 60, 6, 'noir');
    for (let x = 66; x < 126; x += 2) g.rect(x, 36, 1, 6, 'calcaire');
    g.rect(65, 35, 62, 1, 'calcaire.h'); g.rect(65, 42, 62, 1, 'calcaire.h');
    // la rose
    rose(g, 96, 55, 8.5, 'calcaire');
    // galerie des rois
    g.rect(66, 67, 60, 1, 'calcaire.h');
    for (let x = 67; x < 125; x += 3) g.ogive(x + 1, 69, 0.9, 72, 'calcaire.oo');
    g.rect(66, 72, 60, 1, 'calcaire.h');
    // portail central
    g.ogive(96, 81, 7.5, 90, 'calcaire.oo');
    g.ogive(96, 83, 6, 90, 'noir');
    g.rect(95, 82, 2, 8, 'calcaire');
  },
  deco: function (ctx) { arbre(ctx, 22, 24, true); arbre(ctx, 170, 26, true); }
};

// ---------------------------------------------------- château de Versailles
DESSINS.versailles = {
  nom: 'Château de Versailles', merveille: true, sol: { type: 'jardin' }, promenade: [6, 74],
  peindre: function (g) {
    g.rect(6, 45, 180, 45, 'calcaire');
    // avant-corps
    g.rect(70, 41, 52, 49, 'calcaire.h');
    g.rect(22, 43, 24, 47, 'calcaire.h');
    g.rect(146, 43, 24, 47, 'calcaire.h');
    // corniche et balustrade
    g.rect(4, 43, 184, 2, 'calcaire.h');
    g.creneaux(4, 39, 184, 4, 'calcaire', 1, 1);
    g.rect(4, 38, 184, 1, 'calcaire.h');
    g.rect(68, 39, 56, 2, 'calcaire.h');
    g.creneaux(68, 35, 56, 4, 'calcaire', 1, 1);
    g.rect(68, 34, 56, 1, 'calcaire.h');
    // trophées et vases dorés
    for (let x = 8; x < 186; x += 12) { g.rect(x, 34, 3, 4, 'or'); g.px(x + 1, 33, 'or'); }
    [72, 82, 92, 100, 110, 120].forEach(function (x) { g.rect(x, 28, 3, 6, 'or'); g.px(x + 1, 27, 'or'); });
    // les trois niveaux de fenêtres
    g.rect(6, 52, 180, 1, 'calcaire.o');
    g.rect(6, 71, 180, 2, 'calcaire.o');
    for (let x = 10; x < 184; x += 8) {
      g.rect(x - 1, 46, 4, 4, 'vitre');
      g.arche(x + 1, 58, 2.5, 69, 'vitre'); g.rect(x + 1, 57, 1, 12, 'calcaire');
      g.arche(x + 1, 79, 2.5, 89, 'vitre'); g.rect(x + 1, 78, 1, 11, 'calcaire');
    }
    // colonnes des avant-corps
    [72, 80, 88, 104, 112, 120, 24, 32, 40, 148, 156, 164].forEach(function (cx) {
      if (cx < 70 || cx > 122) { if (cx === 32 || cx === 156) return; }
      g.rect(cx + 3, 54, 2, 16, 'calcaire');
      g.rect(cx + 2, 53, 4, 1, 'calcaire.h');
    });
  },
  deco: function (ctx, t) {
    // le bassin et son jet d'eau
    for (let y = 96; y < 104; y++) for (let x = 70; x < 122; x++) {
      const dx = (x + 0.5 - 96) / 24, dy = (y + 0.5 - 100) / 4;
      const r = dx * dx + dy * dy;
      if (r > 1) continue;
      ctx.fillStyle = r > 0.8 ? '#C9BC9C' : (bruit(x + Math.floor(t / 400), y) < 0.03 ? '#A8DEF8' : (((x + y) & 1) ? '#2B74AA' : '#226495'));
      ctx.fillRect(x, y, 1, 1);
    }
    for (let k = 0; k < 14; k++) {
      const h = (t / 60 + k * 5) % 14;
      ctx.fillStyle = k % 3 ? '#DFF3FF' : '#FFFFFF';
      ctx.fillRect(96 + Math.round(Math.sin(k) * (h / 5)), Math.round(99 - (14 - h) * (h / 14) * 1.4), 1, 1);
    }
  }
};

// ---------------------------------------------------- arc de triomphe
DESSINS.arc = {
  nom: 'Arc de triomphe', merveille: true, sol: { type: 'pave' }, promenade: [6, 182],
  peindre: function (g) {
    g.rect(52, 22, 88, 68, 'calcaire');
    g.rect(127, 22, 13, 68, 'calcaire.o');
    // attique et corniches
    g.rect(48, 13, 96, 10, 'calcaire');
    g.rect(47, 11, 98, 2, 'calcaire.h');
    for (let x = 54; x < 140; x += 7) g.ellipse(x + 0.5, 18, 2, 2, 'calcaire.o');
    g.rect(48, 29, 96, 3, 'calcaire.h');
    for (let x = 52; x < 140; x += 2) g.rect(x, 33, 1, 3, 'calcaire.o');
    g.rect(52, 36, 88, 1, 'calcaire.h');
    // l'arche et sa voussure
    g.arche(96, 62, 19, 90, 'calcaire.h');
    g.arche(96, 62, 16, 90, 'noir');
    for (let y = 47; y < 62; y += 3) g.rect(82, y, 29, 1, 'calcaire.oo');
    g.rect(80, 60, 33, 2, 'calcaire.h');
    // bas-reliefs et groupes sculptés
    [56, 116].forEach(function (x) {
      g.rect(x, 40, 20, 10, 'calcaire.o');
      for (let k = 0; k < 7; k++) g.rect(x + 2 + k * 2.6, 42 + (k % 2), 1, 6 - (k % 3), 'calcaire.h');
      g.rect(x, 64, 20, 22, 'calcaire.o');
      g.ellipse(x + 10, 71, 6, 5, 'calcaire');
      g.rect(x + 7, 74, 6, 10, 'calcaire');
      g.rect(x + 4, 66, 2, 8, 'calcaire.h'); g.rect(x + 14, 68, 2, 9, 'calcaire');
      g.rect(x - 1, 86, 22, 2, 'calcaire.h');
    });
  },
  deco: function (ctx, t, etat) {
    if (!etat.fini) return;
    // le grand drapeau tricolore sous la voûte
    const coul = ['#3563BE', '#F4F1EA', '#D43B3B'];
    for (let y = 48; y < 80; y++) for (let k = 0; k < 18; k++) {
      const x = 87 + k + Math.round(Math.sin(y / 5 + t / 400) * 0.8 * (y - 48) / 32);
      ctx.fillStyle = coul[Math.floor(k / 6)];
      ctx.fillRect(x, y, 1, 1);
    }
  }
};

// ---------------------------------------------------- Mont-Saint-Michel
DESSINS.mont = {
  nom: 'Mont-Saint-Michel', merveille: true, sol: { type: 'sable', eau: [[0, 22], [172, 191]] }, promenade: [28, 166],
  peindre: function (g) {
    // le rocher
    g.poly([[24, 90], [50, 78], [64, 64], [76, 52], [90, 46], [108, 46], [122, 54], [136, 66], [150, 78], [170, 90]], 'rocher');
    g.poly([[108, 46], [122, 54], [136, 66], [150, 78], [170, 90], [124, 90], [114, 60]], 'rocher.o');
    // le village, en escalier sur la pente
    [[40, 76, 9, 8], [48, 72, 8, 10], [56, 66, 9, 12], [64, 60, 8, 12], [72, 56, 7, 10], [36, 82, 10, 4], [52, 78, 12, 6], [62, 72, 10, 8]].forEach(function (h, k) {
      g.rect(h[0], h[1], h[2], h[3], k % 3 === 1 ? 'calcaire' : 'blanc');
      g.poly([[h[0] - 1, h[1] + 1], [h[0] + h[2] + 1, h[1] + 1], [h[0] + h[2] / 2, h[1] - 4]], 'ardoise');
      g.rect(h[0] + 2, h[1] + 2, 2, 2, 'vitre');
      if (h[2] > 8) g.rect(h[0] + 5, h[1] + 2, 2, 2, 'vitre');
    });
    // logis abbatial, à gauche du sommet
    g.rect(66, 40, 16, 16, 'granit');
    g.poly([[64, 41], [84, 41], [80, 35], [68, 35]], 'plomb');
    g.arche(71, 46, 1.4, 51, 'noir'); g.arche(77, 46, 1.4, 51, 'noir');
    // la Merveille : hauts murs et contreforts au nord
    g.rect(112, 36, 26, 34, 'granit');
    g.rect(126, 36, 12, 34, 'granit.o');
    for (let x = 112; x < 138; x += 8) g.rect(x, 36, 2, 34, 'granit.h');
    for (let x = 117; x < 136; x += 8) { g.ogive(x, 42, 1.4, 50, 'noir'); g.ogive(x + 2, 42, 1.4, 50, 'noir'); }
    g.rect(110, 34, 30, 2, 'granit.h');
    g.creneaux(110, 31, 30, 3, 'granit', 2, 2);
    // l'abbatiale au sommet
    g.rect(80, 30, 32, 16, 'granit');
    g.rect(102, 30, 10, 16, 'granit.o');
    g.poly([[78, 31], [114, 31], [108, 23], [84, 23]], 'plomb');
    for (let x = 84; x < 110; x += 5) g.ogive(x, 36, 1.2, 42, 'noir');
    // clocher, flèche et saint Michel doré
    g.rect(92, 13, 9, 18, 'granit');
    g.rect(98, 13, 3, 18, 'granit.o');
    g.arche(96.5, 18, 1.6, 25, 'noir');
    g.rect(91, 12, 11, 1, 'granit.h');
    g.poly([[91, 13], [102, 13], [96.5, 2]], 'plomb');
    g.poly([[96.5, 2], [102, 13], [98, 13]], 'plomb.o');
    g.rect(96, 0, 1, 3, 'or'); g.px(95, 1, 'or'); g.px(97, 1, 'or');
    // remparts et tours
    g.rect(30, 82, 136, 8, 'granit');
    g.creneaux(30, 79, 136, 3, 'granit', 3, 2);
    cylindre(g, 28, 74, 10, 16, 'granit'); g.creneaux(27, 71, 12, 3, 'granit', 2, 1);
    cylindre(g, 156, 76, 10, 14, 'granit'); g.creneaux(155, 73, 12, 3, 'granit', 2, 1);
    g.arche(46, 86, 3, 90, 'noir');
  }
};

// ---------------------------------------------------- pont du Gard
DESSINS.gard = {
  nom: 'Pont du Gard', merveille: true, sol: { type: 'herbe', eau: [[40, 150]], berge: 2 }, fondation: 4, promenade: [4, 36],
  peindre: function (g) {
    // premier étage : 6 grandes arches
    g.rect(6, 62, 180, 32, 'pierre');
    g.rect(4, 60, 184, 2, 'pierre.h');
    for (let k = 0; k < 6; k++) {
      const cx = 6 + 15 + k * 30;
      g.arche(cx, 74, 13.5, 75, 'pierre.h');
      g.arche(cx, 74, 11.5, 94, null);
    }
    // deuxième étage : 11 arches
    g.rect(10, 40, 172, 20, 'pierre');
    g.rect(8, 38, 176, 2, 'pierre.h');
    for (let k = 0; k < 11; k++) {
      const cx = 10 + 172 / 22 + k * 172 / 11;
      g.arche(cx, 50, 6.8, 51, 'pierre.h');
      g.arche(cx, 50, 5.6, 60, null);
    }
    // troisième étage : 35 petites arches et le canal
    g.rect(14, 22, 164, 16, 'pierre');
    g.rect(12, 21, 168, 1, 'pierre.h');
    for (let k = 0; k < 35; k++) {
      const cx = 14 + 164 / 70 + k * 164 / 35;
      g.arche(cx, 33, 1.8, 38, null);
    }
  }
};

// ---------------------------------------------------- château de Chambord
DESSINS.chambord = {
  nom: 'Château de Chambord', merveille: true, sol: { type: 'herbe', eau: [[0, 191]], berge: 4 }, promenade: [4, 186],
  peindre: function (g) {
    // ailes basses et tours d'angle
    g.rect(8, 60, 176, 30, 'tuffeau');
    g.poly([[6, 61], [186, 61], [182, 52], [10, 52]], 'ardoise');
    for (let x = 14; x < 182; x += 9) { if (x > 40 && x < 150) continue; g.croisee(x, 66, 5, 8, 'tuffeau'); g.croisee(x, 78, 5, 8, 'tuffeau'); }
    [2, 174].forEach(function (x) {
      cylindre(g, x, 56, 16, 34, 'tuffeau');
      g.ellipse(x + 8, 56, 9, 7, 'ardoise');
      g.poly([[x + 8, 49], [x + 17, 56], [x + 11, 56]], 'ardoise.o');
      g.rect(x + 7, 44, 3, 6, 'tuffeau');
      toitCone(g, x + 8.5, 45, 3, 39, 'ardoise');
      g.croisee(x + 5, 64, 5, 8, 'tuffeau');
    });
    // donjon : façade à pilastres
    g.rect(56, 42, 80, 48, 'tuffeau');
    for (let x = 58; x < 136; x += 9) g.rect(x, 42, 1, 48, 'tuffeau.h');
    g.rect(56, 58, 80, 1, 'tuffeau.h'); g.rect(56, 74, 80, 1, 'tuffeau.h');
    for (let x = 61; x < 132; x += 9) { g.croisee(x, 46, 5, 10, 'tuffeau'); g.croisee(x, 62, 5, 10, 'tuffeau'); }
    g.arche(96, 82, 4, 90, 'bois.o');
    // les grosses tours rondes du donjon
    [40, 128].forEach(function (x) {
      cylindre(g, x, 44, 24, 46, 'tuffeau');
      g.rect(x - 1, 42, 26, 2, 'tuffeau.h');
      g.ellipse(x + 12, 42, 13, 10, 'ardoise');
      g.poly([[x + 12, 32], [x + 25, 42], [x + 16, 42]], 'ardoise.o');
      g.rect(x + 10, 24, 5, 10, 'tuffeau'); g.rect(x + 13, 24, 2, 10, 'tuffeau.o');
      toitCone(g, x + 12.5, 25, 4, 16, 'ardoise');
      cheminee(g, x + 3, 28, 38, 'tuffeau');
      cheminee(g, x + 18, 26, 36, 'tuffeau');
      g.croisee(x + 8, 52, 6, 10, 'tuffeau'); g.croisee(x + 8, 70, 6, 10, 'tuffeau');
    });
    // la « ville sur les toits »
    g.poly([[60, 43], [132, 43], [126, 30], [66, 30]], 'ardoise');
    [[64, 18], [70, 24], [78, 16], [112, 16], [120, 24], [126, 18]].forEach(function (c) {
      cheminee(g, c[0], c[1], 32, 'tuffeau');
      g.px(c[0] + 1, c[1] + 4, 'ardoise'); g.px(c[0] + 2, c[1] + 7, 'ardoise');
    });
    [[74, 30], [118, 30]].forEach(function (c) { g.rect(c[0] - 2, c[1] - 7, 5, 7, 'tuffeau'); toitCone(g, c[0] + 0.5, c[1] - 6, 3.5, c[1] - 14, 'ardoise'); });
    [84, 108].forEach(function (cx) { lucarne(g, cx, 42, 7, 10, 'tuffeau'); });
    // la lanterne centrale
    g.rect(89, 16, 15, 20, 'tuffeau');
    g.rect(99, 16, 5, 20, 'tuffeau.o');
    g.arche(94, 22, 1.6, 30, 'noir'); g.arche(99, 22, 1.6, 30, 'noir');
    toitCone(g, 96.5, 17, 9, 7, 'ardoise');
    g.rect(95, 1, 3, 7, 'tuffeau');
    g.px(96, 0, 'or');
  }
};

// ---------------------------------------------------- cité de Carcassonne
DESSINS.carcassonne = {
  nom: 'Cité de Carcassonne', merveille: true, sol: { type: 'herbe' }, promenade: [4, 186],
  peindre: function (g) {
    const tour = function (cx, haut, bas, w, pointe) {
      cylindre(g, cx - w / 2, haut, w, bas - haut, 'gres');
      toitCone(g, cx, haut + 1, w / 2 + 1.5, haut - pointe, 'ardoise');
      g.rect(Math.floor(cx) - 1, haut + 6, 1, 4, 'noir');
    };
    // enceinte intérieure
    g.rect(16, 50, 160, 30, 'gres');
    g.creneaux(16, 46, 160, 4, 'gres', 3, 2);
    [22, 46, 66, 126, 146, 170].forEach(function (cx, k) { tour(cx, 40 + (k % 2) * 3, 80, 12, 16 + (k % 3) * 3); });
    // enceinte extérieure (les lices)
    g.rect(2, 72, 188, 18, 'gres.o');
    g.creneaux(2, 69, 188, 3, 'gres.o', 3, 2);
    [8, 32, 56, 136, 160, 184].forEach(function (cx) { tour(cx, 64, 90, 10, 13); });
    // la porte Narbonnaise
    g.rect(88, 46, 16, 44, 'gres');
    g.creneaux(88, 42, 16, 4, 'gres', 3, 2);
    for (let x = 88; x < 104; x += 3) g.rect(x, 46, 2, 3, 'gres.h');
    [84, 108].forEach(function (cx) { tour(cx, 34, 90, 16, 22); g.rect(cx - 1, 50, 1, 6, 'noir'); g.rect(cx - 1, 66, 1, 6, 'noir'); });
    g.arche(96, 80, 6, 90, 'gres.h');
    g.arche(96, 81, 4.5, 90, 'noir');
    g.rect(92, 52, 9, 6, 'gres.oo');
    g.rect(96, 0, 1, 8, 'bois');
    g.rect(97, 1, 6, 4, 'or'); g.rect(97, 2, 6, 1, 'rouge');
  }
};

// ---------------------------------------------------- viaduc de Millau
DESSINS.millau = {
  nom: 'Viaduc de Millau', merveille: true, sol: { type: 'herbe', eau: [[82, 110]], berge: 2 }, promenade: [6, 76],
  peindre: function (g) {
    const piles = [14, 54, 96, 138, 178];
    // haubans (sous le tablier)
    piles.forEach(function (cx) {
      for (let k = 1; k <= 10; k++) {
        const yt = 13 + k * 1.6;
        g.ligne(cx, yt, cx - k * 3.6, 45, 'cable');
        g.ligne(cx, yt, cx + k * 3.6, 45, 'cable');
      }
    });
    piles.forEach(function (cx) {
      // pylône au-dessus du tablier
      g.poly([[cx - 2, 46], [cx + 2, 46], [cx + 0.6, 10], [cx - 0.6, 10]], 'acier');
      // pile : fût qui se dédouble sous le tablier
      g.poly([[cx - 3.5, 90], [cx + 3.5, 90], [cx + 2.5, 64], [cx - 2.5, 64]], 'acier');
      g.poly([[cx + 0.5, 90], [cx + 3.5, 90], [cx + 2.5, 64], [cx + 0.5, 64]], 'acier.o');
      g.rect(cx - 3, 50, 2, 15, 'acier'); g.rect(cx + 1, 50, 2, 15, 'acier.o');
    });
    // le tablier
    g.rect(0, 45, 192, 3, 'acier');
    g.rect(0, 48, 192, 2, 'acier.o');
    g.rect(0, 44, 192, 1, 'acier.h');
  },
  deco: function (ctx, t, etat) {
    if (!etat.fini) return;
    // une voiture traverse
    const x = Math.floor((t / 30) % 220) - 14;
    ctx.fillStyle = '#E5484D'; ctx.fillRect(x, 42, 5, 2);
    ctx.fillStyle = '#9FD0FF'; ctx.fillRect(x + 3, 42, 1, 1);
    const x2 = 192 - Math.floor((t / 42 + 90) % 220);
    ctx.fillStyle = '#F0B429'; ctx.fillRect(x2, 42, 5, 2);
  }
};

// ---------------------------------------------------- château de Chenonceau
DESSINS.chenonceau = {
  nom: 'Château de Chenonceau', merveille: true, sol: { type: 'herbe', eau: [[34, 191]] }, fondation: 4, promenade: [4, 30],
  peindre: function (g) {
    // tour des Marques, sur la rive
    cylindre(g, 8, 48, 18, 42, 'tuffeau');
    for (let i = 7; i < 27; i += 3) g.rect(i, 46, 2, 3, 'tuffeau.h');
    g.rect(7, 44, 20, 2, 'tuffeau.h');
    toitCone(g, 17, 45, 12, 24, 'ardoise');
    g.rect(16, 16, 3, 9, 'tuffeau'); toitCone(g, 17.5, 17, 3, 10, 'ardoise');
    g.croisee(14, 58, 6, 9, 'tuffeau'); g.croisee(14, 74, 6, 9, 'tuffeau');
    // le logis, sur sa pile dans le Cher
    g.rect(40, 74, 40, 20, 'tuffeau.o');
    g.rect(42, 38, 36, 36, 'tuffeau');
    g.poly([[39, 39], [81, 39], [74, 17], [47, 17]], 'ardoise');
    g.poly([[66, 39], [81, 39], [74, 17], [68, 17]], 'ardoise.o');
    cheminee(g, 50, 8, 20, 'tuffeau'); cheminee(g, 68, 8, 20, 'tuffeau');
    [52, 68].forEach(function (cx) { lucarne(g, cx, 37, 9, 12, 'tuffeau'); });
    [46, 56, 66].forEach(function (x) { g.croisee(x, 44, 6, 10, 'tuffeau'); g.croisee(x, 60, 6, 10, 'tuffeau'); });
    g.rect(42, 56, 36, 1, 'tuffeau.o');
    // tourelles en encorbellement
    [38, 76].forEach(function (x) {
      cylindre(g, x, 30, 8, 30, 'tuffeau');
      g.poly([[x, 60], [x + 8, 60], [x + 4, 66]], 'tuffeau');
      toitCone(g, x + 4, 31, 5.5, 14, 'ardoise');
    });
    // la galerie sur ses arches
    g.rect(78, 50, 110, 28, 'tuffeau');
    g.poly([[77, 51], [190, 51], [186, 42], [81, 42]], 'ardoise');
    for (let cx = 90; cx < 188; cx += 13) lucarne(g, cx, 50, 7, 9, 'tuffeau');
    for (let x = 84; x < 186; x += 9) { g.croisee(x, 55, 5, 8, 'tuffeau'); g.croisee(x, 67, 5, 8, 'tuffeau'); }
    g.rect(78, 64, 110, 1, 'tuffeau.o');
    g.rect(78, 78, 110, 16, 'tuffeau.o');
    [92, 112, 132, 152, 172].forEach(function (cx) {
      g.arche(cx, 85, 8.5, 86, 'tuffeau');
      g.arche(cx, 85, 7, 94, null);
    });
    for (let cx = 102; cx < 186; cx += 20) g.poly([[cx - 3, 94], [cx + 3, 94], [cx, 88]], 'tuffeau');
  }
};

const ORDRE_TYPES = ['chateau', 'fort', 'palais', 'cathedrale', 'abbaye', 'antique', 'dome', 'edifice', 'phare', 'ronchamp'];
const ORDRE_MERVEILLES = ['eiffel', 'notredame', 'versailles', 'arc', 'mont', 'gard', 'chambord', 'carcassonne', 'millau', 'chenonceau'];
