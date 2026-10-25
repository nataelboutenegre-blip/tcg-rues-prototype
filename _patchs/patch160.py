# -*- coding: utf-8 -*-
u"""
patch160 — « Plus ou moins », le jeu du jour (apercu jouable valide le
25 octobre, avec les photos). SQL : _sql/pom-1-installation.sql (AVANT).
- QG : une carte « Plus ou moins » sous la Commune du jour.
- Le jeu s'ouvre dans une fenetre : 10 duels, photos des cartes (dessin
  neutre sinon), la population apparait apres la reponse (le serveur la
  donne a ce moment-la seulement), puis le score, la ligne 🟩🟥 a copier.
- Sans le SQL : la carte du QG reste cachee.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

h = lire('index.html')
assert 'qgPom' not in h, u'patch160 deja applique'
h = rempl(h, u'''        <div class="qg-carte" id="qgRadar">''', u'''        <div class="qg-carte" id="qgPom" hidden>
          <div class="qg-tete">
            <span class="qg-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 20V5M3.5 8.5 7 5l3.5 3.5"/><path d="M17 4v15M13.5 15.5 17 19l3.5-3.5"/></svg></span>
            <div class="qg-titre"><h2>Plus ou moins</h2><p>Solo · 10 duels de population par jour · jusqu'à 50 pts</p></div>
            <span class="qg-etiquette" id="qgPomEtat"></span>
          </div>
          <div class="qg-actions"><button type="button" class="qg-btn" id="qgPomBtn">Jouer</button><span class="qg-petit" id="qgPomInfo"></span></div>
        </div>

        <div class="qg-carte" id="qgRadar">''', 'carte')
ecrire('index.html', h)

js = lire('app.js')
assert 'pom_partie' not in js, u'patch160 deja applique'
js = rempl(js, u"""  renderQG();
  if(!cdjEtat) chargerCdj();""", u"""  renderQG();
  if(!cdjEtat) chargerCdj();
  chargerPom();   // patch160""", 'qg')
