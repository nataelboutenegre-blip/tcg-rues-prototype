# patch462 : la Belgique dans le jeu (éteinte tant que BELGIQUE_OUVERTE vaut false ; ?belgique=test pour essayer).
# Les 11 provinces (VAN, WLG, BRU…) tiennent le rôle des départements, région « Belgique ».
# Fichiers : data/belgique-terre.json, data/belgique-frontiere.json, data/contours-provinces-be.json,
# contours/<PROV>.json (11). Le jour de l'ouverture : _jour-j/patch-ouverture-belgique.py.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'

def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')

PROV = '{"VAN":"Anvers","VBR":"Brabant flamand","WBR":"Brabant wallon","VWV":"Flandre-Occidentale","VOV":"Flandre-Orientale","WHT":"Hainaut","WLG":"Liège","VLI":"Limbourg","WLX":"Luxembourg","WNA":"Namur","BRU":"Bruxelles-Capitale"}'
NB_PROV = 'VAN:67,VBR:63,WBR:27,VWV:62,VOV:55,WHT:69,WLG:84,VLI:38,WLX:43,WNA:38,BRU:19'

# ---------- app.js ----------
A = 'app.js'
rep(A, "const SUISSE_OUVERTE = false;\nconst SUISSE = SUISSE_OUVERTE || (() => {",
"""const SUISSE_OUVERTE = false;
// patch462 : la Belgique (pendant la saison 3), même principe : BELGIQUE_OUVERTE le jour de son
// ouverture, ?belgique=test pour essayer (allume aussi la Suisse et le fond de la saison 3).
// Les 11 provinces tiennent le rôle des départements (code à trois lettres, région « Belgique »).
const BELGIQUE_OUVERTE = false;
const BELGIQUE = BELGIQUE_OUVERTE || (() => {
  try {
    if(/[?&]belgique=test\\b/.test(location.search)) sessionStorage.setItem('tf-belgique-test', '1');
    return sessionStorage.getItem('tf-belgique-test') === '1';
  } catch(e){ return /[?&]belgique=test\\b/.test(location.search); }
})();
const SUISSE = SUISSE_OUVERTE || BELGIQUE || (() => {""")
rep(A, "const estCanton = (dep) => CANTON_RE.test(String(dep || ''));\n",
"const estCanton = (dep) => CANTON_RE.test(String(dep || ''));\n"
"const PROVINCES_BE = " + PROV + ";   // patch462\n"
"const PROV_BE_RE = /^(VAN|VBR|WBR|VWV|VOV|WHT|WLG|VLI|WLX|WNA|BRU)$/;\n"
"const estProvinceBe = (dep) => PROV_BE_RE.test(String(dep || ''));\n"
"// patch462 : un « département » hors de France (canton suisse ou province belge)\n"
"const estEtrangerDep = (dep) => estCanton(dep) || estProvinceBe(dep);\n")
rep(A, "const estZoneCarte = (dep) => METRO_DEPT_RE.test(dep) || (SUISSE && estCanton(dep));\nif(SUISSE) Object.assign(DEPT_NAMES, CANTONS);",
"const estZoneCarte = (dep) => METRO_DEPT_RE.test(dep) || (SUISSE && estCanton(dep)) || (BELGIQUE && estProvinceBe(dep));\n"
"if(SUISSE) Object.assign(DEPT_NAMES, CANTONS);\nif(BELGIQUE) Object.assign(DEPT_NAMES, PROVINCES_BE);   // patch462")

