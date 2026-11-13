# patch429 (13/11/2026) : Le Mess, l'espace de jeux de l'Arcade (saison 3), premier jeu : la Machine à chiffrer (va avec s3-10).
#  - carte « Le Mess » en haut du QG (tickets, « Entrer ») ;
#  - fenêtre du Mess : scène en pixel art façon Balatro, 3 rotors animés, résultat, table des lots ;
#  - tirage au serveur (mess_chiffrer) ; titre « As du Mess » ; paragraphe des Règles.
# Éteint jusqu'au 22/11 : visible si config 'mess'.actif = 1, ou avec « ?mess=test » pour un modérateur (Nataël).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, S, H = 'app.js', 'style.css', 'index.html'
if 'patch429' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

# chargement : avec l'énergie au démarrage, et à chaque ouverture du QG
rep(A, """  if(!sgLu) sgChargerActif();   // patch405 : le siège est-il allumé ?
""", """  if(!sgLu) sgChargerActif();   // patch405 : le siège est-il allumé ?
  if(!messLu) messCharger();   // patch429 : le Mess
""")
rep(A, """    if(tab.dataset.tab === 'combat' && SAISON2) majEnergie();
""", """    if(tab.dataset.tab === 'combat' && SAISON2) majEnergie();
    if(tab.dataset.tab === 'qg') messCharger();   // patch429
""")

# Règles : le Mess (caché jusqu'à l'allumage)
rep(H, """5 par jour.</p>""", """5 par jour.</p>
            <p data-s3="mess"><b>Le Mess</b> (dans le QG) : chaque duel classé te donne des tickets, <b>3</b> si tu gagnes, <b>2</b> en cas d'égalité, <b>1</b> si tu perds (30 par jour au plus, 2 duels par jour contre le même adversaire). Pas de tickets en défi amical. À la <b>Machine à chiffrer</b>, un ticket fait tourner 3 rotors : 3 symboles identiques donnent le lot du symbole (TP, paquet Terra, énergie, et le titre « As du Mess » pour 3 couronnes), 2 couronnes 25 TP, une autre paire 10 TP. Chaque symbole a la même chance sur chaque rotor. Les tickets ne s'achètent pas et la machine n'en rend jamais.</p><!-- patch429 -->""")

