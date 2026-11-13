# patch430 (13/11/2026) : Le Mess, deuxième jeu : le Recensement (va avec s3-11). « Parfait oui ! » à l'aperçu.
#  - la fenêtre du Mess a deux onglets : « Machine à chiffrer » et « Le Recensement » (le dernier choisi est retenu) ;
#  - le Recensement : registre du Préfet (populations visibles), ton registre (populations cachées jusqu'à la fin),
#    « Recenser » / « Clore », révélation, lots ; une partie laissée en cours reprend à la réouverture ;
#  - Règles : une phrase sur le Recensement.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, S, H = 'app.js', 'style.css', 'index.html'
if 'patch430' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')
if 'patch429' not in open(A, encoding='utf-8').read(): sys.exit('patch429 manquant')

# les onglets et le corps du Recensement dans la fenêtre du Mess
rep(A, """      <canvas class="mess-scene" width="195" height="92" aria-hidden="true"></canvas>
      <div class="mess-corps">""", """      <canvas class="mess-scene" width="195" height="92" aria-hidden="true"></canvas>
      <div class="mess-onglets" role="tablist" aria-label="Jeux du Mess"><button type="button" role="tab" data-mess-jeu="machine">Machine à chiffrer</button><button type="button" role="tab" data-mess-jeu="rec">Le Recensement</button></div><!-- patch430 -->
      <div class="mess-corps mess-rec" data-jeu="rec" hidden></div>
      <div class="mess-corps" data-jeu="machine">""")
rep(A, """    if(b.dataset.mess === 'chiffrer') messChiffrer(fen);
  });
  messFenMaj();""", """    if(b.dataset.mess === 'chiffrer') messChiffrer(fen);
    if(b.dataset.mess === 'rec-lancer') messRecAction(fen, 'mess_rec_lancer');   // patch430
    if(b.dataset.mess === 'rec-tirer') messRecAction(fen, 'mess_rec_tirer');
    if(b.dataset.mess === 'rec-clore') messRecAction(fen, 'mess_rec_clore');
  });
  fen.querySelector('.mess-onglets').addEventListener('click', (e) => { const o = e.target.closest('[data-mess-jeu]'); if(o) messOnglet(fen, o.dataset.messJeu); });
  messOnglet(fen, (() => { try{ return localStorage.getItem('tf-mess-jeu') === 'rec' ? 'rec' : 'machine'; }catch(e){ return 'machine'; } })());
  messFenMaj();""")

# Règles
rep(H, """Chaque symbole a la même chance sur chaque rotor. Les tickets ne s'achètent pas et la machine n'en rend jamais.</p><!-- patch429 -->""",
"""Chaque symbole a la même chance sur chaque rotor. Au <b>Recensement</b> (2 tickets), le Préfet recense d'abord ses communes et montre son total ; tu tires ensuite des communes dont tu vois le nom mais pas la population (de 3 000 à 60 000 habitants). Arrête-toi au-dessus du Préfet sans franchir <b>50 000</b> habitants : 50 TP, et un paquet Terra entre 47 500 et 50 000. Les tickets ne s'achètent pas et les jeux n'en rendent jamais.</p><!-- patch429, patch430 -->""")

