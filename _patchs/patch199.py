# -*- coding: utf-8 -*-
u"""
patch199 — les neuf dos premium (Comète, 14 Juillet, Marée, Puy de feu,
Prisme, Or fondu, Néon, Gravure, Orage), dessinés en WebGL 2.

- app.js : shaders des dos (repris de l'aperçu « Collections premium »),
  moteur dosGl (un seul contexte WebGL, un rendu par dos et par taille,
  copié dans chaque carte visible ; image figée si « moins de mouvement » ;
  résolution qui baisse si l'appareil peine).
- style.css : couleurs du liseré, des coins et de l'épingle pour chaque dos,
  dégradé de secours sans WebGL 2.
SQL : _boutique-euros/10-dos-premium.sql (les 9 articles, visibles des
testeurs tant que la boutique est fermée).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)

BLOC_JS = r'''
// ---------- patch199 : les dos premium, dessinés par la carte graphique ----------
// Neuf dos vendus dans la boutique en euros. Chaque dos garde le liseré, les
// coins et l'épingle du jeu, posés par-dessus un rendu WebGL 2 qui reprend les
// courbes de niveau de tous les dos (même tirage que DOS_MOTIF_SVG).
// Sans WebGL 2, la carte garde un dégradé de la couleur du dos (style.css).
const DOS_GLSL_COMMUN = `#version 300 es
precision highp float;
uniform vec2 u_res; uniform float u_time; uniform vec2 u_tilt; uniform vec2 u_ptr; uniform float u_ptrOn; uniform float u_rev;
uniform sampler2D u_photo; uniform float u_par; uniform vec4 u_gA; uniform vec4 u_gB;
out vec4 fragColor;
const float W=188., H=263., PI=3.14159265, TAU=6.28318531;
float h21(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
vec2 h22(vec2 p){ float n=h21(p); return vec2(n,h21(p+n+.17)); }
float vnoise(vec2 p){ vec2 i=floor(p),f=fract(p); vec2 u=f*f*(3.-2.*f);
  return mix(mix(h21(i),h21(i+vec2(1.,0.)),u.x),mix(h21(i+vec2(0.,1.)),h21(i+vec2(1.,1.)),u.x),u.y); }
float fbm(vec2 p){ float v=0.,a=.5; mat2 m=mat2(1.6,1.2,-1.2,1.6); for(int i=0;i<5;i++){ v+=a*vnoise(p); p=m*p+3.1; a*=.5; } return v; }
float fbm3(vec2 p){ float v=0.,a=.5; mat2 m=mat2(1.6,1.2,-1.2,1.6); for(int i=0;i<3;i++){ v+=a*vnoise(p); p=m*p+3.1; a*=.5; } return v; }
float upx(){ return W/u_res.x; }
float ringsF(vec2 q,float ph,float onde){ vec2 d=q-u_gA.xy; d.y/=.82; float r=length(d); float a=atan(d.y,d.x);
  float m=1.+u_gB.z*sin(u_gA.z*a+u_gB.x+ph)+u_gB.w*sin(u_gA.w*a+u_gB.y-ph*.7)+onde*sin(5.*a+ph*2.); return r/(24.985*m); }
float ringDist(float f){ float g=abs(fract(f+.5)-.5); return g/max(fwidth(f),1e-5)*upx(); }
float lineU(float d,float w){ float p=upx(); return 1.-smoothstep(w-p*.8,w+p*.8,d); }
vec3 spectral(float x){ return .5+.5*cos(TAU*(x+vec3(0.,.33,.67))); }
float sdBox(vec2 p,vec2 b,float r){ vec2 d=abs(p)-b+r; return length(max(d,0.))+min(max(d.x,d.y),0.)-r; }
vec2 cardQ(){ vec2 uv=gl_FragCoord.xy/u_res; uv.y=1.-uv.y; return uv*vec2(W,H); }
float lum(vec3 c){ return dot(c,vec3(.299,.587,.114)); }
float vign(vec2 uv,float k){ return 1.-k*smoothstep(.6,1.1,length(uv-.5)*1.5); }
vec4 photoRect(float b){ return vec4(b,b,W-b,b+(H-2.*b)*.6); }
vec2 photoUV(vec2 q,vec4 R){ vec2 s=(q-R.xy)/(R.zw-R.xy); float rar=(R.z-R.x)/(R.w-R.y);
  if(u_par>rar) s.x=.5+(s.x-.5)*rar/u_par; else s.y=.5+(s.y-.5)*u_par/rar; return s; }
vec3 photo(vec2 s){ return texture(u_photo,clamp(s,.002,.998)).rgb; }
float inR(vec2 q,vec4 R){ float p=upx(); return smoothstep(R.x-p,R.x+p,q.x)*(1.-smoothstep(R.z-p,R.z+p,q.x))*smoothstep(R.y-p,R.y+p,q.y)*(1.-smoothstep(R.w-p,R.w+p,q.y)); }
float frameD(vec2 q,float b){ return sdBox(q-vec2(W,H)*.5,vec2(W,H)*.5-b,7.); }
float interior(vec2 q,float b){ return 1.-smoothstep(-upx(),upx(),frameD(q,b)); }
float glint(vec2 uv,vec2 tl,float k){ float b=dot(uv-.5,normalize(vec2(1.,.62)))-tl.x*.42-tl.y*.26; return exp(-b*b*k); }
vec3 stars(vec2 q,vec2 par,float t,float dens){ vec3 c=vec3(0.);
  for(int L=0;L<3;L++){ float s=float(L); float cs=7.+s*6.; vec2 qq=q+par*(4.+s*9.); vec2 id=floor(qq/cs); vec2 r=h22(id+s*13.1);
    vec2 sp=(id+.15+r*.7)*cs; float d=length(qq-sp); float b=h21(id*1.7+s*5.3); float tw=.55+.45*sin(t*(1.3+b*3.)+b*50.);
    float on=step(1.-dens,b); float sz=.35+.55*smoothstep(.96,1.,b);
    c+=on*tw*(exp(-d*d/(sz*sz))*vec3(.9,.95,1.)*1.3+exp(-d/(2.5*sz))*.1*vec3(.6,.75,1.)); }
  return c; }
vec3 ember(vec2 q,float t,float cs,float speed,float sz,float dens,float seed,vec3 col){
  vec2 p=q; p.y+=t*speed; p.x+=sin(p.y*.05+seed)*4.; vec2 id=floor(p/cs); vec2 r=h22(id+seed); vec2 c=(id+.2+r*.6)*cs;
  float d=length(p-c); float life=fract(r.x*7.+t*.25); return step(1.-dens,r.y)*col*exp(-d*d/sz)*(1.-life)*1.6; }
vec3 fire(float x){ return vec3(.9,.12,.02)*smoothstep(0.,.35,x)+vec3(.1,.35,.05)*smoothstep(.3,.7,x)+vec3(0.,.35,.25)*smoothstep(.65,1.05,x)+vec3(0.,0.,.35)*smoothstep(1.,1.4,x); }
`;
const DOS_GLSL = {
  comete: `
vec3 comet(vec2 q,float t,float P,vec2 A,vec2 B,float sc,out float light){
  float ph=mod(t,P)/P; float act=smoothstep(0.,.04,ph)*(1.-smoothstep(.52,.62,ph)); float pp=ph/.6;
  vec2 head=mix(A,B,pp); vec2 dir=normalize(B-A); vec2 rel=(q-head)/sc; float al=dot(rel,-dir); float pe=dot(rel,vec2(-dir.y,dir.x));
  float tail=0.,ion=0.;
  if(al>0.){ float w=1.2+al*.07; tail=exp(-pe*pe/(w*w))*exp(-al/85.)*(.7+.3*vnoise(vec2(al*.08-t*6.,pe*.3)));
    ion=exp(-pow(pe-al*.05,2.)/(.5+al*.02))*exp(-al/140.)*.5; }
  float hd=exp(-dot(rel,rel)/5.)*1.6+.5/(1.+dot(rel,rel)*.04);
  light=act*exp(-length(q-head)/(50.*sc));
  return act*(tail*vec3(.75,.88,1.)*1.1+ion*vec3(.4,.6,1.)+hd*vec3(1.,.98,.95)); }
vec3 dos(vec2 q,vec2 uv,float t){
  vec3 col=mix(vec3(.012,.025,.075),vec3(.07,.12,.28),1.-smoothstep(0.,.95,length((uv-vec2(.5,.42))*vec2(1.,1.25))));
  vec2 w=uv*2.4+u_tilt*.06; vec2 wq=w+vec2(fbm(w*1.3+t*.015),fbm(w*1.3+vec2(5.2,1.3)-t*.012))*1.4; float n=fbm(wq);
  col+=vec3(.32,.2,.62)*pow(n,3.2)*1.5+vec3(.1,.35,.75)*pow(fbm(wq*1.8+7.),4.)*1.6;
  col+=stars(q,u_tilt,t,.38);
  float li; col+=comet(q,t,6.5,vec2(-40.,30.),vec2(235.,215.),1.,li);
  float f=ringsF(q,0.,0.); col+=vec3(.55,.7,1.)*lineU(ringDist(f),.38)*(.11+1.2*li);
  return col*vign(uv,.35); }`,
  juillet: `
vec3 fwColor(float h){ return h<.33?vec3(.38,.56,1.):(h<.66?vec3(1.,.96,.9):vec3(1.,.3,.34)); }
vec3 burst(vec2 q,vec2 c,float e,vec3 fc,float sc,vec2 sd,inout vec3 lc){
  float fade=exp(-e*1.4); float e0=max(e-.3,0.); vec3 acc=vec3(0.);
  lc+=fc*fade*exp(-length(q-c)/70.);
  vec2 ga=c+vec2(0.,14.*e0*e0), gb=c+vec2(0.,14.*e*e); vec2 pq=q-ga, gd=gb-ga;
  float dc=length(pq-gd*clamp(dot(pq,gd)/max(dot(gd,gd),1e-4),0.,1.));
  if(dc>52.*sc+8.) return vec3(0.);
  vec3 hot=mix(fc,vec3(1.,.97,.9),exp(-e*3.5));
  for(int i=0;i<36;i++){ float fi=float(i); float a=fi/36.*TAU+h21(sd+fi)*.2; float sp=130.*sc*(.7+.3*h21(sd+fi*1.3)); vec2 dir=vec2(cos(a),sin(a));
    vec2 p1=c+dir*sp*(1.-exp(-e*2.6))/2.6+vec2(0.,14.*e*e); vec2 p0=c+dir*sp*(1.-exp(-e0*2.6))/2.6+vec2(0.,14.*e0*e0);
    vec2 pa=q-p0,ba=p1-p0; float hh=clamp(dot(pa,ba)/max(dot(ba,ba),1e-4),0.,1.); float d=length(pa-ba*hh);
    float crep=e<.9?1.:step(.45,h21(vec2(fi,floor(e*22.))+sd));
    float trail=hh*hh;
    acc+=hot*fade*crep*(trail*exp(-d*d*.9)*1.6+exp(-d*d*.35)*.25*trail+exp(-length(q-p1)*.5)*.22)+hot*fade*exp(-length(q-p1)*length(q-p1)*1.2)*1.3; }
  acc+=hot*exp(-e*10.)*exp(-length(q-c)/7.)*1.5; return acc; }
vec3 fireworks(vec2 q,float t,vec4 A,float sc,out vec3 lc){
  vec3 acc=vec3(0.); lc=vec3(0.);
  for(int k=0;k<4;k++){ float fk=float(k); float C=2.8; float tt=t+fk*.7; float cyc=floor(tt/C); float lt=tt-cyc*C; vec2 sd=vec2(cyc,fk*7.3);
    vec2 c=vec2(mix(A.x,A.z,h21(sd)),mix(A.y,A.w,h21(sd+3.1))); vec3 fc=fwColor(fract((fk+cyc)/3.)+.01);
    if(lt<.55){ float pr=lt/.55; vec2 rp=vec2(c.x+(1.-pr)*8.*sin(fk*2.),mix(H+5.,c.y,1.-pow(1.-pr,2.))); vec2 pa=q-rp; vec2 ba=vec2(0.,16.);
      float d=length(pa-ba*clamp(dot(pa,ba)/256.,0.,1.)); float hd=length(q-rp);
      acc+=vec3(1.,.8,.5)*(exp(-hd*hd*.6)*1.4+exp(-d*d*1.5)*.5*(1.-clamp(dot(pa,ba)/256.,0.,1.))+exp(-hd*.4)*.15); }
    else{ acc+=burst(q,c,lt-.55,fc,sc,sd,lc); } }
  return acc; }
vec3 dos(vec2 q,vec2 uv,float t){
  vec3 col=mix(vec3(.02,.035,.12),vec3(.1,.14,.36),1.-smoothstep(0.,1.,length((uv-vec2(.5,.45))*vec2(1.,1.2))));
  col+=vec3(.3,.12,.2)*smoothstep(.55,1.,uv.y)*.3;
  col+=vec3(.55,.55,.7)*fbm3(q*.03+vec2(t*.02,0.))*.07*(1.-uv.y);
  vec3 lc; vec3 fw=fireworks(q,t,vec4(28.,38.,160.,150.),1.,lc);
  float f=ringsF(q,0.,0.); col+=lineU(ringDist(f),.35)*(vec3(.06)+lc*.9);
  col+=lc*(.05+.3*fbm3(q*.022+vec2(t*.03,0.)))+fw; return col*vign(uv,.3); }`,
  maree: `
float caustic(vec2 p0,float t){ vec2 p=p0-250.; vec2 i=p; float c=1.; float inten=.005;
  for(int n=0;n<5;n++){ float tt=t*(1.-3.5/float(n+1)); i=p+vec2(cos(tt-i.x)+sin(tt+i.y),sin(tt-i.y)+cos(tt+i.x));
    c+=1./length(vec2(p.x/(sin(i.x+tt)/inten),p.y/(cos(i.y+tt)/inten))); }
  c/=5.; c=1.17-pow(c,1.4); return pow(abs(c),8.); }
vec3 bubbles(vec2 q,float t){ vec2 p=q; p.y+=t*14.; vec2 id=floor(p/16.); vec2 r=h22(id+2.); vec2 cc=(id+.2+r*.6)*16.; cc.x+=sin(t*2.+r.y*9.)*2.;
  float d=length(p-cc); float rr=.6+r.x*1.2; float bub=step(.6,r.y)*((1.-smoothstep(rr,rr+.25,d))-(1.-smoothstep(rr-.5,rr-.15,d))*.75);
  return bub*.35*vec3(.8,1.,1.); }
vec3 dos(vec2 q,vec2 uv,float t){
  vec3 col=mix(vec3(.02,.17,.26),vec3(.1,.5,.62),1.-smoothstep(0.,1.05,length((uv-vec2(.5,.38))*vec2(1.,1.2))));
  col=mix(col,vec3(.01,.09,.16),smoothstep(.45,1.,uv.y)*.6);
  float ca=caustic(q*.045+u_tilt*.3+vec2(10.,0.),t*.45);
  col+=vec3(.55,.95,1.)*ca*.55;
  float f=ringsF(q,t*.55,.035); float dl=ringDist(f);
  float wave=.5+.5*sin(f*TAU*.5-t*2.2);
  col+=vec3(.8,.98,1.)*lineU(dl,.45)*(.18+.55*pow(wave,6.));
  float band=dot(uv-.5,normalize(vec2(.8,.6)))-u_tilt.x*.35-u_tilt.y*.25+sin(t*.4)*.05;
  col+=vec3(.85,1.,1.)*exp(-band*band*55.)*.22*(.6+.4*ca);
  col+=bubbles(q,t);
  return col*vign(uv,.3); }`,
  feu: `
vec3 dos(vec2 q,vec2 uv,float t){
  vec2 qq=q; float sh=1.-uv.y; qq.x+=(vnoise(vec2(q.y*.08-t*2.2,q.x*.02))-.5)*2.5*(.3+sh);
  float crust=fbm(qq*.07);
  vec3 col=vec3(.05,.018,.012)*(.55+.9*crust)+vec3(.04,.02,.015)*fbm(qq*.3);
  float f=ringsF(qq,0.,0.); float dl=ringDist(f); float ring=floor(f+.5);
  float pulse=.5+.5*sin(t*1.9-ring*.8);
  float flow=fbm(qq*.05+vec2(0.,-t*.35)+ring*1.7);
  float core=1.-smoothstep(0.,2.4,dl); float glow=exp(-dl*.35);
  float T=core*(.55+.75*flow)*(.6+.6*pulse)+glow*.35*(.4+.6*pulse);
  float cr=abs(fbm(qq*.045+3.)-.5); T+=(1.-smoothstep(0.,.025,cr))*(.4+.6*flow)*.55;
  col+=fire(T);
  col+=vec3(.55,.12,0.)*exp(-(H-q.y)/38.)*(.6+.4*sin(t*1.3));
  col+=ember(q,t,13.,22.,.5,.5,0.,vec3(1.,.55,.15))+ember(q,t,20.,36.,.8,.5,4.,vec3(1.,.7,.25));
  return col*vign(uv,.35); }`,
  prisme: `
vec3 dos(vec2 q,vec2 uv,float t){
  vec3 base=mix(vec3(.03,.06,.13),vec3(.1,.17,.33),1.-smoothstep(0.,1.,length((uv-vec2(.5,.42))*vec2(1.,1.2))));
  float f=ringsF(q,0.,0.); float dl=ringDist(f); vec2 tl=u_tilt;
  float ph=f*.17+dot(uv-.5,vec2(1.1,.7))*.9+tl.x*.8+tl.y*.55+t*.03;
  vec3 holo=spectral(ph);
  float grat=.5+.5*sin(q.x*1.7+q.y*.9+f*3.);
  float gl=glint(uv,tl,22.);
  vec3 col=base+holo*(lineU(dl,.55)*(.55+.6*gl)+gl*.38*(.4+.6*grat)+.05);
  col+=holo*exp(-dl*.25)*.06;
  vec2 id=floor(q/9.); vec2 r=h22(id+1.3); vec2 sp=(id+.2+r*.6)*9.; vec2 dv=q-sp; float d=length(dv);
  float on=smoothstep(.93,1.,sin(t*1.7+r.x*TAU+dot(tl,r-.5)*14.));
  float star=exp(-d*d*1.2)+(exp(-abs(dv.x)*2.)*exp(-abs(dv.y)*.35)+exp(-abs(dv.y)*2.)*exp(-abs(dv.x)*.35))*.6;
  col+=on*star*mix(vec3(1.),spectral(r.y+t*.1),.4)*1.4;
  if(u_ptrOn>.5){ float pd=length(uv-u_ptr); col+=holo*exp(-pd*pd*30.)*.35; }
  return col*vign(uv,.3); }`,
  orfondu: `
vec3 dos(vec2 q,vec2 uv,float t){
  float f=ringsF(q,0.,0.);
  float tri=1.-abs(fract(f+.5)-.5)*2.;
  float hg=smoothstep(.6,1.,tri)*2.4+fbm(q*.09)*1.3;
  float gx=dFdx(hg)/upx(), gy=dFdy(hg)/upx();
  vec3 N=normalize(vec3(-gx,gy,1.));
  vec3 L=normalize(vec3(u_tilt.x*1.3+.35*cos(t*.45),-u_tilt.y*1.3+.35*sin(t*.45)+.2,.9));
  float dif=max(dot(N,L),0.); float sp=pow(max(reflect(-L,N).z,0.),38.);
  float env=.5+.5*sin(N.x*7.+N.y*4.+t*.35+u_tilt.x*2.5);
  vec3 col=mix(vec3(.22,.12,.025),vec3(.78,.55,.18),dif*.85+.1); col=mix(col,vec3(1.,.9,.6),env*.35*dif); col+=sp*vec3(1.,.96,.82)*1.3;
  col*=.75+.25*(1.-smoothstep(.2,1.1,length(uv-.5)*1.4));
  float e=min(min(q.x,W-q.x),min(q.y,H-q.y)); float bm=1.-smoothstep(4.,7.,e);
  float an=atan(q.y-H*.5,q.x-W*.5); float cg=pow(.5+.5*cos(an*2.-t*1.6),6.);
  col=mix(col,mix(vec3(.5,.32,.08),vec3(1.,.93,.65),cg),bm*.85);
  col+=ember(q,t,15.,6.,.4,.5,3.,vec3(1.,.9,.6))*.8+ember(q,t*1.1,24.,11.,.9,.45,8.,vec3(1.,.92,.7))*.6;
  return col; }`,
  neon: `
vec3 dos(vec2 q,vec2 uv,float t){
  float gl=step(.93,fract(t/5.3)); float sl=floor(q.y/7.);
  float jit=gl*(h21(vec2(sl,floor(t*24.)))-.5)*16.*step(.55,h21(vec2(sl*3.,floor(t*24.))));
  vec2 qg=q+vec2(jit,0.);
  vec3 col=mix(vec3(.02,.008,.05),vec3(.1,.035,.2),1.-smoothstep(0.,1.,length((uv-vec2(.5,.42))*vec2(1.,1.2))));
  vec3 tubes=vec3(0.);
  for(int c=0;c<3;c++){ float off=(float(c)-1.)*1.1*(1.+gl*2.); float f=ringsF(qg+vec2(off,0.),0.,0.); float idx=floor(f+.5); float dl=ringDist(f);
    vec3 tc=mix(vec3(1.,.17,.84),vec3(.13,.89,1.),mod(idx,2.));
    float fl=(.78+.22*sin(t*2.7+idx*1.9))*step(.06,h21(vec2(idx,floor(t*7.))));
    float v=(exp(-dl*dl*2.6)+exp(-dl*.55)*.45)*fl;
    tubes[c]+=v*tc[c]+exp(-dl*dl*6.)*fl*.35; }
  col+=tubes;
  float by=mod(t*38.,320.)-30.; col+=vec3(.13,.89,1.)*exp(-pow((q.y-by)/14.,2.))*.12;
  col*=.84+.16*step(.5,fract(gl_FragCoord.y/3.));
  col+=(h21(q+fract(t))-.5)*.035;
  return col*vign(uv,.35); }`,
  gravure: `
vec3 paper(vec2 q,vec2 uv){ vec3 p=vec3(.955,.925,.845)*(.92+.08*fbm(q*.35)); return p*(1.-.18*smoothstep(.5,1.05,length((uv-.5)*vec2(1.,.85))*1.45)); }
vec3 dos(vec2 q,vec2 uv,float t){
  vec3 pp=paper(q,uv);
  float f=ringsF(q,0.,0.);
  float tri=1.-abs(fract(f+.5)-.5)*2.; float hg=smoothstep(.55,1.,tri)*2.+fbm(q*.05)*2.5;
  float gx=dFdx(hg)/upx(), gy=dFdy(hg)/upx(); vec3 N=normalize(vec3(-gx,gy,1.));
  vec3 L=normalize(vec3(-.6+u_tilt.x*1.2,.55-u_tilt.y*1.2,.7)); float sh=clamp(dot(N,L),0.,1.);
  float dk=clamp(1.-sh*1.05,0.,1.)*.9;
  vec3 ink=vec3(.2,.14,.08);
  float a=.61; float s1=dot(q,vec2(cos(a),sin(a))); float h1=abs(fract(s1/2.4)-.5)*2.4;
  float l1=1.-smoothstep(dk*1.05-upx(),dk*1.05+upx(),h1);
  float s2=dot(q,vec2(cos(-a),sin(-a))); float h2=abs(fract(s2/2.8)-.5)*2.8; float w2=max(dk-.45,0.)*1.6;
  float l2=1.-smoothstep(w2-upx(),w2+upx(),h2);
  float cl=lineU(ringDist(f),.42);
  vec3 col=mix(pp,ink,max(max(l1,l2)*.62,cl*.9));
  float band=(uv.x+uv.y*.6)-mod(t*.12,2.6)+.6; col+=vec3(1.,.97,.9)*exp(-band*band*40.)*.10;
  return col; }`,
  orage: `
float boltPath(float y,float sd){ return (fbm3(vec2(y*.018,sd))-.5)*70.+(vnoise(vec2(y*.14,sd*3.))-.5)*9.; }
float flash(float t,out float k,out float ph){ float P=4.6; k=floor(t/P); ph=t-k*P;
  return smoothstep(0.,.02,ph)*(1.-smoothstep(.05,.1,ph))+.65*smoothstep(.15,.17,ph)*(1.-smoothstep(.2,.27,ph)); }
vec3 rain(vec2 q,float t,float fl){ vec2 r=mat2(cos(.18),-sin(.18),sin(.18),cos(.18))*q; vec3 c=vec3(0.);
  for(int L=0;L<2;L++){ float s=float(L); float cw=2.6+s*1.4; float cx=floor(r.x/cw); float hh=h21(vec2(cx,s*7.)); float sp=200.+hh*90.+s*60.;
    float yy=r.y-t*sp+hh*400.; float seg=fract(yy/(55.+s*25.)); float drop=smoothstep(0.,.02,seg)*(1.-smoothstep(0.,.14,seg))*step(.45,hh);
    float xw=exp(-pow((fract(r.x/cw)-.5)*cw,2.)*4.); c+=vec3(.6,.7,.85)*drop*xw*(.16+.1*s)*(1.+fl*2.); }
  return c; }
vec3 dos(vec2 q,vec2 uv,float t){
  float k,ph; float fl=flash(t,k,ph); float sd=h21(vec2(k,3.1))*50.;
  vec2 w=q*.011+vec2(t*.025,0.); float cl=fbm(w+fbm(w*1.6-t*.02)*.9);
  vec3 col=mix(vec3(.025,.035,.06),vec3(.16,.2,.28),smoothstep(.3,.85,cl));
  col*=.85+.3*(1.-uv.y);
  float x0=40.+h21(vec2(k,1.7))*108.; float bx=x0+boltPath(q.y,sd); float yEnd=150.+h21(vec2(k,8.))*80.;
  float d=abs(q.x-bx); float vis=1.-smoothstep(yEnd-30.,yEnd,q.y);
  float br=0.;
  if(q.y>55.&&q.y<yEnd*.8){ float bx2=bx+(q.y-55.)*(.5+h21(vec2(k,4.)))*(h21(vec2(k,5.))>.5?1.:-1.)+boltPath(q.y*1.7,sd+9.)*.4;
    br=exp(-pow(q.x-bx2,2.)*1.2)*.6*(1.-smoothstep(55.,yEnd*.8,q.y)); }
  float bolt=(exp(-d*d*1.4)*1.5+exp(-d*.25)*.25)*vis+br;
  float on=max(fl,(1.-smoothstep(.27,.45,ph))*step(.27,ph)*.3);
  col+=vec3(.75,.85,1.)*bolt*on;
  col+=fl*vec3(.45,.55,.8)*(.25+.7*smoothstep(.35,.8,cl))*exp(-abs(q.x-x0)/120.);
  float f=ringsF(q,0.,0.); col+=vec3(.75,.84,.95)*lineU(ringDist(f),.36)*(.1+.85*fl);
  col+=rain(q,t,fl);
  return col*vign(uv,.35); }`,
};
const DOS_GLSL_FIN = `
void main(){ vec2 q=cardQ(); vec2 uv=q/vec2(W,H); vec3 c=dos(q,uv,u_time);
  c=clamp(c,0.,1.)+(h21(gl_FragCoord.xy+fract(u_time))-.5)/255.; fragColor=vec4(c,1.); }`;
// l'image figée (appareil réglé sur « moins de mouvement ») : un instant choisi par dos
const DOS_T_FIXE = { orage: 4.62, juillet: .9 };
const DOS_GEO = (() => {
  const R = aleatoireStable(hashTexte('dos-de-carte')), w = 188, h = 263;
  return { cx: w * (0.3 + R() * 0.4), cy: h * (0.3 + R() * 0.4), k1: 2 + Math.floor(R() * 3), k2: 3 + Math.floor(R() * 4),
           p1: R() * 6.28, p2: R() * 6.28, a1: 0.08 + R() * 0.12, a2: 0.04 + R() * 0.08 };
})();
function dosPremium(k){ return !!k && Object.prototype.hasOwnProperty.call(DOS_GLSL, k); }

const dosGl = (() => {
  let gl = null, essaye = false, enMarche = false, prevu = false, toile = null, ext = null, vs = null, pertes = 0;
  let echelle = 1, couts = [], avant = 0, compilees = 0;
  const progs = new Map();        // dos -> { p, fs, u, pret } ; false si le shader a échoué
  const derniers = new Map();     // groupe -> dernier rendu (vignettes de boutique : 30 images/s)
  const reduit = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const SEL_APERCUS = Object.keys(DOS_GLSL).map(k => `.bq-dos-apercu[data-dos="${k}"] .face-back`).join(',');
  const UNIF = ['u_res', 'u_time', 'u_tilt', 'u_ptr', 'u_ptrOn', 'u_rev', 'u_photo', 'u_par', 'u_gA', 'u_gB'];

  function init(){
    if(essaye) return !!gl;
    essaye = true;
    try{
      toile = document.createElement('canvas');
      gl = toile.getContext('webgl2', { alpha: false, antialias: false, depth: false, stencil: false, premultipliedAlpha: false, powerPreference: 'low-power' });
      if(!gl) return false;
      ext = gl.getExtension('KHR_parallel_shader_compile');
      vs = gl.createShader(gl.VERTEX_SHADER);
      gl.shaderSource(vs, '#version 300 es\nin vec2 p; void main(){ gl_Position=vec4(p,0.,1.); }'); gl.compileShader(vs);
      const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
      gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
      // la carte graphique a été réinitialisée : on repart d'un contexte neuf (3 fois au plus)
      toile.addEventListener('webglcontextlost', (e) => {
        e.preventDefault(); gl = null; progs.clear(); enMarche = false;
        if(++pertes <= 3){ essaye = false; setTimeout(demarrer, 1000); }
      });
    }catch(e){ gl = null; }
    return !!gl;
  }
  function programme(k){
    let e = progs.get(k);
    if(e === undefined){
      if(compilees >= 1) return null;          // un seul shader compilé par image : pas d'à-coup
      compilees++;
      const fs = gl.createShader(gl.FRAGMENT_SHADER);
      gl.shaderSource(fs, DOS_GLSL_COMMUN + DOS_GLSL[k] + DOS_GLSL_FIN); gl.compileShader(fs);
      const p = gl.createProgram(); gl.attachShader(p, vs); gl.attachShader(p, fs);
      gl.bindAttribLocation(p, 0, 'p'); gl.linkProgram(p);
      e = { p, fs, u: {}, pret: false };
      progs.set(k, e);
    }
    if(!e) return null;
    if(!e.pret){
      if(ext && !gl.getProgramParameter(e.p, ext.COMPLETION_STATUS_KHR)) return null;   // compilation en cours
      if(!gl.getProgramParameter(e.p, gl.LINK_STATUS)){
        console.error('dos premium', k, gl.getShaderInfoLog(e.fs) || gl.getProgramInfoLog(e.p));
        progs.set(k, false); return null;
      }
      e.pret = true;
      gl.useProgram(e.p);
      for(const n of UNIF) e.u[n] = gl.getUniformLocation(e.p, n);
      const G = DOS_GEO;
      gl.uniform4f(e.u.u_gA, G.cx, G.cy, G.k1, G.k2); gl.uniform4f(e.u.u_gB, G.p1, G.p2, G.a1, G.a2);
      gl.uniform2f(e.u.u_ptr, .5, .5); gl.uniform1f(e.u.u_ptrOn, 0); gl.uniform1f(e.u.u_rev, 99);
      gl.uniform1i(e.u.u_photo, 0); gl.uniform1f(e.u.u_par, 1);
    }
    return e;
  }
  // le dos d'une carte : celui de l'aperçu qui la contient, sinon le mien
  function dosDe(fb){
    const ap = fb.closest('.bq-dos-apercu');
    return ap ? ap.dataset.dos : document.body.dataset.dos;
  }
  function retirer(c){ const fb = c.parentNode; if(fb) fb.classList.remove('dos-gl-on'); c.remove(); }
  function nettoyer(){
    for(const c of document.querySelectorAll('canvas.dos-gl')){
      const k = c.parentNode ? dosDe(c.parentNode) : null;
      if(!dosPremium(k) || progs.get(k) === false || !gl) retirer(c);
    }
  }
  function present(){
    return dosPremium(document.body.dataset.dos) || !!document.querySelector(SEL_APERCUS);
  }

  function image(now){
    if(!gl || document.hidden){ enMarche = false; return; }
    compilees = 0;
    nettoyer();
    const moi = dosPremium(document.body.dataset.dos);
    const faces = document.querySelectorAll(moi ? '.face-back' : SEL_APERCUS);
    if(!faces.length){ enMarche = false; return; }      // plus aucun dos premium : l'observateur relancera
    const dpr = Math.min(2, window.devicePixelRatio || 1) * echelle;
    const groupes = new Map();
    for(const fb of faces){
      const k = dosDe(fb);
      if(!dosPremium(k) || progs.get(k) === false) continue;
      if(fb.closest('.card.flipped')) continue;                     // carte déjà retournée
      const c3d = fb.closest('.c3d-carte');
      if(c3d && !c3d.classList.contains('retournee')) continue;     // carte en grand, côté face
      const r = fb.getBoundingClientRect();
      if(!r.width || r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) continue;
      let c = fb.querySelector(':scope > canvas.dos-gl');
      if(!c){ c = document.createElement('canvas'); c.className = 'dos-gl'; c.setAttribute('aria-hidden', 'true'); fb.prepend(c); }
      // taille de la mise en page × agrandissement à l'écran (arrondi, pour ne pas
      // redimensionner à chaque inclinaison)
      const lw = fb.offsetWidth || r.width, lh = fb.offsetHeight || r.height;
      const f = Math.max(.5, Math.min(3, Math.round(r.width / lw * 4) / 4));
      if(!c._f || Math.abs(f - c._f) > .3) c._f = f;
      let w = Math.round(lw * c._f * dpr), h = Math.round(lh * c._f * dpr);
      const px = w * h;
      if(px > 420000){ const s = Math.sqrt(420000 / px); w = Math.round(w * s); h = Math.round(h * s); }
      const vignette = !c3d && !!fb.closest('.bq-dos-apercu');
      const cle = k + '|' + w + '|' + h + '|' + (c3d ? 'g' : vignette ? 'v' : 'n');
      let g = groupes.get(cle);
      if(!g){ g = { k, w, h, c3d, vignette, liste: [] }; groupes.set(cle, g); }
      g.liste.push(c);
    }
    const t = now / 1000;
    let anime = false, maxW = 0, maxH = 0;
    for(const g of groupes.values()){ maxW = Math.max(maxW, g.w); maxH = Math.max(maxH, g.h); }
    if(toile.width < maxW || toile.height < maxH){ toile.width = Math.max(toile.width, maxW); toile.height = Math.max(toile.height, maxH); }
    for(const [cle, g] of groupes){
      if(reduit && g.liste.every(c => c.dataset.fait === cle)) continue;
      if(!reduit && g.vignette && now - (derniers.get(cle) || 0) < 32){ anime = true; continue; }
      const e = programme(g.k);
      if(!e){ if(progs.get(g.k) !== false) anime = true; continue; }
      derniers.set(cle, now);
      let tilt;
      if(g.c3d){
        const s = g.c3d.style;
        tilt = [(parseFloat(s.getPropertyValue('--ry')) || 0) / 20, -(parseFloat(s.getPropertyValue('--rx')) || 0) / 16];
      } else tilt = reduit ? [.15, -.1] : [Math.sin(t * .7) * .42, Math.sin(t * .53 + 1) * .28];
      gl.viewport(0, 0, g.w, g.h); gl.useProgram(e.p);
      gl.uniform2f(e.u.u_res, g.w, g.h); gl.uniform1f(e.u.u_time, reduit ? (g.k in DOS_T_FIXE ? DOS_T_FIXE[g.k] : 2.2) : t);
      gl.uniform2f(e.u.u_tilt, tilt[0], tilt[1]);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      for(const c of g.liste){
        if(c.width !== g.w || c.height !== g.h){ c.width = g.w; c.height = g.h; }
        c.getContext('2d').drawImage(toile, 0, toile.height - g.h, g.w, g.h, 0, 0, g.w, g.h);
        c.parentNode.classList.add('dos-gl-on');
        if(reduit) c.dataset.fait = cle;
      }
      if(!reduit) anime = true;
    }
    // un appareil qui peine : on dessine moins de pixels
    if(anime && avant){ couts.push(now - avant);
      if(couts.length >= 60){ const m = couts.reduce((a, b) => a + b, 0) / couts.length; couts = [];
        if(m > 40 && echelle > .5) echelle -= .25; } }
    avant = anime ? now : 0;
    if(anime) requestAnimationFrame(image);
    else setTimeout(() => requestAnimationFrame(image), 400);
  }
  function demarrer(){
    if(!present()){ if(document.querySelector('canvas.dos-gl')) nettoyer(); return; }
    if(!init()) return;
    if(!enMarche){ enMarche = true; avant = 0; requestAnimationFrame(image); }
  }
  // une carte qui apparaît, un dos qui change : on regarde s'il y a un dos premium à dessiner
  new MutationObserver(() => {
    if(enMarche || prevu) return;
    prevu = true;
    requestAnimationFrame(() => { prevu = false; demarrer(); });
  }).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['data-dos'] });
  document.addEventListener('visibilitychange', () => { if(!document.hidden) demarrer(); });
  return { demarrer };
})();
'''

BLOC_CSS = r'''
/* ---------- patch199 : les dos premium (rendu WebGL sous le liseré, les coins et l'épingle) ---------- */
body[data-dos="comete"], .bq-dos-apercu[data-dos="comete"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #2A4386 0%, #1F2A61 55%, #0B1230 100%);
  --dos-liseret: rgba(220,232,255,.55); --dos-or: #E8F0FF; --dos-embleme: #081428; --dos-anneau: rgba(8,20,40,.92); --dos-halo: rgba(140,180,255,.35);
}
body[data-dos="juillet"], .bq-dos-apercu[data-dos="juillet"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #2B346E 0%, #222651 55%, #0C0F2C 100%);
  --dos-liseret: rgba(255,255,255,.6); --dos-or: #FFFFFF; --dos-embleme: #0C1638; --dos-anneau: rgba(224,82,82,.95); --dos-halo: rgba(255,255,255,.2);
}
body[data-dos="maree"], .bq-dos-apercu[data-dos="maree"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #3AA0BD 0%, #28738C 55%, #0E3A4C 100%);
  --dos-liseret: rgba(214,244,250,.6); --dos-or: #D6F4FA; --dos-embleme: #0A3D52; --dos-anneau: rgba(10,61,82,.92); --dos-halo: rgba(120,230,255,.3);
}
body[data-dos="feu"], .bq-dos-apercu[data-dos="feu"]{
  --dos-fond: radial-gradient(circle at 50% 50%, #9A3A12 0%, #712D11 50%, #2A0904 100%);
  --dos-liseret: rgba(255,170,90,.55); --dos-or: #FFB463; --dos-embleme: #1E0805; --dos-anneau: rgba(30,8,5,.92); --dos-halo: rgba(255,110,20,.45);
}
body[data-dos="prisme"], .bq-dos-apercu[data-dos="prisme"]{
  --dos-fond: linear-gradient(135deg, #2E3653 0%, #38597C 35%, #5B3F7A 65%, #2E3653 100%);
  --dos-liseret: rgba(230,236,245,.75); --dos-or: #EEF3FA; --dos-embleme: #0E1A33; --dos-anneau: rgba(14,26,51,.92); --dos-halo: rgba(200,160,255,.3);
}
body[data-dos="orfondu"], .bq-dos-apercu[data-dos="orfondu"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #C99A45 0%, #A07836 55%, #5A3E12 100%);
  --dos-liseret: rgba(255,241,184,.7); --dos-or: #F6D77A; --dos-embleme: #120B02; --dos-anneau: rgba(18,11,2,.92); --dos-halo: rgba(246,215,122,.35);
}
body[data-dos="neon"], .bq-dos-apercu[data-dos="neon"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #2A2258 0%, #1F1A3B 55%, #0A0618 100%);
  --dos-liseret: rgba(32,227,255,.7); --dos-or: #FF8CF0; --dos-embleme: #0A0418; --dos-anneau: rgba(10,4,24,.92); --dos-halo: rgba(255,43,214,.5);
}
body[data-dos="gravure"], .bq-dos-apercu[data-dos="gravure"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #D9CFBC 0%, #BBB19F 60%, #8F846F 100%);
  --dos-liseret: rgba(59,42,23,.85); --dos-or: #3B2A17; --dos-embleme: #F2E8D2; --dos-anneau: rgba(233,221,194,.95); --dos-halo: transparent;
}
body[data-dos="orage"], .bq-dos-apercu[data-dos="orage"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #44506C 0%, #323D56 55%, #121828 100%);
  --dos-liseret: rgba(201,214,234,.6); --dos-or: #C9D6EA; --dos-embleme: #0A1020; --dos-anneau: rgba(10,16,32,.92); --dos-halo: rgba(170,200,255,.25);
}
body[data-dos="gravure"] .face-back:not(.bq-dos-apercu .face-back) .dos-motif path, .bq-dos-apercu[data-dos="gravure"] .face-back .dos-motif path{ stroke: rgba(59,42,23,.3); }
.face-back.dos-gl-on{ isolation: isolate; }
.face-back > canvas.dos-gl{ position: absolute; inset: 0; width: 100%; height: 100%; display: block; border-radius: inherit; pointer-events: none; }
.face-back.dos-gl-on .dos-motif{ display: none; }
.face-back.dos-gl-on::before, .face-back.dos-gl-on .dos-coin, .face-back.dos-gl-on .dos-embleme{ z-index: 1; }
.face-back.dos-gl-on::after{ z-index: 2; }
.face-back.dos-gl-on .dos-coin{ opacity: .9; }
.face-back.dos-gl-on .dos-embleme{
  box-shadow: 0 0 0 2px var(--dos-or), 0 0 0 7px var(--dos-anneau), 0 0 0 8.5px var(--dos-liseret), 0 0 22px var(--dos-halo, transparent);
}
'''

js = lire('app.js')
assert 'patch199' not in js
avant = u"""  return { demarrer };
})();

// ---------- la boutique en euros ----------"""
assert js.count(avant) == 1
js = js.replace(avant, u"""  return { demarrer };
})();
""" + BLOC_JS + u"""
// ---------- la boutique en euros ----------""")
ecrire('app.js', js)

css = lire('style.css')
assert 'patch199' not in css
ecrire('style.css', css.rstrip('\n') + '\n' + BLOC_CSS)
print(u'patch199 applique. Lancer : python3 maj-version.py')
