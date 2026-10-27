# -*- coding: utf-8 -*-
u"""
patch231 — le Combat en vraies cartes (version A validée par Nataël le 27/10).

Chaque cible est la vraie carte, comme dans la Collection (photo, Aurore,
skin), et l'action est en dessous : propriétaire, distance, ta série, puis
un seul bouton qui dit l'état — rouge « Attaquer · coût · chances » quand
c'est prêt, sinon discret (« Prochain round dans… », « Bouclier · … »,
« Protégée encore… »). « Le défenseur a déjà utilisé sa défense » en une
ligne quand ça s'applique.
- Les skins viennent de front_skins() (s2-42), chargés avec le Combat ; sans
  s2-42, les cartes s'affichent sans skin.
- La marque du skin sur la carte (◆ BRASIER) mène à la Boutique.
- L'assaut (patch230) reprend ces skins sans redemander au serveur.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a); assert c == n, ('MATCH', a[:70], 'trouve', c, 'attendu', n); return s.replace(a, b)
def tranche(s, debut, fin, nouveau):
    assert s.count(debut) == 1, ('DEBUT', debut[:60], s.count(debut))
    i = s.index(debut); j = s.index(fin, i); assert j > i, 'FIN'
    return s[:i] + nouveau + s[j:]

s = lire('app.js')
assert 'patch231' not in s

# 1. les données : photo et numéro de la carte, et les skins du Front
s = rep(s, "  const champsCible = 'communes!inner(nom,departement,tier,latitude,longitude), joueurs(pseudo)';",
           "  const champsCible = 'communes!inner(nom,departement,tier,latitude,longitude,photo,rang,palier_total), joueurs(pseudo)';   // patch231\n"
           "  const skinsCharges = chargerSkinsFront();   // patch231")
s = rep(s, "  combatChargeLe = Date.now();   // patch135\n  renderCombatGrid();\n",
           "  combatChargeLe = Date.now();   // patch135\n  await skinsCharges;\n  renderCombatGrid();\n")
s = rep(s, "async function loadCombat(){\n",
"""// patch231 : les skins des cartes du Front (code -> skin), null = pas encore chargés ou s2-42 absent
let FRONT_SKINS = null;
async function chargerSkinsFront(){
  if(!SAISON2) return;
  try{
    const { data, error } = await sb.rpc('front_skins');
    if(error) return;
    FRONT_SKINS = new Map((data || []).map(r => [String(r.commune_code), skinCle(r.skin)]));
  }catch(e){}
}