# le fond : la Belgique rejoint la terre et la frontière, et quitte les voisins éteints
rep(A, "    FOND_S3 = { terre, frontiere, lacs, voisins, chemins: null };\n",
"""    FOND_S3 = { terre, frontiere, lacs, voisins, chemins: null };
    if(BELGIQUE){   // patch462
      try {
        const [bt, bf] = await Promise.all(['belgique-terre.json', 'belgique-frontiere.json'].map(lire));
        FOND_S3.terre = terre.concat(bt); FOND_S3.frontiere = frontiere.concat(bf);
        FOND_S3.voisins = voisins.filter(v => v.nom !== 'BELGIQUE');
      } catch(e){}
    }
""")
rep(A, "      try { Object.assign(deps, await (await fetch('data/contours-cantons.json?v=1', { cache: 'force-cache' })).json()); } catch(e){}\n    }\n",
"""      try { Object.assign(deps, await (await fetch('data/contours-cantons.json?v=1', { cache: 'force-cache' })).json()); } catch(e){}
    }
    if(BELGIQUE){   // patch462 : les provinces
      try { Object.assign(deps, await (await fetch('data/contours-provinces-be.json?v=1', { cache: 'force-cache' })).json()); } catch(e){}
    }
""")
rep(A, "if(SUISSE) for(const c in CANTONS) DEP_REGION[c] = 'Suisse';   // patch330\n",
"if(SUISSE) for(const c in CANTONS) DEP_REGION[c] = 'Suisse';   // patch330\n"
"if(BELGIQUE) for(const c in PROVINCES_BE) DEP_REGION[c] = 'Belgique';   // patch462\n")
rep(A, "  .split(',').forEach(x => { const [d, n] = x.split(':'); COMMUNES_PAR_DEPT[d] = Number(n); });\n",
"  .split(',').forEach(x => { const [d, n] = x.split(':'); COMMUNES_PAR_DEPT[d] = Number(n); });\n"
"// patch462 : les provinces belges (Statbel, 1/1/2025)\n"
"if(BELGIQUE) '" + NB_PROV + "'\n"
"  .split(',').forEach(x => { const [d, n] = x.split(':'); COMMUNES_PAR_DEPT[d] = Number(n); });\n")

# fiche, profil
rep(A, "estSuisseCode(code) ? 'Rang en Suisse' : 'Rang national'", "estSuisseCode(code) ? 'Rang en Suisse' : estBelgeCode(code) ? 'Rang en Belgique' : 'Rang national'")
rep(A, "(estSuisseCode(draw.code) ? ' suisse' : '')", "(estSuisseCode(draw.code) ? ' suisse' : estBelgeCode(draw.code) ? ' belgique' : '')")
rep(A, "estSuisseCode(draw.code) ? chBadge(false) : ''", "estSuisseCode(draw.code) ? chBadge(false) : estBelgeCode(draw.code) ? beBadge(false) : ''")
rep(A, "estSuisseCode(draw.code) ? 'Rang suisse' : 'Rang'", "estSuisseCode(draw.code) ? 'Rang suisse' : estBelgeCode(draw.code) ? 'Rang belge' : 'Rang'")
rep(A, "${estSuisseCode(entry.code) ? ' suisse' : ''}", "${estSuisseCode(entry.code) ? ' suisse' : estBelgeCode(entry.code) ? ' belgique' : ''}")
rep(A, "${estSuisseCode(entry.code) ? chBadge(true) : ''}", "${estSuisseCode(entry.code) ? chBadge(true) : estBelgeCode(entry.code) ? beBadge(true) : ''}")
rep(A, "${estSuisseCode(e.code) ? ' suisse' : ''}", "${estSuisseCode(e.code) ? ' suisse' : estBelgeCode(e.code) ? ' belgique' : ''}")
rep(A, "estSuisseCode(e.code) ? chBadge(true) : ''", "estSuisseCode(e.code) ? chBadge(true) : estBelgeCode(e.code) ? beBadge(true) : ''")

# recherche
rep(A, "  if(t.length < 3) return null;\n  const codes = Object.keys(DEPT_NAMES).filter(c => !cantonsSeuls || estCanton(c));",
"""  let provincesSeules = false;   // patch462 : « province de Liège » -> seulement les provinces belges
  if(BELGIQUE){ const m = t.match(/^province(?:des|du|de|d)?(.{3,})$/); if(m){ t = m[1]; provincesSeules = true; } }
  if(t.length < 3) return null;
  const codes = Object.keys(DEPT_NAMES).filter(c => (!cantonsSeuls || estCanton(c)) && (!provincesSeules || estProvinceBe(c)));""")
rep(A, """      || (String(dept).length > 2 ? String(dept).toLowerCase().startsWith(recherche)
          : estCanton(dept) ? String(dept).toLowerCase() === recherche   // patch332 : un code de canton se tape en entier
          : String(dept).toLowerCase().includes(recherche))""",
"""      || (estEtrangerDep(dept) ? String(dept).toLowerCase() === recherche   // patch332, patch462 : un code de canton ou de province se tape en entier
          : String(dept).length > 2 ? String(dept).toLowerCase().startsWith(recherche)
          : String(dept).toLowerCase().includes(recherche))""")
rep(A, "  if(/^CH\\d/.test(cc)){   // patch330 : « CH6621 » -> le canton, lu dans les données",
       "  if(/^(CH|BE)\\d/.test(cc)){   // patch330 : « CH6621 » -> le canton, lu dans les données ; patch462 : « BE11002 » -> la province (sinon « BE » = Berne)")
