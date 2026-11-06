# patch360 (6/11/2026) : échange Terra, « lui manque » (idée de H34VEN).
#
# Dès qu'on a choisi la carte d'un joueur, la liste « Tes doublons » met en
# premier ceux qui lui manquent (étiquette verte « lui manque ») ; ceux qu'il
# a déjà passent en dessous, grisés (« il l'a déjà »), toujours choisissables.
# Sans carte choisie, rien ne change. Sans s2-107, rien ne change non plus.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch360' not in s, 'patch360 déjà appliqué'

s = rep(s, "// Terra : mes doublons du palier, moins ceux deja promis dans mes\n// propositions envoyees (le serveur applique la meme regle)\nfunction renderEchangeMienTerra(zone, rechercheM){",
"""// patch360 : parmi mes doublons, ceux qui manquent au joueur dont j'ai choisi la carte
let echLuiManque = { autre: null, cle: '', set: null, enVol: false };
async function majLuiManque(codes){
  const autre = echangeCible && echangeCible.proprietaire;
  if(!autre){ echLuiManque = { autre: null, cle: '', set: null, enVol: false }; return; }
  const cle = autre + '|' + codes.slice().sort().join(',');
  if(echLuiManque.cle === cle && (echLuiManque.set || echLuiManque.enVol || echLuiManque.echec)) return;
  echLuiManque = { autre, cle, set: null, enVol: true };
  try{
    const { data, error } = await sb.rpc('terra_lui_manque', { p_autre: autre, p_codes: codes.slice(0, 400) });
    if(echLuiManque.cle !== cle) return;   // un autre choix entre-temps
    echLuiManque = { autre, cle, set: error ? null : new Set(data || []), enVol: false, echec: !!error };
  }catch(e){ echLuiManque.enVol = false; echLuiManque.echec = true; return; }
  if(echLuiManque.set) renderEchangeMien();
}

// Terra : mes doublons du palier, moins ceux deja promis dans mes
// propositions envoyees (le serveur applique la meme regle)
function renderEchangeMienTerra(zone, rechercheM){""")

s = rep(s, "  if(echangeMien && !miennes.some(c => c.code === echangeMien)) echangeMien = null;\n  zone.innerHTML = miennes.map(c => `\n    <button class=\"ech-item ${c.tier.id} ${echangeMien === c.code ? 'choisi' : ''}\" data-mien=\"${echapperTexte(c.code)}\">\n      <b>${echapperTexte(c.nom)}</b>\n      <small>${echRarHtml(c.tier.id)}${echapperTexte(c.dept)} · ${c.libres} doublon${c.libres > 1 ? 's' : ''} échangeable${c.libres > 1 ? 's' : ''}</small>\n    </button>`).join('');",
"""  if(echangeMien && !miennes.some(c => c.code === echangeMien)) echangeMien = null;
  // patch360 : « lui manque » d'abord, dès qu'une carte d'un joueur est choisie
  const autreLM = echangeCible && echangeCible.proprietaire;
  if(autreLM) majLuiManque(miennes.map(c => c.code));
  const lm = (autreLM && echLuiManque.autre === autreLM && echLuiManque.set) ? echLuiManque.set : null;
  if(lm) miennes.sort((a, b) => (lm.has(b.code) ? 1 : 0) - (lm.has(a.code) ? 1 : 0));
  const pseudoLM = autreLM ? (echangeCible.pseudo || 'ce joueur') : '';
  const nbLM = lm ? miennes.filter(c => lm.has(c.code)).length : 0;
  zone.innerHTML = (lm ? `<p class="ech-lm-note">${nbLM ? `<b>${nbLM}</b> de tes doublons manque${nbLM > 1 ? 'nt' : ''} à <b>${echapperTexte(pseudoLM)}</b> : ils sont en premier.` : `<b>${echapperTexte(pseudoLM)}</b> a déjà tous tes doublons de cette rareté.`}</p>` : '')
    + miennes.map(c => `
    <button class="ech-item ${c.tier.id} ${echangeMien === c.code ? 'choisi' : ''}${lm && !lm.has(c.code) ? ' ech-deja' : ''}" data-mien="${echapperTexte(c.code)}">
      <b>${echapperTexte(c.nom)}</b>${lm ? (lm.has(c.code) ? '<span class="ech-lm">lui manque</span>' : '<span class="ech-lm-deja">il l’a déjà</span>') : ''}
      <small>${echRarHtml(c.tier.id)}${echapperTexte(c.dept)} · ${c.libres} doublon${c.libres > 1 ? 's' : ''} échangeable${c.libres > 1 ? 's' : ''}</small>
    </button>`).join('');""")

# la liste « Tes doublons » se redessine quand on choisit (ou retire) la carte d'un joueur
s = rep(s, "  echangeCible = (echangeCible && cleCible(echangeCible) === b.dataset.cible) ? null : c;\n  renderEchangeCibles();\n  if(echToutes()) renderEchangeMien();   // patch275",
           "  echangeCible = (echangeCible && cleCible(echangeCible) === b.dataset.cible) ? null : c;\n  renderEchangeCibles();\n  if(echToutes() || marcheTerra()) renderEchangeMien();   // patch275, patch360")

F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch360' not in c
c += """
/* patch360 : échange Terra, « lui manque » */
.ech-lm-note{ margin:0 0 8px; padding:7px 10px; border-radius:9px; font-size:.84rem; color:#DCE6F2;
  background:rgba(127,227,180,.08); border:1px solid rgba(127,227,180,.28); }
.ech-lm, .ech-lm-deja{ display:inline-block; margin-left:6px; padding:1px 7px; border-radius:20px; font-size:.7rem; font-weight:700; vertical-align:2px; }
.ech-lm{ background:rgba(127,227,180,.18); color:#7FE3B4; }
.ech-lm-deja{ background:rgba(169,188,212,.14); color: var(--brume); font-weight:600; }
.ech-item.ech-deja{ opacity:.55; }
.ech-item.ech-deja.choisi{ opacity:1; }
"""
C.write_text(c, encoding='utf-8')
print('patch360 appliqué')
