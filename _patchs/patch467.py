# patch467 : le Luxembourg dans le jeu (éteint tant que LUXEMBOURG_OUVERT vaut false ; ?luxembourg=test pour essayer).
# Même chemin que la Belgique (patch462). Les 12 cantons (LCA, LLU, LES…) tiennent le rôle des départements, région « Luxembourg ».
# Codes des communes : « LU » + code LAU (LU0001… ; Luxembourg-Ville = LU0304). Décision de Nataël : ouverture le 22/11/2026.
# Fichiers : data/luxembourg-terre.json, data/luxembourg-frontiere.json, data/contours-cantons-lu.json, contours/<CANTON>.json (12).
# Le jour de l'ouverture : _jour-j/patch-ouverture-luxembourg.py.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'

def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')

CANT = '{"LCA":"Capellen","LCL":"Clervaux","LDI":"Diekirch","LEC":"Echternach","LES":"Esch-sur-Alzette","LGR":"Grevenmacher","LLU":"Luxembourg","LME":"Mersch","LRE":"Redange","LRM":"Remich","LVI":"Vianden","LWI":"Wiltz"}'
NB_CANT = 'LCA:9,LCL:5,LDI:10,LEC:7,LES:14,LGR:8,LLU:11,LME:10,LRE:9,LRM:7,LVI:3,LWI:7'

# ---------- app.js ----------
A = 'app.js'
rep(A, "const SUISSE = SUISSE_OUVERTE || BELGIQUE || (() => {",
"""// patch467 : le Luxembourg, même principe : LUXEMBOURG_OUVERT le jour de son ouverture, ?luxembourg=test pour essayer
// (allume aussi la Belgique, la Suisse et le fond de la saison 3). Ses 12 cantons tiennent le rôle des départements
// (code à trois lettres « L.. » : LU, VD, GR… à deux lettres sont des cantons suisses), région « Luxembourg ».
const LUXEMBOURG_OUVERT = false;
const LUXEMBOURG = LUXEMBOURG_OUVERT || (() => {
  try {
    if(/[?&]luxembourg=test\\b/.test(location.search)) sessionStorage.setItem('tf-luxembourg-test', '1');
    return sessionStorage.getItem('tf-luxembourg-test') === '1';
  } catch(e){ return /[?&]luxembourg=test\\b/.test(location.search); }
})();
const SUISSE = SUISSE_OUVERTE || BELGIQUE || LUXEMBOURG || (() => {""")
rep(A, "const BELGIQUE = BELGIQUE_OUVERTE || (() => {", "const BELGIQUE = BELGIQUE_OUVERTE || LUXEMBOURG_TEST_TOT() || (() => {")
rep(A, "const BELGIQUE_OUVERTE = false;\n",
"""const BELGIQUE_OUVERTE = false;
// patch467 : ?luxembourg=test allume aussi la Belgique (lu avant LUXEMBOURG, qui est défini plus bas)
function LUXEMBOURG_TEST_TOT(){
  try { return /[?&]luxembourg=test\\b/.test(location.search) || sessionStorage.getItem('tf-luxembourg-test') === '1'; }
  catch(e){ return /[?&]luxembourg=test\\b/.test(location.search); }
}
""")
rep(A, "// patch462 : un « département » hors de France (canton suisse ou province belge)\nconst estEtrangerDep = (dep) => estCanton(dep) || estProvinceBe(dep);\n",
"const CANTONS_LU = " + CANT + ";   // patch467\n"
"const CANT_LU_RE = /^L(CA|CL|DI|EC|ES|GR|LU|ME|RE|RM|VI|WI)$/;\n"
"const estCantonLu = (dep) => CANT_LU_RE.test(String(dep || ''));\n"
"// patch462 : un « département » hors de France (canton suisse, province belge ; patch467 : canton luxembourgeois)\n"
"const estEtrangerDep = (dep) => estCanton(dep) || estProvinceBe(dep) || estCantonLu(dep);\n")
rep(A, "const estZoneCarte = (dep) => METRO_DEPT_RE.test(dep) || (SUISSE && estCanton(dep)) || (BELGIQUE && estProvinceBe(dep));",
       "const estZoneCarte = (dep) => METRO_DEPT_RE.test(dep) || (SUISSE && estCanton(dep)) || (BELGIQUE && estProvinceBe(dep)) || (LUXEMBOURG && estCantonLu(dep));")