rep(A, "(code ? (String(code).startsWith('97') ? String(code).slice(0, 3) : String(code).slice(0, 2)) : '')",
       "(code ? depDuCode(code) : '')")   # patch462 : réveil, codes suisses et belges compris
rep(A, "codesDepartements(saisi).filter(k => !estCanton(k));", "codesDepartements(saisi).filter(k => !estEtrangerDep(k));")
rep(A, "(SUISSE && estCanton(d.toUpperCase()))){ deps.push", "(SUISSE && estCanton(d.toUpperCase())) || (BELGIQUE && estProvinceBe(d.toUpperCase()))){ deps.push")
rep(A, "!estCanton(d)", "!estEtrangerDep(d)", 6)
rep(A, "if(!estOutremer(e.dept) && !estSuisseCode(e.code)) n++;", "if(!estOutremer(e.dept) && !estEtrangerCode(e.code)) n++;")

# « dans le canton de Vaud », « dans la province de Liège »
rep(A, "const motDep = (d) => estCanton(d) ? 'canton' : 'département';\nconst dansDept = (d) => estCanton(d) ? `dans le canton ${cantonDe(d)} (${d})`\n",
"""const PROVINCE_DANS = { VAN: 'la province d’Anvers', VBR: 'le Brabant flamand', WBR: 'le Brabant wallon', VWV: 'la Flandre-Occidentale',
  VOV: 'la Flandre-Orientale', WHT: 'le Hainaut', WLG: 'la province de Liège', VLI: 'le Limbourg', WLX: 'la province de Luxembourg',
  WNA: 'la province de Namur', BRU: 'la Région de Bruxelles-Capitale' };   // patch462
const motDep = (d) => estCanton(d) ? 'canton' : estProvinceBe(d) ? 'province' : 'département';
const dansDept = (d) => estCanton(d) ? `dans le canton ${cantonDe(d)} (${d})`
  : estProvinceBe(d) ? `dans ${PROVINCE_DANS[d] || d} (${d})`
""")

# collection Terra : le pays choisi parmi France, Suisse, Belgique
rep(A, "const totV = SUISSE && tcPays() === 'CH' ? tcTotauxSuisse() : tot;   // patch407",
       "const totV = SUISSE && tcPays() !== 'FR' ? tcTotauxPays(tcPays()) : tot;   // patch407, patch462")
rep(A, "${SUISSE && tcPays() === 'CH' ? 'Rechercher une commune ou un canton…' : 'Rechercher une commune ou un département…'}",
       "${SUISSE && tcPays() === 'CH' ? 'Rechercher une commune ou un canton…' : SUISSE && tcPays() === 'BE' ? 'Rechercher une commune ou une province…' : 'Rechercher une commune ou un département…'}")
rep(A, ".filter(e => !SUISSE || estSuisseCode(e.code) === (tcPays() === 'CH'))   // patch407 : le pays choisi",
       ".filter(e => !SUISSE || paysDuCode(e.code) === tcPays())   // patch407, patch462 : le pays choisi")
rep(A, "${SUISSE && tcPays() === 'CH' && ![...terraCollection.keys()].some(estSuisseCode) ? 'Pas encore de commune suisse : choisis le paquet Suisse dans l’onglet Tirage.' :",
       "${SUISSE && tcPays() !== 'FR' && ![...terraCollection.keys()].some(c => paysDuCode(c) === tcPays()) ? (tcPays() === 'BE' ? 'Pas encore de commune belge : choisis le paquet Belgique dans l’onglet Tirage.' : 'Pas encore de commune suisse : choisis le paquet Suisse dans l’onglet Tirage.') :")

# réglages des alertes par département
rep(A, "placeholder=\"${SUISSE ? 'Département ou canton' : 'Nom ou numéro du département'}\"",
       "placeholder=\"${BELGIQUE ? 'Département, canton ou province' : SUISSE ? 'Département ou canton' : 'Nom ou numéro du département'}\"")

# la bulle du département : une petite carte de la Belgique pour une province
rep(A, "var depCheminsCH = null, depCheminsCHP = null, depCheminsCHHaut = 200;   // patch414 : les cantons, sur la carte de la Suisse",
       "var DEP_PAYS = {}, DEP_PAYS_P = {}, DEP_PAYS_HAUT = { CH: 200, BE: 200 };   // patch414 : les cantons sur la carte de la Suisse ; patch462 : les provinces sur celle de la Belgique")
