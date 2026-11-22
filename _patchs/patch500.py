# patch500 : la roue des paquets Terra (idée de Maroli et ASMFCB ; décision de Nataël 22/11 20 h 17). Va avec s3-53.
# Sous le choix du pays, « 🎡 Au hasard » : même prix, le serveur tire le pays (France 55 %, Suisse 25 %, Belgique 13 %,
# Luxembourg 7 %, réglables) et une fois sur 10 donne un paquet gratuit en plus. Avant d'ouvrir le paquet, une bande
# de drapeaux défile et s'arrête sur le pays tiré. Sans s3-53 (ou roue éteinte), le bouton n'apparaît pas.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
# 1. le réglage et le choix « roue »
rep(A, "function tcPays(){ return SUISSE ? tpPaysValide(tpLire('tf-coll-pays')) : 'FR'; }",
       "function tcPays(){ return SUISSE ? tpPaysValide(tpLire('tf-coll-pays')) : 'FR'; }\n"
       "// patch500 : la roue des paquets (s3-53)\n"
       "var TPR_CFG = null, TPR = null, TPR_LECTURE = null;\n"
       "function tprOuverte(){ return !!(TPR_CFG && Number(TPR_CFG.ouverte) === 1 && SUISSE); }\n"
       "function tpChoix(){ return tprOuverte() && tpLire('tf-terra-pays') === 'ROUE' ? 'ROUE' : tpPays(); }\n"
       "function tprCharger(){\n"
       "  if(TPR_CFG || TPR_LECTURE) return;\n"
       "  TPR_LECTURE = sb.rpc('terra_roue_reglages').then(({ data, error }) => { TPR_CFG = error ? { ouverte: 0 } : (data || { ouverte: 0 }); TPR_LECTURE = null; const z = document.getElementById('tpPays'); if(z) z.dataset.etat = ''; tpRendre(); }).catch(() => { TPR_LECTURE = null; });\n"
       "}\n"
       "function tprPoidsTexte(){\n"
       "  const P = (TPR_CFG && TPR_CFG.poids) || {}, ps = tpPaysOuverts().filter(p => Number(P[p]) > 0), tot = ps.reduce((s, p) => s + Number(P[p]), 0) || 1;\n"
       "  return ps.map(p => `${TP_NOMS[p]} ${Math.round(100 * Number(P[p]) / tot)} %`).join(', ');\n"
       "}")
# 2. le sélecteur : un bouton de plus, sous les pays
rep(A, "  z.innerHTML = tpSelecteurHtml(p, false)\n",
       "  z.innerHTML = tpSelecteurHtml(tpChoix() === 'ROUE' ? 'ROUE' : p, false)\n"
       "    + (tprOuverte() ? `<button type=\"button\" class=\"tpr-btn${tpChoix() === 'ROUE' ? ' on' : ''}\" data-tpp=\"ROUE\" aria-pressed=\"${tpChoix() === 'ROUE'}\">🎡 <b>Au hasard</b><span>un paquet offert 1 fois sur ${Math.max(1, Math.round(100 / (Number(TPR_CFG.bonus_pct) || 10)))}</span></button>` : '')   // patch500\n")
rep(A, "  const p = tpPays(), etat = p + (tpNouveauVu('CH') ? 'v' : '')",
       "  tprCharger();   // patch500\n  const p = tpPays(), etat = tpChoix() + (tprOuverte() ? 'r' : '') + (tpNouveauVu('CH') ? 'v' : '')")
rep(A, "    + `<p class=\"tp-note\">${p === 'CH' ?",
       "    + (tpChoix() === 'ROUE' ? `<p class=\"tp-note\">La roue choisit le pays : ${tprPoidsTexte()}. Même jeton, même prix. Une fois sur ${Math.max(1, Math.round(100 / (Number(TPR_CFG.bonus_pct) || 10)))}, un paquet gratuit en plus.</p>` :   // patch500\n"
       "    `<p class=\"tp-note\">${p === 'CH' ?")
# fermer la parenthèse ouverte ci-dessus : la note des pays se termine par </p>`;
rep(A, "les raretés tombent aussi souvent dans ${LUXEMBOURG ? 'les quatre' : BELGIQUE ? 'les trois' : 'les deux'}.</p>`;",
       "les raretés tombent aussi souvent dans ${LUXEMBOURG ? 'les quatre' : BELGIQUE ? 'les trois' : 'les deux'}.</p>`);")