rep(A, "if(BELGIQUE) Object.assign(DEPT_NAMES, PROVINCES_BE);   // patch462",
       "if(BELGIQUE) Object.assign(DEPT_NAMES, PROVINCES_BE);   // patch462\nif(LUXEMBOURG) Object.assign(DEPT_NAMES, CANTONS_LU);   // patch467")

# le fond
rep(A, "        FOND_S3.voisins = voisins.filter(v => v.nom !== 'BELGIQUE');\n      } catch(e){}\n    }\n",
"""        FOND_S3.voisins = voisins.filter(v => v.nom !== 'BELGIQUE');
      } catch(e){}
    }
    if(LUXEMBOURG){   // patch467
      try {
        const [lt, lf] = await Promise.all(['luxembourg-terre.json', 'luxembourg-frontiere.json'].map(lire));
        FOND_S3.terre = FOND_S3.terre.concat(lt); FOND_S3.frontiere = FOND_S3.frontiere.concat(lf);
        FOND_S3.voisins = FOND_S3.voisins.filter(v => v.nom !== 'LUX.');
      } catch(e){}
    }
""")
rep(A, "    if(BELGIQUE){   // patch462 : les provinces\n      try { Object.assign(deps, await (await fetch('data/contours-provinces-be.json?v=1', { cache: 'force-cache' })).json()); } catch(e){}\n    }\n",
"""    if(BELGIQUE){   // patch462 : les provinces
      try { Object.assign(deps, await (await fetch('data/contours-provinces-be.json?v=1', { cache: 'force-cache' })).json()); } catch(e){}
    }
    if(LUXEMBOURG){   // patch467 : les cantons luxembourgeois
      try { Object.assign(deps, await (await fetch('data/contours-cantons-lu.json?v=1', { cache: 'force-cache' })).json()); } catch(e){}
    }
""")
rep(A, "if(BELGIQUE) for(const c in PROVINCES_BE) DEP_REGION[c] = 'Belgique';   // patch462\n",
"if(BELGIQUE) for(const c in PROVINCES_BE) DEP_REGION[c] = 'Belgique';   // patch462\n"
"if(LUXEMBOURG) for(const c in CANTONS_LU) DEP_REGION[c] = 'Luxembourg';   // patch467\n")
rep(A, "if(BELGIQUE) 'VAN:67,VBR:63,WBR:27,VWV:62,VOV:55,WHT:69,WLG:84,VLI:38,WLX:43,WNA:38,BRU:19'\n  .split(',').forEach(x => { const [d, n] = x.split(':'); COMMUNES_PAR_DEPT[d] = Number(n); });\n",
"if(BELGIQUE) 'VAN:67,VBR:63,WBR:27,VWV:62,VOV:55,WHT:69,WLG:84,VLI:38,WLX:43,WNA:38,BRU:19'\n  .split(',').forEach(x => { const [d, n] = x.split(':'); COMMUNES_PAR_DEPT[d] = Number(n); });\n"
"// patch467 : les cantons luxembourgeois (ACT)\n"
"if(LUXEMBOURG) '" + NB_CANT + "'\n"
"  .split(',').forEach(x => { const [d, n] = x.split(':'); COMMUNES_PAR_DEPT[d] = Number(n); });\n")

