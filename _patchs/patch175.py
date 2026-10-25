# -*- coding: utf-8 -*-
u"""
patch175 — boutique en euros et garde-robe (25 octobre 2026, aperçu
« Boutique en euros » validé : « OK très bien »).

- Boutique : un volet « Objets TerraFront » à côté de « Avec mes points ».
  Il n'apparaît qu'aux joueurs qui peuvent acheter (euros_catalogue().
  peut_acheter : testeurs tant que la boutique n'est pas ouverte).
  Bandeau de financement, objets OG, habillages, dos, « Mes achats » avec
  « Changer d'avis » pour une livraison à 14 jours.
- Fiche d'achat : livraison tout de suite (deux cases de renonciation) ou
  dans 14 jours, date de naissance au premier achat, plafond des mineurs,
  CGV, bouton « Payer et recevoir l'objet » -> fonction Edge creer-paiement
  -> page Stripe. Retour ?paiement=ok / ?paiement=annule.
- Profil › Personnaliser : dos de carte et habillage de paquet possédés
  (Équipé / Équiper), Ma vitrine, « Voir la boutique ».
- Habillage de paquet réglé à part du dos (SQL 6-garde-robe.sql). Sans ce
  SQL, l'ancien comportement reste : le paquet Nacre suit le dos OG.
- Les 8 habillages en euros reprennent le dessin WebGL validé le 18 octobre
  (aperçu « Paquets et dos OG »), surface du paquet seulement ; les textes,
  l'emblème et l'ouverture restent ceux du jeu. Sans WebGL 2 : un fond CSS.
- Dos OG Prisme et Constellation en CSS (comme le Nacre).
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

# =============================================================== index.html
html = lire('index.html')
assert 'panel-boutiqueeuros' not in html, u'patch175 deja applique'

html = rempl(html, u"""      <h1>Boutique</h1>
      <div class="sub">Dépense tes points Terra : paquets spéciaux et dos de cartes. Tout s'achète en points, rien en euros.</div>""",
u"""      <h1>Boutique</h1>
      <div class="volets" id="bqVolets" role="tablist" aria-label="Boutique" hidden>
        <button type="button" class="volet actif" data-volet="boutique" role="tab" aria-selected="true">Avec mes points</button>
        <button type="button" class="volet" data-volet="boutiqueeuros" role="tab" aria-selected="false">Objets TerraFront</button>
      </div>
      <div class="sub">Dépense tes points Terra : paquets spéciaux et dos de cartes.</div>""", 'boutique volets')

html = rempl(html, u"""
    <section class="tab-panel" id="panel-bourse">""", u"""
    <section class="tab-panel" id="panel-boutiqueeuros">
      <h1>Boutique</h1>
      <div class="volets" role="tablist" aria-label="Boutique">
        <button type="button" class="volet" data-volet="boutique" role="tab" aria-selected="false">Avec mes points</button>
        <button type="button" class="volet actif" data-volet="boutiqueeuros" role="tab" aria-selected="true">Objets TerraFront</button>
      </div>
      <div class="sub">Des objets d'apparence, payés en euros. Ils ne changent jamais le contenu des paquets ni tes chances, et restent associés à ton compte.</div>
      <div id="bqeCorps"><p class="collection-empty">Chargement…</p></div>
    </section>

    <section class="tab-panel" id="panel-bourse">""", 'panel euros')

html = rempl(html, u"""        Succès
      </div>
      <button class="tab tab-plus" id="btnPlus\"""", u"""        Succès
      </div>
      <div class="tab onglet-fusionne" data-tab="boutiqueeuros" aria-hidden="true"><div class="icon"></div>Boutique</div>
      <div class="tab onglet-fusionne" data-tab="personnaliser" aria-hidden="true"><div class="icon"></div>Personnaliser</div>
      <button class="tab tab-plus" id="btnPlus\"""", 'onglets caches')

html = rempl(html, u"""        <button type="button" class="volet" data-volet="succes" role="tab" aria-selected="false">Succès</button>
      </div>
      <div class="sub">Ton niveau monte""", u"""        <button type="button" class="volet" data-volet="succes" role="tab" aria-selected="false">Succès</button>
        <button type="button" class="volet" data-volet="personnaliser" role="tab" aria-selected="false">Personnaliser</button>
      </div>
      <div class="sub">Ton niveau monte""", 'volet profil')

html = rempl(html, u"""        <button type="button" class="volet actif" data-volet="succes" role="tab" aria-selected="true">Succès</button>
      </div>""", u"""        <button type="button" class="volet actif" data-volet="succes" role="tab" aria-selected="true">Succès</button>
        <button type="button" class="volet" data-volet="personnaliser" role="tab" aria-selected="false">Personnaliser</button>
      </div>""", 'volet succes')

html = rempl(html, u"""
    <section class="tab-panel" id="panel-regles">""", u"""
    <section class="tab-panel" id="panel-personnaliser">
      <h1>Profil</h1>
      <div class="volets" role="tablist" aria-label="Profil">
        <button type="button" class="volet" data-volet="profil" role="tab" aria-selected="false">Profil</button>
        <button type="button" class="volet" data-volet="succes" role="tab" aria-selected="false">Succès</button>
        <button type="button" class="volet actif" data-volet="personnaliser" role="tab" aria-selected="true">Personnaliser</button>
      </div>
      <div class="sub">Ce que tu possèdes, en Terra comme sur le Front. Change-le quand tu veux.</div>
      <div id="grCorps"><p class="collection-empty">Chargement…</p></div>
    </section>

    <section class="tab-panel" id="panel-regles">""", 'panel personnaliser')
ecrire('index.html', html)

# =============================================================== app.js
js = lire('app.js')
assert 'patch175' not in js, u'patch175 deja applique'

js = rempl(js, u"""const ONGLETS_FUSIONNES = ['defense', 'succes', 'cdj', 'radar', 'rafale'];""",
u"""const ONGLETS_FUSIONNES = ['defense', 'succes', 'cdj', 'radar', 'rafale', 'boutiqueeuros', 'personnaliser'];""", 'fusionnes')
js = rempl(js, u"""const ONGLET_PARENT = { defense: 'combat', succes: 'profil', cdj: 'qg', radar: 'qg', rafale: 'qg' };""",
u"""const ONGLET_PARENT = { defense: 'combat', succes: 'profil', cdj: 'qg', radar: 'qg', rafale: 'qg', boutiqueeuros: 'boutique', personnaliser: 'profil' };""", 'parents')

js = rempl(js, u"""    if(tab.dataset.tab === 'boutique') loadBoutique();
""", u"""    if(tab.dataset.tab === 'boutique') loadBoutique();
    if(tab.dataset.tab === 'boutiqueeuros') loadBoutiqueEuros();   // patch175
    if(tab.dataset.tab === 'personnaliser') loadGardeRobe();
""", 'onglets charger')

js = rempl(js, u"""  boutiqueCache = data;
  appliquerDos(data.dos);
  renderBoutique();
  // patch159""", u"""  boutiqueCache = data;
  appliquerDos(data.dos);
  // patch175 : l'habillage de paquet se regle a part ; sans le SQL 6, le paquet Nacre suit le dos OG
  appliquerHabillage(data.habillage === undefined ? (data.dos === 'dos-og' ? 'nacre' : null) : data.habillage);
  bqeVerifierAcces();
  renderBoutique();
  // patch159""", 'loadBoutique')

js = rempl(js, u"""  const og = document.body.dataset.dos === 'og';   // patch159 : le paquet suit le dos OG
  const motif = paquetMotifSvg(og ? 'og' : type);
  const pack = document.createElement('button');
  pack.className = 'paquet ' + (type === 'achete' ? 'achete' : 'gratuit') + (og ? ' og' : '');""",
u"""  // patch175 : l'habillage choisi dans la garde-robe (Nacre : patch159)
  const hab = document.body.dataset.habillage || '';
  const og = hab === 'nacre';
  const gl = HAB_PAQ[hab] != null;
  const motif = gl ? habCanvas(hab, false) : paquetMotifSvg(og ? 'og' : type);
  const embleme = og || hab.startsWith('og-') ? '<span class="paquet-hexa"><b>OG</b></span>'
    : hab === 'kraft' ? '<span class="paquet-cachet" aria-hidden="true">' + ICONE_EPINGLE + '</span>' : ICONE_EPINGLE;
  const pack = document.createElement('button');
  pack.className = 'paquet ' + (type === 'achete' ? 'achete' : 'gratuit') + (og ? ' og' : '') + (gl ? ' hab hab-' + hab : '');""", 'makePackEl')
js = rempl(js, u"""      <div class="paquet-etiquette">${og ? '<span class="paquet-hexa"><b>OG</b></span>' : ICONE_EPINGLE}<span class="paquet-titre">Paquet</span></div>""",
u"""      <div class="paquet-etiquette">${embleme}<span class="paquet-titre">Paquet</span></div>""", 'etiquette')
js = rempl(js, u"""    <span class="coupe-consigne" aria-hidden="true">Touche le paquet · ou coupe les pointillés</span>`;
  return pack;
}""", u"""    <span class="coupe-consigne" aria-hidden="true">Touche le paquet · ou coupe les pointillés</span>`;
  if(gl) setTimeout(() => habGl.demarrer(), 0);
  return pack;
}""", 'makePackEl fin')

