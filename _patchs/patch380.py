# patch380 : la fiche d'attaque allégée (simplification, 8/11)
# - En haut : les chances en gros, la série (x / 3) à côté, la barre, la ligne de conquête.
# - Les effets (garnison, débutant, série noire, forteresse, appui, bombe, rébellion,
#   proximité) deviennent des puces courtes, vertes (bonus), rouges (malus) ou grises.
# - « Pourquoi ? » déplie les explications complètes (les anciens encadrés), et le choix
#   reste en mémoire (localStorage tf-atk-detail).
# - La rébellion passe dans « Plus d'options » ; elle s'ouvre directement si le curseur
#   était déjà ouvert.
# Rien ne change côté serveur ni dans les chances.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')

DEBUT = """  el.innerHTML = `
    <div class="pc-tete">
      <div class="pc-titre">
        <b>Attaquer ${echapperHtml(c.nom)}</b>
        <span class="pc-dep">${c.tier.label || LIBELLE_TIER[c.tier.id]} · à ${echapperHtml(c.pseudo)}</span>"""
FIN = """    </div>${rbBlocHtml(code, a)}`;"""
assert s.count(DEBUT) == 1 and s.count(FIN) == 1
i = s.index(DEBUT); j = s.index(FIN, i) + len(FIN)
ancien = s[i:j]
# les encadrés d'explication, gardés tels quels pour « Pourquoi ? »
k1 = ancien.index("    ${attaqueEnGarnison ? `<div class=\"gn-badge\">")
k2 = ancien.index("    <div class=\"pc-serie\">")
explications = ancien[k1:k2].rstrip() + "\n"

nouveau = """  // patch380 : la fiche allégée. Les effets en puces, les explications sur « Pourquoi ? »,
  // la rébellion dans « Plus d'options ».
  const puces = atkPuces(code, a);
  const rbHtml = rbBlocHtml(code, a);
  const optOuvert = atkOptions === code || rbOuvert === code;
  el.innerHTML = `
    <div class="pc-tete">
      <div class="pc-titre">
        <b>Attaquer ${echapperHtml(c.nom)}</b>
        <span class="pc-dep">${c.tier.label || LIBELLE_TIER[c.tier.id]} · à ${echapperHtml(c.pseudo)}</span>
      </div>
      <button class="pc-fermer" data-pc="retour" aria-label="Retour">&larr;</button>
    </div>

    <div class="atk-chance">
      <div class="atk-chance-g"><b>${a.chances}\\u00a0%</b><span>de chances<br>par round</span></div>
      <div class="atk-serie"><span class="pc-points">${[0,1,2].map(i => `<i class="${i < serie ? 'pris' : ''}"></i>`).join('')}</span><small>Série ${serie} / 3</small></div>
    </div>
    <div class="pc-jauge-barre"><i style="width:${a.chances}%"></i></div>
    ${ligneConquete(a.chances, serie)}

    ${puces.length ? `<div class="atk-puces">${puces.map(([k, ic, t]) => `<span class="atk-puce ${k}">${ic}<span>${t}</span></span>`).join('')}<button type="button" class="atk-pourquoi" data-pc="atk-detail" aria-expanded="${atkDetail}">${atkDetail ? 'Masquer' : 'Pourquoi\\u00a0?'}</button></div>` : ''}
    ${atkDetail ? `<div class="atk-detail">${atkDetailHtml(code, a)}</div>` : ''}

    <div class="pc-ints">${pastilles}</div>

    <div class="pc-actions">
      <button class="pc-action attaque" data-pc="assaut" ${attente > 0 || attaqueEnCours ? 'disabled' : ''}>
        ${attente > 0 ? 'Encore ' + formatDuree(attente) + ' à attendre' : `Lancer l’assaut — ${coutTexte(a.cout)}`}
      </button>
    </div>
    ${rbHtml ? (optOuvert ? rbHtml : `<button type="button" class="atk-plus" data-pc="atk-options">Plus d’options</button>`) : ''}`;"""
s = s[:i] + nouveau + s[j:]

