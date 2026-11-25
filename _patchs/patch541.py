# patch541 : l'Espagne, l'Andorre et Monaco dans le jeu (éteints tant que ESPAGNE_OUVERTE vaut false ; ?espagne=test pour essayer).
# Même chemin que le Luxembourg (patch467). Provinces E01…E52 (+ AND, MCO) = départements ; régions = communautés autonomes,
# « Andorre », « Monaco ». Codes : ES + INE (ES28079), AD02…AD08, MC00. Canaries déplacées dans un encart (données).
# Terra : paquet « Espagne » (Andorre comprise) ; Monaco dans le paquet France (serveur s3-79).
# Fichiers : data/espagne-terre.json, data/espagne-frontiere.json, data/micro-etats-terre.json, data/contours-provinces-es.json,
# contours/E01…E52.json, contours/AND.json, contours/MCO.json.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
J = json.load(open('/tmp/es_js.json', encoding='utf-8')) if os.path.exists('/tmp/es_js.json') else json.load(open(os.path.join(os.path.dirname(__file__), 'patch541-tables.json'), encoding='utf-8'))
NOMS = json.dumps(J['noms'], ensure_ascii=False, separators=(',', ':'))
REG = json.dumps(J['reg'], ensure_ascii=False, separators=(',', ':'))
A = 'app.js'

rep(A, "const SUISSE = SUISSE_OUVERTE || BELGIQUE || LUXEMBOURG || (() => {",
"""// patch541 : l'Espagne, l'Andorre et Monaco : ESPAGNE_OUVERTE le jour de l'ouverture, ?espagne=test pour essayer.
// Provinces « E » + code INE (01…52 sont pris par la France), Andorre « AND », Monaco « MCO ».
const ESPAGNE_OUVERTE = false;
const ESPAGNE = ESPAGNE_OUVERTE || (() => {
  try {
    if(/[?&]espagne=test\\b/.test(location.search)) sessionStorage.setItem('tf-espagne-test', '1');
    return sessionStorage.getItem('tf-espagne-test') === '1';
  } catch(e){ return /[?&]espagne=test\\b/.test(location.search); }
})();
const SUISSE = SUISSE_OUVERTE || BELGIQUE || LUXEMBOURG || ESPAGNE || (() => {""")

rep(A, "// patch462 : un « département » hors de France (canton suisse, province belge ; patch467 : canton luxembourgeois)\nconst estEtrangerDep = (dep) => estCanton(dep) || estProvinceBe(dep) || estCantonLu(dep);\n",
"const PROVINCES_ES = " + NOMS + ";   // patch541\n"
"const PROV_ES_RE = /^E(0[1-9]|[1-4][0-9]|5[0-2])$/;\n"
"const estProvinceEs = (dep) => PROV_ES_RE.test(String(dep || ''));\n"
"const estMicroEtat = (dep) => dep === 'AND' || dep === 'MCO';\n"
"// patch462 : un « département » hors de France (canton suisse, province belge ; patch467 : canton luxembourgeois ; patch541 : Espagne, Andorre, Monaco)\n"
"const estEtrangerDep = (dep) => estCanton(dep) || estProvinceBe(dep) || estCantonLu(dep) || estProvinceEs(dep) || estMicroEtat(dep);\n")
rep(A, "|| (LUXEMBOURG && estCantonLu(dep));\nif(SUISSE)", "|| (LUXEMBOURG && estCantonLu(dep)) || (ESPAGNE && (estProvinceEs(dep) || estMicroEtat(dep)));\nif(SUISSE)")
rep(A, "if(LUXEMBOURG) Object.assign(DEPT_NAMES, CANTONS_LU);   // patch467\n",
       "if(LUXEMBOURG) Object.assign(DEPT_NAMES, CANTONS_LU);   // patch467\nif(ESPAGNE) Object.assign(DEPT_NAMES, PROVINCES_ES);   // patch541\n")

