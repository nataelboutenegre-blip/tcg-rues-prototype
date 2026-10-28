# patch257 : objets du pass « Brumes d'automne » — Dos Automne, Dos Braises d'automne, Skin Vendanges
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')

ERABLE = r"""float erable(vec2 p){ float a=atan(p.x,p.y); float r=.4+.32*pow(abs(cos(2.5*a)),2.)*(1.-.45*smoothstep(1.9,3.1,abs(a)));
  vec2 st=p-vec2(0.,-.62); return min(length(p*vec2(1.,1.05))-r,max(abs(st.x)-.035,abs(st.y)-.28)); }
"""

DOS = r"""  automne: `
""" + ERABLE + r"""vec3 dos(vec2 q,vec2 uv,float t){
  vec3 col=mix(vec3(.42,.12,.04),vec3(.8,.4,.11),1.-smoothstep(0.,1.05,length((uv-vec2(.5,.42))*vec2(1.,1.2))));
  col*=.85+.25*fbm(q*.06)+.08*fbm(q*.4);
  vec2 g=q/40.; vec2 id=floor(g); vec2 h=h22(id+11.);
  vec2 c=(id+.5+(h-.5)*.35)*40.; float a=(h.x-.5)*2.4; vec2 p=mat2(cos(a),-sin(a),sin(a),cos(a))*(q-c)/(13.+5.*h.y);
  float d=erable(p);
  vec3 lc=h.y>.5?vec3(.36,.09,.03):vec3(.95,.66,.25);
  col=mix(col,mix(col,lc,.55),(1.-smoothstep(-.03,.03,d))*step(.25,h.x));
  col=mix(col,lc*.8,lineU(abs(p.x)*13.,.5)*step(d,0.)*step(.25,h.x)*.35);
  float f=ringsF(q,0.,0.); col+=vec3(1.,.88,.65)*lineU(ringDist(f),.35)*.28;
  col+=vec3(1.,.85,.55)*glint(uv,u_tilt,14.)*.12*(.6+.4*sin(t*.4));
  return col*vign(uv,.38); }`,
  braises: `
""" + ERABLE + r"""vec3 dos(vec2 q,vec2 uv,float t){
  vec3 col=vec3(.035,.025,.022)*(.6+.9*fbm(q*.04+vec2(0.,-t*.05)));
  col+=vec3(.06,.04,.035)*smoothstep(.5,.9,fbm(q*.015+vec2(t*.02,-t*.06)));
  float f=ringsF(q,0.,0.); float pul=.5+.5*sin(t*1.4-floor(f+.5)*.9);
  col+=fire(.25+.3*pul)*lineU(ringDist(f),.35)*.45;
  for(int k=0;k<2;k++){ float fk=float(k); float cs=k==0?70.:48.; float sz=k==0?19.:12.; float sp=k==0?9.:6.;
    vec2 lq=q-vec2(sin(t*.3+fk)*6.,-t*sp)+fk*23.; vec2 id=floor(lq/cs); vec2 h=h22(id+fk*5.3+1.);
    if(h.y>.45){
      vec2 c=(id+.5+(h-.5)*.3)*cs; c.x+=sin(t*(.7+h.x)+h.y*9.)*5.;
      float a=t*(.4+h.x*.5)*(h.y>.72?1.:-1.)+h.x*TAU; vec2 p=mat2(cos(a),-sin(a),sin(a),cos(a))*(lq-c)/sz;
      float d=erable(p);
      if(d<.35){
        float br=.5+.5*sin(t*3.+h.x*20.+fbm(p*4.)*6.);
        float edge=exp(-max(d,0.)*9.)*(1.-smoothstep(-.12,0.,d)*0.)+(1.-smoothstep(-.12,-.02,d))*0.;
        float inside=1.-smoothstep(-.02,.02,d);
        float cr=1.-smoothstep(0.,.06,abs(fbm(p*3.+h.x*9.)-.5));
        vec3 leaf=vec3(.07,.035,.025)*(.7+.6*fbm(p*6.))+fire(cr*(.45+.4*br))*.8;
        vec3 halo=fire(.55+.45*br)*exp(-abs(d)*11.)*(k==0?1.:.7);
        col=mix(col,leaf,inside*(k==0?1.:.8))+halo*(1.-inside*.65); } } }
  col+=ember(q,t,13.,24.,.5,.55,0.,vec3(1.,.55,.15))+ember(q,t,21.,40.,.85,.5,4.,vec3(1.,.72,.3));
  col+=vec3(.6,.15,.02)*exp(-(H-q.y)/30.)*(.55+.45*sin(t*1.1));
  return col*vign(uv,.42); }`,
"""
s = rep(s, "const DOS_GLSL = {\n", "const DOS_GLSL = {\n" + DOS)