# les puces et les explications
s = rep(s, """// patch140 : la chance de PRENDRE la commune, pas seulement de gagner le round
function ligneConquete(chances, serie){""", """// patch380 : la fiche d'attaque allégée
let atkDetail = false, atkOptions = null;
try{ atkDetail = localStorage.getItem('tf-atk-detail') === '1'; } catch(e){}
const ICONE_REPERE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-6.5-6.2-6.5-11.2a6.5 6.5 0 0 1 13 0C18.5 14.8 12 21 12 21z" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/><circle cx="12" cy="9.8" r="2.3" fill="currentColor"/></svg>';
// [genre, icône, texte] ; genre : plus (bonus), moins (malus), neutre
function atkPuces(code, a){
  const p = [];
  const deb = debutantActif();
  if(attaqueEnGarnison) p.push(['moins', ICONES_PC.bouclier, 'Garnison']);
  if(deb) p.push(attaqueEnGarnison ? ['neutre', ICONE_DEBUTANT, 'Sans bonus de débutant'] : ['plus', ICONE_DEBUTANT, 'Bonus de débutant']);
  if(SAISON2 && attaquePertes >= SN_PERTES && !attaqueEnGarnison) p.push(['plus', ICONE_TREFLE, `Série noire +${SN_BONUS}\\u00a0%`]);
  const B = attaqueEffetBt;
  if(B && B.defense > 0) p.push(['moins', ICONE_FORTERESSE, `Forteresse −${B.defense}\\u00a0%`]);
  if(B && B.appui > 0) p.push(['plus', ICONE_FORTERESSE, `Ta forteresse +${B.appui}\\u00a0%`]);
  if(B && B.bombe > 0) p.push(['plus', '<i class="atk-emo">💥</i>', `Bombe +${B.bombe}\\u00a0%`]);
  const R = attaqueRebellion;
  if(R && R.mienne) p.push(['plus', '<i class="atk-emo">✊</i>', `Rébellion +${rbFmt(Number(R.mienne.pct) || 0)}\\u00a0%`]);
  if(a.a_distance) p.push([deb && !attaqueEnGarnison ? 'neutre' : 'moins', ICONE_REPERE, 'À distance']);
  else if(Number(a.proches) >= 2) p.push(['plus', ICONE_REPERE, `${a.proches} voisines`]);
  else p.push(['neutre', ICONE_REPERE, '1 voisine']);
  return p;
}
// les explications complètes, celles d'avant patch380
function atkDetailHtml(code, a){
  return `
""" + explications + """    `;
}

// patch140 : la chance de PRENDRE la commune, pas seulement de gagner le round
function ligneConquete(chances, serie){""")

# les clics
s = rep(s, """  if(rbClicPanneau(quoi, code)) return;   // lot 8/11 : rébellion""", """  if(quoi === 'atk-detail'){   // patch380
    atkDetail = !atkDetail;
    try{ localStorage.setItem('tf-atk-detail', atkDetail ? '1' : '0'); } catch(err){}
    if(rbDerniers) rendreAttaque(...rbDerniers);
    return;
  }
  if(quoi === 'atk-options'){ atkOptions = code; if(rbDerniers) rendreAttaque(...rbDerniers); return; }   // patch380
  if(rbClicPanneau(quoi, code)) return;   // lot 8/11 : rébellion""")
F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch380' not in c
c += """
/* patch380 : la fiche d'attaque allégée */
.atk-chance{ display:flex; align-items:flex-end; justify-content:space-between; gap:12px; margin-top:12px; }
.atk-chance-g{ display:flex; align-items:flex-end; gap:8px; }
.atk-chance-g b{ font-family: var(--f-titre, inherit); font-size:2.1rem; line-height:.9; color:#fff; font-weight:700; letter-spacing:-.01em; }
.atk-chance-g span{ font-size:.7rem; line-height:1.15; color:#8FA4BF; padding-bottom:2px; }
.atk-serie{ display:flex; flex-direction:column; align-items:flex-end; gap:5px; padding-bottom:2px; }
.atk-serie small{ font-size:.7rem; color:#A9BCD4; }
.atk-chance + .pc-jauge-barre{ margin-top:9px; }
.atk-puces{ display:flex; flex-wrap:wrap; align-items:center; gap:6px; margin-top:10px; }
.atk-puce{ display:inline-flex; align-items:center; gap:5px; padding:4px 9px 4px 7px; border-radius:99px; font-size:.72rem; font-weight:600; line-height:1.2;
  background:rgba(169,188,212,.1); color:#C3D1E3; border:1px solid rgba(169,188,212,.16); }
.atk-puce svg{ width:13px; height:13px; flex:none; }
.atk-puce .atk-emo{ font-style:normal; font-size:.78rem; line-height:1; }
.atk-puce.plus{ background:rgba(61,214,140,.1); color:#8FE3B5; border-color:rgba(61,214,140,.28); }
.atk-puce.moins{ background:rgba(229,72,77,.1); color:#FF9DA0; border-color:rgba(229,72,77,.3); }
.atk-pourquoi{ font:inherit; font-size:.72rem; font-weight:600; color:#A9BCD4; background:none; border:0; padding:4px 2px; cursor:pointer; text-decoration:underline; text-underline-offset:3px; }
.atk-pourquoi:hover{ color:#fff; }
.atk-detail{ margin-top:4px; }
.atk-detail .pc-prox{ margin-top:10px; }
.atk-plus{ display:block; margin:10px auto 0; font:inherit; font-size:.76rem; font-weight:600; color:#A9BCD4; background:none; border:0; padding:4px 8px; cursor:pointer; }
.atk-plus::after{ content:' ▾'; font-size:.7rem; }
.atk-plus:hover{ color:#fff; }
"""
C.write_text(c, encoding='utf-8')
print('patch380 ok')
