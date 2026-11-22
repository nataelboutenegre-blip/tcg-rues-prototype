# patch483 : « Voir sur la carte » sur la fiche Terra (idée d'Arkhannou) et « Autour de… » dans Attaquer
# (idée d'Oshannir). Jeu seul. Aperçus validés par Nataël le 22/11 à 10 h 46.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A, C = 'app.js', 'style.css'
EPINGLE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>'

# ---------- 1. « Voir sur la carte » sur la fiche Terra ----------
rep(A, """${choixDosHtml('terra', code)}</div>
      <div class="fc-corps">
        <h2 id="ftNom" class="fc-nom ${e.nom.length > 22 ? 'long' : ''}">${echapperTexte(e.nom)}</h2>
        <p class="fc-dep">${DEPT_NAMES[e.dept] ? echapperTexte(DEPT_NAMES[e.dept]) + ' (' + echapperTexte(e.dept) + ')' : echapperTexte(e.dept)}</p>""",
"""${choixDosHtml('terra', code)}</div>
      <div class="fc-corps">
        <h2 id="ftNom" class="fc-nom ${e.nom.length > 22 ? 'long' : ''}">${echapperTexte(e.nom)}</h2>
        <p class="fc-dep">${DEPT_NAMES[e.dept] ? echapperTexte(DEPT_NAMES[e.dept]) + ' (' + echapperTexte(e.dept) + ')' : echapperTexte(e.dept)}</p>
        <p class="fc-voir-l"><button type="button" class="fc-voir" data-ft="carte">""" + EPINGLE + """Voir sur la carte</button></p>""")
rep(A, """      if(b.dataset.ft === 'fermer'){ fermer(null); return; }
      if(b.dataset.ft === 'echange'){""", """      if(b.dataset.ft === 'fermer'){ fermer(null); return; }
      if(b.dataset.ft === 'carte'){ fermer(null); terraVoirSurCarte(code); return; }   // patch483
      if(b.dataset.ft === 'echange'){""")
rep(A, """// ---------- patch222 : le centre de notifications ----------""", """// patch483 : « Voir sur la carte » depuis une carte Terra (idée d'Arkhannou). La carte est dans le Front :
// on y passe, puis on centre la commune (l'anneau de visée la montre quelques secondes).
function terraVoirSurCarte(code){
  const aller = (lat, lon) => {
    if(SAISON2 && typeof modeJeu !== 'undefined' && modeJeu !== 'front'){
      const b = document.querySelector('#modeBascule [data-mode="front"]');
      if(b) b.click();
    }
    setTimeout(() => voirCommuneSurCarte({ code, lat, lon }), 260);
  };
  const e = terraCollection.get(code);
  if(e && e.lat != null && e.lon != null) return aller(e.lat, e.lon);
  const c = collectionMap.get(code) || othersMap.get(code);
  if(c && c.lat != null) return aller(c.lat, c.lon);
  const r = CARTE.cat && CARTE.cat.get(String(code));
  if(r && r[4] != null) return aller(r[4], r[5]);
  sb.from('communes').select('latitude, longitude').eq('code', code).maybeSingle()
    .then(({ data }) => aller(data && data.latitude, data && data.longitude));
}

// ---------- patch222 : le centre de notifications ----------""")
rep(C, """.fiche .fc-dep{ margin: 0; text-align: center; font-size: .82rem; color: #A9BCD4; }""", """.fiche .fc-dep{ margin: 0; text-align: center; font-size: .82rem; color: #A9BCD4; }
/* patch483 : « Voir sur la carte » sur la fiche Terra */
.fiche .fc-voir-l{ margin: 10px 0 4px; text-align: center; }
.fiche .fc-voir{ display: inline-flex; align-items: center; gap: 6px; font: inherit; font-size: .92rem; font-weight: 600; color: #F0B429;
  background: rgba(240,180,41,.1); border: 1px solid rgba(240,180,41,.4); border-radius: 999px; padding: 7px 14px; cursor: pointer; }
.fiche .fc-voir svg{ width: 16px; height: 16px; flex: none; }
.fiche .fc-voir:hover{ background: rgba(240,180,41,.18); }""")

# ---------- 2. « Autour de… » dans Attaquer ----------
rep(A, "let combatRayonKm = 20;", """let combatRayonKm = 20;
// patch483 : « Autour de… » (idée d'Oshannir) : les cibles autour d'une commune choisie, pas de mon territoire
let combatAutour = null, combatAutourKm = 20;   // { code, nom, dep, lat, lon }""")
rep(A, """  if(combatProximite && combatFilterTier === 'tous') return COMBAT_TIERS_BAS.slice();""",
       """  if((combatProximite || combatAutour) && combatFilterTier === 'tous') return COMBAT_TIERS_BAS.slice();   // patch483""")
