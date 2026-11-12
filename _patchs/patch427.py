# patch427 (12/11/2026) : quand on te prend une commune, le jeu dit ce que tu perds avec (va avec s2-142).
#  - cloche : sous « Oshannir t'a pris Grigny », la ligne « Tu perds aussi ta Fonderie (12 lingots pillés, plafond 45 → 30) » ;
#  - Journal : une ligne « En prenant Grigny, Oshannir t'a fait perdre ta Fonderie (…), ta Banque (…) » (visible par toi seul).
# Question de Nataël après ASMFCB (capacité 45 → 30 sans explication).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, S = 'app.js', 'style.css'
if 'patch427' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

# Journal : la ligne « pertes »
rep(A, """  else if(e.type === 'fonderie_detruite') texte = `${acteur} ${a} détruit ${e.je_suis_cible ? '<b>ta</b> Fonderie' : `la Fonderie de ${cible}`} à ${commune}`;
""", """  else if(e.type === 'fonderie_detruite') texte = `${acteur} ${a} détruit ${e.je_suis_cible ? '<b>ta</b> Fonderie' : `la Fonderie de ${cible}`} à ${commune}`;
  else if(e.type === 'pertes') texte = `En prenant ${commune}, ${acteur} t’a fait perdre ${pertesTexte(e.infos) || 'tes bâtiments'}`;   // patch427
""")
rep(A, """  const perso = e.je_suis_cible && (e.type === 'conquete' || e.type === 'achat' || e.type === 'fonderie_detruite');   // patch310""",
"""  const perso = e.je_suis_cible && (e.type === 'conquete' || e.type === 'achat' || e.type === 'fonderie_detruite' || e.type === 'pertes');   // patch310, patch427""")

# cloche : sous la commune perdue
rep(A, """    if(e.type === 'conquete' && e.je_suis_cible && p.jeu.perdue)
      items.push({ cle: `j|${e.id}`, sec: 'histo', c: 'histo', i: '🏴', mode: 'front', t: `<b>${echapperTexte(e.acteur_pseudo || 'Un joueur')}</b> t'a pris ${nom}`, s: `${label(e.tier)} · ${ilYA(e.cree_le)}` });""",
"""    if(e.type === 'conquete' && e.je_suis_cible && p.jeu.perdue){
      const pe = pertesDe(d.journal, e), pt = pe ? pertesTexte(pe.infos) : '';   // patch427
      items.push({ cle: `j|${e.id}`, sec: 'histo', c: 'histo', i: '🏴', mode: 'front', t: `<b>${echapperTexte(e.acteur_pseudo || 'Un joueur')}</b> t'a pris ${nom}${pt ? `<span class="nc-pertes">Tu perds aussi ${pt}</span>` : ''}`, s: `${label(e.tier)} · ${ilYA(e.cree_le)}` });
    }""")

open(A, 'a', encoding='utf-8').write("""
// ---------- patch427 : ce qu'on perd avec une commune prise (s2-142) ----------
ICONES_JOURNAL.pertes = ICONES_JOURNAL.fonderie_detruite;
function pertesTexte(infos){
  const L = infos && Array.isArray(infos.b) ? infos.b : [];
  const nb = (n) => Number(n || 0).toLocaleString('fr-FR');
  const nbL = (n) => `${nb(n)} lingot${n > 1 ? 's' : ''}`;
  const out = L.map(x => {
    if(x.t === 'fonderie'){
      const d = [];
      if(x.pille > 0) d.push(`${nbL(x.pille)} pillé${x.pille > 1 ? 's' : ''}`);
      if(x.max_apres < x.max_avant) d.push(`plafond ${x.max_avant} → ${x.max_apres}`);
      if(x.ecrete > 0) d.push(`${nbL(x.ecrete)} au-delà du plafond perdu${x.ecrete > 1 ? 's' : ''}`);
      return '<b>ta Fonderie</b>' + (d.length ? ` (${d.join(', ')})` : '');
    }
    if(x.t === 'banque') return '<b>ta Banque</b>' + (x.contenu > 0 ? ` et ses ${nbL(x.contenu)}${x.pille > 0 ? ` (dont ${nb(x.pille)} pillés)` : ''}` : '');
    if(x.t === 'forteresse') return '<b>ta Forteresse</b>';
    if(x.t === 'radar') return '<b>ton Radar</b>';
    if(x.t === 'centre') return '<b>ton Centre de recherche</b>' + (x.bombe ? ' et <b>ta bombe en préparation</b>' : '');
    return '';
  }).filter(Boolean);
  if(out.length < 2) return out.join('');
  return out.slice(0, -1).join(', ') + ' et ' + out[out.length - 1];
}
// la ligne « pertes » qui va avec une conquête (même commune, même instant)
function pertesDe(journal, e){
  const t = new Date(e.cree_le).getTime();
  return (journal || []).find(x => x.type === 'pertes' && x.commune_code === e.commune_code && Math.abs(new Date(x.cree_le).getTime() - t) < 10e3) || null;
}
""")

open(S, 'a', encoding='utf-8').write("""
/* patch427 : ce qu'on perd avec une commune prise */
.nc-pertes{display:block;margin-top:3px;font-size:.86em;color:#ff9b94;line-height:1.35}
.nc-pertes b{color:#ffb4ae;font-weight:600}
.jr-ligne.pertes{ border-left-color:#E5484D; }
.jr-ligne.pertes .jr-icone{ color:#FF8F92; background:rgba(229,72,77,.15); }
""")
print('patch427 OK')