# fiche, cartes, profil
rep(A, "estBelgeCode(code) ? 'Rang en Belgique' : 'Rang national'", "estBelgeCode(code) ? 'Rang en Belgique' : estLuxCode(code) ? 'Rang au Luxembourg' : 'Rang national'")
rep(A, "estBelgeCode(draw.code) ? ' belgique' : ''", "estBelgeCode(draw.code) ? ' belgique' : estLuxCode(draw.code) ? ' luxembourg' : ''")
rep(A, "estBelgeCode(draw.code) ? beBadge(false) : ''", "estBelgeCode(draw.code) ? beBadge(false) : estLuxCode(draw.code) ? luBadge(false) : ''")
rep(A, "estBelgeCode(draw.code) ? 'Rang belge' : 'Rang'", "estBelgeCode(draw.code) ? 'Rang belge' : estLuxCode(draw.code) ? 'Rang lux.' : 'Rang'")
rep(A, "estBelgeCode(entry.code) ? ' belgique' : ''", "estBelgeCode(entry.code) ? ' belgique' : estLuxCode(entry.code) ? ' luxembourg' : ''")
rep(A, "estBelgeCode(entry.code) ? beBadge(true) : ''", "estBelgeCode(entry.code) ? beBadge(true) : estLuxCode(entry.code) ? luBadge(true) : ''")
rep(A, "estBelgeCode(e.code) ? ' belgique' : ''", "estBelgeCode(e.code) ? ' belgique' : estLuxCode(e.code) ? ' luxembourg' : ''")
rep(A, "estBelgeCode(e.code) ? beBadge(true) : ''", "estBelgeCode(e.code) ? beBadge(true) : estLuxCode(e.code) ? luBadge(true) : ''")

# recherche
rep(A, "  if(/^(CH|BE)\\d/.test(cc)){", "  if(/^(CH|BE|LU)\\d/.test(cc)){   // patch467 : « LU0304 » -> le canton (sinon « LU » = Lucerne)\n  ")
rep(A, "(BELGIQUE && estProvinceBe(d.toUpperCase()))){ deps.push", "(BELGIQUE && estProvinceBe(d.toUpperCase())) || (LUXEMBOURG && estCantonLu(d.toUpperCase()))){ deps.push")

# « dans le canton de Wiltz (Luxembourg) »
rep(A, "const motDep = (d) => estCanton(d) ? 'canton' : estProvinceBe(d) ? 'province' : 'département';",
       "const motDep = (d) => estCanton(d) || estCantonLu(d) ? 'canton' : estProvinceBe(d) ? 'province' : 'département';")
rep(A, "  : estProvinceBe(d) ? `dans ${PROVINCE_DANS[d] || d} (${d})`\n",
       "  : estProvinceBe(d) ? `dans ${PROVINCE_DANS[d] || d} (${d})`\n"
       "  : estCantonLu(d) ? `dans le canton ${/^[AEIOUÉ]/.test(CANTONS_LU[d] || '') ? 'd’' : 'de '}${CANTONS_LU[d] || d} (Luxembourg)`   // patch467\n")

# collection Terra
rep(A, "SUISSE && tcPays() === 'BE' ? 'Rechercher une commune ou une province…' :",
       "SUISSE && tcPays() === 'BE' ? 'Rechercher une commune ou une province…' : SUISSE && tcPays() === 'LU' ? 'Rechercher une commune ou un canton…' :")
rep(A, "(tcPays() === 'BE' ? 'Pas encore de commune belge : choisis le paquet Belgique dans l’onglet Tirage.' :",
       "(tcPays() === 'BE' ? 'Pas encore de commune belge : choisis le paquet Belgique dans l’onglet Tirage.' : tcPays() === 'LU' ? 'Pas encore de commune luxembourgeoise : choisis le paquet Luxembourg dans l’onglet Tirage.' :")
rep(A, "placeholder=\"${BELGIQUE ? 'Département, canton ou province' :", "placeholder=\"${BELGIQUE || LUXEMBOURG ? 'Département, canton ou province' :")

