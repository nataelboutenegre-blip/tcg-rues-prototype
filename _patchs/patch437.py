# patch437 (15/11/2026) : la révélation des cartes mise en scène selon la rareté (étape 2 de la maquette du 15/11).
#  - rare, épique, légendaire : un temps de suspense avant de retourner (halo, tremblement, rayons, scène assombrie) ;
#  - au retournement : éclats, flash, nom de la rareté au-dessus de la carte, reflet qui traverse la carte ;
#    légendaire : secousse, pluie de paillettes, coup sourd ;
#  - peu commune : quelques étincelles. Commune, brillante, monument : comme avant.
#  - le déroulé du jeu ne change pas (pile, « Tout révéler », rangée, sons existants, annonces).
# Allumé avec l'habillage de la saison 3 (html.topo) ; config_jeu 'interface'.revelation = 0 l'éteint seul.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, S = 'app.js', 'style.css'
if 'patch437' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

rep(A, """    tension(tier){ if(!pret()) return;""", """    boum(v){ if(pret()) note(62, 0, 0.9, 'sine', 0.5 * (v || 1)); },   // patch437
    tension(tier){ if(!pret()) return;""")
rep(A, """function lancerRevelation(zone, scene, tries){""", """// ---------- patch437 : la révélation mise en scène selon la rareté ----------
const REV_COUL = { peucommun: '#2BD48B', rare: '#4D94FF', epique: '#B07CFF', legendaire: '#F0B429' };
const REV_NOM = { rare: 'Rare', epique: 'Épique', legendaire: 'Légendaire' };
function revActif(){ const h = document.documentElement.classList; return h.contains('topo') && !h.contains('sans-revelation') && ouvAnim && !REDUCED_MOTION; }
// les particules : une toile fixe au-dessus de la page, qui ne tourne que tant qu'il en reste
const revFx = (() => {
  let cv = null, ctx = null, parts = [], raf = 0, dpr = 1;
  const boucle = () => {
    raf = 0; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, cv.width, cv.height);
    const vivantes = [];
    for(const p of parts){
      p.vie -= 1 / 60; if(p.vie <= 0) continue;
      p.vy += p.g; p.vx *= p.fr; p.vy *= p.fr; p.x += p.vx; p.y += p.vy; p.r += p.vr;
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r); ctx.globalAlpha = Math.min(1, p.vie / p.fin); ctx.fillStyle = p.c;
      if(p.forme === 'eclat'){
        ctx.globalCompositeOperation = 'lighter'; const t = p.t * (.6 + .4 * Math.abs(Math.sin(p.vie * 14)));
        ctx.beginPath(); ctx.moveTo(0, -t * 2.6); ctx.lineTo(t * .45, 0); ctx.lineTo(0, t * 2.6); ctx.lineTo(-t * .45, 0); ctx.closePath(); ctx.fill();
        ctx.beginPath(); ctx.moveTo(-t * 2.6, 0); ctx.lineTo(0, t * .45); ctx.lineTo(t * 2.6, 0); ctx.lineTo(0, -t * .45); ctx.closePath(); ctx.fill();
      } else if(p.forme === 'feuille'){ ctx.scale(1, Math.cos(p.vie * 9 + p.t)); ctx.fillRect(-p.t, -p.t * .6, p.t * 2, p.t * 1.2); }
      else { ctx.globalCompositeOperation = 'lighter'; ctx.beginPath(); ctx.arc(0, 0, p.t, 0, 6.283); ctx.fill(); }
      ctx.restore(); vivantes.push(p);
    }
    parts = vivantes;
    if(parts.length) raf = requestAnimationFrame(boucle); else { cv.remove(); cv = null; }
  };
  return { emettre(x, y, n, o){
    if(!cv){ cv = document.createElement('canvas'); cv.className = 'rev-fx'; cv.setAttribute('aria-hidden', 'true'); document.body.appendChild(cv); ctx = cv.getContext('2d');
      dpr = Math.min(window.devicePixelRatio || 1, 2); cv.width = Math.round(innerWidth * dpr); cv.height = Math.round(innerHeight * dpr); }
    for(let i = 0; i < n; i++){
      const ang = (o.ang != null ? o.ang : Math.random() * 6.283) + (Math.random() - .5) * (o.ouv || 0), v = o.v * (.35 + Math.random() * .9), vie = o.vie * (.6 + Math.random() * .7);
      parts.push({ x: x + (Math.random() - .5) * (o.large || 0), y: y + (Math.random() - .5) * (o.haut || 0), vx: Math.cos(ang) * v, vy: Math.sin(ang) * v, g: o.g != null ? o.g : .08, fr: o.fr || .975,
        r: Math.random() * 6.283, vr: (Math.random() - .5) * (o.vr || .2), vie, fin: vie * .5, t: o.t * (.6 + Math.random() * .8), c: o.c[Math.floor(Math.random() * o.c.length)], forme: o.forme || 'point' });
    }
    if(!raf) raf = requestAnimationFrame(boucle);
  } };
})();
function revCentre(el){ const r = el.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height }; }
function revNettoyer(zone){
  zone.querySelectorAll('.rev-rayons, .rev-lueur, .rev-cri').forEach(e => e.remove());
  zone.querySelectorAll('.card.rev-aura, .card.rev-haut, .card.rev-tremble').forEach(c => c.classList.remove('rev-aura', 'rev-tremble', 'rev-haut'));
  const o = document.getElementById('revOmbre'); if(o) o.remove();
}
// avant de retourner une rare, une épique ou une légendaire : le suspense
async function revSuspens(slot, el, draw, sansSon){
  const t = draw.tier.id, rg = RANG_TIER[t], duree = { rare: 420, epique: 760, legendaire: 1250 }[t] || 0;
  if(!duree) return;
  el.style.setProperty('--rc', REV_COUL[t]); slot.style.setProperty('--rc', REV_COUL[t]);
  el.classList.add('rev-aura');
  const lueur = document.createElement('i'); lueur.className = 'rev-lueur'; slot.insertBefore(lueur, slot.firstChild);
  if(rg >= 3){
    el.classList.add('rev-tremble');
    const r = document.createElement('i'); r.className = 'rev-rayons' + (rg === 4 ? ' fort' : ''); slot.insertBefore(r, slot.firstChild);
  }
  if(rg === 4){
    const c = revCentre(el), o = document.createElement('div'); o.id = 'revOmbre'; o.setAttribute('aria-hidden', 'true');
    o.style.background = `radial-gradient(circle at ${Math.round(c.x)}px ${Math.round(c.y)}px, transparent 0, transparent ${Math.round(c.h * .62)}px, rgba(3,8,18,.82) ${Math.round(c.h * 1.6)}px)`;
    document.body.appendChild(o); requestAnimationFrame(() => o.classList.add('vu'));
  }
  if(!sansSon) sonsOuverture.tension(t);
  await attendreOuv(duree);
  el.classList.remove('rev-tremble');
}
// au retournement : éclats, flash, nom de la rareté, reflet
function revEclat(slot, el, draw){
  const t = draw.tier.id, rg = RANG_TIER[t];
  if(rg < 1) return;
  const c = revCentre(el), coul = REV_COUL[t];
  if(rg === 1){ revFx.emettre(c.x, c.y, 8, { v: 3.2, vie: .6, t: 1.6, c: [coul, '#fff'], g: .02 }); return; }
  const n = { rare: 26, epique: 46, legendaire: 90 }[t];
  revFx.emettre(c.x, c.y, n, { v: rg === 4 ? 9 : 6.5, vie: rg === 4 ? 1.5 : 1, t: 2.2, c: [coul, '#fff', '#FFE9A8'], forme: 'eclat', g: .05, fr: .96, large: c.w * .7, haut: c.h * .7 });
  revFx.emettre(c.x, c.y, n, { v: rg === 4 ? 12 : 8, vie: .8, t: 1.5, c: [coul, '#fff'], g: .03, fr: .95 });
  const f = document.createElement('div'); f.className = 'rev-flash'; f.setAttribute('aria-hidden', 'true');
  f.style.background = `radial-gradient(circle at ${Math.round(c.x)}px ${Math.round(c.y)}px, #fff, ${coul} ${Math.round(c.h * .7)}px, transparent ${Math.round(c.h * 1.5)}px)`;
  document.body.appendChild(f);
  f.animate([{ opacity: rg === 4 ? .8 : rg === 3 ? .42 : .2 }, { opacity: 0 }], { duration: rg === 4 ? 520 : 320, easing: 'ease-out' }).onfinish = () => f.remove();
  const cri = document.createElement('p'); cri.className = 'rev-cri'; cri.setAttribute('aria-hidden', 'true'); cri.textContent = REV_NOM[t]; slot.appendChild(cri);
  const cadre = el.querySelector('.carte-cadre');
  if(cadre && !cadre.querySelector('.rev-holo')) cadre.insertAdjacentHTML('beforeend', '<i class="rev-holo" aria-hidden="true"></i>');
  el.classList.add('rev-haut', 'rev-' + t);
  if(rg >= 3) sonsOuverture.boum(rg === 4 ? 1 : .55);
  if(rg === 4){
    const scene = slot.closest('.ouv-scene');
    if(scene) scene.animate([{ translate: '0 0' }, { translate: '-5px 3px' }, { translate: '4px -4px' }, { translate: '-3px 2px' }, { translate: '2px -1px' }, { translate: '0 0' }], { duration: 380 });
    setTimeout(() => revFx.emettre(c.x, c.y - c.h * .6, 40, { v: 3, vie: 2.2, t: 2.4, c: ['#F0B429', '#FFE9A8', '#fff'], forme: 'feuille', g: .05, fr: .99, large: c.w * 1.6, ang: Math.PI / 2, ouv: 2.4, vr: .4 }), 260);
    if(navigator.vibrate) try{ navigator.vibrate([30, 40, 60]); }catch(e){}
  }
}

function lancerRevelation(zone, scene, tries){""")
rep(A, """  const terminer = async () => {
    if(fini) return;
    fini = true;
    actions.hidden = true;
    await attendreOuv(250);""", """  const terminer = async () => {
    if(fini) return;
    fini = true;
    actions.hidden = true;
    await attendreOuv(250);
    revNettoyer(zone);   // patch437""")