js = rempl(js, u"""document.getElementById('qgCdjBtn').addEventListener('click', () => {""", u"""// ---------- patch160 : Plus ou moins ----------
// Tout se decide sur le serveur (pom_partie, pom_repondre) : la population
// d'un duel n'arrive qu'avec la reponse.
let pomEtat = null;   // null = pas charge, false = indisponible (SQL absent)
let pomFermer = null, pomOccupe = false;
async function chargerPom(){
  const { data, error } = await sb.rpc('pom_partie');
  if(error){ if(fonctionAbsente(error)) pomEtat = false; renderPomCarte(); return; }
  pomEtat = data;
  renderPomCarte();
}
function renderPomCarte(){
  const carte = document.getElementById('qgPom');
  if(!carte) return;
  carte.hidden = !pomEtat;
  if(!pomEtat) return;
  const e = pomEtat, n = (e.reponses || []).length;
  const etat = document.getElementById('qgPomEtat'), btn = document.getElementById('qgPomBtn');
  etat.className = 'qg-etiquette' + (e.fini ? ' vert' : ' or');
  etat.textContent = e.fini ? `${e.justes} / 10` : (n ? `${n} sur 10` : 'À jouer');
  btn.textContent = e.fini ? 'Revoir' : (n ? 'Continuer' : 'Jouer');
  btn.classList.toggle('plein', !e.fini);
  document.getElementById('qgPomInfo').textContent = (e.gain > 0 ? `+${e.gain} pts gagnés · ` : '') + 'nouveaux duels à minuit';
}
const pomNb = (x) => Number(x || 0).toLocaleString('fr-FR');
function pomTuile(c, k){
  const u = urlPhoto(c.photo);
  const photo = u ? `<img src="${echapperTexte(u)}" alt="" decoding="async" onerror="this.remove()">` : '';
  return `<button type="button" class="pom-commune" data-pom-choix="${k}">
      <span class="pom-photo">${photo}<b>${echapperTexte(c.nom)}</b></span>
      <span class="pom-bas"><span class="pom-pop" id="pomPop${k}">${c.population != null ? pomNb(c.population) + '<em>hab.</em>' : ''}</span>
        <small>${echapperTexte(DEPT_NAMES[c.departement] || '')} (${echapperTexte(c.departement)})</small></span>
    </button>`;
}
function pomCredits(d){
  const un = (c) => c.photo && c.auteur
    ? (c.source ? `<a href="${echapperTexte(c.source)}" target="_blank" rel="noopener">${echapperTexte(c.nom)} : ${echapperTexte(c.auteur)}${c.licence ? ' · ' + echapperTexte(c.licence) : ''}</a>`
                : `${echapperTexte(c.nom)} : ${echapperTexte(c.auteur)}${c.licence ? ' · ' + echapperTexte(c.licence) : ''}`) : '';
  const l = [un(d.a), un(d.b)].filter(Boolean);
  return l.length ? `<p class="pom-credits">Photos — ${l.join(' / ')}</p>` : '';
}
function pomPastilles(){
  const e = pomEtat, rep = e.reponses || [];
  return '<span class="pom-pastilles">' + e.duels.map((d, k) => {
    if(k >= rep.length) return `<i class="${k === rep.length ? 'ici' : ''}"></i>`;
    const pa = d.a.population, pb = d.b.population;
    const juste = (rep[k] === 0 && pa > pb) || (rep[k] === 1 && pb > pa);
    return `<i class="${juste ? 'ok' : 'ko'}"></i>`;
  }).join('') + '</span>';
}
function pomLigne(){
  const e = pomEtat;
  return (e.reponses || []).map((r, k) => {
    const d = e.duels[k];
    return ((r === 0 && d.a.population > d.b.population) || (r === 1 && d.b.population > d.a.population)) ? '🟩' : '🟥';
  }).join('');
}
function pomTextePartage(){
  return `TerraFront · Plus ou moins #${pomEtat.numero}\\n${pomEtat.justes}/10  ${pomLigne()}\\nterrafront.fr`;
}
function renderPom(){
  const corps = document.getElementById('pomCorps');
  if(!corps || !pomEtat) return;
  const e = pomEtat, i = (e.reponses || []).length;
  if(e.fini){
    corps.innerHTML = `<div class="pom-fin">
        <span class="pom-sur">Plus ou moins #${e.numero}</span>
        <div class="pom-score">${e.justes}<span> / 10</span></div>
        <div class="pom-ligne">${pomLigne()}</div>
        ${e.gain > 0 ? `<span class="pom-gain">+${e.gain} points Terra</span>` : ''}
        <pre class="pom-partage" id="pomPartage">${echapperTexte(pomTextePartage())}</pre>
        <button type="button" class="pom-btn" data-pom="copier">Copier mon résultat</button>
        <p class="pom-note">Nouveaux duels demain, à minuit.</p>
      </div>`;
    return;
  }
  const d = e.duels[i];
  corps.innerHTML = `<div class="pom-tete"><h2 id="pomTitre">Plus ou moins <span>#${e.numero} · duel ${i + 1} / 10</span></h2>${pomPastilles()}</div>
    <p class="pom-question">Laquelle a le plus d'habitants ?</p>
    <div class="pom-duel">${pomTuile(d.a, 0)}<span class="pom-ou">ou</span>${pomTuile(d.b, 1)}</div>
    <p class="pom-verdict" id="pomVerdict" aria-live="polite"></p>
    <button type="button" class="pom-btn" data-pom="suivant" id="pomSuivant" hidden>${i === 9 ? 'Voir mon score' : 'Duel suivant'}</button>
    ${pomCredits(d)}`;
}
function pomCompter(el, cible){
  if(!el) return;
  if(REDUCED_MOTION){ el.innerHTML = pomNb(cible) + '<em>hab.</em>'; return; }
  const t0 = performance.now(), duree = 700;
  const pas = (t) => {
    const k = Math.min(1, (t - t0) / duree);
    el.innerHTML = pomNb(Math.round(cible * (1 - Math.pow(1 - k, 3)))) + '<em>hab.</em>';
    if(k < 1) requestAnimationFrame(pas);
  };
  requestAnimationFrame(pas);
}
async function pomChoisir(k){
  if(pomOccupe || !pomEtat || pomEtat.fini) return;
  pomOccupe = true;
  const i = (pomEtat.reponses || []).length;
  const tuiles = document.querySelectorAll('#pomCorps .pom-commune');
  tuiles.forEach(t => { t.disabled = true; });
  const { data, error } = await sb.rpc('pom_repondre', { p_i: i, p_choix: k });
  pomOccupe = false;
  if(error){
    notifier({ type: 'erreur', titre: 'Plus ou moins', texte: messageLisible(error.message) });
    await chargerPom(); renderPom();
    return;
  }
  const d = pomEtat.duels[i];
  d.a.population = data.pop_a; d.b.population = data.pop_b;
  pomEtat.reponses = (pomEtat.reponses || []).concat([k]);
  pomEtat.justes = data.justes; pomEtat.gain = data.gain;
  const fini = data.fini;
  const grand = data.pop_a > data.pop_b ? 0 : 1;
  tuiles.forEach((t, j) => {
    t.classList.add(j === grand ? 'gagne' : 'perd');
    if(j === k && !data.juste) t.classList.add('mauvais');
    pomCompter(document.getElementById('pomPop' + j), j === 0 ? data.pop_a : data.pop_b);
  });
  const nomGrand = (grand === 0 ? d.a : d.b).nom;
  const rapport = Math.max(data.pop_a, data.pop_b) / Math.max(1, Math.min(data.pop_a, data.pop_b));
  const ecart = rapport >= 2 ? `${rapport.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} fois plus d'habitants`
                             : `${Math.max(1, Math.round(100 * (rapport - 1)))} % d'habitants de plus`;
  const v = document.getElementById('pomVerdict');
  v.className = 'pom-verdict ' + (data.juste ? 'ok' : 'ko');
  v.textContent = data.juste ? `Bien vu ! ${nomGrand} compte ${ecart}.` : `Raté : c'est ${nomGrand}, avec ${ecart}.`;
  const p = document.querySelector('#pomCorps .pom-pastilles');
  if(p) p.outerHTML = pomPastilles();
  if(data.juste) loadPackStatus();   // le solde affiche suit
  pomEtat.fini = fini;
  const s = document.getElementById('pomSuivant');
  if(s){ s.hidden = false; s.focus(); }
  renderPomCarte();
  if(fini) try{ loadQuetes(); }catch(err){}
}
async function ouvrirPom(){
  if(!pomEtat) await chargerPom();
  if(!pomEtat){ notifier({ type: 'erreur', titre: 'Plus ou moins', texte: "Le jeu n'est pas disponible pour le moment." }); return; }
  pomFermer = ouvrirFenetre(`<div class="fenetre pom" role="dialog" aria-modal="true" aria-labelledby="pomTitre">
      <button type="button" class="pom-fermer" data-pom="fermer" aria-label="Fermer">✕</button>
      <div id="pomCorps"></div></div>`, () => { pomFermer = null; renderPomCarte(); });
  renderPom();
  const f = document.querySelector('.fenetre.pom');
  if(f) f.addEventListener('click', async (ev) => {
    const c = ev.target.closest('[data-pom-choix]');
    if(c && !c.disabled) return pomChoisir(Number(c.dataset.pomChoix));
    const a = ev.target.closest('[data-pom]');
    if(!a) return;
    if(a.dataset.pom === 'fermer' && pomFermer) pomFermer(null);
    else if(a.dataset.pom === 'suivant') renderPom();
    else if(a.dataset.pom === 'copier'){
      try{ await navigator.clipboard.writeText(pomTextePartage()); a.textContent = 'Copié ✓'; }
      catch(err){
        const pre = document.getElementById('pomPartage');
        if(pre){ const r = document.createRange(); r.selectNodeContents(pre); const s = getSelection(); s.removeAllRanges(); s.addRange(r); }
        a.textContent = 'Sélectionné : copie-le';
      }
    }
  });
}
document.getElementById('qgPomBtn').addEventListener('click', () => ouvrirPom());

document.getElementById('qgCdjBtn').addEventListener('click', () => {""", 'jeu')
ecrire('app.js', js)

