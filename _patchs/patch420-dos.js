// ---------- patch420 : les dos du podium de la saison 2 ----------
// Couronne de lauriers, étoile, et en bas un petit podium où la marche du joueur s'allume.
// Or au 1er, argent au 2e, bronze au 3e : trois dos offerts à la clôture (s2-138), un exemplaire chacun.
// Ajoutés à DOS_GLSL avant dosGl : SEL_APERCUS les voit (aperçus de la boutique, de la fiche des récompenses).
(() => {
  const METAUX = {   // [place, M0 sombre, M1 moyen, M2 clair, M3 reflet]
    or:     [1, '.30,.17,.03', '.86,.60,.18', '1.,.88,.55', '1.,.96,.82'],
    argent: [2, '.20,.23,.29', '.70,.75,.82', '.94,.97,1.', '1.,1.,1.'],
    bronze: [3, '.26,.10,.04', '.74,.42,.21', '1.,.76,.52', '1.,.90,.76'],
  };
  const LAURIERS = `
const vec2 CE=vec2(94.,131.5);
vec3 lumiere(float t){ return normalize(vec3(u_tilt.x*1.3+.32*cos(t*.45),-u_tilt.y*1.3+.32*sin(t*.45)+.25,.9)); }
vec3 metal(vec3 N,vec3 L,float t){
  float dif=max(dot(N,L),0.); float sp=pow(max(reflect(-L,N).z,0.),30.);
  float env=.5+.5*sin(N.x*6.+N.y*4.+t*.3+u_tilt.x*2.4);
  vec3 c=mix(M0,M1,dif*.9+.08); c=mix(c,M2,env*.35*dif); return c+M3*sp*1.15; }
vec3 nuitFond(vec2 uv){ return mix(vec3(.012,.024,.06),vec3(.06,.105,.21),1.-smoothstep(0.,1.,length((uv-vec2(.5,.47))*vec2(1.,1.2)))); }
// étoile à cinq branches, pointe en haut (distance signée, négative dedans) ; p en coordonnées de carte (y vers le bas)
float etoile5(vec2 p,float r,float rf){
  const vec2 k1=vec2(.809016994,-.587785252); const vec2 k2=vec2(-k1.x,k1.y);
  p.y=-p.y; p.x=abs(p.x); p-=2.*max(dot(k1,p),0.)*k1; p-=2.*max(dot(k2,p),0.)*k2; p.x=abs(p.x); p.y-=r;
  vec2 ba=rf*vec2(-k1.y,k1.x)-vec2(0.,1.); float h=clamp(dot(p,ba)/dot(ba,ba),0.,r);
  return length(p-ba*h)*sign(p.y*ba.x-p.x*ba.y); }
// une feuille de laurier, base en 0, pointe en (L,0) ; renvoie la distance et la pente (pour la lumière)
float feuille(vec2 p,float L,float Wd,out vec2 g){
  float u=clamp(p.x/L,0.,1.); float hw=Wd*pow(sin(3.14159*u),.7)+.05;
  float d=max(abs(p.y)-hw,max(-p.x,p.x-L));
  float s=clamp(p.y/hw,-1.,1.);
  float dhds=-1.1*s+9.9*s*exp(-s*s*22.);      // bombé + nervure centrale
  g=vec2(0.,dhds/hw*3.);
  return d; }
vec3 dos(vec2 q,vec2 uv,float t){
  vec3 L=lumiere(t);
  vec3 col=nuitFond(uv)*(.9+.2*fbm(q*.05));
  float f=ringsF(q,0.,0.); col+=M1*lineU(ringDist(f),.35)*.10;
  float r=length(q-CE);
  col+=M1*exp(-pow((r-60.)/24.,2.))*.10;
  // la couronne : deux branches en miroir
  float sx=q.x<CE.x?-1.:1.; vec2 qq=vec2(CE.x+abs(q.x-CE.x),q.y); vec2 d=qq-CE;
  float ph=atan(d.x,d.y);                // 0 en bas, pi en haut
  const float R=60., P0=.32, DP=.30; const int N=9;
  // la tige
  float tige=abs(length(d)-R); float onT=step(P0-.2,ph)*step(ph,P0+DP*float(N-1)+.05);
  float wT=1.5*(1.-.45*clamp((ph-P0)/(DP*float(N)),0.,1.));
  float cT=(1.-smoothstep(wT-upx(),wT+upx(),tige))*onT;
  vec2 rq=normalize(d); float sd=clamp((length(d)-R)/wT,-1.,1.);
  col=mix(col,metal(normalize(vec3(rq.x*sx*sd*.8,-rq.y*sd*.8,1.)),L,t)*.85,cT);
  // les feuilles, deux par nœud ; on ne regarde que les nœuds voisins du pixel
  float k0=floor((ph-P0)/DP);
  for(int j=-1;j<=2;j++){ float k=k0+float(j); if(k<0.||k>float(N-1)) continue;
    float a=P0+k*DP; vec2 P=CE+R*vec2(sin(a),cos(a)); vec2 T=vec2(cos(a),-sin(a)), O=vec2(sin(a),cos(a));
    float Lf=mix(17.,9.5,k/float(N-1));
    for(int s=0;s<2;s++){ float be=s==0?.62:-.58; vec2 ax=normalize(T*cos(be)+O*sin(be)); vec2 bx=vec2(-ax.y,ax.x);
      vec2 p=vec2(dot(qq-P,ax),dot(qq-P,bx)); vec2 g; float df=feuille(p,Lf*(s==0?1.:.86),Lf*.3,g);
      if(df<1.){ vec2 gq=g.x*ax+g.y*bx; gq.x*=sx;
        vec3 Nl=normalize(vec3(-gq.x*.55,gq.y*.55,1.));
        vec3 mc=metal(Nl,L,t)*(1.-.32*smoothstep(-1.4,0.,df));
        col=mix(col,mc,1.-smoothstep(-upx(),upx(),df)); } } }
  // le nœud en bas
  vec2 nb=q-vec2(94.,191.5); float noeud=length(nb*vec2(.8,1.25))-4.2;
  col=mix(col,metal(normalize(vec3(nb.x*.12,-nb.y*.12,1.)),L,t),1.-smoothstep(-upx(),upx(),noeud));
  // l'étoile en haut
  vec2 ep=q-vec2(94.,58.); float de=etoile5(ep,11.,.46);
  vec3 Ne=normalize(vec3(ep.x*.09,-ep.y*.09,1.));
  col+=M2*exp(-max(de,0.)*.22)*.10;
  col=mix(col,metal(Ne,L,t)*1.08,1.-smoothstep(-upx(),upx(),de));
  // le podium en bas : la marche du joueur s'allume, les deux autres en filet
  vec2 pb=q-vec2(94.,236.);
  for(int m=0;m<3;m++){ float fm=float(m); float x0=(fm-1.)*17.5; float hh=m==0?12.:m==1?19.:8.; float pl=m==0?2.:m==1?1.:3.;
    float db=sdBox(pb-vec2(x0,-hh*.5),vec2(8.,hh*.5),.9);
    float moi=step(abs(pl-PLACE),.1);
    if(moi>.5){ col+=M2*exp(-max(db,0.)*.3)*.2;
      col=mix(col,metal(normalize(vec3(0.,.15,1.)),L,t)*1.1,1.-smoothstep(-upx(),upx(),db)); }
    else{ col=mix(col,M1*.16,1.-smoothstep(-upx(),upx(),db));
      col=mix(col,M1*.75,(1.-smoothstep(.45-upx(),.45+upx(),abs(db+.45)))); } }
  // des paillettes qui tombent
  col+=ember(q,t,16.,-7.,.45,.42,2.,M2*.75)+ember(q,t*1.2,27.,-11.,.8,.36,7.,M3*.6);
  col+=M2*glint(uv,u_tilt,16.)*.09;
  return col*vign(uv,.35); }`;
  for(const [m, [place, M0, M1, M2, M3]] of Object.entries(METAUX))
    DOS_GLSL['podium-s2-' + m] = `
const vec3 M0=vec3(${M0}), M1=vec3(${M1}), M2=vec3(${M2}), M3=vec3(${M3});
const float PLACE=${place}.;` + LAURIERS;
})();
