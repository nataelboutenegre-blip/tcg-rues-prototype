# patch255 : objets du pass « Brumes d'automne » — Dos Feuilles d'or et Paquet Vendanges
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')

# les objets du pass ont des identifiants « pass-s2-… » : on retombe sur la clé du dessin
s = rep(s, "function dosCle(id){ return id ? id.replace(/^dos-/, '') : 'origine'; }",
           "function dosCle(id){ return id ? id.replace(/^pass-s\\d+-/, '').replace(/^dos-/, '') : 'origine'; }   // patch255 : objets du pass")
s = rep(s, "function habCle(id){ return !id ? '' : id === 'nacre' ? 'nacre' : String(id).replace(/^og-paquet-/, 'og-').replace(/^paquet-/, ''); }",
           "function habCle(id){ return !id ? '' : id === 'nacre' ? 'nacre' : String(id).replace(/^pass-s\\d+-/, '').replace(/^og-paquet-/, 'og-').replace(/^paquet-/, ''); }")
s = rep(s, "const HAB_PAQ = { 'og-prisme': 2, 'og-or-noir': 3, kraft: 4, lave: 5, neon: 6, comete: 7, maree: 8, orage: 9 };",
           "const HAB_PAQ = { 'og-prisme': 2, 'og-or-noir': 3, kraft: 4, lave: 5, neon: 6, comete: 7, maree: 8, orage: 9, vendanges: 10 };   // patch255")

# ---- le paquet Vendanges : velours lie-de-vin, sarment doré, grappes, feuilles de vigne qui tombent
VENDANGES = r"""  else if(u_paq==10){
    vec3 Lg=normalize(vec3(-.45,.55,.75));
    col=mix(vec3(.17,.02,.06),vec3(.44,.07,.15),smoothstep(-.8,.8,q.y))*(.88+.16*dif)+sp*vec3(1.,.8,.75)*.06;
    col*=.9+.2*fbm(q*7.);
    col=mix(col,vec3(.95,.72,.32),rg*.22);
    float sy=.16+.07*sin(q.x*6.+1.2)+.025*sin(q.x*17.);
    col=mix(col,vec3(.95,.74,.32)*(.75+.35*dif),lineW(q.y-sy,.0045)*.9);
    for(int k=0;k<2;k++){
      float cx=k==0?.19:-.24; float s=k==0?1.:.8;
      float ty=.16+.07*sin(cx*6.+1.2)+.025*sin(cx*17.);
      vec2 c=vec2(cx,ty-.07*s);
      col=mix(col,vec3(.85,.62,.25)*(.8+.3*dif),lineW(q.x-cx-(ty-q.y)*.25,.0035)*step(c.y,q.y)*step(q.y,ty)*.9);
      vec2 fq=(q-vec2(cx+.075*s*(k==0?1.:-1.),ty-.02))/(.075*s); fq.x*=k==0?1.:-1.;
      float fa=.5; fq=mat2(cos(fa),-sin(fa),sin(fa),cos(fa))*fq;
      float fd=min(min(length(fq-vec2(0.,.45))-.5,length(fq-vec2(-.42,.05))-.42),min(length(fq-vec2(.42,.05))-.42,length(fq-vec2(0.,-.1))-.45));
      float fv=lineW(fq.x,.04)+lineW(abs(fq.y-abs(fq.x)*.8-.1),.03)*step(abs(fq.x),.55);
      col=mix(col,mix(vec3(.38,.42,.12),vec3(.86,.7,.26),.5+.5*fq.y)*(.75+.35*dif)*(1.-.25*fv),1.-smoothstep(-.03,.02,fd));
      for(int r=0;r<6;r++){ int nr=r==0?4:(r==1?5:(r==2?4:(r==3?3:(r==4?2:1))));
        for(int i=0;i<5;i++){ if(i>=nr) break;
          vec2 jj=h22(vec2(float(r),float(i))+float(k)*7.)-.5;
          vec2 p=c+(vec2((float(i)-float(nr-1)*.5)*.058,-float(r)*.05-.035)+jj*.012)*s;
          float rr=(.031+jj.x*.008)*s; vec2 dv=(q-p)/rr; float d2=dot(dv,dv);
          if(d2<1.){ vec3 n=vec3(dv,sqrt(1.-d2)); float l=max(dot(n,Lg),0.);
            vec3 g=mix(vec3(.12,.02,.16),vec3(.52,.16,.55),l)+vec3(1.,.85,1.)*pow(l,24.)*.7+vec3(.35,.25,.4)*(1.-n.z)*.25;
            col=mix(col,g,smoothstep(1.,.86,d2)); } } } }
    vec2 lq=q-vec2(t*.015,-t*.07); vec2 id=floor(lq/.24); vec2 h=h22(id+9.);
    vec2 lc=(id+.5+(h-.5)*.4)*.24; lc.x+=sin(t*1.1+h.y*9.)*.025;
    float a=t*(.6+h.x)+h.y*TAU; vec2 lp=mat2(cos(a),-sin(a),sin(a),cos(a))*(lq-lc)/(.03+.02*h.y);
    float ld=max(length(lp-vec2(-.55,0.)),length(lp-vec2(.55,0.)))-1.;
    vec3 fc=mix(vec3(.9,.45,.12),vec3(.95,.75,.28),h.x);
    col=mix(col,fc*(.8+.3*dif),step(.55,h.y)*(1.-smoothstep(-.05,.05,ld))*.9);
    float gb=dot(q,normalize(vec2(1.,.6)))-u_tilt.x*.35-u_tilt.y*.2-sin(t*.35)*.15;
    col+=vec3(1.,.85,.6)*exp(-gb*gb*90.)*.12; }
"""
s = rep(s, "  else {\n    float P=3.7; float cy=floor(t/P), ph=t-cy*P;", VENDANGES + "  else {\n    float P=3.7; float cy=floor(t/P), ph=t-cy*P;")