open(A, 'a', encoding='utf-8').write(r"""
// ---------- patch429 : Le Mess (saison 3, s3-10) ----------
// Allumé par le serveur (config 'mess'.actif) ; « ?mess=test » le montre à un modérateur avant le 22/11.
TITRES['mess-as'] = 'As du Mess';
var MESS = null, messLu = false, messFen = null;
const MESS_TEST = (() => {
  try{
    if(/[?&]mess=test\b/.test(location.search)) sessionStorage.setItem('tf-mess-test', '1');
    return sessionStorage.getItem('tf-mess-test') === '1';
  }catch(e){ return false; }
})();
const MESS_ORDRE = ['couronne', 'bombe', 'forteresse', 'fonderie', 'lingot', 'blason'];
const MESS_PAL = { k: '#1b1f2a', o: '#F0B429', y: '#ffd76a', r: '#E5484D', g: '#7E8BA0', w: '#EEF2F6', b: '#2F7CF6', n: '#3a4456', f: '#ff8a3d', s: '#5b6577' };
const MESS_SP = {
  couronne: ['............', '.o...o...o..', '.oo.ooo.oo..', '.oooyoooooo.', '.ooyyoyyooo.', '.ooooooooo..', '.rorrorrorr.', '.oooooooooo.', '.kkkkkkkkkk.', '............', '............', '............'],
  bombe: ['.......f....', '......fy....', '.....k......', '....kk......', '..kkkkkk....', '.kksskkkk...', '.ksskkkkk...', '.kskkkkkk...', '.kkkkkkkk...', '..kkkkkk....', '...kkkk.....', '............'],
  forteresse: ['............', '.s.s....s.s.', '.ssss..ssss.', '.gsgs..gsgs.', '.gggg..gggg.', '.gggggggggg.', '.ggg.gg.ggg.', '.gggggggggg.', '.gggkkkkggg.', '.gggkkkkggg.', '.gggkkkkggg.', '............'],
  fonderie: ['........ss..', '.......ss...', '.......nn...', '.......nn...', '.nn....nn...', '.nnnnnnnnnn.', '.nfnnfnnfnn.', '.nnnnnnnnnn.', '.nnnnnnnnnn.', '.nnkknnkknn.', '.nnkknnkknn.', '............'],
  lingot: ['............', '............', '............', '....oooo....', '...oyyyyo...', '..oyyyyyoo..', '.ooooooooo..', '.oyoooooooo.', '.ooooooooo..', '............', '............', '............'],
  blason: ['............', '.bbbbbbbbbb.', '.bwwbbbwwbb.', '.bwbbbbbwbb.', '.bbbbybbbbb.', '.bbbyyybbbb.', '.bbbbybbbbb.', '..bbbbbbbb..', '...bbbbbb...', '....bbbb....', '.....bb.....', '............'],
};
const messSpCache = {};
function messSpriteUrl(nom){
  if(messSpCache[nom]) return messSpCache[nom];
  const c = document.createElement('canvas'); c.width = 12; c.height = 12;
  const x = c.getContext('2d');
  (MESS_SP[nom] || []).forEach((row, j) => [...row].forEach((ch, i) => { const col = MESS_PAL[ch]; if(col){ x.fillStyle = col; x.fillRect(i, j, 1, 1); } }));
  return (messSpCache[nom] = c.toDataURL());
}
const messSp = (nom, cls) => `<img class="${cls || 'mess-sp'}" src="${messSpriteUrl(nom)}" alt="${nom}" draggable="false">`;
function messVisible(){ return !!(MESS && (MESS.actif || (MESS_TEST && MESS.ouvert))); }
async function messCharger(){
  messLu = true;
  try{
    const { data, error } = await sb.rpc('mess_etat');
    MESS = !error && data ? data : null;
  }catch(e){ MESS = null; }
  document.body.classList.toggle('mess-on', messVisible());
  messCarteRendre();
  messFenMaj();
}
function messCarteRendre(){
  const panneau = document.getElementById('panel-qg');
  if(!panneau) return;
  let c = document.getElementById('qgMess');
  if(!messVisible()){ if(c) c.hidden = true; return; }
  if(!c){
    c = document.createElement('div');
    c.className = 'qg-carte mess-carte';
    c.id = 'qgMess';
    const sub = panneau.querySelector(':scope > .sub');
    (sub || panneau.querySelector('h1')).insertAdjacentElement('afterend', c);
    c.addEventListener('click', (e) => { if(e.target.closest('[data-mess="entrer"]')) messOuvrir(); });
  }
  c.hidden = false;
  const R = MESS.regles || {}, n = Number(MESS.tickets) || 0;
  c.innerHTML = `<div class="qg-tete">
      <span class="qg-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="5" width="16" height="14" rx="2"/><path d="M8 5v14M12 5v14M16 5v14"/><path d="M2 12h2M20 12h2"/></svg></span>
      <div class="qg-titre"><h2>Le Mess</h2><p>L’arrière du front, où l’on joue entre deux batailles. Les tickets se gagnent en duel classé.</p></div>
    </div>
    <div class="qg-actions"><span class="mess-tk">🎟 <b>${n}</b> ticket${n > 1 ? 's' : ''}</span><button type="button" class="qg-btn plein" data-mess="entrer">Entrer</button>
      <span class="qg-petit">+${R.victoire || 3} par duel gagné, +${R.defaite || 1} perdu · aujourd’hui ${Number(MESS.jour) || 0} / ${R.par_jour || 30}</span></div>`;
}
function messLotTexte(id, l){
  if(!l) return '';
  const p = [];
  if(l.terra) p.push(`${l.terra} paquet${l.terra > 1 ? 's' : ''} Terra`);
  if(l.titre && !(MESS && MESS.as)) p.push('titre « As du Mess »');
  if(l.tp) p.push(`${l.tp} TP`);
  if(l.energie) p.push(`+${l.energie} énergie (1 fois par jour)`);
  return p.join(' + ');
}
function messTableHtml(){
  const L = (MESS && MESS.machine && MESS.machine.lots) || {};
  const ligne = (sy, t, or) => `<div class="mess-l"><span class="mess-sy">${sy}</span><span class="mess-lot${or ? ' or' : ''}">${t}</span></div>`;
  let h = '';
  for(const s of MESS_ORDRE) if(L[s]) h += ligne(messSp(s) + messSp(s) + messSp(s), messLotTexte(s, L[s]), !!L[s].terra);
  if(L.paire_couronne) h += ligne(messSp('couronne') + messSp('couronne') + '<i class="mess-vide"></i>', `Deux couronnes : ${L.paire_couronne.tp} TP`);
  if(L.paire) h += ligne(messSp('blason') + messSp('blason') + '<i class="mess-vide"></i>', `Une autre paire : ${L.paire.tp} TP`);
  return h;
}
function messOuvrir(){
  if(!messVisible()) return;
  const prix = (MESS.machine && MESS.machine.prix) || 1;
  const depart = [['blason', 'couronne', 'bombe'], ['fonderie', 'lingot', 'forteresse'], ['bombe', 'blason', 'couronne']];   // pas de triple au repos
  const fermer = ouvrirFenetre(`
    <div class="fenetre mess-fen" role="dialog" aria-modal="true" aria-label="Le Mess">
      <button type="button" class="mess-x" data-mess="fermer" aria-label="Fermer">&times;</button>
      <canvas class="mess-scene" width="195" height="92" aria-hidden="true"></canvas>
      <div class="mess-corps">
        <div class="mess-haut"><h2>Machine à chiffrer</h2><span class="mess-tk">🎟 <b data-mess="tickets">${Number(MESS.tickets) || 0}</b></span></div>
        <div class="mess-machine">
          <div class="mess-rotors">${depart.map(d => `<div class="mess-rotor"><div class="mess-bande">${d.map(s => messSp(s)).join('')}</div></div>`).join('')}</div>
          <div class="mess-ligne"></div>
        </div>
        <div class="mess-res" aria-live="polite"><span class="mess-attente">Aligne trois symboles sur la ligne rouge</span></div>
        <button type="button" class="mess-levier" data-mess="chiffrer">Chiffrer<small>· ${prix} ticket${prix > 1 ? 's' : ''}</small></button>
        <div class="mess-table"><h3>Les lots</h3>${messTableHtml()}</div>
        <p class="mess-note">Chaque symbole a la même chance sur chaque rotor : un triple tombe 1 fois sur 216. Les tickets ne s’achètent pas et la machine n’en rend jamais. Pas de lingots ici.</p>
      </div>
    </div>`, () => { messFen = null; });
  const fen = document.querySelector('#fenetre .mess-fen');
  messFen = fen;
  messScene(fen.querySelector('.mess-scene'));
  fen.addEventListener('click', (e) => {
    const b = e.target.closest('[data-mess]');
    if(!b) return;
    if(b.dataset.mess === 'fermer') fermer(null);
    if(b.dataset.mess === 'chiffrer') messChiffrer(fen);
  });
  messFenMaj();
}
function messFenMaj(){
  const fen = messFen;
  if(!fen || !fen.isConnected || !MESS) return;
  const t = fen.querySelector('[data-mess="tickets"]'); if(t) t.textContent = Number(MESS.tickets) || 0;
  const b = fen.querySelector('[data-mess="chiffrer"]');
  const prix = (MESS.machine && MESS.machine.prix) || 1;
  if(b && !fen.classList.contains('tourne')) b.disabled = (Number(MESS.tickets) || 0) < prix;
  if(b && !fen.classList.contains('tourne') && (Number(MESS.tickets) || 0) < prix){
    const r = fen.querySelector('.mess-res');
    if(r && r.querySelector('.mess-attente')) r.innerHTML = '<span class="mess-attente">Plus de tickets : gagne des duels classés au QG</span>';
  }
}
async function messChiffrer(fen){
  if(fen.classList.contains('tourne')) return;
  const bouton = fen.querySelector('[data-mess="chiffrer"]');
  fen.classList.add('tourne'); bouton.disabled = true;
  fen.querySelector('.mess-machine').classList.remove('gagne');
  fen.querySelectorAll('.mess-rotor').forEach(r => r.classList.remove('gagnant'));
  const res = fen.querySelector('.mess-res');
  res.innerHTML = '<span class="mess-attente">Chiffrement…</span>';
  let data;
  try{
    const r = await sb.rpc('mess_chiffrer');
    if(r.error) throw r.error;
    data = r.data;
  }catch(err){
    fen.classList.remove('tourne'); bouton.disabled = false;
    res.innerHTML = '';
    notifier({ type: 'erreur', titre: 'Le Mess', texte: messageLisible((err && err.message) || String(err)) });
    return;
  }
  MESS.tickets = Number(data.tickets) || 0;
  const t = fen.querySelector('[data-mess="tickets"]'); if(t) t.textContent = MESS.tickets;
  const rot = (data.rotors || []).map(String);
  const reduit = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fins = [...fen.querySelectorAll('.mess-rotor')].map((r, k) => new Promise(ok => {
    const bande = r.querySelector('.mess-bande');
    const pas = r.clientHeight / 3;
    const n = reduit ? 3 : 14 + k * 5;
    const suite = [];
    for(let i = 0; i < n; i++) suite.push(MESS_ORDRE[Math.floor(Math.random() * MESS_ORDRE.length)]);
    const iRes = MESS_ORDRE.indexOf(rot[k]);
    suite.push(MESS_ORDRE[(iRes + 5) % 6], rot[k], MESS_ORDRE[(iRes + 1) % 6]);
    const garder = [...bande.children].slice(0, 3).map(img => img.alt);
    bande.innerHTML = garder.concat(suite).map(s => messSp(s)).join('');
    const fin = -(suite.length) * pas;
    if(reduit){ bande.style.transform = `translateY(${fin}px)`; ok(); return; }
    const a = bande.animate([{ transform: 'translateY(0)', filter: 'blur(0)' }, { transform: `translateY(${fin * .55}px)`, filter: 'blur(1.5px)', offset: .5 }, { transform: `translateY(${fin}px)`, filter: 'blur(0)' }],
      { duration: 900 + k * 420, easing: 'cubic-bezier(.25,.6,.25,1)', fill: 'forwards' });
    a.onfinish = () => { bande.style.transform = `translateY(${fin}px)`; a.cancel(); ok(); };
  }));
  await Promise.all(fins);
  // la bande repart des trois symboles visibles, pour le tour suivant
  fen.querySelectorAll('.mess-rotor').forEach((r, k) => {
    const b = r.querySelector('.mess-bande'); const imgs = [...b.children].slice(-3).map(i => i.alt);
    b.style.transform = ''; b.innerHTML = imgs.map(s => messSp(s)).join('');
  });
  const g = data.gain || {};
  if(data.lot){
    const c = {}; rot.forEach(s => c[s] = (c[s] || 0) + 1);
    fen.querySelectorAll('.mess-rotor').forEach((r, k) => r.classList.toggle('gagnant', c[rot[k]] >= 2 && (data.lot !== 'paire_couronne' || rot[k] === 'couronne')));
    if(data.lot !== 'paire' && data.lot !== 'paire_couronne') fen.querySelector('.mess-machine').classList.add('gagne');
    const chips = [];
    if(g.terra) chips.push(`+${g.terra} paquet${g.terra > 1 ? 's' : ''} Terra`);
    if(g.titre) chips.push(`Titre « ${echapperTexte(TITRES[g.titre] || g.titre)} »`);
    if(g.energie) chips.push(`+${g.energie} énergie`);
    if(g.tp) chips.push(`+${g.tp} TP`);
    const grand = data.lot !== 'paire' && data.lot !== 'paire_couronne';
    res.innerHTML = `<span class="mess-titre${grand ? ' grand' : ''}">${grand ? 'Message déchiffré !' : echapperTexte(data.nom || 'Une paire')}</span>${chips.map(x => `<span class="mess-chip">${x}</span>`).join('')}`;
    if(g.tp || g.terra) { try{ loadPackStatus(); }catch(e){} }
    if(g.energie) { try{ majEnergie(); }catch(e){} }
    if(g.titre) notifier({ type: 'succes', titre: 'As du Mess', texte: 'Trois couronnes ! Le titre « As du Mess » est à toi : choisis-le dans ton profil.' });
  } else {
    res.innerHTML = '<span class="mess-titre brouille">Message brouillé</span>';
  }
  fen.classList.remove('tourne');
  bouton.disabled = false;
  messFenMaj();
  messCarteRendre();
}
// la scène du Mess en pixel art (195 × 92, agrandie sans lissage)
function messScene(sc){
  if(!sc || !sc.getContext) return;
  const g = sc.getContext('2d');
  const R = (c, x, y, w, h) => { g.fillStyle = c; g.fillRect(x, y, w, h); };
  for(let y = 0; y < 60; y++){ const t = y / 60; g.fillStyle = `rgb(${14 + t * 6},${24 + t * 10},${40 + t * 10})`; g.fillRect(0, y, 195, 1); }
  for(let x = 0; x < 195; x += 13) R('rgba(255,255,255,.025)', x, 0, 1, 60);
  const neon = '#F0B429';
  g.save(); g.shadowColor = neon; g.shadowBlur = 6;
  const LET = { L: ['1..', '1..', '1..', '1..', '111'], E: ['111', '1..', '11.', '1..', '111'], M: ['1...1', '11.11', '1.1.1', '1...1', '1...1'], S: ['111', '1..', '111', '..1', '111'] };
  let cx = 64;
  ['L', 'E', ' ', 'M', 'E', 'S', 'S'].forEach(ch => { if(ch === ' '){ cx += 4; return; } const m = LET[ch]; m.forEach((row, j) => [...row].forEach((v, i) => { if(v === '1') R(neon, cx + i * 2, 8 + j * 2, 2, 2); })); cx += m[0].length * 2 + 3; });
  g.restore();
  R('rgba(240,180,41,.25)', 60, 6, 74, 1); R('rgba(240,180,41,.25)', 60, 20, 74, 1);
  R('#2b3446', 10, 12, 34, 30); R('#e9e2cf', 12, 14, 30, 26);
  ['....11......', '...1111.....', '..1111111...', '.111111111..', '1111111111..', '.1111111111.', '..111111111.', '...1111111..', '....11111...', '.....111....']
    .forEach((row, j) => [...row].forEach((v, i) => { if(v === '1') R('#7E8BA0', 15 + i * 2, 16 + j * 2, 2, 2); }));
  R('#E5484D', 28, 22, 2, 2); R('#E5484D', 21, 30, 2, 2); R('#2F7CF6', 33, 27, 2, 2);
  R('#3a4456', 150, 0, 1, 12); R('#5b6577', 144, 12, 13, 4); R('#ffd76a', 147, 16, 7, 2);
  g.fillStyle = 'rgba(255,215,106,.07)'; g.beginPath(); g.moveTo(144, 18); g.lineTo(120, 60); g.lineTo(182, 60); g.lineTo(157, 18); g.fill();
  R('#0e3b2c', 0, 58, 195, 34); R('#145a40', 0, 58, 195, 3); R('#3b2a18', 0, 56, 195, 3);
  for(let x = 0; x < 195; x += 3) for(let y = 62; y < 92; y += 4) if((x + y) % 7 === 0) R('rgba(255,255,255,.035)', x, y, 1, 1);
  [[20, 72, '#E5484D'], [26, 74, '#2F7CF6'], [32, 72, '#F0B429']].forEach(([x, y, c]) => { for(let k = 0; k < 4; k++){ R(c, x, y - k * 2, 6, 2); R('rgba(255,255,255,.35)', x + 1, y - k * 2, 1, 1); } });
  [['#2F7CF6', 96], ['#9B5CF6', 104], ['#F0B429', 112]].forEach(([c, x], k) => { R('#0a0e15', x + 1, 66 + k, 12, 16); R('#EEF2F6', x, 65 + k, 12, 16); R(c, x + 1, 66 + k, 10, 4); R('#c9ced8', x + 2, 72 + k, 8, 1); R('#c9ced8', x + 2, 74 + k, 6, 1); });
  [[150, 74], [160, 78]].forEach(([x, y]) => { R('#F0B429', x, y, 9, 5); R('#9a6f0f', x + 3, y, 1, 5); });
  [[60, 76, 4], [68, 78, 2], [75, 75, 1]].forEach(([x, y, n]) => { R('#EEF2F6', x, y, 6, 6); R('#9aa3b2', x, y + 5, 6, 1); ({ 1: [[2, 2]], 2: [[1, 1], [3, 3]], 4: [[1, 1], [3, 1], [1, 3], [3, 3]] })[n].forEach(([a, b]) => R('#13233B', x + a, y + b, 2, 2)); });
  [[176, 40], [179, 34], [175, 28]].forEach(([x, y], k) => { g.fillStyle = `rgba(169,188,212,${.10 - k * .025})`; g.fillRect(x, y, 5, 4); });
  R('#e9e2cf', 172, 52, 8, 2); R('#f86b2b', 179, 52, 2, 2);
}
""")

