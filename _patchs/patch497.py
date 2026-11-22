# patch497 : un minuteur dans la fiche d'un siège (idée d'Oshannir, 22/11 19 h ; « C'est une bonne idée » de Nataël).
# Sous la jauge : « Elle peut tomber dans 12:40 » quand l'énergie qui attend suffit, sinon « Ton énergie en attente
# aura fini de partir dans 08:10, puis il manquera ≈ 1 ⚡ », ou « Il manque ≈ 1 ⚡ : envoie une vague » quand rien n'attend.
# Calcul côté jeu : le plafond du siège monte de résistance / durée par minute (siège long, ou rare et épique en éclair) ;
# l'énergie qui attend part au passage suivant (toutes les 5 min). À zéro, la fiche se relit.
# Va avec s3-51 (jauge arrondie vers le bas). sgRepartition (patch494) suit aussi le plafond qui monte.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
rep(A, "  SG.ap = data || null; SG.err = '';", "  SG.ap = data || null; SG.err = ''; SG.apLe = Date.now();   // patch497 : l'heure de lecture, pour le plafond qui monte")
rep(A, "  if(s && s.plafond != null){ plafond = Number(s.plafond); envoyes = Number(s.envoyes_long) || 0; }",
       "  if(s && s.plafond != null){ plafond = sgPlafondMaintenant(); envoyes = Number(s.envoyes_long) || 0; }   // patch497")
rep(A, "function sgRepartitionHtml(n){", r'''// patch497 : le plafond du siège monte avec le temps ; le serveur l'a donné au moment de la lecture
function sgRythmeMin(){   // points par minute, ou null si la jauge n'a pas de rythme (éclair sans durée minimale)
  const a = SG.ap; if(!a) return null;
  const s = a.siege && !a.siege.resultat ? a.siege : null;
  const res = Number(s ? s.resistance : a.resistance) || 0, long = s ? !!s.long : !!a.long;
  const duree = long ? Number(a.duree_long_min) : Number(a.eclair_min);
  return res > 0 && duree > 0 ? res / duree : null;
}
function sgPlafondMaintenant(){
  const s = SG.ap && SG.ap.siege; if(!s || s.plafond == null) return null;
  const r = sgRythmeMin();
  return Number(s.plafond) + (r ? r * Math.max(0, Date.now() - (SG.apLe || Date.now())) / 60000 : 0);
}
// patch497 : le minuteur sous la jauge
function sgMinuteurInfo(){
  const a = SG.ap; if(!a) return null;
  const s = a.siege && !a.siege.resultat ? a.siege : null; if(!s) return null;
  const pts = 10 * (Number(a.mult) || 1), res = Number(s.resistance) || 0, deg = Number(s.degats) || 0, bcl = Number(s.bouclier) || 0;
  const att = Number(s.attente) || 0, resteP = Math.max(0, res - deg + bcl);
  if(resteP <= 0) return null;
  const besoin = Math.max(1, Math.ceil(resteP / pts));
  if(att <= 0) return { texte: `Il manque ≈ <b>${besoin} ⚡</b> pour finir : rien n'attend dans ton siège, envoie une vague.` };
  const plafond = sgPlafondMaintenant(), r = sgRythmeMin();
  let min = 0;
  const suffit = att >= besoin;
  if(plafond != null && r){
    const cible = (Number(s.envoyes_long) || 0) + (suffit ? resteP : att * pts);
    min = Math.max(0, (cible - plafond) / r);
  }
  return { fin: Date.now() + min * 60000, suffit, manque: besoin - att };
}
function sgMinuteurTexte(i){
  const ms = i.fin - Date.now();
  const t = ms <= 0 ? 'au prochain passage (toutes les 5 min)' : 'dans <b class="sg-chrono">' + sgChrono(ms) + '</b>';
  return i.suffit ? `⏱️ Elle peut tomber ${t}, si personne ne renforce.`
    : `⏱️ Ton énergie en attente aura fini de partir ${t}. Il manquera ensuite ≈ <b>${i.manque} ⚡</b>.`;
}
function sgChrono(ms){
  const s = Math.ceil(ms / 1000), h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60;
  return h ? `${h} h ${String(m).padStart(2, '0')}` : `${String(m).padStart(2, '0')}:${String(x).padStart(2, '0')}`;
}
function sgMinuteurHtml(){
  const i = sgMinuteurInfo(); if(!i) return '';
  if(i.fin == null) return `<p class="sg-minuteur">${i.texte}</p>`;
  return `<p class="sg-minuteur" data-sg-fin="${Math.round(i.fin)}" data-sg-suffit="${i.suffit ? 1 : 0}" data-sg-manque="${i.manque}">${sgMinuteurTexte(i)}</p>`;
}
function sgTic(){
  const el = document.querySelector('#sgBoite [data-sg-fin]');
  if(!el){ clearInterval(SG.tic); SG.tic = 0; return; }
  const i = { fin: Number(el.dataset.sgFin), suffit: el.dataset.sgSuffit === '1', manque: Number(el.dataset.sgManque) || 0 };
  el.innerHTML = sgMinuteurTexte(i);
  if(Date.now() > i.fin + 60000 && !SG.relu){ SG.relu = true; sgCharger(false).then(() => { SG.relu = false; }); }   // une minute après : on relit
}
function sgRepartitionHtml(n){''')
rep(A, """        ${tombe > 0 ? `<p class="sg-tombe">Sans nouvelle vague, le siège tombe dans ${formatDuree(tombe)}.</p>` : ''}
      </div>`;""", """        ${sgMinuteurHtml()}
        ${tombe > 0 ? `<p class="sg-tombe">Sans nouvelle vague, le siège tombe dans ${formatDuree(tombe)}.</p>` : ''}
      </div>`;   // patch497 : le minuteur""")