open(A, 'a', encoding='utf-8').write(r"""
// ---------- patch430 : le Recensement (Mess, s3-11) ----------
const messNb = (n) => Number(n || 0).toLocaleString('fr-FR');
function messOnglet(fen, jeu){
  try{ localStorage.setItem('tf-mess-jeu', jeu); }catch(e){}
  fen.querySelectorAll('[data-mess-jeu]').forEach(b => { const on = b.dataset.messJeu === jeu; b.classList.toggle('on', on); b.setAttribute('aria-selected', String(on)); });
  fen.querySelectorAll('.mess-corps[data-jeu]').forEach(c => { c.hidden = c.dataset.jeu !== jeu; });
  const h2 = fen.querySelector('.mess-corps[data-jeu="machine"] .mess-haut h2');
  if(jeu === 'rec') messRecRendre(fen, MESS && MESS.rec, false);
}
function messRecRendre(fen, v, revele){
  const corps = fen.querySelector('.mess-corps[data-jeu="rec"]');
  if(!corps || !MESS) return;
  const R = MESS.recensement || {}, L = R.lots || {}, prix = R.prix || 2, plafond = R.plafond || 50000;
  const tk = Number(v && v.tickets != null ? v.tickets : MESS.tickets) || 0;
  const ligne = (x, cache, k) => `<div class="mess-ins${revele && !cache ? ' revele' : ''}"${revele ? ` style="animation-delay:${k * 160}ms"` : ''}><span>${echapperTexte(x.nom || '?')} <i>(${echapperTexte(x.dept || '')})</i></span><span class="mess-pop${cache ? ' cache' : ''}">${cache ? '? ? ?' : messNb(x.pop)}</span></div>`;
  let jeu = '', res = '', boutons = '';
  if(!v){
    jeu = `<div class="mess-reg prefet vide"><h3><span>Registre du Préfet</span><b>—</b></h3><p>Le Préfet attend ton ticket.</p></div>`;
    boutons = `<button type="button" class="mess-levier" data-mess="rec-lancer"${tk < prix ? ' disabled' : ''}>Jouer<small>· ${prix} tickets</small></button>`;
    if(tk < prix) res = '<span class="mess-attente">Plus assez de tickets : gagne des duels classés au QG</span>';
  } else {
    const fini = !v.en_cours;
    jeu = `<div class="mess-reg prefet"><h3><span>Registre du Préfet</span><b>${messNb(v.prefet_total)}</b></h3>${(v.prefet || []).map(x => ligne(x, false, 0)).join('')}</div>
      <div class="mess-reg"><h3><span>Ton registre</span><b>${fini ? messNb(v.joueur_total) : '? ? ?'}</b></h3>${(v.joueur || []).map((x, k) => ligne(x, !fini, k)).join('')}</div>`;
    if(!fini){
      res = `<span class="mess-attente">Dépasse ${messNb(v.prefet_total)} sans franchir ${messNb(plafond)} habitants.</span>`;
      boutons = `<div class="mess-boutons"><button type="button" class="mess-levier" data-mess="rec-tirer">Recenser</button><button type="button" class="mess-levier creux" data-mess="rec-clore">Clore</button></div>`;
    } else {
      const g = v.gain || {}, chips = [];
      if(g.terra) chips.push(`+${g.terra} paquet${g.terra > 1 ? 's' : ''} Terra`);
      if(g.tp) chips.push(`+${g.tp} TP`);
      const titre = { parfait: 'Recensement parfait !', gagne: 'Recensé !', perdu: 'Le Préfet l’emporte', depasse: 'Plafond dépassé' }[v.resultat] || '';
      const bon = v.resultat === 'parfait' || v.resultat === 'gagne';
      res = `<span class="mess-titre${bon ? ' grand' : ' brouille'}">${titre}</span>${chips.map(x => `<span class="mess-chip">${x}</span>`).join('')}`;
      boutons = `<button type="button" class="mess-levier" data-mess="rec-lancer"${tk < prix ? ' disabled' : ''}>Rejouer<small>· ${prix} tickets</small></button>`;
    }
  }
  corps.innerHTML = `<div class="mess-haut"><h2>Le Recensement</h2><span class="mess-tk">🎟 <b data-mess="tickets">${tk}</b></span></div>
    <div class="mess-cible">Plafond <b>${messNb(plafond)}</b> habitants</div>
    ${jeu}
    <div class="mess-res" aria-live="polite">${res}</div>
    ${boutons}
    <div class="mess-table"><h3>Les lots · ${prix} tickets</h3>
      <div class="mess-l"><span>Tu dépasses le Préfet sans franchir le plafond</span><span class="mess-lot">${(L.gagne && L.gagne.tp) || 50} TP</span></div>
      <div class="mess-l"><span>Recensement parfait (${messNb(R.parfait || 47500)} à ${messNb(plafond)})</span><span class="mess-lot or">${(L.parfait && L.parfait.terra) || 1} paquet Terra</span></div>
      <div class="mess-l"><span>Au-dessus du plafond, ou pas plus que le Préfet</span><span class="mess-lot gris">rien</span></div></div>
    <p class="mess-note">Des communes de 3 000 à 60 000 habitants. Tu vois leur nom, pas leur population : connaître la France aide.</p>`;
}
async function messRecAction(fen, rpc){
  if(fen.classList.contains('tourne')) return;
  fen.classList.add('tourne');
  fen.querySelectorAll('.mess-rec .mess-levier').forEach(b => b.disabled = true);
  let v = null;
  try{
    const r = await sb.rpc(rpc);
    if(r.error) throw r.error;
    v = r.data;
  }catch(err){
    fen.classList.remove('tourne');
    messRecRendre(fen, MESS.rec, false);
    notifier({ type: 'erreur', titre: 'Le Recensement', texte: messageLisible((err && err.message) || String(err)) });
    return;
  }
  fen.classList.remove('tourne');
  MESS.rec = v && v.en_cours ? v : null;
  MESS.tickets = Number(v && v.tickets) || 0;
  messRecRendre(fen, v, !!(v && !v.en_cours));
  if(v && !v.en_cours && v.gain && (v.gain.tp || v.gain.terra)){ try{ loadPackStatus(); }catch(e){} }
  const t = fen.querySelector('.mess-corps[data-jeu="machine"] [data-mess="tickets"]'); if(t) t.textContent = MESS.tickets;
  messCarteRendre();
}
""")

