// ---------- patch468 : cinq dos assortis aux skins du 22/11 (Givre, Vitrail, Topo, Aquarelle, Kintsugi) ----------
// Vendus avec leur skin (collections pack-givre…). Le liseré, les coins et l'épingle viennent du CSS (style.css, patch468).
Object.assign(DOS_GLSL, {
  // ------------------------------------------------------------------ GIVRE
  givre: `
float ridge(vec2 p){ float v=0.,a=.55; for(int i=0;i<4;i++){ float n=1.-abs(2.*vnoise(p)-1.); v+=a*n*n*n; p=mat2(1.7,1.1,-1.1,1.7)*p+7.1; a*=.5; } return v; }
float etoile(vec2 p,float R0){
  float r=length(p); float a=atan(p.y,p.x); a=mod(a+PI/6.,PI/3.)-PI/6.; vec2 u=r*vec2(cos(a),abs(sin(a)));
  float ep=.2+.3*(1.-u.x/R0);
  float arm=(1.-smoothstep(ep*.4,ep,u.y))*(1.-smoothstep(R0*.86,R0,u.x));
  float sp=R0*.2; vec2 bq=vec2(mod(u.x,sp)-sp*.3,u.y);
  float bl=(R0-u.x)*.46;
  float db=abs(dot(bq,vec2(-.866,.5))), lb=dot(bq,vec2(.5,.866));
  float barb=(1.-smoothstep(.12,.36,db))*step(0.,lb)*(1.-smoothstep(bl*.75,bl,lb))*step(sp*.7,u.x)*(1.-smoothstep(R0*.78,R0*.9,u.x));
  return max(arm,barb*.85)*(1.-.45*r/R0)+exp(-r*r/(R0*R0*.012))*.7; }
float cristaux(vec2 q,float cs,float seed){ float v=0.; vec2 id=floor(q/cs);
  for(int j=-1;j<=1;j++) for(int i=-1;i<=1;i++){ vec2 g=id+vec2(float(i),float(j)); vec2 r=h22(g+seed); float pr=h21(g+seed*1.7+3.);
    vec2 c=(g+.15+r*.7)*cs; float R0=cs*(.4+.5*pr); float an=pr*6.28; vec2 p=mat2(cos(an),-sin(an),sin(an),cos(an))*(q-c);
    v=max(v,etoile(p,R0)*step(.22,pr)); }
  return v; }
vec3 dos(vec2 q,vec2 uv,float t){
  vec2 c0=vec2(W,H)*.5; float rc=length(q-c0);
  // un bloc de glace, la lumière passe dedans
  vec3 col=mix(vec3(.075,.25,.41),vec3(.012,.05,.115),smoothstep(0.,1.05,length((uv-vec2(.5,.42))*vec2(1.,1.2))));
  float ca=fbm(q*.022+vec2(t*.02,0.));
  col+=vec3(.1,.34,.48)*pow(.5+.5*sin(q.x*.045+q.y*.03+ca*6.+u_tilt.x*2.5),7.)*.3;
  float f=ringsF(q,0.,0.); col+=vec3(.6,.85,1.)*lineU(ringDist(f),.35)*.15;
  float sti=cristaux(q+vec2(3.,11.),38.,8.7);
  col+=vec3(.45,.75,.95)*sti*(.1+.4*glint(uv,u_tilt,7.));
  // la grande étoile de givre, derrière l'emblème
  float a0=.262; vec2 p=mat2(cos(a0),-sin(a0),sin(a0),cos(a0))*(q-c0);
  float big=clamp(etoile(p/3.1,27.),0.,1.)*smoothstep(40.,52.,rc);
  col=mix(col,vec3(.86,.95,1.),big*(.3+.5*glint(uv,u_tilt,6.)));
  // le givre gagne par les bords
  vec2 dd=min(q,vec2(W,H)-q); float dE=min(dd.x,dd.y);
  float n1=fbm(q*.04+3.), n2=fbm3(q*.15+8.);
  float reach=14.+30.*n1;
  float g=1.-smoothstep(reach*.15,reach,dE+(n2-.5)*8.);
  float cn=exp(-dd.x/34.)*exp(-dd.y/30.);
  g=max(g,smoothstep(.1,.42,cn+(n1-.5)*.3));
  float cr=ridge(q*.5+vec2(0.,n1*2.)), cr2=ridge(q*1.1+11.);
  float st=max(cristaux(q,23.,1.3),cristaux(q+7.,11.5,5.1)*.8);
  float stz=smoothstep(0.,.42,g+.2*n1-.02);
  float fr=clamp(g*(.3+.55*smoothstep(.2,.6,cr)+.5*cr2)+g*g*.3,0.,1.);
  vec3 glace=mix(vec3(.66,.81,.94),vec3(.98,.995,1.),clamp(cr*.7+cr2*.5,0.,1.));
  col=mix(col,glace,fr*(.62+.3*cr2));
  col=mix(col,vec3(.95,.985,1.),st*stz*.82);
  // la neige tombe doucement
  for(int L=0;L<2;L++){ float fl=float(L); float cs=17.+9.*fl;
    vec2 pn=q; pn.y-=t*(5.+4.*fl); pn.x+=sin(pn.y*.045+fl*2.)*3.5+u_tilt.x*(5.+9.*fl);
    vec2 id=floor(pn/cs); vec2 r=h22(id+fl*17.); float d=length(pn-(id+.2+r*.6)*cs);
    col+=vec3(.85,.95,1.)*exp(-d*d/(.45+.6*fl))*step(.5,r.x)*(.3+.26*fl); }
  col+=vec3(.75,.9,1.)*glint(uv,u_tilt,12.)*(.07+.3*st*stz+.16*fr);
  vec2 gi=floor(q*1.7); float sp=h21(gi);
  float tw=pow(max(0.,sin(sp*60.+u_tilt.x*11.+u_tilt.y*8.+t*.8)),26.);
  col+=vec3(.9,.97,1.)*tw*step(.9,sp)*clamp(fr+st*stz+big*.6,0.,1.)*1.5;
  return col*vign(uv,.25); }`,

  // ------------------------------------------------------------------ VITRAIL (une rosace)
  vitrail: `
float vE;
vec3 vcell(vec2 p){
  vec2 n=floor(p),f=fract(p); vec2 mg=vec2(0.),mr=vec2(0.); float md=9.;
  for(int j=-1;j<=1;j++) for(int i=-1;i<=1;i++){ vec2 g=vec2(float(i),float(j)); vec2 o=.14+.72*h22(n+g+3.7); vec2 r=g+o-f; float d=dot(r,r); if(d<md){ md=d; mr=r; mg=g; } }
  float e=9.;
  for(int j=-2;j<=2;j++) for(int i=-2;i<=2;i++){ vec2 g=mg+vec2(float(i),float(j)); vec2 o=.14+.72*h22(n+g+3.7); vec2 r=g+o-f; vec2 dr=r-mr; if(dot(dr,dr)>1e-5) e=min(e,dot(.5*(mr+r),normalize(dr))); }
  vE=e; return vec3(p+mr,h21(n+mg+9.1)); }
vec3 joyau(float h){ return h<.34?vec3(.72,.07,.09):h<.68?vec3(.07,.2,.66):h<.86?vec3(.96,.66,.13):vec3(.08,.5,.27); }
vec3 dos(vec2 q,vec2 uv,float t){
  vec2 c0=vec2(W,H)*.5; vec2 d=q-c0; float r=length(d); float a=atan(d.y,d.x)+PI/12.;
  // le soleil derrière la verrière : il suit l'inclinaison
  vec2 sun=vec2(W*(.5+u_tilt.x*.7)+sin(t*.23)*14.,H*(.4-u_tilt.y*.6));
  float sl=exp(-dot(q-sun,q-sun)/(85.*85.));
  // le fond : des pièces de verre bleu nuit, quelques rubis, de rares ambres
  float sc=1./12.5; vec3 c=vcell(q*sc+vec2(.31,.17)); float e=vE/sc; float grain=c.z;
  vec3 g=c.z<.62?mix(vec3(.04,.1,.4),vec3(.07,.22,.62),fract(c.z*7.3)):c.z<.88?mix(vec3(.3,.05,.3),vec3(.5,.04,.12),fract(c.z*5.1)):vec3(.85,.55,.12);
  // la rosace : un œil d'ambre, douze pétales, douze médaillons
  float sa=TAU/12.; float R0=45.,R1=63.,R2=81.;
  if(r<R2+.9){
    float i1=floor(a/sa+.5); float la=a-i1*sa;
    float pd=(length(vec2((r-54.)/8.3,la/(sa*.4)))-1.)*7.;
    float i2=floor(a/sa); float lb=a-(i2+.5)*sa;
    vec2 mc=vec2(cos(lb),sin(lb))*r-vec2(72.,0.); float md=length(mc)-7.3;
    float ee;
    if(r<R0){ g=vec3(.96,.66,.13); ee=min(abs(la)*r,abs(r-33.)); grain=i1*.13; }
    else if(r<R1){
      if(pd<0.){ g=mod(i1,2.)<.5?vec3(.72,.07,.09):vec3(.07,.2,.66); ee=-pd; grain=i1*.37+.2; }
      else { g=vec3(.98,.74,.2); ee=min(pd,abs(lb)*r); grain=i2*.21+.5; } }
    else {
      if(md<0.){ g=mod(i2,2.)<.5?vec3(.08,.5,.27):vec3(.56,.1,.5); ee=min(-md,min(abs(mc.x),abs(mc.y))+1.2); grain=i2*.29+.7; }
      else { g=mod(i1,2.)<.5?vec3(.07,.2,.66):vec3(.05,.12,.46); ee=min(md,abs(la)*r); grain=i1*.17+.9; } }
    e=max(0.,min(min(ee,abs(r-R0)-.3),min(abs(r-R1)-.3,abs(r-R2)-.7)));
  } else e=min(e,r-R2-.7);
  // la frise du bord : des verres de couleur
  float dE=-sdBox(d,c0,13.);
  if(dE<7.4){
    vec2 dd=min(q,vec2(W,H)-q); bool hz=dd.y<dd.x; float co=hz?q.x:q.y; float ti=floor(co/8.2), tf=fract(co/8.2);
    float cote=hz?(q.y<c0.y?1.:2.):(q.x<c0.x?3.:4.); float hs=h21(vec2(ti,cote));
    g=joyau(hs); grain=hs*3.; e=min(min(tf,1.-tf)*8.2,7.4-dE);
  } else e=min(e,dE-7.4);
  float plomb=1.-smoothstep(.28,.64,e);
  g*=.82+.3*fract(grain*5.7);
  g*=.9+.22*fbm3(q*vec2(1.1,.14)+grain*20.);
  g*=.74+.26*smoothstep(0.,1.9,e);
  float lit=.5+.95*sl+.06*sin(t*.6);
  vec3 col=g*lit+g*g*sl*.5;
  vec3 pb=vec3(.055,.05,.05)+vec3(.5,.46,.38)*glint(uv,u_tilt,16.)*.22;
  col=mix(col,pb,plomb);
  // poussière dans le rayon
  vec2 dp=q+vec2(t*1.3,-t*2.1); vec2 di=floor(dp/9.); vec2 dr=h22(di+.5); float ds=length(dp-(di+.2+dr*.6)*9.);
  col+=vec3(1.,.9,.7)*exp(-ds*ds/.5)*step(.8,dr.x)*sl*.5*(.5+.5*sin(t*1.7+dr.y*30.));
  return col*vign(uv,.3); }`,

  // ------------------------------------------------------------------ TOPO (saison 3)
  topo: `
vec3 pal(float x){ x=clamp(x,0.,1.);
  vec3 c=mix(vec3(.028,.062,.125),vec3(.055,.145,.29),smoothstep(0.,.2,x));
  c=mix(c,vec3(.11,.27,.5),smoothstep(.2,.4,x));
  c=mix(c,vec3(.26,.48,.73),smoothstep(.4,.6,x));
  c=mix(c,vec3(.62,.77,.89),smoothstep(.6,.8,x));
  c=mix(c,vec3(.955,.925,.835),smoothstep(.8,.98,x)); return c; }
vec3 dos(vec2 q,vec2 uv,float t){
  vec3 nuit=vec3(.028,.062,.125), acier=vec3(.27,.47,.7), ivoire=vec3(.965,.93,.845), orc=vec3(.95,.72,.17);
  vec2 c0=vec2(W,H)*.5; float rc=length(q-c0);
  // le relief : les courbes de niveau du jeu, teintées par altitude
  float off=t*.02;
  float rf=ringsF(q,0.,0.)+off*.5; float rn=floor(rf);
  float alt=1.-clamp((rn+.5-off*.5)/9.,0.,1.);
  vec3 col=pal(.05+.44*alt)*(.9+.2*fbm(q*.05));
  float rg=lineU(ringDist(rf),.3);
  float rmaj=step(abs(mod(rn,4.)-3.),.5);
  col=mix(col,mix(acier,orc,rmaj),rg*(.36+.5*rmaj));
  col+=orc*glint(uv,u_tilt,10.)*rg*rmaj*.55;
  // carroyage et croix de repère
  float gx=abs(fract(q.x/22.2+.5)-.5)*22.2, gy=abs(fract(q.y/22.2+.5)-.5)*22.2;
  float gri=lineU(min(gx,gy),.2);
  float croix=lineU(min(gx,gy),.3)*step(max(gx,gy),2.4);
  col=mix(col,acier,gri*.13);
  col=mix(col,ivoire,croix*.5);
  // points cotés
  vec2 gi=floor(q/44.4); vec2 hr=h22(gi+5.); vec2 pc=(gi+.25+hr*.5)*44.4; float dp=length(q-pc);
  col=mix(col,ivoire,step(.5,hr.x)*(1.-smoothstep(.8,1.25,dp))*.9);
  col=mix(col,ivoire,step(.5,hr.x)*lineU(abs(dp-2.6),.2)*.55);
  // la rose des vents, autour de l'épingle
  float aa=atan(q.y-c0.y,q.x-c0.x);
  float tick=abs(fract(aa/TAU*36.+.5)-.5)/36.*TAU*rc;
  float card=abs(fract(aa/TAU*4.+.5)-.5)/4.*TAU*rc;
  float rose=lineU(tick,.28)*step(47.5,rc)*step(rc,51.)+lineU(card,.5)*step(47.5,rc)*step(rc,59.);
  rose=max(rose,lineU(abs(rc-47.5),.25)*.8);
  col=mix(col,ivoire,clamp(rose,0.,1.)*.8);
  // le relevé : une bande de lumière passe et fait briller les courbes
  float ph=fract(t/8.5)*3.2; float xs=mix(-50.,W+50.,ph)+(q.y-60.)*.28;
  float bande=exp(-pow((q.x-xs)/14.,2.))*step(ph,1.);
  col+=(orc*rg*1.1+vec3(.12,.24,.42)*.35)*bande;
  col+=vec3(.75,.92,1.)*exp(-pow((q.x-xs-14.)/.8,2.))*.5*step(ph,1.);
  // filet de carte : segments ivoire et nuit
  float dE=-sdBox(q-c0,c0,13.);
  vec2 dd=min(q,vec2(W,H)-q); bool hz=dd.y<dd.x; float co=hz?q.x:q.y; float seg=step(.5,fract(co/14.));
  float liste=step(3.5,dE)*step(dE,6.1);
  col=mix(col,mix(nuit,ivoire,seg),liste);
  col=mix(col,ivoire,max(lineU(abs(dE-3.5),.25),lineU(abs(dE-6.1),.25)));
  return col*vign(uv,.3); }`,

  // ------------------------------------------------------------------ AQUARELLE
  aquarelle: `
const vec2 AQ_C[6]=vec2[6](vec2(50.,56.),vec2(146.,86.),vec2(46.,168.),vec2(144.,198.),vec2(96.,131.),vec2(98.,246.));
const vec3 AQ_P[6]=vec3[6](vec3(.2,.36,.7),vec3(.26,.58,.47),vec3(.95,.7,.22),vec3(.84,.3,.38),vec3(.5,.38,.7),vec3(.2,.6,.72));
const float AQ_R[6]=float[6](60.,54.,54.,58.,46.,44.);
vec3 dos(vec2 q,vec2 uv,float t){
  vec2 c0=vec2(W,H)*.5;
  float gr=vnoise(q*2.3)*.6+vnoise(q*5.3+7.)*.4;
  vec3 paper=vec3(.975,.957,.918)*(1.-.065*gr)-vec3(0.,.004,.014)*fbm3(q*.03);
  vec3 col=paper;
  // la feuille peinte : bords irréguliers, une marge de papier blanc
  float wob=fbm(q*.055+2.)-.5, wob2=fbm3(q*.21+8.)-.5;
  float dP=sdBox(q-c0,c0-vec2(15.,16.),14.)+wob*12.+wob2*3.5;
  float zone=1.-smoothstep(-1.3,1.3,dP);
  // les lavis : six pigments qui fusent les uns dans les autres
  vec2 w=vec2(fbm(q*.018+1.7+t*.004),fbm(q*.018+6.1-t*.003))-.5;
  vec2 qq=q+w*56.;
  for(int i=0;i<6;i++){ float fi=float(i);
    float dd=length(qq-AQ_C[i])/AQ_R[i]+(fbm3(q*.09+fi*7.)-.5)*.4;
    float m=(1.-smoothstep(.5,1.,dd))*zone;
    float cerne=smoothstep(.82,.98,dd)*(1.-smoothstep(.98,1.05,dd))*zone;
    float dens=(.5+.42*fbm3(q*.05+fi*3.))*(1.-.22*gr);
    vec3 teinte=1.-(1.-AQ_P[i])*.88;
    col*=mix(vec3(1.),teinte,m*dens);
    col*=mix(vec3(1.),teinte,cerne*.42); }
  // le bord de la feuille : la peinture s'y accumule
  col*=1.-.16*smoothstep(-5.,-.8,dP)*zone;
  // auréoles : l'eau repousse le pigment
  vec2 ai=floor(q/38.); vec2 ar=h22(ai+2.3); float ad=length(q-(ai+.25+ar*.5)*38.)+(fbm3(q*.3)-.5)*3.;
  float aur=step(.55,ar.x)*(1.-smoothstep(3.,8.+6.*ar.y,ad));
  col=mix(col,paper,aur*.3*zone);
  col*=1.-.12*step(.55,ar.x)*smoothstep(6.+6.*ar.y,8.+6.*ar.y,ad)*(1.-smoothstep(8.+6.*ar.y,9.5+6.*ar.y,ad))*zone;
  // le crayon : les courbes de niveau, à la mine
  float f=ringsF(q+vec2(wob2,-wob2)*1.2,0.,0.);
  float rg=lineU(ringDist(f),.34);
  col=mix(col,vec3(.2,.2,.28),rg*(.2+.22*gr)*(1.-smoothstep(-3.,6.,dP-4.)));
  // quelques éclaboussures
  vec2 ei=floor(q/11.); vec2 er=h22(ei+7.7); float ed=length(q-(ei+.2+er*.6)*11.);
  float ecl=step(.88,er.x)*(1.-smoothstep(.5+er.y*.9,.9+er.y*.9,ed));
  col*=mix(vec3(1.),1.-(1.-AQ_P[int(mod(ei.x+ei.y*3.,6.))])*.8,ecl*.7);
  col+=vec3(1.)*glint(uv,u_tilt,10.)*.045;
  return col*(1.-.08*smoothstep(.65,1.1,length(uv-.5)*1.5)); }`,

  // ------------------------------------------------------------------ KINTSUGI
  kintsugi: `
float kE; float kI;
float seig(vec2 p){ float jy=floor(p.y*2.); float v=0.; bool pris=false;
  for(int k=1;k>=-1;k--){ float j=jy+float(k); float ox=mod(j,2.)*.5;
    for(int i=0;i<2;i++){ vec2 c=vec2(floor(p.x-ox)+ox+float(i),j*.5+.5);
      float d=length(p-c); if(!pris && d<.5 && p.y<c.y+.02){ pris=true; v=smoothstep(.55,1.,abs(sin(d*PI*6.))); } } }
  return v; }
void kcell(vec2 p){
  vec2 n=floor(p),f=fract(p); vec2 mg=vec2(0.),mr=vec2(0.); float md=9.;
  for(int j=-1;j<=1;j++) for(int i=-1;i<=1;i++){ vec2 g=vec2(float(i),float(j)); vec2 o=.1+.8*h22(n+g+1.9); vec2 r=g+o-f; float d=dot(r,r); if(d<md){ md=d; mr=r; mg=g; } }
  float e=9.;
  for(int j=-2;j<=2;j++) for(int i=-2;i<=2;i++){ vec2 g=mg+vec2(float(i),float(j)); vec2 o=.1+.8*h22(n+g+1.9); vec2 r=g+o-f; vec2 dr=r-mr; if(dot(dr,dr)>1e-5) e=min(e,dot(.5*(mr+r),normalize(dr))); }
  kE=e; kI=h21(n+mg+4.4); }
vec3 dos(vec2 q,vec2 uv,float t){
  // des éclats de laque : noire, et de loin en loin un éclat rouge
  vec2 wq=q+(vec2(fbm3(q*.03),fbm3(q*.03+4.7))-.5)*16.;
  float sc=1./72.; kcell(wq*sc+vec2(.37,.61)); float e=kE/sc; float id=kI;
  float wv=.8+1.6*fbm3(q*.07+id*3.);
  float hg=1.-clamp(e/wv,0.,1.);
  float seam=1.-smoothstep(wv*.6,wv,e);
  vec2 dec=(h22(vec2(id*31.,7.))-.5)*2.6;
  float py=smoothstep(0.,1.,length((uv-vec2(.5,.42))*vec2(1.,1.2)));
  float rouge=step(.74,h21(vec2(id,8.)));
  vec3 laque=mix(vec3(.09,.082,.125),vec3(.026,.025,.042),py)*(.88+.26*h21(vec2(id,5.)));
  laque=mix(laque,mix(vec3(.36,.06,.05),vec3(.13,.02,.025),py),rouge);
  float ang=(h21(vec2(id,3.))-.5)*.6; mat2 rm=mat2(cos(ang),-sin(ang),sin(ang),cos(ang));
  float sg=seig(rm*(q+dec)/15.);
  laque+=mix(vec3(.5,.46,.6),vec3(1.,.5,.3),rouge)*sg*(.045+.19*glint(uv,u_tilt,5.));
  laque+=vec3(.25,.22,.3)*glint(uv+dec*.01,u_tilt,6.)*.14;
  laque*=1.-.4*(1.-smoothstep(wv,wv+3.,e));
  // poussière d'or près des fêlures
  float pd=h21(floor(q*2.1)+id); float pres=1.-smoothstep(wv,wv+11.,e);
  laque+=vec3(1.,.82,.4)*step(.9985-.06*pres,pd)*(.35+.65*pow(max(0.,sin(pd*90.+u_tilt.x*9.+u_tilt.y*7.+t*.5)),6.))*.8;
  vec3 col=laque;
  // l'or dans les fêlures, en relief
  vec2 gd=vec2(dFdx(e),dFdy(e)); gd/=max(length(gd),1e-4);
  vec2 lum2=normalize(vec2(-.5+u_tilt.x*2.,-.7+u_tilt.y*2.));
  float nl=dot(gd,lum2)*(1.-hg*hg);
  float sh=.5+.5*nl;
  vec3 orc=mix(vec3(.42,.25,.05),vec3(1.,.8,.36),smoothstep(.1,.85,sh*.75+hg*.3));
  orc+=vec3(1.,.96,.8)*pow(clamp(sh*.6+hg*.5,0.,1.),7.)*.55;
  orc*=.88+.24*vnoise(q*3.1);
  orc+=vec3(1.,.95,.8)*pow(max(0.,sin(h21(floor(q*2.6))*70.+u_tilt.x*10.+u_tilt.y*8.+t*.6)),22.)*.6;
  // une lueur parcourt l'or
  float onde=exp(-pow((fract(length(q-vec2(26.,14.))/300.-t*.08)-.5)*10.,2.));
  orc+=vec3(1.,.9,.6)*onde*.45;
  col=mix(col,orc,seam);
  return col*vign(uv,.3); }`,
});
