# -*- coding: utf-8 -*-
u"""
patch159 — dos de carte OG « Nacre » et paquet assorti (apercu valide le
25 octobre). SQL : _sql/dos-og.sql (offre le dos aux 48 OG).
- body[data-dos="og"] : fond nacre, liseré et coins holographiques,
  hexagone OG a la place de l'epingle, mention SAISON 1, reflet lent.
- Le paquet suit le dos : nacre + hexagone OG ; bande holographique pour le
  gratuit, doree pour l'achete.
- Boutique : « Mettre » devient « Équiper », « Sur tes cartes » devient
  « Équipé ». Un message, une seule fois par appareil, previent les OG.
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
assert 'paquet-hexa' not in js, u'patch159 deja applique'
js = rempl(js, u"""function paquetMotifSvg(type){
  const achete = type === 'achete';
  const clair = achete ? '#FCE38A' : '#3B6FB8';
  const moyen = achete ? '#F0B429' : '#1D3F72';
  const fonce = achete ? '#9A6412' : '#0B1D38';
  const trait = achete ? 'rgba(90,55,5,0.28)' : 'rgba(169,210,255,0.22)';""",
u"""function paquetMotifSvg(type){
  const achete = type === 'achete', og = type === 'og';   // patch159 : nacre OG
  const clair = og ? '#F4F1FF' : achete ? '#FCE38A' : '#3B6FB8';
  const moyen = og ? '#D9D3F2' : achete ? '#F0B429' : '#1D3F72';
  const fonce = og ? '#A79FCF' : achete ? '#9A6412' : '#0B1D38';
  const trait = og ? 'rgba(91,74,158,0.22)' : achete ? 'rgba(90,55,5,0.28)' : 'rgba(169,210,255,0.22)';""", 'motif')
js = rempl(js, u"""  const motif = paquetMotifSvg(type);
  const pack = document.createElement('button');
  pack.className = 'paquet ' + (type === 'achete' ? 'achete' : 'gratuit');""",
u"""  const og = document.body.dataset.dos === 'og';   // patch159 : le paquet suit le dos OG
  const motif = paquetMotifSvg(og ? 'og' : type);
  const pack = document.createElement('button');
  pack.className = 'paquet ' + (type === 'achete' ? 'achete' : 'gratuit') + (og ? ' og' : '');""", 'paquet')
js = rempl(js, u"""      <div class="paquet-etiquette">${ICONE_EPINGLE}<span class="paquet-titre">Paquet</span></div>""",
u"""      <div class="paquet-etiquette">${og ? '<span class="paquet-hexa"><b>OG</b></span>' : ICONE_EPINGLE}<span class="paquet-titre">Paquet</span></div>""", 'etiquette')
js = rempl(js, u"""    if(equipe) action = `<span class="bq-equipe">Sur tes cartes</span>`;
    else if(a.possede) action = `<button class="bq-btn secondaire" data-bq-mettre="${a.id || ''}">Mettre</button>`;""",
u"""    if(equipe) action = `<span class="bq-equipe">Équipé</span>`;
    else if(a.possede) action = `<button class="bq-btn secondaire" data-bq-mettre="${a.id || ''}">Équiper</button>`;""", 'equiper')
js = rempl(js, u"""Mets-le sur tes cartes depuis la Boutique.""", u"""Équipe-le depuis la Boutique.""", 'message')
js = rempl(js, u"""  boutiqueCache = data;
  appliquerDos(data.dos);
  renderBoutique();
}
function bqPrix(n){""", u"""  boutiqueCache = data;
  appliquerDos(data.dos);
  renderBoutique();
  // patch159 : prevenir les OG une fois (par appareil)
  try{
    const og = (data.articles || []).some(a => a.id === 'dos-og' && a.possede);
    if(og && data.dos !== 'dos-og' && localStorage.getItem('tf-dos-og-vu') !== '1'){
      localStorage.setItem('tf-dos-og-vu', '1');
      notifier({ type: 'succes', titre: 'Merci d\\'avoir joué la saison 1 !',
                 texte: 'Ton dos de carte OG t\\'attend dans la Boutique : touche « Équiper ».' });
    }
  }catch(e){}
}
function bqPrix(n){""", 'annonce')
ecrire('app.js', js)

HOLO = u"linear-gradient(115deg, #8FF3FF 0%, #C7A6FF 28%, #FFB7E3 46%, #FFE7A3 64%, #9CF7C9 82%, #8FF3FF 100%)"
SAISON = (u"url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='14'%3E%3Ctext x='60' y='11' "
          u"text-anchor='middle' font-family='Arial Narrow,Arial,sans-serif' font-size='10' letter-spacing='3' fill='%235B4A9E'%3ESAISON 1%3C/text%3E%3C/svg%3E\")")
OG = u'body[data-dos="og"] .face-back:not(.bq-dos-apercu .face-back), .bq-dos-apercu[data-dos="og"] .face-back'
def og(suffixe):
    return u', '.join(s + suffixe for s in OG.split(u', '))
css = lire('style.css')
css = rempl(css, u"/* patch115 : l'astuce sous la recherche d'echange */", u"""/* ---------- patch159 : le dos OG « Nacre » et son paquet ---------- */
body[data-dos="og"], .bq-dos-apercu[data-dos="og"]{
  --dos-fond: """ + SAISON + u""" center bottom 22px / 120px 14px no-repeat,
              radial-gradient(circle at 50% 42%, #F4F1FF 0%, #D9D3F2 55%, #A79FCF 100%);
  --dos-liseret: rgba(91,74,158,0.5); --dos-embleme: #F4F1FF; --dos-or: #5B4A9E; --dos-anneau: rgba(167,159,207,0.9);
}
""" + og(u'::before') + u"""{
  border-color: transparent; background: """ + HOLO + u""" border-box; background-size: 220% 220%;
  -webkit-mask: linear-gradient(#000 0 0) padding-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) padding-box, linear-gradient(#000 0 0); mask-composite: exclude;
  animation: ogHolo 6s ease-in-out infinite;
}
""" + og(u' .dos-coin') + u"""{ background: linear-gradient(115deg, #8FF3FF, #C7A6FF, #FFB7E3, #FFE7A3); opacity: 1; }
""" + og(u' .dos-motif') + u"""{
  background: linear-gradient(105deg, transparent 38%, rgba(143,243,255,.6) 46%, rgba(255,183,227,.6) 52%, rgba(255,231,163,.5) 56%, transparent 64%);
  background-size: 300% 100%; mix-blend-mode: soft-light; animation: ogReflet 5s ease-in-out infinite;
}
""" + og(u' .dos-motif path') + u"""{ stroke: rgba(91,74,158,0.2); }
""" + og(u' .dos-embleme') + u"""{
  width: 74px; height: 84px; margin: -42px 0 0 -37px; border-radius: 0; box-shadow: none;
  clip-path: polygon(50% 0, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
  background: """ + HOLO + u"""; background-size: 220% 220%; animation: ogHolo 6s ease-in-out infinite;
}
""" + og(u' .dos-embleme::before') + u"""{ content: ""; position: absolute; inset: 4px; clip-path: inherit; background: #F4F1FF; }
""" + og(u' .dos-embleme::after') + u"""{
  content: "OG"; position: relative; font-family: var(--titre); font-weight: 900; font-size: 28px; letter-spacing: .02em;
  background: linear-gradient(115deg, #3D6BFF, #8A4DFF 40%, #E0479E 70%, #D98A00); -webkit-background-clip: text; background-clip: text; color: transparent;
}
""" + og(u' .dos-embleme svg') + u"""{ display: none; }
@keyframes ogReflet{ 0%{ background-position: 100% 0; } 55%, 100%{ background-position: 0% 0; } }
.paquet.og .paquet-etiquette{ color: #3D2E7A; }
.paquet .paquet-hexa{ width: 40px; height: 46px; display: grid; place-items: center; position: relative;
  clip-path: polygon(50% 0, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
  background: """ + HOLO + u"""; background-size: 220% 220%; animation: ogHolo 6s ease-in-out infinite; }
.paquet .paquet-hexa::before{ content: ""; position: absolute; inset: 3px; clip-path: inherit; background: #F4F1FF; }
.paquet .paquet-hexa b{ position: relative; font-family: var(--titre); font-weight: 900; font-size: 15px; color: #5B4A9E; }
.paquet.og.gratuit .paquet-bande{ background: """ + HOLO.replace(u'115deg', u'90deg') + u"""; background-size: 220% 100%; color: #2A1F5C;
  animation: ogHolo 6s ease-in-out infinite; }
.paquet.og.achete .paquet-bande{ background: linear-gradient(90deg, #B7791F, #FCE38A 30%, var(--c-legendaire) 55%, #B7791F); color: var(--encre); }
@media (prefers-reduced-motion: reduce){
  """ + og(u' .dos-motif') + u""", """ + og(u'::before') + u""", """ + og(u' .dos-embleme') + u""",
  .paquet .paquet-hexa, .paquet.og.gratuit .paquet-bande{ animation: none; }
}

/* patch115 : l'astuce sous la recherche d'echange */""", 'css')
ecrire('style.css', css)
print(u'patch159 applique. Lancer : python3 maj-version.py')
