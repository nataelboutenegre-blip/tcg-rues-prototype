# patch256 : objets du pass « Brumes d'automne » — Skin Brume et Paquet Sous-bois
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')

s = rep(s, "const skinCle = (id) => id ? String(id).replace(/^skin-/, '') : null;",
           "const skinCle = (id) => id ? String(id).replace(/^pass-s\\d+-/, '').replace(/^skin-/, '') : null;   // patch256 : objets du pass")
s = rep(s, "neon: 'Néon', gravure: 'Gravure', orage: 'Orage' };", "neon: 'Néon', gravure: 'Gravure', orage: 'Orage', brume: 'Brume' };")
s = rep(s, "orage: 9, vendanges: 10 };   // patch255", "orage: 9, vendanges: 10, 'sous-bois': 11 };   // patch255-256")

# ---- le skin Brume : cadre d'étain, photo voilée de brume qui dérive, rayons de lumière ; la brume se lève à l'ouverture
BRUME = r"""  brume: `
vec3 face(vec2 q,vec2 uv,float t){
  float b=3.; vec4 R=photoRect(b); float ii=interior(q,b); float ip=inR(q,R);
  float an=atan(q.y-H*.5,q.x-W*.5);
  vec3 frame=mix(vec3(.42,.47,.54),vec3(.86,.9,.95),pow(.5+.5*sin(an*2.+t*.35+u_tilt.x*2.),3.))*(.82+.3*glint(uv,u_tilt,9.));
  frame*=.92+.08*fbm(q*vec2(.9,.06));
  float lev=u_rev<1.8?1.-smoothstep(.1,1.7,u_rev):0.;
  vec2 s=photoUV(q,R); vec3 p=photo(s); float L=lum(p);
  vec3 ph=mix(vec3(L),p,.55)*vec3(.86,.93,1.)*.92+vec3(.03,.04,.06);
  float f1=fbm(vec2(q.x*.022-t*.06,q.y*.05)+vec2(0.,t*.01)); float f2=fbm(vec2(q.x*.04+t*.11,q.y*.08)+3.7);
  float voile=smoothstep(.35,.85,f1*.65+f2*.45)*(.35+.45*smoothstep(.2,1.,s.y))+lev*.9;
  vec3 brumeC=vec3(.82,.86,.9);
  ph=mix(ph,brumeC,clamp(voile,0.,1.)*.75);
  vec2 rd=normalize(vec2(.55+u_tilt.x*.25,1.)); float ra=dot(q-vec2(10.,-20.),vec2(rd.y,-rd.x));
  float rays=pow(.5+.5*sin(ra*.11+t*.2),8.)*(1.-s.y)*.22*(1.-lev);
  ph+=vec3(1.,.97,.9)*rays;
  vec3 inner=mix(vec3(.09,.11,.14),vec3(.2,.23,.27),1.-smoothstep(.35,1.,uv.y));
  float f3=fbm(vec2(q.x*.03+t*.05,q.y*.04-t*.01)+9.); inner=mix(inner,vec3(.5,.55,.6),smoothstep(.45,.9,f3)*.3+lev*.5);
  float rg=lineU(ringDist(ringsF(q,0.,0.)),.35); inner+=vec3(.75,.8,.88)*rg*.07;
  vec3 col=mix(inner,ph,ip);
  float bas=exp(-pow((q.y-R.w+6.)/14.,2.))*(.5+.5*fbm(vec2(q.x*.05-t*.08,t*.05)));
  col=mix(col,brumeC*.8,bas*.45);
  col=mix(frame,col,ii);
  return col; }`,
"""
s = rep(s, "const SKIN_GLSL = {\n", "const SKIN_GLSL = {\n" + BRUME)