rep(A, """    if(enCours){ versRangee(enCours.el); enCours = null; }
    const draw = pile.pop();
    const el = makeCardEl(draw, surCarteRetournee(draw));
    el.classList.add('ouv-scene-carte');
    slotCarte.appendChild(el);
    enCours = { draw, el };
    redessinerPile();
    sonsOuverture.retourne();
    requestAnimationFrame(() => requestAnimationFrame(async () => {
      el.click();                                  // retourne la carte et l'ajoute a la collection""", """    revNettoyer(zone);   // patch437 : la mise en scène de la carte d'avant s'efface
    if(enCours){ versRangee(enCours.el); enCours = null; }
    const draw = pile.pop();
    const el = makeCardEl(draw, surCarteRetournee(draw));
    el.classList.add('ouv-scene-carte');
    slotCarte.appendChild(el);
    enCours = { draw, el };
    const rev = revActif() && !draw.brillante;   // patch437
    const derniere = !pile.length;               // la dernière a déjà eu sa lueur et son son sur la pile
    redessinerPile();
    sonsOuverture.retourne();
    requestAnimationFrame(() => requestAnimationFrame(async () => {
      if(rev && RANG_TIER[draw.tier.id] >= 2) await revSuspens(slotCarte, el, draw, derniere);   // patch437
      el.click();                                  // retourne la carte et l'ajoute a la collection""")
