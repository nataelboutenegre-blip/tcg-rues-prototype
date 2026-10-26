# -*- coding: utf-8 -*-
u"""
patch211 — les légendaires rapportent de l'énergie (Front, saison 2).
Sous la jauge d'énergie de Combat : « Tes légendaires », +2 énergie par
légendaire tenue depuis 24 h (10 au plus), à récolter à la main une fois
par jour ; sinon, quand la prochaine compte, ou comment en profiter.
SQL : _sql/s2-30-recolte-legendaires.sql, À PASSER AVANT de pousser.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a)
    assert c == n, (a[:90], c, n)
    return s.replace(a, b)

js = lire('app.js')
assert 'patch211' not in js
js = rep(js, u"""  energieEtat = { energie: Number(data[0].energie), prochaine_dans: data[0].prochaine_dans, lu: Date.now() };
  renderJaugeEnergie();
}
""", u"""  energieEtat = { energie: Number(data[0].energie), prochaine_dans: data[0].prochaine_dans, lu: Date.now() };
  renderJaugeEnergie();
  if(!recolteLu || Date.now() - recolteLu > 300000) chargerRecolte();   // patch211
}

// patch211 : les légendaires tenues depuis 24 h rapportent de l'énergie, à récolter une fois par jour
let recolteEtat = null, recolteLu = 0, recolteEnCours = false;
async function chargerRecolte(){
  if(!SAISON2) return;
  recolteLu = Date.now();
  try{
    const { data, error } = await sb.rpc('front_recolte_etat');
    recolteEtat = error ? null : (Array.isArray(data) ? data[0] : data) || null;
  }catch(e){ recolteEtat = null; }
  renderJaugeEnergie();
}
function blocRecolteHtml(){
  const r = recolteEtat;
  if(!r) return '';
  const n = Number(r.pretes) || 0, e = Number(r.energie) || 0;
  const bientot = Array.isArray(r.bientot) ? r.bientot : [];
  const prochaine = bientot.length ? `<span class="rc-bientot">${echapperTexte(bientot[0].nom)} comptera dans ${bientot[0].heures} h${bientot.length > 1 ? ` · +${bientot.length - 1} autre${bientot.length > 2 ? 's' : ''}` : ''}</span>` : '';
  let corps;
  if(r.recoltee){
    corps = `<div class="rc-ligne"><span class="rc-texte"><b>Récolté aujourd'hui : +${Number(r.recoltee_energie) || 0}</b><small>Prochaine récolte demain.</small></span><span class="rc-fait">✓</span></div>`;
  } else if(n > 0){
    corps = `<div class="rc-ligne"><span class="rc-texte"><b>${n} légendaire${n > 1 ? 's' : ''} tenue${n > 1 ? 's' : ''} depuis 24 h</b><small>+2 énergie chacune, 10 au plus par jour</small></span>
      <button type="button" class="rc-bouton" data-recolter${recolteEnCours ? ' disabled' : ''}>Récolter <b>+${e}</b> ${ICONE_ENERGIE}</button></div>`;
  } else {
    corps = `<div class="rc-ligne"><span class="rc-texte"><b>Garde une légendaire 24 h</b><small>Chacune te rapporte +2 énergie par jour, à récolter ici (10 au plus).</small></span></div>`;
  }
  return `<div class="rc-bloc${r.recoltee ? ' fait' : n > 0 ? ' pret' : ''}"><div class="rc-titre"><span class="rc-etoile">★</span> Tes légendaires</div>${corps}${prochaine}</div>`;
}
document.addEventListener('click', async (ev) => {
  const b = ev.target.closest('[data-recolter]');
  if(!b || recolteEnCours) return;
  recolteEnCours = true; b.disabled = true;
  try{
    const { data, error } = await sb.rpc('front_recolter');
    if(error) notifier({ type: 'erreur', titre: 'Récolte', texte: messageLisible(error.message) });
    else {
      const l = Array.isArray(data) ? data[0] : data;
      notifier({ type: 'succes', titre: 'Énergie récoltée', texte: l && l.message ? l.message : '' });
    }
  }catch(e){ notifier({ type: 'erreur', titre: 'Récolte', texte: 'Réessaie dans un instant.' }); }
  recolteEnCours = false;
  await majEnergie();
  await chargerRecolte();
});
""")
js = rep(js, u"""    <p class="je-note">L'énergie se recharge seule : +1 toutes les 10 minutes.</p>`;
}""", u"""    <p class="je-note">L'énergie se recharge seule : +1 toutes les 10 minutes.</p>${blocRecolteHtml()}`;
}""")
ecrire('app.js', js)

css = lire('style.css')
assert 'patch211' not in css
css = css.rstrip('\n') + u"""

/* ---------- patch211 : la récolte des légendaires ---------- */
.rc-bloc{ margin-top:12px; padding:10px 12px; border-radius:12px; background:rgba(240,180,41,.06); border:1px solid rgba(240,180,41,.22); }
.rc-bloc.pret{ background:linear-gradient(180deg, rgba(240,180,41,.16), rgba(240,180,41,.05)); border-color:rgba(240,180,41,.55); }
.rc-bloc.fait{ background:rgba(169,188,212,.05); border-color:rgba(169,188,212,.16); }
.rc-titre{ display:flex; align-items:center; gap:6px; color: var(--c-legendaire); font-weight:600; font-size:.74rem; text-transform:uppercase; letter-spacing:.06em; margin-bottom:6px; }
.rc-bloc.fait .rc-titre{ color: var(--brume); }
.rc-ligne{ display:flex; align-items:center; justify-content:space-between; gap:10px; }
.rc-texte{ display:flex; flex-direction:column; gap:2px; min-width:0; }
.rc-texte b{ color:#fff; font-size:.9rem; }
.rc-texte small{ color: var(--brume); font-size:.74rem; line-height:1.35; }
.rc-bouton{ flex:none; display:inline-flex; align-items:center; gap:5px; min-height:44px; padding:8px 14px; border-radius:10px; border:0; cursor:pointer;
  background: var(--c-legendaire); color:#1a1205; font: inherit; font-weight:700; font-size:.88rem; }
.rc-bouton b{ font-family: var(--titre); font-weight:900; font-size:1.05rem; }
.rc-bouton svg{ width:14px; height:14px; }
.rc-bouton:disabled{ opacity:.6; cursor:default; }
.rc-fait{ flex:none; width:32px; height:32px; border-radius:50%; display:grid; place-items:center; background:rgba(76,195,138,.15); color:#4CC38A; font-weight:700; }
.rc-bientot{ display:block; margin-top:6px; font-size:.74rem; color: var(--brume); }
"""
ecrire('style.css', css)
print(u'patch211 applique. Passer _sql/s2-30-recolte-legendaires.sql AVANT de pousser. Lancer : python3 maj-version.py')
