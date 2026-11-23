# patch524 : « Mes départements » accepte les pays (demande de Maroli, 23/11) : Luxembourg, Suisse, Belgique.
# - taper « Luxembourg », « Suisse » ou « Belgique » ajoute tous ses cantons / provinces (avant, « Luxembourg »
#   ajoutait la province belge du même nom) ; un code étranger (LLU, VD, WLX…) ou un nom de canton marche aussi ;
# - les suggestions proposent les pays où le joueur a des communes ;
# - un pays complet s'affiche en une seule pastille « 🇱🇺 Luxembourg × » (la retirer retire tous ses cantons).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js', "function sgPrioHtml(){\n  if(defPrio === null) return '';\n  const chips = (defPrio || []).map(d =>",
"""// patch524 : les pays dans « Mes départements »
function defPays(){
  const P = [];
  if(typeof LUXEMBOURG !== 'undefined' && LUXEMBOURG) P.push({ id: 'luxembourg', nom: 'Luxembourg', drapeau: '🇱🇺', codes: Object.keys(CANTONS_LU) });
  if(typeof SUISSE !== 'undefined' && SUISSE) P.push({ id: 'suisse', nom: 'Suisse', drapeau: '🇨🇭', codes: Object.keys(CANTONS) });
  if(typeof BELGIQUE !== 'undefined' && BELGIQUE) P.push({ id: 'belgique', nom: 'Belgique', drapeau: '🇧🇪', codes: Object.keys(PROVINCES_BE) });
  return P;
}
async function defPaysBasculer(id, retirer){
  const p = defPays().find(x => x.id === id); if(!p) return;
  const prio = defPrio || [];
  const codes = retirer ? p.codes.filter(c => prio.includes(c)) : p.codes.filter(c => !prio.includes(c));
  if(!retirer && prio.length + codes.length > DEF_PRIO_MAX){
    notifier({ type: 'erreur', titre: 'Départements', texte: `${p.nom} compte ${p.codes.length} ${p.id === 'belgique' ? 'provinces' : 'cantons'} : il te reste ${DEF_PRIO_MAX - prio.length} places sur ${DEF_PRIO_MAX}.` }); return;
  }
  for(const c of codes){
    const { data, error } = await sb.rpc('basculer_departement_defense', { p_dep: c });
    if(error){ notifier({ type: 'erreur', titre: 'Départements', texte: messageLisible(error.message) }); break; }
    defPrio = (data || []).map(x => x.departement);
  }
  if(!(defPrio || []).length) defFiltre = 'tout';
  renderMenaces();
}
function sgPrioHtml(){
  if(defPrio === null) return '';
  const pleins = defPays().filter(p => p.codes.every(c => (defPrio || []).includes(c)));   // patch524 : un pays complet = une pastille
  const caches = new Set(pleins.flatMap(p => p.codes));
  const paysSugg = defAjoutOuvert ? defPays().filter(p => !pleins.includes(p)).map(p => [p, [...collectionMap.values()].filter(e => !e.perdue && p.codes.includes(e.dept)).length]).filter(([, n]) => n > 0) : [];
  const chips = pleins.map(p => `<button type="button" class="df-dep" data-def-pays="${p.id}" data-def-pays-retirer="1" title="Retirer tout le pays">${p.drapeau} ${p.nom} <span>tout le pays</span> ×</button>`).join('')
    + (defPrio || []).filter(d => !caches.has(d)).map(d =>""")
rep('app.js', "      `<button type=\"button\" class=\"df-dep ajout\" data-def-dep=\"${echapperTexte(d)}\">+ ${echapperTexte(d)} <span>${echapperTexte(DEPT_NAMES[d] || '')} · ${n}</span></button>`).join('') || '<span class=\"df-aide\">Tous tes départements sont déjà choisis.</span>'}\n      <input type=\"text\" id=\"defDepChamp\" maxlength=\"30\" placeholder=\"Autre : 33 ou Gironde\" autocomplete=\"off\"></div>` : '';\n  return `<div class=\"df-prio\">",
              "      `<button type=\"button\" class=\"df-dep ajout\" data-def-dep=\"${echapperTexte(d)}\">+ ${echapperTexte(d)} <span>${echapperTexte(DEPT_NAMES[d] || '')} · ${n}</span></button>`).join('') || '<span class=\"df-aide\">Tous tes départements sont déjà choisis.</span>'}\n      ${paysSugg.map(([p, n]) => `<button type=\"button\" class=\"df-dep ajout\" data-def-pays=\"${p.id}\">+ ${p.drapeau} ${p.nom} <span>tout le pays · ${n}</span></button>`).join('')}\n      <input type=\"text\" id=\"defDepChamp\" maxlength=\"30\" placeholder=\"Autre : 33, Gironde, Luxembourg, Suisse…\" autocomplete=\"off\"></div>` : '';   // patch524\n  return `<div class=\"df-prio\">")
# le clic sur un pays, et la saisie d'un nom de pays
rep('app.js', "  const d = e.target.closest('[data-def-dep]');\n  if(d){ basculerDefPrio(d.dataset.defDep); return; }",
              "  const pa = e.target.closest('[data-def-pays]');   // patch524\n  if(pa){ defPaysBasculer(pa.dataset.defPays, !!pa.dataset.defPaysRetirer); return; }\n  const d = e.target.closest('[data-def-dep]');\n  if(d){ basculerDefPrio(d.dataset.defDep); return; }")
rep('app.js', "  if(e.key !== 'Enter' || e.target.id !== 'defDepChamp') return;\n  const code = trouverDepartementSaisi(e.target.value);",
              "  if(e.key !== 'Enter' || e.target.id !== 'defDepChamp') return;\n  const tp = sansAccents(String(e.target.value || '').trim()).toLowerCase();   // patch524 : un pays entier\n  const pays = defPays().find(p => p.id === tp || sansAccents(p.nom).toLowerCase() === tp);\n  if(pays){ defPaysBasculer(pays.id, false); return; }\n  const code = trouverDepartementSaisi(e.target.value);")
rep('app.js', "  if(!code){ notifier({ type: 'erreur', titre: 'Département inconnu', texte: 'Tape son numéro (16) ou son nom (Charente).' }); return; }",
              "  if(!code){ notifier({ type: 'erreur', titre: 'Département inconnu', texte: 'Tape son numéro (16), son nom (Charente), un canton (Vaud), ou un pays (Luxembourg, Suisse, Belgique).' }); return; }")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = d[0]; e.setdefault('nouveautes', [])
l = "📍 Mes départements : tu peux ajouter un pays entier (Luxembourg, Suisse, Belgique) d'un coup, ou un canton / une province par son nom. Demande de Maroli."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