rep(A, "function depCheminsTracer(C, carre){", "function depCheminsTracer(C, carre, pays){")
rep(A, "  if(!carre) depCheminsCHHaut = Math.ceil((y1 - y0) * e + 10);", "  if(!carre) DEP_PAYS_HAUT[pays] = Math.ceil((y1 - y0) * e + 10);")
rep(A, """function depCheminsCharger(suisse){
  if(suisse){
    if(depCheminsCH) return Promise.resolve(depCheminsCH);
    if(!depCheminsCHP) depCheminsCHP = fetch('data/contours-cantons.json?v=1', { cache: 'force-cache' }).then(r => r.json())
      .then(C => (depCheminsCH = depCheminsTracer(C, false))).catch(() => { depCheminsCHP = null; return null; });
    return depCheminsCHP;
  }""", """function depCheminsCharger(pays){
  if(pays === 'CH' || pays === 'BE'){
    if(DEP_PAYS[pays]) return Promise.resolve(DEP_PAYS[pays]);
    const f = pays === 'BE' ? 'data/contours-provinces-be.json?v=1' : 'data/contours-cantons.json?v=1';
    if(!DEP_PAYS_P[pays]) DEP_PAYS_P[pays] = fetch(f, { cache: 'force-cache' }).then(r => r.json())
      .then(C => (DEP_PAYS[pays] = depCheminsTracer(C, false, pays))).catch(() => { DEP_PAYS_P[pays] = null; return null; });
    return DEP_PAYS_P[pays];
  }""")
rep(A, "  const ch = estCanton(d), C = await depCheminsCharger(ch);   // patch414",
       "  const pays = estCanton(d) ? 'CH' : estProvinceBe(d) ? 'BE' : 'FR', ch = pays !== 'FR', C = await depCheminsCharger(pays);   // patch414, patch462")
rep(A, "viewBox=\"0 0 200 ${ch ? depCheminsCHHaut : 200}\"", "viewBox=\"0 0 200 ${ch ? DEP_PAYS_HAUT[pays] : 200}\"")

# zone de départ : la Belgique, nouvelle, après les régions françaises
rep(A, "const ZD_NOUVEAU = new Set(['Suisse']);", "const ZD_NOUVEAU = new Set(['Suisse', 'Belgique']);   // patch462")
rep(A, ".sort((a, c) => (a.zone === 'Suisse') - (c.zone === 'Suisse') || a.zone.localeCompare(c.zone, 'fr'));",
       ".sort((a, c) => ZD_NOUVEAU.has(a.zone) - ZD_NOUVEAU.has(c.zone) || a.zone.localeCompare(c.zone, 'fr'));")

# le paquet Terra par pays, et la collection
rep(A, "function estSuisseCode(code){ return /^CH\\d/.test(String(code || '')); }\n",
"""function estSuisseCode(code){ return /^CH\\d/.test(String(code || '')); }
function estBelgeCode(code){ return /^BE\\d/.test(String(code || '')); }   // patch462
function estEtrangerCode(code){ return estSuisseCode(code) || estBelgeCode(code); }
function paysDuCode(code){ return estSuisseCode(code) ? 'CH' : estBelgeCode(code) ? 'BE' : 'FR'; }
function beDrapeau(cls){ return `<svg${cls ? ` class="${cls}"` : ''} viewBox="0 0 3 2" aria-hidden="true"><rect width="1" height="2" fill="#1A1A1A" stroke="none"/><rect x="1" width="1" height="2" fill="#FDDA24" stroke="none"/><rect x="2" width="1" height="2" fill="#EF3340" stroke="none"/></svg>`; }
function beBadge(mini){ return `<span class="ch-badge be-badge${mini ? ' ch-mini' : ''}" title="Commune belge">${beDrapeau()}${mini ? '' : '<b>Belgique</b>'}</span>`; }
const TP_NOMS = { FR: 'France', CH: 'Suisse', BE: 'Belgique' };
function tpPaysOuverts(){ return ['FR'].concat(SUISSE ? ['CH'] : [], BELGIQUE ? ['BE'] : []); }
function tpPaysValide(p){ return tpPaysOuverts().includes(p) ? p : 'FR'; }
""")
rep(A, "function tpDrapeau(pays){\n  return pays === 'CH'",
       "function tpDrapeau(pays){\n  if(pays === 'BE') return beDrapeau('tp-drap tp-drap-be');   // patch462\n  return pays === 'CH'")
