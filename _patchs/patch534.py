# patch534 (Arkhannou) : échanges du clan, filtres Pays et Département / canton au-dessus de chaque liste.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js', "const clanEch = { etat: null, qui: null, donne: null, recoit: null, mes: null, leurs: null, r1: '', r2: '' };",
    "const clanEch = { etat: null, qui: null, donne: null, recoit: null, mes: null, leurs: null, r1: '', r2: '', p1: '', d1: '', p2: '', d2: '' };   // patch534 : p/d = pays, département")
rep('app.js', "function ceListeHtml(liste, cle, choisi, filtre){\n  if(!liste) return '<p class=\"ce-attente\">Chargement…</p>';\n  const f = sansAccents((filtre || '').toLowerCase());\n  const l = liste.filter(c => !f || correspondUnTerme(c.nom, c.departement, f));   // patch509 : « 25, 90, 70 »",
"""// patch534 : pays d'un « département » (canton suisse, province belge, canton luxembourgeois, sinon France)
const CE_PAYS = { FR: '🇫🇷 France', CH: '🇨🇭 Suisse', BE: '🇧🇪 Belgique', LU: '🇱🇺 Luxembourg' };
function cePays(dep){ return estCanton(dep) ? 'CH' : estProvinceBe(dep) ? 'BE' : estCantonLu(dep) ? 'LU' : 'FR'; }
function ceFiltresHtml(liste, cote){
  if(!liste || !liste.length) return '';
  const pays = clanEch['p' + cote], dep = clanEch['d' + cote];
  const lp = [...new Set(liste.map(c => cePays(c.departement)))];
  const ld = [...new Set(liste.filter(c => !pays || cePays(c.departement) === pays).map(c => String(c.departement)))]
    .sort((a, b) => a.localeCompare(b, 'fr', { numeric: true }));
  if(lp.length < 2 && ld.length < 2) return '';
  return `<div class="ce-filtres"><select data-ce-pays="${cote}" aria-label="Pays"><option value="">Tous les pays</option>${['FR', 'CH', 'BE', 'LU'].filter(p => lp.includes(p)).map(p => `<option value="${p}"${p === pays ? ' selected' : ''}>${CE_PAYS[p]}</option>`).join('')}</select>`
    + `<select data-ce-dep="${cote}" aria-label="Département ou canton"><option value="">${pays && pays !== 'FR' ? (pays === 'BE' ? 'Toutes les provinces' : 'Tous les cantons') : 'Tous les départements'}</option>${ld.map(d => `<option value="${echapperTexte(d)}"${d === dep ? ' selected' : ''}>${echapperTexte(d)} · ${echapperTexte(DEPT_NAMES[d] || '')}</option>`).join('')}</select></div>`;
}
function ceListeHtml(liste, cle, choisi, filtre, cote){
  if(!liste) return '<p class="ce-attente">Chargement…</p>';
  const f = sansAccents((filtre || '').toLowerCase());
  const pays = cote ? clanEch['p' + cote] : '', dep = cote ? clanEch['d' + cote] : '';   // patch534
  const l = liste.filter(c => (!pays || cePays(c.departement) === pays) && (!dep || String(c.departement) === dep)
                         && (!f || correspondUnTerme(c.nom, c.departement, f)));   // patch509 : « 25, 90, 70 »""")
rep('app.js', "  if(d) d.innerHTML = ceListeHtml(clanEch.mes, 'ce-donne', clanEch.donne, clanEch.r1);\n  const leurs = ceLeursFiltrees();",
"""  if(d) d.innerHTML = ceListeHtml(clanEch.mes, 'ce-donne', clanEch.donne, clanEch.r1, 1);
  const leurs = ceLeursFiltrees();
  const f1 = document.getElementById('ceF1'), f2 = document.getElementById('ceF2');   // patch534
  if(f1) f1.innerHTML = ceFiltresHtml(clanEch.mes, 1);
  if(f2) f2.innerHTML = clanEch.qui ? ceFiltresHtml(leurs, 2) : '';""")
rep('app.js', "  if(r) r.innerHTML = clanEch.qui ? ceListeHtml(leurs, 'ce-recoit', clanEch.recoit, clanEch.r2) : '<p class=\"ce-attente\">Choisis d\\'abord un coéquipier.</p>';",
              "  if(r) r.innerHTML = clanEch.qui ? ceListeHtml(leurs, 'ce-recoit', clanEch.recoit, clanEch.r2, 2) : '<p class=\"ce-attente\">Choisis d\\'abord un coéquipier.</p>';")
rep('app.js', """<div><div class="ce-attente">2. Tu donnes</div><input type="search" class="ce-recherche" id="ceR1\"""",
              """<div><div class="ce-attente">2. Tu donnes</div><div id="ceF1"></div><input type="search" class="ce-recherche" id="ceR1\"""")
rep('app.js', """<div><div class="ce-attente" id="ceT3">3. Tu reçois · même rareté</div><input type="search" class="ce-recherche" id="ceR2\"""",
              """<div><div class="ce-attente" id="ceT3">3. Tu reçois · même rareté</div><div id="ceF2"></div><input type="search" class="ce-recherche" id="ceR2\"""")
rep('app.js', "  if(e.target.id === 'ceR2'){ clanEch.r2 = e.target.value; majListesCe(); }\n});",
"""  if(e.target.id === 'ceR2'){ clanEch.r2 = e.target.value; majListesCe(); }
});
document.getElementById('panel-clan').addEventListener('change', (e) => {   // patch534 : les filtres des échanges
  const p = e.target.closest('[data-ce-pays]'), d = e.target.closest('[data-ce-dep]');
  if(p){ clanEch['p' + p.dataset.cePays] = p.value; clanEch['d' + p.dataset.cePays] = ''; majListesCe(); }
  if(d){ clanEch['d' + d.dataset.ceDep] = d.value; majListesCe(); }
});""")
rep('style.css', ".ce-recherche{ width:100%;",
""".ce-filtres{ display:flex; gap:6px; margin:0 0 6px; }   /* patch534 */
.ce-filtres select{ flex:1; min-width:0; padding:7px 8px; border-radius:9px; border:1px solid rgba(169,188,212,0.3); background: var(--nuit); color:#fff; font:inherit; font-size:.82rem; }
.ce-recherche{ width:100%;""")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = d[0]; assert e['date'] == '2026-11-25'
l = "🔎 Échanges du clan : deux menus, Pays et Département / canton, au-dessus de chaque liste. Fini les « Juvigny » quand tu cherches le Jura suisse (merci Arkhannou)."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
