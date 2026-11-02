# patch313 : le sondage « d'autres pays ? » en haut du Tirage (s2-80)
# Comptes de plus de 3 jours, une réponse par compte ; « ✕ » cache jusqu'au
# lendemain, une seule relance. Rien ne s'affiche tant que s2-80 n'est pas lancé.
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
assert 'patch313' not in s
s = rep(s, """      <div class="pp" id="premiersPas" hidden></div><!-- patch306 -->""",
           """      <div class="sd" id="sondagePays" hidden></div><!-- patch313 -->
      <div class="pp" id="premiersPas" hidden></div><!-- patch306 -->""")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch313' not in s
s = rep(s, """  chargerPremiersPas();   // patch306
""", """  chargerPremiersPas();   // patch306
  chargerSondagePays();   // patch313
""")
s = s.rstrip('\n') + r"""

// ---------- patch313 : le sondage « d'autres pays ? » (s2-80) ----------
// Une question, une fois : savoir si ajouter des pays plairait aux joueurs.
// Pas de récompense, pas de pourcentages montrés (ils influenceraient).
var SONDAGE_PAYS = null, sdChoix = '', sdPays = '';
var SD_CHOIX = [['meme', 'Oui, sur la même carte que la France'], ['apart', 'Oui, mais dans un mode à part'],
                ['non', 'Non, c’est la France qui me plaît'], ['egal', 'Ça m’est égal']];
var SD_PAYS = [['belgique', '🇧🇪 Belgique'], ['suisse', '🇨🇭 Suisse'], ['luxembourg', '🇱🇺 Luxembourg'], ['italie', '🇮🇹 Italie'],
               ['espagne', '🇪🇸 Espagne'], ['allemagne', '🇩🇪 Allemagne'], ['royaume-uni', '🇬🇧 Royaume-Uni'], ['quebec', '🇨🇦 Québec'], ['autre', 'Autre']];
async function chargerSondagePays(){
  try{
    const { data, error } = await sb.rpc('sondage_pays_etat');
    SONDAGE_PAYS = !error && data && data.afficher ? data : null;   // s2-80 pas lancé : rien
  }catch(e){ SONDAGE_PAYS = null; }
  renderSondagePays();
}
function renderSondagePays(merci){
  const z = document.getElementById('sondagePays');
  if(!z) return;
  if(merci){
    z.className = 'sd merci'; z.hidden = false;
    z.innerHTML = `<button type="button" class="sd-x" data-sd="cacher" aria-label="Fermer">✕</button>
      <div class="sd-t">Merci ! 🙌</div>
      <p class="sd-q sd-fin">Ta réponse est enregistrée. On partagera les résultats sur le Discord.</p>`;
    return;
  }
  if(!SONDAGE_PAYS){ z.hidden = true; z.innerHTML = ''; return; }
  const oui = sdChoix === 'meme' || sdChoix === 'apart';
  z.className = 'sd'; z.hidden = false;
  z.innerHTML = `<button type="button" class="sd-x" data-sd="fermer" aria-label="Plus tard" title="Plus tard">✕</button>
    <div class="sd-t">🌍 On a une question pour toi</div>
    <p class="sd-q">Ajouter d’autres pays à TerraFront, ça te plairait&nbsp;?</p>
    <p class="sd-sous">Rien n’est décidé : ta réponse nous aide à choisir.</p>
    <div class="sd-choix">${SD_CHOIX.map(([id, t]) => `<button type="button" data-sd="choix" data-v="${id}" aria-pressed="${sdChoix === id}"><span class="rond"></span>${t}</button>`).join('')}</div>
    ${oui ? `<div class="sd-pays"><p>Lequel en premier ? (facultatif)</p>
      <div class="sd-puces">${SD_PAYS.map(([id, t]) => `<button type="button" data-sd="pays" data-v="${id}" aria-pressed="${sdPays === id}">${t}</button>`).join('')}</div></div>` : ''}
    <button type="button" class="sd-envoyer" data-sd="envoyer"${sdChoix ? '' : ' disabled'}>Envoyer ma réponse</button>
    <p class="sd-pied">Une seule réponse par compte · anonyme dans les résultats</p>`;
}
document.getElementById('sondagePays').addEventListener('click', async (e) => {
  const b = e.target.closest('[data-sd]');
  if(!b || b.disabled) return;
  const quoi = b.dataset.sd;
  if(quoi === 'choix'){ sdChoix = b.dataset.v; if(sdChoix !== 'meme' && sdChoix !== 'apart') sdPays = ''; renderSondagePays(); return; }
  if(quoi === 'pays'){ sdPays = sdPays === b.dataset.v ? '' : b.dataset.v; renderSondagePays(); return; }
  if(quoi === 'cacher'){ const z = document.getElementById('sondagePays'); z.hidden = true; z.innerHTML = ''; return; }
  if(quoi === 'fermer'){
    SONDAGE_PAYS = null; renderSondagePays();
    try{ await sb.rpc('sondage_pays_fermer'); }catch(x){}
    return;
  }
  if(quoi === 'envoyer' && sdChoix){
    b.disabled = true;
    const { error } = await sb.rpc('sondage_pays_repondre', { p_choix: sdChoix, p_pays: sdPays || null });
    if(error){ b.disabled = false; notifier({ type: 'erreur', titre: 'Sondage', texte: messageLisible(error.message) }); return; }
    SONDAGE_PAYS = null;
    renderSondagePays(true);
  }
});
"""
f.write_text(s + '\n', encoding='utf-8')

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch313' not in s
s = s.rstrip('\n') + """

/* patch313 : le sondage « d'autres pays ? » */
.sd{ position:relative; background:linear-gradient(160deg,rgba(90,169,255,.18),rgba(15,31,56,.6) 55%); border:1px solid rgba(90,169,255,.5);
  border-radius:14px; padding:14px 14px 12px; color:#fff; margin:0 0 14px; text-align:left; }
.sd[hidden]{ display:none; }
.sd-x{ position:absolute; right:6px; top:4px; width:34px; height:34px; border:0; background:none; color:#A9BCD4; font-size:1.05rem; cursor:pointer; }
.sd-t{ font-family:var(--titre); font-weight:900; font-size:1.1rem; margin-right:30px; }
.sd-q{ font-size:.92rem; font-weight:600; margin:6px 0 2px; }
.sd-q.sd-fin{ font-weight:500; }
.sd-sous{ font-size:.76rem; color:#A9BCD4; margin:0 0 10px; }
.sd-choix{ display:flex; flex-direction:column; gap:7px; }
.sd-choix button{ display:flex; align-items:center; gap:10px; width:100%; text-align:left; padding:10px 12px; border-radius:10px;
  border:1px solid rgba(169,188,212,.28); background:rgba(10,22,40,.45); color:#fff; font:inherit; font-size:.86rem; cursor:pointer; }
.sd-choix .rond{ flex:none; width:18px; height:18px; border-radius:50%; border:2px solid rgba(169,188,212,.5); box-sizing:border-box; }
.sd-choix button[aria-pressed="true"]{ border-color:#5AA9FF; background:rgba(90,169,255,.16); }
.sd-choix button[aria-pressed="true"] .rond{ border-color:#5AA9FF; background:radial-gradient(circle,#5AA9FF 45%,transparent 50%); }
.sd-pays{ margin-top:12px; padding-top:10px; border-top:1px solid rgba(169,188,212,.14); }
.sd-pays p{ font-size:.8rem; color:#A9BCD4; margin:0 0 7px; }
.sd-puces{ display:flex; flex-wrap:wrap; gap:6px; }
.sd-puces button{ padding:6px 11px; border-radius:999px; border:1px solid rgba(169,188,212,.3); background:transparent; color:#fff; font:inherit; font-size:.78rem; cursor:pointer; }
.sd-puces button[aria-pressed="true"]{ background:#fff; color:#0F1F38; border-color:#fff; }
.sd-envoyer{ display:block; width:100%; margin-top:12px; padding:11px 12px; border-radius:10px; border:0; background:#5AA9FF; color:#0F1F38;
  font:inherit; font-weight:800; font-size:.9rem; cursor:pointer; }
.sd-envoyer:disabled{ opacity:.45; cursor:default; }
.sd-pied{ font-size:.72rem; color:#A9BCD4; margin:8px 0 0; text-align:center; }
.sd.merci{ background:linear-gradient(160deg,rgba(43,212,139,.16),rgba(15,31,56,.6) 55%); border-color:rgba(43,212,139,.5); }
.sd.merci .sd-t{ color:#7EE2B0; }
"""
f.write_text(s, encoding='utf-8')
print('patch313 appliqué')