open(S, 'a', encoding='utf-8').write("""
/* patch430 : le Recensement */
.mess-onglets{ display:flex; gap:6px; padding:10px 14px 0; background:#0d1a2c; }
.mess-onglets button{ flex:1; font:800 14px var(--titre); text-transform:uppercase; letter-spacing:.05em; padding:8px 6px; border-radius:9px 9px 0 0; color:var(--brume); background:#111a29; border:1px solid rgba(169,188,212,.12); border-bottom:0; cursor:pointer; }
.mess-onglets button.on{ color:#2a1d00; background:var(--c-legendaire); border-color:var(--c-legendaire); }
.mess-corps[hidden]{ display:none; }
.mess-cible{ display:flex; justify-content:center; gap:8px; align-items:baseline; font-size:13px; color:var(--brume); }
.mess-cible b{ font:800 18px var(--titre); color:var(--c-legendaire); }
.mess-reg{ border-radius:12px; background:#e9e2cf; color:#1b1f2a; padding:10px 12px; box-shadow:inset 0 0 0 2px #cbbf9f; }
.mess-reg h3{ margin:0 0 4px; font:800 15px var(--titre); text-transform:uppercase; letter-spacing:.05em; display:flex; justify-content:space-between; align-items:baseline; color:#3a2f1a; }
.mess-reg h3 b{ font-size:19px; color:#1b1f2a; font-variant-numeric:tabular-nums; }
.mess-reg.prefet{ background:#cfd6e2; box-shadow:inset 0 0 0 2px #aab4c5; }
.mess-reg.prefet h3{ color:#1F3A60; }
.mess-reg.vide p{ margin:4px 0 2px; font-size:13px; color:#4a5568; }
.mess-ins{ display:flex; justify-content:space-between; align-items:center; gap:8px; padding:6px 0; border-top:1px dashed #b9ad8c; font-size:14px; }
.mess-reg h3 + .mess-ins{ border-top:0; }
.mess-ins i{ font-style:normal; color:#6b5f45; font-size:12px; margin-left:2px; }
.mess-pop{ font:800 18px var(--titre); font-variant-numeric:tabular-nums; flex:none; }
.mess-pop.cache{ letter-spacing:.15em; color:#9a8e70; }
.mess-ins.revele .mess-pop{ animation: messRevele .45s both cubic-bezier(.2,.8,.3,1.3); animation-delay:inherit; }
@keyframes messRevele{ from{ opacity:0; transform:translateY(-6px) scale(.8); } to{ opacity:1; transform:none; } }
.mess-boutons{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.mess-boutons .mess-levier{ font-size:17px; padding:11px 8px; }
.mess-levier.creux{ background:transparent; color:var(--c-legendaire); border:2px solid var(--c-legendaire); box-shadow:none; }
.mess-lot.gris{ color:var(--brume); }
.mess-rec .mess-lot{ white-space:nowrap; flex:none; }
""")
print('patch430 OK')
