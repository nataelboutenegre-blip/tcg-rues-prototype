# patch535 (Arkhannou) : « ↻ Changer » une quête du jour, 1 par jour en Terra et 1 en Front (s3-73).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "let quetesTout = [];\nasync function loadQuetes(){\n  const { data, error } = await sb.rpc('quetes');",
"""let quetesTout = [];
let quetesRelance = null;   // patch535 : { terra: bool, front: bool } — une quête à changer par jour et par mode
const QUETES_FIXES = ['f_cdj', 'f_conquete', 't_bonus', 'f_bonus'];
async function loadQuetes(){
  sb.rpc('quetes_relance_etat').then(({ data, error }) => { quetesRelance = error ? null : data; if(!error) renderObjectifs(); });
  const { data, error } = await sb.rpc('quetes');""")
rep('app.js', """  const etat = o.reclame
    ? '<span class="obj-fait">Récupéré</span>'
    : (o.reclamable ? `<button class="obj-btn" data-objectif="${echapperTexte(o.id)}">Récupérer</button>` : '');""",
"""  const peutChanger = SAISON2 && quetesRelance && quetesRelance[o.mode] && o.categorie === 'jour' && !QUETES_FIXES.includes(o.id)
    && !o.reclame && !o.reclamable && Number(o.avancement) < Number(o.cible);   // patch535
  const etat = o.reclame
    ? '<span class="obj-fait">Récupéré</span>'
    : (o.reclamable ? `<button class="obj-btn" data-objectif="${echapperTexte(o.id)}">Récupérer</button>`
       : peutChanger ? `<button type="button" class="obj-changer" data-qrelance="${echapperTexte(o.id)}" title="Changer cette quête (1 par jour en ${o.mode === 'terra' ? 'Terra' : 'Front'})">↻ Changer</button>` : '');""")
rep('app.js', """  const btn = e.target.closest('[data-objectif]');
  if(!btn) return;
  btn.disabled = true;""",
"""  const rel = e.target.closest('[data-qrelance]');   // patch535
  if(rel){
    rel.disabled = true;
    const { data, error } = await sb.rpc('quete_relancer', { p_quete: rel.dataset.qrelance });
    if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); rel.disabled = false; return; }
    quetesRelance = data;
    notifier({ type: 'succes', titre: 'Quête changée', texte: 'Une nouvelle quête la remplace. Prochain changement demain.' });
    await loadQuetes();
    return;
  }
  const btn = e.target.closest('[data-objectif]');
  if(!btn) return;
  btn.disabled = true;""")
rep('style.css', "  .obj-btn:disabled{ opacity:0.5; cursor:default; }",
"""  .obj-btn:disabled{ opacity:0.5; cursor:default; }
  .obj-changer{ background:transparent; color:#C9D6EA; border:1px solid rgba(169,188,212,.4); border-radius:9px; padding:5px 9px; font:inherit; font-size:.78rem; font-weight:600; cursor:pointer; white-space:nowrap; }   /* patch535 */
  .obj-changer:disabled{ opacity:.45; cursor:default; }""")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = d[0]; assert e['date'] == '2026-11-25'
l = "↻ Quêtes : tu peux changer une quête du jour par jour en Terra et une en Front (pas les quêtes fixes ni une quête finie). La nouvelle vient de la même famille. Merci Arkhannou."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
