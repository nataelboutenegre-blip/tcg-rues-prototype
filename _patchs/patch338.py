# patch338 (4/11/2026) : défendre en choisissant son engagement (aperçu validé
# « parfait ! », va avec s2-95).
# - Le bouton « Défendre » (écran Défendre et Mon front) ouvre une fiche :
#   série de l'attaquant, défenses disponibles (et quand la suivante revient),
#   garnison, puis le choix Prudente / Normale / Offensive avec chances et
#   coût (1, 2 ou 3 énergie, comme l'attaque). Les engagements trop chers pour
#   l'énergie du moment sont grisés.
# - Le choix de défense est retenu à part de celui d'attaque ('tf-intensite-def').
# - Règles corrigées : les communes voisines ne comptent pas en défense ; coût
#   selon l'engagement. Une ligne dans la cloche.
import pathlib, json

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

# ===================================================================== app.js
F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
s = rep(s, """const intensite = (id) => INTENSITES.find(i => i.id === (id || intensiteChoisie)) || INTENSITES[1];""",
"""const intensite = (id) => INTENSITES.find(i => i.id === (id || intensiteChoisie)) || INTENSITES[1];
// patch338 : l'engagement de défense, retenu à part de celui d'attaque
let intensiteDefense = 'normale';
try{
  const v = localStorage.getItem('tf-intensite-def');
  if(v && INTENSITES.some(i => i.id === v)) intensiteDefense = v;
} catch(e){}""")
s = rep(s, """data-nom="${echapperTexte(g.nom)}">${ICONE_BOUCLIER}${coutTexte(SAISON2 ? 1 : coutIntensite(g.tier))}</button>""",
"""data-nom="${echapperTexte(g.nom)}">${ICONE_BOUCLIER}${SAISON2 ? 'Défendre' : coutTexte(coutIntensite(g.tier))}</button>""")
s = rep(s, """data-nom="${echapperTexte(m.nom || '')}">Défendre · 1 ${E}</button>""",
"""data-nom="${echapperTexte(m.nom || '')}">Défendre</button>""")
s = rep(s, """  if(!btn || btn.disabled) return;
  defendreDepuis(btn);""", """  if(!btn || btn.disabled) return;
  if(SAISON2) pdOuvrir(btn); else defendreDepuis(btn);   // patch338""")
s = rep(s, """  if(def){ if(!def.disabled) defendreDepuis(def); return; }""",
"""  if(def){ if(!def.disabled){ if(SAISON2) pdOuvrir(def); else defendreDepuis(def); } return; }   // patch338""")
s = rep(s, """    if(sub) sub.textContent = 'Quand un joueur gagne un round contre toi, tente une défense (1 énergie). Tes garnisons, elles, se défendent toutes seules.';""",
"""    if(sub) sub.textContent = 'Quand un joueur gagne un round contre toi, tente une défense : tu choisis ton engagement, 1 à 3 énergie. Tes garnisons, elles, se défendent toutes seules.';   // patch338""")
s = rep(s, """async function defendreDepuis(btn){""", """async function defendreDepuis(btn, choix){   // patch338 : choix = engagement de défense""")
s = rep(s, """    let { data, error } = await sb.rpc('defendre', { p_commune_code: btn.dataset.commune, p_attaquant: btn.dataset.attaquant, p_intensite: intensiteChoisie });""",
"""    let { data, error } = await sb.rpc('defendre', { p_commune_code: btn.dataset.commune, p_attaquant: btn.dataset.attaquant, p_intensite: choix || intensiteChoisie });""")

