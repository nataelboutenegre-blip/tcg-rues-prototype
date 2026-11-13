# patch432 (13/11/2026) : le Mess compte pour le classement (va avec s3-12 ; Oshannir, décision de Nataël : 25 énergies par jour + des lingots).
#  - lots avec énergie et lingots dans les tables (Machine, Recensement), et dans les résultats ;
#  - « Ration du jour : énergie 9 / 25 · lingots 2 / 6 » dans la fenêtre du Mess ; au-delà, des TP ;
#  - Règles : la ration.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, S, H = 'app.js', 'style.css', 'index.html'
if 'patch432' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')
if 'patch430' not in open(A, encoding='utf-8').read(): sys.exit('patch430 manquant')

rep(A, """  if(l.tp) p.push(`${l.tp} TP`);
  if(l.energie) p.push(`+${l.energie} énergie (1 fois par jour)`);
  return p.join(' + ');""", """  if(l.tp) p.push(`${l.tp} TP`);
  if(l.energie) p.push(`${l.energie} ⚡`);   // patch432
  if(l.lingots) p.push(`${l.lingots} lingot${l.lingots > 1 ? 's' : ''}`);
  return p.join(' + ');""")
# résultats : énergie et lingots
rep(A, """    if(g.energie) chips.push(`+${g.energie} énergie`);
    if(g.tp) chips.push(`+${g.tp} TP`);""", """    if(g.energie) chips.push(`+${g.energie} énergie`);
    if(g.lingots) chips.push(`+${g.lingots} lingot${g.lingots > 1 ? 's' : ''}`);   // patch432
    if(g.tp) chips.push(`+${g.tp} TP`);""")
rep(A, """      if(g.terra) chips.push(`+${g.terra} paquet${g.terra > 1 ? 's' : ''} Terra`);
      if(g.tp) chips.push(`+${g.tp} TP`);
      const titre = {""", """      if(g.terra) chips.push(`+${g.terra} paquet${g.terra > 1 ? 's' : ''} Terra`);
      if(g.energie) chips.push(`+${g.energie} énergie`);   // patch432
      if(g.lingots) chips.push(`+${g.lingots} lingot${g.lingots > 1 ? 's' : ''}`);
      if(g.tp) chips.push(`+${g.tp} TP`);
      const titre = {""")
# table du Recensement
rep(A, """      <div class="mess-l"><span>Tu dépasses le Préfet sans franchir le plafond</span><span class="mess-lot">${(L.gagne && L.gagne.tp) || 50} TP</span></div>
      <div class="mess-l"><span>Recensement parfait (${messNb(R.parfait || 47500)} à ${messNb(plafond)})</span><span class="mess-lot or">${(L.parfait && L.parfait.terra) || 1} paquet Terra</span></div>""",
"""      <div class="mess-l"><span>Tu dépasses le Préfet sans franchir le plafond</span><span class="mess-lot">${messLotTexte('gagne', L.gagne) || '50 TP'}</span></div>
      <div class="mess-l"><span>Recensement parfait (${messNb(R.parfait || 47500)} à ${messNb(plafond)})</span><span class="mess-lot or">${messLotTexte('parfait', L.parfait) || '1 paquet Terra'}</span></div>""")
rep(A, """    <p class="mess-note">Des communes de 3 000 à 60 000 habitants. Tu vois leur nom, pas leur population : connaître la France aide.</p>`;""",
"""    ${messRationHtml()}
    <p class="mess-note">Des communes de 3 000 à 60 000 habitants. Tu vois leur nom, pas leur population : connaître la France aide.</p>`;""")
# la ration sous la table de la Machine
rep(A, """        <div class="mess-table"><h3>Les lots</h3>${messTableHtml()}</div>""",
"""        <div class="mess-table"><h3>Les lots</h3>${messTableHtml()}</div>
        <div data-mess="ration">${messRationHtml()}</div>""")