# le fond : la terre et la frontière de l'Espagne, de l'Andorre et de Monaco ; plus de voisin « ESPAGNE »
rep(A, """        FOND_S3.voisins = FOND_S3.voisins.filter(v => v.nom !== 'LUX.');
      } catch(e){}
    }
""", """        FOND_S3.voisins = FOND_S3.voisins.filter(v => v.nom !== 'LUX.');
      } catch(e){}
    }
    if(ESPAGNE){   // patch541
      try {
        const [et, ef, mt] = await Promise.all(['espagne-terre.json', 'espagne-frontiere.json', 'micro-etats-terre.json'].map(lire));
        FOND_S3.terreEs = et.concat(mt);
        FOND_S3.terre = FOND_S3.terre.concat(et, mt); FOND_S3.frontiere = FOND_S3.frontiere.concat(ef, mt);
        FOND_S3.voisins = FOND_S3.voisins.filter(v => !['ESPAGNE', 'ANDORRE', 'MONACO'].includes(v.nom));
      } catch(e){}
    }
""")
# la largeur de la carte en km (pour le zoom maximal) grandit avec l'Espagne
rep(A, "  mapBounds = {latMin, latMax, lonMin, lonMax};\n",
"""  mapBounds = {latMin, latMax, lonMin, lonMax};
  // patch541 : la carte couvre plus de kilomètres avec l'Espagne : le zoom maximal suit
  window.__largeurCarte = 1;
  if(FOND_S3 && FOND_S3.terreEs){
    let a = 180, b = -180;
    const sansEs = new Set(FOND_S3.terreEs);
    for(const ring of FRANCE_OUTLINE.concat(FOND_S3.terre.filter(r => !sansEs.has(r)))) for(const [lon] of ring){ if(lon < a) a = lon; if(lon > b) b = lon; }
    if(b > a) window.__largeurCarte = (lonMax - lonMin) / ((b - a) * (1 + 2 * pad));
  }
""")
rep(A, "  const cible = CIBLE_PX_PAR_KM * LARGEUR_FRANCE_KM / w;", "  const cible = CIBLE_PX_PAR_KM * LARGEUR_FRANCE_KM * (window.__largeurCarte || 1) / w;   // patch541")
rep(A, """    if(LUXEMBOURG){   // patch467 : les cantons luxembourgeois
      try { Object.assign(deps, await (await fetch('data/contours-cantons-lu.json?v=1', { cache: 'force-cache' })).json()); } catch(e){}
    }
""", """    if(LUXEMBOURG){   // patch467 : les cantons luxembourgeois
      try { Object.assign(deps, await (await fetch('data/contours-cantons-lu.json?v=1', { cache: 'force-cache' })).json()); } catch(e){}
    }
    if(ESPAGNE){   // patch541 : les provinces espagnoles, l'Andorre et Monaco
      try { Object.assign(deps, await (await fetch('data/contours-provinces-es.json?v=1', { cache: 'force-cache' })).json()); } catch(e){}
    }
""")
rep(A, "if(LUXEMBOURG) for(const c in CANTONS_LU) DEP_REGION[c] = 'Luxembourg';   // patch467\n",
"if(LUXEMBOURG) for(const c in CANTONS_LU) DEP_REGION[c] = 'Luxembourg';   // patch467\n"
"if(ESPAGNE) Object.assign(DEP_REGION, " + REG + ");   // patch541 : communautés autonomes\n")
rep(A, "if(LUXEMBOURG) 'LCA:9,LCL:5,LDI:10,LEC:7,LES:14,LGR:8,LLU:11,LME:10,LRE:9,LRM:7,LVI:3,LWI:7'\n  .split(',').forEach(x => { const [d, n] = x.split(':'); COMMUNES_PAR_DEPT[d] = Number(n); });\n",
"if(LUXEMBOURG) 'LCA:9,LCL:5,LDI:10,LEC:7,LES:14,LGR:8,LLU:11,LME:10,LRE:9,LRM:7,LVI:3,LWI:7'\n  .split(',').forEach(x => { const [d, n] = x.split(':'); COMMUNES_PAR_DEPT[d] = Number(n); });\n"
"// patch541 : les provinces espagnoles (INE 2026), l'Andorre, Monaco\n"
"if(ESPAGNE) '" + J['n'] + "'\n  .split(',').forEach(x => { const [d, n] = x.split(':'); COMMUNES_PAR_DEPT[d] = Number(n); });\n")