# ---- le dos Feuilles d'or : sous-bois sombre, brume, feuilles d'or qui tombent et accrochent la lumière
FEUILLES = r"""  'feuilles-or': `
float feuille(vec2 p){ float d=max(length(p-vec2(-.45,0.)),length(p-vec2(.45,0.)))-.9; vec2 st=p-vec2(0.,-.95); return min(d,max(abs(st.x)-.035,abs(st.y)-.22)); }
vec3 orFeuille(vec2 p,float d,float sz,vec3 L){
  float e=.02; vec2 gr=vec2(feuille(p+vec2(e,0.))-d,feuille(p+vec2(0.,e))-d)/e;
  float bev=smoothstep(0.,.35,-d); vec3 N=normalize(vec3(gr*(1.-bev)*.9,1.));
  float vein=1.-smoothstep(0.,.05,abs(p.x))*1.; float side=1.-smoothstep(0.,.05,abs(fract((p.y-abs(p.x)*.9)*3.5)-.5)/3.5);
  float l=max(dot(N,L),0.); float sp=pow(max(reflect(-L,N).z,0.),18.);
  vec3 c=mix(vec3(.42,.25,.06),vec3(.92,.68,.24),l)+vec3(1.,.93,.7)*sp*1.1;
  c*=1.-.25*vein*step(abs(p.y),.75)-.12*side*step(.08,abs(p.x));
  return c; }
vec3 dos(vec2 q,vec2 uv,float t){
  vec3 L=normalize(vec3(u_tilt.x*1.4+.25,-u_tilt.y*1.4+.45,.85));
  vec3 col=mix(vec3(.045,.03,.018),vec3(.15,.085,.035),1.-smoothstep(0.,1.,length((uv-vec2(.5,.4))*vec2(1.,1.2))));
  col+=vec3(.07,.05,.02)*fbm(q*.05);
  float f=ringsF(q,0.,0.); col+=vec3(.75,.55,.2)*lineU(ringDist(f),.35)*.22;
  float m=fbm(q*.012+vec2(t*.03,-t*.01)); col+=vec3(.45,.36,.25)*smoothstep(.45,.85,m)*.22*smoothstep(.3,1.,uv.y);
  for(int k=0;k<2;k++){ float fk=float(k); float cs=k==0?64.:44.; float sz=k==0?17.:10.5; float sp=k==0?11.:7.;
    vec2 lq=q-vec2(t*2.5*(fk+1.),-t*sp)+fk*31.; vec2 id=floor(lq/cs); vec2 h=h22(id+fk*7.1+3.);
    if(h.y>(k==0?.42:.5)){
      vec2 c=(id+.5+(h-.5)*.3)*cs; c.x+=sin(t*(.8+h.x)+h.y*9.)*4.;
      float a=t*(.5+h.x*.7)*(h.y>.7?1.:-1.)+h.x*TAU; float fl=.55+.45*cos(t*(1.2+h.y)+h.x*5.);
      vec2 p=mat2(cos(a),-sin(a),sin(a),cos(a))*(lq-c)/sz; p.x/=max(fl,.18);
      float d=feuille(p);
      if(d<.08){ vec3 lc=orFeuille(p,d,sz,L)*(k==0?1.:.7); col=mix(col,lc,1.-smoothstep(-.06,.03,d)); } } }
  col+=vec3(1.,.8,.45)*glint(uv,u_tilt,18.)*.08;
  return col*vign(uv,.4); }`,
"""
s = rep(s, "const DOS_GLSL = {\n", "const DOS_GLSL = {\n" + FEUILLES)
f.write_text(s, encoding='utf-8')

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
s += """
/* ---------- patch255 : objets du pass « Brumes d'automne » ---------- */
body[data-dos="feuilles-or"], .bq-dos-apercu[data-dos="feuilles-or"]{
  --dos-fond: radial-gradient(circle at 50% 40%, #3A2410 0%, #24160A 55%, #0E0804 100%);
  --dos-liseret: rgba(240,196,110,.65); --dos-or: #F2CB72; --dos-embleme: #140C04; --dos-anneau: rgba(20,12,4,.92); --dos-halo: rgba(240,180,80,.35);
}
:is(.paquet.hab-vendanges, .hab-vignette[data-hab="vendanges"]){
  --hab-fond: radial-gradient(circle at 70% 60%, #6A1F5A 0 6%, transparent 7%), linear-gradient(180deg, #2B0410, #6E1226);
  --hab-texte: #FBE3B0; --hab-bande: linear-gradient(90deg, #8A5A16, #F2CB72 45%, #9A6A1E); --hab-bande-texte: #2B0410; --hab-lueur: 0 2px 8px rgba(30,0,10,.6); }
"""
f.write_text(s, encoding='utf-8')
print('patch255 ok')
