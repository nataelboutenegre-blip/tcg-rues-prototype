# -*- coding: utf-8 -*-
u"""
patch74 — Radar : le résumé d'un duel.

Demandé le 6 octobre (maquette validée) : une fois une partie finie, on
peut cliquer dessus dans le QG et revoir les 5 communes, avec les points
des deux joueurs manche par manche.

- QG, « Tes derniers duels » : chaque ligne est cliquable (›). Les parties
  qui attendent encore un adversaire apparaissent en tête (« En attente »)
  et s'ouvrent aussi, avec tes points seulement.
- Le résumé : le résultat, une carte avec les 5 communes numérotées, ton
  point (bleu) et celui de l'adversaire (rouge) ; « Tout » ou une manche
  (1 à 5), la manche choisie ressort et les autres s'estompent. Cliquer une
  ligne du tableau choisit aussi la manche. Sur ordinateur, la carte à
  gauche, le reste à droite.
- L'écran de fin de duel est ce même résumé (plus de tableau seul).

Serveur : radar_resume(id) et radar_etat().attente_liste
(_sql/radar-3-resume.sql, à passer avant le push).
"""
import io, os

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def entre(src, debut, fin, nouveau, etiquette):
    assert src.count(debut) == 1, u'%s : début introuvable ou double' % etiquette
    a = src.index(debut)
    b = src.index(fin, a)
    return src[:a] + nouveau + src[b:]

js = lire('app.js')

# ---------------------------------------------------------------------
# 1. QG : les lignes cliquables, les parties en attente en tête
# ---------------------------------------------------------------------
js = entre(js, u"  // derniers duels\n", u"\n\n  // classement", u"""  // derniers duels, et en tete les parties qui attendent un adversaire.
  // Chaque ligne ouvre le resume du duel (patch74).
  const d = r.derniers || [], att = r.attente_liste || [];
  document.getElementById('qgDerniersBloc').hidden = d.length === 0 && att.length === 0;
  const kmQG = (n) => Number(n).toLocaleString('fr-FR');
  document.getElementById('qgDerniers').innerHTML = att.map(x =>
    `<li data-id="${Number(x.id)}" tabindex="0" role="button"><span class="qg-res attente">En attente</span>
      <span class="qg-adv">pas encore d’adversaire<small>${kmQG(x.total_km)} km</small></span>
      <span></span><span class="qg-chev" aria-hidden="true">›</span></li>`).join('')
  + d.map(x => {
    const delta = (x.elo_apres != null && x.elo_avant != null) ? x.elo_apres - x.elo_avant : 0;
    const mot = x.resultat === 'victoire' ? 'Victoire' : x.resultat === 'defaite' ? 'Défaite' : 'Égalité';
    return `<li class="${x.vu ? '' : 'nouveau'}" data-id="${Number(x.id)}" tabindex="0" role="button"><span class="qg-res ${x.resultat}">${mot}</span>
      <span class="qg-adv">contre <b>${echapperTexte(x.adversaire || 'un joueur')}</b><small>${kmQG(x.total_km)} km contre ${kmQG(x.adversaire_km)} km</small></span>
      <span class="qg-delta ${delta >= 0 ? 'plus' : 'moins'}">${delta >= 0 ? '+' : ''}${delta}</span><span class="qg-chev" aria-hidden="true">›</span></li>`;
  }).join('');""", u'derniers duels')