# le département d'une commune depuis son code
rep(A, """  if(/^(CH|BE|LU)\\d/.test(cc)){   // patch467""", """  if(/^ES\\d{5}$/.test(cc)) return 'E' + cc.slice(2, 4);   // patch541
  if(/^AD\\d/.test(cc)) return 'AND';
  if(cc === 'MC00') return 'MCO';
  if(/^(CH|BE|LU)\\d/.test(cc)){   // patch467""")
rep(A, "(LUXEMBOURG && estCantonLu(d.toUpperCase()))){ deps.push", "(LUXEMBOURG && estCantonLu(d.toUpperCase())) || (ESPAGNE && (estProvinceEs(d.toUpperCase()) || estMicroEtat(d.toUpperCase())))){ deps.push")

# les mots
rep(A, "const motDep = (d) => estCanton(d) || estCantonLu(d) ? 'canton' : estProvinceBe(d) ? 'province' : 'département';",
       "const motDep = (d) => estCanton(d) || estCantonLu(d) ? 'canton' : estProvinceBe(d) || estProvinceEs(d) ? 'province' : estMicroEtat(d) ? 'pays' : 'département';")
rep(A, "  : estCantonLu(d) ? `dans le canton ${/^[AEIOUÉ]/.test(CANTONS_LU[d] || '') ? 'd’' : 'de '}${CANTONS_LU[d] || d} (Luxembourg)`   // patch467\n",
"  : estCantonLu(d) ? `dans le canton ${/^[AEIOUÉ]/.test(CANTONS_LU[d] || '') ? 'd’' : 'de '}${CANTONS_LU[d] || d} (Luxembourg)`   // patch467\n"
"  : d === 'AND' ? 'en Andorre' : d === 'MCO' ? 'à Monaco'   // patch541\n"
"  : estProvinceEs(d) ? `dans la province ${/^[AEIOUÉÁÍÓÚ]/.test(PROVINCES_ES[d] || '') ? 'd’' : 'de '}${PROVINCES_ES[d] || d} (Espagne)`\n")