css = lire('style.css')
css = rempl(css, u"/* patch115 : l'astuce sous la recherche d'echange */", u"""/* ---------- patch160 : Plus ou moins ---------- */
.fenetre.pom{ width:min(640px, 100%); padding:22px 20px 18px; display:grid; gap:14px; max-height:calc(100dvh - 24px); overflow:auto; }
.pom-fermer{ position:absolute; top:10px; right:10px; width:34px; height:34px; border-radius:50%; border:0; cursor:pointer; background:rgba(255,255,255,.08); color:#fff; font-size:1rem; z-index:2; }
.pom-tete{ display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; padding-right:36px; }
.pom-tete h2{ font-family: var(--titre); font-size:1.4rem; margin:0; } .pom-tete h2 span{ color: var(--brume); font-size:.95rem; margin-left:6px; font-weight:600; }
.pom-pastilles{ display:flex; gap:4px; } .pom-pastilles i{ width:16px; height:6px; border-radius:3px; background:#2A3B57; }
.pom-pastilles i.ok{ background:#3DD68C; } .pom-pastilles i.ko{ background:#E5484D; } .pom-pastilles i.ici{ background: var(--c-legendaire); }
.pom-question{ text-align:center; font-family: var(--titre); font-size:1.25rem; margin:0; }
.pom-duel{ display:grid; grid-template-columns:minmax(0,1fr) auto minmax(0,1fr); gap:10px; align-items:stretch; }
.pom-ou{ align-self:center; font-family: var(--titre); color: var(--brume); }
.pom-commune{ font:inherit; color:#fff; text-align:left; padding:0; border:0; border-radius:14px; overflow:hidden; cursor:pointer; min-width:0;
  display:flex; flex-direction:column; background: radial-gradient(circle at 30% 20%, #24446F 0%, #13284A 60%, #0B1830 100%);
  box-shadow: inset 0 0 0 1.5px rgba(169,188,212,.25), 0 8px 18px rgba(0,0,0,.35); transition: transform .15s, box-shadow .2s; }
@media (hover:hover){ .pom-commune:hover:not(:disabled){ transform:translateY(-3px); box-shadow: inset 0 0 0 2px var(--c-legendaire), 0 10px 22px rgba(0,0,0,.4); } }
.pom-commune:disabled{ cursor:default; }
.pom-photo{ position:relative; display:block; aspect-ratio:4/3; max-width:100%; overflow:hidden;
  background: linear-gradient(160deg, #3B5378, #1C2E4D); }
.pom-photo img{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }
.pom-photo::after{ content:""; position:absolute; inset:0; background: linear-gradient(180deg, transparent 45%, rgba(11,24,48,.92)); }
.pom-photo b{ position:absolute; left:10px; right:10px; bottom:7px; z-index:1; font-family: var(--titre); font-size:1.3rem; line-height:1.05; overflow-wrap:anywhere; text-shadow:0 2px 6px rgba(0,0,0,.6); }
.pom-bas{ display:grid; gap:4px; padding:8px 10px 10px; }
.pom-bas small{ color: var(--brume); font-size:.8rem; }
.pom-pop{ font-family: var(--titre); font-size:1.45rem; color: var(--c-legendaire); min-height:1.75rem; font-variant-numeric: tabular-nums; }
.pom-pop em{ font-style:normal; font-size:.8rem; color: var(--brume); margin-left:4px; font-family: var(--texte); }
.pom-commune.gagne{ box-shadow: inset 0 0 0 3px #3DD68C, 0 0 22px rgba(61,214,140,.35); }
.pom-commune.perd{ opacity:.72; }
.pom-commune.mauvais{ opacity:1; box-shadow: inset 0 0 0 3px #E5484D; }
.pom-verdict{ text-align:center; min-height:1.4rem; font-weight:700; margin:0; }
.pom-verdict.ok{ color:#3DD68C; } .pom-verdict.ko{ color:#E5484D; }
.pom-btn{ justify-self:center; background: var(--c-legendaire); color: var(--encre); border:0; border-radius:12px; padding:11px 20px;
  font-family: var(--titre); font-weight:800; font-size:1.05rem; cursor:pointer; box-shadow:0 4px 0 #B7791F; }
.pom-credits{ margin:0; font-size:.68rem; color: var(--brume); text-align:center; line-height:1.4; }
.pom-credits a{ color: inherit; }
.pom-fin{ display:grid; gap:10px; justify-items:center; text-align:center; padding-top:6px; }
.pom-sur{ font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; color: var(--brume); font-weight:700; }
.pom-score{ font-family: var(--titre); font-size:3.2rem; line-height:1; } .pom-score span{ font-size:1.3rem; color: var(--brume); }
.pom-ligne{ font-size:1.3rem; letter-spacing:2px; }
.pom-gain{ background: rgba(240,180,41,.12); border:1px solid rgba(240,180,41,.4); border-radius:999px; padding:6px 12px; font-weight:600; font-size:.9rem; }
.pom-partage{ background: var(--nuit); border-radius:10px; padding:10px 12px; margin:0; text-align:left; font-size:.82rem; color: var(--brume); white-space:pre-wrap; }
.pom-note{ margin:0; color: var(--brume); font-size:.85rem; }
@media (max-width:420px){ .pom-duel{ grid-template-columns:minmax(0,1fr) minmax(0,1fr); } .pom-ou{ display:none; } .pom-photo b{ font-size:1.1rem; } .pom-pop{ font-size:1.2rem; } }

/* patch115 : l'astuce sous la recherche d'echange */""", 'css')
ecrire('style.css', css)
print(u'patch160 applique. Lancer : python3 maj-version.py')