SKIN = r"""  vendanges: `
vec3 face(vec2 q,vec2 uv,float t){
  float b=3.; vec4 R=photoRect(b); float ii=interior(q,b); float ip=inR(q,R);
  float fd=frameD(q,b);
  vec3 frame=mix(vec3(.5,.31,.08),vec3(1.,.86,.46),pow(.5+.5*sin(atan(q.y-H*.5,q.x-W*.5)*2.+t*.4+u_tilt.x*2.5),2.))*(.8+.35*glint(uv,u_tilt,9.));
  float vigne=sin(q.x*.35+sin(q.y*.2)*2.)*sin(q.y*.35+sin(q.x*.2)*2.); frame*=.88+.12*smoothstep(.2,.8,vigne);
  vec2 s=photoUV(q,R); vec3 p=photo(s);
  vec3 ph=p*vec3(1.1,.96,.78)+vec3(.06,.02,0.)*(1.-s.y);
  ph+=vec3(1.,.75,.4)*glint(uv,u_tilt,10.)*.12;
  float lev=u_rev<1.8?(1.-smoothstep(.1,1.6,u_rev))*120.:0.;
  float tilt=clamp(u_tilt.x*.4,-.26,.26);
  float ys=168.+lev+(q.x-W*.5)*tilt+sin(q.x*.07+t*1.3)*1.8+sin(q.x*.13-t*.9)*1.;
  float sous=smoothstep(ys-.6,ys+.6,q.y);
  vec3 air=mix(vec3(.16,.05,.08),vec3(.09,.03,.05),smoothstep(116.,ys,q.y));
  float prof=clamp((q.y-ys)/(H-ys),0.,1.);
  vec3 vin=mix(vec3(.5,.04,.12),vec3(.16,.01,.04),prof);
  vin+=vec3(.9,.25,.3)*pow(.5+.5*sin(q.x*.09+q.y*.04-t*.8+fbm(q*.03+t*.05)*5.),10.)*.18*(1.-prof);
  float men=exp(-pow((q.y-ys)/1.3,2.)); vin+=vec3(1.,.6,.6)*men*.55;
  vin+=vec3(1.,.85,.8)*men*step(.94,h21(floor(vec2(q.x*.5-t*3.,0.))))*.6;
  vec3 inner=mix(air,vin,sous)+vec3(1.,.82,.5)*men*(1.-sous)*.25;
  float verre=exp(-pow((q.x-20.-u_tilt.x*8.)/4.,2.))+.5*exp(-pow((q.x-31.-u_tilt.x*8.)/1.6,2.)); inner+=vec3(1.,.85,.9)*verre*.07*smoothstep(118.,140.,q.y);
  vec3 col=mix(inner,ph,ip);
  col=mix(frame,col,ii);
  return col; }`,
"""
s = rep(s, "const SKIN_GLSL = {\n", "const SKIN_GLSL = {\n" + SKIN)
s = rep(s, "orage: 'Orage', brume: 'Brume' };", "orage: 'Orage', brume: 'Brume', vendanges: 'Vendanges' };")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
s += """
/* ---------- patch257 : Dos Automne, Dos Braises d'automne, Skin Vendanges ---------- */
body[data-dos="automne"], .bq-dos-apercu[data-dos="automne"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #C2621C 0%, #9A3E12 55%, #4E1606 100%);
  --dos-liseret: rgba(255,226,180,.7); --dos-or: #FFE2B4; --dos-embleme: #3A1004; --dos-anneau: rgba(58,16,4,.92); --dos-halo: rgba(255,190,120,.35);
}
body[data-dos="braises"], .bq-dos-apercu[data-dos="braises"]{
  --dos-fond: radial-gradient(circle at 50% 60%, #3A1408 0%, #1C0B06 55%, #080403 100%);
  --dos-liseret: rgba(255,150,70,.6); --dos-or: #FFA45A; --dos-embleme: #120604; --dos-anneau: rgba(18,6,4,.92); --dos-halo: rgba(255,100,20,.45);
}
.mini.skin-vendanges{ --sk-acc: #F2CB72; }
.mini.skin-vendanges .mini-nom{ color: #FBE3B0; text-shadow: 0 0 6px rgba(120,10,30,.6); }
.mini.skin-vendanges .mini-num{ color: #E6B3A0; } .mini.skin-vendanges .mini-rarete{ color: #F2CB72 !important; } .mini.skin-vendanges .mini-dept{ color: rgba(251,227,176,.18); }
"""
f.write_text(s, encoding='utf-8')
print('patch257 ok')