rep(A, """function tpPays(){ return SUISSE && tpLire('tf-terra-pays') === 'CH' ? 'CH' : 'FR'; }
function tcPays(){ return SUISSE && tpLire('tf-coll-pays') === 'CH' ? 'CH' : 'FR'; }
function tpNouveauVu(){ return tpLire('tf-terra-ch-vu') === '1'; }""",
"""function tpPays(){ return SUISSE ? tpPaysValide(tpLire('tf-terra-pays')) : 'FR'; }   // patch462 : FR, CH ou BE
function tcPays(){ return SUISSE ? tpPaysValide(tpLire('tf-coll-pays')) : 'FR'; }
function tpNouveauVu(p){ return tpLire(p === 'BE' ? 'tf-terra-be-vu' : 'tf-terra-ch-vu') === '1'; }""")
rep(A, """  if(p !== 'CH') return args;
  tpEcrire('tf-terra-ch-vu', '1');
  return Object.assign({}, args, { p_pays: 'CH' });""",
"""  if(p === 'FR') return args;
  tpEcrire(p === 'BE' ? 'tf-terra-be-vu' : 'tf-terra-ch-vu', '1');
  return Object.assign({}, args, { p_pays: p });""")
rep(A, """  if(!pack || !SUISSE || pays !== 'CH') return;
  pack.classList.add('paquet-ch');
  const et = pack.querySelector('.paquet-etiquette');
  if(et) et.innerHTML = tpDrapeau('CH') + '<span class="paquet-titre">Paquet Suisse</span>';
  const bd = pack.querySelector('.paquet-bande');
  if(bd) bd.textContent = '5 communes de Suisse';""",
"""  if(!pack || !SUISSE || (pays !== 'CH' && pays !== 'BE')) return;
  pack.classList.add(pays === 'BE' ? 'paquet-be' : 'paquet-ch');   // patch462
  const et = pack.querySelector('.paquet-etiquette');
  if(et) et.innerHTML = tpDrapeau(pays) + '<span class="paquet-titre">Paquet ' + TP_NOMS[pays] + '</span>';
  const bd = pack.querySelector('.paquet-bande');
  if(bd) bd.textContent = '5 communes de ' + TP_NOMS[pays];""")
rep(A, """    + `<button type="button" ${at}="FR" class="${pays === 'FR' ? 'on' : ''}" aria-pressed="${pays === 'FR'}">${tpDrapeau('FR')}France</button>`
    + `<button type="button" ${at}="CH" class="tp-b-ch${pays === 'CH' ? ' on' : ''}" aria-pressed="${pays === 'CH'}">${tpDrapeau('CH')}Suisse${coll || tpNouveauVu() ? '' : '<small>Nouveau</small>'}</button></div>`;""",
"""    + tpPaysOuverts().map(p => `<button type="button" ${at}="${p}" class="${p === 'FR' ? '' : 'tp-b-' + p.toLowerCase()}${pays === p ? ' on' : ''}" aria-pressed="${pays === p}">${tpDrapeau(p)}${TP_NOMS[p]}${p === 'FR' || coll || tpNouveauVu(p) ? '' : '<small>Nouveau</small>'}</button>`).join('')   // patch462
    + '</div>';""")
rep(A, "  if(sub && !sub.dataset.tpAvant){ sub.dataset.tpAvant = sub.textContent; sub.textContent = 'Chaque carte tirée est une vraie commune, de France ou de Suisse, à sa vraie position géographique.",
       "  const pays3 = BELGIQUE ? 'de France, de Suisse ou de Belgique' : 'de France ou de Suisse';   // patch462\n"
       "  if(sub && !sub.dataset.tpAvant){ sub.dataset.tpAvant = sub.textContent; sub.textContent = 'Chaque carte tirée est une vraie commune, ' + pays3 + ', à sa vraie position géographique.")
rep(A, "court.textContent = 'Chaque carte est une vraie commune de France ou de Suisse.'; }",
       "court.textContent = 'Chaque carte est une vraie commune ' + pays3 + '.'; }")
rep(A, "  const p = tpPays(), etat = p + (tpNouveauVu() ? 'v' : '');",
       "  const p = tpPays(), etat = p + (tpNouveauVu('CH') ? 'v' : '') + (tpNouveauVu('BE') ? 'b' : '');")