# ---- le paquet Sous-bois : troncs, rayons de lumière, lucioles, cèpes et feuilles au sol
SOUSBOIS = r"""  else if(u_paq==11){
    vec2 tl=u_tilt;
    float hz=smoothstep(-.3,.75,q.y);
    col=mix(vec3(.03,.07,.06),vec3(.36,.38,.22),pow(hz,1.6));
    col+=vec3(.5,.42,.2)*exp(-length((q-vec2(-.25,.78))*vec2(1.,1.4))*2.2)*.6;
    // trois plans de troncs, du plus lointain (pâle, dans la brume) au plus proche (noir)
    for(int L=0;L<3;L++){ float fl=float(L); float cw=L==0?.11:(L==1?.2:.34); float px=(fl+1.)*.025;
      vec2 lq=q+tl*px; float id=floor(lq.x/cw); float hh=h21(vec2(id,fl*5.+1.));
      float cx=(id+.5+(hh-.5)*.6)*cw; float w=(L==0?.01:(L==1?.022:.04))*(.7+.6*h21(vec2(id,fl+9.)));
      float lean=(h21(vec2(id,fl+4.))-.5)*.08; float d=abs(lq.x-cx-lean*(lq.y+.2))-w;
      float on=step(L==2?.55:.25,h21(vec2(id,fl+13.)));
      vec3 tc=L==0?mix(col,vec3(.2,.24,.17),.55):(L==1?vec3(.06,.07,.05):vec3(.02,.018,.015));
      float bark=fbm(vec2((lq.x-cx)*60.,lq.y*6.)+id);
      if(L>0) tc*=.75+.5*bark;
      float rim=L==2?smoothstep(0.,-w*.6,d)*smoothstep(-w,-w*.4,d)*step(lq.x,cx):0.;
      tc+=vec3(.35,.45,.12)*rim*.6;
      col=mix(col,tc,(1.-smoothstep(-.002,.002,d))*on*step(-.3,q.y+.1*fl)); }
    // rayons de lumière et poussières qui y dansent
    vec2 rd=normalize(vec2(-.42+tl.x*.18,1.)); float ra=dot(q-vec2(-.25,.78),vec2(rd.y,-rd.x));
    float rays=pow(.5+.5*sin(ra*14.+t*.15),6.)*.7+pow(.5+.5*sin(ra*31.-t*.1+1.),12.)*.4;
    rays*=smoothstep(-.35,.7,q.y)*(.7+.3*fbm(vec2(ra*4.,t*.1)));
    col+=vec3(1.,.86,.5)*rays*.32;
    vec2 dq=q+vec2(t*.01,-t*.02); vec2 did=floor(dq/.03); vec2 dh=h22(did+40.); vec2 dc=(did+.2+dh*.6)*.03;
    float dd=length(dq-dc); col+=vec3(1.,.9,.6)*step(.82,dh.x)*exp(-dd*dd*90000.)*rays*2.2;
    // brume au ras du sol
    float fog=fbm(vec2(q.x*3.-t*.08,q.y*8.))*exp(-pow((q.y+.18)/.08,2.));
    col=mix(col,vec3(.55,.62,.5),fog*.55);
    // le sol moussu
    float sol=-.2+.015*sin(q.x*11.)+.01*sin(q.x*29.);
    vec3 sc=mix(vec3(.05,.07,.03),vec3(.14,.2,.06),fbm(q*18.))*(.8+.3*dif);
    col=mix(col,sc,smoothstep(sol+.006,sol-.006,q.y));
    // champignons qui luisent, et un cèpe
    float lueur=0.;
    for(int k=0;k<4;k++){ vec2 c=k==0?vec2(-.13,-.205):(k==1?vec2(-.075,-.21):(k==2?vec2(-.03,-.208):vec2(.16,-.212)));
      float sc2=k==0?1.05:(k==1?.75:(k==2?.55:1.3)); bool cepe=k==3;
      vec2 m=(q-c)/sc2; m.x+=sin(t*.6+float(k))*.004*m.y*10.;
      float stem=sdBox(m-vec2(0.,.045),vec2(.016-m.y*.05,.05),.012);
      float cap=cepe?max(length((m-vec2(0.,.105))*vec2(1.,1.6))-.075,-(m.y-.095)):max(length((m-vec2(0.,.095))*vec2(1.,1.25))-.05,-(m.y-.085));
      vec3 capC=cepe?mix(vec3(.3,.15,.06),vec3(.6,.36,.14),smoothstep(.09,.17,m.y)):mix(vec3(.15,.75,.6),vec3(.7,1.,.85),smoothstep(.09,.14,m.y));
      vec3 stC=cepe?vec3(.85,.77,.58):vec3(.55,.85,.75);
      float pul=.8+.2*sin(t*1.7+float(k)*2.);
      col=mix(col,stC*(cepe?(.75+.3*dif):pul),1.-smoothstep(-.003,.003,stem*sc2));
      vec2 sm=m*70.; vec2 si=floor(sm); float spot=cepe?0.:step(.6,h21(si))*(1.-smoothstep(.18,.28,length(sm-si-.5)))*step(.1,m.y);
      col=mix(col,capC*(cepe?(.8+.35*dif):pul*1.15)+spot*.4,1.-smoothstep(-.003,.003,cap*sc2));
      if(!cepe) lueur+=exp(-length(q-c-vec2(0.,.09*sc2))*14./sc2)*pul; }
    col+=vec3(.2,.95,.75)*lueur*.35;
    // fougères au premier plan, qui ondulent
    for(int k=0;k<2;k++){ float sg=k==0?1.:-1.; vec2 o=vec2(.535*sg,-.27); vec2 fq=q-o; fq.x*=-sg;
      float a=(k==0?.42:.5)+sin(t*.7+float(k)*2.)*.035; fq=mat2(cos(a),-sin(a),sin(a),cos(a))*fq;
      float u=fq.x, v=fq.y-1.1*u*u+.1*u; float len=k==0?.48:.4;
      float w=.085*(1.-u/len)*smoothstep(0.,.03,u)*(.55+.45*abs(sin(u*70.)));
      float fd=abs(v)-w; float on=step(0.,u)*step(u,len);
      col=mix(col,vec3(.02,.05,.02)+vec3(.12,.22,.05)*smoothstep(-w,0.,fd)*.6,(1.-smoothstep(-.002,.002,fd))*on); }
    // lucioles
    vec2 fq2=q+vec2(sin(t*.3)*.04,0.); vec2 fid=floor(fq2/.13); vec2 fh=h22(fid+33.);
    vec2 fc=(fid+.5+(fh-.5)*.4)*.13+.018*vec2(sin(t*1.3+fh.x*9.),cos(t*1.1+fh.y*7.));
    float fd2=length(fq2-fc); float onf=pow(.5+.5*sin(t*(1.+fh.y)+fh.x*30.),3.);
    col+=vec3(.8,1.,.4)*step(.66,fh.y)*step(sol+.02,fc.y)*onf*(exp(-fd2*fd2*50000.)*1.5+exp(-fd2*fd2*5000.)*.3);
    col=mix(col,vec3(.9,.78,.4),rg*.08);
    col*=.85+.15*smoothstep(1.2,.3,length(q*vec2(1.3,.9))); }
"""
s = rep(s, "  else {\n    float P=3.7; float cy=floor(t/P), ph=t-cy*P;", SOUSBOIS + "  else {\n    float P=3.7; float cy=floor(t/P), ph=t-cy*P;")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
s += """
/* ---------- patch256 : Skin Brume et Paquet Sous-bois (pass « Brumes d'automne ») ---------- */
.mini.skin-brume{ --sk-acc: #C8D3DC; }
.mini.skin-brume .mini-nom{ color: #F2F5F8; text-shadow: 0 0 6px rgba(200,211,220,.45); }
.mini.skin-brume .mini-num{ color: #A9B6C2; } .mini.skin-brume .mini-rarete{ color: #D5DDE4 !important; } .mini.skin-brume .mini-dept{ color: rgba(213,221,228,.2); }
:is(.paquet.hab-sous-bois, .hab-vignette[data-hab="sous-bois"]){
  --hab-fond: radial-gradient(40% 25% at 30% 65%, rgba(150,95,40,.55), transparent 70%), linear-gradient(180deg, #08130A, #1F2E12);
  --hab-texte: #EAF2C8; --hab-bande: linear-gradient(90deg, #4A3416, #C8A04A 45%, #5A4018); --hab-bande-texte: #0E1608; --hab-lueur: 0 0 10px rgba(190,255,90,.35); }
"""
f.write_text(s, encoding='utf-8')
print('patch256 ok')
