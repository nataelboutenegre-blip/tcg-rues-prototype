// TerraFront · la carte en direct : l'impact d'une bombe (patch378, s2-120).
// Aperçu validé par Nataël le 5/11 (« c'est parfait ! »), demandé le 8/11.
// Une bombe arrive dans le fil : la carte zoome sur la zone, viseur, flash plein écran,
// trois ondes de choc, l'écran tremble, les garnisons soufflées éclatent, un carton
// « 💥 BOMBE SUR … » ; au bout de ~6 s, retour à la vue d'ensemble. Le cercle reste
// pendant les 24 h de la zone. ?bombe=demo dans l'adresse : une démonstration au chargement.
// S'appuie sur direct.js (chargé avant) : D, VU, W, H, DPR, K_MAX, ECH, px, py, canvas,
// toutPeindre, geste, borner, esc, sb ; et sur recherche.js s'il est là (TikTok), qui attend la fin.
'use strict';
(function(){
  const carte = document.querySelector('.carte'), scene = document.getElementById('scene');
  if(!carte || !scene) return;
  const fx = document.createElement('canvas');
  fx.className = 'bombe-fx'; fx.width = W * DPR; fx.height = H * DPR; fx.setAttribute('aria-hidden', 'true');
  carte.insertBefore(fx, document.getElementById('eclairs'));
  const fxc = fx.getContext('2d');
  const flash = document.createElement('div'); flash.className = 'bombe-flash'; scene.append(flash);
  const carton = document.createElement('div'); carton.className = 'bombe-carton'; carton.setAttribute('aria-live', 'polite'); scene.append(carton);

  // [id, code, nom, dept, lat, lon, rayon, garnisons, forteresses, communes, lanceur, le, fin, touchees[]]
  let ZONES = [];
  let A = null;
  const file = [];
  const DEMO = new URLSearchParams(location.search).get('bombe') === 'demo';
  async function chargerZones(){
    try{
      const { data, error } = await sb.rpc('direct_bombes');
      if(!error && Array.isArray(data)) ZONES = data;
    }catch(e){}
  }
  const rayonBase = (km) => km / 111.19 * ECH;   // en pixels de la carte de base

  // le cercle des zones encore actives, dessiné avec la carte
  function zonesDessiner(){
    const maintenant = Date.now() / 1000;
    ctx.save();
    poserVue();
    for(const z of ZONES){
      if(z[12] < maintenant || z[4] == null) continue;
      if(A && A.cache && A.z[0] === z[0]) continue;   // l'animation la dessine
      const x = px(z[5]), y = py(z[4]), r = rayonBase(z[6]);
      ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(229,72,77,0.16)'; ctx.fill();
      ctx.setLineDash([8 / VU.k, 5 / VU.k]); ctx.strokeStyle = 'rgba(255,90,82,0.95)'; ctx.lineWidth = 2.2 / VU.k; ctx.stroke(); ctx.setLineDash([]);
      const f = 15 / VU.k, txt = '💥 +15 % · ' + (z[2] || '');
      ctx.font = '600 ' + f + 'px "Instrument Sans", system-ui, sans-serif';
      const w = ctx.measureText(txt).width + f * 1.2, h = f * 1.7, ty = y - r - 6 / VU.k - h;
      ctx.fillStyle = 'rgba(229,72,77,0.92)'; ctx.beginPath();
      if(ctx.roundRect) ctx.roundRect(x - w / 2, ty, w, h, h / 2); else ctx.rect(x - w / 2, ty, w, h);
      ctx.fill();
      ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(txt, x, ty + h / 2 + f * 0.05);
    }
    ctx.restore();
  }
  const peindre0 = window.toutPeindre;
  window.toutPeindre = function(){ peindre0(); zonesDessiner(); };

  // ---------- l'animation ----------
  const ease = (t) => t < 0 ? 0 : t > 1 ? 1 : 1 - Math.pow(1 - t, 3);
  const easeIO = (t) => t < 0 ? 0 : t > 1 ? 1 : t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  const borne = (t) => Math.max(0, Math.min(1, t));
  const lerp = (a, b, t) => a + (b - a) * t;
  const nbFr = (n) => Number(n || 0).toLocaleString('fr-FR');

  function jouer(z){
    if(z[4] == null) return;
    const x = px(z[5]), y = py(z[4]), r = rayonBase(z[6]);
    const kf = Math.max(1, Math.min(K_MAX, 0.78 * Math.min(W, H) / (2 * r)));
    const fin = { k: kf, x: W / 2 - x * kf, y: H / 2 - y * kf };
    const touchees = (z[13] || []).map((c) => { const k = D.cat && D.cat.get(String(c)); return k && k[4] != null ? [px(k[5]), py(k[4])] : null; }).filter(Boolean);
    const g = Number(z[7]) || 0;
    carton.innerHTML = '<div class="gros">💥 BOMBE SUR ' + esc(String(z[2] || '').toUpperCase()) + '</div>'
      + '<div class="detail"><b>' + esc(z[10] || 'Un joueur') + '</b> · rayon <b>' + nbFr(z[6]) + ' km</b>'
      + (g ? ' · <b>' + nbFr(g) + ' garnison' + (g > 1 ? 's' : '') + '</b> soufflée' + (g > 1 ? 's' : '') : '')
      + ' · <b>+15 %</b> en attaque pendant 24 h</div>';
    A = { z, x, y, r, dep: { ...VU }, fin, touchees, t0: performance.now(), cache: true, paliers: [2.5, 5, 10, 20].filter((k) => k < kf * 0.85), retour: [], raf: 0 };
    window.BOMBE_EN_COURS = true;
    instantane = null; toutPeindre();
    A.raf = requestAnimationFrame(image);
  }
  function arreter(){
    if(!A) return;
    cancelAnimationFrame(A.raf);
    fxc.setTransform(1, 0, 0, 1, 0, 0); fxc.clearRect(0, 0, fx.width, fx.height);
    flash.style.opacity = 0; carton.classList.remove('vu');
    canvas.style.transform = ''; fx.style.transform = '';
    A = null; window.BOMBE_EN_COURS = false;
    VU.k = 1; VU.x = 0; VU.y = 0; instantane = null; toutPeindre();
  }
  function image(now){
    const a = A; if(!a) return;
    const t = (now - a.t0) / 1000;
    // la caméra : vers la zone (0,9 → 2,3 s) ; à 9 s, retour immédiat à la France (comme les fiches du direct)
    if(t < 9){
      const k = easeIO((t - .9) / 1.4);
      const c0 = [(W / 2 - a.dep.x) / a.dep.k, (H / 2 - a.dep.y) / a.dep.k];
      const vk = a.dep.k * Math.pow(a.fin.k / a.dep.k, k);
      VU.k = vk; VU.x = W / 2 - lerp(c0[0], a.x, k) * vk; VU.y = H / 2 - lerp(c0[1], a.y, k) * vk;
      if(t > .9){
        if(k >= 1){ if(!a.net){ a.net = true; instantane = null; toutPeindre(); } }
        else if(a.paliers.length && vk >= a.paliers[0]){ a.paliers.shift(); instantane = null; toutPeindre(); }
        else geste();
      }
    } else if(!a.rentre){ a.rentre = true; VU.k = 1; VU.x = 0; VU.y = 0; instantane = null; toutPeindre(); }
    const ti = t - 2.5;
    flash.style.opacity = ti > 0 ? Math.max(0, .85 - ti / .6).toFixed(3) : 0;
    if(ti > .45 && t < 8.7) carton.classList.add('vu'); else carton.classList.remove('vu');
    const sh = ti > 0 && ti < .6 ? (1 - ti / .6) : 0;
    const dx = Math.sin(ti * 80) * 9 * sh, dy = Math.cos(ti * 63) * 6 * sh;
    canvas.style.transform = fx.style.transform = sh ? 'translate(' + dx.toFixed(2) + 'px,' + dy.toFixed(2) + 'px)' : '';
    const st = {
      viseur: borne((t - 1.9) / .6),
      flash: ti > 0 ? Math.max(0, 1 - ti / .6) : 0,
      ondes: [ti / 1.3, (ti - .25) / 1.3, (ti - .5) / 1.3],
      rouge: ti > 0 ? (ti < .25 ? ti / .25 : Math.max(.25, 1 - (ti - .25) / 2.2)) : 0,
      eclat: ti < .15 ? 0 : (ti - .15) / .8,
      zone: borne((ti - 1.4) / .6)
    };
    if(t > 9) st.rouge = .25 * Math.max(0, 1 - (t - 9) / 1);
    if(a.cache && ti > 2.0){ a.cache = false; if(!instantane) toutPeindre(); }   // le cercle passe sur la carte
    dessiner(a, st);
    if(t > 11){ arreter(); suivante(); return; }
    a.raf = requestAnimationFrame(image);
  }
  function dessiner(a, st){
    fxc.setTransform(1, 0, 0, 1, 0, 0); fxc.clearRect(0, 0, fx.width, fx.height);
    fxc.setTransform(DPR * VU.k, 0, 0, DPR * VU.k, DPR * VU.x, DPR * VU.y);
    const lw = 1 / VU.k, { x, y, r } = a;
    if(st.rouge > 0){
      const gr = fxc.createRadialGradient(x, y, 0, x, y, r);
      gr.addColorStop(0, 'rgba(255,70,60,' + (.75 * st.rouge).toFixed(3) + ')'); gr.addColorStop(1, 'rgba(255,70,60,' + (.75 * st.rouge * .65).toFixed(3) + ')');
      fxc.fillStyle = gr; fxc.beginPath(); fxc.arc(x, y, r, 0, Math.PI * 2); fxc.fill();
    }
    if(a.cache && st.zone > 0){
      fxc.globalAlpha = st.zone; fxc.beginPath(); fxc.arc(x, y, r, 0, Math.PI * 2);
      fxc.fillStyle = 'rgba(229,72,77,0.16)'; fxc.fill();
      fxc.setLineDash([8 * lw, 5 * lw]); fxc.strokeStyle = 'rgba(255,90,82,0.95)'; fxc.lineWidth = 2.2 * lw; fxc.stroke(); fxc.setLineDash([]);
      fxc.globalAlpha = 1;
    }
    // les garnisons soufflées (bouclier clair, sans « à moi » sur le direct)
    const tG = 10.5 * lw;
    for(const [gx, gy] of a.touchees){
      const e = st.eclat;
      const bouclier = (al, sc) => {
        fxc.save(); fxc.translate(gx, gy); fxc.scale(sc, sc); fxc.globalAlpha = al;
        fxc.beginPath(); fxc.moveTo(0, -tG); fxc.lineTo(tG * .85, -tG * .6); fxc.lineTo(tG * .7, tG * .35); fxc.lineTo(0, tG); fxc.lineTo(-tG * .7, tG * .35); fxc.lineTo(-tG * .85, -tG * .6); fxc.closePath();
        fxc.fillStyle = '#DCE6F2'; fxc.fill(); fxc.strokeStyle = '#07111F'; fxc.lineWidth = tG * .22; fxc.stroke();
        fxc.restore();
      };
      if(e <= 0) bouclier(1, 1);
      else if(e < 1){
        bouclier(1 - e, 1 + e * 1.2);
        for(let i = 0; i < 7; i++){
          const an = i / 7 * Math.PI * 2 + gx * 40, d = tG * (1 + e * 4.5);
          fxc.beginPath(); fxc.arc(gx + Math.cos(an) * d, gy + Math.sin(an) * d, tG * .22 * (1 - e), 0, Math.PI * 2);
          fxc.fillStyle = 'rgba(255,170,150,' + (1 - e) + ')'; fxc.fill();
        }
      }
    }
    for(const o of st.ondes){
      if(o <= 0 || o >= 1) continue;
      fxc.beginPath(); fxc.arc(x, y, r * ease(o) * 1.02, 0, Math.PI * 2);
      fxc.strokeStyle = 'rgba(255,' + Math.round(lerp(240, 90, o)) + ',' + Math.round(lerp(220, 80, o)) + ',' + (1 - o).toFixed(3) + ')';
      fxc.lineWidth = lerp(6, 1.5, o) * 1.6 * lw; fxc.stroke();
    }
    if(st.flash > 0){
      const gr = fxc.createRadialGradient(x, y, 0, x, y, r * .9);
      gr.addColorStop(0, 'rgba(255,255,255,' + st.flash + ')'); gr.addColorStop(.35, 'rgba(255,190,150,' + st.flash * .7 + ')'); gr.addColorStop(1, 'rgba(255,90,82,0)');
      fxc.fillStyle = gr; fxc.beginPath(); fxc.arc(x, y, r * .9, 0, Math.PI * 2); fxc.fill();
    }
    if(st.viseur > 0 && st.viseur < 1){
      const v = st.viseur, rr = r * lerp(1.6, .18, ease(v));
      fxc.save(); fxc.translate(x, y); fxc.rotate(v * 1.2);
      fxc.strokeStyle = 'rgba(255,90,82,' + Math.min(1, v * 3).toFixed(3) + ')'; fxc.lineWidth = 3 * lw;
      fxc.beginPath(); fxc.arc(0, 0, rr, 0, Math.PI * 2); fxc.stroke();
      for(let i = 0; i < 4; i++){ fxc.rotate(Math.PI / 2); fxc.beginPath(); fxc.moveTo(rr * .55, 0); fxc.lineTo(rr * 1.35, 0); fxc.stroke(); }
      fxc.restore();
    }
  }
  // une à la fois ; sur la page TikTok, on attend que la fiche de la commune soit partie
  function suivante(){
    if(A || !file.length) return;
    if(scene.classList.contains('recherche')){ setTimeout(suivante, 1000); return; }
    const id = file.shift();
    const z = ZONES.find((x) => String(x[0]) === id);
    if(z) jouer(z); else suivante();
  }
  // le fil (direct.js) appelle eclair() pour chaque nouvel événement
  const eclair0 = window.eclair;
  window.eclair = function(e){
    eclair0(e);
    if(!e || e[1] !== 'bombe') return;
    const id = String(e[0]).replace(/^b/, '');
    if(Date.now() / 1000 - e[2] > 300) return;   // trop vieille pour être jouée
    chargerZones().then(() => { if(!file.includes(id)) file.push(id); suivante(); });
  };
  chargerZones().then(() => toutPeindre());
  setInterval(() => chargerZones().then(() => { if(!A) toutPeindre(); }), 300000);   // une zone qui s'éteint au bout de 24 h

  // ?bombe=demo : une démonstration sur la commune la plus peuplée de Charente (aucune donnée n'est écrite)
  if(DEMO){
    const essai = () => {
      if(!D.cat || !D.chemins.size){ setTimeout(essai, 1000); return; }
      let m = null;
      for(const [c, r] of D.cat) if(r[2] === '16' && r[4] != null && (!m || (r[3] || 0) > (m[1][3] || 0))) m = [c, r];
      if(!m) return;
      const proches = [...D.cat].filter(([c, r]) => r[4] != null && Math.hypot((r[4] - m[1][4]) * 111, (r[5] - m[1][5]) * 78) < 13 && D.proprio.get(c)).slice(0, 4).map(([c]) => c);
      const z = [0, m[0], m[1][1], '16', m[1][4], m[1][5], 15, proches.length, 0, 0, 'Démonstration', Date.now() / 1000, Date.now() / 1000 + 600, proches];
      ZONES = ZONES.filter((x) => x[0] !== 0).concat([z]);
      jouer(z);
    };
    setTimeout(essai, 2500);
  }
})();