rep(A, "  const b = ev.target.closest('[data-tpp]');\n  if(!b) return;\n  tpEcrire('tf-terra-pays', tpPaysValide(b.dataset.tpp));",
       "  const b = ev.target.closest('[data-tpp]');\n  if(!b) return;\n  tpEcrire('tf-terra-pays', b.dataset.tpp === 'ROUE' && tprOuverte() ? 'ROUE' : tpPaysValide(b.dataset.tpp));   // patch500")
# 3. ouvrir le paquet par la roue
rep(A, """  if(enTerra()){
    // Terra : le serveur paie et tire les 5 cartes en un seul appel
    const { data, error } = await briRpcPaquet('terra_ouvrir_paquet', tpArgs({ p_paye: type === 'achete' }));   // patch269, patch407 : le pays""",
       """  if(enTerra() && tpChoix() === 'ROUE'){   // patch500 : la roue tire le pays
    const { data, error } = await sb.rpc('terra_roue', { p_paye: type === 'achete' });
    if(!error && data && Array.isArray(data.cartes)){
      terraPaquet = data.cartes; tpPaquetPaye = data.pays || 'FR'; TPR = { pays: tpPaquetPaye, bonus: !!data.bonus };
      terraPaquetBloque = type === 'achete';
      viderBilanTerra();
      return null;
    }
    if(error && !fonctionAbsente(error)){ terraPaquet = null; return error; }
  }
  if(enTerra()){
    // Terra : le serveur paie et tire les 5 cartes en un seul appel
    const { data, error } = await briRpcPaquet('terra_ouvrir_paquet', tpArgs({ p_paye: type === 'achete' }));   // patch269, patch407 : le pays""")
rep(A, """  const zone = document.getElementById('packZone');
  zone.innerHTML = '';
  const pack = makePackEl(type);
  if(enTerra()) tpHabiller(pack, tpPaquetPaye);   // patch407""",
       """  const zone = document.getElementById('packZone');
  zone.innerHTML = '';
  if(enTerra() && TPR){ const r = TPR; TPR = null; tprAnimer(zone, r, () => afficherPaquetATirer(type, nbCartes)); return; }   // patch500 : d'abord la roue
  const pack = makePackEl(type);
  if(enTerra()) tpHabiller(pack, tpPaquetPaye);   // patch407""")
rep(A, "function paquetSansCarte(zone){", r'''// patch500 : la bande de drapeaux qui défile et s'arrête sur le pays tiré
function tprAnimer(zone, r, suite){
  const ps = tpPaysOuverts(), N = 26, CIBLE = 22, L = 96;
  const items = Array.from({ length: N }, (_, i) => i === CIBLE ? r.pays : ps[Math.floor(Math.random() * ps.length)]);
  zone.innerHTML = `<div class="tpr"><p class="tpr-t">🎡 La roue tourne…</p>
    <div class="tpr-fen"><div class="tpr-bande">${items.map(p => `<span class="tpr-i">${tpDrapeau(p)}<b>${TP_NOMS[p]}</b></span>`).join('')}</div><i class="tpr-curseur" aria-hidden="true"></i></div>
    <p class="tpr-r" role="status"></p></div>`;
  const bande = zone.querySelector('.tpr-bande'), fen = zone.querySelector('.tpr-fen');
  const rapide = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fin = () => {
    const res = zone.querySelector('.tpr-r'), t = zone.querySelector('.tpr-t');
    if(t) t.textContent = '🎡 La roue a choisi';
    if(res) res.innerHTML = `${tpDrapeau(r.pays)}<b>Paquet ${TP_NOMS[r.pays]} !</b>${r.bonus ? '<span class="tpr-bonus">🎁 Et un paquet gratuit en plus</span>' : ''}`;
    const it = bande && bande.children[CIBLE]; if(it) it.classList.add('gagne');
    if(r.bonus){ notifier({ type: 'succes', titre: '🎁 Paquet offert', texte: 'La roue t’a donné un paquet gratuit en plus.' }); try{ loadPackStatus(); }catch(e){} }
    setTimeout(suite, r.bonus ? 1700 : 1100);
  };
  requestAnimationFrame(() => {
    const w = fen ? fen.clientWidth : 288;
    bande.style.transition = `transform ${rapide ? 0.25 : 2.3}s cubic-bezier(.12,.62,.1,1)`;
    bande.style.transform = `translateX(${Math.round(w / 2 - (CIBLE + 0.5) * L)}px)`;
    setTimeout(fin, rapide ? 300 : 2400);
  });
}
function paquetSansCarte(zone){''')
rep(A, "  if(enTerra()) tpHabiller(pack, tpPays());   // patch407",
       "  if(enTerra()) tpHabiller(pack, tpChoix());   // patch407 ; patch500 : le paquet surprise")