# codes, drapeaux, badges
rep(A, "function estEtrangerCode(code){ return estSuisseCode(code) || estBelgeCode(code) || estLuxCode(code); }\nfunction paysDuCode(code){ return estSuisseCode(code) ? 'CH' : estBelgeCode(code) ? 'BE' : estLuxCode(code) ? 'LU' : 'FR'; }",
"""// patch541 : l'Espagne (ES + INE), l'Andorre (AD..), Monaco (MC00) ; l'Andorre est dans le paquet espagnol, Monaco dans le français
function estEsCode(code){ return /^ES\\d/.test(String(code || '')); }
function estAdCode(code){ return /^AD\\d/.test(String(code || '')); }
function estMcCode(code){ return String(code || '') === 'MC00'; }
function estIberCode(code){ return estEsCode(code) || estAdCode(code) || estMcCode(code); }
function estEtrangerCode(code){ return estSuisseCode(code) || estBelgeCode(code) || estLuxCode(code) || estEsCode(code) || estAdCode(code); }
function paysDuCode(code){ return estSuisseCode(code) ? 'CH' : estBelgeCode(code) ? 'BE' : estLuxCode(code) ? 'LU' : estEsCode(code) || estAdCode(code) ? 'ES' : 'FR'; }
function esDrapeau(cls){ return `<svg${cls ? ` class="${cls}"` : ''} viewBox="0 0 3 2" aria-hidden="true"><rect width="3" height="2" fill="#AA151B" stroke="none"/><rect y=".5" width="3" height="1" fill="#F1BF00" stroke="none"/></svg>`; }
function adDrapeau(){ return `<svg viewBox="0 0 3 2" aria-hidden="true"><rect width="1" height="2" fill="#10069F" stroke="none"/><rect x="1" width="1" height="2" fill="#FEDD00" stroke="none"/><rect x="2" width="1" height="2" fill="#D50032" stroke="none"/></svg>`; }
function mcDrapeau(){ return `<svg viewBox="0 0 3 2" aria-hidden="true"><rect width="3" height="1" fill="#CE1126" stroke="none"/><rect y="1" width="3" height="1" fill="#fff" stroke="none"/></svg>`; }
function iberClasse(code){ return estEsCode(code) ? ' espagne' : estAdCode(code) ? ' andorre' : estMcCode(code) ? ' monaco' : ''; }
function iberBadge(code, mini){
  const [d, nom, cls] = estEsCode(code) ? [esDrapeau(), 'Espagne', 'es'] : estAdCode(code) ? [adDrapeau(), 'Andorre', 'ad'] : [mcDrapeau(), 'Monaco', 'mc'];
  return `<span class="ch-badge ${cls}-badge${mini ? ' ch-mini' : ''}" title="Commune : ${nom}">${d}${mini ? '' : '<b>' + nom + '</b>'}</span>`;
}
function iberRang(code){ return estEsCode(code) ? 'Rang en Espagne' : estAdCode(code) ? 'Rang en Andorre' : 'Rang à Monaco'; }""")
rep(A, "estLuxCode(code) ? 'Rang au Luxembourg' : 'Rang national'", "estLuxCode(code) ? 'Rang au Luxembourg' : estIberCode(code) ? iberRang(code) : 'Rang national'")
rep(A, "estLuxCode(draw.code) ? ' luxembourg' : ''", "estLuxCode(draw.code) ? ' luxembourg' : iberClasse(draw.code)")
rep(A, "estLuxCode(draw.code) ? luBadge(false) : ''", "estLuxCode(draw.code) ? luBadge(false) : estIberCode(draw.code) ? iberBadge(draw.code, false) : ''")
rep(A, "estLuxCode(draw.code) ? 'Rang lux.' : 'Rang'", "estLuxCode(draw.code) ? 'Rang lux.' : estEsCode(draw.code) ? 'Rang esp.' : 'Rang'")
rep(A, "estLuxCode(entry.code) ? ' luxembourg' : ''", "estLuxCode(entry.code) ? ' luxembourg' : iberClasse(entry.code)")
rep(A, "estLuxCode(entry.code) ? luBadge(true) : ''", "estLuxCode(entry.code) ? luBadge(true) : estIberCode(entry.code) ? iberBadge(entry.code, true) : ''")
rep(A, "estLuxCode(e.code) ? ' luxembourg' : ''", "estLuxCode(e.code) ? ' luxembourg' : iberClasse(e.code)")
rep(A, "estLuxCode(e.code) ? luBadge(true) : ''", "estLuxCode(e.code) ? luBadge(true) : estIberCode(e.code) ? iberBadge(e.code, true) : ''")

# la bulle du département : la petite carte de l'Espagne
rep(A, "DEP_PAYS_HAUT = { CH: 200, BE: 200, LU: 200 };", "DEP_PAYS_HAUT = { CH: 200, BE: 200, LU: 200, ES: 200 };   // patch541 : ES")
rep(A, "  if(pays === 'CH' || pays === 'BE' || pays === 'LU'){", "  if(pays === 'CH' || pays === 'BE' || pays === 'LU' || pays === 'ES'){")
rep(A, "pays === 'LU' ? 'data/contours-cantons-lu.json?v=1' :", "pays === 'LU' ? 'data/contours-cantons-lu.json?v=1' : pays === 'ES' ? 'data/contours-provinces-es.json?v=1' :")
rep(A, "estCantonLu(d) ? 'LU' : 'FR', ch = pays !== 'FR'", "estCantonLu(d) ? 'LU' : estProvinceEs(d) || estMicroEtat(d) ? 'ES' : 'FR', ch = pays !== 'FR'")

