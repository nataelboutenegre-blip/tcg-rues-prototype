# -*- coding: utf-8 -*-
u"""
patch171 — les photos sur les cartes Terra (apercu valide le 25 octobre :
meme presentation que les cartes du Front). SQL : _sql/terra-photos.sql.
Collection, choix de la vitrine, vitrines des profils. Les Aurore gardent
leur fond ; sans photo, le dessin. Sans le SQL : le dessin partout.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)
js = lire('app.js')
assert 'terra_photos_moi' not in js, u'patch171 deja applique'
js = rempl(js, u"""      <div class="mini-art">${miniArtSvg(e.code, e.tier.id)}<span class="mini-dept">${echapperTexte(e.dept)}</span></div>
      <div class="mini-infos">
        <p class="mini-nom ${e.nom.length > 14 ? 'long' : ''}">${nom}</p>""",
u"""      <div class="mini-art">${e.photo ? artCommune(e, e.tier.id, 'mini') : miniArtSvg(e.code, e.tier.id)}<span class="mini-dept">${echapperTexte(e.dept)}</span></div>
      <div class="mini-infos">
        <p class="mini-nom ${e.nom.length > 14 ? 'long' : ''}">${nom}</p>""", 'mini')
js = rempl(js, u"""  // patch170 : les Aurore venues du Front S1""", u"""  // patch171 : les photos (par pages : une collection depasse 1000 cartes)
  try{
    const { data: ph, error: ep } = await toutesLesLignes(() => sb.rpc('terra_photos_moi'), 'code');
    if(!ep) for(const p of ph || []){ const e = terraCollection.get(p.code); if(e){ e.photo = p.photo; e.photoAuteur = p.auteur; e.photoLicence = p.licence; e.photoSource = p.source; } }
  }catch(err){}
  // patch170 : les Aurore venues du Front S1""", 'collection')
js = rempl(js, u"""  let s1 = new Set();   // patch170""", u"""  const photos = new Map();   // patch171
  try{
    const codes = (data || []).map(r => r.code);
    if(codes.length){ const r3 = await sb.rpc('terra_photos', { p_codes: codes }); if(!r3.error) for(const p of r3.data || []) photos.set(p.code, p.photo); }
  }catch(err){}
  let s1 = new Set();   // patch170""", 'vitrine1')
js = rempl(js, u"""aurore: r.aurore ? 1 : 0, auroreS1: s1.has(r.code) }));""",
u"""aurore: r.aurore ? 1 : 0, auroreS1: s1.has(r.code), photo: photos.get(r.code) || '' }));""", 'vitrine2')
ecrire('app.js', js)
print(u'patch171 applique. Lancer : python3 maj-version.py')