rep(A, """  const t = fen.querySelector('[data-mess="tickets"]'); if(t) t.textContent = Number(MESS.tickets) || 0;
  const b = fen.querySelector('[data-mess="chiffrer"]');""", """  const t = fen.querySelector('[data-mess="tickets"]'); if(t) t.textContent = Number(MESS.tickets) || 0;
  const ra = fen.querySelector('[data-mess="ration"]'); if(ra) ra.innerHTML = messRationHtml();   // patch432
  const b = fen.querySelector('[data-mess="chiffrer"]');""")
# après un gain, la ration du jour se relit
rep(A, """    if(g.energie) { try{ majEnergie(); }catch(e){} }""", """    if(g.energie || g.lingots) { try{ majEnergie(); }catch(e){} messRationAjouter(g); }   // patch432""")
rep(A, """  messRecRendre(fen, v, !!(v && !v.en_cours));""",
"""  if(v && !v.en_cours && v.gain && (v.gain.energie || v.gain.lingots)){ try{ majEnergie(); }catch(e){} messRationAjouter(v.gain); }   // patch432
  messRecRendre(fen, v, !!(v && !v.en_cours));""")

# Règles
rep(H, """Les tickets ne s'achètent pas et les jeux n'en rendent jamais.</p><!-- patch429, patch430 -->""",
"""Des lots donnent de l'<b>énergie</b> et des <b>lingots</b> : <b>25 énergies et 6 lingots par jour</b> au plus venant du Mess (au-delà, ou au plafond, 10 TP par énergie et 15 TP par lingot). Les tickets ne s'achètent pas et les jeux n'en rendent jamais.</p><!-- patch429, patch430, patch432 -->""")

open(A, 'a', encoding='utf-8').write(r"""
// ---------- patch432 : la ration du Mess (s3-12) ----------
function messRationHtml(){
  const r = MESS && MESS.ration;
  if(!r) return '';
  const e = Number(r.energie_jour) || 0, l = Number(r.lingots_jour) || 0, E = Number(r.energie) || 25, L = Number(r.lingots) || 6;
  const barre = (n, m) => `<i class="mess-ra-barre"><b style="width:${Math.min(100, Math.round(n / m * 100))}%"></b></i>`;
  return `<div class="mess-ration"><span class="mess-ra-t">Ration du jour</span>
    <span class="mess-ra-l">⚡ <b>${e}</b> / ${E} ${barre(e, E)}</span>
    <span class="mess-ra-l">Lingots <b>${l}</b> / ${L} ${barre(l, L)}</span>
    <small>Au-delà, ${Number(r.tp_par_energie) || 10} TP par énergie et ${Number(r.tp_par_lingot) || 15} TP par lingot.</small></div>`;
}
function messRationAjouter(g){
  if(!MESS || !MESS.ration || !g) return;
  MESS.ration.energie_jour = (Number(MESS.ration.energie_jour) || 0) + (Number(g.energie) || 0);
  MESS.ration.lingots_jour = (Number(MESS.ration.lingots_jour) || 0) + (Number(g.lingots) || 0);
  if(messFen) messFenMaj();
}
""")

open(S, 'a', encoding='utf-8').write("""
/* patch432 : la ration du Mess */
.mess-ration{ display:grid; grid-template-columns:1fr 1fr; gap:6px 12px; align-items:center; border-radius:12px; background:#121a28; border:1px solid rgba(240,180,41,.25); padding:10px 12px; font-size:13px; }
.mess-ra-t{ grid-column:1 / -1; font:800 15px var(--titre); text-transform:uppercase; letter-spacing:.05em; color:var(--c-legendaire); }
.mess-ra-l{ display:flex; flex-wrap:wrap; align-items:center; gap:4px 6px; color:var(--brume); }
.mess-ra-l b{ color:#fff; font-family:var(--titre); font-size:16px; }
.mess-ra-barre{ display:block; width:100%; height:6px; border-radius:4px; background:#1f2a3d; overflow:hidden; }
.mess-ra-barre b{ display:block; height:100%; background:linear-gradient(90deg,#22A06B,#F0B429); }
.mess-ration small{ grid-column:1 / -1; color:var(--brume); font-size:11.5px; }
""")
print('patch432 OK')