# zone de départ : les nouvelles régions
rep(A, "const ZD_NOUVEAU = new Set(['Suisse', 'Belgique', 'Luxembourg']);   // patch462, patch467",
       "const ZD_NOUVEAU = new Set(['Suisse', 'Belgique', 'Luxembourg'].concat(ESPAGNE ? [...new Set(Object.values(" + REG + "))] : []));   // patch462, patch467, patch541")

# Terra
rep(A, "const TP_NOMS = { FR: 'France', CH: 'Suisse', BE: 'Belgique', LU: 'Luxembourg' };", "const TP_NOMS = { FR: 'France', CH: 'Suisse', BE: 'Belgique', LU: 'Luxembourg', ES: 'Espagne' };")
rep(A, "LUXEMBOURG ? ['LU'] : []); }", "LUXEMBOURG ? ['LU'] : [], ESPAGNE ? ['ES'] : []); }")
rep(A, "  if(pays === 'LU') return luDrapeau('tp-drap tp-drap-lu');   // patch467\n",
       "  if(pays === 'LU') return luDrapeau('tp-drap tp-drap-lu');   // patch467\n  if(pays === 'ES') return esDrapeau('tp-drap tp-drap-es');   // patch541\n")
rep(A, "p === 'LU' ? 'tf-terra-lu-vu' : 'tf-terra-ch-vu') === '1'; }", "p === 'LU' ? 'tf-terra-lu-vu' : p === 'ES' ? 'tf-terra-es-vu' : 'tf-terra-ch-vu') === '1'; }")
rep(A, "  tpEcrire(p === 'BE' ? 'tf-terra-be-vu' : p === 'LU' ? 'tf-terra-lu-vu' : 'tf-terra-ch-vu', '1');",
       "  tpEcrire(p === 'BE' ? 'tf-terra-be-vu' : p === 'LU' ? 'tf-terra-lu-vu' : p === 'ES' ? 'tf-terra-es-vu' : 'tf-terra-ch-vu', '1');")
rep(A, "(pays !== 'CH' && pays !== 'BE' && pays !== 'LU')) return;", "(pays !== 'CH' && pays !== 'BE' && pays !== 'LU' && pays !== 'ES')) return;")
rep(A, "  if(bd) bd.textContent = '5 communes ' + (pays === 'LU' ? 'du ' : 'de ') + TP_NOMS[pays];",
       "  if(bd) bd.textContent = '5 communes ' + (pays === 'LU' ? 'du ' : pays === 'ES' ? 'd’' : 'de ') + TP_NOMS[pays];")
rep(A, "+ (tpNouveauVu('LU') ? 'l' : '');", "+ (tpNouveauVu('LU') ? 'l' : '') + (tpNouveauVu('ES') ? 'e' : '');")
rep(A, "  const n = { FR: 0, CH: 0, BE: 0, LU: 0 };", "  const n = { FR: 0, CH: 0, BE: 0, LU: 0, ES: 0 };")
rep(A, "communes ${p === 'BE' ? 'belges' : p === 'LU' ? 'luxembourgeoises' : 'suisses'} <span", "communes ${p === 'BE' ? 'belges' : p === 'LU' ? 'luxembourgeoises' : p === 'ES' ? 'd’Espagne et d’Andorre' : 'suisses'} <span")
rep(A, "    : p === 'LU' ? { legendaire: 1, epique: 3, rare: 10, peucommun: 37, commun: 49 }   // s3-35 : 100 communes (patch467)\n",
       "    : p === 'LU' ? { legendaire: 1, epique: 3, rare: 10, peucommun: 37, commun: 49 }   // s3-35 : 100 communes (patch467)\n"
       "    : p === 'ES' ? { legendaire: 71, epique: 242, rare: 799, peucommun: 3006, commun: 4021 }   // patch541 : 8 132 + 7 (Andorre)\n")
