# patch523 : Défendre (saison 3) — « Mes départements » et « Laisser filer » automatique (idée de H34VEN, 23/11).
# Reprend les départements choisis en saison 2 (mes_departements_defense / basculer_departement_defense) :
# un siège hors de ces départements est laissé filer tout seul (pas dans la pastille, en bas, en petit) ;
# « Suivre » le remet en grand. Les sièges laissés filer, à la main ou non, sont des boîtes réduites, regroupées en bas.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

# 1. les départements sont chargés aussi en saison 3
rep('app.js', "async function loadMenacesSiege(){\n  const { data, error } = await sb.rpc('sieges_contre_moi_v2');",
              "async function loadMenacesSiege(){\n  await chargerDefPrio();   // patch523\n  const { data, error } = await sb.rpc('sieges_contre_moi_v2');")

# 2. qui est laissé filer
rep('app.js', "function renderMenacesSiege(){\n  const laisses = sgLaisses();\n  const vus = sgMenaces.filter(m => !laisses.has(m.id));",
"""// patch523 : hors de « Mes départements », un siège est laissé filer tout seul, sauf si on le suit à nouveau
function sgSuivis(){ try{ return new Set(JSON.parse(localStorage.getItem('tf-siege-suivis') || '[]')); }catch(e){ return new Set(); } }
function sgAuto(m){ return Array.isArray(defPrio) && defPrio.length > 0 && !defPrio.includes(String(m.dept)); }
function sgEstLaisse(m, laisses, suivis){ return laisses.has(m.id) || (sgAuto(m) && !suivis.has(m.id)); }
function sgPrioHtml(){
  if(defPrio === null) return '';
  const chips = (defPrio || []).map(d => `<button type="button" class="df-dep" data-def-dep="${echapperTexte(d)}" title="Retirer">${echapperTexte(d)} <span>${echapperTexte(DEPT_NAMES[d] || '')}</span> ×</button>`).join('');
  const sugg = defAjoutOuvert ? `<div class="df-sugg">${suggestionsDefPrio().map(([d, n]) =>
      `<button type="button" class="df-dep ajout" data-def-dep="${echapperTexte(d)}">+ ${echapperTexte(d)} <span>${echapperTexte(DEPT_NAMES[d] || '')} · ${n}</span></button>`).join('') || '<span class="df-aide">Tous tes départements sont déjà choisis.</span>'}
      <input type="text" id="defDepChamp" maxlength="30" placeholder="Autre : 33 ou Gironde" autocomplete="off"></div>` : '';
  return `<div class="df-prio"><div class="df-prio-ligne"><span class="df-prio-t">📍 Mes départements</span>${chips}
      ${(defPrio || []).length < DEF_PRIO_MAX ? `<button type="button" class="df-dep plus" data-def-ajout>${defAjoutOuvert ? 'Fermer' : '+ Ajouter'}</button>` : ''}</div>
      <p class="df-aide">${(defPrio || []).length ? 'Les sièges hors de ces départements sont laissés filer tout seuls : ils restent en bas, en petit, et ne comptent pas dans la pastille.' : 'Choisis tes départements : les sièges ailleurs seront laissés filer tout seuls.'}</p>${sugg}</div>`;
}
function sgMiniHtml(m){
  const tier = sgTier(m.tier), res = Number(m.resistance) || 0, deg = Number(m.degats) || 0, p = res ? Math.round(100 * deg / res) : 0;
  return `<div class="sg-mini${p >= 66 ? ' chaud' : ''}"><i class="sg-rar" style="--c:${tier.color}"></i>
    <button type="button" class="sg-def-nom" data-voir-carte="${echapperTexte(m.commune)}">${echapperTexte(m.nom)}</button>${badgeDept(m.dept)}
    <span class="sg-mini-p">${p} %</span><span class="sg-mini-q">${echapperTexte(m.attaquant_pseudo || '')}</span>
    <button type="button" class="sg-laisser" data-sg-laisser="${m.id}"${sgAuto(m) ? ' data-sg-auto="1"' : ''}>Suivre</button></div>`;
}
function renderMenacesSiege(){
  const laisses = sgLaisses(), suivis = sgSuivis();
  const vus = sgMenaces.filter(m => !sgEstLaisse(m, laisses, suivis));   // patch523""")