# ---------------------------------------------------------------------
# 2. Le résumé (remplace l'ancien écran de fin)
# ---------------------------------------------------------------------
js = entre(js, u"function radarResultat(){", u"\ninitAuth();", u"""function radarResultat(){
  clearInterval(radarChrono);
  radarAfficherResume(radarPartie, true);
  radarPartie = null;
  chargerRadar();
}

// ----- le resume d'un duel (patch74) -----
let radarRes = null, radarResSel = -1;

async function radarOuvrirResume(id){
  try{
    const [{ data, error }] = await Promise.all([sb.rpc('radar_resume', { p_id: id }), loadOutline()]);
    if(error) throw error;
    const t = document.querySelector('.tab[data-tab="radar"]'); if(t) t.click();
    radarAfficherResume(data, false);
    window.scrollTo({ top: 0 });
  } catch(err){
    notifier({ type: 'erreur', titre: 'Radar', texte: messageLisible(err.message) });
  }
}

(function(){
  const liste = document.getElementById('qgDerniers');
  liste.addEventListener('click', (e) => {
    const li = e.target.closest('li[data-id]'); if(li) radarOuvrirResume(Number(li.dataset.id));
  });
  liste.addEventListener('keydown', (e) => {
    if(e.key !== 'Enter' && e.key !== ' ') return;
    const li = e.target.closest('li[data-id]'); if(!li) return;
    e.preventDefault(); radarOuvrirResume(Number(li.dataset.id));
  });
  // choix de la manche : puces, lignes du tableau, groupes de la carte
  document.getElementById('rdFin').addEventListener('click', (e) => {
    const x = e.target.closest('[data-m]'); if(!x || !radarRes) return;
    const i = Number(x.dataset.m);
    radarResChoisir(x.tagName === 'BUTTON' ? i : (radarResSel === i ? -1 : i));
  });
})();

function radarQuand(iso){
  if(!iso) return '';
  const d = new Date(iso), auj = new Date(), hier = new Date();
  hier.setDate(auj.getDate() - 1);
  const h = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }).replace(':', ' h ');
  const jour = d.toDateString() === auj.toDateString() ? 'aujourd’hui'
    : d.toDateString() === hier.toDateString() ? 'hier'
    : d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
  return `${jour} ${h}`;
}

function radarKm(c){
  if(!c) return '';
  return c.lon === null || c.lon === undefined
    ? `<span class="rd-passe" title="temps écoulé">${Number(c.km).toLocaleString('fr-FR')} km</span>`
    : `${Number(c.km).toLocaleString('fr-FR')} km`;
}

function radarAfficherResume(p, fin){
  radarMontrer('rdFin');
  radarRes = p; radarResSel = -1;
  const fmt = (n) => Number(n).toLocaleString('fr-FR');
  const adv = p.adversaire && p.resultat ? p.adversaire : null;
  const nomAdv = adv ? echapperTexte(adv.pseudo) : '';
  const quand = radarQuand(p.regle_le);
  let tete;
  if(adv){
    const mot = p.resultat === 'victoire' ? 'Victoire' : p.resultat === 'defaite' ? 'Défaite' : 'Égalité';
    const delta = p.elo_apres - p.elo_avant;
    const avant = radarRangDe(p.elo_avant), apres = radarRangDe(p.elo_apres);
    tete = `<div class="rd-titre"><h2 class="${p.resultat}">${mot}</h2><span>contre <b>${nomAdv}</b>${quand ? ` · ${quand}` : ''}</span></div>
      <div class="rd-score"><div><b>${fmt(p.total_km)} km</b><span>Toi</span></div><em>contre</em><div><b>${fmt(adv.total_km)} km</b><span>${nomAdv}</span></div></div>
      <div class="rd-elo"><span>Elo</span><b class="${delta >= 0 ? 'plus' : 'moins'}">${delta >= 0 ? '+' : ''}${delta}</b><span class="qg-petit">${fmt(p.elo_apres)} · ${apres}${apres !== avant ? (delta > 0 ? ' (promu !)' : ' (rétrogradé)') : ''}</span></div>`;
  } else {
    tete = `<h2>${fmt(p.total_km)} km</h2>
      <p class="qg-petit">${fin
        ? 'Ta partie attend un adversaire : le prochain joueur qui lance un duel affrontera ces 5 communes. Le résultat et l’Elo arriveront dans le QG.'
        : 'Cette partie attend encore un adversaire. Le résultat et l’Elo arriveront dans le QG.'}</p>`;
  }
  const gagne = (m) => m.lui && m.moi.km < m.lui.km;
  const puces = `<div class="rd-manches"><button type="button" data-m="-1" class="actif">Tout</button>${p.jouees.map((m, i) =>
    `<button type="button" data-m="${i}">${i + 1}${adv ? `<i class="${gagne(m) ? 'g' : 'p'}"></i>` : ''}</button>`).join('')}</div>
    <div class="rd-focus" id="rdFocus" hidden></div>`;
  const lignes = p.jouees.map((m, i) => `<tr data-m="${i}"><td><span class="rd-num">${i + 1}</span>${echapperTexte(m.nom)} <small>(${echapperTexte(m.dept)})</small></td>
    <td class="${adv && gagne(m) ? 'mieux' : ''}">${radarKm(m.moi)}</td>
    ${adv ? `<td class="${m.lui && m.lui.km < m.moi.km ? 'mieux' : ''}">${radarKm(m.lui)}</td>` : ''}</tr>`).join('');
  const tableau = `<table class="rd-detail"><thead><tr><th>Commune</th><th>Toi</th>${adv ? `<th>${nomAdv}</th>` : ''}</tr></thead><tbody>${lignes}</tbody></table>`;
  const partage = adv
    ? `TerraFront · Radar\\n${p.resultat === 'victoire' ? 'Victoire' : p.resultat === 'defaite' ? 'Défaite' : 'Égalité'} contre ${adv.pseudo} : ${fmt(p.total_km)} km contre ${fmt(adv.total_km)} km\\n${p.jouees.map(m => gagne(m) ? '🟦' : '🟥').join('')}\\nterrafront.fr/?onglet=qg`
    : null;
  document.getElementById('rdFin').innerHTML = `<button type="button" class="rd-retour" id="rdRetourHaut">← QG</button>
    <div class="rd-resume">
      <div class="rd-bloc rd-res-tete">${tete}${puces}</div>
      <div class="rd-bloc rd-res-carte"><div class="rd-zone"><svg id="rdResCarte" role="img" aria-label="Carte du duel : les communes et les points des joueurs"></svg></div>
        <div class="rd-legende"><span><i class="c"></i>la commune</span><span><i class="m"></i>toi</span>${adv ? `<span><i class="l"></i>${nomAdv}</span>` : ''}</div></div>
      <div class="rd-bloc rd-res-detail">${tableau}
        ${partage ? `<pre class="cdj-partage" id="rdPartage">${echapperTexte(partage)}</pre>` : ''}
        <div class="qg-actions"><button type="button" class="qg-btn plein" id="rdRetour">Retour au QG</button>${partage ? '<button type="button" class="qg-btn" id="rdCopier">Copier pour Discord</button>' : ''}</div></div>
    </div>`;
  const retour = () => { const t = document.querySelector('.tab[data-tab="qg"]'); if(t) t.click(); };
  document.getElementById('rdRetour').onclick = retour;
  document.getElementById('rdRetourHaut').onclick = retour;
  const c = document.getElementById('rdCopier');
  if(c) c.onclick = async () => {
    try{ await navigator.clipboard.writeText(partage); c.textContent = 'Copié'; }
    catch(err){ const s = getSelection(), r = document.createRange(); r.selectNodeContents(document.getElementById('rdPartage')); s.removeAllRanges(); s.addRange(r); c.textContent = 'Sélectionné : copie-le'; }
  };
  radarResDessiner();
}

function radarResChoisir(i){
  const p = radarRes; if(!p) return;
  radarResSel = (i >= 0 && i < p.jouees.length) ? i : -1;
  const fin = document.getElementById('rdFin');
  fin.querySelectorAll('.rd-manches button').forEach(b => b.classList.toggle('actif', Number(b.dataset.m) === radarResSel));
  fin.querySelectorAll('.rd-detail tbody tr').forEach(tr => tr.classList.toggle('sel', Number(tr.dataset.m) === radarResSel));
  const f = document.getElementById('rdFocus');
  if(radarResSel < 0){ f.hidden = true; f.innerHTML = ''; }
  else {
    const m = p.jouees[radarResSel];
    const adv = p.adversaire && p.resultat ? p.adversaire : null;
    const dit = (c) => c.lon === null || c.lon === undefined ? 'temps écoulé (1 000 km)' : radarKm(c);
    f.hidden = false;
    f.innerHTML = `<b>${echapperTexte(m.nom)} <small>(${echapperTexte(m.dept)})</small></b>
      <span><span class="rd-c-moi">Toi ${dit(m.moi)}</span>${adv && m.lui ? ` · <span class="rd-c-lui">${echapperTexte(adv.pseudo)} ${dit(m.lui)}</span>` : ''}</span>`;
  }
  radarResDessiner();
}

function radarResDessiner(){
  const svg = document.getElementById('rdResCarte'), p = radarRes;
  if(!svg || !p || !radarAssurerBornes()) return;
  const contour = FRANCE_OUTLINE || cdjContour;
  svg.setAttribute('viewBox', `0 0 ${cdjBornes.w.toFixed(2)} ${cdjBornes.h.toFixed(2)}`);
  const ray = cdjBornes.w / 80;
  let h = '';
  for(const a of contour) h += `<path class="cdj-fr" d="M${a.map(([lo, la]) => cdjPx(lo, la).join(',')).join('L')}Z"/>`;
  // la manche choisie en dernier, pour passer au-dessus des autres
  const ordre = p.jouees.map((m, i) => i).filter(i => i !== radarResSel);
  if(radarResSel >= 0) ordre.push(radarResSel);
  for(const i of ordre){
    const m = p.jouees[i];
    const [cx, cy] = cdjPx(+m.lon, +m.lat).map(Number);
    let g = '';
    for(const [qui, c] of [['lui', m.lui], ['moi', m.moi]]){
      if(!c || c.lon === null || c.lon === undefined) continue;
      const [x, y] = cdjPx(+c.lon, +c.lat);
      g += `<line class="rd-trait ${qui}" x1="${x}" y1="${y}" x2="${cx}" y2="${cy}" stroke-width="${ray / 3}" stroke-dasharray="${ray / 2} ${ray / 2}"/>`;
      g += `<circle class="rd-${qui}" cx="${x}" cy="${y}" r="${ray * 0.85}" stroke-width="${qui === 'moi' ? ray / 3.5 : ray / 4}"/>`;
    }
    g += `<circle class="rd-pastille" cx="${cx}" cy="${cy}" r="${ray * 1.5}"/>`;
    g += `<text class="rd-pastille-n" x="${cx}" y="${(cy + ray * 0.6).toFixed(3)}" font-size="${ray * 1.7}">${i + 1}</text>`;
    if(i === radarResSel) g += `<text class="rd-etiquette" x="${cx}" y="${(cy - ray * 2.6).toFixed(3)}" font-size="${ray * 2.2}">${echapperTexte(m.nom)}</text>`;
    h += `<g data-m="${i}" class="${radarResSel < 0 || radarResSel === i ? '' : 'estompe'}">${g}</g>`;
  }
  svg.innerHTML = h;
}
""", u'écran de fin')

