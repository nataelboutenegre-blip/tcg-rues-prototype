# patch436 (15/11/2026) : le paquet devient un sachet en aluminium (maquette validée par Nataël le 15/11).
#  - matière : soudures crantées fines, froissé, relief, plis, reflet qui suit le doigt (classe .alu) ;
#  - déchirure : la bandelette se décolle sous le doigt (une copie de la languette, masquée de part et d'autre
#    de la coupe), puis s'envole ; le trait de lumière et son indice de rareté restent ;
#  - tout le reste est inchangé (gestes, attente du serveur, sortie de la pile, habillages, Halloween).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, S = 'app.js', 'style.css'
if 'patch436' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

ALU = '<span class="alu" aria-hidden="true"><i class="alu-bosse"></i><i class="alu-relief"></i><i class="alu-plis"></i><i class="alu-plis bas"></i><i class="alu-soudure"></i><i class="alu-soudure bas"></i><i class="alu-froisse"></i><i class="alu-iris"></i><i class="alu-reflet"></i></span>'
rep(A, """    <div class="paquet-languette">${motif}</div>""", """    <div class="paquet-languette">${motif}${ALU_COUCHES}</div>""")
rep(A, """      <div class="paquet-bande">5 communes</div>
    </div>
    <div class="paquet-eclat"></div>""", """      <div class="paquet-bande">5 communes</div>${ALU_COUCHES}
    </div>
    <div class="paquet-eclat"></div>""")
rep(A, """  if(gl) setTimeout(() => habGl.demarrer(), 0);
  if(HW && HW.actif) hw2Paquet(pack);   // patch265 : le paquet maudit
  return pack;""", """  aluInstaller(pack);   // patch436 : le sachet en aluminium
  if(gl) setTimeout(() => habGl.demarrer(), 0);
  if(HW && HW.actif) hw2Paquet(pack);   // patch265 : le paquet maudit
  return pack;""")
rep(A, """// Paquet bleu pour le gratuit, dore pour celui achete
function makePackEl(type){""", """// ---------- patch436 : le sachet en aluminium ----------
// Des couches posées sur le motif (dans la languette et dans le corps, alignées comme lui), une copie de la
// languette qui se décolle derrière la coupe, et un reflet qui suit le doigt ou la souris.
const ALU_COUCHES = '""" + ALU + """';
function aluInstaller(pack){
  pack.classList.add('alu');
  const l = pack.querySelector('.paquet-languette');
  if(l){ const c = l.cloneNode(true); c.classList.add('pelee'); c.style.display = 'none'; l.insertAdjacentElement('afterend', c); }
  let dernier = 0;
  pack.addEventListener('pointermove', (e) => {
    const t = performance.now(); if(t - dernier < 24) return; dernier = t;
    const r = pack.getBoundingClientRect(); if(!r.width) return;
    pack.style.setProperty('--alu-x', (100 - Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * 100).toFixed(1) + '%');
    pack.classList.add('alu-suit');
  });
  pack.addEventListener('pointerleave', () => pack.classList.remove('alu-suit'));
}
// v de 0 à 1 : la languette reste à droite de la coupe, sa copie se soulève à gauche
function aluPeler(l, pl, v){
  if(v <= 0){ l.style.webkitMaskImage = l.style.maskImage = ''; pl.style.display = 'none'; return; }
  const x = (v * 200).toFixed(1) + 'px';
  const m1 = `linear-gradient(90deg, transparent ${x}, #000 ${x})`, m2 = `linear-gradient(90deg, #000 ${x}, transparent ${x})`;
  l.style.webkitMaskImage = m1; l.style.maskImage = m1; l.style.transform = '';
  pl.style.display = ''; pl.style.webkitMaskImage = m2; pl.style.maskImage = m2;
  pl.style.transformOrigin = `${x} 100%`; pl.style.transform = `rotate(${(-(5 + 27 * v)).toFixed(2)}deg)`;
}

// Paquet bleu pour le gratuit, dore pour celui achete
function makePackEl(type){""")
rep(A, """  const languette = q('.paquet-languette'), trace = q('.coupe-trace'), tete = q('.coupe-tete'), lueur = q('.coupe-lueur');""",
       """  const languette = q('.paquet-languette'), trace = q('.coupe-trace'), tete = q('.coupe-tete'), lueur = q('.coupe-lueur');
  const pelee = q('.paquet-languette.pelee');   // patch436""")