# le module, juste avant la première conquête guidée (il en réutilise la fiche)
s = rep(s, """// ---------- patch336 : la première conquête guidée ----------""",
r"""// ---------- patch338 : défendre en choisissant son engagement (s2-95) ----------
// Avant, la défense prenait en silence l'engagement choisi pour attaquer et
// coûtait toujours 1 énergie. Maintenant on choisit à chaque défense, au même
// prix que l'attaque (1, 2 ou 3 énergie pour 35, 50 ou 65 %).
var PD = { btn: null, m: null, code: null };
function pdOuvrir(btn){
  const code = btn.dataset.commune, att = btn.dataset.attaquant;
  PD.m = (menaces || []).find(x => x.commune_code === code && String(x.attaquant_id) === String(att)) || null;
  PD.code = code;
  PD.btn = { dataset: { commune: code, attaquant: att, nom: btn.dataset.nom || (PD.m && PD.m.nom) || code }, disabled: false };
  pcOuvrir(pdHtml());
}
function pdHtml(){
  const m = PD.m, nom = PD.btn.dataset.nom;
  const v = m ? Number(m.victoires_consecutives) || 0 : 0;
  const faites = m && m.defenses_faites != null ? Math.min(2, Number(m.defenses_faites) || 0) : (m && m.defense_utilisee ? 2 : null);
  const dispo = faites == null ? null : 2 - faites;
  const revient = m && m.defense_revient ? new Date(m.defense_revient).getTime() - Date.now() : 0;
  const en = energieEtat ? Math.floor(Number(energieEtat.energie) || 0) : null;
  const gn = typeof garnisonsMoi !== 'undefined' ? garnisonsMoi.get(PD.code) : null;
  const dept = m && typeof deptDe === 'function' ? deptDe(m) : '';
  const cout = ENERGIE_INTENSITE[intensiteDefense] || 2;
  const ch = (INTENSITES.find(i => i.id === intensiteDefense) || INTENSITES[1]).chances;
  const tropCher = en != null && cout > en;
  const serie = [0, 1, 2].map(i => `<i class="${i < v ? 'pris' : ''}"></i>`).join('');
  const dispoTxt = dispo == null ? '<b>2</b><span>défenses par attaque</span>'
    : `<b>${dispo} sur 2</b><span>${dispo === 2 ? 'défenses disponibles' : dispo === 1
        ? `défense disponible${revient > 0 ? ` · la 2e revient dans ${formatDuree(revient)}` : ''}`
        : `aucune disponible${revient > 0 ? ` · une revient dans ${formatDuree(revient)}` : ''}`}</span>`;
  const ints = INTENSITES.map(i => {
    const c = ENERGIE_INTENSITE[i.id];
    return `<button type="button" class="pd-int${i.id === intensiteDefense ? ' on' : ''}" data-pd-int="${i.id}" ${en != null && c > en ? 'disabled' : ''}>
      <span>${i.label}</span><b>${i.chances} %</b><small>${c} énergie</small></button>`;
  }).join('');
  return `<div class="pc-poignee"></div>
    <div class="pc-kicker">Défense · ${echapperHtml(nom)}${dept ? ' (' + echapperHtml(dept) + ')' : ''}</div>
    <div class="pc-titre">Repousser ${echapperHtml((m && m.attaquant_pseudo) || 'l’attaquant')}</div>
    <p class="pd-sous">Réussie, il perd une victoire. Ratée, tu ne perds que l'énergie.</p>
    <div class="pd-etat">
      <div><span class="menace-serie">${serie}</span><span>${v} victoire${v > 1 ? 's' : ''} sur 3${v === 2 ? ' : encore une et il la prend' : ''}</span></div>
      <div>${dispoTxt}</div>
    </div>
    ${gn ? '<div class="pd-gn">🛡 Ta garnison défend aussi seule, une chance sur deux à chaque round gagné.</div>' : ''}
    <p class="pd-lab">Ton engagement${en != null ? ` <span>· ton énergie : <b>${en}</b></span>` : ''}</p>
    <div class="pd-ints">${ints}</div>
    <button type="button" class="pc-go" data-pd-go ${dispo === 0 || tropCher ? 'disabled' : ''}>${dispo === 0 ? 'Plus de défense disponible' : tropCher ? 'Pas assez d’énergie' : `Défendre · ${cout} ⚡ · ${ch} %`}</button>
    <p class="pd-note">Pas de bonus pour tes communes voisines en défense. <b>Ton choix est retenu</b> pour tes prochaines défenses.</p>
    <div class="pc-sec"><span></span><button type="button" data-pd-fermer>Annuler</button></div>`;
}
document.addEventListener('click', (e) => {
  const i = e.target.closest('[data-pd-int]');
  if(i && !i.disabled){
    intensiteDefense = i.dataset.pdInt;
    try{ localStorage.setItem('tf-intensite-def', intensiteDefense); }catch(err){}
    const b = document.getElementById('pcBoite'); if(b) b.innerHTML = pdHtml();
    return;
  }
  const g = e.target.closest('[data-pd-go]');
  if(g && !g.disabled){ g.disabled = true; pcFermer(); defendreDepuis(PD.btn, intensiteDefense); return; }
  if(e.target.closest('[data-pd-fermer]')) pcFermer();
});

// ---------- patch336 : la première conquête guidée ----------""")
F.write_text(s, encoding='utf-8')