# la bulle du département : la petite carte du Luxembourg pour un canton
rep(A, "DEP_PAYS_HAUT = { CH: 200, BE: 200 };", "DEP_PAYS_HAUT = { CH: 200, BE: 200, LU: 200 };   // patch467 : LU")
rep(A, """  if(pays === 'CH' || pays === 'BE'){
    if(DEP_PAYS[pays]) return Promise.resolve(DEP_PAYS[pays]);
    const f = pays === 'BE' ? 'data/contours-provinces-be.json?v=1' : 'data/contours-cantons.json?v=1';""",
"""  if(pays === 'CH' || pays === 'BE' || pays === 'LU'){
    if(DEP_PAYS[pays]) return Promise.resolve(DEP_PAYS[pays]);
    const f = pays === 'BE' ? 'data/contours-provinces-be.json?v=1' : pays === 'LU' ? 'data/contours-cantons-lu.json?v=1' : 'data/contours-cantons.json?v=1';   // patch467""")
rep(A, "  const pays = estCanton(d) ? 'CH' : estProvinceBe(d) ? 'BE' : 'FR',",
       "  const pays = estCanton(d) ? 'CH' : estProvinceBe(d) ? 'BE' : estCantonLu(d) ? 'LU' : 'FR',")

# zone de départ
rep(A, "const ZD_NOUVEAU = new Set(['Suisse', 'Belgique']);   // patch462", "const ZD_NOUVEAU = new Set(['Suisse', 'Belgique', 'Luxembourg']);   // patch462, patch467")

# Terra : codes, drapeau, paquet, choix du pays
rep(A, """function estEtrangerCode(code){ return estSuisseCode(code) || estBelgeCode(code); }
function paysDuCode(code){ return estSuisseCode(code) ? 'CH' : estBelgeCode(code) ? 'BE' : 'FR'; }""",
"""function estLuxCode(code){ return /^LU\\d/.test(String(code || '')); }   // patch467
function estEtrangerCode(code){ return estSuisseCode(code) || estBelgeCode(code) || estLuxCode(code); }
function paysDuCode(code){ return estSuisseCode(code) ? 'CH' : estBelgeCode(code) ? 'BE' : estLuxCode(code) ? 'LU' : 'FR'; }
function luDrapeau(cls){ return `<svg${cls ? ` class="${cls}"` : ''} viewBox="0 0 3 2" aria-hidden="true"><rect width="3" height=".667" fill="#EF3340" stroke="none"/><rect y=".667" width="3" height=".667" fill="#fff" stroke="none"/><rect y="1.333" width="3" height=".667" fill="#00A3E0" stroke="none"/></svg>`; }
function luBadge(mini){ return `<span class="ch-badge lu-badge${mini ? ' ch-mini' : ''}" title="Commune luxembourgeoise">${luDrapeau()}${mini ? '' : '<b>Luxembourg</b>'}</span>`; }""")
rep(A, "const TP_NOMS = { FR: 'France', CH: 'Suisse', BE: 'Belgique' };", "const TP_NOMS = { FR: 'France', CH: 'Suisse', BE: 'Belgique', LU: 'Luxembourg' };")
rep(A, "function tpPaysOuverts(){ return ['FR'].concat(SUISSE ? ['CH'] : [], BELGIQUE ? ['BE'] : []); }",
       "function tpPaysOuverts(){ return ['FR'].concat(SUISSE ? ['CH'] : [], BELGIQUE ? ['BE'] : [], LUXEMBOURG ? ['LU'] : []); }")
rep(A, "  if(pays === 'BE') return beDrapeau('tp-drap tp-drap-be');   // patch462\n",
       "  if(pays === 'BE') return beDrapeau('tp-drap tp-drap-be');   // patch462\n  if(pays === 'LU') return luDrapeau('tp-drap tp-drap-lu');   // patch467\n")
rep(A, "function tpNouveauVu(p){ return tpLire(p === 'BE' ? 'tf-terra-be-vu' : 'tf-terra-ch-vu') === '1'; }",
       "function tpNouveauVu(p){ return tpLire(p === 'BE' ? 'tf-terra-be-vu' : p === 'LU' ? 'tf-terra-lu-vu' : 'tf-terra-ch-vu') === '1'; }")
