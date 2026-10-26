# -*- coding: utf-8 -*-
u"""
patch201 — les skins de carte : moteur WebGL (animé sur la carte en grand,
image figée dans les grilles et les vitrines), choix du skin dans la fiche
d'une carte (Terra et Front), skins visibles dans la vitrine des autres.
SQL : _boutique-euros/13-skins.sql (à passer avant de pousser).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)

BLOC_JS = r'''
// ---------- patch201 : les skins de carte ----------
// Un skin habille l'intérieur d'une carte (photo, fond, textes) ; le cadre de
// rareté reste. Animé sur la carte en grand, image figée ailleurs (grilles,
// vitrines) : une seule image par carte, gardée en mémoire. Rendu WebGL 2,
// mêmes outils que les dos premium (DOS_GLSL_COMMUN), au format de .mini-int.
const SKIN_GLSL_COMMUN = DOS_GLSL_COMMUN.replace('H=263.', 'H=285.')
  .replace('vec4 photoRect(float b){ return vec4(b,b,W-b,b+(H-2.*b)*.6); }', 'vec4 photoRect(float b){ return vec4(5.2,5.2,W-5.2,116.); }');
const SKIN_GLSL = {
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
vec3 face(vec2 q,vec2 uv,float t){
  float b=5.; vec4 R=photoRect(b); float ii=interior(q,b); float ip=inR(q,R);
  float an=atan(q.y-H*.5,q.x-W*.5);
  vec3 frame=mix(vec3(.38,.46,.66),vec3(.93,.97,1.),pow(.5+.5*sin(an*2.+t*.6+u_tilt.x*2.5),3.))*(.85+.3*glint(uv,u_tilt,8.));
  vec3 inner=mix(vec3(.02,.035,.1),vec3(.05,.08,.2),1.-smoothstep(.3,1.,uv.y))+stars(q,u_tilt*.5,t,.16)*.6;
  vec2 s=photoUV(q,R); vec3 p=photo(s); float L=lum(p);
  vec3 night=vec3(.03,.06,.16)+p*vec3(.3,.42,.85)*1.05;
  night+=vec3(1.,.78,.42)*smoothstep(.72,.95,L)*smoothstep(.35,.7,s.y)*.28;
  float sky=smoothstep(.5,.78,L)*(1.-smoothstep(.2,.6,s.y));
  night+=stars(q*1.4,u_tilt,t,.5)*sky*1.2;
  vec3 col=mix(inner,night,ip);
  float li; col+=comet(q,t+2.,7.,vec2(-30.,10.),vec2(225.,140.),.8,li)*(.45+.55*ip);
  col=mix(frame,col,ii);
  if(u_rev<1.5){ float l2; col+=comet(q,u_rev/1.4*.6*7.,7.,vec2(-60.,-20.),vec2(250.,290.),1.6,l2)*1.3; }
  return col; }`,
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
vec3 face(vec2 q,vec2 uv,float t){
  float b=5.; vec4 R=photoRect(b); float ii=interior(q,b); float ip=inR(q,R);
  vec3 frame=q.x<W/3.?vec3(.16,.27,.62):(q.x<2.*W/3.?vec3(.95,.95,.97):vec3(.86,.24,.27));
  frame*=.82+.3*glint(uv,u_tilt,10.);
  vec3 lc; vec3 fw=fireworks(q,t,vec4(25.,20.,163.,92.),.85,lc);
  vec2 s=photoUV(q,R); vec3 p=photo(s);
  vec3 night=p*vec3(.36,.42,.7)*.85+p*min(lc,vec3(.8))*.75;
  vec3 inner=mix(vec3(.03,.05,.15),vec3(.07,.1,.26),1.-smoothstep(.4,1.,uv.y))+lc*.08;
  vec3 col=mix(inner,night,ip)+fw*(.35+.65*ip);
  col=mix(frame,col,ii);
  if(u_rev<1.8){ vec3 l2=vec3(0.);
    col+=burst(q,vec2(94.,112.),u_rev,vec3(1.,.96,.9),1.7,vec2(3.,1.),l2);
    col+=burst(q,vec2(52.,70.),max(u_rev-.18,0.),vec3(.38,.56,1.),1.1,vec2(5.,2.),l2)*step(.18,u_rev);
    col+=burst(q,vec2(138.,76.),max(u_rev-.3,0.),vec3(1.,.3,.34),1.1,vec2(7.,4.),l2)*step(.3,u_rev);
    col+=l2*.12+p*min(l2,vec3(.7))*.5*ip; }
  return col; }`,
  maree: `
float caustic(vec2 p0,float t){ vec2 p=p0-250.; vec2 i=p; float c=1.; float inten=.005;
  for(int n=0;n<5;n++){ float tt=t*(1.-3.5/float(n+1)); i=p+vec2(cos(tt-i.x)+sin(tt+i.y),sin(tt-i.y)+cos(tt+i.x));
    c+=1./length(vec2(p.x/(sin(i.x+tt)/inten),p.y/(cos(i.y+tt)/inten))); }
  c/=5.; c=1.17-pow(c,1.4); return pow(abs(c),8.); }
vec3 bubbles(vec2 q,float t){ vec2 p=q; p.y+=t*14.; vec2 id=floor(p/16.); vec2 r=h22(id+2.); vec2 cc=(id+.2+r*.6)*16.; cc.x+=sin(t*2.+r.y*9.)*2.;
  float d=length(p-cc); float rr=.6+r.x*1.2; float bub=step(.6,r.y)*((1.-smoothstep(rr,rr+.25,d))-(1.-smoothstep(rr-.5,rr-.15,d))*.75);
  return bub*.35*vec3(.8,1.,1.); }
vec3 face(vec2 q,vec2 uv,float t){
  float b=5.; vec4 R=photoRect(b); float ii=interior(q,b); float ip=inR(q,R);
  float g=glint(uv,u_tilt,9.); float ca=caustic(q*.05+u_tilt*.3+vec2(10.,0.),t*.45);
  vec3 frame=mix(vec3(.1,.45,.56),vec3(.7,.96,1.),.3+.7*g)+ca*.15;
  vec3 inner=mix(vec3(.02,.15,.22),vec3(.03,.28,.38),1.-smoothstep(.3,1.,uv.y))+vec3(.5,.9,1.)*ca*.18;
  vec2 s=photoUV(q,R); float m=smoothstep(.58,1.,s.y);
  s.x+=sin(s.y*95.+t*3.)*.004*m+sin(s.y*37.-t*2.)*.003*m; s.y+=sin(s.x*60.+t*2.2)*.002*m;
  vec3 p=photo(s); p=mix(p,p*vec3(.8,1.02,1.08),.5); p+=vec3(.6,.95,1.)*ca*(.1+.25*m);
  vec3 col=mix(inner,p,ip)+bubbles(q,t)*(1.-ip*.4);
  col=mix(frame,col,ii);
  if(u_rev<1.4){ float x=u_rev/1.4; float bb=(uv.x*.7+uv.y*.7)-(x*2.2-.4); col+=vec3(.75,1.,1.)*exp(-bb*bb*18.)*.55*(1.-x*.4);
    float rr=abs(length(q-vec2(94.,131.))-x*210.); col+=vec3(.7,1.,1.)*exp(-rr*rr*.02)*.35*(1.-x); }
  return col; }`,
  feu: `
vec3 face(vec2 q,vec2 uv,float t){
  float b=5.; vec4 R=photoRect(b); float ii=interior(q,b); float ip=inR(q,R);
  float k=.5+.5*sin(t*2.4);
  vec3 frame=mix(vec3(.18,.02,0.),vec3(1.,.45,.03),pow(uv.y,1.4))*(.65+.55*k)+vec3(.4,.1,0.)*vnoise(q*.2+t*2.)*.4;
  vec3 inner=mix(vec3(.08,.015,.008),vec3(.18,.04,.01),smoothstep(.5,1.,uv.y));
  vec2 s=photoUV(q,R); float hm=smoothstep(.45,1.,s.y);
  s.x+=(vnoise(vec2(q.y*.25-t*3.,q.x*.05))-.5)*.014*hm;
  vec3 p=photo(s); p=pow(p,vec3(1.1))*vec3(1.12,.86,.64); p*=mix(.55,1.,smoothstep(0.,.45,s.y));
  vec3 col=mix(inner,p,ip);
  float v=(R.w-q.y)/34.; float fl=fbm(vec2(q.x*.075,q.y*.06+t*1.7))*1.5-v*1.25-.15+.15*sin(t*3.+q.x*.1);
  col+=fire(max(fl,0.)*1.7)*ip*(1.-smoothstep(0.,1.2,v));
  col+=vec3(.5,.1,0.)*exp(-(H-b-q.y)/12.)*(.5+.5*k)*ii;
  col+=ember(q,t,12.,26.,.6,.45,1.,vec3(1.,.55,.15))+ember(q,t*1.3,19.,40.,.9,.4,7.,vec3(1.,.75,.3));
  col=mix(frame,col,ii);
  if(u_rev<1.5){ float x=u_rev/1.5; float fr0=H*(1.1-x*1.5); float vv=(q.y-fr0)/40.;
    float fr=fbm(vec2(q.x*.06,q.y*.05+u_rev*3.))*1.4-abs(vv)*1.1; col+=fire(max(fr,0.)*2.)*(1.-x*.6); }
  return col; }`,
  prisme: `
vec3 face(vec2 q,vec2 uv,float t){
  float b=5.; vec4 R=photoRect(b); float ii=interior(q,b); float ip=inR(q,R); vec2 tl=u_tilt;
  float f=ringsF(q,0.,0.);
  vec3 holo=spectral(f*.12+dot(uv-.5,vec2(1.2,.8))+tl.x*.9+tl.y*.6+t*.025);
  float gl=glint(uv,tl,16.);
  vec3 frame=mix(vec3(.6,.65,.75),vec3(.97,.98,1.),.5+.5*sin((q.x+q.y)*.05+tl.x*3.))+holo*.35*(.3+gl);
  vec3 inner=mix(vec3(.04,.07,.15),vec3(.08,.13,.25),1.-smoothstep(0.,.5,abs(uv.y-.78)));
  vec2 s=photoUV(q,R); vec3 p=photo(s);
  vec3 col=mix(inner,p*(1.+.15*gl),ip);
  float grat=.5+.5*sin(q.x*1.3+q.y*.75+f*2.);
  float foilM=(ip*.55+(1.-ip)*.75)*(.25+.75*gl);
  col+=holo*foilM*(.18+.22*grat)*(.6+.4*lum(p)*ip);
  col+=holo*lineU(ringDist(f),.3)*.25*(1.-ip)*(.4+gl);
  vec2 id=floor(q/7.); vec2 r=h22(id+4.1); vec2 sp=(id+.2+r*.6)*7.; vec2 dv=q-sp; float d=length(dv);
  float on=smoothstep(.92,1.,sin(t*1.5+r.x*TAU+dot(tl,r-.5)*16.));
  col+=on*(exp(-d*d*1.4)+(exp(-abs(dv.x)*2.2)*exp(-abs(dv.y)*.4)+exp(-abs(dv.y)*2.2)*exp(-abs(dv.x)*.4))*.5)*1.3;
  if(u_ptrOn>.5){ float pd=length(uv-u_ptr); col+=(holo*.4+.2)*exp(-pd*pd*25.)*.6; }
  col=mix(frame,col,ii);
  if(u_rev<1.4){ float x=u_rev/1.4; float bb=(uv.x*.8+uv.y*.6)-(x*2.4-.5); col+=spectral(uv.x+uv.y+x)*exp(-bb*bb*14.)*.8*(1.-x*.5); }
  return col; }`,
  orfondu: `
vec3 face(vec2 q,vec2 uv,float t){
  float b=7.; vec4 R=photoRect(b); float ii=interior(q,b); float ip=inR(q,R);
  float eo=min(min(q.x,W-q.x),min(q.y,H-q.y)); float pr=sin(clamp(eo/b,0.,1.)*PI);
  float hg=pr*3.+fbm(q*.25)*.25; float gx=dFdx(hg)/upx(), gy=dFdy(hg)/upx(); vec3 N=normalize(vec3(-gx,gy,1.));
  vec3 L=normalize(vec3(u_tilt.x*1.2+.3*cos(t*.5),-u_tilt.y*1.2+.3*sin(t*.5)+.2,.9));
  float dif=max(dot(N,L),0.); float sp=pow(max(reflect(-L,N).z,0.),30.);
  float an=atan(q.y-H*.5,q.x-W*.5); float cg=pow(.5+.5*cos(an*2.-t*1.5),5.);
  vec3 frame=mix(vec3(.3,.18,.04),vec3(.95,.74,.3),dif)+sp*vec3(1.,.95,.8)+cg*vec3(.6,.5,.25);
  vec3 inner=mix(vec3(.07,.045,.01),vec3(.16,.1,.02),1.-smoothstep(.4,1.,uv.y));
  vec2 s=photoUV(q,R); vec3 p=photo(s); float Lp=lum(p);
  vec3 g=mix(p,vec3(Lp)*vec3(1.1,.9,.6),.45)*1.06; g=mix(g,inner,smoothstep(.75,1.,s.y)*.85);
  g+=vec3(1.,.88,.5)*glint(uv,u_tilt,14.)*.22;
  vec3 col=mix(inner,g,ip);
  col+=ember(q,t,15.,8.,.5,.5,3.,vec3(1.,.88,.55))*.8+ember(q,t*1.2,23.,13.,.8,.4,9.,vec3(1.,.92,.65))*.6;
  col=mix(frame,col,ii);
  if(u_rev<1.4){ float x=u_rev/1.4; float rr=abs(length((q-vec2(94.,131.))*vec2(1.,.8))-x*190.);
    col+=vec3(1.,.85,.45)*exp(-rr*rr*.012)*.9*(1.-x); col+=vec3(1.,.9,.6)*exp(-x*6.)*.35; }
  return col; }`,
  neon: `
vec3 face(vec2 q,vec2 uv,float t){
  float b=4.; vec4 R=photoRect(b); float ii=interior(q,b); float ip=inR(q,R);
  float gl=step(.93,fract(t/5.1)); float sl=floor(q.y/6.);
  float jit=gl*(h21(vec2(sl,floor(t*24.)))-.5)*.05*step(.55,h21(vec2(sl*3.,floor(t*24.))));
  if(u_rev<1.){ jit+=(h21(vec2(sl,floor(u_rev*30.)))-.5)*.12*(1.-u_rev)*step(.4,h21(vec2(sl*2.,floor(u_rev*30.)))); }
  vec2 s=photoUV(q,R); s.x+=jit;
  vec2 tx=1.5/vec2(textureSize(u_photo,0));
  float l=lum(photo(s));
  float lx=lum(photo(s+vec2(tx.x,0.)))-lum(photo(s-vec2(tx.x,0.)));
  float ly=lum(photo(s+vec2(0.,tx.y)))-lum(photo(s-vec2(0.,tx.y)));
  float e=length(vec2(lx,ly));
  vec3 mag=vec3(1.,.17,.84), cy=vec3(.13,.89,1.);
  vec3 duo=mix(vec3(.03,.008,.07),mix(vec3(.35,.05,.45),vec3(.05,.25,.5),s.y),smoothstep(.1,.9,l));
  vec3 ec=mix(mag,cy,smoothstep(.2,.8,s.x+.25*sin(t*.8+s.y*3.)));
  float rch=lum(photo(s+vec2(.006,0.)));
  vec3 ph=duo+ec*smoothstep(.06,.3,e)*1.6+vec3(rch-l,0.,l-rch)*.4;
  ph*=.82+.18*step(.5,fract(gl_FragCoord.y/3.));
  vec3 inner=mix(vec3(.025,.01,.06),vec3(.07,.02,.13),1.-smoothstep(.3,1.,uv.y));
  vec3 col=mix(inner,ph,ip);
  float dt=abs(sdBox(q-vec2(W,H)*.5,vec2(W,H)*.5-2.6,8.)); float an=atan(q.y-H*.5,q.x-W*.5);
  vec3 tc=mix(mag,cy,.5+.5*sin(an-t*1.6)); float fl=.85+.15*sin(t*13.)*step(.97,fract(t*.37));
  float tube=(exp(-dt*dt*2.5)*1.2+exp(-dt*.45)*.5)*fl;
  col=mix(vec3(.03,.01,.06),col,ii);
  col+=tc*tube+vec3(1.)*exp(-dt*dt*8.)*.4*fl;
  if(u_rev<1.){ col+=vec3(1.)*exp(-u_rev*5.)*.5*tube; }
  col+=(h21(q+fract(t))-.5)*.03;
  return col; }`,
  gravure: `
vec3 paper(vec2 q,vec2 uv){ vec3 p=vec3(.955,.925,.845)*(.92+.08*fbm(q*.35)); return p*(1.-.18*smoothstep(.5,1.05,length((uv-.5)*vec2(1.,.85))*1.45)); }
vec3 face(vec2 q,vec2 uv,float t){
  float b=6.; vec4 R=photoRect(b); float ip=inR(q,R); vec3 ink=vec3(.19,.13,.07);
  vec3 pp=paper(q,uv); vec3 col=pp;
  float eo=min(min(q.x,W-q.x),min(q.y,H-q.y));
  col=mix(col,ink,max(lineU(abs(eo-2.8),.45),lineU(abs(eo-4.9),.25))*.9);
  vec2 s=photoUV(q,R); vec3 p=photo(s); float L=clamp((lum(p)-.5)*1.35+.55,0.,1.);
  float dk=clamp(1.-L+dot(uv-.5,u_tilt)*.25,0.,1.);
  float a=.6; float s1=dot(q,vec2(cos(a),sin(a))); float h1=abs(fract(s1/1.9)-.5)*1.9; float w1=dk*.9;
  float l1=1.-smoothstep(w1-upx(),w1+upx(),h1);
  float s2=dot(q,vec2(cos(-a),sin(-a))); float h2=abs(fract(s2/2.2)-.5)*2.2; float w2=max(dk-.5,0.)*1.7;
  float l2=1.-smoothstep(w2-upx(),w2+upx(),h2);
  col=mix(col,mix(pp,ink,max(l1,l2)*.92),ip);
  float dr=abs(sdBox(q-(R.xy+R.zw)*.5,(R.zw-R.xy)*.5,0.)); col=mix(col,ink,lineU(dr,.45)*.95);
  float band=(uv.x+uv.y*.6)-mod(t*.12,2.6)+.6; col+=vec3(1.,.97,.9)*exp(-band*band*40.)*.08;
  if(u_rev<1.4){ float x=u_rev/1.4; float ring=1.-x; col=mix(col,ink,(1.-smoothstep(0.,max(30.*ring,.01),eo))*ring*.85); }
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
vec3 face(vec2 q,vec2 uv,float t){
  float b=5.; vec4 R=photoRect(b); float ii=interior(q,b); float ip=inR(q,R);
  float k,ph; float fl=flash(t,k,ph);
  if(u_rev<.6){ fl=max(fl,smoothstep(0.,.03,u_rev)*(1.-smoothstep(.06,.12,u_rev))+.8*smoothstep(.2,.22,u_rev)*(1.-smoothstep(.28,.36,u_rev))); }
  vec3 frame=mix(vec3(.27,.33,.44),vec3(.08,.11,.18),uv.y)+glint(uv,u_tilt,10.)*.18+fl*.35;
  vec3 inner=mix(vec3(.025,.04,.08),vec3(.06,.08,.14),1.-smoothstep(.3,1.,uv.y))*(1.+fl*1.5);
  vec2 s=photoUV(q,R); vec3 p=photo(s); float L=lum(p);
  vec3 g=mix(vec3(L),p,.35)*vec3(.72,.82,1.05); g*=mix(.45,.85,smoothstep(0.,.6,s.y)); g*=1.+fl*(.75+.5*(1.-s.y));
  float x0=40.+h21(vec2(k,1.7))*108.; float sd=h21(vec2(k,3.1))*50.;
  float d=abs(q.x-(x0+boltPath(q.y,sd)*.7)); float vis=1.-smoothstep(R.w*.5,R.w*.75,q.y);
  g+=vec3(.85,.92,1.)*(exp(-d*d*1.6)*1.6+exp(-d*.3)*.3)*vis*fl; g=min(g,vec3(1.));
  vec3 col=mix(inner,g,ip)+rain(q,t,fl)*(.6+.4*ip);
  col=mix(frame,col,ii);
  return col; }`,
};
const SKIN_GLSL_FIN = `
void main(){ vec2 q=cardQ(); vec2 uv=q/vec2(W,H); vec3 c=face(q,uv,u_time);
  c=clamp(c,0.,1.)+(h21(gl_FragCoord.xy+fract(u_time))-.5)/255.; fragColor=vec4(c,1.); }`;
const SKIN_NOMS = { comete: 'Comète', juillet: '14 Juillet', maree: 'Marée', feu: 'Brasier', prisme: 'Prisme', orfondu: 'Or fondu', neon: 'Néon', gravure: 'Gravure', orage: 'Orage' };
const SKIN_T_FIXE = { orage: 4.62, juillet: .9 };
const skinCle = (id) => id ? String(id).replace(/^skin-/, '') : null;
const skinConnu = (k) => !!k && Object.prototype.hasOwnProperty.call(SKIN_GLSL, k);

let mesSkinsCartes = null;   // Map 'terra|83137' -> { skin, nom }
let mesSkins = null;         // [{ id, nom }] : les skins que je possède
async function chargerMesSkinsCartes(force){
  if(mesSkinsCartes && !force) return mesSkinsCartes;
  const m = new Map();
  try{
    const { data, error } = await sb.rpc('skin_cartes', { p_joueur: window.__monId });
    if(!error) for(const r of data || []) m.set(r.source + '|' + r.code, { skin: r.skin, nom: r.nom });
  }catch(e){}
  mesSkinsCartes = m;
  skinGl.rafraichir();
  return m;
}
async function chargerMesSkins(force){
  if(mesSkins && !force) return mesSkins;
  try{ const { data, error } = await sb.rpc('garde_robe_skins'); mesSkins = error ? [] : (data || []); }catch(e){ mesSkins = []; }
  return mesSkins;
}
function skinDeMaCarte(source, code){
  const r = mesSkinsCartes && mesSkinsCartes.get(source + '|' + code);
  return r ? skinCle(r.skin) : undefined;
}

const skinGl = (() => {
  let gl = null, essaye = false, enMarche = false, prevu = false, sale = true, toile = null, ext = null, vs = null;
  let compilees = 0, pertes = 0, echelle = 1, couts = [], avant = 0, dernierScan = 0;
  const progs = new Map(), textures = new Map(), figees = new Map();
  const revs = new WeakMap();   // carte en grand -> moment où sa face est apparue
  const reduit = matchMedia('(prefers-reduced-motion: reduce)').matches;
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
      gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
      toile.addEventListener('webglcontextlost', (e) => {
        e.preventDefault(); gl = null; progs.clear(); textures.clear(); enMarche = false;
        if(++pertes <= 3){ essaye = false; sale = true; setTimeout(demarrer, 1000); }
      });
    }catch(e){ gl = null; }
    return !!gl;
  }
  function programme(k){
    let e = progs.get(k);
    if(e === undefined){
      if(compilees >= 1) return null;
      compilees++;
      const fs = gl.createShader(gl.FRAGMENT_SHADER);
      gl.shaderSource(fs, SKIN_GLSL_COMMUN + SKIN_GLSL[k] + SKIN_GLSL_FIN); gl.compileShader(fs);
      const p = gl.createProgram(); gl.attachShader(p, vs); gl.attachShader(p, fs);
      gl.bindAttribLocation(p, 0, 'p'); gl.linkProgram(p);
      e = { p, fs, u: {}, pret: false };
      progs.set(k, e);
    }
    if(!e) return null;
    if(!e.pret){
      if(ext && !gl.getProgramParameter(e.p, ext.COMPLETION_STATUS_KHR)) return null;
      if(!gl.getProgramParameter(e.p, gl.LINK_STATUS)){
        console.error('skin', k, gl.getShaderInfoLog(e.fs) || gl.getProgramInfoLog(e.p));
        progs.set(k, false); return null;
      }
      e.pret = true;
      gl.useProgram(e.p);
      for(const n of UNIF) e.u[n] = gl.getUniformLocation(e.p, n);
      const G = DOS_GEO;
      gl.uniform4f(e.u.u_gA, G.cx, G.cy, G.k1, G.k2); gl.uniform4f(e.u.u_gB, G.p1, G.p2, G.a1, G.a2);
      gl.uniform2f(e.u.u_ptr, .5, .5); gl.uniform1f(e.u.u_ptrOn, 0); gl.uniform1i(e.u.u_photo, 0);
    }
    return e;
  }
  // l'image de la carte : sa photo (chargée pour la carte graphique), sinon le dessin de ses courbes
  function versTexture(e, img){
    if(!gl) return false;
    try{
      const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      e.t = t; e.ar = (img.naturalWidth || img.width) / (img.naturalHeight || img.height) || 1.6; e.pret = true; sale = true;
      return true;
    }catch(err){ return false; }   // photo refusée par le navigateur (CORS) : on passe au dessin
  }
  function depuisSvg(e, svg){
    if(!svg){ e.echec = true; return; }
    const x = svg.cloneNode(true);
    x.setAttribute('xmlns', 'http://www.w3.org/2000/svg'); x.setAttribute('width', '320'); x.setAttribute('height', '200');
    const img = new Image();
    img.onload = () => { if(!versTexture(e, img)) e.echec = true; };
    img.onerror = () => { e.echec = true; };
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(new XMLSerializer().serializeToString(x));
  }
  function texture(mini){
    const ph = mini.querySelector('.mini-art img.art-photo');
    const cle = ph && ph.src ? ph.src : 'svg:' + mini.title;
    let e = textures.get(cle);
    if(e){ e.vu = performance.now(); return e; }
    e = { cle, t: null, ar: 1.6, pret: false, echec: false, vu: performance.now() };
    textures.set(cle, e);
    const svg = mini.querySelector('.mini-art > svg');
    if(ph && ph.src){
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => { if(!versTexture(e, img)) depuisSvg(e, svg); };
      img.onerror = () => depuisSvg(e, svg);
      img.src = ph.src + (ph.src.includes('?') ? '&' : '?') + 'gl=1';
    } else depuisSvg(e, svg);
    // pas plus de 60 images en mémoire de la carte graphique
    if(textures.size > 60){
      const vieille = [...textures.values()].sort((a, b) => a.vu - b.vu)[0];
      if(vieille && gl && vieille.t) gl.deleteTexture(vieille.t);
      textures.delete(vieille.cle);
    }
    return e;
  }
  // le skin d'une carte : posé dans le HTML (fiche, vitrine), sinon le mien dans mes grilles
  function skinDe(mini){
    if(mini.dataset.skin) return mini.dataset.skin;
    if(!mesSkinsCartes || !mesSkinsCartes.size) return null;
    if(mini.dataset.tcode && mini.parentElement && mini.parentElement.id === 'tcGrille') return skinDeMaCarte('terra', mini.dataset.tcode) || null;
    if(mini.dataset.code && !mini.classList.contains('perdue') && mini.closest('#collectionGrid')) return skinDeMaCarte('front', mini.dataset.code) || null;
    return null;
  }
  function retirer(mini){
    mini.classList.remove('skin', 'skin-anime', ...[...mini.classList].filter(c => c.startsWith('skin-')));
    const int = mini.querySelector('.mini-int');
    if(int) int.querySelectorAll(':scope > canvas.skin-gl, :scope > .skin-marque').forEach(x => x.remove());
    delete mini.dataset.skinFait;
  }
  function habiller(mini, k, anime){
    const int = mini.querySelector('.mini-int');
    let c = int.querySelector(':scope > canvas.skin-gl');
    if(!c){ c = document.createElement('canvas'); c.className = 'skin-gl'; c.setAttribute('aria-hidden', 'true'); int.prepend(c); }
    const avant = [...mini.classList].filter(x => x.startsWith('skin-') && x !== 'skin-' + k && x !== 'skin-anime');
    if(avant.length) mini.classList.remove(...avant);
    mini.classList.add('skin', 'skin-' + k);
    mini.classList.toggle('skin-anime', !!anime);
    let m = int.querySelector(':scope > .skin-marque');
    if(!anime && !m){ m = document.createElement('span'); m.className = 'skin-marque'; int.appendChild(m); }
    if(m){ if(anime) m.remove(); else m.textContent = SKIN_NOMS[k]; }
    return c;
  }
  function taille(mini, r){
    const int = mini.querySelector('.mini-int');
    const lw = int.offsetWidth || r.width, lh = int.offsetHeight || r.height;
    const f = Math.max(.5, Math.min(3, Math.round(r.width / (mini.offsetWidth || r.width) * 4) / 4));
    if(!mini._skf || Math.abs(f - mini._skf) > .3) mini._skf = f;
    const dpr = Math.min(2, window.devicePixelRatio || 1) * echelle;
    let w = Math.round(lw * mini._skf * dpr), h = Math.round(lh * mini._skf * dpr);
    if(w * h > 420000){ const s = Math.sqrt(420000 / (w * h)); w = Math.round(w * s); h = Math.round(h * s); }
    return [Math.max(8, w), Math.max(8, h)];
  }
  function rendre(e, tex, w, h, t, tilt, rev){
    if(toile.width < w || toile.height < h){ toile.width = Math.max(toile.width, w); toile.height = Math.max(toile.height, h); }
    gl.viewport(0, 0, w, h); gl.useProgram(e.p);
    gl.uniform2f(e.u.u_res, w, h); gl.uniform1f(e.u.u_time, t); gl.uniform2f(e.u.u_tilt, tilt[0], tilt[1]);
    gl.uniform1f(e.u.u_rev, rev); gl.uniform1f(e.u.u_par, tex.ar);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex.t);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }
  function copier(c, w, h){
    if(c.width !== w || c.height !== h){ c.width = w; c.height = h; }
    c.getContext('2d').drawImage(toile, 0, toile.height - h, w, h, 0, 0, w, h);
  }

  function image(now){
    if(!gl || document.hidden){ enMarche = false; return; }
    compilees = 0;
    let anime = false, attente = false, faits = 0;
    const t = now / 1000;
    // 1. les cartes en grand (fiche) : animées
    for(const mini of document.querySelectorAll('.c3d .mini')){
      const k = skinDe(mini);
      if(!skinConnu(k) || progs.get(k) === false){ if(mini.classList.contains('skin')) retirer(mini); continue; }
      const carte = mini.closest('.c3d-carte');
      const face = carte && !carte.classList.contains('retournee');
      if(!face){ if(carte) revs.delete(carte); continue; }
      const r = mini.getBoundingClientRect();
      if(!r.width || r.bottom < 0 || r.top > innerHeight) continue;
      const tex = texture(mini); const e = programme(k);
      if(!e || !tex.pret){ if(!tex.echec) attente = true; continue; }
      if(!revs.has(carte)) revs.set(carte, now);
      const [w, h] = taille(mini, r);
      const s = carte.style;
      const tilt = reduit ? [.15, -.1] : [(parseFloat(s.getPropertyValue('--ry')) || 0) / 20, -(parseFloat(s.getPropertyValue('--rx')) || 0) / 16];
      rendre(e, tex, w, h, reduit ? (SKIN_T_FIXE[k] || 2.2) : t, tilt, reduit ? 99 : (now - revs.get(carte)) / 1000);
      copier(habiller(mini, k, true), w, h);
      if(!reduit) anime = true;
    }
    // 2. les grilles et les vitrines : une image figée par carte, quelques-unes par image
    if(sale || now - dernierScan > 1000){
      dernierScan = now; sale = false;
      const sel = '.mini[data-skin]' + (mesSkinsCartes && mesSkinsCartes.size ? ', #tcGrille > .mini[data-tcode], #collectionGrid .mini[data-code]' : '');
      for(const mini of document.querySelectorAll(sel)){
        if(mini.closest('.c3d')) continue;
        const k = skinDe(mini);
        if(!skinConnu(k) || progs.get(k) === false){ if(mini.classList.contains('skin')) retirer(mini); continue; }
        const r = mini.getBoundingClientRect();
        if(!r.width || r.bottom < -300 || r.top > innerHeight + 300) continue;
        const tex = texture(mini);
        if(tex.echec) continue;
        const [w, h] = taille(mini, r);
        const cle = k + '|' + tex.cle + '|' + w + 'x' + h;
        if(mini.dataset.skinFait === cle) continue;
        if(faits >= 4){ attente = true; continue; }   // la suite à l'image suivante
        const e = programme(k);
        if(!e || !tex.pret){ attente = true; continue; }
        const c = habiller(mini, k, false);
        const deja = figees.get(cle);
        if(deja){
          if(c.width !== w || c.height !== h){ c.width = w; c.height = h; }
          c.getContext('2d').drawImage(deja, 0, 0);
        } else {
          rendre(e, tex, w, h, SKIN_T_FIXE[k] || 2.2, [.15, -.1], 99);
          copier(c, w, h);
          const garde = document.createElement('canvas'); garde.width = w; garde.height = h;
          garde.getContext('2d').drawImage(c, 0, 0);
          figees.set(cle, garde);
          if(figees.size > 40) figees.delete(figees.keys().next().value);
          faits++;
        }
        mini.dataset.skinFait = cle;
      }
      if(attente) sale = true;
    }
    if(anime && avant){ couts.push(now - avant);
      if(couts.length >= 60){ const m = couts.reduce((a, b) => a + b, 0) / couts.length; couts = [];
        if(m > 40 && echelle > .5) echelle -= .25; } }
    avant = anime ? now : 0;
    if(anime || attente || sale) requestAnimationFrame(image);
    else enMarche = false;
  }
  function present(){
    return !!document.querySelector('.mini[data-skin]') || !!(mesSkinsCartes && mesSkinsCartes.size);
  }
  function demarrer(){
    if(!present()){ document.querySelectorAll('.mini.skin').forEach(retirer); return; }
    if(!init()) return;
    if(!enMarche){ enMarche = true; avant = 0; requestAnimationFrame(image); }
  }
  function rafraichir(){ sale = true; demarrer(); }
  const relancer = () => {
    sale = true;
    if(enMarche || prevu) return;
    prevu = true;
    requestAnimationFrame(() => { prevu = false; demarrer(); });
  };
  new MutationObserver(relancer).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['data-skin'] });
  document.addEventListener('scroll', relancer, { capture: true, passive: true });
  window.addEventListener('resize', relancer);
  document.addEventListener('visibilitychange', () => { if(!document.hidden) relancer(); });
  // une carte en grand qu'on retourne côté face : l'effet d'apparition repart
  document.addEventListener('pointerup', () => setTimeout(relancer, 0));
  document.addEventListener('keyup', () => setTimeout(relancer, 0));
  return { demarrer, rafraichir };
})();

// le choix du skin, sous la carte en grand d'une fiche à moi
function choixSkinHtml(source, code){
  if(!SAISON2) return '';
  return `<div class="sk-choix" data-sk-src="${source}" data-sk-code="${echapperTexte(code)}" hidden>
      <div class="dc-tete"><span>Skin de cette carte</span><small class="sk-etat"></small></div>
      <div class="sk-rangee" role="group" aria-label="Skin de cette carte"></div>
    </div>`;
}
async function armerSkinFiche(boite){
  const el = boite && boite.querySelector('.sk-choix');
  if(!el) return;
  const source = el.dataset.skSrc, code = el.dataset.skCode;
  const [liste] = await Promise.all([chargerMesSkins(), chargerMesSkinsCartes()]);
  if(!el.isConnected || !liste.length) return;   // aucun skin : rien à choisir
  el.hidden = false;
  const mini = boite.querySelector('.c3d .mini');
  const dessiner = () => {
    const r = mesSkinsCartes.get(source + '|' + code);
    const actuel = r ? r.skin : '';
    const opts = [{ val: '', nom: 'Aucun', k: '' }].concat(liste.map(o => ({ val: o.id, nom: SKIN_NOMS[skinCle(o.id)] || o.nom, k: skinCle(o.id) })));
    el.querySelector('.sk-rangee').innerHTML = opts.map(o => `<button type="button" class="sk-opt${o.val === actuel ? ' on' : ''}" data-sk-val="${echapperTexte(o.val)}" aria-pressed="${o.val === actuel}">
        <i class="sk-pastille${o.k ? ' sk-p-' + o.k : ''}" aria-hidden="true"></i>${echapperTexte(o.nom)}</button>`).join('');
    el.querySelector('.sk-etat').textContent = actuel ? (SKIN_NOMS[skinCle(actuel)] || '') : 'aucun';
    if(mini){ const k = skinCle(actuel); if(k) mini.dataset.skin = k; else delete mini.dataset.skin; }
  };
  dessiner();
  el.addEventListener('click', async (e) => {
    const b = e.target.closest('[data-sk-val]');
    if(!b || b.disabled) return;
    const val = b.dataset.skVal;
    el.querySelectorAll('.sk-opt').forEach(x => { x.disabled = true; });
    const { error } = await sb.rpc('skin_cartes_definir', { p_source: source, p_codes: [code], p_skin: val || null });
    el.querySelectorAll('.sk-opt').forEach(x => { x.disabled = false; });
    if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); return; }
    if(val) mesSkinsCartes.set(source + '|' + code, { skin: val, nom: '' }); else mesSkinsCartes.delete(source + '|' + code);
    // la carte se remet côté face pour montrer le skin
    const carte = boite.querySelector('.c3d-carte');
    if(carte) carte.classList.remove('retournee');
    dessiner();
    skinGl.rafraichir();
  });
}
'''
BLOC_CSS = r'''
/* ---------- patch201 : les skins de carte ---------- */
/* le cadre de rareté reste ; l'intérieur prend le skin (rendu WebGL dessous, textes par-dessus) */
.mini.skin .mini-int{ position: relative; background: #000; isolation: isolate; }
.mini.skin .skin-gl{ position: absolute; inset: 0; width: 100%; height: 100%; display: block; z-index: 0; pointer-events: none; }
.mini.skin .mini-art{ background: transparent; }
.mini.skin .mini-art > svg, .mini.skin .mini-art > img, .mini.skin .mini-art .art-voile, .mini.skin .au-fond{ visibility: hidden; }
.mini.skin .mini-art, .mini.skin .mini-infos, .mini.skin .mini-lisere{ position: relative; z-index: 1; }
.mini.skin .mini-lisere{ margin: 0 4px 3px; border-radius: 2px; overflow: hidden; }
.mini .skin-marque{ position: absolute; right: 6px; top: 6px; z-index: 2; font: 700 8px/1 var(--texte, sans-serif); letter-spacing: .08em; text-transform: uppercase;
  padding: 3px 5px; border-radius: 999px; background: rgba(8,19,37,.75); color: #fff; pointer-events: none; }
.mini.skin-neon .mini-nom{ color: #fff; text-shadow: 0 0 2px #fff, 0 0 7px #FF2BD6, 0 0 14px #FF2BD6; }
.mini.skin-neon .mini-num{ color: #9FE9FF; }
.mini.skin-neon .mini-rarete{ color: #20E3FF !important; text-shadow: 0 0 6px rgba(32,227,255,.8); }
.mini.skin-neon .mini-dept{ color: transparent; -webkit-text-stroke: 1px rgba(255,43,214,.7); }
.mini.skin-neon .mini-lisere span{ box-shadow: 0 0 5px currentColor; }
.mini.skin-gravure .mini-nom{ color: #2A1D10; font-family: 'IM Fell English', Georgia, serif; font-weight: 400; }
.mini.skin-gravure .mini-num{ color: #5A4426; font-family: 'IM Fell English', Georgia, serif; font-style: italic; }
.mini.skin-gravure .mini-rarete{ color: #2A1D10 !important; font-family: 'IM Fell English', Georgia, serif; font-style: italic; font-weight: 400; }
.mini.skin-gravure .mini-dept{ color: rgba(42,29,16,.25); font-family: 'IM Fell English', Georgia, serif; font-weight: 400; }
.mini.skin-gravure .mini-lisere{ opacity: .85; }
.mini.skin-comete .mini-nom{ background: linear-gradient(100deg,#FFFFFF,#BFD3FF 45%,#FFFFFF 70%,#9DB8F5); -webkit-background-clip: text; background-clip: text; color: transparent; filter: drop-shadow(0 0 3px rgba(140,180,255,.6)); }
.mini.skin-comete .mini-num{ color: #AFC3EA; } .mini.skin-comete .mini-rarete{ color: #DCE6FF !important; } .mini.skin-comete .mini-dept{ color: rgba(200,215,255,.28); }
.mini.skin-juillet .mini-nom{ color: #fff; text-shadow: -1px 0 0 rgba(76,123,255,.9), 1px 0 0 rgba(255,77,90,.9), 0 0 8px rgba(255,255,255,.35); }
.mini.skin-juillet .mini-num{ color: #C7D3FF; } .mini.skin-juillet .mini-rarete{ color: #fff !important; } .mini.skin-juillet .mini-dept{ color: rgba(255,255,255,.22); }
.mini.skin-maree .mini-nom{ color: #F2FDFF; text-shadow: 0 0 7px rgba(110,230,255,.65); }
.mini.skin-maree .mini-num{ color: #A8E7F2; } .mini.skin-maree .mini-rarete{ color: #D6F4FA !important; } .mini.skin-maree .mini-dept{ color: rgba(214,244,250,.25); }
.mini.skin-feu .mini-nom{ color: #FFF3E0; text-shadow: 0 0 6px rgba(255,120,20,.95), 0 1px 0 #7A1800; }
.mini.skin-feu .mini-num{ color: #FFB37A; } .mini.skin-feu .mini-rarete{ color: #FFD36B !important; } .mini.skin-feu .mini-dept{ color: rgba(255,140,50,.3); }
.mini.skin-prisme .mini-nom{ background: linear-gradient(90deg,#fff,#CFE6FF 30%,#FFE3F2 55%,#E5FFE9 75%,#fff); -webkit-background-clip: text; background-clip: text; color: transparent; filter: drop-shadow(0 1px 2px rgba(0,0,0,.5)); }
.mini.skin-prisme .mini-num{ color: rgba(255,255,255,.8); } .mini.skin-prisme .mini-rarete{ color: #fff !important; } .mini.skin-prisme .mini-dept{ color: rgba(255,255,255,.25); }
.mini.skin-orfondu .mini-nom{ background: linear-gradient(100deg,#B7791F 0%,#FFF1B8 40%,#F6D77A 55%,#9A6412 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }
.mini.skin-orfondu .mini-num{ color: rgba(246,231,193,.75); } .mini.skin-orfondu .mini-rarete{ color: #F6D77A !important; } .mini.skin-orfondu .mini-dept{ color: rgba(246,215,122,.25); }
.mini.skin-orage .mini-nom{ color: #fff; text-shadow: 0 0 6px rgba(191,216,255,.5); }
.mini.skin-orage .mini-num{ color: #9FB3D1; } .mini.skin-orage .mini-rarete{ color: #C9D6EA !important; } .mini.skin-orage .mini-dept{ color: rgba(201,214,234,.2); }
/* le choix du skin, sous la carte en grand */
.sk-choix{ width: min(360px, 100%); margin: 10px auto 0; text-align: left; background: rgba(15,31,56,.6); border: 1px solid rgba(169,188,212,.18); border-radius: 14px; padding: 10px 12px; display: grid; gap: 8px; }
.sk-choix[hidden]{ display: none; }
.sk-rangee{ display: flex; gap: 6px; flex-wrap: wrap; }
.sk-opt{ display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 6px 10px; border-radius: 999px; cursor: pointer;
  background: transparent; border: 1px solid rgba(169,188,212,.2); color: #fff; font: inherit; font-size: .78rem; font-weight: 600; }
.sk-opt.on{ border-color: var(--c-legendaire); background: rgba(240,180,41,.12); }
.sk-opt:disabled{ opacity: .6; cursor: default; }
.sk-opt:focus-visible{ outline: 2px solid #fff; outline-offset: 2px; }
.sk-pastille{ width: 14px; height: 14px; border-radius: 50%; flex: none; background: rgba(169,188,212,.25); box-shadow: inset 0 0 0 1px rgba(255,255,255,.25); }
.sk-p-comete{ background: linear-gradient(135deg, #1B2A6B, #8FB4FF); }
.sk-p-juillet{ background: linear-gradient(90deg, #2B4A9A 33%, #fff 33% 66%, #E05252 66%); }
.sk-p-maree{ background: linear-gradient(135deg, #0E4F66, #3FC6D8); }
.sk-p-feu{ background: linear-gradient(135deg, #3E0E04, #FF6A1A); }
.sk-p-prisme{ background: linear-gradient(115deg, #8FF3FF, #C7A6FF, #FFB7E3, #FFE7A3); }
.sk-p-orfondu{ background: linear-gradient(135deg, #8A6114, #F6D77A); }
.sk-p-neon{ background: linear-gradient(135deg, #FF2BD6, #20E3FF); }
.sk-p-gravure{ background: linear-gradient(135deg, #F2E8D2, #8F846F); }
.sk-p-orage{ background: linear-gradient(135deg, #121828, #9FB3D1); }
'''
REMPL = [('return `<div class="mini ${e.tier.id}${au ? \' aurore\' : \'\'}" title="${nom} (', 'return `<div class="mini ${e.tier.id}${au ? \' aurore\' : \'\'}"${e.skin ? ` data-skin="${echapperTexte(e.skin)}"` : \'\'} title="${nom} ('), ("${miniTerra(e)}${carte3dFin(dosDeMaCarte('terra', code))}${choixDosHtml('terra', code)}</div>", "${miniTerra({ ...e, skin: skinDeMaCarte('terra', code) })}${carte3dFin(dosDeMaCarte('terra', code))}${choixSkinHtml('terra', code)}${choixDosHtml('terra', code)}</div>"), ("armerDosFiche(boite, 'terra', code);   // patch200", "armerDosFiche(boite, 'terra', code);   // patch200\n    armerSkinFiche(boite);   // patch201"), ('${miniTerra({ ...entry, exemplaires: 1, aurore: auroreFront(entry.code) ? 1 : 0 })}${carte3dFin(', "${miniTerra({ ...entry, exemplaires: 1, aurore: auroreFront(entry.code) ? 1 : 0, skin: entry.perdue ? undefined : skinDeMaCarte('front', entry.code) })}${carte3dFin("), ("${entry.perdue ? '' : choixDosHtml('front', entry.code)}", "${entry.perdue ? '' : choixSkinHtml('front', entry.code) + choixDosHtml('front', entry.code)}"), ("if(!entry.perdue) armerDosFiche(boite, 'front', entry.code);   // patch200", "if(!entry.perdue){ armerDosFiche(boite, 'front', entry.code); armerSkinFiche(boite); }   // patch200-201"), ('  let s1 = new Set();   // patch170', "  const skinsCartes = new Map();   // patch201 : le skin de chaque carte exposée\n  try{ const r6 = await sb.rpc('skin_cartes', { p_joueur: id });\n    if(!r6.error) for(const x of r6.data || []) skinsCartes.set(x.source + '|' + x.code, skinCle(x.skin)); }catch(err){}\n  let s1 = new Set();   // patch170"), ("    dos: dosCartes.get((r.source === 'front' ? 'front' : 'terra') + '|' + r.code) || dos,", "    dos: dosCartes.get((r.source === 'front' ? 'front' : 'terra') + '|' + r.code) || dos,\n    skin: skinsCartes.get((r.source === 'front' ? 'front' : 'terra') + '|' + r.code),"), ('chargerMesDosCartes(true);   // patch200 : les dos carte par carte', 'chargerMesDosCartes(true);   // patch200 : les dos carte par carte\n  chargerMesSkinsCartes(true);   // patch201'), ('// ---------- patch179 : la carte en grand, inclinable et retournable ----------', '__BLOC__// ---------- patch179 : la carte en grand, inclinable et retournable ----------')]

js = lire('app.js')
assert 'patch201' not in js
for avant, apres in REMPL:
    assert js.count(avant) == 1, avant[:60]
    js = js.replace(avant, apres.replace('__BLOC__', BLOC_JS))
ecrire('app.js', js)
css = lire('style.css')
assert 'patch201' not in css
ecrire('style.css', css.rstrip('\n') + '\n' + BLOC_CSS)
print(u'patch201 applique. Lancer : python3 maj-version.py')
