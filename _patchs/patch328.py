# patch328 (3/11/2026) : la légende des icônes de la carte, sur téléphone et en détail
# Retours de Nataël :
#  1. « sur téléphone, il n'y a pas de légende sur les icônes » : les tailles
#     (commun → légendaire, Aurore) et les bâtiments étaient cachés sous 720 px,
#     du temps où la légende était posée SUR la carte. Sur téléphone elle est
#     maintenant SOUS la carte (.en-dessous) : on les remontre.
#  2. « quand on clique sur les icônes (sur pc et portable), ça donne l'info du
#     bâtiment, à quoi il sert » : Fonderie, Forteresse et Centre dévoilé
#     deviennent des boutons ; une bulle explique le bâtiment (mêmes chiffres
#     que les Règles du jeu). Un 2e appui, un clic ailleurs, Échap ou le
#     défilement la ferment.
# Aperçus validés : apercu-legende-telephone.png, apercu-bulles-batiments.png.
import pathlib

def patcher(nom, remplacements):
    F = pathlib.Path(nom)
    s = F.read_text(encoding='utf-8')
    for avant, apres, n in remplacements:
        c = s.count(avant)
        assert c == n, f'{nom} : {c} fois au lieu de {n} : {avant[:70]!r}'
        s = s.replace(avant, apres)
    F.write_text(s, encoding='utf-8')

patcher('app.js', [
    ("""      <div class="leg-tailles leg-batiments"><div><span class="leg-bt">${ICONE_FONDERIE}</span>Fonderie</div><div><span class="leg-bt">${ICONE_FORTERESSE}</span>Forteresse</div><div><span class="leg-bt leg-centre">${ICONE_CENTRE}</span>Centre dévoilé</div></div>` : ''}""",
     """      <div class="leg-tailles leg-batiments">${['fonderie', 'forteresse', 'centre'].map(k => `<button type="button" class="leg-bt-info${btBulleCle === k ? ' on' : ''}" data-bt-info="${k}" aria-expanded="${btBulleCle === k}"><span class="leg-bt${k === 'centre' ? ' leg-centre' : ''}">${k === 'fonderie' ? ICONE_FONDERIE : k === 'forteresse' ? ICONE_FORTERESSE : ICONE_CENTRE}</span><span class="leg-nom">${BT_INFO[k].titre}</span></button>`).join('')}</div>` : ''}   <!-- patch328 -->""", 1),
    ("""// ---------- patch324 : mesure de l'accueil (s2-86) ----------""",
     """// ---------- patch328 : la bulle d'un bâtiment de la légende ----------
var BT_INFO = {
  fonderie: { titre: 'Fonderie', role: 'Elle produit les lingots qui servent à construire tes bâtiments.',
    li: ['La 1re est <b>gratuite</b> : <b>10 lingots par jour</b>, 30 en réserve.', 'Une 2e coûte <b>30 lingots</b> : 10 de plus par jour, réserve jusqu’à 45.',
         'Si on prend sa commune, elle disparaît et le joueur pille <b>la moitié</b> de tes lingots (le quart si tu en as deux).'],
    pied: 'Se construit en 6 h sur une de tes communes.' },
  forteresse: { titre: 'Forteresse', role: 'Elle rend une de tes communes plus dure à prendre.',
    li: ['Coûte <b>20 lingots</b>, 3 au plus.', '<b>−15 %</b> aux chances de ceux qui l’attaquent.', '<b>+5 %</b> à tes attaques à moins de 20 km.',
         'Disparaît si on prend sa commune, ou sous une bombe.'],
    pied: 'Se construit en 6 h sur une de tes communes.' },
  centre: { titre: 'Centre dévoilé', role: 'Le centre de recherche d’un joueur qui prépare une bombe.',
    li: ['Il est secret, mais apparaît sur la carte après <b>48 h</b> de préparation, et reste visible 24 h après l’impact.',
         '<b>Le prendre fait perdre la bombe</b> à son propriétaire.',
         'La bombe détruit garnisons et forteresses de tout le monde dans sa zone (jusqu’à 20 km), et tout le monde y attaque à <b>+15 %</b> pendant 24 h.'],
    pied: 'Pour en construire un : 2 Fonderies et 40 lingots.' },
};
var btBulle = null, btBulleCle = null;
function btBulleCacher(){
  if(btBulle) btBulle.hidden = true;
  btBulleCle = null;
  document.querySelectorAll('.leg-bt-info.on').forEach(x => { x.classList.remove('on'); x.setAttribute('aria-expanded', 'false'); });
}
function btBulleMontrer(b){
  const k = b.dataset.btInfo, I = BT_INFO[k];
  if(!I) return;
  if(btBulleCle === k){ btBulleCacher(); return; }
  if(!btBulle){ btBulle = document.createElement('div'); btBulle.className = 'bt-bulle'; btBulle.setAttribute('role', 'dialog'); btBulle.hidden = true; document.body.appendChild(btBulle); }
  btBulleCacher();
  btBulleCle = k; b.classList.add('on'); b.setAttribute('aria-expanded', 'true');
  const ic = k === 'fonderie' ? ICONE_FONDERIE : k === 'forteresse' ? ICONE_FORTERESSE : ICONE_CENTRE;
  btBulle.setAttribute('aria-label', I.titre);
  btBulle.innerHTML = `<h4><span class="leg-bt${k === 'centre' ? ' leg-centre' : ''}">${ic}</span>${I.titre}</h4><p class="bt-role">${I.role}</p>
    <ul>${I.li.map(x => `<li>${x}</li>`).join('')}</ul><p class="bt-pied">${I.pied}</p>`;
  btBulle.hidden = false;
  const rb = b.getBoundingClientRect(), w = btBulle.offsetWidth, h = btBulle.offsetHeight;
  let x = rb.left, y = rb.bottom + 8;
  if(y + h > window.innerHeight - 8) y = rb.top - h - 8;
  x = Math.max(8, Math.min(x, window.innerWidth - w - 8));
  btBulle.style.left = x + 'px'; btBulle.style.top = Math.max(8, y) + 'px';
}
document.addEventListener('click', (e) => {
  const b = e.target.closest && e.target.closest('.leg-bt-info[data-bt-info]');
  if(b){ e.preventDefault(); btBulleMontrer(b); return; }
  if(btBulleCle && !(btBulle && btBulle.contains(e.target))) btBulleCacher();
}, true);
document.addEventListener('keydown', (e) => { if(e.key === 'Escape' && btBulleCle) btBulleCacher(); });
window.addEventListener('scroll', () => { if(btBulleCle) btBulleCacher(); }, true);

// ---------- patch324 : mesure de l'accueil (s2-86) ----------""", 1),
])

