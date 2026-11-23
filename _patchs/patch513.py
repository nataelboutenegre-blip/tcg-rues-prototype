# patch513 : QG › Bâtiments — « Bâtiments pris et perdus cette saison » (idée d'Arkhannou, 23/11).
# Lit batiments_pris_perdus() (s3-59), qui reprend les lignes « pertes » du journal (s2-142) depuis le début de la saison.
# Repliée par défaut, chargée à l'ouverture.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js', "    if(pBat) pBat.appendChild(bt); else g.insertAdjacentElement('beforebegin', bt);",
"""    if(pBat) pBat.appendChild(bt); else g.insertAdjacentElement('beforebegin', bt);
    if(pBat && typeof bthCreer === 'function') pBat.appendChild(bthCreer());   // patch513""")
rep('app.js', "// patch379 : la galerie depuis le volet Bâtiments",
"""// patch513 : les bâtiments pris et perdus cette saison (idée d'Arkhannou)
function bthCreer(){
  const d = document.createElement('details');
  d.className = 'garnisons-bloc bth'; d.id = 'btHisto';
  d.innerHTML = '<summary><span>Bâtiments pris et perdus cette saison</span><b class="bth-n"></b></summary><div class="bth-c"><p class="bth-vide">Un instant…</p></div>';
  d.addEventListener('toggle', () => { if(d.open) bthCharger(); });
  return d;
}
function bthQuoi(x){
  const nom = { fonderie: 'Fonderie', forteresse: 'Forteresse', banque: 'Banque', centre: 'Centre de recherche', radar: 'Radar', artillerie: 'Artillerie', centrale: 'Centrale de clan' }[x.t] || 'bâtiment';
  const fem = ['fonderie', 'forteresse', 'banque', 'artillerie', 'centrale'].includes(x.t);
  return { nom, fem };
}
function bthLigne(r){
  const pris = r.sens === 'pris', autre = echapperTexte(r.autre || 'un joueur');
  const L = Array.isArray(r.b) ? r.b : [];
  const noms = L.map(x => { const q = bthQuoi(x); const v = /^[AEIOU]/.test(q.nom); return pris ? `${v ? 'l’' : q.fem ? 'la ' : 'le '}<b>${q.nom}</b>` : `${q.fem && !v ? 'ta' : 'ton'} <b>${q.nom}</b>`; });
  const quoi = noms.length > 1 ? noms.slice(0, -1).join(', ') + ' et ' + noms[noms.length - 1] : (noms[0] || 'un bâtiment');
  const pille = L.reduce((s, x) => s + (Number(x.pille) || 0), 0);
  const bombe = L.some(x => x.t === 'centre' && x.bombe);
  const plus = [pille > 0 ? `${pris ? '+' : '−'}${pille} lingot${pille > 1 ? 's' : ''}` : '', bombe ? (pris ? 'sa bombe perdue' : 'ta bombe perdue') : ''].filter(Boolean).join(' · ');
  const quand = new Date(r.le).toLocaleString('fr-FR', { weekday: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  const tier = sgTier(r.tier);
  return `<li class="bth-l ${pris ? 'pris' : 'perdu'}"><span class="bth-s" aria-hidden="true">${pris ? '▲' : '▼'}</span>
    <div><p>${pris ? `Tu as pris ${quoi} de <b>${autre}</b>` : `<b>${autre}</b> t'a pris ${quoi}`}</p>
    <small><i class="sg-rar" style="--c:${tier.color}"></i><button type="button" class="btl-nom" data-voir-carte="${echapperTexte(r.code)}">${echapperTexte(r.nom || r.code)}</button> · ${quand}</small></div>
    ${plus ? `<span class="bth-p">${plus}</span>` : ''}</li>`;
}
async function bthCharger(){
  const d = document.getElementById('btHisto'); if(!d) return;
  const c = d.querySelector('.bth-c'), n = d.querySelector('.bth-n');
  const { data, error } = await sb.rpc('batiments_pris_perdus');
  if(error){ c.innerHTML = `<p class="bth-vide">${fonctionAbsente(error) ? 'Bientôt ici.' : 'Impossible de charger la liste.'}</p>`; return; }
  const D = data || { pris: 0, perdus: 0, liste: [] };
  n.textContent = `${D.pris} pris · ${D.perdus} perdu${D.perdus > 1 ? 's' : ''}`;
  c.innerHTML = (D.liste || []).length ? `<ul class="bth-liste">${D.liste.map(bthLigne).join('')}</ul>`
    : '<p class="bth-vide">Aucun bâtiment pris ni perdu depuis le début de la saison. Prendre une commune qui porte un bâtiment le détruit, et une Fonderie ou une Banque se pille au passage.</p>';
}
// patch379 : la galerie depuis le volet Bâtiments""")
rep('style.css', ".btv-galerie{",
""".bth{ border:1px solid rgba(255,255,255,.1); border-radius:14px; padding:0; background:rgba(255,255,255,.03); }   /* patch513 */
.bth > summary{ display:flex; justify-content:space-between; align-items:center; gap:10px; padding:12px 14px; cursor:pointer; font-weight:700; list-style:none; }
.bth > summary::-webkit-details-marker{ display:none; }
.bth > summary::after{ content:'›'; font-size:1.2rem; color:var(--brume); transition:transform .2s; }
.bth[open] > summary::after{ transform:rotate(90deg); }
.bth-n{ margin-left:auto; font-size:.78rem; font-weight:600; color:var(--brume); }
.bth-c{ padding:0 14px 12px; }
.bth-vide{ font-size:.82rem; color:var(--brume); margin:0; line-height:1.45; }
.bth-liste{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:8px; }
.bth-l{ display:flex; align-items:flex-start; gap:10px; padding:10px; border-radius:10px; background:rgba(255,255,255,.04); }
.bth-l p{ margin:0 0 3px; font-size:.86rem; line-height:1.35; }
.bth-l small{ display:flex; align-items:center; gap:6px; font-size:.75rem; color:var(--brume); }
.bth-l > div{ flex:1; min-width:0; }
.bth-s{ font-size:.8rem; line-height:1.6; }
.bth-l.pris .bth-s{ color:#3DD68C; } .bth-l.perdu .bth-s{ color:#FF6369; }
.bth-p{ font-size:.78rem; font-weight:700; white-space:nowrap; }
.bth-l.pris .bth-p{ color:#3DD68C; } .bth-l.perdu .bth-p{ color:#FF6369; }
.btv-galerie{""")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-23': d.insert(0, {'date': '2026-11-23', 'nouveautes': []})
e = d[0]; e.setdefault('nouveautes', [])
l = "🏚️ QG › Bâtiments : « Bâtiments pris et perdus cette saison », la liste de ceux que tu as détruits ou perdus en conquête, avec les lingots pillés. Idée d'Arkhannou."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