rep(A, "document.body.classList.toggle('luxembourg-on', !!LUXEMBOURG);   // patch467 : la règle du Luxembourg",
       "document.body.classList.toggle('luxembourg-on', !!LUXEMBOURG);   // patch467 : la règle du Luxembourg\n"
       "document.body.classList.toggle('espagne-on', !!ESPAGNE);   // patch541")

rep(A, """${tpDrapeau(p)}${p === 'LU' ? '<span class="tp-long">Luxembourg</span><span class="tp-court">Lux.</span>' : TP_NOMS[p]}""",
       """${tpDrapeau(p)}<span class="tp-nom">${p === 'LU' ? '<span class="tp-long">Luxembourg</span><span class="tp-court">Lux.</span>' : TP_NOMS[p]}</span>""")
rep(A, "  const pays3 = LUXEMBOURG ? 'de France, de Suisse, de Belgique ou du Luxembourg' :",
       "  const pays3 = ESPAGNE ? 'de France, de Suisse, de Belgique, du Luxembourg ou d’Espagne' : LUXEMBOURG ? 'de France, de Suisse, de Belgique ou du Luxembourg' :")
rep(A, "Mêmes jetons et même prix pour ${LUXEMBOURG ? 'les quatre paquets' :", "Mêmes jetons et même prix pour ${ESPAGNE ? 'les cinq paquets' : LUXEMBOURG ? 'les quatre paquets' :")
rep(A, "les raretés tombent aussi souvent dans ${LUXEMBOURG ? 'les quatre' :", "les raretés tombent aussi souvent dans ${ESPAGNE ? 'les cinq' : LUXEMBOURG ? 'les quatre' :")
rep(A, "p === 'LU' ? '5 vraies communes luxembourgeoises. ' : ''}", "p === 'LU' ? '5 vraies communes luxembourgeoises. ' : p === 'ES' ? '5 vraies communes d’Espagne ou d’Andorre. ' : ''}")

rep(A, 'aria-pressed="${pays === p}">${tpDrapeau(p)}', 'aria-pressed="${pays === p}" title="${TP_NOMS[p]}" aria-label="${TP_NOMS[p]}">${tpDrapeau(p)}')

S = 'style.css'
rep(S, ".lu-badge{ background:#00A3E0; color:#fff; }", """.lu-badge{ background:#00A3E0; color:#fff; }
/* patch541 : l'Espagne, l'Andorre, Monaco */
.tp-pays button.tp-b-es.on{ background:rgba(241,191,0,.16); color:#fff; box-shadow:inset 0 0 0 1px rgba(241,191,0,.6); }
body.espagne-on .tp-pays button{ padding:8px 8px; gap:4px; }
/* 5 pays sur un téléphone : les drapeaux seuls, et le nom du pays choisi */
@media (max-width: 520px){ body.espagne-on .tp-pays{ gap:2px; } body.espagne-on .tp-pays button{ padding:8px 10px; font-size:.82rem; }
  body.espagne-on .tp-pays small{ display:none; } body.espagne-on .tp-pays button:not(.on) .tp-nom{ display:none; }
  body.espagne-on .tp-pays .tp-long{ display:inline; } body.espagne-on .tp-pays .tp-court{ display:none; } }
.paquet.paquet-es .paquet-etiquette .tp-drap{ width:30px; height:20px; }
.es-badge{ background:#AA151B; color:#fff; } .ad-badge{ background:#10069F; color:#fff; } .mc-badge{ background:#CE1126; color:#fff; }
.es-badge svg, .ad-badge svg, .mc-badge svg{ width:15px; height:10px; border-radius:2px; box-shadow:0 0 0 1px rgba(255,255,255,.35); }
.card.espagne .carte-lisere span:nth-child(odd), .mini.espagne .mini-lisere span:nth-child(odd){ background:#AA151B; }
.card.espagne .carte-lisere span:nth-child(2), .mini.espagne .mini-lisere span:nth-child(2){ background:#F1BF00; }
.card.andorre .carte-lisere span:nth-child(1), .mini.andorre .mini-lisere span:nth-child(1){ background:#10069F; }
.card.andorre .carte-lisere span:nth-child(2), .mini.andorre .mini-lisere span:nth-child(2){ background:#FEDD00; }
.card.andorre .carte-lisere span:nth-child(3), .mini.andorre .mini-lisere span:nth-child(3){ background:#D50032; }
.card.monaco .carte-lisere span:nth-child(odd), .mini.monaco .mini-lisere span:nth-child(odd){ background:#CE1126; }
.card.monaco .carte-lisere span:nth-child(2), .mini.monaco .mini-lisere span:nth-child(2){ background:#fff; }""")
rep(S, 'body.belgique-on #panel-regles [data-s3="belgique"], body.luxembourg-on #panel-regles [data-s3="luxembourg"],',
       'body.belgique-on #panel-regles [data-s3="belgique"], body.luxembourg-on #panel-regles [data-s3="luxembourg"], body.espagne-on #panel-regles [data-s3="espagne"],')