rep(A, "    + `<p class=\"tp-note\">${p === 'CH' ? '5 vraies communes suisses. ' : ''}Mêmes jetons et même prix pour les deux paquets ; les raretés tombent aussi souvent dans les deux.</p>`;",
       "    + `<p class=\"tp-note\">${p === 'CH' ? '5 vraies communes suisses. ' : p === 'BE' ? '5 vraies communes belges. ' : ''}Mêmes jetons et même prix pour ${BELGIQUE ? 'les trois paquets' : 'les deux paquets'} ; les raretés tombent aussi souvent dans ${BELGIQUE ? 'les trois' : 'les deux'}.</p>`;")
rep(A, "  tpEcrire('tf-terra-pays', b.dataset.tpp === 'CH' ? 'CH' : 'FR');", "  tpEcrire('tf-terra-pays', tpPaysValide(b.dataset.tpp));")
rep(A, """  if(!SUISSE) return terraCollection;
  const ch = tcPays() === 'CH';
  return new Map([...terraCollection].filter(([, e]) => estSuisseCode(e.code) === ch));""",
"""  if(!SUISSE) return terraCollection;
  const p = tcPays();   // patch462
  return new Map([...terraCollection].filter(([, e]) => paysDuCode(e.code) === p));""")
rep(A, "  tpEcrire('tf-coll-pays', p === 'CH' ? 'CH' : 'FR');", "  tpEcrire('tf-coll-pays', tpPaysValide(p));")
rep(A, """function tcTotauxSuisse(){
  const t = { legendaire: 27, epique: 218, rare: 652, peucommun: 953, commun: 260 };   // s3-5 : 2 110 communes
  for(const e of terraCollection.values()) if(estSuisseCode(e.code) && e.tierSize) t[e.tier.id] = Number(e.tierSize);
  const r = {};
  for(const k in t) r[k] = { total: t[k] };
  return r;
}
function tcTotalSuisse(){ return Object.values(tcTotauxSuisse()).reduce((s, l) => s + l.total, 0); }""",
"""function tcTotauxPays(p){
  const t = p === 'BE' ? { legendaire: 5, epique: 16, rare: 56, peucommun: 209, commun: 279 }   // s3-32 : 565 communes (patch462)
    : { legendaire: 27, epique: 218, rare: 652, peucommun: 953, commun: 260 };   // s3-5 : 2 110 communes
  for(const e of terraCollection.values()) if(paysDuCode(e.code) === p && e.tierSize) t[e.tier.id] = Number(e.tierSize);
  const r = {};
  for(const k in t) r[k] = { total: t[k] };
  return r;
}
function tcTotalPays(p){ return Object.values(tcTotauxPays(p)).reduce((s, l) => s + l.total, 0); }
function tcTotauxSuisse(){ return tcTotauxPays('CH'); }
function tcTotalSuisse(){ return tcTotalPays('CH'); }""")
rep(A, """  let ch = 0;
  for(const e of terraCollection.values()) if(estSuisseCode(e.code)) ch++;
  if(tcPays() === 'CH')
    return `<span class="coll-compteur"><b>${fmtNombre(ch)}</b> / ${fmtNombre(tcTotalSuisse())} communes suisses <span class="om-compteur">· <b>${fmtNombre(collectionMetro() + collectionOutremer().n)}</b> en France</span></span>`;
  return compteurCollectionHtml(totalFrance).replace(/<\\/span>$/, ` <span class="om-compteur">· <b>${fmtNombre(ch)}</b> / ${fmtNombre(tcTotalSuisse())} en Suisse</span></span>`);""",
"""  const n = { FR: 0, CH: 0, BE: 0 };   // patch462 : la Belgique aussi
  for(const e of terraCollection.values()) n[paysDuCode(e.code)]++;
  const p = tcPays();
  if(p !== 'FR')
    return `<span class="coll-compteur"><b>${fmtNombre(n[p])}</b> / ${fmtNombre(tcTotalPays(p))} communes ${p === 'BE' ? 'belges' : 'suisses'} <span class="om-compteur">· <b>${fmtNombre(collectionMetro() + collectionOutremer().n)}</b> en France</span></span>`;
  const etr = tpPaysOuverts().filter(x => x !== 'FR').map(x => ` <span class="om-compteur">· <b>${fmtNombre(n[x])}</b> / ${fmtNombre(tcTotalPays(x))} en ${TP_NOMS[x]}</span>`).join('');
  return compteurCollectionHtml(totalFrance).replace(/<\\/span>$/, etr + '</span>');""")

rep(A, "document.body.classList.toggle('suisse-on', !!SUISSE);",
       "document.body.classList.toggle('suisse-on', !!SUISSE);\ndocument.body.classList.toggle('belgique-on', !!BELGIQUE);   // patch462 : la règle de la Belgique")