rep(A, "function tpHabiller(pack, pays){\n",
       "function tpHabiller(pack, pays){\n"
       "  if(pack && pays === 'ROUE'){   // patch500 : le paquet de la roue, avant le tirage\n"
       "    pack.classList.add('paquet-roue');\n"
       "    const et = pack.querySelector('.paquet-etiquette'); if(et) et.innerHTML = '<span class=\"tpr-emb\" aria-hidden=\"true\">🎡</span><span class=\"paquet-titre\">Paquet surprise</span>';\n"
       "    const bd = pack.querySelector('.paquet-bande'); if(bd) bd.textContent = 'Pays au hasard';\n"
       "    return;\n"
       "  }\n")
p = os.path.join(R, 'style.css'); t = open(p, encoding='utf-8').read()
M = '/* ---------- patch500 : la roue des paquets Terra ---------- */'
if M not in t:
    t = t.rstrip('\n') + '\n\n' + M + """
.tpr-btn{ display:flex; align-items:center; gap:8px; margin:-4px 0 10px; padding:8px 14px; border-radius:999px; border:1px dashed rgba(240,180,41,.5); background:rgba(240,180,41,.06); color:#FFE3A3; font:inherit; font-size:.88rem; cursor:pointer; max-width:100%; }
.tpr-btn b{ font-weight:800; }
.tpr-btn span{ font-size:.74rem; color:var(--brume); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.tpr-btn.on{ border-style:solid; background:rgba(240,180,41,.18); box-shadow:inset 0 0 0 1px rgba(240,180,41,.55); color:#fff; }
.tpr-btn.on span{ color:#FFE3A3; }
.tp-pays:has(+ .tpr-btn.on) button.on{ background:none; box-shadow:none; color:var(--brume); }
.tpr{ display:flex; flex-direction:column; align-items:center; gap:14px; padding:26px 0 18px; }
.tpr-t{ margin:0; font-weight:800; font-size:1.05rem; color:#FFE3A3; }
.tpr-fen{ position:relative; width:min(300px, 86vw); height:96px; overflow:hidden; border-radius:16px; background:#0E1A2E; border:1px solid rgba(240,180,41,.4); box-shadow:inset 0 0 18px rgba(0,0,0,.6); }
.tpr-fen::before, .tpr-fen::after{ content:''; position:absolute; top:0; bottom:0; width:60px; z-index:2; pointer-events:none; }
.tpr-fen::before{ left:0; background:linear-gradient(90deg, #0E1A2E, transparent); }
.tpr-fen::after{ right:0; background:linear-gradient(270deg, #0E1A2E, transparent); }
.tpr-bande{ display:flex; height:100%; will-change:transform; }
.tpr-i{ flex:0 0 96px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:6px; font-size:.72rem; color:var(--brume); }
.tpr-i .tp-drap{ width:42px; height:28px; border-radius:4px; }
.tpr-i .tp-drap.tp-drap-ch{ width:30px; height:30px; }
.tpr-i.gagne{ color:#fff; }
.tpr-i.gagne b{ color:#FFD36B; }
.tpr-curseur{ position:absolute; left:50%; top:0; bottom:0; width:96px; transform:translateX(-50%); border-left:2px solid rgba(240,180,41,.7); border-right:2px solid rgba(240,180,41,.7); z-index:3; pointer-events:none; }
.tpr-r{ margin:0; min-height:1.6em; display:flex; flex-wrap:wrap; justify-content:center; align-items:center; gap:8px; font-size:1.05rem; }
.tpr-r .tp-drap{ width:24px; height:16px; }
.tpr-r .tp-drap.tp-drap-ch{ width:18px; height:18px; }
.tpr-bonus{ flex-basis:100%; text-align:center; font-weight:800; color:#8EE3B8; }
.paquet.paquet-roue .paquet-bande{ background:linear-gradient(90deg, #2B5BD7, #DA291C 40%, #FDDA24 70%, #00A3E0); color:#fff; text-shadow:0 1px 2px rgba(0,0,0,.5); }
.paquet .tpr-emb{ font-size:1.3rem; line-height:1; }
"""
    open(p, 'w', encoding='utf-8').write(t); print('style.css : ok')
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = next(x for x in d if x.get('date') == '2026-11-22')
l = "🎡 Terra : « Au hasard » sous le choix du pays. La roue choisit le pays de ton paquet (même prix), et une fois sur 10 elle t'offre un paquet gratuit en plus (idée de Maroli et ASMFCB)."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