async function loadCombat(){
""")
# l'assaut reprend la liste, sans redemander
s = rep(s, "  if(!SAISON2) return null;\n  const c = skinsCibles.get(code);\n",
           "  if(!SAISON2) return null;\n  if(FRONT_SKINS) return FRONT_SKINS.get(String(code)) || null;   // patch231\n  const c = skinsCibles.get(code);\n")

# 2. la carte de la cible
s = tranche(s, "    const au = auroreFront(c.commune_code);   // patch228\n    return `\n      <article class=\"cible ",
               "  };\n\n  // la signature dit si c'est un nouveau filtrage",
r'''    // patch231 : la vraie carte (photo, Aurore, skin), l'action en dessous
    const au = auroreFront(c.commune_code);
    const sk = !au && FRONT_SKINS ? FRONT_SKINS.get(String(c.commune_code)) : null;
    const carte = miniTerra({ code: c.commune_code, nom: commune.nom, dept: commune.departement, tier,
      exemplaires: 1, photo: commune.photo || '', rank: commune.rang, tierSize: commune.palier_total,
      aurore: au ? 1 : 0, skin: sk && skinConnu(sk) ? sk : undefined });
    let bouton;
    if(etatClasse === 'pret'){
      bouton = `<button class="cible-attaquer ca-att" data-action="attaquer" data-code="${c.commune_code}">Attaquer <span class="ca-pastille"><b>${coutTexte(cout)}</b> · <i>${vrai ? vrai.chances + ' %' : '…'}</i></span></button>`;
    } else {
      const texte = etatClasse === 'bouclier' ? `${ICONE_BOUCLIER}Bouclier · ${formatDuree(bouclierFin - now)}`
        : etatClasse === 'protegee' ? `Protégée encore ${formatDuree(immuniteFin - now)}`
        : `Prochain round dans ${formatDuree(prochainRound - now)}`;
      bouton = `<button class="cible-attaquer ca-att off" data-action="attaquer" data-code="${c.commune_code}" disabled>${texte}</button>`;
    }
    const km = c._distKm !== null ? (c._distKm < 10 ? c._distKm.toFixed(1).replace('.', ',') : Math.round(c._distKm)) + ' km' : '';
    const titreKm = km ? ` title="À ${km} ${echapperTexte(deCommune(c._procheDe))}"` : '';
    const serie = [0, 1, 2].map(i => `<i class="${i < victoires ? 'plein' : ''}"></i>`).join('');
    return `<article class="ca-cible">${carte}
      <p class="ca-qui"${titreKm}><i style="background:${colorForPlayer(c.joueur_id)}"></i><b>${echapperTexte(pseudo)}</b>${km ? `<span>· ${km}</span>` : ''}<span class="ca-serie" title="Ta série : ${victoires} / 3">${serie}</span></p>
      ${bouton}${noteAlerte ? `<p class="ca-note">${note}</p>` : ''}</article>`;
''')
s = rep(s, "      <article class=\"cible ", "      <article class=\"cible ", 0)   # l'ancien gabarit a bien disparu

# 3. la marque du skin mène à la Boutique
s = s.rstrip('\n') + u'''

// ---------- patch231 : dans le Combat, la marque du skin (◆ BRASIER) mène à la Boutique ----------
document.addEventListener('click', (e) => {
  const m = e.target.closest('#combatGrid .mini.skin .skin-marque');
  if(!m) return;
  const k = m.closest('.mini').dataset.skin;
  if(k){ e.preventDefault(); ouvrirSkinBoutique(k); }
});
'''
ecrire('app.js', s)

c = lire('style.css')
c = c.rstrip('\n') + u'''

/* ---------- patch231 : le Combat en vraies cartes ---------- */
#combatGrid.cibles-grille{ grid-template-columns:repeat(auto-fill, minmax(160px, 1fr)); gap:24px 16px; align-items:start; }
@media (max-width:520px){ #combatGrid.cibles-grille{ grid-template-columns:repeat(2, minmax(0, 1fr)); gap:20px 12px; } }
.ca-cible{ display:flex; flex-direction:column; gap:10px; min-width:0; }
.ca-cible > .mini{ width:100%; content-visibility:visible; }
.ca-cible > .mini:hover{ transform:none; }
.ca-qui{ display:flex; align-items:center; gap:6px; margin:0 2px; font-size:.74rem; color:var(--brume); min-width:0; }
.ca-qui > i{ width:8px; height:8px; border-radius:2px; flex:none; }
.ca-qui b{ color:#fff; font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; min-width:0; }
.ca-qui span{ white-space:nowrap; }
.ca-serie{ margin-left:auto; display:flex; gap:3px; flex:none; }
.ca-serie i{ width:7px; height:7px; border-radius:50%; border:1.5px solid rgba(169,188,212,.5); }
.ca-serie i.plein{ background:var(--c-rouge, #E5484D); border-color:var(--c-rouge, #E5484D); }
.cible-attaquer.ca-att{ margin:0; width:100%; gap:8px; padding:8px 8px 9px; font-size:1.05rem; }
.ca-att .ca-pastille{ font-family:var(--texte); font-size:.68rem; font-weight:600; background:rgba(0,0,0,.2); padding:2px 7px; border-radius:999px; white-space:nowrap; }
.ca-att .ca-pastille b{ background:none; padding:0; font-size:inherit; }
.ca-att .ca-pastille i{ font-style:normal; font-size:inherit; opacity:1; }
.cible-attaquer.ca-att.off, .cible-attaquer.ca-att.off:disabled{ background:transparent; color:var(--brume); box-shadow:inset 0 0 0 1px rgba(169,188,212,.28);
  font-family:var(--texte); font-size:.76rem; font-weight:600; letter-spacing:0; padding:9px 8px; }
.ca-att.off svg{ width:13px; height:13px; flex:none; }
.ca-note{ margin:-4px 2px 0; font-size:.68rem; color:#F7B267; }
#combatGrid .mini.skin .skin-marque{ pointer-events:auto; cursor:pointer; }
#combatGrid .mini.skin .skin-marque::after{ content:''; position:absolute; inset:-10px -8px; }
'''
ecrire('style.css', c)
print('patch231 ok')
