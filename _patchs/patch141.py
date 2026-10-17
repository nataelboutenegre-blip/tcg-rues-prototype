# -*- coding: utf-8 -*-
u"""
patch141 — saison 2, Terra :
 1. Cartes achetées en points non échangeables (_sql/s2-23-cartes-bloquees.sql) :
    la collection lit ses exemplaires bloqués (terra_bloques_moi) ; la Bourse
    entre joueurs et l'Échange ne proposent que les doublons échangeables ;
    « 🔒 N achetés, vente au jeu seulement » ; la revente au jeu reste ouverte.
 2. Monuments dans Terra (_sql/s2-24-monuments-terra.sql) : en saison 2,
    l'album lit monuments_terra() ; doré = dans ta collection Terra, gris =
    à trouver ; filtres Tous / À toi / À trouver ; plus d'attaque.
Rien ne change en saison 1 (tout est derrière SAISON2 / Terra).
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
js = lire('app.js'); css = lire('style.css')
assert 'echangeablesTerra' not in js, u'patch141 deja applique'

# ---- 1a. lire les bloques avec la collection
js = rempl(js, u"""      exemplaires: Number(r.exemplaires) || 1, aurore: Number(r.aurore) || 0, rank: r.rang, tierSize: r.palier_total });
  }
  terraCharge = true;
  return true;
}""", u"""      exemplaires: Number(r.exemplaires) || 1, aurore: Number(r.aurore) || 0, rank: r.rang, tierSize: r.palier_total });
  }
  // patch141 : exemplaires achetes en points (non echangeables). Sans
  // s2-23, la fonction manque : tout reste echangeable cote affichage, le
  // serveur tranche de toute facon.
  try{
    const { data: bl, error: eb } = await sb.rpc('terra_bloques_moi');
    if(!eb) for(const b of bl || []){ const e = terraCollection.get(b.code); if(e) e.bloques = Number(b.bloques) || 0; }
  }catch(err){}
  terraCharge = true;
  return true;
}""", u'collection')

# ---- 1b. definition
js = rempl(js, u"""const libresTerra = (e) => e.exemplaires - Math.max(1, e.aurore || 0);""",
u"""const libresTerra = (e) => e.exemplaires - Math.max(1, e.aurore || 0);
// patch141 : ceux qu'on peut ECHANGER ou mettre en Bourse : ni Aurore, ni achetes en points
const echangeablesTerra = (e) => Math.max(0, e.exemplaires - Math.max(1, (e.aurore || 0) + (e.bloques || 0)));
// les doublons qui ne partent qu'au jeu : achetes en points
const achetesTerra = (e) => Math.max(0, libresTerra(e) - echangeablesTerra(e));""", u'libres')

# ---- 1c. paquet paye / boutique : les cartes arrivent bloquees
js = rempl(js, u"""    const { data, error } = await sb.rpc('boutique_ouvrir_collection', { p_collection: achat.collection });
    terraPaquet = error ? null : (data || []);""", u"""    const { data, error } = await sb.rpc('boutique_ouvrir_collection', { p_collection: achat.collection });
    terraPaquet = error ? null : (data || []);
    terraPaquetBloque = true;""", u'boutique collection')
js = rempl(js, u"""    const { data, error } = await sb.rpc('boutique_ouvrir_paquet', { p_article: achat.id, p_departement: achat.dep });
    terraPaquet = error ? null : (data || []);""", u"""    const { data, error } = await sb.rpc('boutique_ouvrir_paquet', { p_article: achat.id, p_departement: achat.dep });
    terraPaquet = error ? null : (data || []);
    terraPaquetBloque = true;""", u'boutique paquet')
js = rempl(js, u"""    const { data, error } = await sb.rpc('terra_ouvrir_paquet', { p_paye: type === 'achete' });
    terraPaquet = error ? null : (data || []);""", u"""    const { data, error } = await sb.rpc('terra_ouvrir_paquet', { p_paye: type === 'achete' });
    terraPaquet = error ? null : (data || []);
    terraPaquetBloque = type === 'achete';""", u'paquet')
js = rempl(js, u"""let terraPaquet = null; """, u"""let terraPaquetBloque = false;     // patch141 : paquet paye en points -> cartes non echangeables
let terraPaquet = null; """, u'variable')
js = rempl(js, u"""  if(e){ e.exemplaires = draw.terraExemplaires; if(draw.aurore) e.aurore = (e.aurore || 0) + 1; }
  else terraCollection.set(draw.code, { code: draw.code, nom: draw.nom, dept: draw.dept, tier: draw.tier,
    pop: draw.pop, exemplaires: draw.terraExemplaires, rank: draw.rank, tierSize: draw.tierSize,
    aurore: draw.aurore ? 1 : 0 });""", u"""  if(e){ e.exemplaires = draw.terraExemplaires; if(draw.aurore) e.aurore = (e.aurore || 0) + 1;
         if(terraPaquetBloque) e.bloques = (e.bloques || 0) + 1; }
  else terraCollection.set(draw.code, { code: draw.code, nom: draw.nom, dept: draw.dept, tier: draw.tier,
    pop: draw.pop, exemplaires: draw.terraExemplaires, rank: draw.rank, tierSize: draw.tierSize,
    aurore: draw.aurore ? 1 : 0, bloques: terraPaquetBloque ? 1 : 0 });""", u'carte retournee')

# ---- 1d. vente de tous les doublons : les bloques partent d'abord (comme le serveur)
js = rempl(js, u"""    for(const e of terraCollection.values()) if(choix.includes(e.tier.id) && libresTerra(e) > 0) e.exemplaires = Math.max(1, e.aurore || 0);""",
u"""    for(const e of terraCollection.values()) if(choix.includes(e.tier.id) && libresTerra(e) > 0){
      const vendus = libresTerra(e);
      e.exemplaires = Math.max(1, e.aurore || 0);
      e.bloques = Math.min(Math.max(0, (e.bloques || 0) - vendus), e.exemplaires);
    }""", u'vente lot')

# ---- 1e. Bourse : ligne
js = rempl(js, u"""    const n = libresTerra(e);
    const prixAnnonce = myListings.get(e.code);
    const actions = prixAnnonce
      ? `<span class="chip-vente">En vente à ${Number(prixAnnonce).toLocaleString('fr-FR')} pts</span>
         <div class="ligne-actions"><button class="btn-p contour" data-action="retirer" data-code="${e.code}">Retirer</button></div>`
      : `<div class="ligne-actions"><button class="btn-p contour" data-action="vendre-jeu" data-code="${e.code}">Vendre au jeu <b>${TERRA_REVENTE[e.tier.id]}</b></button>
         <button class="btn-p or" data-action="mettre-vente" data-code="${e.code}">Mettre en vente</button></div>`;""",
u"""    const n = libresTerra(e);
    const ach = achetesTerra(e);
    const prixAnnonce = myListings.get(e.code);
    const actions = prixAnnonce
      ? `<span class="chip-vente">En vente à ${Number(prixAnnonce).toLocaleString('fr-FR')} pts</span>
         <div class="ligne-actions"><button class="btn-p contour" data-action="retirer" data-code="${e.code}">Retirer</button></div>`
      : `<div class="ligne-actions"><button class="btn-p contour" data-action="vendre-jeu" data-code="${e.code}">Vendre au jeu <b>${TERRA_REVENTE[e.tier.id]}</b></button>
         ${echangeablesTerra(e) > 0 ? `<button class="btn-p or" data-action="mettre-vente" data-code="${e.code}">Mettre en vente</button>` : ''}</div>`;""", u'bourse ligne')
js = rempl(js, u"""${n > 0 ? n + ' doublon' + (n > 1 ? 's' : '') : 'plus de doublon'}</span>""",
u"""${n > 0 ? n + ' doublon' + (n > 1 ? 's' : '') : 'plus de doublon'}${ach > 0 ? ` · <span class="bq-achete">🔒 ${ach} acheté${ach > 1 ? 's' : ''}, vente au jeu seulement</span>` : ''}</span>""", u'bourse detail')

# ---- 1f. Echange : mes doublons echangeables
js = rempl(js, u"""    .filter(c => c.tier.id === echangeTier && libresTerra(c) > 0);
  const miennes = duPalier
    .map(c => Object.assign({}, c, { libres: libresTerra(c) - (promis[c.code] || 0) }))""",
u"""    .filter(c => c.tier.id === echangeTier && echangeablesTerra(c) > 0);
  const miennes = duPalier
    .map(c => Object.assign({}, c, { libres: echangeablesTerra(c) - (promis[c.code] || 0) }))""", u'echange')
js = rempl(js, u"""      <small>${echapperTexte(c.dept)} · ${c.libres} doublon${c.libres > 1 ? 's' : ''}</small>
    </button>`).join('');
  majResumeEchange();""", u"""      <small>${echapperTexte(c.dept)} · ${c.libres} doublon${c.libres > 1 ? 's' : ''} échangeable${c.libres > 1 ? 's' : ''}</small>
    </button>`).join('');
  if([...terraCollection.values()].some(c => c.tier.id === echangeTier && achetesTerra(c) > 0))
    zone.insertAdjacentHTML('afterbegin', '<p class="ech-note">🔒 Les cartes des paquets achetés en points ne s\\u2019échangent pas : elles restent dans ta collection ou se revendent au jeu.</p>');
  majResumeEchange();""", u'echange note')

# ---- 2. Monuments en Terra
js = rempl(js, u"""  const { data, error } = await sb.rpc('monuments_catalogue');""",
u"""  // patch141 : en saison 2, l'album est celui de Terra
  const { data, error } = await sb.rpc(SAISON2 ? 'monuments_terra' : 'monuments_catalogue');""", u'monuments rpc')
js = rempl(js, u"""  const qui = m.a_moi ? 'à toi'
            : (m.libre ? 'personne ne l\\'a' : echapperTexte(m.proprietaire || 'un joueur'));
  // une commune libre ne s'attaque pas : elle sort d'un paquet ou d'un
  // contrat. Pas d'action, donc pas d'apparence cliquable.
  const action = m.a_moi ? 'fiche' : (m.libre ? '' : 'attaquer');""",
u"""  const qui = SAISON2 ? (m.a_moi ? 'dans ta collection' : 'à trouver dans un paquet')
            : m.a_moi ? 'à toi'
            : (m.libre ? 'personne ne l\\'a' : echapperTexte(m.proprietaire || 'un joueur'));
  // une commune libre ne s'attaque pas : elle sort d'un paquet ou d'un
  // contrat. Pas d'action, donc pas d'apparence cliquable. En Terra
  // (patch141), rien ne s'attaque : pas d'action du tout.
  const action = SAISON2 ? '' : m.a_moi ? 'fiche' : (m.libre ? '' : 'attaquer');""", u'monuments carte')
js = rempl(js, u"""    filtres.innerHTML = [['tous', 'Tous'], ['moi', 'À toi'],
                         ['pris', 'Chez les autres'], ['libres', 'Libres']]""",
u"""    filtres.innerHTML = (SAISON2 ? [['tous', 'Tous'], ['moi', 'À toi'], ['libres', 'À trouver']]
                                 : [['tous', 'Tous'], ['moi', 'À toi'],
                         ['pris', 'Chez les autres'], ['libres', 'Libres']])""", u'monuments filtres')

# ---- 2b. texte d'introduction de l'onglet en saison 2
js = rempl(js, u"""async function loadMonuments(){
  const grille = document.getElementById('monGrille');
  if(!grille) return;""", u"""async function loadMonuments(){
  const grille = document.getElementById('monGrille');
  if(!grille) return;
  if(SAISON2){
    const sub = document.querySelector('#panel-monuments .sub');
    if(sub) sub.textContent = 'Les monuments des communes de France. Un monument entre dans ton album dès que sa commune entre dans ta collection Terra, et il y reste : personne ne peut te le prendre. Les cartes en gris sont celles qu\\u2019il te reste à trouver.';
  }""", u'monuments texte')

css += u"""
/* ---------- patch141 : cartes achetees, Monuments en Terra ---------- */
.bq-achete{ color:#A9BCD4; }
.ech-note{ grid-column:1 / -1; width:100%; font-size:.76rem; color:#8FA4BF; margin:0 0 8px; }
"""
ecrire('app.js', js); ecrire('style.css', css)
print(u'patch141 applique')