js = rempl(js, u"""    [/Tu ne peux pas attaquer un membre de ton clan/i, 'Tu ne peux pas attaquer un membre de ton clan.'],
  ];""", u"""    [/Tu ne peux pas attaquer un membre de ton clan/i, 'Tu ne peux pas attaquer un membre de ton clan.'],
    // patch175 : boutique en euros
    [/La boutique ouvre bientot/i, 'La boutique ouvre bientôt.'],
    [/Article introuvable/i, 'Cet objet n\\'est pas en vente pour le moment.'],
    [/Les conditions de vente ont change/i, 'Les conditions de vente ont changé : recharge la page.'],
    [/Coche l'acceptation des conditions de vente/i, 'Coche l\\'acceptation des conditions de vente.'],
    [/Pour recevoir l'objet tout de suite, coche les deux cases/i, 'Pour recevoir l\\'objet tout de suite, coche les deux cases.'],
    [/Cet objet est reserve aux joueurs OG/i, 'Cet objet est réservé aux joueurs OG.'],
    [/Tu as deja paye cet objet, il arrive bientot/i, 'Tu as déjà payé cet objet : il arrive bientôt.'],
    [/Indique ta date de naissance/i, 'Indique ta date de naissance.'],
    [/Date de naissance invalide/i, 'Date de naissance invalide.'],
    [/La boutique est reservee aux joueurs de (\\d+) ans/i, (x) => `La boutique est ouverte à partir de ${x[1]} ans.`],
    [/Plafond de ([\\d,]+) € par mois atteint pour les moins de 18 ans \\(reste ([\\d,]+) €\\)/i, (x) => `Avant 18 ans, c'est ${x[1]} € par mois au plus : il te reste ${x[2]} € ce mois-ci.`],
    [/Le delai de 14 jours est passe ou l'objet est deja livre/i, 'Le délai de 14 jours est passé, ou l\\'objet est déjà livré.'],
    [/Commande introuvable/i, 'Commande introuvable.'],
  ];""", 'messages')

js = rempl(js, u"""  if(SAISON2) loadBoutique(true);   // patch107 : le dos de carte choisi
""", u"""  if(SAISON2) loadBoutique(true);   // patch107 : le dos de carte choisi
  if(SAISON2) bqeRetourPaiement();   // patch175 : retour de la page de paiement Stripe
""", 'init')