F = pathlib.Path('style.css')
s = F.read_text(encoding='utf-8')
if 'patch328' not in s:
    s = s.rstrip('\n') + """

/* patch328 : sous la carte (téléphone), la légende montre aussi les tailles et les bâtiments ; la bulle d'un bâtiment */
.map-legende.en-dessous .leg-tailles{ display:flex; }
.map-legende.en-dessous .leg-batiments{ flex-wrap:wrap; }
.leg-bt-info{ display:flex; align-items:center; gap:6px; padding:3px 6px 3px 3px; margin:0; border:0; border-radius:999px; background:none; color:inherit; font:inherit; cursor:pointer; }
.leg-bt-info .leg-nom{ text-decoration:underline dotted rgba(169,188,212,.6); text-underline-offset:3px; }
.leg-bt-info:hover, .leg-bt-info.on{ background:rgba(232,131,58,.16); color:#fff; }
.leg-bt-info:focus-visible{ outline:2px solid #E8833A; outline-offset:2px; }
.bt-bulle{ position:fixed; z-index:9000; width:260px; max-width:calc(100vw - 16px); box-sizing:border-box; padding:12px 14px; background:#0B1A33;
  border:1px solid rgba(232,131,58,.6); border-radius:12px; box-shadow:0 10px 24px rgba(0,0,0,.45); color:#EAF1F8; font-size:.8rem; line-height:1.4; text-align:left; }
.bt-bulle[hidden]{ display:none; }
.bt-bulle h4{ display:flex; align-items:center; gap:8px; margin:0 0 4px; font-size:.95rem; color:#FFB27A; }
.bt-bulle h4 .leg-bt{ margin:0; }
.bt-bulle .bt-role{ margin:0 0 8px; color:#fff; }
.bt-bulle ul{ margin:0; padding-left:16px; }
.bt-bulle li{ margin:3px 0; }
.bt-bulle li b{ color:#FFD9B8; }
.bt-bulle .bt-pied{ margin:8px 0 0; color:#A9BCD4; font-size:.72rem; }
"""
    F.write_text(s, encoding='utf-8')
print('patch328 appliqué')
