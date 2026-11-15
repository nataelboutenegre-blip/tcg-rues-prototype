#!/usr/bin/env python3
# patch438 : la boutique en vitrine (TP et euros), avec l'habillage Topo de la saison 3.
# Tout est sous html.topo:not(.sans-vitrine) ; interface.vitrine = 0 l'éteint seul.
import io, sys
A = 'app.js'; S = 'style.css'
a = io.open(A, encoding='utf-8').read()
s = io.open(S, encoding='utf-8').read()
if 'patch438' in a or 'patch438' in s: sys.exit('patch438 déjà appliqué')

def rempl(t, avant, apres, n=1):
    assert t.count(avant) == n, (t.count(avant), avant[:70])
    return t.replace(avant, apres)

# ---- 1. l'interrupteur
a = rempl(a, "function aluActif(){",
"""// patch438 : la boutique en vitrine (habillage Topo ; interface.vitrine = 0 l'éteint)
function bqLuxe(){ const h = document.documentElement.classList; return h.contains('topo') && !h.contains('sans-vitrine'); }
function bqxEcrin(html){ return bqLuxe() ? '<div class="bqx-ecrin">' + html + '</div>' : html; }
function aluActif(){""")
a = rempl(a, "      document.documentElement.classList.toggle('sans-revelation', o.revelation !== undefined && o.revelation !== null && Number(o.revelation) === 0);   // patch437\n",
"      document.documentElement.classList.toggle('sans-revelation', o.revelation !== undefined && o.revelation !== null && Number(o.revelation) === 0);   // patch437\n"
"      document.documentElement.classList.toggle('sans-vitrine', o.vitrine !== undefined && o.vitrine !== null && Number(o.vitrine) === 0);   // patch438\n")

# ---- 2. la boutique en TP : paquets et dos
a = rempl(a, """  st.innerHTML = `<span class="puce solde">Solde <b>${Number(b.solde).toLocaleString('fr-FR')}</b></span>`""",
"""  const L = bqLuxe();   // patch438
  st.innerHTML = `<span class="puce solde">Solde <b>${Number(b.solde).toLocaleString('fr-FR')}</b>${L ? ' <small>TP</small>' : ''}</span>`""")
a = rempl(a, """  paq.innerHTML = b.articles.filter(a => a.type === 'paquet').map(a => {""",
"""  // patch438 : le vrai sachet, en petit, à la place de l'épingle
  const sachet = (id) => {
    if(!L) return '<div class="bq-paquet-icone" aria-hidden="true">' + ICONE_EPINGLE + '</div>';
    const p = makePackEl('achete');
    const t = p.querySelector('.paquet-titre'), bd = p.querySelector('.paquet-bande');
    if(t) t.textContent = id === 'paquet-departement' ? 'Département' : 'Garanti';
    if(bd) bd.textContent = id === 'paquet-departement' ? '5 communes' : '1 rare ou mieux';
    return '<div class="bqx-sachet" aria-hidden="true">' + p.outerHTML.replace(/^<button/, '<div').replace(/<\\/button>$/, '</div>') + '</div>';
  };
  const quota = L ? `<div class="bqx-quota">${Array.from({ length: b.paquets_max }, (_, i) => `<i${i < b.paquets_du_jour ? ' class="on"' : ''}></i>`).join('')}<span>${b.paquets_du_jour} paquet${b.paquets_du_jour > 1 ? 's' : ''} sur ${b.paquets_max} aujourd'hui</span></div>` : '';
  paq.innerHTML = quota + b.articles.filter(a => a.type === 'paquet').map(a => {""")
a = rempl(a, """    return `<div class="bq-article bq-paquet ${a.id}">
        <div class="bq-paquet-icone" aria-hidden="true">${ICONE_EPINGLE}</div>
        <b>${echapperTexte(a.nom)}</b>""",
"""    return `<div class="bq-article bq-paquet ${a.id}">
        ${sachet(a.id)}
        <b>${echapperTexte(a.nom)}</b>""")
a = rempl(a, """    return `<div class="bq-article bq-dos${equipe ? ' equipe' : ''}">
        ${dosApercuHtml(a.id)}""",
"""    return `<div class="bq-article bq-dos${equipe ? ' equipe' : ''}">
        ${bqxEcrin(dosApercuHtml(a.id))}""")