rep(A, """  const searchText = sansAccents(rechercheCombat);
  majAideCombat(searchText);
""", """  const searchText = sansAccents(rechercheCombat);
  majAideCombat(searchText);
  combatAutourUI(searchText);   // patch483
""")
rep(A, """  if(combatProximite){
    cibles = cibles
      .filter(c => c._distKm !== null && c._distKm <= combatRayonKm)
      .sort((a, b) => a._distKm - b._distKm);
  }
""", """  if(combatProximite){
    cibles = cibles
      .filter(c => c._distKm !== null && c._distKm <= combatRayonKm)
      .sort((a, b) => a._distKm - b._distKm);
  }
  if(combatAutour){   // patch483
    const A = combatAutour;
    for(const c of cibles){
      const la = c.communes.latitude, lo = c.communes.longitude;
      c._distAutour = la == null || lo == null ? null : distanceKm(la, lo, A.lat, A.lon);
    }
    cibles = cibles.filter(c => c._distAutour !== null && c._distAutour <= combatAutourKm)
      .sort((a, b) => a._distAutour - b._distAutour);
  }
""")
rep(A, """    } else if(combatProximite){
      msg = `Aucune cible à moins de ${combatRayonKm} km de ton territoire.`;
    }""", """    } else if(combatProximite){
      msg = `Aucune cible à moins de ${combatRayonKm} km de ton territoire.`;
    }
    if(combatAutour && !combatEnCours) msg = `Aucune cible à moins de ${combatAutourKm} km ${deCommune(combatAutour.nom)}.`;   // patch483""")
rep(A, """    const distance = c._distKm !== null
      ? `<p class="cible-distance">À ${c._distKm < 10 ? c._distKm.toFixed(1).replace('.', ',') : Math.round(c._distKm)} km ${deCommune(c._procheDe)}</p>` : '';""",
"""    const dAff = combatAutour ? c._distAutour : c._distKm, deAff = combatAutour ? combatAutour.nom : c._procheDe;   // patch483
    const distance = dAff != null
      ? `<p class="cible-distance">À ${dAff < 10 ? dAff.toFixed(1).replace('.', ',') : Math.round(dAff)} km ${deCommune(deAff)}</p>` : '';""")
rep(A, """    const km = c._distKm !== null ? (c._distKm < 10 ? c._distKm.toFixed(1).replace('.', ',') : Math.round(c._distKm)) + ' km' : '';
    const titreKm = km ? ` title="À ${km} ${echapperTexte(deCommune(c._procheDe))}"` : '';""",
"""    const km = dAff != null ? (dAff < 10 ? dAff.toFixed(1).replace('.', ',') : Math.round(dAff)) + ' km' : '';   // patch483
    const titreKm = km ? ` title="À ${km} ${echapperTexte(deCommune(deAff))}"` : '';""")
rep(A, """  if(!combatEnCours && (triChances || combatProximite) && cibles.length){""",
       """  if(!combatEnCours && !combatAutour && (triChances || combatProximite) && cibles.length){   // patch483 : autour d'une commune, on garde l'ordre des distances""")
rep(A, """  const signature = [combatFilterTier, searchText, combatProximite,
                     combatRayonKm, combatEnCours, cibles.length, triChances ? 'tri' : ''].join('|');   // patch293""",
"""  const signature = [combatFilterTier, searchText, combatProximite,
                     combatRayonKm, combatEnCours, cibles.length, triChances ? 'tri' : '',
                     combatAutour ? combatAutour.code + '@' + combatAutourKm : ''].join('|');   // patch293, patch483""")