rep(A, "  sgAnimerVague(b);   // patch406\n}", "  sgAnimerVague(b);   // patch406\n  if(!SG.tic && b.querySelector('[data-sg-fin]')) SG.tic = setInterval(sgTic, 1000);   // patch497\n}")
rep(A, "  SG = { code, ap: null, n: 5, envoi: false, dernier: null, err: '', anim: null, calc: SG.calc || false };   // patch406 : anim, calc",
       "  if(SG && SG.tic) clearInterval(SG.tic);   // patch497\n  SG = { code, ap: null, n: 5, envoi: false, dernier: null, err: '', anim: null, calc: SG.calc || false, tic: 0 };   // patch406 : anim, calc")
p = os.path.join(R, 'style.css'); t = open(p, encoding='utf-8').read()
M = '/* ---------- patch497 : le minuteur du siège ---------- */'
if M not in t:
    t = t.rstrip('\n') + '\n\n' + M + """
.sg-minuteur{ margin:9px 0 0; padding:8px 10px; border-radius:10px; background:rgba(240,180,41,.10); border:1px solid rgba(240,180,41,.28); color:#FFE3A3; font-size:.8rem; line-height:1.4; }
.sg-minuteur b{ color:#fff; }
.sg-minuteur .sg-chrono{ font-family:var(--titre, 'Big Shoulders Display'), Impact, sans-serif; font-weight:800; font-size:1.05rem; letter-spacing:.02em; font-variant-numeric:tabular-nums; color:#FFD36B; }
"""
    open(p, 'w', encoding='utf-8').write(t); print('style.css : ok')
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = next(x for x in d if x.get('date') == '2026-11-22')
l = "⏱️ Siège : un minuteur sous la jauge dit quand la commune peut tomber, ou quand ton énergie en attente aura fini de partir et ce qu'il manquera (idée d'Oshannir). La jauge n'affiche plus « 65 / 65 » quand il manque une fraction de point."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