rep(A, "  tpEcrire(p === 'BE' ? 'tf-terra-be-vu' : 'tf-terra-ch-vu', '1');",
       "  tpEcrire(p === 'BE' ? 'tf-terra-be-vu' : p === 'LU' ? 'tf-terra-lu-vu' : 'tf-terra-ch-vu', '1');")
rep(A, """  if(!pack || !SUISSE || (pays !== 'CH' && pays !== 'BE')) return;
  pack.classList.add(pays === 'BE' ? 'paquet-be' : 'paquet-ch');   // patch462""",
"""  if(!pack || !SUISSE || (pays !== 'CH' && pays !== 'BE' && pays !== 'LU')) return;
  pack.classList.add('paquet-' + pays.toLowerCase());   // patch462, patch467""")
rep(A, "  if(bd) bd.textContent = '5 communes de ' + TP_NOMS[pays];",
       "  if(bd) bd.textContent = '5 communes ' + (pays === 'LU' ? 'du ' : 'de ') + TP_NOMS[pays];")
# 4 pays : sur un petit écran, « Lux. »
rep(A, "${tpDrapeau(p)}${TP_NOMS[p]}${p === 'FR' || coll || tpNouveauVu(p) ? '' : '<small>Nouveau</small>'}</button>`).join('')   // patch462",
       "${tpDrapeau(p)}${p === 'LU' ? '<span class=\"tp-long\">Luxembourg</span><span class=\"tp-court\">Lux.</span>' : TP_NOMS[p]}${p === 'FR' || coll || tpNouveauVu(p) ? '' : '<small>Nouveau</small>'}</button>`).join('')   // patch462, patch467")
rep(A, "  const pays3 = BELGIQUE ? 'de France, de Suisse ou de Belgique' : 'de France ou de Suisse';   // patch462",
       "  const pays3 = LUXEMBOURG ? 'de France, de Suisse, de Belgique ou du Luxembourg' : BELGIQUE ? 'de France, de Suisse ou de Belgique' : 'de France ou de Suisse';   // patch462, patch467")
rep(A, "etat = p + (tpNouveauVu('CH') ? 'v' : '') + (tpNouveauVu('BE') ? 'b' : '');",
       "etat = p + (tpNouveauVu('CH') ? 'v' : '') + (tpNouveauVu('BE') ? 'b' : '') + (tpNouveauVu('LU') ? 'l' : '');")
rep(A, "p === 'BE' ? '5 vraies communes belges. ' : ''}Mêmes jetons et même prix pour ${BELGIQUE ? 'les trois paquets' : 'les deux paquets'} ; les raretés tombent aussi souvent dans ${BELGIQUE ? 'les trois' : 'les deux'}.",
       "p === 'BE' ? '5 vraies communes belges. ' : p === 'LU' ? '5 vraies communes luxembourgeoises. ' : ''}Mêmes jetons et même prix pour ${LUXEMBOURG ? 'les quatre paquets' : BELGIQUE ? 'les trois paquets' : 'les deux paquets'} ; les raretés tombent aussi souvent dans ${LUXEMBOURG ? 'les quatre' : BELGIQUE ? 'les trois' : 'les deux'}.")
rep(A, "  const t = p === 'BE' ? { legendaire: 5, epique: 16, rare: 56, peucommun: 209, commun: 279 }   // s3-32 : 565 communes (patch462)\n",
       "  const t = p === 'BE' ? { legendaire: 5, epique: 16, rare: 56, peucommun: 209, commun: 279 }   // s3-32 : 565 communes (patch462)\n"
       "    : p === 'LU' ? { legendaire: 1, epique: 3, rare: 10, peucommun: 37, commun: 49 }   // s3-35 : 100 communes (patch467)\n")
