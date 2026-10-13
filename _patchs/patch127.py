# -*- coding: utf-8 -*-
u"""
patch127 — qui est en ligne (idée de Nataël).

- Chaque jeu ouvert se signale sur un canal « en-ligne » de Supabase Realtime
  (présence : rien n'est écrit dans la base). Le signal disparaît quand le
  joueur ferme le jeu.
- Classement : un point vert après le pseudo des joueurs en ligne, et
  « N joueurs en ligne » en haut. Même point dans la liste des joueurs de
  la carte.
- Règles : case « Apparaître hors ligne » (retenue sur cet appareil). On voit
  toujours les autres ; on n'apparaît plus soi-même.
- Si Realtime ne répond pas, rien ne s'affiche et le jeu continue.
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

def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)

js = lire('app.js')
css = lire('style.css')
html = lire('index.html')
assert 'demarrerPresence' not in js, u'patch127 deja applique'

# ---------------------------------------------------------------- html : reglage
html = rempl(html, u"""        <div class="notif-carte" id="notifCarte"></div>""", u"""        <div class="notif-carte" id="notifCarte"></div>
        <label class="presence-reglage"><input type="checkbox" id="horsLigne"> <span><b>Apparaître hors ligne</b> · les autres joueurs ne verront pas que tu es connecté (réglage de cet appareil)</span></label>""", u'reglage')

# ---------------------------------------------------------------- js : presence
js = rempl(js, u"""// ---------- patch122 : ecran de chargement ----------""", u"""// ---------- patch127 : qui est en ligne ----------
let enLigne = new Set();
let canalPresence = null;
let horsLigne = (() => { try{ return localStorage.getItem('tf-hors-ligne') === '1'; }catch(e){ return false; } })();
const POINT_EN_LIGNE = '<i class="en-ligne-point" title="En ligne"></i>';
const pointEnLigne = (id) => enLigne.has(id) ? POINT_EN_LIGNE : '';
function demarrerPresence(uid){
  if(canalPresence || !uid || typeof sb.channel !== 'function') return;
  try{
    canalPresence = sb.channel('en-ligne', { config: { presence: { key: uid } } });
    canalPresence.on('presence', { event: 'sync' }, () => {
      enLigne = new Set(Object.keys(canalPresence.presenceState()));
      majEnLigne();
    });
    canalPresence.subscribe(async (statut) => {
      if(statut === 'SUBSCRIBED' && !horsLigne){
        try{ await canalPresence.track({ depuis: Date.now() }); }catch(e){}
      }
    });
  }catch(e){ console.error('Présence :', e); }
}
async function basculerHorsLigne(valeur){
  horsLigne = valeur;
  try{ localStorage.setItem('tf-hors-ligne', valeur ? '1' : '0'); }catch(e){}
  if(!canalPresence) return;
  try{ valeur ? await canalPresence.untrack() : await canalPresence.track({ depuis: Date.now() }); }catch(e){}
}
function majEnLigne(){
  const n = enLigne.size;
  let el = document.getElementById('clEnLigne');
  const tete = document.querySelector('#classement .cl-tete h2');
  if(!el && tete){
    el = document.createElement('span');
    el.id = 'clEnLigne';
    el.className = 'cl-enligne';
    tete.after(el);
  }
  if(el){
    el.hidden = n === 0;
    el.innerHTML = `<i></i>${n} joueur${n > 1 ? 's' : ''} en ligne`;
  }
  if(typeof renderClassement === 'function' && typeof classementDonnees !== 'undefined' && classementDonnees.length) renderClassement();
  if(typeof majLegendeEnLigne === 'function') majLegendeEnLigne();
}
// la liste des joueurs de la carte : on pose ou retire le point sans la redessiner
function majLegendeEnLigne(){
  document.querySelectorAll('.leg-joueur[data-joueur-id]').forEach(b => {
    const p = b.querySelector('.leg-pseudo');
    if(!p) return;
    const point = p.querySelector('.en-ligne-point');
    const doit = enLigne.has(b.dataset.joueurId);
    if(doit && !point) p.insertAdjacentHTML('beforeend', POINT_EN_LIGNE);
    else if(!doit && point) point.remove();
  });
}
(function brancherHorsLigne(){
  const c = document.getElementById('horsLigne');
  if(!c) return;
  c.checked = horsLigne;
  c.addEventListener('change', () => basculerHorsLigne(c.checked));
})();

// ---------- patch122 : ecran de chargement ----------""", u'presence')

js = rempl(js, u"""  dmMesure('paquets');
  dmFin();""", u"""  dmMesure('paquets');
  dmFin();
  demarrerPresence(session_.user.id);   // patch127""", u'demarrage presence')

# classement : podium et lignes
js = rempl(js, u"""      <span class="cl-pseudo">${l.est_moi ? 'Toi' : echapperTexte(l.pseudo)}</span>
      <span class="cl-score">${nb(l.score)}<small>pts</small></span>""", u"""      <span class="cl-pseudo">${l.est_moi ? 'Toi' : echapperTexte(l.pseudo)}${pointEnLigne(l.joueur_id)}</span>
      <span class="cl-score">${nb(l.score)}<small>pts</small></span>""", u'podium')
js = rempl(js, u"""        ? `<span class="sc-nom"><span class="cl-pseudo">${l.est_moi ? '<b>Toi</b>' : echapperTexte(l.pseudo)}</span>${scoreBarre(l.joueur_id)}</span>`
        : `<span class="cl-pseudo">${l.est_moi ? '<b>Toi</b>' : echapperTexte(l.pseudo)}</span>`}""",
u"""        ? `<span class="sc-nom"><span class="cl-pseudo">${l.est_moi ? '<b>Toi</b>' : echapperTexte(l.pseudo)}${pointEnLigne(l.joueur_id)}</span>${scoreBarre(l.joueur_id)}</span>`
        : `<span class="cl-pseudo">${l.est_moi ? '<b>Toi</b>' : echapperTexte(l.pseudo)}${pointEnLigne(l.joueur_id)}</span>`}""", u'lignes')

# legende de la carte : le point apres chaque rendu
js = rempl(js, u"""function renderLegendeCarte(joueurs, idSvg){""", u"""function renderLegendeCarte(joueurs, idSvg){
  setTimeout(majLegendeEnLigne, 0);   // patch127""", u'legende')

css += u"""
/* ---------- patch127 : qui est en ligne ---------- */
.cl-enligne{ display:inline-flex; align-items:center; gap:6px; font-size:.78rem; color:var(--brume); }
.cl-enligne[hidden]{ display:none; }
.cl-enligne i, .en-ligne-point{ display:inline-block; width:8px; height:8px; border-radius:50%; background:#3DDC84; box-shadow:0 0 8px rgba(61,220,132,.7); flex-shrink:0; }
.en-ligne-point{ width:7px; height:7px; margin-left:7px; vertical-align:2px; }
.presence-reglage{ display:flex; gap:10px; align-items:flex-start; margin:12px 0 0; font-size:.84rem; color:var(--brume); line-height:1.45; cursor:pointer; max-width:62ch; }
.presence-reglage b{ color:#fff; font-weight:600; }
.presence-reglage input{ margin-top:3px; accent-color: var(--c-legendaire); }
"""

ecrire('app.js', js)
ecrire('style.css', css)
ecrire('index.html', html)
print(u'patch127 applique')