js += u"""

// ---------- patch175 : boutique en euros, garde-robe, habillages de paquet ----------
// Les habillages en euros : dessin WebGL du 18 octobre (aperçu « Paquets et dos OG »),
// surface du paquet seulement. Un seul canevas WebGL hors écran dessine, puis on recopie
// l'image dans les canevas des paquets (languette et corps). Un dessin par habillage
// et par image, et seulement pour les paquets visibles.
const HAB_PAQ = { 'og-prisme': 2, 'og-or-noir': 3, kraft: 4, lave: 5, neon: 6, comete: 7, maree: 8, orage: 9 };
function habCle(id){ return !id ? '' : id === 'nacre' ? 'nacre' : String(id).replace(/^og-paquet-/, 'og-').replace(/^paquet-/, ''); }
function habCanvas(hab, fixe, w, h){
  return `<canvas class="paquet-motif paquet-gl" data-hab="${hab}"${fixe ? ' data-fixe="1"' : ''} width="${w || 400}" height="${h || 560}" aria-hidden="true"></canvas>`;
}
function appliquerHabillage(id){
  const avant = document.body.dataset.habillage || '';
  const k = habCle(id);
  document.body.dataset.habillage = k;
  if(avant !== k && !paquetEnCours){
    const zone = document.getElementById('packZone');
    if(zone && zone.querySelector('.paquet[data-pret]')){ zone.innerHTML = ''; afficherPaquetPret('gratuit'); }
  }
}

const HAB_GLSL = `#version 300 es
precision highp float;
uniform vec2 u_res; uniform float u_time; uniform vec2 u_tilt; uniform int u_paq;
out vec4 fragColor;
const float PI=3.14159265, TAU=6.28318531;
float UPX=.01;
const float PH=1.5; const float PW=1.5*200./280.; const float YT=.75;
float h21(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
vec2 h22(vec2 p){ float n=h21(p); return vec2(n,h21(p+n+.17)); }
float vnoise(vec2 p){ vec2 i=floor(p),f=fract(p); vec2 u=f*f*(3.-2.*f);
  return mix(mix(h21(i),h21(i+vec2(1.,0.)),u.x),mix(h21(i+vec2(0.,1.)),h21(i+vec2(1.,1.)),u.x),u.y); }
float fbm(vec2 p){ float v=0.,a=.5; mat2 m=mat2(1.6,1.2,-1.2,1.6); for(int i=0;i<4;i++){ v+=a*vnoise(p); p=m*p+3.1; a*=.5; } return v; }
float fbm3(vec2 p){ float v=0.,a=.5; mat2 m=mat2(1.6,1.2,-1.2,1.6); for(int i=0;i<3;i++){ v+=a*vnoise(p); p=m*p+3.1; a*=.5; } return v; }
vec3 spectral(float x){ return .5+.5*cos(TAU*(x+vec3(0.,.33,.67))); }
float lineW(float d,float w){ return clamp((w-abs(d))/UPX+.5,0.,1.); }
vec3 fire(float x){ return vec3(.9,.12,.02)*smoothstep(0.,.35,x)+vec3(.1,.35,.05)*smoothstep(.3,.7,x)+vec3(0.,.35,.25)*smoothstep(.65,1.05,x)+vec3(0.,0.,.35)*smoothstep(1.,1.4,x); }
vec3 Ldir(float t){ return normalize(vec3(u_tilt.x*1.3+.3*cos(t*.5)-.15,-u_tilt.y*1.3+.3*sin(t*.5)+.35,.9)); }
float sdBox(vec2 p,vec2 b,float r){ vec2 d=abs(p)-b+r; return length(max(d,0.))+min(max(d.x,d.y),0.)-r; }
float crH(vec2 p){ return abs(fbm3(p*3.4)-.5)*1.4+fbm3(p*10.)*.22; }
vec3 froisse(vec2 q,float k){ float e=.006; float h0=crH(q), hx=crH(q+vec2(e,0.)), hy=crH(q+vec2(0.,e)); return vec3(-(hx-h0)/e,-(hy-h0)/e,0.)*k; }
float anneaux(vec2 q,float n){ vec2 c=q-vec2(-.12,.1); float r=length(c*vec2(1.,.82)); float a=atan(c.y,c.x); float f=r*n+.35*sin(3.*a+1.)+.2*sin(5.*a-2.); return 1.-smoothstep(.0,1.3,abs(fract(f)-.5)/max(fwidth(f),1e-4)); }
float caustic(vec2 p0,float t){ vec2 p=p0-250.; vec2 i=p; float c=1.; float inten=.005;
  for(int n=0;n<5;n++){ float tt=t*(1.-3.5/float(n+1)); i=p+vec2(cos(tt-i.x)+sin(tt+i.y),sin(tt-i.y)+cos(tt+i.x));
    c+=1./length(vec2(p.x/(sin(i.x+tt)/inten),p.y/(cos(i.y+tt)/inten))); }
  c/=5.; c=1.17-pow(c,1.4); return pow(abs(c),8.); }
vec3 matiere(vec2 q,float t){
  vec2 uv=vec2((q.x+PW*.5)/PW,(YT-q.y)/PH);
  vec3 Ld=Ldir(t);
  float kf=u_paq==2?.7:(u_paq==3?.55:(u_paq==4?.12:(u_paq==5?.2:(u_paq==8?.3:.9))));
  vec3 Nf=froisse(q,.06*kf);
  float sx=2.*uv.x-1.; Nf.x+=sx*sx*sx*.55;
  float crimp=max(1.-smoothstep(.0,.07,uv.y),smoothstep(.93,1.,uv.y));
  Nf.y+=sin(uv.y*PH*260.)*.35*crimp;
  vec3 N=normalize(vec3(Nf.xy,1.));
  float shin=u_paq==4?6.:(u_paq==5?10.:40.);
  float dif=max(dot(N,Ld),0.), sp=pow(max(reflect(-Ld,N).z,0.),shin);
  float rg=anneaux(q,13.);
  vec3 col;
  if(u_paq==2){ float ph=dot(N.xy,vec2(1.8,1.2))*.55+uv.x*.8+uv.y*.55+u_tilt.x*.8+u_tilt.y*.4+t*.05;
    col=mix(vec3(.8,.82,.9),spectral(ph),.72)*(.6+.5*dif)+sp*1.1; col=mix(col,vec3(1.),rg*.3);
    vec2 id=floor(q*24.); vec2 h=h22(id+6.); vec2 dv=(q*24.-id-.2-h*.6)/24.;
    float on=step(.8,h.x)*smoothstep(.88,1.,sin(t*1.7+h.y*TAU+dot(u_tilt,h-.5)*12.));
    col+=on*(exp(-dot(dv,dv)*40000.)*1.4+(exp(-abs(dv.x)*900.)*exp(-abs(dv.y)*90.)+exp(-abs(dv.y)*900.)*exp(-abs(dv.x)*90.))*.6); }
  else if(u_paq==3){ col=vec3(.035,.035,.045)*(.6+.6*dif)+sp*vec3(1.,.93,.75)*1.2; float env=pow(.5+.5*sin(N.x*6.+N.y*3.+t*.3+u_tilt.x*2.),6.); col+=vec3(.3,.25,.15)*env*.5;
    col=mix(col,vec3(.95,.72,.28)*(.6+.6*dif),rg*.75); }
  else if(u_paq==4){
    float fib=fbm(q*vec2(70.,9.))*.5+fbm(q*vec2(9.,70.))*.3; float spk=step(.975,h21(floor(q*260.)));
    col=vec3(.7,.54,.35)*(.8+.28*fib)*(.86+.2*dif)-spk*.14;
    col=mix(col,vec3(.3,.18,.08),rg*.5*(.55+.45*fbm(q*30.))); }
  else if(u_paq==5){
    float n=fbm(q*3.2+vec2(0.,-t*.05)); float cr=abs(fbm(q*3.6+3.)-.5); float vein=1.-smoothstep(0.,.022,cr);
    float calme=1.-.75*(1.-smoothstep(.03,.2,abs(q.y)))*(1.-smoothstep(.45,.6,abs(q.x)));
    float pulse=.75+.25*sin(t*2.+q.y*3.);
    col=vec3(.075,.06,.055)*(.55+.7*dif)+sp*.12;
    col+=fire((vein*(.8+.5*n)+rg*.22)*pulse*1.1*calme); }
  else if(u_paq==6){
    col=mix(vec3(.05,.02,.1),vec3(.1,.03,.17),uv.y)*(.7+.4*dif)+sp*.3; col+=vec3(.13,.89,1.)*rg*.14;
    float ed=sdBox(q,vec2(PW*.5-.065,PH*.5-.12),.07); float fl=.85+.15*sin(t*11.)*step(.95,fract(t*.31));
    vec3 tc=mix(vec3(1.,.17,.84),vec3(.13,.89,1.),.5+.5*sin(atan(q.y,q.x)*2.-t*1.2));
    col+=tc*(exp(-pow(ed/.011,2.))*1.2+exp(-abs(ed)/.045)*.35)*fl+vec3(1.)*exp(-pow(ed/.004,2.))*.5*fl;
    col*=.9+.1*step(.5,fract(gl_FragCoord.y/3.)); }
  else if(u_paq==7){
    col=mix(vec3(.02,.04,.12),vec3(.08,.13,.32),1.-uv.y*.8)*(.8+.3*dif)+sp*.45;
    col+=vec3(.32,.2,.62)*pow(fbm(q*2.+t*.02),3.)*1.3;
    vec2 sq=q*34.; vec2 id=floor(sq); vec2 h=h22(id); float d=length(sq-id-.2-h*.6);
    col+=step(.78,h.x)*exp(-d*d*14.)*(.5+.5*sin(t*(1.5+h.y*3.)+h.y*40.))*vec3(.9,.95,1.);
    float P=4.5, ph=mod(t,P)/P; vec2 A=vec2(-.75,.8), B=vec2(.75,-.35); vec2 hp=mix(A,B,ph/.4);
    if(ph<.42){ vec2 dir=normalize(A-B); vec2 lq=q-hp; float al=dot(lq,dir), pe=dot(lq,vec2(-dir.y,dir.x));
      if(al>0.){ float w=.006+al*.03; col+=vec3(.75,.88,1.)*exp(-al*2.2)*exp(-pe*pe/(w*w))*1.3; }
      float hl=length(lq); col+=vec3(1.)*(exp(-hl*hl*6000.)*1.6+.2/(1.+hl*hl*900.)); }
    col=mix(col,vec3(.8,.86,1.),rg*.18); }
  else if(u_paq==8){
    float ca=caustic(q*2.6,t*.45);
    col=mix(vec3(.04,.34,.46),vec3(.1,.62,.72),1.-uv.y)*(.72+.32*dif)+vec3(.6,.95,1.)*ca*.45+sp*1.3;
    vec2 bq=q-vec2(0.,t*.12); vec2 id=floor(bq/.07); vec2 h=h22(id+2.); vec2 bc=(id+.2+h*.6)*.07; float bd=length(bq-bc); float rr=.006+h.x*.01;
    col+=step(.72,h.y)*lineW(bd-rr*.8,.0018)*.6;
    col=mix(col,vec3(.85,1.,1.),rg*.22); }
  else {
    float P=3.7; float cy=floor(t/P), ph=t-cy*P;
    float fl=smoothstep(0.,.02,ph)*(1.-smoothstep(.06,.14,ph))+.6*smoothstep(.2,.22,ph)*(1.-smoothstep(.28,.38,ph));
    float cl=fbm(q*2.4+vec2(t*.06,0.));
    col=mix(vec3(.07,.09,.14),vec3(.3,.35,.46),smoothstep(.35,.8,cl))*(.75+.35*dif)*(1.+fl*1.5)+sp*.2;
    float bx=(h21(vec2(cy,1.))-.5)*.5+(fbm3(vec2(q.y*2.2,cy))-.5)*.4; float bd=abs(q.x-bx);
    col+=vec3(.82,.9,1.)*(exp(-pow(bd/.006,2.))*1.6+exp(-bd/.04)*.3)*fl*step(-.1,q.y);
    vec2 rq=mat2(cos(.2),-sin(.2),sin(.2),cos(.2))*q; float cw=.02; float cx=floor(rq.x/cw); float hh=h21(vec2(cx,4.));
    float seg=fract((rq.y+t*1.6+hh*7.)/.22); col+=vec3(.6,.7,.85)*step(.5,hh)*(1.-smoothstep(0.,.16,seg))*smoothstep(0.,.02,seg)*exp(-pow((fract(rq.x/cw)-.5)*cw/.0016,2.))*.25;
    col=mix(col,vec3(.75,.82,.95),rg*(.12+.4*fl)); }
  col*=1.-.25*crimp;
  float bord=-sdBox(q,vec2(PW*.5,PH*.5),.0); col*=.85+.15*smoothstep(0.,.03,bord);
  return col;
}
void main(){
  vec2 uv=gl_FragCoord.xy/u_res; uv.y=1.-uv.y; UPX=PH/u_res.y;
  vec2 q=vec2((uv.x-.5)*PW, YT-uv.y*PH);
  fragColor=vec4(clamp(matiere(q,u_time),0.,1.),1.);
}`;

const habGl = (() => {
  let gl = null, essaye = false, enMarche = false, toile = null, prog = null, loc = {}, echelle = 1, couts = [], avant = 0;
  const reduit = matchMedia('(prefers-reduced-motion: reduce)').matches;
  function init(){
    if(essaye) return !!gl;
    essaye = true;
    try{
      toile = document.createElement('canvas');
      gl = toile.getContext('webgl2', { alpha: false, antialias: false, depth: false, stencil: false, premultipliedAlpha: false, powerPreference: 'low-power' });
      if(!gl) return false;
      const sh = (type, src) => { const o = gl.createShader(type); gl.shaderSource(o, src); gl.compileShader(o);
        if(!gl.getShaderParameter(o, gl.COMPILE_STATUS)){ console.error('habillage', gl.getShaderInfoLog(o)); return null; } return o; };
      const vs = sh(gl.VERTEX_SHADER, '#version 300 es\\nin vec2 p; void main(){ gl_Position=vec4(p,0.,1.); }');
      const fs = sh(gl.FRAGMENT_SHADER, HAB_GLSL);
      if(!vs || !fs){ gl = null; return false; }
      prog = gl.createProgram(); gl.attachShader(prog, vs); gl.attachShader(prog, fs); gl.bindAttribLocation(prog, 0, 'p'); gl.linkProgram(prog);
      if(!gl.getProgramParameter(prog, gl.LINK_STATUS)){ gl = null; return false; }
      gl.useProgram(prog);
      const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
      gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
      for(const n of ['u_res', 'u_time', 'u_tilt', 'u_paq']) loc[n] = gl.getUniformLocation(prog, n);
      document.addEventListener('visibilitychange', () => { if(!document.hidden) demarrer(); });
    }catch(e){ gl = null; }
    return !!gl;
  }
  function rendre(hab, t, w, h){
    if(toile.width !== w || toile.height !== h){ toile.width = w; toile.height = h; }
    gl.viewport(0, 0, w, h);
    gl.uniform2f(loc.u_res, w, h); gl.uniform1f(loc.u_time, t); gl.uniform1i(loc.u_paq, HAB_PAQ[hab]);
    gl.uniform2f(loc.u_tilt, reduit ? .15 : Math.sin(t * .7) * .45, reduit ? -.1 : Math.sin(t * .53 + 1) * .3);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }
  function image(now){
    const toutes = [...document.querySelectorAll('canvas.paquet-gl:not([data-fait])')];
    if(!toutes.length || document.hidden){ enMarche = false; return; }
    const t = reduit ? 2.4 : now / 1000;
    const groupes = new Map();
    for(const c of toutes){
      const r = c.getBoundingClientRect();
      if(!r.width || r.bottom < 0 || r.top > innerHeight) continue;   // cache ou hors de l'ecran
      const cle = c.dataset.hab + '|' + (c.dataset.fixe ? 1 : 0) + '|' + c.width;
      if(!groupes.has(cle)) groupes.set(cle, []);
      groupes.get(cle).push(c);
    }
    let anime = false;
    for(const [cle, liste] of groupes){
      const [hab, fixe] = cle.split('|');
      if(HAB_PAQ[hab] == null) continue;
      const w = Math.round(liste[0].width * echelle), h = Math.round(liste[0].height * echelle);
      rendre(hab, fixe === '1' ? 2.4 : t, w, h);
      for(const c of liste){
        const x = c.getContext('2d'); x.drawImage(toile, 0, 0, w, h, 0, 0, c.width, c.height);
        if(fixe === '1' || reduit) c.dataset.fait = '1'; else anime = true;
      }
    }
    // un appareil qui peine : on dessine moins de pixels
    if(anime && avant){ couts.push(now - avant);
      if(couts.length >= 60){ const m = couts.reduce((a, b) => a + b, 0) / couts.length; couts = [];
        if(m > 40 && echelle > .5) echelle -= .25; } }
    avant = anime ? now : 0;
    if(anime) requestAnimationFrame(image);
    else setTimeout(() => requestAnimationFrame(image), groupes.size ? 0 : 400);
  }
  function demarrer(){ if(!init()) return; if(!enMarche){ enMarche = true; avant = 0; requestAnimationFrame(image); } }
  return { demarrer };
})();

// ---------- la boutique en euros ----------
let bqeAcces = null, bqeCat = null, bqeBandeau = null, bqeCommandes = [];
const euros = (c) => (Number(c) / 100).toFixed(2).replace('.', ',') + ' €';
const dateLongue = (d) => new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });
function bqeNomCourt(a){ return String(a.nom || '').replace(/^(Paquet|Dos) (OG )?/, ''); }

async function bqeVerifierAcces(){
  if(bqeAcces === null){
    try{
      const { data, error } = await sb.rpc('euros_catalogue');
      bqeAcces = !error && !!data && data.peut_acheter === true;
      if(bqeAcces) bqeCat = data;
    }catch(e){ bqeAcces = false; }
  }
  const v = document.getElementById('bqVolets');
  if(v) v.hidden = !bqeAcces;
}

async function loadBoutiqueEuros(){
  const corps = document.getElementById('bqeCorps');
  if(!corps) return;
  const [c, b, m] = await Promise.all([sb.rpc('euros_catalogue'), sb.rpc('euros_bandeau'), sb.rpc('euros_mes_commandes')]);
  if(c.error || !c.data){ corps.innerHTML = '<p class="collection-empty">La boutique est indisponible pour le moment.</p>'; return; }
  bqeCat = c.data; bqeBandeau = b.error ? null : b.data; bqeCommandes = m.error ? [] : (m.data || []);
  renderBoutiqueEuros();
}

function bqeBandeauHtml(){
  const b = bqeBandeau;
  if(!b || b.mois_pourcent == null) return '';
  const mois = new Date().toLocaleDateString('fr-FR', { month: 'long' });
  const trois = b.conformite_pourcent != null;
  let etape, titre, pct, note = '';
  if(b.mois_pourcent < 100){ etape = 1; titre = `Objectif de ${mois} · les frais du jeu`; pct = b.mois_pourcent; }
  else if(trois && b.conformite_pourcent < 100){ etape = 2; titre = 'Mise en conformité · juriste, données personnelles, marque'; pct = b.conformite_pourcent; note = `Les frais de ${mois} sont couverts, merci !`; }
  else { etape = trois ? 3 : 2; titre = 'TerraFront sur iPhone et Android'; pct = b.app_pourcent || 0; note = `Les frais de ${mois} sont couverts, merci !`; }
  const nb = trois ? 3 : 2;
  return `<div class="bqe-bandeau">
    <div class="bqe-l1"><b>${titre}</b><span class="bqe-pc">${pct} %</span></div>
    <div class="bqe-barre"><i style="width:${Math.max(0, Math.min(100, pct))}%"></i></div>
    <div class="bqe-etapes" aria-label="Étape ${etape} sur ${nb}">${Array.from({ length: nb }, (_, i) => `<span class="${i < etape ? 'on' : ''}"></span>`).join('')}</div>
    <small>${note ? note + ' ' : ''}Étape ${etape} sur ${nb}. Ce que rapporte la boutique paie d'abord les frais du jeu.</small>
  </div>`;
}

function habVignette(k, w){
  const gl = HAB_PAQ[k] != null;
  return `<div class="hab-vignette" data-hab="${k}"${w ? ` style="width:${w}px"` : ''} aria-hidden="true">${gl ? habCanvas(k, true, 200, 280) : ''}<span class="hv-bande"></span></div>`;
}
function bqeVignette(a){ return a.type === 'dos' ? dosApercuHtml(a.id) : habVignette(habCle(a.id)); }

function bqeCarte(a){
  const attente = !a.possede && a.livraison_le;
  const bas = a.possede ? '<span class="bqe-etat ok">Dans ta garde-robe</span>'
    : attente ? `<span class="bqe-etat">Arrive le ${dateLongue(a.livraison_le)}</span>`
    : `<span class="bq-btn bqe-prix">${euros(a.prix_centimes)}</span>`;
  return `<button type="button" class="bq-article bqe-article" data-bqe="${echapperTexte(a.id)}">
      ${bqeVignette(a)}
      <b>${echapperTexte(bqeNomCourt(a))}</b>
      <p>${echapperTexte(a.description)}</p>
      ${bas}
    </button>`;
}

function bqeCommandeHtml(c){
  let etat = '', action = '';
  if(c.statut === 'livree') etat = `Payé le ${dateLongue(c.payee_le)} · livré`;
  else if(c.statut === 'payee' && c.retractation_le) etat = 'Annulation demandée · tu seras remboursé sous quelques jours';
  else if(c.statut === 'payee'){
    etat = `Payé le ${dateLongue(c.payee_le)} · arrive le ${dateLongue(c.livrer_apres)}`;
    if(c.livraison === 'differee') action = `<button type="button" class="bqe-lien" data-retract="${c.id}">Changer d'avis et être remboursé</button>`;
  }
  else if(c.statut === 'remboursee') etat = 'Remboursé';
  else if(c.statut === 'contestee') etat = 'Paiement contesté auprès de la banque';
  else if(c.statut === 'a_verifier') etat = 'Paiement en cours de vérification';
  return `<div class="bqe-achat"><div><b>${echapperTexte(c.article)} · ${euros(c.prix_centimes)}</b><small>${etat}</small></div>${action}</div>`;
}

function renderBoutiqueEuros(){
  const corps = document.getElementById('bqeCorps');
  const cat = bqeCat;
  if(!corps || !cat) return;
  const arts = (cat.articles || []).filter(a => a.type === 'dos' || a.type === 'habillage');
  const og = arts.filter(a => a.reserve_og);
  const hab = arts.filter(a => !a.reserve_og && a.type === 'habillage');
  const dos = arts.filter(a => !a.reserve_og && a.type === 'dos');
  const section = (titre, mot, liste, badge) => liste.length ? `<div class="bourse-section bq-section">
      <h2>${titre}${badge ? ' <span class="bqe-og">OG</span>' : ''}${mot ? ` <small class="bqe-mot">${mot}</small>` : ''}</h2>
      <div class="bq-grille bq-grille-dos">${liste.map(bqeCarte).join('')}</div></div>` : '';
  corps.innerHTML = bqeBandeauHtml()
    + (cat.ouverte ? '' : '<p class="bqe-test">Mode test : la boutique n\\'est visible que des comptes testeurs. Paie avec une carte de test Stripe.</p>')
    + (cat.og ? section('Réservé aux OG', 'pour les joueurs de la saison 1', og, true) : '')
    + section('Habillages de paquet', 'l\\'emballage de tes paquets', hab)
    + section('Dos de cartes', '', dos)
    + (!arts.length ? '<p class="collection-empty">Rien en vente pour le moment.</p>' : '')
    + (bqeCommandes.length ? `<div class="bourse-section bq-section"><h2>Mes achats</h2><div class="bqe-achats">${bqeCommandes.map(bqeCommandeHtml).join('')}</div></div>` : '')
    + `<p class="bqe-pied">Paiement par Stripe · TerraFront, entrepreneur individuel · <a href="cgv.html" target="_blank" rel="noopener">Conditions de vente</a> · <a href="mentions-legales.html" target="_blank" rel="noopener">Mentions légales</a></p>`;
  habGl.demarrer();
}

function bqeAge(iso){
  const n = new Date(iso + 'T12:00:00'), auj = new Date();
  let a = auj.getFullYear() - n.getFullYear();
  if(auj.getMonth() < n.getMonth() || (auj.getMonth() === n.getMonth() && auj.getDate() < n.getDate())) a--;
  return a;
}

function bqeOuvrirFiche(id){
  const cat = bqeCat;
  const a = cat && (cat.articles || []).find(x => x.id === id);
  if(!a) return;
  if(a.possede){ notifier({ type: 'info', titre: 'Tu l\\'as déjà', texte: 'Il est dans Profil › Personnaliser.' }); return; }
  if(a.livraison_le){ notifier({ type: 'info', titre: 'Déjà payé', texte: 'Il arrive le ' + dateLongue(a.livraison_le) + '.' }); return; }
  const nom = bqeNomCourt(a), prix = euros(a.prix_centimes);
  const date14 = dateLongue(Date.now() + 14 * 86400000);
  const quoi = a.type === 'habillage' ? `<b>l'habillage ${echapperTexte(nom)}</b> sur tous tes paquets` : `<b>le dos ${echapperTexte(nom)}</b> sur toutes tes cartes`;
  const plafondBloque = cat.mineur && cat.plafond_restant != null && Number(cat.plafond_restant) < Number(a.prix_centimes);
  const grand = a.type === 'dos' ? dosApercuHtml(a.id) : `<div class="hab-grand">${habVignette(habCle(a.id), 92).replace('data-fixe="1" ', '')}</div>`;
  const aujourdhui = new Date().toISOString().slice(0, 10);
  const fermer = ouvrirFenetre(`
    <div class="fenetre bqe-fiche" role="dialog" aria-modal="true" aria-labelledby="bqeNom">
      <button type="button" class="bqe-fermer" aria-label="Fermer">×</button>
      <div class="bqe-tete"><div class="bqe-grand">${grand}</div>
        <div><small>${a.type === 'dos' ? 'Dos de carte' : 'Habillage de paquet'}${a.reserve_og ? ' · réservé aux OG' : ''}</small>
          <h2 id="bqeNom">${echapperTexte(nom)}</h2><b class="bqe-gros-prix">${prix}</b></div></div>
      <p class="bqe-recoit">Tu reçois ${quoi}, gardé à vie et associé à ton compte. Ça ne change ni le contenu des paquets ni tes chances. Il ne s'échange pas et ne se revend pas.</p>
      <fieldset class="bqe-liv"><legend>Quand veux-tu le recevoir ?</legend>
        <label><input type="radio" name="bqeLiv" value="immediate" checked><b>Tout de suite</b><span>Tu renonces au délai de rétractation.</span></label>
        <label><input type="radio" name="bqeLiv" value="differee"><b>Le ${date14}</b><span>Tu peux changer d'avis pendant 14 jours.</span></label>
      </fieldset>
      <div class="bqe-cases" id="bqeCasesImm">
        <label class="bqe-case"><input type="checkbox" id="bqeImm"><span>Je demande à recevoir l'objet tout de suite, avant la fin du délai de rétractation de 14 jours.</span></label>
        <label class="bqe-case"><input type="checkbox" id="bqeRen"><span>Je reconnais qu'en le recevant tout de suite, je perds mon droit de rétractation.</span></label>
      </div>
      <p class="bqe-info" id="bqeInfoDiff" hidden>L'objet arrivera le ${date14}. D'ici là, tu peux annuler depuis « Mes achats » et être remboursé en entier.</p>
      ${cat.naissance_connue ? '' : `<div class="bqe-naissance"><label for="bqeNaiss">Ta date de naissance</label>
        <input type="date" id="bqeNaiss" min="1920-01-01" max="${aujourdhui}">
        <p class="bqe-info" id="bqeInfoAge">Demandée une seule fois. Avant 18 ans, les achats sont limités à 15 € par mois.</p></div>`}
      ${plafondBloque ? `<p class="bqe-info rouge">Avant 18 ans, c'est 15 € par mois au plus : il te reste ${euros(cat.plafond_restant)} ce mois-ci.</p>` : ''}
      ${cat.mineur && !plafondBloque ? `<p class="bqe-info">Il te reste ${euros(cat.plafond_restant)} ce mois-ci. Demande l'accord d'un parent avant de payer.</p>` : ''}
      <label class="bqe-case"><input type="checkbox" id="bqeCgv"><span>J'ai lu et j'accepte les <a href="cgv.html" target="_blank" rel="noopener">conditions générales de vente</a>.</span></label>
      <button type="button" class="bqe-payer" id="bqePayer" disabled>Payer et recevoir l'objet · ${prix}</button>
      <p class="bqe-erreur" id="bqeErreur" role="alert" hidden></p>
      <p class="bqe-securite">Tu passes un instant sur la page de paiement sécurisée de Stripe. TerraFront ne voit jamais ta carte bancaire. TVA non applicable, art. 293 B du CGI.</p>
    </div>`);
  const f = document.querySelector('.bqe-fiche');
  if(!f) return;
  f.querySelector('.bqe-fermer').addEventListener('click', () => fermer(null));
  habGl.demarrer();
  const liv = () => f.querySelector('input[name="bqeLiv"]:checked').value;
  const verifier = () => {
    const imm = liv() === 'immediate';
    f.querySelector('#bqeCasesImm').hidden = !imm;
    f.querySelector('#bqeInfoDiff').hidden = imm;
    let ageOk = cat.naissance_connue;
    const n = f.querySelector('#bqeNaiss'), info = f.querySelector('#bqeInfoAge');
    if(n){
      if(!n.value){ info.className = 'bqe-info'; info.textContent = 'Demandée une seule fois. Avant 18 ans, les achats sont limités à 15 € par mois.'; }
      else{
        const age = bqeAge(n.value);
        if(age < 15){ info.className = 'bqe-info rouge'; info.textContent = 'La boutique est ouverte à partir de 15 ans. Tout le jeu reste gratuit.'; }
        else if(age < 18){
          ageOk = Number(a.prix_centimes) <= 1500;
          info.className = 'bqe-info' + (ageOk ? '' : ' rouge');
          info.textContent = ageOk ? 'Avant 18 ans, 15 € par mois au plus. Demande l\\'accord d\\'un parent avant de payer.' : 'Avant 18 ans, 15 € par mois au plus.';
        } else { ageOk = true; info.className = 'bqe-info vert'; info.textContent = 'C\\'est noté, on ne te la redemandera plus.'; }
        if(age < 15) ageOk = false;
      }
    }
    const cases = !imm || (f.querySelector('#bqeImm').checked && f.querySelector('#bqeRen').checked);
    f.querySelector('#bqePayer').disabled = !(cases && ageOk && !plafondBloque && f.querySelector('#bqeCgv').checked);
  };
  f.addEventListener('change', verifier);
  f.addEventListener('input', verifier);
  verifier();
  f.querySelector('#bqePayer').addEventListener('click', async () => {
    const btn = f.querySelector('#bqePayer'), err = f.querySelector('#bqeErreur');
    const imm = liv() === 'immediate';
    const n = f.querySelector('#bqeNaiss');
    btn.disabled = true; btn.textContent = 'Ouverture du paiement sécurisé…'; err.hidden = true;
    let url = null, msg = null;
    try{
      const { data, error } = await sb.functions.invoke('creer-paiement', { body: {
        article: a.id, livraison: imm ? 'immediate' : 'differee', case_cgv: f.querySelector('#bqeCgv').checked,
        case_immediate: imm && f.querySelector('#bqeImm').checked, case_renonciation: imm && f.querySelector('#bqeRen').checked,
        cgv_version: cat.cgv_version, date_naissance: n && n.value ? n.value : null } });
      if(error){ try{ msg = (await error.context.json()).erreur; }catch(e){ msg = error.message; } }
      else url = data && data.url;
    }catch(e){ msg = e.message; }
    if(url){ location.href = url; return; }
    err.textContent = messageLisible(msg || 'Le paiement est indisponible pour le moment.');
    err.hidden = false;
    btn.textContent = 'Payer et recevoir l\\'objet · ' + prix;
    verifier();
  });
}

async function bqeRetourPaiement(){
  const q = new URLSearchParams(location.search).get('paiement');
  if(!q) return;
  history.replaceState(null, '', location.pathname);
  if(q === 'annule'){ notifier({ type: 'info', titre: 'Paiement annulé', texte: 'Rien n\\'a été débité.' }); return; }
  if(q !== 'ok') return;
  notifier({ type: 'succes', titre: 'Paiement reçu, merci !', texte: 'Ton objet arrive dans quelques secondes.', duree: 6000 });
  const tab = document.querySelector('.tab[data-tab="boutiqueeuros"]');
  if(tab) tab.click();
  // la confirmation de Stripe arrive en général en quelques secondes
  for(let i = 0; i < 6; i++){
    await new Promise(r => setTimeout(r, 2500));
    await loadBoutiqueEuros();
    const derniere = bqeCommandes[0];
    if(derniere && derniere.statut !== 'creee') break;
  }
  loadBoutique(true);
}

document.getElementById('bqeCorps').addEventListener('click', async (e) => {
  const art = e.target.closest('[data-bqe]');
  if(art){ bqeOuvrirFiche(art.dataset.bqe); return; }
  const r = e.target.closest('[data-retract]');
  if(!r || r.disabled) return;
  if(!r.classList.contains('confirmer')){
    r.classList.add('confirmer'); r.textContent = 'Confirmer : annuler l\\'achat';
    setTimeout(() => { if(r.isConnected){ r.classList.remove('confirmer'); r.textContent = 'Changer d\\'avis et être remboursé'; } }, 4000);
    return;
  }
  r.disabled = true;
  const { data, error } = await sb.rpc('euros_demander_retractation', { p_commande: r.dataset.retract });
  if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); r.disabled = false; return; }
  bqeCommandes = data || [];
  renderBoutiqueEuros();
  notifier({ type: 'succes', titre: 'Achat annulé', texte: 'L\\'objet ne sera pas livré. Tu seras remboursé sous quelques jours.' });
});

// ---------- Profil › Personnaliser ----------
let gardeRobe = null, grVitrine = null;
async function loadGardeRobe(){
  const corps = document.getElementById('grCorps');
  if(!corps) return;
  const { data, error } = await sb.rpc('garde_robe');
  if(error || !data){ corps.innerHTML = '<p class="collection-empty">La garde-robe arrive bientôt.</p>'; return; }
  gardeRobe = data;
  renderGardeRobe();
  try{
    const r = await sb.rpc('terra_vitrine', { p_joueur: window.__monId });
    grVitrine = r.error ? null : (r.data || []).length;
  }catch(e){ grVitrine = null; }
  renderGardeRobe();
}
function renderGardeRobe(){
  const corps = document.getElementById('grCorps');
  const g = gardeRobe;
  if(!corps || !g) return;
  const tuile = (rangee, o, vignette) => {
    const eq = (g[rangee] || null) === (o.id || null);
    const nom = rangee === 'dos' ? String(o.nom).replace(/^Dos /, '') : String(o.nom).replace(/^Paquet /, '');
    return `<div class="gr-objet${eq ? ' equipe' : ''}">${vignette}<span class="gr-nom">${echapperTexte(nom)}</span>
      ${eq ? '<span class="bq-equipe">Équipé</span>' : `<button type="button" class="bq-btn secondaire" data-gr-r="${rangee}" data-gr-id="${echapperTexte(o.id || '')}">Équiper</button>`}</div>`;
  };
  const dos = g.dos_liste || [], habs = g.habillages || [];
  corps.innerHTML = `
    <div class="bourse-section gr-bloc">
      <h2>Mes cartes</h2>
      <div class="gr-titre">Dos de carte <span>${dos.length} possédé${dos.length > 1 ? 's' : ''}</span></div>
      <div class="gr-objets">${dos.map(o => tuile('dos', o, dosApercuHtml(o.id))).join('')}</div>
      <div class="gr-titre">Habillage de paquet <span>${habs.length} possédé${habs.length > 1 ? 's' : ''}</span></div>
      <div class="gr-objets">${habs.map(o => tuile('habillage', o, habVignette(habCle(o.id), 66))).join('')}</div>
      <div class="gr-voir"><p>D'autres dos et habillages t'attendent : à gagner en jouant ou dans la boutique.</p>
        <button type="button" class="bq-btn secondaire" data-gr-boutique>Voir la boutique</button></div>
    </div>
    <div class="bourse-section gr-bloc">
      <h2>Ma vitrine</h2>
      <div class="gr-vitrine"><span>${grVitrine == null ? 'Tes plus belles cartes Terra, sur ton profil' : `<b>${grVitrine} / ${VITRINE_MAX}</b> cartes exposées`}</span>
        <button type="button" class="bq-btn secondaire" data-gr-vitrine>Modifier</button></div>
    </div>`;
  habGl.demarrer();
}
document.getElementById('grCorps').addEventListener('click', async (e) => {
  if(e.target.closest('[data-gr-boutique]')){
    const t = document.querySelector(`.tab[data-tab="${bqeAcces ? 'boutiqueeuros' : 'boutique'}"]`);
    if(t) t.click();
    return;
  }
  if(e.target.closest('[data-gr-vitrine]')){
    const vt = await chargerVitrine(window.__monId);
    ouvrirChoixVitrine(vt, 'panneau');
    return;
  }
  const b = e.target.closest('[data-gr-r]');
  if(!b || b.disabled) return;
  b.disabled = true;
  const { data, error } = await sb.rpc('garde_robe_equiper', { p_rangee: b.dataset.grR, p_id: b.dataset.grId || null });
  if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); b.disabled = false; return; }
  gardeRobe = data;
  appliquerDos(data.dos);
  appliquerHabillage(data.habillage);
  if(boutiqueCache){ boutiqueCache.dos = data.dos; boutiqueCache.habillage = data.habillage; renderBoutique(); }
  renderGardeRobe();
});
"""
ecrire('app.js', js)

