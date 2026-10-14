# -*- coding: utf-8 -*-
u"""
patch133 — deux idées de Wally.

1. Le solde toujours au même endroit (saison 1). Sur téléphone, dans
   l'en-tête à côté du bouton Règles ; sur ordinateur, en haut à droite de
   l'écran, fixe. Mis à jour à chaque lecture du solde (mon_etat) et après
   un paquet. En saison 2, la barre Terra / Front affiche déjà points et
   énergie en haut de chaque page : la pastille ne s'affiche pas.
2. Poser ses 5 favoris (communes gardées en fin de saison) depuis la carte :
   bouton « Garder en fin de saison » dans la bulle d'une de ses communes,
   et une étoile à côté du nom quand elle est gardée. Mêmes règles qu'en
   Collection (5 places, une seule légendaire).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)
js = lire('app.js'); css = lire('style.css'); html = lire('index.html')
assert 'majSoldeGlobal' not in js, u'patch133 deja applique'

# ------------------------------------------------ 1. le solde
html = rempl(html, u"""    <div class="entete-mobile">
      <span class="brand">Terra<span>Front</span></span>""", u"""    <div class="entete-mobile">
      <span class="brand">Terra<span>Front</span></span>
      <span class="solde-global" hidden title="Ton solde de points"><b>—</b> pts</span>""", u'pastille')
html = rempl(html, u"""    <div class="entete-mobile">""", u"""    <span class="solde-global solde-fixe" hidden title="Ton solde de points"><b>—</b> pts</span>
    <div class="entete-mobile">""", u'pastille ordinateur')

js = rempl(js, u"""async function monEtat(){
  const { data, error } = await sb.rpc('mon_etat');
  if(error) return null;
  return Array.isArray(data) ? (data[0] || null) : data;
}""", u"""async function monEtat(){
  const { data, error } = await sb.rpc('mon_etat');
  if(error) return null;
  const row = Array.isArray(data) ? (data[0] || null) : data;
  if(row) majSoldeGlobal(row.solde);   // patch133
  return row;
}

// patch133 : le solde toujours au meme endroit (saison 1 ; en saison 2 la
// barre Terra / Front le montre deja)
function majSoldeGlobal(solde){
  document.querySelectorAll('.solde-global').forEach(el => {
    if(SAISON2 || solde == null || isNaN(Number(solde))){ el.hidden = true; return; }
    el.querySelector('b').textContent = fmtNombre(Number(solde));
    el.hidden = false;
  });
}""", u'mon etat')

js = rempl(js, u"""  packStatusCache = data[0];""", u"""  packStatusCache = data[0];
  if(packStatusCache) majSoldeGlobal(packStatusCache.solde);   // patch133""", u'paquets')

# ------------------------------------------------ 2. les favoris depuis la carte
js = rempl(js, u"""ICONES_PC['gn-poser'] = ICONES_PC.bouclier;""", u"""ICONES_PC['gn-poser'] = ICONES_PC.bouclier;
ICONES_PC.favori = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M12 3.5l2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.8l-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z"/></svg>';""", u'icone')

js = rempl(js, u"""  if(mienne && enVente == null) actions.push(['', 'vente', 'Mettre en vente', 'Vendre ' + c.nom]);""",
u"""  if(mienne && enVente == null) actions.push(['', 'vente', 'Mettre en vente', 'Vendre ' + c.nom]);
  // patch133 : garder la commune en fin de saison, depuis la carte (idee de Wally)
  const gardee = mienne && favorisCharges && favorisSet.has(code);
  if(mienne && favorisCharges && !c.perdue)
    actions.push([gardee ? 'favori actif' : 'favori', 'favori',
      gardee ? `Gardée en fin de saison <span class="pc-gn-nb">${favorisSet.size} / ${FAV_MAX}</span>`
             : `Garder en fin de saison <span class="pc-gn-nb">${favorisSet.size} / ${FAV_MAX}</span>`,
      gardee ? 'Retirer l’étoile de ' + c.nom : 'Garder ' + c.nom + ' à la fin de la saison']);
  if(mienne && !favorisCharges) chargerFavoris().then(() => { if(panneauCommune === code && favorisCharges){ const a = panneauAncre; ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40); } });""", u'action favori')

js = rempl(js, u"""        <b>${echapperHtml(c.nom)}</b>
        <span class="pc-dep">""", u"""        <b>${echapperHtml(c.nom)}${gardee ? ' <span class="pc-etoile" title="Gardée en fin de saison">★</span>' : ''}</b>
        <span class="pc-dep">""", u'etoile titre')

js = rempl(js, u"""  if(quoi === 'attaque'){ ouvrirAttaque(code); return; }""", u"""  if(quoi === 'attaque'){ ouvrirAttaque(code); return; }
  if(quoi === 'favori'){   // patch133
    b.disabled = true;
    basculerFavori(c).then(() => { const a = panneauAncre; if(panneauCommune === code) ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40); });
    return;
  }""", u'clic favori')

css += u"""
/* ---------- patch133 : solde fixe, favoris depuis la carte ---------- */
.solde-global{ display:inline-flex; align-items:baseline; gap:4px; padding:5px 11px; border-radius:999px; font-size:.8rem; color: var(--brume);
  background: rgba(240,180,41,.1); border:1px solid rgba(240,180,41,.35); white-space:nowrap; font-variant-numeric:tabular-nums; }
.solde-global b{ font-family: var(--titre); font-weight:800; font-size:1.05rem; color: var(--c-legendaire); letter-spacing:.02em; }
.solde-global[hidden]{ display:none; }
.solde-fixe{ position:fixed; top:16px; right:22px; z-index:40; box-shadow:0 6px 18px rgba(0,0,0,.35); background: rgba(22,44,75,.92); backdrop-filter: blur(6px); }
@media (max-width: 720px){ .solde-fixe{ display:none !important; } }
.pc-action.favori.actif{ background: rgba(240,180,41,.16); color: var(--c-legendaire); }
.pc-action.favori.actif svg{ fill: var(--c-legendaire); }
.pc-etoile{ color: var(--c-legendaire); }
"""
ecrire('app.js', js); ecrire('style.css', css); ecrire('index.html', html)
print(u'patch133 applique')
