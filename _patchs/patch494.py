# patch494 : la fiche d'un siège dit ce que devient l'énergie d'une vague (question d'ASMFCB, 22/11 16 h 15).
# Sur un siège long (légendaire, garnison, renfort) ou une épique, une grosse vague reste bloquée des heures.
# - Sous le choix de l'énergie : « X partent tout de suite, Y attendront leur tour (≈ durée) », et l'énergie de trop.
# - L'énergie déjà en attente compte : « Juste assez », la suggestion et « énergie pour finir » la retirent.
#   Si elle suffit : « Tes N ⚡ en attente suffisent pour finir ».
# Calcul côté jeu avec ce que le serveur envoie déjà (plafond, envoyes_long, attente, rythme). Aucun SQL.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
rep(A, """function sgSuggestion(){
  const a = SG.ap; if(!a) return 5;
  const e = sgEnergie(), neuf = !a.siege;
  const max = Math.max(1, Math.min(Number(a.vague_max) || 60, e === null ? 99 : e - (neuf ? Number(a.pose) || 2 : 0)));
  return Math.max(1, Math.min(sgReste(), max));
}""", """// patch494 : l'énergie déjà en attente dans le siège compte
function sgAttente(){ const s = SG.ap && SG.ap.siege && !SG.ap.siege.resultat ? SG.ap.siege : null; return s ? Number(s.attente) || 0 : 0; }
function sgResteNet(){ return Math.max(0, sgReste() - sgAttente()); }
function sgSuggestion(){
  const a = SG.ap; if(!a) return 5;
  const e = sgEnergie(), neuf = !a.siege;
  const max = Math.max(1, Math.min(Number(a.vague_max) || 60, e === null ? 99 : e - (neuf ? Number(a.pose) || 2 : 0)));
  return Math.max(1, Math.min(sgResteNet() || 1, max));
}
// patch494 : ce que devient une vague de n énergie (tout de suite, en attente, de trop)
function sgRepartition(n){
  const a = SG.ap; if(!a) return null;
  const s = a.siege && !a.siege.resultat ? a.siege : null;
  const pts = 10 * (Number(a.mult) || 1);
  const res = Number(s ? s.resistance : a.resistance) || 0, deg = Number(s ? s.degats : 0) || 0, bcl = Number(s ? s.bouclier : a.bouclier) || 0;
  const att = sgAttente(), besoin = Math.ceil(Math.max(0, res - deg + bcl) / pts);
  const long = s ? !!s.long : !!a.long;
  let plafond = null, envoyes = 0;
  if(s && s.plafond != null){ plafond = Number(s.plafond); envoyes = Number(s.envoyes_long) || 0; }
  else if(!s && (long || a.eclair_min)) plafond = res * 0.1;   // 10 % part tout de suite
  const duree = long ? Number(a.duree_long_min) : Number(a.eclair_min);
  const rythme = plafond != null && duree > 0 ? res * 60 / duree : null;   // points par heure
  const utile = Math.max(0, Math.min(n, besoin - att)), trop = n - utile;
  if(plafond == null) return { maintenant: utile, attend: 0, trop, att, besoin, finit: att + n >= besoin, minutes: 0 };
  const k = Math.max(0, Math.ceil((plafond - envoyes) / pts));
  const passe = Math.min(att + n, k, besoin);
  const maintenant = Math.min(utile, Math.max(0, passe - att));
  const total = Math.min(att + n, besoin);
  const minutes = rythme ? Math.max(0, (envoyes + total * pts - plafond) / rythme * 60) : 0;
  return { maintenant, attend: utile - maintenant, trop, att, besoin, finit: att + n >= besoin, minutes };
}
function sgRepartitionHtml(n){
  const r = sgRepartition(n); if(!r) return '';
  if(r.att > 0 && r.besoin <= r.att) return `<p class="sg-repart ok">Tes <b>${r.att} ⚡</b> en attente suffisent pour finir : pas besoin d'en renvoyer. Ce qui sera de trop te reviendra à la fin.</p>`;
  if(!r.attend && !r.trop) return '';
  const quand = r.minutes >= 1 ? (r.finit ? `elle peut tomber dans ≈ <b>${sgDuree(r.minutes)}</b> si personne ne renforce` : `≈ <b>${sgDuree(r.minutes)}</b> pour qu'elles partent toutes`) : '';
  const debut = r.maintenant ? `<b>${r.maintenant}</b> part${r.maintenant > 1 ? 'ent' : ''} tout de suite` : 'aucune ne part tout de suite';
  return `<p class="sg-repart">⏳ Sur ces ${n} ⚡ : ${debut}${r.attend ? `, <b>${r.attend}</b> attendront leur tour et partiront toutes seules` : ''}${quand ? ` (${quand})` : ''}.`
    + `${r.trop ? ` <b>${r.trop}</b> de trop${r.att ? ' avec ce qui attend déjà' : ''} : elles te reviendront à la fin du siège.` : ''}</p>`;
}""")
rep(A, """      <div><b>≈ ${sgReste()}</b><span>énergie ${s ? 'pour finir' : 'en tout'}</span></div></div>`;""",
       """      <div><b>≈ ${sgAttente() ? sgResteNet() : sgReste()}</b><span>énergie ${s ? (sgAttente() ? 'à envoyer en plus' : 'pour finir') : 'en tout'}</span></div></div>`;   // patch494""")
rep(A, """<button type="button" data-sg-v="fin"${n === sgReste() ? ' class="on"' : ''}>Juste assez</button>""",
       """<button type="button" data-sg-v="fin"${n === Math.max(1, sgResteNet()) ? ' class="on"' : ''}>Juste assez</button>""")
rep(A, """      ${e !== null ? `<small>Tu as <b>${e} ⚡</b></small>` : ''}
    </div>`;""", """      ${e !== null ? `<small>Tu as <b>${e} ⚡</b></small>` : ''}
    </div>${sgRepartitionHtml(n)}`;   // patch494""")
rep(A, """if(t.dataset.sgV){ SG.n = t.dataset.sgV === 'fin' ? sgReste() : Number(t.dataset.sgV); sgRendre(); return; }""",
       """if(t.dataset.sgV){ SG.n = t.dataset.sgV === 'fin' ? Math.max(1, sgResteNet()) : Number(t.dataset.sgV); sgRendre(); return; }   // patch494""")
p = os.path.join(R, 'style.css'); t = open(p, encoding='utf-8').read()
M = '/* ---------- patch494 : ce que devient une vague ---------- */'
if M not in t:
    t = t.rstrip('\n') + '\n\n' + M + """
.sg-repart{ margin:-4px 0 12px; padding:9px 12px; border-radius:10px; background:rgba(143,193,255,.10); border:1px solid rgba(143,193,255,.28); color:#CFE3FF; font-size:.84rem; line-height:1.45; }
.sg-repart b{ color:#fff; }
.sg-repart.ok{ background:rgba(95,211,157,.10); border-color:rgba(95,211,157,.32); color:#C9F2DD; }
"""
    open(p, 'w', encoding='utf-8').write(t); print('style.css : ok')
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = next(x for x in d if x.get('date') == '2026-11-22')
l = "Siège : la fiche dit ce que devient ta vague (ce qui part tout de suite, ce qui attend son tour et combien de temps, ce qui est de trop). L'énergie déjà en attente compte dans « Juste assez » (question d'ASMFCB)."
e.setdefault('correctifs', [])
if l not in e['correctifs']: e['correctifs'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