rep(A, """function renderCombatGrid(){
  if(rendreALOuverture('combat', renderCombatGrid)) return;""", """// patch483 : « Autour de… » — les propositions sous la recherche, ou le bandeau quand c'est choisi
let combatCatEnCours = false;
function combatAutourSuggestions(t){
  if(!t || t.length < 3 || /[,;]/.test(t) || /^(\\d{2,3}|2a|2b)$/i.test(t)) return [];
  if(!CARTE.cat){   // la carte n'a pas encore chargé son catalogue : on le demande, puis on revient
    if(!combatCatEnCours){ combatCatEnCours = true; carteCatalogue(CARTE.catVersion || null).then(() => { combatCatEnCours = false; if(CARTE.cat) renderCombatGrid(); }); }
    return [];
  }
  const out = [];
  for(const r of CARTE.cat.values()){
    if(r[4] == null || r[5] == null) continue;
    if(sansAccents(String(r[1])).includes(t)) out.push(r);
  }
  const n = (r) => sansAccents(String(r[1]));
  out.sort((a, b) => (n(b) === t) - (n(a) === t) || n(b).startsWith(t) - n(a).startsWith(t) || (Number(b[3]) || 0) - (Number(a[3]) || 0));
  return out.slice(0, 3);
}
function combatAutourUI(searchText){
  const s = document.getElementById('combatSearch');
  if(!s) return;
  let box = document.getElementById('combatAutourBox');
  if(!box){ box = document.createElement('div'); box.id = 'combatAutourBox'; s.insertAdjacentElement('afterend', box); }
  if(combatAutour){
    const A = combatAutour;
    s.style.display = 'none';
    box.innerHTML = `<div class="aut-ban"><b>📍 Autour ${echapperTexte(deCommune(A.nom))} (${echapperTexte(A.dep)})<small>Les communes que tu peux attaquer, de la plus proche à la plus loin</small></b>`
      + [10, 20, 50].map(k => `<button type="button" class="filter-pill${k === combatAutourKm ? ' active' : ''}" data-autour-km="${k}">${k} km</button>`).join('')
      + `<button type="button" class="aut-x" data-autour-x>✕ Fermer</button></div>`;
    return;
  }
  s.style.display = '';
  const sugg = combatAutourSuggestions(searchText);
  box.innerHTML = sugg.length ? `<div class="aut-sugg"><span>Ou chercher autour d’une commune :</span>${sugg.map(r =>
    `<button type="button" class="aut-chip" data-autour="${echapperTexte(String(r[0]))}">📍 Autour ${echapperTexte(deCommune(String(r[1])))} (${echapperTexte(String(r[2]))})</button>`).join('')}</div>` : '';
}
document.addEventListener('click', (e) => {
  const ch = e.target.closest('[data-autour]');
  if(ch){
    const r = CARTE.cat && CARTE.cat.get(ch.dataset.autour);
    if(!r) return;
    combatAutour = { code: String(r[0]), nom: String(r[1]), dep: String(r[2]), lat: r[4], lon: r[5] };
    const s = document.getElementById('combatSearch'); if(s) s.value = '';
    if(combatProximite){   // un seul centre à la fois
      combatProximite = false;
      const btn = document.getElementById('combatProxToggle');
      if(btn){ btn.classList.remove('active'); btn.setAttribute('aria-pressed', 'false'); }
      const ry = document.getElementById('combatRayons'); if(ry) ry.hidden = true;
    }
    renderCombatGrid(); assurerCiblesBas();
    const g = document.getElementById('combatAutourBox'); if(g && g.scrollIntoView) g.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }
  const km = e.target.closest('[data-autour-km]');
  if(km){ combatAutourKm = Number(km.dataset.autourKm) || 20; renderCombatGrid(); return; }
  if(e.target.closest('[data-autour-x]')){ combatAutour = null; renderCombatGrid(); }
});
function renderCombatGrid(){
  if(rendreALOuverture('combat', renderCombatGrid)) return;""")
rep(C, """/* patch483 : « Voir sur la carte » sur la fiche Terra */""", """/* patch483 : « Autour de… » dans Attaquer */
.aut-sugg{ display: flex; flex-wrap: wrap; gap: 6px; margin: -4px 0 12px; }
.aut-sugg > span{ width: 100%; font-size: .82rem; color: #A9BCD4; }
.aut-chip{ display: inline-flex; align-items: center; gap: 6px; font: inherit; font-size: .88rem; font-weight: 600; color: #F0B429; cursor: pointer;
  background: rgba(240,180,41,.1); border: 1px solid rgba(240,180,41,.4); border-radius: 999px; padding: 6px 12px; text-align: left; }
.aut-ban{ display: flex; align-items: center; flex-wrap: wrap; gap: 8px; background: rgba(240,180,41,.1); border: 1px solid rgba(240,180,41,.45);
  border-radius: 14px; padding: 10px 12px; margin: 0 0 12px; }
.aut-ban > b{ flex: 1 1 100%; font-size: .95rem; }
.aut-ban > b small{ display: block; font-weight: 500; color: #A9BCD4; font-size: .78rem; }
.aut-x{ margin-left: auto; font: inherit; font-size: .88rem; color: #F1F5F9; background: transparent; border: 1px solid rgba(169,188,212,.35); border-radius: 10px; padding: 5px 10px; cursor: pointer; }
/* patch483 : « Voir sur la carte » sur la fiche Terra */""")
print('patch483 : fini')
