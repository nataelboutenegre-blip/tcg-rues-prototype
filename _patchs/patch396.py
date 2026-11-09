# patch396 (10/11/2026) : le fil de la roue du Front (s2-132, idée d'Oshannir, 9/11) :
# les derniers gros lots de tout le monde, le dernier jackpot, et ma journée à copier pour Discord.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
rep(A, """      <div class="rdf-chances" id="rdfChances" hidden></div>`;
    setRoueRot(roueRot);
  }""", """      <div class="rdf-chances" id="rdfChances" hidden></div>
      <div class="rdf-journal" id="rdfJournal" hidden></div>`;   // patch396
    setRoueRot(roueRot);
  }
  roueJournalCharger();   // patch396""")
rep(A, """function renderRoueInfos(){
  const el = document.getElementById('roueFront');
  if(!el || el.hidden || !ROUE || !el.offsetParent) return;   // onglet caché : rien à écrire
""", """// patch396 : le fil de la roue (s2-132) : gros lots de tout le monde, dernier jackpot, ma journée
let roueJournal = null, roueJournalLu = 0;
const ROUE_GROS = ['jackpot', 'gros', 'coffre', 'cagnotte', 'terra'];
async function roueJournalCharger(force){
  if(!roueActive()) return;
  const age = Date.now() - roueJournalLu;
  if(age < (force ? 8000 : 60000)) return;
  roueJournalLu = Date.now();
  try{
    const { data, error } = await sb.rpc('roue_front_journal');
    if(error){ if(fonctionAbsente(error)) roueJournalLu = Date.now() + 3600000; return; }
    roueJournal = data || null;
  }catch(e){ return; }
  renderRoueJournal();
}
function roueIlya(t){
  const m = Math.max(0, Math.round((Date.now() - Date.parse(t)) / 60000));
  return m < 1 ? 'à l’instant' : m < 60 ? `il y a ${m} min` : m < 1440 ? `il y a ${Math.floor(m / 60)} h` : `il y a ${Math.floor(m / 1440)} j`;
}
function roueCaseDe(id){ return (ROUE && Array.isArray(ROUE.cases) ? ROUE.cases : []).find(k => k.id === id) || { id, nom: id }; }
function roueMoiParts(m, brut){
  const e = Number(m.energie) || 0, l = Number(m.lingots) || 0, tp = Number(m.tp) || 0, t = Number(m.terra) || 0;
  return [e ? (brut ? `+${e} ⚡` : `+${e}<span class="rdf-e">${ICONE_ENERGIE}</span>`) : '', l ? `+${l} lingot${l > 1 ? 's' : ''}` : '',
          tp ? `+${tp} TP` : '', t ? `${t} paquet${t > 1 ? 's' : ''} Terra` : ''].filter(Boolean);
}
function roueMoiCopie(){
  const m = roueJournal && roueJournal.moi; if(!m) return '';
  const n = Number(m.tours) || 0, g = Number(m.gros) || 0, j = Number(m.jackpots) || 0;
  return `🎡 Ma roue du Front aujourd’hui : ${n} tour${n > 1 ? 's' : ''}${roueMoiParts(m, true).map(x => ', ' + x).join('')}`
    + (g ? `, ${g} gros lot${g > 1 ? 's' : ''}${j ? ` dont ${j} jackpot${j > 1 ? 's' : ''} 🎰` : ''}` : ', aucun gros lot 😭');
}
function renderRoueJournal(){
  const el = document.getElementById('rdfJournal'); if(!el) return;
  const J = roueJournal;
  if(!J){ el.hidden = true; return; }
  const lots = Array.isArray(J.lots) ? J.lots : [], jp = J.jackpot, m = J.moi || {};
  const ligne = (x) => {
    const k = roueCaseDe(x.case_id), g = roueGainsTexte(x) || 'réserve pleine';
    return `<div class="rdf-lot"><i style="background:${roueStyle(k).puce}"></i><span><b>${echapperTexte(x.pseudo || 'Un joueur')}</b> · ${echapperTexte(k.nom || x.case_id)}<small>${roueIlya(x.le)}</small></span><em>${g}</em></div>`;
  };
  const n = Number(m.tours) || 0;
  const html = `<h4>Le fil de la roue</h4>
    ${jp ? `<p class="rdf-jp">🎰 Dernier jackpot : <b>${echapperTexte(jp.pseudo || 'un joueur')}</b>, ${roueIlya(jp.le)}${Number(jp.jour) ? ` · ${jp.jour} en 24 h` : ''}</p>` : ''}
    ${lots.length ? lots.map(ligne).join('') : '<p class="rdf-vide">Aucun gros lot depuis deux jours.</p>'}
    <div class="rdf-moi"><span>Ta roue aujourd’hui : <b>${n} tour${n > 1 ? 's' : ''}</b>${n ? roueMoiParts(m).map(x => ' · ' + x).join('') : ''}${Number(m.gros) ? ` · <b>${m.gros} gros lot${m.gros > 1 ? 's' : ''}</b>` : ''}</span>
    ${n ? '<button type="button" class="rdf-copier" id="rdfCopier">Copier pour Discord</button>' : ''}</div>`;
  el.hidden = false;
  roueEcrire('rdfJournal', html);
}
function renderRoueInfos(){
  const el = document.getElementById('roueFront');
  if(!el || el.hidden || !ROUE || !el.offsetParent) return;   // onglet caché : rien à écrire
  renderRoueJournal();   // patch396 : les « il y a » avancent
""")
rep(A, """  roueGainMontrer(data);
  renderRoueInfos();""", """  roueGainMontrer(data);
  renderRoueInfos();
  setTimeout(() => roueJournalCharger(true), 600);   // patch396""")
