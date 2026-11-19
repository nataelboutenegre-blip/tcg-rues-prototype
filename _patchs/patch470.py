# patch470 : skin Or fondu (version redessinée de la saison 3, patch454) : les gouttes coulent du bord de la photo.
# Bug vu par Nataël le 19/11 : la ligne dorée était dessinée par-dessus les gouttes, coupées en « épingles ».
# Maintenant : un filet d'or continu (le bord de la photo) d'où les gouttes se détachent, un peu plus courtes.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
p = os.path.join(R, 'app.js'); t = open(p, encoding='utf-8').read()
if 'patch470' in t: print('app.js : déjà fait'); raise SystemExit
i = t.index("  orfondu: SKIN_PRE2 + `"); j = t.index("  neon: SKIN_PRE2 + `", i)
s = t[i:j]
a = s[s.index("  // des gouttes d'or perlent sous la photo"):s.index("  // poussière d'or")]
b = """  // l'or coule du bord de la photo : un filet, et des gouttes qui s'en détachent (patch470)
  float cw=15.; float ci=floor(q.x/cw); float ch=h21(vec2(ci,3.));
  float xc=(ci+.5)*cw+(h21(vec2(ci,5.))-.5)*6.;
  float y0=R.w-.5; float lg=(2.+5.5*ch)*(.85+.15*sin(t*.4+ch*20.))+lev*30.;
  float yb=y0+lg; float larg=1.35+.9*ch;
  float tt=clamp((q.y-y0)/max(lg,.1),0.,1.);
  float rr=larg*(1.05-.5*smoothstep(0.,.8,tt));
  float dSeg=length(vec2(q.x-xc,q.y-clamp(q.y,y0,yb)))-rr;
  float dBul=length((q-vec2(xc,yb+larg*.25))*vec2(1.,.92))-larg*1.18;
  float dG=smin(dSeg,dBul,1.6)+1e3*step(ch,.3);
  float dJ=abs(q.y-y0)-1.25;
  float dOr=smin(dG,dJ,3.2);
  float oD=1.-smoothstep(-.45,.45,dOr);
  float cote=clamp(.5-(q.x-xc)/larg*.5+u_tilt.x*.6,0.,1.);
  vec3 og=mix(vec3(.5,.3,.06),vec3(1.,.86,.45),mix(.55+.3*glint(uv,u_tilt,7.),cote,smoothstep(0.,1.,(q.y-y0)/2.5)*step(dG,dJ+1.)));
  og+=vec3(1.,.97,.8)*exp(-pow((q.x-xc+larg*.35)/.45,2.))*.5*step(dG,0.)*step(y0+1.,q.y);
  og+=vec3(1.,.95,.75)*exp(-dot(q-vec2(xc-larg*.4,yb),q-vec2(xc-larg*.4,yb))/.6)*.7*step(.3,ch);
  float ombre=(1.-smoothstep(0.,2.2,dOr))*step(y0,q.y)*.55;
"""
s = s.replace(a, b)
x = "  col=mix(col,vec3(.95,.72,.25)*(.7+.5*glint(uv,u_tilt,7.)),joint*.75);\n  col=mix(col,og,goutte*step(R.w-1.,q.y));\n"
assert s.count(x) == 1
s = s.replace(x, "  col*=1.-ombre;\n  col=mix(col,og,oD*step(R.w-3.,q.y));\n")
s = s.replace("vec3 face(vec2 q,vec2 uv,float t){", "float smin(float a,float b,float k){ float h=clamp(.5+.5*(b-a)/k,0.,1.); return mix(b,a,h)-k*h*(1.-h); }\nvec3 face(vec2 q,vec2 uv,float t){", 1)
assert 'goutte=' not in s and 'joint' not in s
open(p, 'w', encoding='utf-8').write(t[:i] + s + t[j:]); print('app.js : ok')
