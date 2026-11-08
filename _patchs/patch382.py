# patch382 : choisir combien d'énergie on met en rechargeant une garnison (demande de Nataël, 8/11)
# - Défendre › Mes garnisons : « Recharger » (avant : toujours +5) ouvre une rangée
#   +1 / +2 / +5 / Plein (+ ce qui manque jusqu'à 10) / Annuler. Un bouton au-delà de
#   l'énergie disponible est grisé.
# - Fiche de la commune sur la carte : en plus de +1 et +5, « Plein » quand il manque plus de 5.
# Rien ne change côté serveur : garnison_poser plafonne déjà à 10.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')

# --- Défendre : la liste des garnisons
s = rep(s, """        <button class="gl-r" data-gn-recharger="${code}" ${g.energie >= 10 ? 'disabled' : ''}>Recharger</button></div>`;
    }).join('')}""", """        <button class="gl-r${gnDose === code ? ' actif' : ''}" data-gn-recharger="${code}" ${g.energie >= 10 ? 'disabled' : ''}>Recharger</button></div>${gnDose === code ? gnDoseHtml(code, g) : ''}`;
    }).join('')}""")
s = rep(s, """// patch174 : poser une garnison depuis Defendre
let gnRecherche = '';""", """// patch382 : la recharge au choix (+1, +2, +5, plein)
let gnDose = null;
function gnDoseHtml(code, g){
  const manque = Math.max(0, 10 - (Number(g.energie) || 0));
  const dispo = energieEtat ? Math.floor(Number(energieEtat.energie) || 0) : 10;
  const b = (n, txt, cls) => `<button type="button"${cls ? ` class="${cls}"` : ''} data-gn-dose="${echapperTexte(code)}" data-n="${n}" ${n > dispo ? 'disabled' : ''}>${txt} ${ICONE_ENERGIE}</button>`;
  return `<div class="gn-btns gn-dose">${[1, 2, 5].filter(n => n < manque).map(n => b(n, '+' + n)).join('')}${b(manque, 'Plein +' + manque, 'gn-plein')}<button type="button" class="sec gn-dose-x" data-gn-dose-x aria-label="Annuler">✕</button></div>
    ${dispo < manque ? `<p class="gn-txt gn-dose-note">Tu as ${dispo} énergie.</p>` : ''}`;
}

// patch174 : poser une garnison depuis Defendre
let gnRecherche = '';""")
s = rep(s, """      const b = e.target.closest('[data-gn-recharger]');
      if(b) garnisonAction(b.dataset.gnRecharger, 5);""", """      // patch382 : « Recharger » ouvre le choix de la quantité
      const b = e.target.closest('[data-gn-recharger]');
      if(b){ gnDose = gnDose === b.dataset.gnRecharger ? null : b.dataset.gnRecharger; renderGarnisons(); return; }
      if(e.target.closest('[data-gn-dose-x]')){ gnDose = null; renderGarnisons(); return; }
      const d = e.target.closest('[data-gn-dose]');
      if(d){
        d.disabled = true;
        const code = d.dataset.gnDose;
        gnDose = null;
        garnisonAction(code, Number(d.dataset.n) || 1);
        return;
      }""")

# --- les places libres : l'ancien plafond de 3 était resté en dur (avec 3 ou 4 garnisons sur 5,
#     la liste « En garnison » disparaissait de Défendre)
s = rep(s, """    ${liste.length < 3 ? `<p class="gl-vide">${3 - liste.length} place${liste.length < 2 ? 's' : ''} libre${liste.length < 2 ? 's' : ''} : choisis""",
           """    ${liste.length < garnisonsMax() ? `<p class="gl-vide">${garnisonsMax() - liste.length} place${garnisonsMax() - liste.length > 1 ? 's' : ''} libre${garnisonsMax() - liste.length > 1 ? 's' : ''} : choisis""")

# --- la fiche de la commune : « Plein » quand il manque plus de 5
s = rep(s, """      <button data-pc="gn-plus" data-n="5" ${g.energie >= 10 ? 'disabled' : ''}>+5 ${ICONE_ENERGIE}</button>""", """      <button data-pc="gn-plus" data-n="5" ${g.energie >= 10 ? 'disabled' : ''}>+5 ${ICONE_ENERGIE}</button>
      ${10 - g.energie > 5 ? `<button class="gn-plein" data-pc="gn-plus" data-n="${10 - g.energie}">Plein +${10 - g.energie} ${ICONE_ENERGIE}</button>` : ''}""")
F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch382' not in c
c += """
/* patch382 : la recharge de garnison au choix */
.gn-dose{ margin:2px 0 10px; flex-wrap:wrap; }
.gn-dose button{ min-width:48px; }
.gn-dose .gn-dose-x{ flex:0 0 40px; min-width:40px; }
.gn-btns button.gn-plein{ white-space:nowrap; font-size:.76rem; }
.gn-dose-note{ margin:-4px 0 10px; }
.gl-r.actif{ border-color:rgba(229,72,77,.6); background:rgba(229,72,77,.2); color:#fff; }
"""
C.write_text(c, encoding='utf-8')
print('patch382 ok')