rep(A, """  if(e.target.closest('#rdfLien')){ roueChancesOuvertes = !roueChancesOuvertes; renderRoue(); return; }""",
"""  if(e.target.closest('#rdfLien')){ roueChancesOuvertes = !roueChancesOuvertes; renderRoue(); return; }
  if(e.target.closest('#rdfCopier')){   // patch396
    const txt = roueMoiCopie();
    if(txt && navigator.clipboard) navigator.clipboard.writeText(txt).then(() => notifier({ type: 'succes', titre: 'Copié', texte: 'Colle-le sur Discord !' }), () => {});
    return;
  }""")
rep('style.css', ".rdf-ch-pied{ font-size:.68rem; color:#7F92AA; margin:6px 0 2px; }",
""".rdf-ch-pied{ font-size:.68rem; color:#7F92AA; margin:6px 0 2px; }
/* patch396 : le fil de la roue */
.rdf-journal{ margin:10px auto 0; max-width:330px; text-align:left; background:rgba(9,16,30,.7); border:1px solid rgba(169,188,212,.18); border-radius:14px; padding:8px 12px 10px; }
.rdf-journal[hidden]{ display:none; }
.rdf-journal h4{ margin:2px 0 6px; font:800 .78rem/1.2 var(--titre); letter-spacing:.06em; text-transform:uppercase; color:#FFE29A; }
.rdf-jp{ margin:0 0 6px; padding:6px 9px; border-radius:10px; background:rgba(232,48,111,.14); border:1px solid rgba(232,48,111,.35); font-size:.74rem; color:#FFD6E4; }
.rdf-jp b{ color:#fff; }
.rdf-lot{ display:grid; grid-template-columns:10px 1fr auto; gap:8px; align-items:center; padding:5px 0; border-top:1px solid rgba(169,188,212,.08); font-size:.76rem; color:#DCE5F0; }
.rdf-lot i{ width:10px; height:10px; border-radius:3px; }
.rdf-lot span{ min-width:0; overflow:hidden; text-overflow:ellipsis; }
.rdf-lot span b{ color:#fff; }
.rdf-lot small{ display:block; font-size:.64rem; color:#7F92AA; }
.rdf-lot em{ font-style:normal; font-weight:800; color:#fff; white-space:nowrap; font-size:.74rem; }
.rdf-vide{ font-size:.72rem; color:#7F92AA; margin:4px 0; }
.rdf-moi{ margin-top:6px; padding-top:8px; border-top:1px solid rgba(169,188,212,.18); font-size:.74rem; color:#DCE5F0; display:flex; flex-wrap:wrap; align-items:center; gap:6px 10px; }
.rdf-moi b{ color:#fff; }
.rdf-copier{ padding:5px 10px; border-radius:999px; border:1px solid rgba(169,188,212,.35); background:rgba(169,188,212,.08); color:#DCE5F0; font:inherit; font-size:.72rem; font-weight:700; cursor:pointer; }""")
print('patch396 ok')