rep(A, "  const n = { FR: 0, CH: 0, BE: 0 };   // patch462 : la Belgique aussi", "  const n = { FR: 0, CH: 0, BE: 0, LU: 0 };   // patch462 : la Belgique aussi ; patch467 : le Luxembourg")
rep(A, "communes ${p === 'BE' ? 'belges' : 'suisses'} <span", "communes ${p === 'BE' ? 'belges' : p === 'LU' ? 'luxembourgeoises' : 'suisses'} <span")
rep(A, "${fmtNombre(tcTotalPays(x))} en ${TP_NOMS[x]}</span>", "${fmtNombre(tcTotalPays(x))} ${x === 'LU' ? 'au' : 'en'} ${TP_NOMS[x]}</span>")

rep(A, "document.body.classList.toggle('belgique-on', !!BELGIQUE);   // patch462 : la règle de la Belgique",
       "document.body.classList.toggle('belgique-on', !!BELGIQUE);   // patch462 : la règle de la Belgique\n"
       "document.body.classList.toggle('luxembourg-on', !!LUXEMBOURG);   // patch467 : la règle du Luxembourg")

# la trame des cantons à l'écran sans commune possédée : déjà générale (estEtrangerDep), rien à faire

# ---------- style.css ----------
S = 'style.css'
rep(S, "@media (max-width: 400px){ body.belgique-on .tp-pays button{ padding:8px 9px; font-size:.82rem; } body.belgique-on .tp-pays small{ display:none; } }",
"""@media (max-width: 400px){ body.belgique-on .tp-pays button{ padding:8px 9px; font-size:.82rem; } body.belgique-on .tp-pays small{ display:none; } }
/* patch467 : le Luxembourg */
.tp-pays button.tp-b-lu.on{ background:rgba(0,163,224,.18); color:#fff; box-shadow:inset 0 0 0 1px rgba(0,163,224,.65); }
.tp-pays .tp-court{ display:none; }
body.luxembourg-on .tp-pays button{ padding:9px 10px; gap:5px; }
@media (max-width: 440px){ body.luxembourg-on .tp-pays button{ padding:8px 8px; font-size:.8rem; } body.luxembourg-on .tp-pays .tp-long{ display:none; } body.luxembourg-on .tp-pays .tp-court{ display:inline; } }
.paquet.paquet-lu .paquet-etiquette .tp-drap{ width:30px; height:20px; }
.paquet.paquet-lu .paquet-titre{ font-size:2.05rem; }
.paquet.paquet-lu .paquet-bande{ font-size:1.02rem; }
.lu-badge{ background:#00A3E0; color:#fff; }
.lu-badge svg{ width:15px; height:10px; border-radius:2px; box-shadow:0 0 0 1px rgba(255,255,255,.35); }
.card.luxembourg .carte-lisere span:nth-child(1), .mini.luxembourg .mini-lisere span:nth-child(1){ background:#EF3340; }
.card.luxembourg .carte-lisere span:nth-child(2), .mini.luxembourg .mini-lisere span:nth-child(2){ background:#fff; }
.card.luxembourg .carte-lisere span:nth-child(3), .mini.luxembourg .mini-lisere span:nth-child(3){ background:#00A3E0; }""")
rep(S, "body.belgique-on #panel-regles [data-s3=\"belgique\"],", "body.belgique-on #panel-regles [data-s3=\"belgique\"], body.luxembourg-on #panel-regles [data-s3=\"luxembourg\"],")

# ---------- index.html : la règle ----------
I = 'index.html'
rep(I, '          <a href="#s3-belgique" data-s3="belgique">Belgique</a>\n',
       '          <a href="#s3-belgique" data-s3="belgique">Belgique</a>\n          <a href="#s3-luxembourg" data-s3="luxembourg">Luxembourg</a>\n')
rep(I, '<span data-s3="belgique">, provinces belges</span>)',
       '<span data-s3="belgique">, provinces belges</span><span data-s3="luxembourg">, cantons luxembourgeois</span>)')
