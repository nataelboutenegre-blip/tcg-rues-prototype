// TerraFront · la commune demandée en live (s2-103), pour la scène portrait (tiktok.html).
// La régie (regie.html) choisit une commune ; ici on lit direct_affiche() toutes les 2 s :
// la carte zoome dessus (projecteur + cercle), une fiche remplace la colonne de droite, puis retour à la France.
// Entre deux demandes, les conquêtes, défenses et bombes du fil zooment chacune 6 s, dans l'ordre d'arrivée
// (une demande de la régie passe toujours devant). ?attaques=0 dans l'adresse pour couper ce zoom auto.
// S'appuie sur direct.js (chargé avant) : D, VU, BOITES, cadrer, geste, toutPeindre, placerEclairs, px, py, esc, DEPT_NAMES.
'use strict';
(function(){
  const scene = document.getElementById('scene');
  const fiche = document.createElement('div');
  fiche.className = 'fiche'; fiche.hidden = true; fiche.setAttribute('aria-live', 'polite');
  scene.append(fiche);
  const BULLE = '<svg viewBox="0 0 24 24"><path d="M4 5h16v11H9l-5 4z"/><path d="M8 9.5h8M8 12.5h5"/></svg>';
  let dernierN = null, codeAffiche = null, source = null, finLocale = 0, total = 15000, raf = 0;
  const ATTAQUES = new URLSearchParams(location.search).get('attaques') !== '0';
  const DUREE_ATTAQUE = 6000, PAUSE = 4000, TROP_VIEUX = 120;
  const file = [];
  let pauseJusqua = 0;

  // la commune affichée en « projecteur » : le reste de la carte assombri, elle en pleine couleur, contour blanc
  function contour(){
    if(!codeAffiche) return;
    const p = D.chemins.get(codeAffiche);
    if(!p) return;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = 'rgba(10,22,40,.6)'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    poserVue();
    ctx.fillStyle = couleurDe(codeAffiche); ctx.fill(p);
    ctx.lineJoin = 'round';
    ctx.lineWidth = 12 / VU.k; ctx.strokeStyle = 'rgba(10,22,40,.9)'; ctx.stroke(p);
    ctx.lineWidth = 6 / VU.k; ctx.strokeStyle = '#FFFFFF'; ctx.stroke(p);
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

  function htmlDemande(code, demandeur){
    const r = D.cat.get(code);
    const j = D.proprio.get(code), jo = j ? D.joueurs.get(j) : null, cl = jo && jo.clan ? D.clans.get(jo.clan) : null;
    const dep = DEPT_NAMES[r[2]] || r[2], z = compter(r, cl, jo);
    const zone = j && cl
      ? '<div class="zone"><b>' + z.nClan.toLocaleString('fr-FR') + (z.nClan > 1 ? ' communes</b>tenues' : ' commune</b>tenue') + ' par [' + esc(cl.tag) + '] en ' + esc(dep) + '</div>'
      : '<div class="zone"><b>' + z.nLibres.toLocaleString('fr-FR') + (z.nLibres > 1 ? ' libres' : ' libre') + '</b>en ' + esc(dep) + ', sur ' + z.nDep.toLocaleString('fr-FR') + ' communes</div>';
    return '<div class="qui">' + BULLE + (demandeur ? '<span>Demandée par <b>' + esc(demandeur) + '</b></span>' : '<span>Commune demandée</span>') + '</div>'
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

  // la fiche d'une attaque du fil : [id, type, t, acteur, tag, cible, code, nom, …, dép.]
  const EPEE = '<svg viewBox="0 0 24 24"><path d="M14.5 3.5 20.5 3.5 20.5 9.5 9 21 3 15z"/><path d="M6 12l6 6"/></svg>';
  const BOUCLIER = '<svg viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z"/></svg>';
  const BOUM = '<svg viewBox="0 0 24 24"><circle cx="11" cy="14" r="6.5"/><path d="M15.5 9.5l2.5-2.5M18 4v2M21 7h-2"/></svg>';
  function htmlAttaque(e){
    const [, type, t, acteur, tag, cible, code] = e;
    const r = D.cat.get(String(code)), dep = DEPT_NAMES[r[2]] || r[2];
    const cl = tag ? [...D.clans.values()].find((c) => c.tag === tag) : null;
    const quand = Math.max(0, Math.round(Date.now() / 1000 - t)), ilya = quand < 60 ? quand + ' s' : Math.floor(quand / 60) + ' min';
    const titre = type === 'defense' ? BOUCLIER + '<span>Défense réussie · il y a ' + ilya + '</span>'
      : type === 'bombe' ? BOUM + '<span>Bombe lâchée · il y a ' + ilya + '</span>'
      : EPEE + '<span>Conquête · il y a ' + ilya + '</span>';
    const etat = type === 'defense' ? 'Tient bon' : type === 'bombe' ? 'Bombardée par' : 'Prise par';
    const suite = type === 'defense' ? (cible ? '<b>' + esc(cible) + '</b> repoussé' : 'L’attaque est repoussée')
      : type === 'bombe' ? 'Les communes autour encaissent'
      : (cible ? 'Arrachée à <b>' + esc(cible) + '</b>' : 'Elle était libre');
    return '<div class="qui">' + titre + '</div>'
      + '<h3>' + esc(r[1]) + '</h3>'
      + '<div class="lieu"><b>' + esc(dep) + ' (' + esc(r[2]) + ')</b> · ' + Number(r[3] || 0).toLocaleString('fr-FR') + ' hab.</div>'
      + '<div class="sep"></div>'
      + '<div class="etat">' + etat + '</div><div class="tenant"><i style="background:' + esc(cl ? cl.couleur : SEUL) + '"></i><b>' + esc(acteur || 'un joueur') + '</b></div>'
      + (cl ? '<div class="clan">Clan <em>[' + esc(cl.tag) + '] ' + esc(cl.nom) + '</em></div>' : '<div class="clan">Sans clan</div>')
      + '<div class="zone suite">' + suite + '</div>'
      + '<div class="appel">Toi aussi, <b>entre dans la guerre</b> sur terrafront.fr</div>'
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

  function montrer(code, html, reste, src){
    if(!D.cat || !D.cat.get(code)) return false;
    codeAffiche = code; source = src;
    fiche.innerHTML = html;
    fiche.classList.toggle('attaque', src === 'attaque');
    fiche.hidden = false; scene.classList.add('recherche');
    total = Math.max(1000, reste * 1000); finLocale = Date.now() + reste * 1000;
    const box = document.getElementById('eclairs');
    box.querySelectorAll('.repere').forEach((e) => e.remove());
    const b = BOITES.get(code), r = D.cat.get(code);
    if(b){
      // la commune au centre, avec ses voisines autour (le coin du clan se voit)
      const cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2, R = Math.max(55, (b[2] - b[0]) * 1.3, (b[3] - b[1]) * 1.3);
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
    if(source === 'attaque') pauseJusqua = Date.now() + PAUSE;
    codeAffiche = null; source = null; cancelAnimationFrame(raf);
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
      if(!code || reste <= 0){ if(source === 'demande') fermer(); dernierN = n; return; }
      if(n !== dernierN || source !== 'demande' || code !== codeAffiche){ dernierN = n; montrer(code, htmlDemande(code, data.demandeur), reste, 'demande'); return; }
      // même demande : la régie a pu ajouter du temps (+15 s)
      const fin = Date.now() + reste * 1000;
      if(fin > finLocale + 1500){ total += fin - finLocale; finLocale = fin; }
    }catch(e){ console.error(e); }
    finally{ enCours = false; }
  }
  // les attaques du fil, dans l'ordre d'arrivée (direct.js appelle eclair() pour chaque nouvelle)
  const eclairOrigine = window.eclair;
  window.eclair = function(e){
    eclairOrigine(e);
    if(!ATTAQUES || !e || !['conquete', 'defense', 'bombe'].includes(e[1])) return;
    if(!BOITES.has(String(e[6]))) return;
    file.push(e);
    while(file.length > 4) file.shift();   // en cas de rafale : les 4 plus récentes
  };
  // la fiche s'en va à l'heure (la régie peut ne plus répondre) ; puis l'attaque suivante
  setInterval(() => {
    const maintenant = Date.now();
    if(codeAffiche && maintenant > finLocale + (source === 'demande' ? 3000 : 0)) fermer();
    if(codeAffiche || maintenant < pauseJusqua) return;
    while(file.length){
      const e = file.shift();
      if(maintenant / 1000 - e[2] > TROP_VIEUX) continue;
      montrer(String(e[6]), htmlAttaque(e), DUREE_ATTAQUE / 1000, 'attaque');
      break;
    }
  }, 500);
  setInterval(lire, 2000);
})();