ecrire('app.js', js)

# ---------------------------------------------------------------------
# 3. Les styles
# ---------------------------------------------------------------------
css = lire('style.css')
MARQUE = u'/* ---------- Radar : le résumé d’un duel (patch74) ---------- */'
assert MARQUE not in css, u'patch74 déjà passé'
css = css.rstrip('\n') + u'\n\n' + MARQUE + u"""
.qg-duels li{ grid-template-columns:84px minmax(0,1fr) auto 12px; }
.qg-duels li[data-id]{ cursor:pointer; }
.qg-duels li[data-id]:hover, .qg-duels li[data-id]:focus-visible{ background: rgba(255,255,255,.06); outline:none; }
.qg-duels li.nouveau:hover{ background: rgba(240,180,41,.16); }
.qg-res.attente{ color: var(--brume); }
.qg-chev{ color: var(--brume); font-size:18px; line-height:1; }
#rdFin{ max-width:1100px; }
.rd-retour{ align-self:flex-start; background:none; border:0; color: var(--brume); font:inherit; font-size:14px; padding:2px 0; cursor:pointer; }
.rd-retour:hover{ color:#fff; }
.rd-resume{ display:flex; flex-direction:column; gap:14px; }
.rd-titre{ display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }
.rd-titre span{ color: var(--brume); font-size:14px; }
.rd-titre span b{ color:#fff; }
.rd-manches{ display:flex; gap:6px; }
.rd-manches button{ flex:1; position:relative; border:1px solid rgba(169,188,212,.25); background:transparent; color:#fff; border-radius:9px; padding:8px 0 9px; font:600 14px var(--texte); cursor:pointer; }
.rd-manches button:hover{ border-color: rgba(169,188,212,.6); }
.rd-manches button i{ position:absolute; left:30%; right:30%; bottom:3px; height:3px; border-radius:2px; }
.rd-manches button i.g{ background: var(--c-legendaire); } .rd-manches button i.p{ background: rgba(169,188,212,.35); }
.rd-manches button.actif{ background: var(--c-legendaire); border-color: var(--c-legendaire); color: var(--nuit); }
.rd-manches button.actif i{ background: var(--nuit); }
.rd-focus{ display:flex; justify-content:space-between; align-items:baseline; gap:4px 10px; flex-wrap:wrap; }
.rd-focus[hidden]{ display:none; }
.rd-focus b{ font-family: var(--titre); font-size:26px; font-weight:800; }
.rd-focus b small{ font-size:16px; color: var(--brume); font-weight:600; }
.rd-focus > span{ font-size:13.5px; }
.rd-c-moi{ color:#6EA6FF; } .rd-c-lui{ color:#FF8A8D; }
.rd-zone{ background: var(--nuit); border-radius:12px; padding:8px; }
.rd-zone svg{ width:100%; height:auto; display:block; }
.rd-zone g[data-m]{ cursor:pointer; transition:opacity .15s; }
.rd-zone g.estompe{ opacity:.18; }
.rd-pastille{ fill: var(--c-legendaire); }
.rd-pastille-n{ fill: var(--nuit); font-weight:800; text-anchor:middle; }
.rd-legende{ display:flex; gap:14px; flex-wrap:wrap; font-size:12.5px; color: var(--brume); }
.rd-legende i{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; vertical-align:-1px; }
.rd-legende i.c{ background: var(--c-legendaire); } .rd-legende i.m{ background: var(--c-rare); } .rd-legende i.l{ background: var(--c-rouge); }
.rd-detail tbody tr{ cursor:pointer; }
.rd-detail tbody tr:hover td{ background: rgba(255,255,255,.04); }
.rd-detail tr.sel td{ background: rgba(240,180,41,.1); }
.rd-num{ display:inline-grid; place-items:center; width:20px; height:20px; border-radius:50%; background: rgba(240,180,41,.18); color: var(--c-legendaire); font-size:11.5px; font-weight:700; margin-right:6px; }
.rd-passe{ color: var(--brume); font-style:italic; }
@media (min-width: 900px){
  .rd-resume{ display:grid; grid-template-columns:minmax(0,1fr) 380px; grid-template-rows:auto 1fr; align-items:start; }
  .rd-res-carte{ grid-column:1; grid-row:1 / 3; }
  .rd-res-tete, .rd-res-detail{ grid-column:2; }
}
"""
ecrire('style.css', css)
print(u'patch74 : OK')