# ===================================================================== style
F = pathlib.Path('style.css'); s = F.read_text(encoding='utf-8')
s += """
/* patch338 : défendre en choisissant son engagement */
.pd-sous{ font-size:.8rem; color:var(--brume); margin:-6px 0 12px; }
.pd-etat{ display:flex; gap:8px; margin-bottom:12px; }
.pd-etat > div{ flex:1; background:rgba(10,22,40,.45); border-radius:12px; padding:9px 10px; }
.pd-etat b{ display:block; font:900 1.25rem/1 var(--titre); }
.pd-etat span{ display:block; font-size:.7rem; color:var(--brume); margin-top:4px; line-height:1.35; }
.pd-etat .menace-serie{ display:flex; margin:0 0 6px; }
.pd-gn{ font-size:.75rem; background:rgba(43,212,139,.1); border:1px solid rgba(43,212,139,.35); border-radius:10px; padding:8px 10px; margin-bottom:12px; color:#BFF3DC; }
.pd-lab{ font-size:.76rem; color:var(--brume); margin:0 0 7px; }
.pd-lab b{ color:#fff; }
.pd-ints{ display:grid; grid-template-columns:repeat(3,1fr); gap:7px; margin-bottom:12px; }
.pd-int{ font:inherit; color:#fff; cursor:pointer; border-radius:12px; border:1.5px solid rgba(169,188,212,.25); background:rgba(10,22,40,.4); padding:10px 6px; text-align:center; }
.pd-int span{ display:block; font-size:.8rem; font-weight:600; }
.pd-int b{ display:block; font:900 1.5rem/1.1 var(--titre); margin:4px 0 2px; }
.pd-int small{ display:block; font-size:.7rem; color:var(--brume); }
.pd-int.on{ border-color:var(--c-legendaire); background:rgba(240,180,41,.12); }
.pd-int.on span{ color:var(--c-legendaire); }
.pd-int:disabled{ opacity:.4; cursor:default; }
.pc-go:disabled{ background:var(--nuit-3); color:#9FB0C8; box-shadow:none; cursor:default; }
.pd-note{ font-size:.72rem; color:#8FA2BC; line-height:1.45; margin:12px 0 0; }
.pd-note b{ color:#C9D3E0; }
"""
F.write_text(s, encoding='utf-8')

# ===================================================================== règles
F = pathlib.Path('index.html'); s = F.read_text(encoding='utf-8')
s = rep(s, """<p><b>Défendre</b> : quand un joueur gagne un round contre toi, tu peux tenter une défense pour <b>1 énergie</b>, deux fois par attaque. Une défense utilisée revient <b>24 h</b> plus tard (deux au plus). Réussie, l'attaquant perd une victoire.</p><!-- patch334 -->""",
"""<p><b>Défendre</b> : quand un joueur gagne un round contre toi, tu peux tenter une défense, deux fois par attaque. Tu choisis ton engagement à chaque défense : prudente <b>1 énergie</b> (35 %), normale <b>2</b> (50 %), offensive <b>3</b> (65 %). Tes communes voisines ne comptent pas en défense. Une défense utilisée revient <b>24 h</b> plus tard (deux au plus). Réussie, l'attaquant perd une victoire.</p><!-- patch334, patch338 -->""")
s = rep(s, """Comme pour l'attaque, tu choisis ton engagement — et <b>tu défends chez toi</b> : toutes tes communes voisines comptent pour toi.""",
"""Comme pour l'attaque, tu choisis ton engagement à chaque défense : <b>35, 50 ou 65 %</b> de chances pour 1, 2 ou 3 énergie. Tes communes voisines ne comptent pas en défense.""")
s = rep(s, """<p>Le même choix s'applique à la défense, et <b>le défenseur ne voit pas</b> avec quel engagement on l'a attaqué.</p>""",
"""<p>La défense se choisit à part, au moment de défendre, et <b>le défenseur ne voit pas</b> avec quel engagement on l'a attaqué.</p>""")
F.write_text(s, encoding='utf-8')

# ===================================================================== cloche
F = pathlib.Path('data/nouveautes.json'); d = json.loads(F.read_text(encoding='utf-8'))
assert d[0]['date'] == '2026-11-04'
d[0]['nouveautes'].insert(0, "🛡 Défense : tu choisis ton engagement à chaque défense, avec tes chances affichées : prudente 1 énergie (35 %), normale 2 (50 %), offensive 3 (65 %), comme l’attaque. Tes communes voisines ne comptent pas en défense")
F.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch338 appliqué')