rep(A, """      if(RANG_TIER[draw.tier.id] >= 2 || monumentsNoms.has(draw.code)) el.classList.add('ouv-eclat');
      if(draw.brillante) briFete(slotCarte, el, draw);   // patch269""", """      if(RANG_TIER[draw.tier.id] >= 2 || monumentsNoms.has(draw.code)) el.classList.add('ouv-eclat');
      if(rev) revEclat(slotCarte, el, draw);   // patch437
      if(draw.brillante) briFete(slotCarte, el, draw);   // patch269""")
rep(A, """    verrou = true;
    btnTout.hidden = true;
    if(enCours){ versRangee(enCours.el); enCours = null; }""", """    verrou = true;
    btnTout.hidden = true;
    revNettoyer(zone);   // patch437
    if(enCours){ versRangee(enCours.el); enCours = null; }""")
rep(A, """      document.documentElement.classList.toggle('sans-sachet', o.sachet !== undefined && o.sachet !== null && Number(o.sachet) === 0);   // patch436
""", """      document.documentElement.classList.toggle('sans-sachet', o.sachet !== undefined && o.sachet !== null && Number(o.sachet) === 0);   // patch436
      document.documentElement.classList.toggle('sans-revelation', o.revelation !== undefined && o.revelation !== null && Number(o.revelation) === 0);   // patch437
""")