rep(I, "        </details><!-- patch462 -->\n",
"""        </details><!-- patch462 -->
        <details class="regle" id="s3-luxembourg" data-s3="luxembourg">
          <summary>
            <span class="regle-icone"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="5" width="16" height="14" rx="3"/><path d="M4 9.7h16M4 14.3h16"/></svg></span>
            <h2>Luxembourg<small>12 cantons, 100 communes</small></h2>
            <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 9l6 6 6-6"/></svg>
          </summary>
          <div class="regle-corps">
            <p>Les <b>100 communes</b> du Luxembourg rejoignent la carte. Ses <b>12 cantons</b> (LLU pour Luxembourg, LES pour Esch-sur-Alzette, LWI pour Wiltz…) jouent le rôle des départements, et forment ensemble la région <b>Luxembourg</b>. La rareté suit la population, dans les mêmes proportions qu'en France : une seule légendaire, la ville de Luxembourg (<b>n° 1 / 1</b>). Les communes gardent leur nom officiel.</p>
            <p><b>Front</b> : elles sortent des paquets du Front et s'assiègent comme les autres ; la frontière ne compte pas pour la proximité. Chaque canton a moins de 20 communes : il rapporte au prorata, comme les petits cantons suisses. Région Luxembourg : seul en tête avec 10 % ou plus dans plus de la moitié des cantons (<b>7 sur 12</b>).</p>
            <p><b>Terra</b> : au Tirage, choisis <b>France</b>, <b>Suisse</b>, <b>Belgique</b> ou <b>Luxembourg</b> : mêmes jetons et même prix, même tirage de la rareté. Ta collection a son choix de pays ; Ma France reste française.</p>
            <p>Pas encore de Luxembourg dans les mini-jeux (Commune du jour, Radar, Rafale, Plus ou moins), dans les contrats, dans le paquet Département de la boutique, ni dans la quête « Complète un département ».</p>
            <p class="regle-source">Contours des communes et des cantons : Administration du cadastre et de la topographie (data.public.lu, CC0). Population : Registre national des personnes physiques (CTIE, octobre 2026).</p>
          </div>
        </details><!-- patch467 -->
""")

# ---------- direct/direct.js : la carte en direct ----------
D = 'direct/direct.js'
rep(D, "const BELGIQUE = BELGIQUE_OUVERTE || /[?&]belgique=test\\b/.test(location.search);",
"""// patch467 : le Luxembourg, même interrupteur que le jeu (LUXEMBOURG_OUVERT, ?luxembourg=test)
const LUXEMBOURG_OUVERT = false;
const LUXEMBOURG = LUXEMBOURG_OUVERT || /[?&]luxembourg=test\\b/.test(location.search);
const BELGIQUE = BELGIQUE_OUVERTE || LUXEMBOURG || /[?&]belgique=test\\b/.test(location.search);""")
rep(D, "if(BELGIQUE) Object.assign(DEPT_NAMES, {", "if(LUXEMBOURG) Object.assign(DEPT_NAMES, " + CANT + ");   // patch467\nif(BELGIQUE) Object.assign(DEPT_NAMES, {")
rep(D, "      if(fb) D.frontiere = chemin((frontiere || []).concat(fb));\n    }\n",
"""      if(fb) D.frontiere = chemin((frontiere || []).concat(fb));
    }
    if(LUXEMBOURG){   // patch467 : les cantons et la frontière luxembourgeoise
      const [cl, fl] = await Promise.all([lire('contours-cantons-lu.json'), lire('luxembourg-frontiere.json')]);
      for(const [c, rings] of Object.entries(cl || {})){ D.depBords.push(chemin(rings)); liste.push(c); }
      if(fl){ const pf = chemin(fl); if(D.frontiere) D.frontiere.addPath(pf); else D.frontiere = pf; }
    }
""")
rep(D, "if(p) p.textContent = BELGIQUE ? 'Les 37 000 communes de France, de Suisse et de Belgique, à prendre. Gratuit.' :",
       "if(p) p.textContent = LUXEMBOURG ? 'Les 37 000 communes de France, de Suisse, de Belgique et du Luxembourg, à prendre. Gratuit.' : BELGIQUE ? 'Les 37 000 communes de France, de Suisse et de Belgique, à prendre. Gratuit.' :")
print('patch467 : fini')