rep(A, """    languette.style.transform = v > 0 ? `rotate(${(-v * 4).toFixed(2)}deg)` : '';""",
       """    if(pelee) aluPeler(languette, pelee, v);   // patch436 : la bandelette se décolle derrière la coupe
    else languette.style.transform = v > 0 ? `rotate(${(-v * 4).toFixed(2)}deg)` : '';""")

dents_haut = ', '.join(f'{i * 2.5:g}% {0 if i % 2 else 3.4}px' for i in range(41))
dents_bas = ', '.join(f'{i * 2.5:g}% calc(100% - {0 if i % 2 else 3.4}px)' for i in range(40, -1, -1))
FROISSE = 'url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%27200%27 height=%27280%27%3E%3Cfilter id=%27f%27 x=%270%27 y=%270%27 width=%27100%25%27 height=%27100%25%27%3E%3CfeTurbulence type=%27fractalNoise%27 baseFrequency=%270.016 0.034%27 numOctaves=%274%27 seed=%2711%27 result=%27n%27/%3E%3CfeDiffuseLighting in=%27n%27 lighting-color=%27%23fff%27 surfaceScale=%276.5%27 diffuseConstant=%271.05%27%3E%3CfeDistantLight azimuth=%27225%27 elevation=%2760%27/%3E%3C/feDiffuseLighting%3E%3C/filter%3E%3Crect width=%27100%25%27 height=%27100%25%27 filter=%27url(%23f)%27/%3E%3C/svg%3E")'
CSS = """
/* =====================================================================
   patch436 — le paquet devient un sachet en aluminium
   ===================================================================== */
.paquet.alu .paquet-languette{ clip-path: polygon(""" + dents_haut + """, 100% 100%, 0 100%); }
.paquet.alu .paquet-corps{ clip-path: polygon(0 0, 100% 0, """ + dents_bas + """); }
.paquet.alu .paquet-corps::after{ display:none; }
.paquet .alu{ position:absolute; left:0; top:0; width:200px; height:280px; pointer-events:none; display:block; }
.paquet .paquet-corps > .alu{ top: calc(var(--h-languette) * -1); }
.paquet .alu > i{ position:absolute; inset:0; display:block; }
.paquet .alu-relief{ background:
  linear-gradient(90deg, rgba(0,0,0,.5), rgba(0,0,0,.12) 9%, rgba(255,255,255,.13) 24%, rgba(255,255,255,0) 44%, rgba(0,0,0,0) 72%, rgba(0,0,0,.2) 90%, rgba(0,0,0,.55)),
  linear-gradient(180deg, rgba(0,0,0,.32), rgba(0,0,0,0) 15%, rgba(0,0,0,0) 84%, rgba(0,0,0,.4)); }
.paquet .alu > i.alu-bosse{ inset:38px 11px 22px 11px; border-radius:13px;
  box-shadow: 0 0 0 1px rgba(255,255,255,.05), 0 0 16px 2px rgba(255,255,255,.07), inset 0 0 20px rgba(255,255,255,.06), inset 0 -9px 18px rgba(0,0,0,.14); }
.paquet .alu-froisse{ mix-blend-mode:overlay; opacity:.4; background: """ + FROISSE + """ 0 0 / 200px 280px; }
.paquet.hab .alu-froisse{ opacity:.3; }
.paquet .alu > i.alu-plis{ top:19px; bottom:auto; height:46px; opacity:.8;
  background: repeating-linear-gradient(90deg, rgba(255,255,255,.10) 0 2px, transparent 2px 9px, rgba(0,0,0,.14) 9px 11px, transparent 11px 19px, rgba(255,255,255,.06) 19px 20px, transparent 20px 31px);
  -webkit-mask-image: linear-gradient(180deg, #000, transparent); mask-image: linear-gradient(180deg, #000, transparent); }
.paquet .alu > i.alu-plis.bas{ top:auto; bottom:19px; -webkit-mask-image: linear-gradient(0deg, #000, transparent); mask-image: linear-gradient(0deg, #000, transparent); }
.paquet .alu > i.alu-soudure{ bottom:auto; height:19px;
  background: repeating-linear-gradient(90deg, rgba(255,255,255,.26) 0 1px, rgba(0,0,0,.3) 1px 2px, rgba(0,0,0,0) 2px 4px),
              linear-gradient(180deg, rgba(0,0,0,.34), rgba(255,255,255,.16) 46%, rgba(0,0,0,.3) 92%, rgba(255,255,255,.35) 96%, rgba(0,0,0,.45)); }
.paquet .alu > i.alu-soudure.bas{ top:auto; bottom:0; transform:scaleY(-1); }
.paquet.hab .alu-soudure{ opacity:.7; }
.paquet .alu-reflet{ mix-blend-mode:screen; opacity:.42;
  background: linear-gradient(112deg, transparent 34%, rgba(255,255,255,.06) 41%, rgba(255,255,255,.5) 48.5%, rgba(205,230,255,.22) 51.5%, rgba(255,255,255,.05) 58%, transparent 66%) 50% 0 / 260% 100%;
  animation: aluReflet 7s ease-in-out infinite alternate; }
.paquet .alu-iris{ mix-blend-mode:color-dodge; opacity:.08;
  background: linear-gradient(112deg, transparent 30%, #ff8ad4 40%, #ffd76a 46%, #7df3c3 52%, #6fb6ff 58%, transparent 68%) 50% 0 / 300% 100%;
  animation: aluReflet 7s ease-in-out infinite alternate-reverse; }
@keyframes aluReflet{ from{ background-position: 12% 0; } to{ background-position: 88% 0; } }
.paquet.alu-suit .alu-reflet{ animation:none; background-position: var(--alu-x, 50%) 0; }
.paquet.alu-suit .alu-iris{ animation:none; background-position: calc(100% - var(--alu-x, 50%)) 0; }
.paquet.alu .paquet-titre{ text-shadow: 0 1px 0 rgba(255,255,255,.3), 0 -1px 0 rgba(0,0,0,.4), 0 3px 0 rgba(4,12,28,.45), 0 9px 14px rgba(0,0,0,.4); }
.paquet.alu.hab .paquet-titre{ text-shadow: var(--hab-lueur, 0 0 0 transparent), 0 3px 0 rgba(0,0,0,.3), 0 9px 14px rgba(0,0,0,.4); }
.paquet.alu.achete:not(.hab) .paquet-titre, .paquet.alu.og .paquet-titre{ text-shadow: 0 1px 0 rgba(255,255,255,.5), 0 -1px 0 rgba(90,55,5,.3); }
.paquet.alu.gratuit:not(.hab):not(.og) .paquet-bande{ background: linear-gradient(180deg, #8A5A10, #F6D26B 14%, #FFF1B8 30%, #E9B43A 52%, #B67A16 78%, #F2CE66 92%, #7A4E0C);
  box-shadow: 0 2px 0 rgba(0,0,0,.35), 0 -1px 0 rgba(0,0,0,.3), inset 0 1px 0 rgba(255,255,255,.5); text-shadow: 0 1px 0 rgba(255,255,255,.45); }
/* la bandelette décollée : une copie de la languette, au-dessus du reste */
.paquet .paquet-languette.pelee{ z-index:2; pointer-events:none; transition:none; filter: drop-shadow(0 5px 4px rgba(0,0,0,.35)); }
.paquet.alu.coupee .paquet-languette:not(.pelee){ animation:none; visibility:hidden; }
.paquet.alu.coupee .paquet-languette.pelee{ animation: aluEnvol .9s cubic-bezier(.3,0,.75,1) forwards; }
@keyframes aluEnvol{ 0%{ transform: rotate(-32deg); opacity:1; } 32%{ transform: translate(40px,-56px) rotate(-70deg); opacity:1; } 100%{ transform: translate(110px,380px) rotate(-200deg); opacity:0; } }
.paquet.alu.dechire .paquet-languette.pelee, .paquet.alu.charge .paquet-languette.pelee{ display:none !important; }
@media (prefers-reduced-motion: reduce){ .paquet .alu-reflet, .paquet .alu-iris{ animation:none; } .paquet.alu.coupee .paquet-languette.pelee{ animation:none; opacity:0; } }
"""
open(S, 'a', encoding='utf-8').write(CSS)
print('patch436 OK')