open(S, 'a', encoding='utf-8').write("""
/* =====================================================================
   patch437 — la révélation mise en scène selon la rareté
   ===================================================================== */
html.topo:not(.sans-revelation) .ouv-scene{ padding-top:46px; }
.rev-fx{ position:fixed; inset:0; width:100%; height:100%; pointer-events:none; z-index:45; }
.rev-flash{ position:fixed; inset:0; pointer-events:none; z-index:44; opacity:0; }
#revOmbre{ position:fixed; inset:0; pointer-events:none; z-index:3; opacity:0; transition: opacity .5s; }
#revOmbre.vu{ opacity:1; }
.ouv-slot-carte .rev-lueur, .ouv-slot-carte .rev-rayons{ position:absolute; left:50%; top:50%; border-radius:50%; pointer-events:none; display:block; }
.ouv-slot-carte .rev-lueur{ width:440px; height:440px; margin:-220px 0 0 -220px; opacity:.7;
  background: radial-gradient(closest-side, color-mix(in srgb, var(--rc, #F0B429) 62%, transparent), transparent 68%); animation: revApparait .45s ease-out both; }
.ouv-slot-carte .rev-rayons{ width:680px; height:680px; margin:-340px 0 0 -340px; opacity:.3;
  background: repeating-conic-gradient(from 0deg, color-mix(in srgb, var(--rc, #F0B429) 55%, transparent) 0 5deg, transparent 5deg 15deg);
  -webkit-mask-image: radial-gradient(closest-side, #000 12%, rgba(0,0,0,.5) 34%, transparent 68%); mask-image: radial-gradient(closest-side, #000 12%, rgba(0,0,0,.5) 34%, transparent 68%);
  animation: revTourne 26s linear infinite, revApparait .5s ease-out both; }
.ouv-slot-carte .rev-rayons.fort{ opacity:.55; }
@keyframes revApparait{ from{ opacity:0; } }
@keyframes revTourne{ to{ transform: rotate(360deg); } }
.ouv-slot-carte .card{ z-index:1; }
.card.rev-aura{ filter: drop-shadow(0 0 12px var(--rc)) drop-shadow(0 0 30px var(--rc)); }
.card.rev-tremble{ animation: revTremble .09s linear infinite; }
@keyframes revTremble{ 0%{ translate:-1px 0; } 25%{ translate:1px -1px; } 50%{ translate:1px 1px; } 75%{ translate:-1px 1px; } 100%{ translate:-1px 0; } }
html .ouv-slot-carte p.rev-cri{ position:absolute; left:-90px; right:-90px; bottom: calc(100% + 4px); margin:0; z-index:2; text-align:center; white-space:nowrap; pointer-events:none;
  font-family:'Big Shoulders Display', Impact, sans-serif; font-weight:900; font-size:36px; line-height:1; letter-spacing:.05em; text-transform:uppercase;
  color: var(--rc, #F0B429); text-shadow: 0 0 22px color-mix(in srgb, var(--rc, #F0B429) 70%, transparent), 0 3px 0 rgba(0,0,0,.45);
  animation: revCri .6s cubic-bezier(.2,1.5,.4,1) both; }
@keyframes revCri{ from{ opacity:0; transform: scale(.55) translateY(14px); } }
.card .rev-holo{ position:absolute; inset:0; border-radius:14px; pointer-events:none; z-index:6; mix-blend-mode:hard-light; opacity:0; display:block;
  background: linear-gradient(112deg, transparent 30%, #9cc7ff 41%, #e2f1ff 47%, #9cc7ff 53%, transparent 64%) 0 0 / 320% 100%; }
.card.rev-epique .rev-holo{ background-image: linear-gradient(112deg, transparent 30%, #c59bff 41%, #7fd0ff 47%, #ff9ad8 53%, transparent 64%); }
.card.rev-legendaire .rev-holo{ background-image: linear-gradient(112deg, transparent 30%, #ffd76a 41%, #8fd3ff 47%, #ff9ad8 53%, transparent 64%); }
.card.rev-haut .rev-holo{ animation: revBalaye 1.2s ease-out .25s both; }
@keyframes revBalaye{ 0%{ opacity:0; background-position:0 0; } 20%{ opacity:.42; } 80%{ opacity:.42; } 100%{ opacity:0; background-position:100% 0; } }
@media (prefers-reduced-motion: reduce){ .card.rev-tremble, .ouv-slot-carte .rev-rayons, .card.rev-haut .rev-holo{ animation:none; } }
""")
print('patch437 OK')