# =============================================================== style.css
css = lire('style.css')
assert 'patch175' not in css, u'patch175 deja applique'
css += u"""

/* ---------- patch175 : boutique en euros, garde-robe, habillages ---------- */
/* les habillages : fond de secours (sans WebGL 2) et couleurs des textes du paquet */
.paquet.hab .paquet-motif{ background: var(--hab-fond); }
body.mode-terra .paquet.hab .paquet-motif{ filter: none; }
.paquet.hab .paquet-etiquette{ color: var(--hab-texte); }
.paquet.hab .paquet-etiquette svg{ stroke: var(--hab-texte); }
.paquet.hab .paquet-bande{ background: var(--hab-bande); color: var(--hab-bande-texte); }
.paquet.hab .paquet-titre{ text-shadow: var(--hab-lueur, none); }
.paquet .paquet-cachet{ width: 46px; height: 46px; border-radius: 50%; display: grid; place-items: center;
  background: radial-gradient(circle at 36% 32%, #D2584E, #9A1F1A 58%, #620F0C);
  box-shadow: 0 2px 4px rgba(0,0,0,.4), inset 0 0 0 4px rgba(0,0,0,.14), inset 0 0 0 6px rgba(255,180,170,.12); }
.paquet .paquet-cachet svg{ width: 24px !important; height: 24px !important; stroke: rgba(60,6,5,.75) !important; }
.paquet.hab-og-or-noir .paquet-hexa{ background: linear-gradient(135deg, #8A5A12, #FFE7A0 45%, #B7791F); animation: none; }
.paquet.hab-og-or-noir .paquet-hexa::before{ background: #0A0806; }
.paquet.hab-og-or-noir .paquet-hexa b{ color: #F6D77A; }

:is(.paquet.hab-og-prisme, .hab-vignette[data-hab="og-prisme"]){
  --hab-fond: linear-gradient(115deg, #8FF3FF, #C7A6FF 30%, #FFB7E3 55%, #FFE7A3 80%, #8FF3FF);
  --hab-texte: #fff; --hab-bande: #121C3A; --hab-bande-texte: #E6DAFF; --hab-lueur: 0 2px 8px rgba(20,16,48,.45); }
:is(.paquet.hab-og-or-noir, .hab-vignette[data-hab="og-or-noir"]){
  --hab-fond: repeating-radial-gradient(circle at 38% 40%, transparent 0 9px, rgba(242,184,71,.7) 9px 10px), linear-gradient(160deg, #141008, #050403);
  --hab-texte: #FFDB7A; --hab-bande: linear-gradient(90deg, #9A6412, #FFE7A0 45%, #B7791F); --hab-bande-texte: #0F0C0A; }
:is(.paquet.hab-kraft, .hab-vignette[data-hab="kraft"]){
  --hab-fond: repeating-linear-gradient(8deg, rgba(90,60,25,.12) 0 1px, transparent 1px 4px), linear-gradient(160deg, #C29A66, #A47C4C);
  --hab-texte: #40240F; --hab-bande: #F0E3C4; --hab-bande-texte: #522E12; }
:is(.paquet.hab-lave, .hab-vignette[data-hab="lave"]){
  --hab-fond: radial-gradient(60% 30% at 50% 100%, rgba(255,110,20,.85), transparent 70%), repeating-linear-gradient(115deg, transparent 0 11px, rgba(255,120,30,.5) 11px 12px, transparent 12px 27px), linear-gradient(180deg, #160806, #2E0C06);
  --hab-texte: #FFD173; --hab-bande: #0D0808; --hab-bande-texte: #FF9E38; --hab-lueur: 0 0 12px rgba(255,97,10,.85); }
:is(.paquet.hab-neon, .hab-vignette[data-hab="neon"]){
  --hab-fond: linear-gradient(180deg, #1A0830, #0D0519);
  --hab-texte: #FFE0FA; --hab-bande: #08020F; --hab-bande-texte: #66F2FF; --hab-lueur: 0 0 10px #FF2BD6, 0 0 22px rgba(255,43,214,.6); }
:is(.paquet.hab-comete, .hab-vignette[data-hab="comete"]){
  --hab-fond: radial-gradient(1px 1px at 20% 30%, #fff, transparent), radial-gradient(1px 1px at 70% 20%, #fff, transparent), radial-gradient(1.5px 1.5px at 40% 80%, #dfe8ff, transparent), linear-gradient(170deg, #050A1F, #142152);
  --hab-texte: #F2F7FF; --hab-bande: #0A122E; --hab-bande-texte: #CCE0FF; }
:is(.paquet.hab-maree, .hab-vignette[data-hab="maree"]){
  --hab-fond: linear-gradient(180deg, #1A9EB8, #0A5975);
  --hab-texte: #fff; --hab-bande: #05334D; --hab-bande-texte: #BFF7FF; --hab-lueur: 0 2px 8px rgba(0,40,60,.5); }
:is(.paquet.hab-orage, .hab-vignette[data-hab="orage"]){
  --hab-fond: linear-gradient(180deg, #3A4254, #12161F);
  --hab-texte: #EBF2FF; --hab-bande: #0A0D17; --hab-bande-texte: #CCE0FF; }
.hab-vignette[data-hab=""]{ --hab-fond: radial-gradient(circle at 40% 30%, #3B6FB8, #1D3F72 55%, #0B1D38); --hab-bande: linear-gradient(90deg, #B7791F, #FCE38A 30%, #F0B429 55%, #B7791F); }
.hab-vignette[data-hab="nacre"]{ --hab-fond: linear-gradient(135deg, #F4F1FF, #D9D3F2 55%, #A79FCF); --hab-bande: linear-gradient(90deg, #8FF3FF, #C7A6FF 30%, #FFB7E3 55%, #FFE7A3 80%); }
.hab-vignette{ position: relative; width: 72px; aspect-ratio: 200 / 280; max-width: 100%; margin: 0 auto 4px; border-radius: 5px; overflow: hidden;
  background: var(--hab-fond); box-shadow: 0 8px 16px rgba(0,0,0,.45); }
.hab-vignette canvas{ position: absolute; inset: 0; width: 100%; height: 100%; }
.hab-vignette .hv-bande{ position: absolute; left: 0; right: 0; bottom: 16.4%; height: 15.7%; background: var(--hab-bande); }
.hab-vignette::before, .hab-vignette::after{ content: ""; position: absolute; left: 0; right: 0; height: 6%; z-index: 1;
  background: repeating-linear-gradient(90deg, rgba(255,255,255,.2) 0 3px, rgba(0,0,0,.14) 3px 6px); }
.hab-vignette::before{ top: 0; } .hab-vignette::after{ bottom: 0; }

/* les dos OG en euros : Prisme et Constellation (CSS, comme le Nacre) */
body[data-dos="og-dos-prisme"], .bq-dos-apercu[data-dos="og-dos-prisme"]{
  --dos-fond: radial-gradient(1.6px 1.6px at 18% 22%, #fff, transparent), radial-gradient(1.4px 1.4px at 74% 30%, #fff, transparent), radial-gradient(1.6px 1.6px at 34% 70%, #fff, transparent), radial-gradient(1.4px 1.4px at 82% 76%, #fff, transparent), radial-gradient(1.2px 1.2px at 56% 12%, #fff, transparent),
              repeating-linear-gradient(60deg, rgba(255,255,255,.09) 0 2px, transparent 2px 5px),
              linear-gradient(115deg, #8FF3FF 0%, #C7A6FF 28%, #FFB7E3 46%, #FFE7A3 64%, #9CF7C9 82%, #8FF3FF 100%);
  --dos-liseret: rgba(255,255,255,.85); --dos-or: #fff; --dos-embleme: #141030; --dos-anneau: rgba(20,16,48,.6);
}
body[data-dos="og-dos-constellation"], .bq-dos-apercu[data-dos="og-dos-constellation"]{
  --dos-fond: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 140 140'%3E%3Cpolygon points='70,8 124,39 124,101 70,132 16,101 16,39' fill='none' stroke='%23E6C26E' stroke-opacity='.45' stroke-width='1'/%3E%3Cg fill='%23FFF4D6'%3E%3Ccircle cx='70' cy='8' r='2'/%3E%3Ccircle cx='124' cy='39' r='2'/%3E%3Ccircle cx='124' cy='101' r='2'/%3E%3Ccircle cx='70' cy='132' r='2'/%3E%3Ccircle cx='16' cy='101' r='2'/%3E%3Ccircle cx='16' cy='39' r='2'/%3E%3C/g%3E%3C/svg%3E") center / 140px 140px no-repeat,
              radial-gradient(1.4px 1.4px at 14% 18%, #fff, transparent), radial-gradient(1px 1px at 30% 34%, #dfe8ff, transparent), radial-gradient(1.4px 1.4px at 78% 14%, #fff, transparent), radial-gradient(1px 1px at 88% 44%, #fff, transparent), radial-gradient(1.2px 1.2px at 22% 82%, #fff, transparent), radial-gradient(1px 1px at 64% 88%, #dfe8ff, transparent), radial-gradient(1.4px 1.4px at 84% 70%, #fff, transparent), radial-gradient(1px 1px at 46% 8%, #fff, transparent),
              radial-gradient(70% 55% at 50% 45%, rgba(90,60,150,.35), transparent 70%),
              radial-gradient(circle at 50% 45%, #141B46 0%, #0A0E2A 60%, #04061A 100%);
  --dos-liseret: rgba(230,194,110,.7); --dos-or: #E6C26E; --dos-embleme: #070B22; --dos-anneau: rgba(7,11,34,.9);
}
:is(body[data-dos="og-dos-prisme"], body[data-dos="og-dos-constellation"]) .face-back:not(.bq-dos-apercu .face-back) .dos-embleme,
.bq-dos-apercu:is([data-dos="og-dos-prisme"], [data-dos="og-dos-constellation"]) .face-back .dos-embleme{
  width: 74px; height: 84px; margin: -42px 0 0 -37px; border-radius: 0; box-shadow: none;
  clip-path: polygon(50% 0, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
  background: linear-gradient(115deg, #8FF3FF 0%, #C7A6FF 28%, #FFB7E3 46%, #FFE7A3 64%, #9CF7C9 82%, #8FF3FF 100%); background-size: 220% 220%; animation: ogHolo 6s ease-in-out infinite;
}
:is(body[data-dos="og-dos-constellation"]) .face-back:not(.bq-dos-apercu .face-back) .dos-embleme,
.bq-dos-apercu[data-dos="og-dos-constellation"] .face-back .dos-embleme{ background: linear-gradient(135deg, #8A5A12, #FFE7A0 45%, #B7791F); animation: none; }
:is(body[data-dos="og-dos-prisme"], body[data-dos="og-dos-constellation"]) .face-back:not(.bq-dos-apercu .face-back) .dos-embleme::before,
.bq-dos-apercu:is([data-dos="og-dos-prisme"], [data-dos="og-dos-constellation"]) .face-back .dos-embleme::before{ content: ""; position: absolute; inset: 4px; clip-path: inherit; background: var(--dos-embleme); }
:is(body[data-dos="og-dos-prisme"], body[data-dos="og-dos-constellation"]) .face-back:not(.bq-dos-apercu .face-back) .dos-embleme::after,
.bq-dos-apercu:is([data-dos="og-dos-prisme"], [data-dos="og-dos-constellation"]) .face-back .dos-embleme::after{
  content: "OG"; position: relative; font-family: var(--titre); font-weight: 900; font-size: 28px; letter-spacing: .02em;
  background: linear-gradient(115deg, #8FF3FF, #C7A6FF 40%, #FFB7E3 70%, #FFE7A3); -webkit-background-clip: text; background-clip: text; color: transparent;
}
:is(body[data-dos="og-dos-constellation"]) .face-back:not(.bq-dos-apercu .face-back) .dos-embleme::after,
.bq-dos-apercu[data-dos="og-dos-constellation"] .face-back .dos-embleme::after{ background: linear-gradient(180deg, #FFF1C2, #E6C26E); -webkit-background-clip: text; background-clip: text; }
:is(body[data-dos="og-dos-prisme"], body[data-dos="og-dos-constellation"]) .face-back:not(.bq-dos-apercu .face-back) .dos-embleme svg,
.bq-dos-apercu:is([data-dos="og-dos-prisme"], [data-dos="og-dos-constellation"]) .face-back .dos-embleme svg{ display: none; }
body[data-dos="og-dos-prisme"] .face-back:not(.bq-dos-apercu .face-back) .dos-motif, .bq-dos-apercu[data-dos="og-dos-prisme"] .face-back .dos-motif{
  background: linear-gradient(105deg, transparent 36%, rgba(255,255,255,.75) 47%, rgba(255,255,255,.2) 53%, transparent 62%);
  background-size: 300% 100%; mix-blend-mode: soft-light; animation: ogReflet 4.5s ease-in-out infinite;
}
body[data-dos="og-dos-prisme"] .face-back:not(.bq-dos-apercu .face-back) .dos-motif path, .bq-dos-apercu[data-dos="og-dos-prisme"] .face-back .dos-motif path{ stroke: rgba(255,255,255,.4); }
body[data-dos="og-dos-constellation"] .face-back:not(.bq-dos-apercu .face-back) .dos-motif, .bq-dos-apercu[data-dos="og-dos-constellation"] .face-back .dos-motif{
  background: linear-gradient(152deg, transparent 47%, rgba(220,232,255,.9) 49.6%, rgba(220,232,255,0) 50.4%, transparent 52%) no-repeat;
  background-size: 260% 260%; animation: dosEtoileFilante 5s ease-in infinite;
}
body[data-dos="og-dos-constellation"] .face-back:not(.bq-dos-apercu .face-back) .dos-motif path, .bq-dos-apercu[data-dos="og-dos-constellation"] .face-back .dos-motif path{ stroke: rgba(199,166,255,.16); }
@keyframes dosEtoileFilante{ 0%{ background-position: 100% 0%; opacity: 0; } 4%{ opacity: 1; } 16%{ background-position: 0% 100%; opacity: 0; } 100%{ background-position: 0% 100%; opacity: 0; } }
@media (prefers-reduced-motion: reduce){
  body[data-dos^="og-dos-"] .face-back .dos-motif, body[data-dos^="og-dos-"] .face-back .dos-embleme,
  .bq-dos-apercu[data-dos^="og-dos-"] .face-back .dos-motif, .bq-dos-apercu[data-dos^="og-dos-"] .face-back .dos-embleme{ animation: none; }
}

/* la boutique en euros */
.bqe-bandeau{ max-width: 860px; background: var(--nuit-2); border: 1px solid rgba(169,188,212,0.16); border-radius: 14px; padding: 12px 14px; display: grid; gap: 8px; margin: 0 0 18px; }
.bqe-l1{ display: flex; justify-content: space-between; align-items: baseline; gap: 10px; flex-wrap: wrap; }
.bqe-l1 b{ font-family: var(--titre); font-size: 1.15rem; letter-spacing: .02em; }
.bqe-pc{ font-family: var(--titre); font-weight: 800; font-size: 1.3rem; color: var(--c-legendaire); font-variant-numeric: tabular-nums; }
.bqe-barre{ height: 8px; border-radius: 4px; background: #2A3B57; overflow: hidden; }
.bqe-barre i{ display: block; height: 100%; background: linear-gradient(90deg, var(--c-peucommun), var(--c-legendaire)); border-radius: 4px; }
.bqe-etapes{ display: flex; gap: 6px; } .bqe-etapes span{ flex: 1; height: 3px; border-radius: 2px; background: #2A3B57; } .bqe-etapes span.on{ background: var(--c-legendaire); }
.bqe-bandeau small{ color: var(--brume); font-size: .78rem; }
.bqe-test{ max-width: 860px; margin: 0 0 14px; padding: 8px 12px; border-radius: 10px; font-size: .82rem; color: #FFD9A0; background: rgba(240,180,41,.08); border: 1px dashed rgba(240,180,41,.45); }
.bq-section h2 .bqe-og{ font-family: var(--texte); font-size: .62rem; font-weight: 700; letter-spacing: .1em; padding: 3px 8px; border-radius: 999px; vertical-align: middle; color: #2A1E52;
  background: linear-gradient(115deg, #8FF3FF, #C7A6FF, #FFB7E3, #FFE7A3); }
.bq-section h2 .bqe-mot{ font-family: var(--texte); font-size: .78rem; font-weight: 500; color: var(--brume); letter-spacing: 0; }
.bqe-article{ font: inherit; text-align: left; cursor: pointer; transition: border-color .2s, transform .2s; }
.bqe-article:hover{ border-color: rgba(240,180,41,.55); transform: translateY(-2px); }
.bqe-article:focus-visible{ outline: 2px solid var(--c-legendaire); outline-offset: 2px; }
.bqe-prix{ display: block; text-align: center; font-variant-numeric: tabular-nums; }
.bqe-etat{ margin-top: 4px; text-align: center; padding: 8px 4px; font-size: .8rem; font-weight: 600; border-radius: 9px; color: var(--brume); box-shadow: inset 0 0 0 1.5px rgba(169,188,212,.35); }
.bqe-etat.ok{ color: var(--c-peucommun); box-shadow: inset 0 0 0 1.5px rgba(34,160,107,.5); }
.bqe-achats{ display: grid; gap: 6px; max-width: 860px; }
.bqe-achat{ display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; background: rgba(15,31,56,0.55); border: 1px solid rgba(169,188,212,0.18); border-radius: 10px; padding: 9px 12px; font-size: .86rem; }
.bqe-achat b{ font-weight: 600; } .bqe-achat small{ display: block; color: var(--brume); font-size: .76rem; margin-top: 2px; }
.bqe-lien{ border: 0; background: none; color: var(--c-legendaire); font: 600 .8rem var(--texte); cursor: pointer; text-decoration: underline; text-underline-offset: 3px; padding: 6px 2px; }
.bqe-lien.confirmer{ color: #FF9A9D; }
.bqe-pied{ max-width: 860px; margin: 18px 0 0; padding-top: 12px; border-top: 1px solid rgba(169,188,212,0.16); color: var(--brume); font-size: .76rem; }
.bqe-pied a{ color: var(--brume); }

.fenetre.bqe-fiche{ position: relative; width: min(440px, 100%); text-align: left; display: grid; gap: 12px; }
.bqe-fermer{ position: absolute; right: 8px; top: 8px; width: 36px; height: 36px; border-radius: 50%; border: 0; background: rgba(169,188,212,.12); color: #fff; font-size: 1.3rem; cursor: pointer; }
.bqe-tete{ display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 14px; align-items: center; padding-right: 34px; }
.bqe-tete small{ color: var(--brume); font-size: .78rem; }
.bqe-tete h2{ font-family: var(--titre); font-weight: 900; font-size: 1.9rem; line-height: .95; margin: 2px 0; }
.bqe-gros-prix{ font-family: var(--titre); font-weight: 800; font-size: 1.5rem; color: var(--c-legendaire); font-variant-numeric: tabular-nums; }
.bqe-grand .bq-dos-apercu{ margin: 0; }
.bqe-recoit{ margin: 0; font-size: .86rem; line-height: 1.45; background: rgba(7,16,31,.45); border-radius: 10px; padding: 10px 12px; }
.bqe-liv{ border: 0; margin: 0; padding: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; min-width: 0; }
.bqe-liv legend{ font-weight: 700; font-size: .88rem; margin-bottom: 6px; padding: 0; }
.bqe-liv label{ position: relative; display: grid; gap: 2px; cursor: pointer; border-radius: 10px; padding: 10px; background: rgba(7,16,31,.45); box-shadow: inset 0 0 0 1.5px rgba(169,188,212,.25); font-size: .78rem; color: var(--brume); }
.bqe-liv label b{ color: #fff; font-size: .92rem; }
.bqe-liv input{ position: absolute; opacity: 0; pointer-events: none; }
.bqe-liv label:has(input:checked){ box-shadow: inset 0 0 0 2px var(--c-legendaire); background: rgba(240,180,41,.08); }
.bqe-liv label:has(input:focus-visible){ outline: 2px solid var(--c-legendaire); outline-offset: 2px; }
.bqe-cases{ display: grid; gap: 8px; }
.bqe-cases[hidden]{ display: none; }
.bqe-case{ display: grid; grid-template-columns: 22px minmax(0, 1fr); gap: 8px; align-items: start; font-size: .82rem; line-height: 1.4; cursor: pointer; }
.bqe-case input{ width: 18px; height: 18px; margin: 1px 0 0; accent-color: var(--c-legendaire); }
.bqe-case a{ color: var(--c-legendaire); }
.bqe-info{ margin: 0; font-size: .8rem; color: var(--brume); }
.bqe-info.vert{ color: #9CF7C9; } .bqe-info.rouge{ color: #FF9A9D; }
.bqe-naissance{ display: grid; gap: 6px; background: rgba(7,16,31,.45); border-radius: 10px; padding: 10px 12px; }
.bqe-naissance label{ font-weight: 700; font-size: .86rem; }
.bqe-naissance input{ font: inherit; color: #fff; background: var(--nuit); border: 1px solid rgba(169,188,212,.35); border-radius: 8px; padding: 8px 10px; max-width: 220px; color-scheme: dark; }
.bqe-payer{ border: 0; border-radius: 11px; padding: 13px 14px; cursor: pointer; font-family: var(--titre); font-weight: 800; font-size: 1.18rem; letter-spacing: .02em; background: var(--c-legendaire); color: var(--encre); box-shadow: 0 3px 0 #B7791F; }
.bqe-payer:disabled{ opacity: .4; cursor: default; box-shadow: none; }
.bqe-erreur{ margin: 0; font-size: .84rem; color: #FF9A9D; }
.bqe-securite{ margin: 0; font-size: .74rem; color: var(--brume); line-height: 1.4; }
.hab-grand .hab-vignette{ margin: 0; }
@media (max-width: 420px){ .bqe-liv{ grid-template-columns: 1fr; } .bqe-payer{ font-size: 1.02rem; } }

/* Profil › Personnaliser */
.gr-bloc{ max-width: 860px; display: grid; gap: 12px; }
.gr-titre{ display: flex; justify-content: space-between; align-items: baseline; gap: 8px; font-weight: 700; font-size: .9rem; }
.gr-titre span{ color: var(--brume); font-weight: 500; font-size: .78rem; }
.gr-objets{ display: flex; gap: 8px; overflow-x: auto; padding-bottom: 6px; scrollbar-width: thin; }
.gr-objet{ flex: none; width: 112px; display: flex; flex-direction: column; align-items: center; gap: 6px; background: rgba(15,31,56,0.55); border: 1.5px solid rgba(169,188,212,0.16); border-radius: 12px; padding: 10px 6px; }
.gr-objet.equipe{ border-color: var(--c-peucommun); }
.gr-objet .bq-dos-apercu{ margin: 0; }
.gr-objet .hab-vignette{ margin: 0; height: 131.5px; width: auto !important; }
.gr-nom{ font-size: .78rem; font-weight: 600; text-align: center; line-height: 1.15; min-height: 2.3em; display: grid; place-items: center; }
.gr-objet .bq-btn, .gr-objet .bq-equipe{ margin: 0; width: 100%; padding: 6px 4px; font-size: .9rem; }
.gr-voir{ display: grid; gap: 8px; justify-items: start; }
.gr-voir p{ margin: 0; color: var(--brume); font-size: .84rem; }
.gr-voir .bq-btn, .gr-vitrine .bq-btn{ margin: 0; }
.gr-vitrine{ display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; font-size: .9rem; }
.gr-vitrine b{ font-family: var(--titre); font-size: 1.2rem; }
"""
ecrire('style.css', css)
print(u'patch175 applique')