a = rempl(a, """        ${action}
      </div>`;
  }).join('');
}

// achat en deux temps""",
"""        ${action}
      </div>`;
  }).join('');
  if(L) try{ habGl.demarrer(); }catch(e){}
}

// achat en deux temps""")

# ---- 3. « Ta boutique » : la carte de la semaine à la une
a = rempl(a, """    const libre = !x.achete && !x.possede;
    return `<div class="bqr-item ${tier.id}${x.achete ? ' achete' : ''}${x.possede ? ' deja' : ''}">
        <div class="bqr-carte">${carte.outerHTML}${libre ? `<span class="bqr-remise">−${x.remise} %</span>` : ''}${libre && x.album ? `<span class="bqr-album">Album · ${echapperTexte(x.album)}</span>` : ''}</div>""",
"""    const libre = !x.achete && !x.possede;
    if(x === une){   // patch438 : à la une
      const act = libre ? action.replace('class="bq-btn"', 'class="bq-btn bqx-cta"') : action;
      return `<div class="bqx-une ${tier.id}${x.achete ? ' achete' : ''}${x.possede ? ' deja' : ''}">
        <div class="bqx-une-carte"><div class="bqr-carte">${carte.outerHTML}</div></div>
        <div class="bqx-une-txt">
          <span class="bqx-sur">À la une · ${echapperTexte(tier.label)}</span>
          <b class="bqx-une-nom">${echapperTexte(x.nom)}</b>
          <span class="bqx-une-dept">${echapperTexte(DEPT_NAMES[x.dept] || '')} (${echapperTexte(x.dept)})</span>
          <div class="bqr-prix"><s>${Number(x.base).toLocaleString('fr-FR')}</s><b>${Number(x.prix).toLocaleString('fr-FR')}<small>TP</small></b>${libre ? `<span class="bqr-remise">−${x.remise} %</span>` : ''}</div>
          ${libre && x.album ? `<span class="bqr-album">Album · ${echapperTexte(x.album)}</span>` : ''}
          ${act}
        </div></div>`;
    }
    return `<div class="bqr-item ${tier.id}${x.achete ? ' achete' : ''}${x.possede ? ' deja' : ''}">
        ${L ? '<div class="bqx-ecrin">' : ''}<div class="bqr-carte">${carte.outerHTML}${libre ? `<span class="bqr-remise">−${x.remise} %</span>` : ''}${libre && x.album ? `<span class="bqr-album">Album · ${echapperTexte(x.album)}</span>` : ''}</div>${L ? '</div>' : ''}""")
a = rempl(a, """  const solde = boutiqueCache ? Number(boutiqueCache.solde) : Number(B.solde) || 0;
  const item = (x) => {""",
"""  const solde = boutiqueCache ? Number(boutiqueCache.solde) : Number(B.solde) || 0;
  const L = bqLuxe();   // patch438
  // à la une : la plus rare de la semaine, encore à vendre de préférence
  let une = null;
  if(L){
    const sem = (B.cartes || []).filter(x => x.periode === 'semaine');
    const rang = (x) => (RANG_TIER[x.tier] || 0) + (!x.achete && !x.possede ? 10 : 0);
    une = sem.slice().sort((p, q) => rang(q) - rang(p))[0] || null;
  }
  const item = (x) => {""")
a = rempl(a, """  const semaine = (B.cartes || []).filter(x => x.periode === 'semaine');
  el.innerHTML = `<div class="bqr">""",
"""  const semaine = (B.cartes || []).filter(x => x.periode === 'semaine');
  if(L){
    const autres = semaine.filter(x => x !== une);
    el.innerHTML = `<div class="bqr bqx-vitrine">
      <div class="bqr-tete"><h2>Ta boutique</h2><p>Des communes qui te manquent, choisies pour toi. Chaque carte s’achète une fois.</p></div>
      <div class="bqr-rang">De la semaine<span class="bqr-minuteur" data-fin="${B.fin_semaine}">${BQR_HORLOGE}${bqrReste(B.fin_semaine)}</span></div>
      ${une ? item(une) : '<p class="bqr-vide">Tu as déjà toutes ces communes : bravo !</p>'}
      ${autres.length ? `<div class="bqr-grille semaine">${autres.map(item).join('')}</div>` : ''}
      <div class="bqr-rang">Du jour<span class="bqr-minuteur" data-fin="${B.fin_jour}">${BQR_HORLOGE}${bqrReste(B.fin_jour)}</span></div>
      ${jour.length ? `<div class="bqr-grille">${jour.map(item).join('')}</div>` : '<p class="bqr-vide">Tu as déjà toutes ces communes : bravo !</p>'}
      <p class="bqr-note">Les cartes achetées en TP ne s’échangent pas et ne vont pas à la Bourse. Elles ne comptent pas dans les 3 paquets de boutique par jour.</p>
    </div>`;
  } else
  el.innerHTML = `<div class="bqr">""")

