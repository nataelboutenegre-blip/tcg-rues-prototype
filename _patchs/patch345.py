# patch345 (4/11/2026) : la discussion propose les pseudos après @ (aperçu
# validé « parfait »).
# - Dès « @ » et 2 lettres : une liste « Mentionner » au-dessus du champ, 5
#   pseudos au plus qui commencent par ces lettres. D'abord les joueurs qui ont
#   écrit dans la discussion (« dans la discussion »), puis tous les joueurs
#   (même recherche que dans Amis).
# - Toucher un pseudo l'écrit en entier, suivi d'une espace. Sur ordinateur :
#   flèches, Entrée ou Tab pour choisir, Échap pour fermer.
import pathlib, json

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

# ====================================================================== app.js
F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
SUGG_JS = r"""
// ---------- patch345 : proposer les pseudos après @ dans la discussion ----------
var DG_SUGG = { liste: [], i: 0, debut: -1, q: '', minuteur: null, seq: 0 };
function dgSuggFermer(){
  document.querySelectorAll('.dg-sugg').forEach(x => x.remove());
  DG_SUGG.liste = []; DG_SUGG.debut = -1; DG_SUGG.seq++;
}
// le mot en cours de frappe, s'il commence par @ et fait au moins 2 lettres
function dgSuggMot(champ){
  if(!champ) return null;
  const pos = champ.selectionStart == null ? champ.value.length : champ.selectionStart;
  const m = champ.value.slice(0, pos).match(/(^|\s)@([^\s@]{2,20})$/);
  return m ? { q: m[2], debut: pos - m[2].length - 1 } : null;
}
function dgSuggRendre(){
  const f = document.getElementById('dgForm');
  if(!f) return;
  document.querySelectorAll('.dg-sugg').forEach(x => x.remove());
  if(!DG_SUGG.liste.length) return;
  const n = DG_SUGG.q.length;
  f.insertAdjacentHTML('afterbegin', `<div class="dg-sugg" role="listbox" aria-label="Mentionner un joueur"><p class="dg-sugg-t">Mentionner</p>${DG_SUGG.liste.map((j, i) => {
    const p = String(j.pseudo || '');
    return `<button type="button" class="dg-sugg-l${i === DG_SUGG.i ? ' on' : ''}" role="option" aria-selected="${i === DG_SUGG.i}" data-dg-sugg="${i}"><span class="dg-av" style="background:${colorForPlayer(j.id || '')}">${echapperTexte(p.slice(0, 1).toUpperCase())}</span><span class="dg-sugg-p"><b>${echapperTexte(p.slice(0, n))}</b>${echapperTexte(p.slice(n))}</span>${j.clan ? `<span class="dg-tag">${echapperTexte(j.clan)}</span>` : ''}${j.recent ? '<em>dans la discussion</em>' : ''}</button>`;
  }).join('')}</div>`);
}
function dgSuggMaj(champ){
  const mot = dgSuggMot(champ);
  if(!mot){ if(DG_SUGG.liste.length || document.querySelector('.dg-sugg')) dgSuggFermer(); return; }
  const q = mot.q, ql = sansAccents(q.toLowerCase()), moi = window.__monId || '';
  DG_SUGG.q = q; DG_SUGG.debut = mot.debut;
  // d'abord ceux qui ont écrit dans la discussion, du plus récent au plus ancien
  const vus = new Map();
  for(let i = DG.msgs.length - 1; i >= 0; i--){
    const m = DG.msgs[i];
    if(!m.auteur || m.auteur === moi || m.retire || vus.has(m.auteur)) continue;
    vus.set(m.auteur, { id: m.auteur, pseudo: m.pseudo, clan: m.clan, recent: true });
  }
  DG_SUGG.liste = [...vus.values()].filter(j => sansAccents(String(j.pseudo || '').toLowerCase()).startsWith(ql)).slice(0, 5);
  DG_SUGG.i = 0;
  dgSuggRendre();
  if(DG_SUGG.liste.length >= 5) return;
  // puis tous les joueurs (même recherche que dans Amis), après une pause de frappe
  clearTimeout(DG_SUGG.minuteur);
  const seq = ++DG_SUGG.seq;
  DG_SUGG.minuteur = setTimeout(async () => {
    try{
      const motif = q.replace(/[^\p{L}\p{N} ._-]/gu, '');
      if(motif.length < 2) return;
      const { data, error } = await sb.from('joueurs').select('id, pseudo').ilike('pseudo', motif + '%').limit(8);
      if(error || seq !== DG_SUGG.seq) return;
      const deja = new Set(DG_SUGG.liste.map(j => j.id));
      for(const j of data || []){
        if(!j || j.id === moi || deja.has(j.id)) continue;
        DG_SUGG.liste.push({ id: j.id, pseudo: j.pseudo });
        if(DG_SUGG.liste.length >= 5) break;
      }
      dgSuggRendre();
    }catch(e){}
  }, 250);
}
function dgSuggChoisir(i){
  const j = DG_SUGG.liste[i], c = document.getElementById('dgTexte');
  if(!j || !c || DG_SUGG.debut < 0) return;
  const pos = c.selectionStart == null ? c.value.length : c.selectionStart;
  const avant = c.value.slice(0, DG_SUGG.debut), ins = '@' + j.pseudo + ' ';
  c.value = (avant + ins + c.value.slice(pos)).slice(0, 300);
  const p = Math.min(c.value.length, avant.length + ins.length);
  dgSuggFermer();
  c.focus();
  try{ c.setSelectionRange(p, p); }catch(e){}
  c.dispatchEvent(new Event('input', { bubbles: true }));
}
document.addEventListener('input', (e) => { if(e.target.id === 'dgTexte') dgSuggMaj(e.target); });
// toucher la liste ne doit pas faire perdre le champ (ni fermer le clavier du téléphone)
document.addEventListener('mousedown', (e) => { if(e.target.closest('.dg-sugg')) e.preventDefault(); });
document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-dg-sugg]');
  if(b){ dgSuggChoisir(Number(b.dataset.dgSugg)); return; }
  if(DG_SUGG.liste.length && !e.target.closest('.dg-sugg, #dgTexte')) dgSuggFermer();
});
document.addEventListener('keydown', (e) => {
  if(e.target.id !== 'dgTexte' || !DG_SUGG.liste.length || !document.querySelector('.dg-sugg')) return;
  const n = DG_SUGG.liste.length;
  if(e.key === 'ArrowDown' || e.key === 'ArrowUp'){
    e.preventDefault();
    DG_SUGG.i = (DG_SUGG.i + (e.key === 'ArrowDown' ? 1 : -1) + n) % n;
    dgSuggRendre();
  } else if(e.key === 'Enter' || e.key === 'Tab'){
    e.preventDefault();
    dgSuggChoisir(DG_SUGG.i);
  } else if(e.key === 'Escape'){
    e.preventDefault(); e.stopPropagation();
    dgSuggFermer();
  }
});
"""
s = rep(s, """
// ---------- patch313 : le sondage « d'autres pays ? » (s2-80) ----------""", SUGG_JS + """
// ---------- patch313 : le sondage « d'autres pays ? » (s2-80) ----------""")
F.write_text(s, encoding='utf-8')

