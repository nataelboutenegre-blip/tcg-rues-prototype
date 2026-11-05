// TerraFront · la commune demandée en live (s2-103), pour la scène portrait (tiktok.html).
// La régie (regie.html) choisit une commune ; ici on lit direct_affiche() toutes les 2 s :
// la carte zoome dessus (contour + cercle), une fiche remplace la colonne de droite, puis retour à la France.
// S'appuie sur direct.js (chargé avant) : D, VU, BOITES, cadrer, geste, toutPeindre, placerEclairs, px, py, esc, DEPT_NAMES.
'use strict';
(function(){
  const scene = document.getElementById('scene');
  const fiche = document.createElement('div');
  fiche.className = 'fiche'; fiche.hidden = true; fiche.setAttribute('aria-live', 'polite');
  scene.append(fiche);
  const BULLE = '<svg viewBox="0 0 24 24"><path d="M4 5h16v11H9l-5 4z"/><path d="M8 9.5h8M8 12.5h5"/></svg>';
  let dernierN = null, codeAffiche = null, finLocale = 0, total = 15000, raf = 0;

  // le contour de la commune affichée, redessiné après chaque dessin complet de la carte
  function contour(){
    if(!codeAffiche) return;
    const p = D.chemins.get(codeAffiche);
    if(!p) return;
    poserVue();
    ctx.lineJoin = 'round';
    ctx.lineWidth = 9 / VU.k; ctx.strokeStyle = 'rgba(10,22,40,.85)'; ctx.stroke(p);
    ctx.lineWidth = 4.5 / VU.k; ctx.strokeStyle = '#F0B429'; ctx.stroke(p);
  }
  const peindreTout = window.toutPeindre;
  window.toutPeindre = function(){ peindreTout(); contour(); };

  function compter(r, cl, jo){
    let nClan = 0, nLibres = 0, nDep = 0;
    for(const [c, x] of D.cat){
      if(x[2] !== r[2]) continue;
      nDep++;
      const o = D.proprio.get(c);
      if(!o) nLibres++;
      else if(cl){ const oj = D.joueurs.get(o); if(oj && oj.clan === jo.clan) nClan++; }
    }
    return { nClan, nLibres, nDep };
  }

  function remplir(code, demandeur){
    const r = D.cat.get(code);
    const j = D.proprio.get(code), jo = j ? D.joueurs.get(j) : null, cl = jo && jo.clan ? D.clans.get(jo.clan) : null;
    const dep = DEPT_NAMES[r[2]] || r[2], z = compter(r, cl, jo);
    const zone = j && cl
      ? '<div class="zone"><b>' + z.nClan.toLocaleString('fr-FR') + (z.nClan > 1 ? ' communes</b>tenues' : ' commune</b>tenue') + ' par [' + esc(cl.tag) + '] en ' + esc(dep) + '</div>'
      : '<div class="zone"><b>' + z.nLibres.toLocaleString('fr-FR') + (z.nLibres > 1 ? ' libres' : ' libre') + '</b>en ' + esc(dep) + ', sur ' + z.nDep.toLocaleString('fr-FR') + ' communes</div>';
    fiche.innerHTML = '<div class="qui">' + BULLE + (demandeur ? '<span>Demandée par <b>' + esc(demandeur) + '</b></span>' : '<span>Commune demandée</span>') + '</div>'
      + '<h3>' + esc(r[1]) + '</h3>'
      + '<div class="lieu"><b>' + esc(dep) + ' (' + esc(r[2]) + ')</b> · ' + Number(r[3] || 0).toLocaleString('fr-FR') + ' hab.</div>'
      + '<div class="sep"></div>'
      + (j
        ? '<div class="etat">Tenue par</div><div class="tenant"><i style="background:' + esc(cl ? cl.couleur : SEUL) + '"></i><b>' + esc(jo ? jo.pseudo : 'un joueur') + '</b></div>'
          + (cl ? '<div class="clan">Clan <em>[' + esc(cl.tag) + '] ' + esc(cl.nom) + '</em></div>' : '<div class="clan">Sans clan</div>')
          + zone + '<div class="appel">Tu la veux&nbsp;? <b>Attaque-la</b> sur terrafront.fr</div>'
        : '<div class="etat">Personne ne la tient</div><div class="libre">Libre&nbsp;!</div>'
          + zone + '<div class="appel"><b>Viens la prendre</b> gratuitement sur terrafront.fr</div>')
      + '<div class="temps"><i></i></div>';
  }

  function barre(){
    cancelAnimationFrame(raf);
    const i = fiche.querySelector('.temps i');
    const pas = () => {
      if(!codeAffiche || !i) return;
      const reste = Math.max(0, finLocale - Date.now());
      i.style.width = (100 * reste / total).toFixed(2) + '%';
      raf = requestAnimationFrame(pas);
    };
    pas();
  }

  function montrer(code, demandeur, reste){
    if(!D.cat || !D.cat.get(code)) return false;
    codeAffiche = code;
    remplir(code, demandeur);
    fiche.hidden = false; scene.classList.add('recherche');
    total = Math.max(1000, reste * 1000); finLocale = Date.now() + reste * 1000;
    const box = document.getElementById('eclairs');
    box.querySelectorAll('.repere').forEach((e) => e.remove());
    const b = BOITES.get(code), r = D.cat.get(code);
    if(b){
      // la commune au centre, avec ses voisines autour (le coin du clan se voit)
      const cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2, R = Math.max(75, (b[2] - b[0]) * 1.2, (b[3] - b[1]) * 1.2);
      const m = document.createElement('div'); m.className = 'repere';
      m.dataset.bx = px(r[5]); m.dataset.by = py(r[4]); box.append(m);
      cadrer(cx - R, cy - R, cx + R, cy + R);
    }else{
      // outre-mer : pas de contour sur cette carte, la fiche seule
      VU.k = 1; VU.x = 0; VU.y = 0; geste();
    }
    barre();
    return true;
  }

  function fermer(){
    if(!codeAffiche) return;
    codeAffiche = null; cancelAnimationFrame(raf);
    fiche.hidden = true; scene.classList.remove('recherche');
    document.querySelectorAll('#eclairs .repere').forEach((e) => e.remove());
    VU.k = 1; VU.x = 0; VU.y = 0; geste();
  }

  let enCours = false;
  async function lire(){
    if(enCours || !D.cat || !D.chemins.size) return;
    enCours = true;
    try{
      const { data, error } = await sb.rpc('direct_affiche');
      if(error || !data) return;
      const n = Number(data.n) || 0, code = data.code ? String(data.code) : null, reste = Number(data.reste) || 0;
      if(dernierN === null){ dernierN = n; if(!code) return; }   // au chargement : rien de vieux, sauf une commune encore à l'écran
      if(!code || reste <= 0){ fermer(); dernierN = n; return; }
      if(n !== dernierN || code !== codeAffiche){ dernierN = n; montrer(code, data.demandeur, reste); return; }
      // même demande : la régie a pu ajouter du temps (+15 s)
      const fin = Date.now() + reste * 1000;
      if(fin > finLocale + 1500){ total += fin - finLocale; finLocale = fin; }
    }catch(e){ console.error(e); }
    finally{ enCours = false; }
  }
  // sécurité : si la base ne répond plus, la fiche s'en va quand même à l'heure
  setInterval(() => { if(codeAffiche && Date.now() > finLocale + 3000) fermer(); }, 1000);
  setInterval(lire, 2000);
})();
