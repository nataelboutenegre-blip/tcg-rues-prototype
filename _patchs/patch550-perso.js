
// ---------- patch550 : Personnaliser, le seul endroit (Mes cartes · Mon paquet · Mon territoire) ----------
// L'atelier quitte la Boutique : ses styles (à toi, à gagner, en vente) passent dans Mes cartes ; la couleur et le motif dans Mon territoire.
var grVue = 'cartes';   // var : lu avant la fin du fichier
function grSegHtml(){
  return `<div class="gr-seg" role="tablist" aria-label="Personnaliser">${[['cartes', 'Mes cartes'], ['paquet', 'Mon paquet'], ['territoire', 'Mon territoire']]
    .map(([v, l]) => `<button type="button" role="tab" data-gr-vue="${v}" class="${grVue === v ? 'on' : ''}" aria-selected="${grVue === v}">${l}</button>`).join('')}</div>`;
}
function grAtelierRemplir(corps){   // les blocs de l'atelier, rendus par atbRendre dans un cadre à part
  const cible = corps.querySelector('.gr-atb');
  if(!cible) return;
  if(!ATL.lu || !ATL.ouvert){ cible.closest('.gr-atb-zone')?.remove(); return; }
  const tmp = document.createElement('div');
  const vue = atbVue; atbVue = 'cartes'; atbCible = tmp;
  try{ atbRendre(); }finally{ atbCible = null; atbVue = vue; }
  const tete = tmp.querySelector('.atb-tete');
  const compo = tete && [...tete.querySelectorAll('p')].find(x => /Ta composition/.test(x.textContent));
  const txt = corps.querySelector('.gr-at-txt');
  if(compo && txt){
    const s = txt.querySelector('span'); if(s) s.textContent = ATL.v2 ? 'Styles, finitions, halos et bordures pour tes cartes Terra' : 'Finitions et halos pour tes cartes Terra';
    compo.className = 'gr-at-compo'; txt.appendChild(compo);
  }
  if(tete) tete.remove();
  const blocs = [...tmp.children];
  const moi = blocs.find(b => /^À toi/.test((b.querySelector('.atb-h') || {}).textContent || ''));
  const ici = corps.querySelector('.gr-atb-moi');
  if(moi && ici){ ici.replaceWith(moi); moi.classList.add('gr-atb-moi'); }
  [...tmp.children].forEach(b => cible.appendChild(b));
  if(!cible.querySelector('.atb-l')) cible.closest('.gr-atb-zone')?.remove();
}
function grTerrDessiner(corps){
  const c = corps.querySelector('.gr-terr');
  if(!c) return;
  const dessiner = () => { const b = c.querySelector('[data-mot-bande="moi"]'); if(b) motBande(b, MTF.moi, motMaCouleur()); };
  dessiner();
  if(!MTF.formes && MTF.ouvert !== false) motFormesCharger().then(dessiner).catch(() => {});
  if(!MTF.lu && !MTF.lecture){ MTF.lecture = motMoiCharger().then(ok => { MTF.lecture = null; if(ok && grVue === 'territoire') renderGardeRobe(); }); }
}
async function grAtbAcheter(id){
  const o = ATL_TOUTES_FAMILLES.flatMap(f => f.options).find(x => x.id === id);
  try{ await bqeVerifierAcces(); }catch(err){}
  const art = o && atlArticle(o);
  if(!bqeAcces || !art){ notifier({ type: 'erreur', titre: 'Indisponible', texte: 'Cet élément n’est pas en vente pour le moment.' }); return; }
  bqeOuvrirFiche(art.id, 'atelier');
}
document.getElementById('grCorps').addEventListener('click', async (e) => {
  const v = e.target.closest('[data-gr-vue]');
  if(v){ grVue = v.dataset.grVue; renderGardeRobe(); return; }
  if(e.target.closest('[data-atb="ouvrir"]')){ atlOuvrir(); return; }
  const ach = e.target.closest('[data-atb-acheter]');
  if(ach){ grAtbAcheter(ach.dataset.atbAcheter); return; }
  if(!e.target.closest('.gr-terr')) return;
  if(e.target.closest('[data-mot="ouvrir"]')){ motOuvrir(); return; }
  const pc = e.target.closest('[data-pf="couleur"]');
  if(pc){ await choisirCouleur(pc.dataset.couleur); renderGardeRobe(); return; }
  const dr = e.target.closest('[data-pf="dore"]');
  if(dr){
    try{ localStorage.setItem(CLE_DORE, dr.checked ? '1' : '0'); }catch(err){}
    appliquerCouleurMoi();
    try{ renderMapOverlay(); }catch(err){}
  }
});
function grOuvrir(vue){   // ouvre Profil › Personnaliser sur une partie
  grVue = vue || 'cartes';
  const t = document.querySelector('.tab[data-tab="personnaliser"]');
  if(t) t.click();
  try{ if(gardeRobe) renderGardeRobe(); }catch(e){}
}