rep('app.js', "  if(bloc.hidden){ liste.innerHTML = ''; return; }\n  liste.innerHTML = sgMenaces.map(m => {\n    const tier = sgTier(m.tier), res = Number(m.resistance) || 0, deg = Number(m.degats) || 0;\n    const tombe = m.tombe_le ? new Date(m.tombe_le).getTime() - Date.now() : 0;\n    const laisse = laisses.has(m.id);",
              "  if(bloc.hidden){ liste.innerHTML = ''; return; }\n  const filer = sgMenaces.filter(m => sgEstLaisse(m, laisses, suivis));   // patch523\n  liste.innerHTML = sgPrioHtml() + vus.map(m => {\n    const tier = sgTier(m.tier), res = Number(m.resistance) || 0, deg = Number(m.degats) || 0;\n    const tombe = m.tombe_le ? new Date(m.tombe_le).getTime() - Date.now() : 0;\n    const laisse = false;")
rep('app.js', "        <button type=\"button\" class=\"sg-laisser\" data-sg-laisser=\"${m.id}\">${laisse ? 'Suivre à nouveau' : 'Laisser filer'}</button>\n      </div></div>`;\n  }).join('');\n}",
              "        <button type=\"button\" class=\"sg-laisser\" data-sg-laisser=\"${m.id}\"${sgAuto(m) ? ' data-sg-auto=\"1\"' : ''}>Laisser filer</button>\n      </div></div>`;\n  }).join('')\n    + (vus.length ? '' : '<p class=\"collection-empty\">Rien à défendre dans tes départements.</p>')\n    + (filer.length ? `<details class=\"sg-filer\"${vus.length ? '' : ' open'}><summary>Laissées filer <span>${filer.length}</span></summary>${filer.map(sgMiniHtml).join('')}</details>` : '');   // patch523\n}")
# 3. le bouton : à la main (tf-siege-laisses) ou, pour un siège hors de mes départements, « suivi » (tf-siege-suivis)
rep('app.js', "  if(t.dataset.sgLaisser){\n    const s = sgLaisses(), id = Number(t.dataset.sgLaisser);\n    if(s.has(id)) s.delete(id); else s.add(id);\n    try{ localStorage.setItem('tf-siege-laisses', JSON.stringify([...s].slice(-60))); }catch(e){}",
              "  if(t.dataset.sgLaisser){\n    const s = sgLaisses(), id = Number(t.dataset.sgLaisser);\n    if(t.dataset.sgAuto){   // patch523 : hors de mes départements\n      const su = sgSuivis(); s.delete(id);\n      if(su.has(id)) su.delete(id); else su.add(id);\n      try{ localStorage.setItem('tf-siege-suivis', JSON.stringify([...su].slice(-60))); }catch(e){}\n    } else if(s.has(id)) s.delete(id); else s.add(id);\n    try{ localStorage.setItem('tf-siege-laisses', JSON.stringify([...s].slice(-60))); }catch(e){}")
rep('style.css', ".sg-def.laisse{ opacity:.6; }",
""".sg-def.laisse{ opacity:.6; }
.sg-filer{ margin-top:12px; border:1px solid rgba(255,255,255,.08); border-radius:12px; }   /* patch523 */
.sg-filer > summary{ padding:10px 12px; cursor:pointer; font-weight:700; font-size:.86rem; color:var(--brume); list-style:none; display:flex; gap:8px; align-items:center; }
.sg-filer > summary::-webkit-details-marker{ display:none; }
.sg-filer > summary span{ font-size:.75rem; background:rgba(255,255,255,.08); border-radius:999px; padding:1px 8px; }
.sg-filer > summary::after{ content:'›'; margin-left:auto; transition:transform .2s; }
.sg-filer[open] > summary::after{ transform:rotate(90deg); }
.sg-mini{ display:flex; align-items:center; gap:8px; padding:7px 12px; border-top:1px solid rgba(255,255,255,.06); font-size:.82rem; opacity:.8; }
.sg-mini .sg-def-nom{ font-size:.86rem; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.sg-mini-p{ font-weight:700; margin-left:auto; } .sg-mini.chaud .sg-mini-p{ color:#FF8A8F; }
.sg-mini-q{ color:var(--brume); max-width:90px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.sg-mini .sg-laisser{ margin-left:0; padding:4px 2px; }""")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-23': d.insert(0, {'date': '2026-11-23', 'nouveautes': []})
e = d[0]; e.setdefault('nouveautes', [])
l = "📍 Défendre : « Mes départements » revient. Les sièges ailleurs sont laissés filer tout seuls, et tous les sièges laissés filer deviennent de petites lignes en bas (« Suivre » pour les remettre en grand). Idée de H34VEN."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