# =================================================================== style.css
F = pathlib.Path('style.css'); s = F.read_text(encoding='utf-8')
s += """
/* patch345 : les pseudos proposés après @ */
.dg-saisie{ position:relative; }
.dg-sugg{ position:absolute; left:0; right:52px; bottom:calc(100% + 6px); z-index:5; background:#0F1D33; border:1px solid rgba(169,188,212,.25); border-radius:12px; padding:4px; box-shadow:0 12px 30px rgba(0,0,0,.55); }
.dg-sugg-t{ font-size:.62rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; color:#6F84A3; padding:4px 8px 2px; margin:0; }
.dg-sugg-l{ display:flex; align-items:center; gap:9px; width:100%; box-sizing:border-box; padding:7px 8px; border:0; border-radius:9px; background:none; color:#E6EDF6; font:inherit; font-size:.9rem; text-align:left; cursor:pointer; }
.dg-sugg-l.on{ background:rgba(240,180,41,.14); }
@media (hover: hover){ .dg-sugg-l:hover{ background:rgba(240,180,41,.08); } }
.dg-sugg-l .dg-av{ width:24px; height:24px; font-size:.7rem; }
.dg-sugg-p{ min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.dg-sugg-l b{ color:#FFD35A; font-weight:800; }
.dg-sugg-l em{ margin-left:auto; padding-left:6px; font-style:normal; font-size:.68rem; color:#7F92AA; white-space:nowrap; }
"""
F.write_text(s, encoding='utf-8')

# ======================================================= data/nouveautes.json
F = pathlib.Path('data/nouveautes.json'); d = json.loads(F.read_text(encoding='utf-8'))
assert d[0]['date'] == '2026-11-04', d[0]['date']
assert d[0]['nouveautes'][0].startswith('💬 Discussion'), d[0]['nouveautes'][0][:30]
d[0]['nouveautes'][0] = d[0]['nouveautes'][0] + ". Tape @ et les premières lettres d’un pseudo : le jeu te le propose"
F.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch345 appliqué')