open(S, 'a', encoding='utf-8').write("""
/* patch429 : Le Mess (saison 3) */
#panel-regles [data-s3="mess"]{ display:none !important; }
body.mess-on #panel-regles [data-s3="mess"]{ display:revert !important; }
.mess-carte{ border-color: rgba(240,180,41,.35); margin-bottom:16px; }
.mess-carte[hidden]{ display:none; }
.mess-tk{ display:inline-flex; align-items:center; gap:6px; background:rgba(240,180,41,.12); border:1px solid rgba(240,180,41,.4); color:var(--c-legendaire); border-radius:999px; padding:4px 10px; font-weight:600; font-size:13px; }
.mess-tk b{ font-family:var(--titre); font-size:17px; }
.fenetre.mess-fen{ padding:0; text-align:left; width:min(400px, 100%); max-height:calc(100vh - 24px); overflow:auto; border-color: rgba(240,180,41,.3); background:#0b1220; }
.mess-x{ position:absolute; top:8px; right:8px; z-index:2; width:32px; height:32px; border-radius:50%; border:0; background:rgba(5,12,24,.6); color:#fff; font-size:20px; line-height:1; cursor:pointer; }
.mess-scene{ display:block; width:100%; aspect-ratio:195/92; image-rendering:pixelated; image-rendering:crisp-edges; }
.mess-corps{ padding:14px; display:flex; flex-direction:column; gap:12px; background:linear-gradient(#0d1a2c,#0b1220); }
.mess-haut{ display:flex; justify-content:space-between; align-items:center; gap:10px; }
.mess-haut h2{ font-family:var(--titre); font-weight:900; font-size:26px; text-transform:uppercase; margin:0; letter-spacing:.03em; line-height:1; }
.mess-machine{ position:relative; border-radius:12px; padding:12px; background:#151b26; border:2px solid #2b3446; box-shadow:inset 0 0 0 2px #0a0e15; }
.mess-rotors{ display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }
.mess-rotor{ position:relative; height:120px; border-radius:8px; background:#e9e2cf; overflow:hidden; box-shadow:inset 0 6px 10px rgba(0,0,0,.45), inset 0 -6px 10px rgba(0,0,0,.45); transition: box-shadow .2s; }
.mess-bande{ display:flex; flex-direction:column; align-items:center; will-change:transform; }
.mess-bande .mess-sp{ width:40px; height:40px; flex:none; image-rendering:pixelated; }
.mess-rotor::before, .mess-rotor::after{ content:''; position:absolute; left:0; right:0; height:40px; z-index:1; pointer-events:none; }
.mess-rotor::before{ top:0; background:linear-gradient(rgba(233,226,207,.55), rgba(233,226,207,.15)); }
.mess-rotor::after{ bottom:0; background:linear-gradient(rgba(233,226,207,.15), rgba(233,226,207,.55)); }
.mess-ligne{ position:absolute; left:6px; right:6px; top:50%; height:2px; margin-top:-1px; background:rgba(229,72,77,.85); z-index:2; }
.mess-rotor.gagnant{ box-shadow:inset 0 6px 10px rgba(0,0,0,.45), inset 0 -6px 10px rgba(0,0,0,.45), 0 0 0 2px var(--c-legendaire); }
.mess-machine.gagne .mess-rotor{ box-shadow:inset 0 6px 10px rgba(0,0,0,.45), inset 0 -6px 10px rgba(0,0,0,.45), 0 0 0 2px var(--c-legendaire), 0 0 18px rgba(240,180,41,.55); }
.mess-res{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; justify-content:center; min-height:34px; text-align:center; }
.mess-titre{ font:800 22px var(--titre); text-transform:uppercase; letter-spacing:.04em; color:var(--c-legendaire); }
.mess-titre.grand{ font-size:24px; animation: messPop .5s cubic-bezier(.2,.8,.3,1.4); }
.mess-titre.brouille{ color:var(--brume); font-size:19px; }
.mess-attente{ color:var(--brume); font-size:13px; }
.mess-chip{ font:600 13px var(--texte); color:#fff; background:rgba(240,180,41,.15); border:1px solid rgba(240,180,41,.45); border-radius:999px; padding:3px 10px; }
@keyframes messPop{ from{ transform:scale(.6); opacity:0; } to{ transform:none; opacity:1; } }
.mess-levier{ width:100%; font:800 20px var(--titre); letter-spacing:.06em; text-transform:uppercase; padding:12px; border-radius:10px; border:0; background:var(--c-legendaire); color:#2a1d00; box-shadow:0 4px 0 #9a6f0f; cursor:pointer; }
.mess-levier small{ font:600 13px var(--texte); letter-spacing:0; text-transform:none; opacity:.8; margin-left:6px; }
.mess-levier:active:not(:disabled){ transform:translateY(3px); box-shadow:0 1px 0 #9a6f0f; }
.mess-levier:disabled{ opacity:.5; cursor:default; }
.mess-table{ border-radius:12px; background:#121a28; border:1px solid rgba(169,188,212,.14); padding:10px 12px; }
.mess-table h3{ margin:0 0 6px; font:800 15px var(--titre); text-transform:uppercase; letter-spacing:.05em; color:var(--brume); }
.mess-l{ display:flex; align-items:center; gap:8px; padding:5px 0; border-top:1px solid rgba(169,188,212,.08); font-size:13px; }
.mess-table h3 + .mess-l{ border-top:0; }
.mess-sy{ display:flex; gap:2px; flex:none; }
.mess-sy .mess-sp, .mess-vide{ width:22px; height:22px; image-rendering:pixelated; background:#e9e2cf; border-radius:4px; padding:2px; box-sizing:border-box; }
.mess-vide{ background:none; border:1px dashed #3a4456; display:inline-block; }
.mess-lot{ margin-left:auto; font-weight:600; color:#fff; text-align:right; }
.mess-lot.or{ color:var(--c-legendaire); }
.mess-note{ font-size:11.5px; color:var(--brume); line-height:1.45; margin:0; }
""")
print('patch429 OK')