I = 'index.html'
rep(I, '          <a href="#s3-luxembourg" data-s3="luxembourg">Luxembourg</a>\n',
       '          <a href="#s3-luxembourg" data-s3="luxembourg">Luxembourg</a>\n          <a href="#s3-espagne" data-s3="espagne">Espagne</a>\n')
rep(I, '<span data-s3="luxembourg">, cantons luxembourgeois</span>)',
       '<span data-s3="luxembourg">, cantons luxembourgeois</span><span data-s3="espagne">, provinces espagnoles, Andorre, Monaco</span>)')
rep(I, "        </details><!-- patch467 -->\n",
"""        </details><!-- patch467 -->
        <details class="regle" id="s3-espagne" data-s3="espagne">
          <summary>
            <span class="regle-icone"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="5" width="16" height="14" rx="3"/><path d="M4 9.5h16M4 14.5h16"/></svg></span>
            <h2>Espagne, Andorre, Monaco<small>52 provinces, 8 140 communes</small></h2>
            <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 9l6 6 6-6"/></svg>
          </summary>
          <div class="regle-corps">
            <p>Les <b>8 132 communes</b> d'Espagne rejoignent la carte, avec les <b>7 paroisses</b> d'Andorre et <b>Monaco</b>. Les <b>52 provinces</b> (E28 pour Madrid, E08 pour Barcelone, E41 pour Séville…) jouent le rôle des départements, et les <b>communautés autonomes</b> celui des régions (Andalousie, Catalogne, Pays basque…). L'Andorre et Monaco comptent chacun comme un département et une région. Les Canaries sont dessinées dans un encart, au sud-ouest de l'Espagne.</p>
            <p>La rareté suit la population, dans les mêmes proportions qu'en France : 71 légendaires, de Madrid à Sant Cugat del Vallès. L'Andorre et Monaco suivent les seuils de population de la France : Monaco est légendaire. Les communes gardent leur nom officiel ; les grandes villes connues en France prennent leur nom français (Séville, Saragosse, Saint-Sébastien…).</p>
            <p><b>Front</b> : elles sortent des paquets du Front et s'assiègent comme les autres ; la frontière ne compte pas pour la proximité. Les communes espagnoles sont en moyenne quatre fois plus grandes que les françaises.</p>
            <p><b>Terra</b> : au Tirage, choisis le paquet <b>Espagne</b> (communes d'Espagne et d'Andorre) : mêmes jetons et même prix. Monaco tombe dans le paquet France.</p>
            <p>Pas encore d'Espagne dans les mini-jeux (Commune du jour, Radar, Rafale, Plus ou moins), dans les contrats, dans le paquet Département de la boutique, ni dans la quête « Complète un département ».</p>
            <p class="regle-source">Contours et position des communes espagnoles : Instituto Geográfico Nacional (ign.es, CC BY 4.0). Codes et population au 1<sup>er</sup> janvier 2025 : INE. Andorre et Monaco : © contributeurs d'OpenStreetMap (ODbL), population Wikidata.</p>
          </div>
        </details><!-- patch541 -->
""")
print('patch541 : fini')