# ---- 4. la boutique en euros : à la une, rangées, « Tout voir »
a = rempl(a, """  return `<button type="button" class="bq-article bqe-article" data-bqe="${echapperTexte(a.id)}">
      ${bqeVignette(a)}""",
"""  return `<button type="button" class="bq-article bqe-article bqe-t-${a.type}" data-bqe="${echapperTexte(a.id)}">
      ${bqxEcrin(bqeVignette(a))}""")
a = rempl(a, """function renderBoutiqueEuros(){""",
"""// patch438 : l'objet à la une (une collection de préférence), il change chaque jour
function bqxUneEuros(arts){
  const libres = arts.filter(a => !a.possede && !a.livraison_le && !a.reserve_og && a.type !== 'effet');
  const cols = libres.filter(a => a.type === 'collection');
  const liste = cols.length ? cols : libres;
  if(!liste.length) return '';
  const a = liste[Math.floor(Date.now() / 86400000) % liste.length];
  const genre = { collection: 'Collection', habillage: 'Habillage de paquet', dos: 'Dos de carte', skin: 'Skin de carte' }[a.type] || '';
  return `<button type="button" class="bqx-une bqx-une-eu bqe-t-${a.type}" data-bqe="${echapperTexte(a.id)}">
      <div class="bqx-une-vis">${bqeVignette(a)}</div>
      <div class="bqx-une-txt">
        <span class="bqx-sur">À la une · ${genre}</span>
        <b class="bqx-une-nom">${echapperTexte(bqeNomCourt(a))}</b>
        <span class="bqx-une-dept">${echapperTexte(a.description || '')}</span>
        <span class="bqx-une-prix">${bqePrixHtml(a)}</span>
      </div></button>`;
}
function renderBoutiqueEuros(){""")
a = rempl(a, """  const section = (titre, mot, liste, badge) => liste.length ? `<div class="bourse-section bq-section">
      <h2>${titre}${badge ? ' <span class="bqe-og">OG</span>' : ''}${mot ? ` <small class="bqe-mot">${mot}</small>` : ''}</h2>""",
"""  const L = bqLuxe();   // patch438
  const section = (titre, mot, liste, badge) => liste.length ? `<div class="bourse-section bq-section">
      <h2>${titre}${badge ? ' <span class="bqe-og">OG</span>' : ''}${mot ? ` <small class="bqe-mot">${mot}</small>` : ''}${L && liste.length > 2 ? `<button type="button" class="bqx-tout" data-bqx-tout>Tout voir <span>(${liste.length})</span></button>` : ''}</h2>""")
a = rempl(a, """  corps.innerHTML = bqeBandeauHtml()
    + (cat.ouverte ?""",
"""  corps.innerHTML = (L ? bqxUneEuros(arts) : '') + bqeBandeauHtml()
    + (cat.ouverte ?""")
a = rempl(a, """  const art = e.target.closest('[data-bqe]');
  if(art){ bqeOuvrirFiche(art.dataset.bqe); return; }
  const r = e.target.closest('[data-retract]');""",
"""  const tv = e.target.closest('[data-bqx-tout]');   // patch438 : la rangée s'ouvre en grille
  if(tv){ const sec = tv.closest('.bq-section'); const o = sec.classList.toggle('ouvert'); tv.firstChild.textContent = o ? 'Réduire ' : 'Tout voir '; return; }
  const art = e.target.closest('[data-bqe]');
  if(art){ bqeOuvrirFiche(art.dataset.bqe); return; }
  const r = e.target.closest('[data-retract]');""")

css = io.open('_patchs/patch438.css', encoding='utf-8').read()
css = css.replace('BQ ', 'html.topo:not(.sans-vitrine) :is(#panel-boutique, #panel-boutiqueeuros) ').replace('VV ', 'html.topo:not(.sans-vitrine) ')
s = s.rstrip('\n') + '\n\n' + css
io.open(A, 'w', encoding='utf-8').write(a)
io.open(S, 'w', encoding='utf-8').write(s)
print('patch438 appliqué')