# ---------- style.css ----------
S = 'style.css'
rep(S, "@media (max-width: 360px){ .tp-pays button{ padding:8px 12px; font-size:.84rem; } }",
"""@media (max-width: 360px){ .tp-pays button{ padding:8px 12px; font-size:.84rem; } }
/* patch462 : la Belgique */
.tp-pays button.tp-b-be.on{ background:rgba(253,218,36,.16); color:#fff; box-shadow:inset 0 0 0 1px rgba(253,218,36,.6); }
.paquet.paquet-be .paquet-etiquette .tp-drap{ width:30px; height:20px; }
.be-badge{ background:#1A1A1A; color:#FDDA24; }
.be-badge svg{ width:15px; height:10px; border-radius:2px; box-shadow:0 0 0 1px rgba(255,255,255,.25); }
.card.belgique .carte-lisere span:nth-child(1), .mini.belgique .mini-lisere span:nth-child(1){ background:#1A1A1A; }
.card.belgique .carte-lisere span:nth-child(2), .mini.belgique .mini-lisere span:nth-child(2){ background:#FDDA24; }
.card.belgique .carte-lisere span:nth-child(3), .mini.belgique .mini-lisere span:nth-child(3){ background:#EF3340; }
body.belgique-on .tp-pays{ gap:2px; }
body.belgique-on .tp-pays button{ padding:9px 12px; gap:6px; }
@media (max-width: 400px){ body.belgique-on .tp-pays button{ padding:8px 9px; font-size:.82rem; } body.belgique-on .tp-pays small{ display:none; } }""")
rep(S, "body.siege-on #panel-regles [data-s3=\"siege\"], body.suisse-on #panel-regles [data-s3=\"suisse\"],",
       "body.siege-on #panel-regles [data-s3=\"siege\"], body.suisse-on #panel-regles [data-s3=\"suisse\"], body.belgique-on #panel-regles [data-s3=\"belgique\"],")

# ---------- index.html : la règle ----------
I = 'index.html'
rep(I, '          <a href="#s3-suisse" data-s3="suisse">Suisse</a>\n',
       '          <a href="#s3-suisse" data-s3="suisse">Suisse</a>\n          <a href="#s3-belgique" data-s3="belgique">Belgique</a>\n')
rep(I, '(métropole<span data-s3="suisse"> et cantons suisses</span>)',
       '(métropole<span data-s3="suisse"> et cantons suisses</span><span data-s3="belgique">, provinces belges</span>)')
rep(I, "        </details><!-- patch418 -->\n        <details class=\"regle\" id=\"s2-quetes\">\n",
"""        </details><!-- patch418 -->
        <details class="regle" id="s3-belgique" data-s3="belgique">
          <summary>
            <span class="regle-icone"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="5" width="16" height="14" rx="3"/><path d="M9.3 5v14M14.7 5v14"/></svg></span>
            <h2>Belgique<small>11 provinces, 565 communes</small></h2>
            <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 9l6 6 6-6"/></svg>
          </summary>
          <div class="regle-corps">
            <p>Les <b>565 communes</b> de Belgique rejoignent la carte. Ses <b>11 provinces</b> (en comptant la Région de Bruxelles-Capitale : VAN pour Anvers, WLG pour Liège, BRU pour Bruxelles…) jouent le rôle des départements, et forment ensemble la région <b>Belgique</b>. La rareté suit la population, dans les mêmes proportions qu'en France ; leur numéro, par exemple <b>n° 1 / 5</b> pour Anvers, est leur rang parmi les communes belges. Les grandes villes gardent leur nom français (Anvers, Gand, Bruges, Louvain…), les autres leur nom officiel.</p>
            <p><b>Front</b> : elles sortent des paquets du Front et s'assiègent comme les autres ; la frontière ne compte pas pour la proximité. Chaque province rapporte les mêmes paliers qu'un département ; Bruxelles-Capitale (19 communes) rapporte au prorata, comme les petits cantons suisses. Région Belgique : seul en tête avec 10 % ou plus dans plus de la moitié des provinces (<b>6 sur 11</b>).</p>
            <p><b>Terra</b> : au Tirage, choisis <b>France</b>, <b>Suisse</b> ou <b>Belgique</b> : mêmes jetons et même prix, même tirage de la rareté. Ta collection a son choix de pays ; Ma France reste française.</p>
            <p>Pas encore de Belgique dans les mini-jeux (Commune du jour, Radar, Rafale, Plus ou moins), dans les contrats, dans le paquet Département de la boutique, ni dans la quête « Complète un département ».</p>
            <p class="regle-source">Communes, contours et population : Statbel (Office belge de statistique), 1<sup>er</sup> janvier 2025.</p>
          </div>
        </details><!-- patch462 -->
        <details class="regle" id="s2-quetes">
""")

# ---------- direct/direct.js : la carte en direct ----------
D = 'direct/direct.js'
rep(D, "const SUISSE = SUISSE_OUVERTE || /[?&]suisse=test\\b/.test(location.search);",
"""// patch462 : la Belgique, même interrupteur que le jeu (BELGIQUE_OUVERTE, ?belgique=test)
const BELGIQUE_OUVERTE = false;
const BELGIQUE = BELGIQUE_OUVERTE || /[?&]belgique=test\\b/.test(location.search);
const SUISSE = SUISSE_OUVERTE || BELGIQUE || /[?&]suisse=test\\b/.test(location.search);""")
rep(D, "if(SUISSE) Object.assign(DEPT_NAMES, CANTONS);\nconst VUE = { lon0: -5.25, lon1: SUISSE ? 10.8 : 9.65, lat0: 41.3, lat1: 51.15 }",
       "if(SUISSE) Object.assign(DEPT_NAMES, CANTONS);\n"
       "if(BELGIQUE) Object.assign(DEPT_NAMES, " + PROV + ");\n"
       "const VUE = { lon0: -5.25, lon1: SUISSE ? 10.8 : 9.65, lat0: 41.3, lat1: BELGIQUE ? 51.56 : 51.15 }")
rep(D, "    if(frontiere) D.frontiere = chemin(frontiere);\n  }\n",
"""    if(frontiere) D.frontiere = chemin(frontiere);
    if(BELGIQUE){   // patch462 : les provinces et la frontière belge
      const [provinces, fb] = await Promise.all([lire('contours-provinces-be.json'), lire('belgique-frontiere.json')]);
      for(const [c, rings] of Object.entries(provinces || {})){ D.depBords.push(chemin(rings)); liste.push(c); }
      if(fb) D.frontiere = chemin((frontiere || []).concat(fb));
    }
  }
""")
rep(D, "if(p) p.textContent = 'Les 37 000 communes de France et de Suisse, à prendre. Gratuit.';",
       "if(p) p.textContent = BELGIQUE ? 'Les 37 000 communes de France, de Suisse et de Belgique, à prendre. Gratuit.' : 'Les 37 000 communes de France et de Suisse, à prendre. Gratuit.';")
print('patch462 : fini')

# ---------- la trame des communes d'un canton ou d'une province où personne ne possède rien ----------
# departementsVisibles ne voyait que les départements où une commune est possédée : à l'ouverture,
# tout est libre en Belgique (comme en Suisse le jour J), et ses communes ne se dessinaient pas.
rep('app.js', """  for(const c of liste) ajouter(c);
  // sans ca, une commune perdue dans un departement ou l'on ne possede plus""",
"""  for(const c of liste) ajouter(c);
  // patch462 : les cantons et provinces à l'écran, même sans commune possédée (leur boîte, d'après les contours de loin)
  if(SUISSE && CONTOURS_DEPTS && typeof CONTOURS_DEPTS === 'object'){
    if(!departementsVisibles.boites || departementsVisibles.boitesDe !== mapBounds){
      const bt = {};
      for(const d in CONTOURS_DEPTS){
        if(!estEtrangerDep(d) || !estZoneCarte(d)) continue;
        let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
        for(const r of CONTOURS_DEPTS[d]) for(const [lon, lat] of r){
          const p = project(lat, lon), x = p.x * MAP_W, y = p.y * MAP_H;
          if(x < x0) x0 = x; if(x > x1) x1 = x; if(y < y0) y0 = y; if(y > y1) y1 = y;
        }
        bt[d] = [x0, y0, x1, y1];
      }
      departementsVisibles.boites = bt; departementsVisibles.boitesDe = mapBounds;
    }
    const k = ech * mapZoom;
    for(const d in departementsVisibles.boites){
      const [x0, y0, x1, y1] = departementsVisibles.boites[d];
      if(x1 * k + mapPanX > -60 && x0 * k + mapPanX < w + 60 && y1 * k + mapPanY > -60 && y0 * k + mapPanY < h + 60) vus.add(d);
    }
  }
  // sans ca, une commune perdue dans un departement ou l'on ne possede plus""")
